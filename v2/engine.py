"""Paper Trader v2 engine. One long-running process per trading day (resumable: state lives in data/v2/state.json).

    python -m v2.engine [--git] [--max-minutes 330]
"""
import argparse
import json
import time as _time
from datetime import datetime, timedelta

from v2 import bots, costs, exits, orchestrator, report, risk
from v2 import config as C
from v2.feed import Feed
from v2.util import ET, hm, log, parse_ts


class RealEnv:
    def now(self):
        return datetime.now(ET)

    def sleep(self, s):
        _time.sleep(s)


def _fresh_state(today):
    return {"date": today, "start_equity": None, "halted": False, "flattened": False, "reported": False,
            "metas": {}, "cooldown": {}, "news": {}, "briefing": "", "news_done": False, "signals": 0,
            "equity_today": [], "last_equity_row": "", "spy_open": None}


class Engine:
    def __init__(self, broker, env=None, git=False, news_fn=None, max_minutes=330, symbols=None):
        self.broker, self.env, self.git = broker, env or RealEnv(), git
        self.news_fn = news_fn if news_fn is not None else bots.run_news_desk
        self.max_minutes = max_minutes
        self.symbols = list(symbols or C.WATCHLIST)
        self.feed = Feed(broker, self.symbols)
        self.state = None
        self._last_git = 0.0

    # ---------- state ----------
    def _load_state(self, today):
        p = C.DATA_DIR / "state.json"
        try:
            s = json.load(open(p))
            if s.get("date") == today:
                return s
        except Exception:
            pass
        return _fresh_state(today)

    def _save_state(self):
        report.write_json("state.json", self.state)

    # ---------- main loop ----------
    def run(self):
        now = self.env.now()
        today = now.date().isoformat()
        cal = self.broker.calendar(today, today)
        if not cal or cal[0]["date"] != today:
            log("Market closed today - nothing to do.")
            return
        d = now.date()
        self.open_dt = datetime.combine(d, hm(cal[0]["open"]), tzinfo=ET)
        self.close_dt = datetime.combine(d, hm(cal[0]["close"]), tzinfo=ET)
        self.first_entry = self.open_dt + timedelta(minutes=C.FIRST_ENTRY_MIN_AFTER_OPEN)
        self.last_entry = self.close_dt - timedelta(minutes=C.LAST_ENTRY_MIN_BEFORE_CLOSE)
        self.flatten_at = self.close_dt - timedelta(minutes=C.FLATTEN_MIN_BEFORE_CLOSE)
        deadline = now + timedelta(minutes=self.max_minutes)
        self.state = self._load_state(today)
        if self.state["reported"]:
            log("Today is already finished.")
            return

        while self.env.now() < self.open_dt - timedelta(minutes=12):
            if self.env.now() >= deadline:
                log("Time budget reached before the open.")
                return
            self.env.sleep(60)
        self.feed.load_history(self.env.now(), self.open_dt)
        log(f"v2 engine running. Open {self.open_dt:%H:%M}, first entry {self.first_entry:%H:%M}, flatten {self.flatten_at:%H:%M}")

        fails = 0
        while True:
            now = self.env.now()
            if now >= deadline:
                log("Time budget reached - a fresh job will take over (positions keep their stops at Alpaca).")
                break
            if now < self.open_dt:
                self.env.sleep(30)
                continue
            if now >= self.close_dt + timedelta(minutes=2):
                self.finish_day(now)
                break
            try:
                self.cycle(now)
                fails = 0
            except Exception as e:
                fails += 1
                log(f"Cycle failed ({fails}): {type(e).__name__}: {e}")
                if fails >= 30:
                    log("Too many failures in a row - stopping.")
                    break
            self._save_state()
            if self.git and _time.time() - self._last_git > C.GIT_SYNC_SECONDS:
                report.git_sync(f"v2: {self.env.now():%Y-%m-%d %H:%M} ET")
                self._last_git = _time.time()
            self.env.sleep(C.SCAN_SECONDS)
        self._save_state()
        if self.git:
            report.git_sync(f"v2: {self.env.now():%Y-%m-%d %H:%M} ET (end of run)")

    # ---------- one scan ----------
    def cycle(self, now):
        st, metas = self.state, self.state["metas"]
        self.feed.update(now, self.open_dt)
        acct = self.broker.account()
        equity = float(acct["equity"])
        if st["start_equity"] is None:
            st["start_equity"] = float(acct.get("last_equity") or equity)
        if st["spy_open"] is None and self.feed.today.get("SPY"):
            st["spy_open"] = self.feed.today["SPY"][0]["o"]
        positions = {p["symbol"]: p for p in self.broker.positions()}

        self._maybe_news(now)
        ctxs = {s: self.feed.ctx(s, now, tuple(st["news"].get(s, ("both", "")))) for s in self.symbols}

        self._sync(now, positions, ctxs)

        # hard stops for the day
        if not st["halted"] and risk.daily_stop_hit(equity, st["start_equity"]):
            log(f"Daily loss limit hit (equity {equity:,.0f}) - closing everything, done for the day")
            self._close_all(positions, "daily loss limit")
            st["halted"] = True
        if now >= self.flatten_at and not st["flattened"]:
            log("Flatten time - closing everything")
            self._close_all(positions, "flatten")
            st["flattened"] = True

        if not st["flattened"] and not st["halted"]:
            self._manage_exits(now, positions, ctxs)
            if self.first_entry <= now < self.last_entry:
                self._entries(now, equity, positions, ctxs)

        # reports
        last = st["last_equity_row"]
        if not last or (now - parse_ts(last)).total_seconds() >= 300:
            report.append_csv("equity.csv", report.EQUITY_COLS,
                              {"time": now.isoformat(timespec="minutes"), "equity": round(equity, 2), "cash": acct["cash"]})
            st["equity_today"].append({"t": now.strftime("%H:%M"), "v": round(equity, 2)})
            st["last_equity_row"] = now.isoformat()
        report.write_live(now, self.open_dt <= now < self.close_dt, st["halted"], acct, st["start_equity"],
                          list(positions.values()), metas, st["equity_today"], st["briefing"])

    # ---------- pieces ----------
    def _maybe_news(self, now):
        st = self.state
        if st["news_done"] or now < self.first_entry - timedelta(minutes=2):
            return
        rows = []
        for s in self.symbols:
            c = self.feed.ctx(s, now)
            rows.append({"symbol": s, "gap_pct": c.gap_pct, "relvol": c.rvol})
        try:
            dec, brief = self.news_fn(rows, now)
        except Exception as e:
            dec, brief = {}, f"news desk error: {type(e).__name__}: {e}"
        st["news"] = {k: list(v) for k, v in dec.items()}
        st["briefing"] = brief
        st["news_done"] = True
        blocked = [k for k, v in dec.items() if v[0] == "block"]
        log(f"News desk done: {len(dec)} calls, blocked {blocked}" if dec else f"News desk: no calls ({brief[:100]})")

    def _sync(self, now, positions, ctxs):
        st, metas = self.state, self.state["metas"]
        for sym in list(metas):
            m = metas[sym]
            if sym in positions:
                if not m["seen"]:
                    m["seen"] = True
                    m["entry"] = float(positions[sym]["avg_entry_price"])
                    m["risk_ps"] = abs(m["entry"] - m["stop"]) or m["risk_ps"]
                continue
            if not m["seen"]:
                if (now - parse_ts(m["submitted"])).total_seconds() < 90:
                    continue            # entry still filling
                log(f"{sym}: entry never filled - dropping it")
                try:
                    self.broker.cancel_orders(sym)
                except Exception as e:
                    log(f"  cancel failed: {e}")
                metas.pop(sym)
                continue
            self._record_exit(sym, now)
        for sym in positions:
            if sym not in metas:
                log(f"{sym}: position without a plan (left over?) - closing it")
                try:
                    self.broker.close_position(sym)
                except Exception as e:
                    log(f"  close failed: {e}")

    def _record_exit(self, sym, now):
        st = self.state
        m = st["metas"].pop(sym)
        fill = self.broker.last_exit_fill(sym, m["opened"], m["side"])
        last_px = self.feed.today[sym][-1]["c"] if self.feed.today.get(sym) else m["entry"]
        exit_px = fill[0] if fill else last_px
        sign = 1 if m["side"] == "long" else -1
        qty = m["qty"]
        pnl = sign * (exit_px - m["entry"]) * qty
        spread = self.feed.ctx(sym, now).spread_bps
        cost = costs.trade_cost(qty, m["entry"], exit_px, m["in_bps"], costs.bps_per_side(spread))
        held = (now - parse_ts(m["opened"])).total_seconds() / 60
        reason = m.get("closing") or ("trailing stop" if abs(m["stop"] - m["stop0"]) > 0.005 else "stop loss")
        report.append_csv("trades.csv", report.TRADE_COLS, {
            "date": now.date().isoformat(), "symbol": sym, "side": m["side"], "qty": qty,
            "entry": round(m["entry"], 4), "exit": round(exit_px, 4), "pnl": round(pnl, 2),
            "pnl_pct": round(sign * (exit_px / m["entry"] - 1) * 100, 3), "est_cost": round(cost, 2),
            "hold_min": round(held, 1), "exit_reason": reason, "score": round(m["score"], 3), "votes": m["votes"]})
        st["cooldown"][sym] = now.isoformat()
        log(f"CLOSED {m['side']} {sym} x{qty}: {pnl:+.2f} (cost est {cost:.2f}) - {reason}")
        report.update_bots_json()

    def _close_all(self, positions, reason):
        for sym, m in self.state["metas"].items():
            m["closing"] = reason
        try:
            self.broker.close_all()
        except Exception as e:
            log(f"close_all failed: {e}")

    def _manage_exits(self, now, positions, ctxs):
        for sym, m in list(self.state["metas"].items()):
            p = positions.get(sym)
            if not p or not m["seen"]:
                continue
            price = float(p["current_price"])
            held = (now - parse_ts(m["opened"])).total_seconds() / 60
            act = exits.manage(m, price, ctxs.get(sym), held)
            if act["action"] == "close":
                m["closing"] = act["reason"]
                try:
                    self.broker.close_position(sym)
                    log(f"EXIT {sym} @ {price:.2f} ({act['r']:+.2f}R): {act['reason']}")
                except Exception as e:
                    log(f"{sym}: close failed: {e}")
            elif act["action"] == "stop":
                try:
                    if self.broker.replace_stop(sym, act["new_stop"]):
                        m["stop"] = act["new_stop"]
                        log(f"STOP {sym} -> {act['new_stop']:.2f} ({act['reason']})")
                except Exception as e:
                    log(f"{sym}: stop move failed: {e}")

    def _entries(self, now, equity, positions, ctxs):
        st, metas = self.state, self.state["metas"]
        weights = orchestrator.load_weights()
        cands = []
        for s in self.symbols:
            if s in metas:
                continue
            cd = st["cooldown"].get(s)
            if cd and (now - parse_ts(cd)).total_seconds() < C.COOLDOWN_MIN * 60:
                continue
            d = orchestrator.evaluate(ctxs[s], weights)
            if d.side and not d.skip:
                cands.append(d)
        cands.sort(key=lambda d: -abs(d.score))
        marks = {s: float(p["current_price"]) for s, p in positions.items()}
        placed = 0
        for d in cands:
            if placed >= C.MAX_NEW_ENTRIES_PER_SCAN:
                break
            c = ctxs[d.symbol]
            qty = risk.size(equity, c.price, d.stop_dist)
            ok, why = risk.check(metas, marks, equity, d.symbol, qty, c.price, d.stop_dist, st["halted"])
            if not ok:
                log(f"{d.symbol}: signal {d.side} {d.score:+.2f} skipped by risk bot ({why})")
                continue
            if d.side == "short" and not self.broker.is_shortable(d.symbol):
                continue
            cid = f"v2-{d.symbol}-{now:%H%M%S}"
            try:
                self.broker.submit_entry(d.symbol, qty, "buy" if d.side == "long" else "sell", d.stop_price, cid)
            except Exception as e:
                log(f"{d.symbol}: order failed: {e}")
                continue
            st["signals"] += 1
            metas[d.symbol] = {"symbol": d.symbol, "side": d.side, "qty": qty, "entry": c.price, "stop0": d.stop_price,
                               "stop": d.stop_price, "risk_ps": d.stop_dist, "opened": now.isoformat(),
                               "submitted": now.isoformat(), "seen": False, "peak_r": 0.0, "in_bps": d.side_bps,
                               "score": d.score, "votes": orchestrator.votes_str(d.votes)}
            placed += 1
            log(f"ENTER {d.side} {d.symbol} x{qty} @ ~{c.price:.2f} stop {d.stop_price:.2f} score {d.score:+.2f} "
                + " ".join(f"{v.name}{v.dir:+d}" for v in d.votes if v.dir))

    # ---------- end of day ----------
    def finish_day(self, now):
        st = self.state
        try:
            positions = {p["symbol"]: p for p in self.broker.positions()}
            if positions:
                self.broker.close_all()
            self.feed.update(now, self.open_dt)
            self._sync(now, {}, {})
        except Exception as e:
            log(f"finish_day cleanup: {e}")
        acct = self.broker.account()
        equity = float(acct["equity"])
        today = now.date().isoformat()
        trades = [t for t in report.read_csv("trades.csv") if t["date"] == today]
        spy = self.feed.today.get("SPY") or []
        spy_open, spy_close = (spy[0]["o"], spy[-1]["c"]) if spy else (0, 0)
        start = st["start_equity"] or equity
        report.append_csv("daily.csv", report.DAILY_COLS, {
            "date": today, "start_equity": round(start, 2), "end_equity": round(equity, 2),
            "pnl": round(equity - start, 2), "pnl_pct": round((equity / start - 1) * 100, 3),
            "trades": len(trades), "wins": sum(1 for t in trades if float(t["pnl"]) > 0), "signals": st["signals"],
            "ai_blocked": 0, "ai_blocked_pnl": 0, "spy_open": round(spy_open, 2), "spy_close": round(spy_close, 2),
            "spy_pct": round((spy_close / spy_open - 1) * 100, 3) if spy_open else 0,
            "longs": sum(1 for t in trades if t["side"] == "long"), "shorts": sum(1 for t in trades if t["side"] == "short")})
        report.write_live(now, False, st["halted"], acct, start, [], st["metas"], st["equity_today"], st["briefing"])
        report.update_bots_json()
        st["reported"] = True
        log(f"Day finished: equity {equity:,.2f} ({equity - start:+,.2f}), {len(trades)} trades")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--git", action="store_true", help="commit data/v2 back to the repo periodically")
    ap.add_argument("--max-minutes", type=int, default=330)
    a = ap.parse_args()
    from v2.broker import AlpacaBroker
    Engine(AlpacaBroker(), git=a.git, max_minutes=a.max_minutes).run()


if __name__ == "__main__":
    main()
