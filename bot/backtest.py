"""Backtest: replay opening-range-breakout rule sets over past minute data.

Compares the bot's current rules against the research versions (Zarattini, Barbon & Aziz):
  - opening range: 15 min (ours) vs 5 min
  - stop: middle of the range (ours) vs 10% / 25% of the stock's 14-day ATR
  - exit: 2R profit target (ours) vs hold to the close
plus the paper's exact recipe (5-min range, trade in the first candle's direction, top 20 by
relative volume, 10% ATR stop, hold to close).

Every rule set is scored two ways:
  - per trade, in R (profit / initial risk) - independent of position sizing;
  - as a portfolio run with the bot's real limits (0.5% risk, max 5 positions, max 3 per side,
    20% per position, 150% gross, no doubling up within a group).
Each is run with and without slippage, and split into an earlier "train" stretch and a later
"test" stretch: pick on train, then check the pick still holds on test.

Run by .github/workflows/backtest.yml. Writes data/backtest/REPORT.md, results.csv, trades.csv.gz,
equity.png.

Limits: uses the bot's CORE list only (past "top movers" lists aren't available), 1-minute bars
(inside the entry bar, a stop or target only counts if the bar closes beyond it), and ignores the
dynamic correlation guard and the daily loss limit.
"""
import csv
import gzip
import math
import os
import statistics
import sys
import time
from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

import alpaca
import config as C
import universe

ET = ZoneInfo("America/New_York")
OUT = Path(__file__).resolve().parent.parent / "data" / "backtest"
MONTHS = int(os.getenv("BT_MONTHS", "12"))
SLIP = float(os.getenv("BT_SLIPPAGE_BPS", "3")) / 1e4     # per side, fraction of price
FEED = os.getenv("BT_FEED", "sip")                         # free plan allows SIP history > 15 min old
START_EQUITY = 100_000.0
OPEN_MIN = 9 * 60 + 30
# The bot's original (v2) rules, kept here so the backtest can still replay them.
V2 = {"max_chase": 0.5, "min_price": 10.0, "min_range": 0.002, "max_range": 0.04, "universe": 40}
REWARD_RISK = 2.0

ENTRIES = {
    # name: (range minutes, direction rule, VWAP filter, max chase in range-widths, selection)
    "15m": (15, "both", True, V2["max_chase"], "ours"),
    "5m": (5, "both", True, V2["max_chase"], "ours"),
    "paper5m": (5, "candle", False, None, "paper"),
}
STOPS = {"mid": "range middle", 0.10: "10% ATR", 0.25: "25% ATR"}
TARGETS = {"2R": "2R target", "close": "hold to close"}


def variant_name(e, s, t):
    tag = {"15m": "15-min range", "5m": "5-min range", "paper5m": "Paper recipe (5-min)"}[e]
    return f"{tag} · {STOPS[s]} stop · {TARGETS[t]}"


CURRENT = ("paper5m", 0.10, "close")   # live since v3
V2_RULES = ("15m", "mid", "2R")
PAPER = ("paper5m", 0.10, "close")


# ---------------- data ----------------
SESSION = requests.Session()


def get(base, path, **params):
    for attempt in range(6):
        r = SESSION.get(base + path, headers=alpaca._headers(), params=params, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 + attempt * 3)
            continue
        if r.status_code >= 400:
            raise RuntimeError(f"Alpaca {path} HTTP {r.status_code}: {r.text[:200]!r}")
        return r.json()
    raise RuntimeError(f"Alpaca {path}: gave up after retries")


def calendar(start, end):
    days = get(alpaca.TRADE, "/v2/calendar", start=start.isoformat(), end=end.isoformat())
    return [(d["date"], int(d["close"][:2]) * 60 + int(d["close"][3:5])) for d in days]


def day_bars(symbols, d, close_min, feed):
    """Regular-session 1-min bars for one day: {sym: [(minute, o, h, l, c, v), ...]}."""
    t0 = datetime.fromisoformat(d + "T09:30").replace(tzinfo=ET)
    t1 = t0 + timedelta(minutes=close_min - OPEN_MIN)
    iso = lambda t: t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {}
    for i in range(0, len(symbols), 100):
        chunk, token = symbols[i:i + 100], None
        while True:
            p = dict(symbols=",".join(chunk), timeframe="1Min", start=iso(t0),
                     end=iso(t1 - timedelta(seconds=1)), feed=feed, limit=10000, adjustment="split")
            if token:
                p["page_token"] = token
            j = get(alpaca.DATA, "/v2/stocks/bars", **p)
            for s, bl in (j.get("bars") or {}).items():
                rows = out.setdefault(s, [])
                for b in bl:
                    t = datetime.fromisoformat(b["t"].replace("Z", "+00:00")).astimezone(ET)
                    rows.append((t.hour * 60 + t.minute, b["o"], b["h"], b["l"], b["c"], b["v"]))
            token = j.get("next_page_token")
            if not token:
                break
    for rows in out.values():
        rows.sort()
    return out


# ---------------- signals ----------------
def find_entry(bars, k, direction, vwap_on, chase, cutoff):
    """First valid breakout after the k-minute opening range.
    Returns (bar index, side +1/-1, raw fill, range high, range low) or None."""
    end_or = OPEN_MIN + k
    orb = [b for b in bars if b[0] < end_or]
    if len(orb) < max(3, k // 3):
        return None
    hi, lo = max(b[2] for b in orb), min(b[3] for b in orb)
    if hi <= lo:
        return None
    longs = shorts = True
    if direction == "candle":
        o, c = orb[0][1], orb[-1][4]
        if c > o:
            shorts = False
        elif c < o:
            longs = False
        else:
            return None
    pv = sum((b[2] + b[3] + b[4]) / 3 * b[5] for b in orb)
    vv = sum(b[5] for b in orb)
    w = hi - lo
    for i, b in enumerate(bars):
        m, o, h, l, c, v = b
        if m < end_or:
            continue
        if m > cutoff:
            return None
        vw = pv / vv if vv else None
        up, dn = longs and h >= hi, shorts and l <= lo
        if up and not dn:
            px = max(hi, o)
            if (chase is None or px <= hi + chase * w) and (not vwap_on or vw is None or px > vw):
                return i, 1, px, hi, lo
        elif dn and not up:
            px = min(lo, o)
            if (chase is None or px >= lo - chase * w) and (not vwap_on or vw is None or px < vw):
                return i, -1, px, hi, lo
        pv += (h + l + c) / 3 * v
        vv += v
    return None


def run_exit(bars, i, side, px, hi, lo, atr, stop_rule, target_rule, flat):
    """Walk forward from the entry bar. Returns (stop, risk, exit, exit_type, exit_minute) or None."""
    stop = (hi + lo) / 2 if stop_rule == "mid" else px - side * stop_rule * atr
    risk = (px - stop) * side
    if risk <= max(0.01, px * 0.0005):  # stop too close to be real
        return None
    target = px + side * REWARD_RISK * risk if target_rule == "2R" else None
    for j in range(i, len(bars)):
        m, o, h, l, c, v = bars[j]
        if m >= flat:
            return stop, risk, o, "close", m
        if j == i:  # entry bar: we don't know the order of moves inside it - use its close
            if (c - stop) * side <= 0:
                return stop, risk, stop, "stop", m
            if target is not None and (c - target) * side >= 0:
                return stop, risk, target, "target", m
            continue
        if (o - stop) * side <= 0:
            return stop, risk, o, "stop", m          # gapped through the stop
        if target is not None and (o - target) * side >= 0:
            return stop, risk, o, "target", m
        if ((l if side > 0 else h) - stop) * side <= 0:
            return stop, risk, stop, "stop", m
        if target is not None and ((h if side > 0 else l) - target) * side >= 0:
            return stop, risk, target, "target", m
    m, o, h, l, c, v = bars[-1]
    return stop, risk, c, "close", m


def net_pnl(side, entry, exit_, exit_type, slip):
    e = entry * (1 + side * slip)
    x = exit_ if exit_type == "target" else exit_ * (1 - side * slip)  # targets are limit orders
    return (x - e) * side


# ---------------- per-day selection ----------------
class History:
    """Rolling per-symbol history needed for ATR and relative volume."""

    def __init__(self):
        self.daily = defaultdict(lambda: deque(maxlen=15))           # (h, l, c, v)
        self.or_vol = defaultdict(lambda: defaultdict(lambda: deque(maxlen=14)))  # k -> volumes

    def atr(self, s):
        d = list(self.daily[s])
        if len(d) < 15:
            return None
        trs = [max(h - l, abs(h - d[i][2]), abs(l - d[i][2])) for i, (h, l, c, v) in enumerate(d[1:])]
        return sum(trs) / len(trs)

    def add_day(self, s, bars):
        self.daily[s].append((max(b[2] for b in bars), min(b[3] for b in bars), bars[-1][4],
                              sum(b[5] for b in bars)))
        for k in (5, 15):
            self.or_vol[s][k].append(sum(b[5] for b in bars if b[0] < OPEN_MIN + k))


def select(day, hist, k, how):
    """Today's trading list for an entry style: (symbol, score) best first."""
    rows = []
    for s, bars in day.items():
        d = hist.daily[s]
        atr = hist.atr(s)
        if not d or atr is None:
            continue
        prev_c, prev_v = d[-1][2], d[-1][3]
        orb = [b for b in bars if b[0] < OPEN_MIN + k]
        if len(orb) < max(3, k // 3):
            continue
        hi, lo, last = max(b[2] for b in orb), min(b[3] for b in orb), orb[-1][4]
        vol = sum(b[5] for b in orb)
        if how == "ours":  # same formula as bot/universe.py
            width = (hi - lo) / last
            if prev_c < V2["min_price"] or not (V2["min_range"] <= width <= V2["max_range"]):
                continue
            relvol = vol / max(prev_v * k / 390, 1)
            gap = orb[0][1] / prev_c - 1
            rows.append((relvol * (1 + 10 * abs(gap)), s))
        else:  # paper: price > $5, avg volume >= 1M, ATR > $0.50, relvol >= 1 vs same window, top 20
            hist_or = hist.or_vol[s][k]
            avg_daily_vol = sum(x[3] for x in d) / len(d)
            if len(hist_or) < 14 or orb[0][1] <= 5 or avg_daily_vol < 1e6 or atr <= 0.5:
                continue
            base = sum(hist_or) / len(hist_or)
            relvol = vol / base if base else 0
            if relvol >= 1:
                rows.append((relvol, s))
    rows.sort(reverse=True)
    n = V2["universe"] if how == "ours" else 20
    return [(s, sc) for sc, s in rows[:n]]


# ---------------- portfolio ----------------
def group_of(s):
    return next((g for g, names in C.GROUPS.items() if s in names), None)


def portfolio(trades, days, slipped):
    """Replay trades with the bot's limits. Returns list of (date, equity, day_pnl)."""
    by_day = defaultdict(list)
    for t in trades:
        by_day[t["date"]].append(t)
    eq, curve = START_EQUITY, []
    for d in days:
        pnl, open_ = 0.0, []
        for t in sorted(by_day.get(d, []), key=lambda t: (t["t_in"], -t["score"])):
            open_ = [o for o in open_ if o[0] > t["t_in"]]
            if len(open_) >= C.MAX_OPEN_POSITIONS:
                continue
            if sum(1 for o in open_ if o[1] == t["side"]) >= C.MAX_PER_SIDE:
                continue
            g = group_of(t["symbol"])
            if g and any(o[1] == t["side"] and o[2] == g for o in open_):
                continue
            room = max(0.0, eq * C.MAX_GROSS_EXPOSURE - sum(o[3] for o in open_))
            qty = math.floor(min(eq * C.RISK_PER_TRADE / t["risk"], eq * C.MAX_POSITION_PCT / t["entry"],
                                 room / t["entry"]))
            if qty < 1:
                continue
            pnl += qty * (t["pnl_net"] if slipped else t["pnl_gross"])
            open_.append((t["t_out"], t["side"], g, qty * t["entry"]))
        eq += pnl
        curve.append((d, eq, pnl))
    return curve


# ---------------- stats ----------------
def trade_stats(ts, key):
    if not ts:
        return {"trades": 0}
    rs = [t[key] for t in ts]
    wins = [r for r in rs if r > 0]
    ex = defaultdict(int)
    for t in ts:
        ex[t["exit_type"]] += 1
    n = len(ts)
    sd = statistics.pstdev(rs) if n > 1 else 0
    return {"trades": n, "hit": len(wins) / n * 100, "avg_r": sum(rs) / n, "total_r": sum(rs),
            "t": (sum(rs) / n) / (sd / math.sqrt(n)) if sd else 0,
            "stop%": ex["stop"] / n * 100, "target%": ex["target"] / n * 100, "close%": ex["close"] / n * 100}


def curve_stats(curve):
    if not curve:
        return {}
    start = curve[0][1] - curve[0][2]
    rets, peak, mdd = [], start, 0.0
    prev = start
    for d, eq, pnl in curve:
        rets.append(pnl / prev if prev else 0)
        prev = eq
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    sd = statistics.pstdev(rets) if len(rets) > 1 else 0
    return {"return%": (curve[-1][1] / start - 1) * 100,
            "sharpe": (sum(rets) / len(rets)) / sd * math.sqrt(252) if sd else 0,
            "maxdd%": mdd * 100, "green%": sum(1 for r in rets if r > 0) / len(rets) * 100}


# ---------------- main ----------------
def main():
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=round(MONTHS * 30.44))
    warm = start - timedelta(days=40)  # ~25 trading days to fill ATR / relative-volume history
    cal = calendar(warm, end)
    symbols = sorted(s for s in universe.CORE if s not in C.EXCLUDE)
    feed = FEED
    print(f"Backtest {start} -> {end}: {len(symbols)} symbols, {len(cal)} sessions incl. warm-up, "
          f"feed {feed}, slippage {SLIP * 1e4:.1f} bps/side", flush=True)

    hist = History()
    trades = defaultdict(list)            # variant -> trades
    days, spy = [], []
    t_start = time.time()
    for n, (d, close_min) in enumerate(cal):
        try:
            bars = day_bars(symbols, d, close_min, feed)
        except RuntimeError as e:
            if feed == "sip" and "403" in str(e):
                print(f"SIP history not allowed on this plan ({e}); switching to IEX", flush=True)
                feed = "iex"
                bars = day_bars(symbols, d, close_min, feed)
            else:
                raise
        bars = {s: b for s, b in bars.items() if len(b) >= 30}
        flat = min(15 * 60 + 45, close_min - 15)  # 15:45, or 15 min before an early close
        cutoff = min(14 * 60 + 30, close_min - 90)
        if date.fromisoformat(d) >= start:
            days.append(d)
            if "SPY" in bars:
                spy.append((d, bars["SPY"][-1][4]))
            for ename, (k, direction, vwap_on, chase, how) in ENTRIES.items():
                for s, score in select(bars, hist, k, how):
                    ent = find_entry(bars[s], k, direction, vwap_on, chase, cutoff)
                    if not ent:
                        continue
                    i, side, px, hi, lo = ent
                    atr = hist.atr(s)
                    for stop_rule in STOPS:
                        for tgt in TARGETS:
                            r = run_exit(bars[s], i, side, px, hi, lo, atr, stop_rule, tgt, flat)
                            if not r:
                                continue
                            stop, risk, exit_, how_out, m_out = r
                            g = net_pnl(side, px, exit_, how_out, 0.0)
                            nt = net_pnl(side, px, exit_, how_out, SLIP)
                            trades[(ename, stop_rule, tgt)].append({
                                "date": d, "symbol": s, "side": side, "score": score,
                                "t_in": bars[s][i][0], "t_out": m_out, "entry": px, "stop": stop,
                                "risk": risk, "exit": exit_, "exit_type": how_out,
                                "pnl_gross": g, "pnl_net": nt, "r_gross": g / risk, "r_net": nt / risk,
                                "risk_pct": risk / px * 100})
        for s, b in bars.items():
            hist.add_day(s, b)
        if n % 20 == 0:
            print(f"  {d}: {n + 1}/{len(cal)} sessions, {time.time() - t_start:.0f}s", flush=True)

    write_report(trades, days, spy, feed)


def fmt(x, nd=2, pct=False):
    if x is None:
        return "-"
    return f"{x:+.{nd}f}{'%' if pct else ''}" if isinstance(x, float) else str(x)


def write_report(trades, days, spy, feed):
    OUT.mkdir(parents=True, exist_ok=True)
    cut = days[int(len(days) * 2 / 3)] if days else ""
    train_days = [d for d in days if d < cut]
    test_days = [d for d in days if d >= cut]
    rows = []
    curves = {}
    for v, ts in trades.items():
        tr = [t for t in ts if t["date"] < cut]
        te = [t for t in ts if t["date"] >= cut]
        row = {"variant": variant_name(*v), "key": v}
        for label, subset, dd in (("all", ts, days), ("train", tr, train_days), ("test", te, test_days)):
            st_n = trade_stats(subset, "r_net")
            st_g = trade_stats(subset, "r_gross")
            cv = portfolio(subset, dd, slipped=True)
            cs = curve_stats(cv)
            if label == "all":
                curves[v] = cv
            row[label] = {"net": st_n, "gross": st_g, "port": cs,
                          "avg_risk%": statistics.mean(t["risk_pct"] for t in subset) if subset else None}
        rows.append(row)
    rows.sort(key=lambda r: r["train"]["port"].get("sharpe", -99), reverse=True)

    # results.csv
    with (OUT / "results.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant", "period", "trades", "hit%", "avg_R_net", "avg_R_gross", "total_R_net", "t_stat",
                    "stop%", "target%", "close%", "avg_stop_dist%", "port_return%", "sharpe", "maxdd%", "green_days%"])
        for r in rows:
            for p in ("all", "train", "test"):
                n, g, pt = r[p]["net"], r[p]["gross"], r[p]["port"]
                if not n.get("trades"):
                    continue
                w.writerow([r["variant"], p, n["trades"], round(n["hit"], 1), round(n["avg_r"], 3),
                            round(g["avg_r"], 3), round(n["total_r"], 1), round(n["t"], 2), round(n["stop%"], 1),
                            round(n["target%"], 1), round(n["close%"], 1), round(r[p]["avg_risk%"], 2),
                            round(pt.get("return%", 0), 2), round(pt.get("sharpe", 0), 2),
                            round(pt.get("maxdd%", 0), 2), round(pt.get("green%", 0), 1)])

    with gzip.open(OUT / "trades.csv.gz", "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant", "date", "symbol", "side", "entry_min", "exit_min", "entry", "stop", "exit",
                    "exit_type", "risk_pct", "r_gross", "r_net"])
        for v, ts in trades.items():
            for t in ts:
                w.writerow([variant_name(*v), t["date"], t["symbol"], "long" if t["side"] > 0 else "short",
                            t["t_in"], t["t_out"], round(t["entry"], 4), round(t["stop"], 4), round(t["exit"], 4),
                            t["exit_type"], round(t["risk_pct"], 3), round(t["r_gross"], 3), round(t["r_net"], 3)])

    spy_ret = (spy[-1][1] / spy[0][1] - 1) * 100 if len(spy) > 1 else None
    plot(curves, rows, spy)

    L = [f"# Backtest: {days[0]} to {days[-1]} ({len(days)} trading days)", "",
         f"- Universe: the bot's core list ({len(set(t['symbol'] for ts in trades.values() for t in ts))} symbols traded), "
         f"1-minute bars from the `{feed}` feed.",
         f"- Costs: {SLIP * 1e4:.0f} bps slippage per side on market fills (targets fill at their limit).",
         f"- **Train** = {train_days[0]} to {train_days[-1]} ({len(train_days)} days). "
         f"**Test** = {test_days[0]} to {test_days[-1]} ({len(test_days)} days). "
         "Rule sets are ranked on train only; test is the honest check.",
         f"- Portfolio = the bot's real limits (0.5% risk/trade, 5 positions, 3 per side, 20%/position, "
         f"150% gross, one per group per side), starting at $100k. SPY buy & hold over the whole period: "
         f"{fmt(spy_ret, 1, True)}.",
         "- R = profit divided by the trade's initial risk (entry to stop). +0.10R/trade is a real edge; "
         "t-stat above ~2 means it's unlikely to be luck.", "",
         "## Ranked by train-period Sharpe", "",
         "| # | Rule set | Train Sharpe | Train return | **Test Sharpe** | **Test return** | Test avg R (net) | "
         "Test hit % | Trades/day | Avg stop distance |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        tr, te = r["train"], r["test"]
        mark = " (current bot = paper recipe)" if r["key"] == CURRENT else " (old v2 rules)" if r["key"] == V2_RULES else ""
        tpd = r["all"]["net"].get("trades", 0) / max(len(days), 1)
        L.append(f"| {i} | {r['variant']}{mark} | {tr['port'].get('sharpe', 0):.2f} | "
                 f"{tr['port'].get('return%', 0):+.1f}% | **{te['port'].get('sharpe', 0):.2f}** | "
                 f"**{te['port'].get('return%', 0):+.1f}%** | {te['net'].get('avg_r', 0):+.3f} | "
                 f"{te['net'].get('hit', 0):.0f}% | {tpd:.1f} | {r['all']['avg_risk%'] or 0:.2f}% |")
    L += ["", "## How trades ended (whole period)", "",
          "| Rule set | Trades | Avg R gross | Avg R net | t-stat (net) | Hit stop | Hit target | Held to close | "
          "Max drawdown |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a = r["all"]
        L.append(f"| {r['variant']} | {a['net'].get('trades', 0)} | {a['gross'].get('avg_r', 0):+.3f} | "
                 f"{a['net'].get('avg_r', 0):+.3f} | {a['net'].get('t', 0):.2f} | {a['net'].get('stop%', 0):.0f}% | "
                 f"{a['net'].get('target%', 0):.0f}% | {a['net'].get('close%', 0):.0f}% | "
                 f"{a['port'].get('maxdd%', 0):.1f}% |")
    L += ["", "![Equity](equity.png)", "",
          "Limits: core list only (no historical top-mover lists), 1-minute bars, no dynamic correlation "
          "guard or daily loss limit. Files: `results.csv`, `trades.csv.gz`."]
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:12 + len(rows)]), flush=True)


def plot(curves, rows, spy):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(11, 5.5))
    show = [r["key"] for r in rows[:4]]
    for k in (CURRENT, V2_RULES):
        if k not in show and k in curves:
            show.append(k)
    for k in show:
        cv = curves.get(k)
        if cv:
            lw = 2.4 if k == CURRENT else 1.4
            ax.plot([datetime.fromisoformat(d) for d, _, _ in cv], [e for _, e, _ in cv],
                    lw=lw, label=variant_name(*k) + (" (current)" if k == CURRENT else ""))
    if len(spy) > 1:
        ax.plot([datetime.fromisoformat(d) for d, _ in spy], [START_EQUITY * c / spy[0][1] for _, c in spy],
                color="gray", ls="--", lw=1.2, label="SPY buy & hold")
    ax.axhline(START_EQUITY, color="black", lw=0.5)
    ax.set_title("Backtest equity, $100k start, with slippage")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "equity.png", dpi=110)


if __name__ == "__main__":
    main()
