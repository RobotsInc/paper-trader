"""Alpaca PAPER broker + market data (free IEX feed). The engine only talks to this interface,
so tests can swap in v2/sim.py's SimBroker."""
import os

import requests

TRADE = "https://paper-api.alpaca.markets"   # paper only - never the live endpoint
DATA = "https://data.alpaca.markets"
FEED = "iex"


class AlpacaBroker:
    def __init__(self):
        self.h = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
                  "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
        self._shortable = {}

    # ---- plumbing ----
    def _req(self, method, base, path, ok=(200,), **kw):
        r = requests.request(method, base + path, headers=self.h, timeout=30, **kw)
        if r.status_code not in ok and not (200 <= r.status_code < 300):
            raise RuntimeError(f"Alpaca {method} {path} HTTP {r.status_code}: {r.text[:200]!r}")
        return r.json() if r.content else None

    def _get(self, base, path, **params):
        return self._req("GET", base, path, params=params)

    # ---- account / clock ----
    def clock(self):
        return self._get(TRADE, "/v2/clock")

    def calendar(self, start, end):
        return self._get(TRADE, "/v2/calendar", start=start, end=end)

    def account(self):
        return self._get(TRADE, "/v2/account")

    def positions(self):
        return self._get(TRADE, "/v2/positions")

    def open_orders(self, symbol=None):
        p = dict(status="open", limit=500)
        if symbol:
            p["symbols"] = symbol
        return self._get(TRADE, "/v2/orders", **p)

    def is_shortable(self, symbol):
        if symbol not in self._shortable:
            a = self._get(TRADE, f"/v2/assets/{symbol}")
            self._shortable[symbol] = bool(a.get("shortable") and a.get("easy_to_borrow"))
        return self._shortable[symbol]

    # ---- orders ----
    def submit_entry(self, symbol, qty, side, stop_price, client_id):
        """Market entry with an attached stop-loss that Alpaca holds. side: 'buy' (long) or 'sell' (short)."""
        body = {"symbol": symbol, "qty": str(int(qty)), "side": side, "type": "market",
                "time_in_force": "day", "order_class": "oto",
                "stop_loss": {"stop_price": f"{stop_price:.2f}"}, "client_order_id": client_id}
        return self._req("POST", TRADE, "/v2/orders", json=body)

    def replace_stop(self, symbol, new_stop):
        """Move the protective stop for this symbol. Returns True if an order was changed."""
        for o in self.open_orders(symbol):
            if o.get("type") == "stop":
                self._req("PATCH", TRADE, f"/v2/orders/{o['id']}", json={"stop_price": f"{new_stop:.2f}"})
                return True
        return False

    def current_stop(self, symbol):
        for o in self.open_orders(symbol):
            if o.get("type") == "stop" and o.get("stop_price"):
                return float(o["stop_price"])
        return None

    def cancel_orders(self, symbol):
        for o in self.open_orders(symbol):
            try:
                self._req("DELETE", TRADE, f"/v2/orders/{o['id']}")
            except RuntimeError:
                pass

    def close_position(self, symbol):
        self.cancel_orders(symbol)   # the stop must go first or Alpaca refuses the close
        return self._req("DELETE", TRADE, f"/v2/positions/{symbol}")

    def close_all(self):
        return self._req("DELETE", TRADE, "/v2/positions", params={"cancel_orders": "true"}) or []

    def last_exit_fill(self, symbol, after_iso, entry_side):
        """(price, iso time) of the most recent filled order on the opposite side of the entry."""
        exit_side = "sell" if entry_side == "long" else "buy"
        rows = self._get(TRADE, "/v2/orders", status="closed", symbols=symbol, after=after_iso,
                         direction="desc", limit=50)
        for o in rows:
            if o.get("side") == exit_side and o.get("filled_avg_price") and o.get("filled_at"):
                return float(o["filled_avg_price"]), o["filled_at"]
        return None

    # ---- market data ----
    def bars(self, symbols, start, end=None, timeframe="1Min"):
        out = {}
        for i in range(0, len(symbols), 100):
            chunk, token = symbols[i:i + 100], None
            while True:
                p = dict(symbols=",".join(chunk), timeframe=timeframe, start=start, feed=FEED,
                         limit=10000, adjustment="split")
                if end:
                    p["end"] = end
                if token:
                    p["page_token"] = token
                j = self._get(DATA, "/v2/stocks/bars", **p)
                for sym, b in (j.get("bars") or {}).items():
                    out.setdefault(sym, []).extend(b)
                token = j.get("next_page_token")
                if not token:
                    break
        return out

    def quotes(self, symbols):
        """{symbol: (bid, ask)} - IEX's own quote; can be wider/staler than the national best."""
        out = {}
        for i in range(0, len(symbols), 100):
            j = self._get(DATA, "/v2/stocks/quotes/latest", symbols=",".join(symbols[i:i + 100]), feed=FEED)
            out.update({s: (float(q.get("bp") or 0), float(q.get("ap") or 0)) for s, q in (j.get("quotes") or {}).items()})
        return out
