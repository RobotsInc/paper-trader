"""A fake market + paper broker for testing the engine without Alpaca.
Prices are random walks; some symbols get a trending, high-volume window so the bots have something to find."""
import random
from datetime import date, datetime, timedelta, timezone

from v2.util import ET


class SimEnv:
    def __init__(self, day, start_hm=(9, 0)):
        self.t = datetime(day.year, day.month, day.day, *start_hm, tzinfo=ET)
        self.broker = None

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += timedelta(seconds=s)
        if self.broker:
            self.broker.advance(self.t)


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SimBroker:
    def __init__(self, env, symbols, day, seed=1, equity=100000.0, short_ok=True):
        self.env, self.symbols, self.day = env, list(symbols), day
        env.broker = self
        self.rng = random.Random(seed)
        self.cash0 = equity
        self.realized = 0.0
        self.pos = {}          # sym -> dict(qty signed, entry)
        self.orders = []       # open stop orders
        self.closed = []       # closed orders
        self.oid = 0
        self.short_ok = short_ok
        self.nbars = 390
        self.cursor = None     # last processed minute (datetime)
        self.bars_by_day = {s: {} for s in self.symbols}
        self.base = {s: self.rng.uniform(20, 600) for s in self.symbols}
        prior = [day - timedelta(days=i) for i in range(1, 15)]
        prior = [d for d in prior if d.weekday() < 5][:10][::-1]
        for s in self.symbols:
            for d in prior:
                self.bars_by_day[s][d] = self._gen_day(s, d, trending=False)
            self.bars_by_day[s][day] = self._gen_day(s, day, trending=True)
        self.advance(env.now())

    # ---- price generation ----
    def _gen_day(self, s, d, trending):
        r, px = self.rng, self.base[s]
        mu_trend = r.choice([0, 0, 1, -1]) * r.uniform(0.0006, 0.0012) if trending else 0.0
        t_start, t_end = r.randint(20, 150), r.randint(200, 330)
        out = []
        for i in range(390):
            u = 1.6 if i < 30 or i > 360 else 1.0
            sig = 0.0006 * r.uniform(0.7, 1.4)
            in_trend = trending and t_start <= i <= t_end
            drift = mu_trend if in_trend else 0.0
            o = px
            c = o * (1 + drift + r.gauss(0, sig))
            h, l = max(o, c) * (1 + abs(r.gauss(0, sig / 2))), min(o, c) * (1 - abs(r.gauss(0, sig / 2)))
            v = max(50, int(r.lognormvariate(6.0, 0.5) * u * (2.2 if in_trend and mu_trend else 1.0)))
            ts = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET) + timedelta(minutes=i)
            out.append({"t": _iso(ts), "o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4), "v": v, "_ts": ts})
            px = c
        self.base[s] = px
        return out

    # ---- time ----
    def _now_idx(self):
        t = self.env.now()
        return int((t - datetime(t.year, t.month, t.day, 9, 30, tzinfo=ET)).total_seconds() // 60)

    def advance(self, now):
        """Process every minute bar that has completed since the last call: stops trigger on them."""
        idx = self._now_idx()
        start = -1 if self.cursor is None else self.cursor
        for i in range(max(start + 1, 0), min(idx, self.nbars - 1) + 1):
            for s in self.symbols:
                b = self.bars_by_day[s][self.day][i]
                self._check_stops(s, b, now)
        if idx >= 0:
            self.cursor = min(idx, self.nbars - 1)

    def _px(self, s):
        i = min(max(self._now_idx(), 0), self.nbars - 1)
        return self.bars_by_day[s][self.day][i]["c"]

    def _check_stops(self, s, b, now):
        for o in list(self.orders):
            if o["symbol"] != s or o["type"] != "stop":
                continue
            stop = float(o["stop_price"])
            hit = (o["side"] == "sell" and b["l"] <= stop) or (o["side"] == "buy" and b["h"] >= stop)
            if hit and s in self.pos:
                self._fill_close(s, stop, now, o)

    def _fill_close(self, s, px, now, order=None):
        p = self.pos.pop(s)
        self.realized += (px - p["entry"]) * p["qty"]
        self.orders = [o for o in self.orders if o["symbol"] != s]
        self.closed.append({"symbol": s, "side": "sell" if p["qty"] > 0 else "buy", "filled_avg_price": f"{px:.4f}",
                            "filled_at": _iso(now)})

    # ---- broker interface ----
    def clock(self):
        i = self._now_idx()
        return {"is_open": 0 <= i < self.nbars}

    def calendar(self, start, end):
        return [{"date": self.day.isoformat(), "open": "09:30", "close": "16:00"}]

    def account(self):
        upl = sum((self._px(s) - p["entry"]) * p["qty"] for s, p in self.pos.items())
        return {"equity": f"{self.cash0 + self.realized + upl:.2f}", "cash": f"{self.cash0 + self.realized:.2f}",
                "buying_power": "300000", "last_equity": f"{self.cash0:.2f}"}

    def positions(self):
        out = []
        for s, p in self.pos.items():
            px = self._px(s)
            upl = (px - p["entry"]) * p["qty"]
            out.append({"symbol": s, "qty": str(p["qty"]), "side": "long" if p["qty"] > 0 else "short",
                        "avg_entry_price": f"{p['entry']:.4f}", "current_price": f"{px:.4f}",
                        "unrealized_pl": f"{upl:.2f}", "unrealized_plpc": f"{upl / (p['entry'] * abs(p['qty'])):.5f}"})
        return out

    def open_orders(self, symbol=None):
        return [o for o in self.orders if symbol in (None, o["symbol"])]

    def is_shortable(self, symbol):
        return self.short_ok

    def submit_entry(self, symbol, qty, side, stop_price, client_id):
        if symbol in self.pos:
            raise RuntimeError("position exists")
        px = self._px(symbol) * (1 + (0.0002 if side == "buy" else -0.0002))   # a little slippage
        self.pos[symbol] = {"qty": qty if side == "buy" else -qty, "entry": px}
        self.oid += 1
        self.orders.append({"id": f"o{self.oid}", "symbol": symbol, "type": "stop",
                            "side": "sell" if side == "buy" else "buy", "stop_price": f"{stop_price:.2f}"})
        return {"id": f"e{self.oid}"}

    def replace_stop(self, symbol, new_stop):
        for o in self.orders:
            if o["symbol"] == symbol and o["type"] == "stop":
                o["stop_price"] = f"{new_stop:.2f}"
                return True
        return False

    def cancel_orders(self, symbol):
        self.orders = [o for o in self.orders if o["symbol"] != symbol]

    def close_position(self, symbol):
        if symbol in self.pos:
            self._fill_close(symbol, self._px(symbol), self.env.now())

    def close_all(self):
        for s in list(self.pos):
            self._fill_close(s, self._px(s), self.env.now())
        return []

    def last_exit_fill(self, symbol, after_iso, entry_side):
        for o in reversed(self.closed):
            if o["symbol"] == symbol:
                return float(o["filled_avg_price"]), o["filled_at"]
        return None

    def bars(self, symbols, start, end=None, timeframe="1Min"):
        st = datetime.fromisoformat(start.replace("Z", "+00:00"))
        now = self.env.now()
        out = {}
        for s in symbols:
            rows = []
            for d, bars in self.bars_by_day[s].items():
                for b in bars:
                    if b["_ts"] >= st and b["_ts"] <= now - timedelta(seconds=1):
                        if end and b["_ts"] > datetime.fromisoformat(end.replace("Z", "+00:00")):
                            continue
                        rows.append({k: v for k, v in b.items() if k != "_ts"})
            out[s] = rows
        return out

    def quotes(self, symbols):
        return {s: (self._px(s) * 0.99985, self._px(s) * 1.00015) for s in symbols}
