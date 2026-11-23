import json, sys, tempfile, pathlib, unittest, io, contextlib
from datetime import date, datetime, timedelta
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from v2 import config as C, indicators as ind, risk, exits, orchestrator, bots, costs, report
from v2.feed import Ctx
from v2.sim import SimEnv, SimBroker
from v2.engine import Engine
from v2.util import ET, parse_ts


def sim_day(seed=1, news=None, max_minutes=600, **cfg):
    tmp = pathlib.Path(tempfile.mkdtemp())
    old = (C.DATA_DIR, {k: getattr(C, k) for k in cfg})
    C.DATA_DIR = tmp
    for k, v in cfg.items():
        setattr(C, k, v)
    day = date(2026, 11, 24)
    env = SimEnv(day)
    b = SimBroker(env, C.WATCHLIST, day, seed=seed)
    eng = Engine(b, env, news_fn=news or (lambda rows, now: ({}, "")), max_minutes=max_minutes)
    return tmp, env, b, eng, old


def restore(old):
    C.DATA_DIR = old[0]
    for k, v in old[1].items():
        setattr(C, k, v)


def quiet(fn):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn()


def rows(tmp, name):
    import csv
    p = tmp / name
    if not p.exists():
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


class Indicators(unittest.TestCase):
    def test_ema_rsi_bb_atr(self):
        up = [float(i) for i in range(1, 40)]
        self.assertEqual(ind.rsi(up, 14), 100.0)
        self.assertLess(ind.rsi(up[::-1], 14), 1)
        self.assertAlmostEqual(ind.ema([5, 5, 5, 5], 3)[-1], 5)
        mid, hi, lo = ind.bollinger([10.0] * 20)
        self.assertEqual((mid, hi, lo), (10.0, 10.0, 10.0))
        self.assertAlmostEqual(ind.atr([2, 3, 4], [1, 2, 3], [1.5, 2.5, 3.5], 14), 1.5, places=6)

    def test_vwap(self):
        bars = [{"h": 10, "l": 10, "c": 10, "v": 100}, {"h": 20, "l": 20, "c": 20, "v": 300}]
        vw, sd = ind.vwap_sd(bars)
        self.assertAlmostEqual(vw, 17.5)
        self.assertGreater(sd, 0)


class Risk(unittest.TestCase):
    def test_size_capped(self):
        # 0.5% of 100k = 500 risk; stop 0.5 -> 1000 sh by risk, but 10% cap at $100 = 100 sh
        self.assertEqual(risk.size(100000, 100, 0.5), 100)
        self.assertEqual(risk.size(100000, 100, 10), 50)       # risk-bound
        self.assertEqual(risk.size(100000, 100, 0), 0)

    def test_limits(self):
        m = {"side": "long", "qty": 100, "entry": 100.0, "stop": 99.0}
        self.assertAlmostEqual(risk.open_risk({"A": m}), 100.0)
        m2 = dict(m, stop=100.5)                                  # stop past breakeven: no risk left
        self.assertEqual(risk.open_risk({"A": m2}), 0.0)
        ok, why = risk.check({"A": m}, {}, 100000, "A", 10, 100, 1, False)
        self.assertFalse(ok)
        ok, why = risk.check({}, {}, 100000, "B", 10, 100, 1, True)
        self.assertFalse(ok)
        ok, _ = risk.check({}, {}, 100000, "B", 10, 100, 1, False)
        self.assertTrue(ok)
        # open-risk cap: 3% of 100k = 3000
        ok, why = risk.check({}, {}, 100000, "B", 1000, 100, 3.5, False)
        self.assertFalse(ok)
        self.assertIn("open risk", why)


class Exits(unittest.TestCase):
    def meta(self, side="long"):
        return {"side": side, "entry": 100.0, "stop": 99.0 if side == "long" else 101.0, "risk_ps": 1.0, "peak_r": 0.0}

    def test_ratchet_long(self):
        m = self.meta()
        a = exits.manage(m, 100.3, None, 5)              # +0.3R: nothing to lock yet
        self.assertEqual(a["action"], "hold")
        a = exits.manage(m, 100.5, None, 5)              # +0.5R (>= 0.4R) -> stop to breakeven
        self.assertEqual(a["action"], "stop")
        self.assertAlmostEqual(a["new_stop"], 100.0)
        m["stop"] = 100.0
        a = exits.manage(m, 100.7, None, 6)              # peak .7 -> lock .2
        self.assertAlmostEqual(a["new_stop"], 100.2)

    def test_ratchet_short_and_never_loosens(self):
        m = self.meta("short")
        a = exits.manage(m, 99.35, None, 5)              # +0.65R
        self.assertEqual(a["action"], "stop")
        self.assertAlmostEqual(a["new_stop"], 99.8)
        m["stop"] = 99.8
        a = exits.manage(m, 99.9, None, 6)               # pulled back; stop must not loosen
        self.assertEqual(a["action"], "hold")

    def test_target_and_time_stop(self):
        m = self.meta()
        a = exits.manage(m, 101.2, None, 10)             # >= 1R, no strong context -> take profit
        self.assertEqual(a["action"], "close")
        m = self.meta()
        a = exits.manage(m, 100.1, None, C.MAX_HOLD_MIN + 1)
        self.assertEqual(a["action"], "close")


class Orchestrator(unittest.TestCase):
    def ctx(self, **kw):
        c = Ctx(symbol="X", ready=True, now_idx=60, price=100.5, day_open=100, prev_close=100, vwap=100.0,
                vwap_sd=0.3, vwap_slope=0.05, or_high=100.2, or_low=99.8, rvol=2.5, vol_last3=1000, vol_avg20=1000,
                atr1=0.1, atr5=0.25, ema_fast=100.4, ema_slow=100.0, rsi5=62, macd_h=0.05, macd_h_prev=0.03,
                rsi1_7=60, bb=(100.2, 100.8, 99.6), spread_bps=2.0, bar_age_min=0)
        c.bars = [{"c": 100.4, "o": 100.3, "idx": 59}] * 3
        c.closes1 = [100 + i * 0.01 for i in range(60)]
        for k, v in kw.items():
            setattr(c, k, v)
        return c

    def test_long_signal(self):
        d = orchestrator.evaluate(self.ctx())
        self.assertEqual(d.side, "long", d.skip)
        self.assertLess(d.stop_price, 100.5)
        self.assertGreaterEqual(d.stop_dist, C.MIN_STOP_PCT * 100.5 - 1e-9)
        self.assertLessEqual(d.stop_dist, C.MAX_STOP_PCT * 100.5 + 1e-9)

    def test_vetoes(self):
        self.assertEqual(orchestrator.evaluate(self.ctx(news="block", news_note="earnings")).side, "")
        self.assertEqual(orchestrator.evaluate(self.ctx(news="short")).side, "")      # news disagrees
        self.assertEqual(orchestrator.evaluate(self.ctx(rvol=0.5)).side, "")          # volume filter
        self.assertEqual(orchestrator.evaluate(self.ctx(spread_bps=40)).side, "")     # liquidity
        self.assertEqual(orchestrator.evaluate(self.ctx(bar_age_min=9)).side, "")     # stale print
        self.assertEqual(orchestrator.evaluate(Ctx(symbol="X")).side, "")             # not ready

    def test_weights_change_score(self):
        base = orchestrator.evaluate(self.ctx()).score
        w = {"vwap": 0.25, "trend": 0.25, "orb": 0.25}
        self.assertNotEqual(base, orchestrator.evaluate(self.ctx(), w).score)

    def test_cost_model(self):
        self.assertEqual(costs.bps_per_side(None), C.SLIPPAGE_BPS_PER_SIDE)
        self.assertEqual(costs.bps_per_side(100), C.SLIPPAGE_CAP_BPS)
        self.assertAlmostEqual(costs.trade_cost(100, 50, 50, 3, 3), 3.0)


class SimDay(unittest.TestCase):
    def test_full_day_invariants(self):
        for seed in (1, 2, 3):
            tmp, env, b, eng, old = sim_day(seed, news=lambda r, n: ({"TSLA": ("block", "earnings")}, "b"))
            try:
                quiet(eng.run)
            finally:
                restore(old)
            self.assertEqual(b.pos, {}, "flat at the end")
            self.assertEqual(b.orders, [], "no dangling stop orders")
            tr = rows(tmp, "trades.csv")
            self.assertTrue(len(tr) > 0, f"seed {seed}: no trades")
            self.assertFalse(any(t["symbol"] == "TSLA" for t in tr), "news block respected")
            for t in tr:
                self.assertGreater(int(t["qty"]), 0)
            self.assertEqual(len(rows(tmp, "daily.csv")), 1)
            live = json.load(open(tmp / "live.json"))
            self.assertEqual(live["positions"], [])
            self.assertIn("day_pnl", live["account"])
            bj = json.load(open(tmp / "bots.json"))
            self.assertEqual(len(bj["bots"]), 11)
            # costs recorded on every trade
            self.assertTrue(all(float(t["est_cost"]) > 0 for t in tr))

    def test_no_entries_outside_window(self):
        tmp, env, b, eng, old = sim_day(4)
        entries = []
        orig = b.submit_entry
        def spy(symbol, qty, side, stop, cid):
            entries.append(env.now())
            return orig(symbol, qty, side, stop, cid)
        b.submit_entry = spy
        try:
            quiet(eng.run)
        finally:
            restore(old)
        self.assertTrue(entries)
        d = env.now().date()
        lo = datetime(d.year, d.month, d.day, 9, 45, tzinfo=ET)
        hi = datetime(d.year, d.month, d.day, 15, 30, tzinfo=ET)
        self.assertTrue(all(lo <= t < hi for t in entries), [str(t) for t in entries if not lo <= t < hi])

    def test_position_and_risk_caps_hold(self):
        tmp, env, b, eng, old = sim_day(5)
        peak = {"n": 0, "risk": 0.0}
        orig = eng._entries
        def watch(now, equity, positions, ctxs):
            orig(now, equity, positions, ctxs)
            metas = eng.state["metas"]
            peak["n"] = max(peak["n"], len(metas))
            peak["risk"] = max(peak["risk"], risk.open_risk(metas) / equity)
        eng._entries = watch
        try:
            quiet(eng.run)
        finally:
            restore(old)
        self.assertLessEqual(peak["n"], C.MAX_OPEN_POSITIONS)
        self.assertLessEqual(peak["risk"], C.MAX_OPEN_RISK + 1e-9)

    def test_daily_loss_limit_halts(self):
        tmp, env, b, eng, old = sim_day(6, DAILY_LOSS_LIMIT=0.0001)
        try:
            quiet(eng.run)
        finally:
            restore(old)
        st = json.load(open(tmp / "state.json"))
        self.assertEqual(b.pos, {})
        # once halted, no more entries: every trade closed before or at the halt
        self.assertTrue(st["halted"] or len(rows(tmp, "trades.csv")) == 0)

    def test_resume_after_time_budget(self):
        """Job 1 stops mid-day with positions open; job 2 (a fresh Engine) picks up from state.json."""
        tmp, env, b, eng, old = sim_day(7, max_minutes=240)       # 9:00 + 4h = 13:00
        try:
            quiet(eng.run)
            self.assertFalse(json.load(open(tmp / "state.json"))["reported"])
            eng2 = Engine(b, env, news_fn=lambda r, n: ({}, ""), max_minutes=600)
            quiet(eng2.run)
        finally:
            restore(old)
        self.assertEqual(b.pos, {})
        self.assertEqual(len(rows(tmp, "daily.csv")), 1)
        tr = rows(tmp, "trades.csv")
        self.assertEqual(len({(t["symbol"], t["entry"]) for t in tr}), len(tr), "no trade recorded twice")


if __name__ == "__main__":
    unittest.main(verbosity=2)
