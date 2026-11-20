"""Backtest: the live bot's rules on the WHOLE market (thousands of stocks, incl. $5-10 names).

This is the setup of the original research (Zarattini, Barbon & Aziz): every morning scan every
US stock, keep price >= $5, 14-day average volume >= 1M, ATR(14) >= $0.50, rank by relative volume
of the first 5 minutes vs the same 5 minutes over the last 14 sessions (needs >= 10, relvol >= 1),
and trade the top 20. Entry/exit = the live bot: first-candle direction, break of the 5-minute
range, skip if > 0.2 ATR past the edge, stop 10% of ATR away, skip if that stop is < 0.25% away,
hold to 15:45 (no target).

Costs are real: for every trade, the median all-exchange (SIP) bid-ask spread in the entry minute
is charged (half in, half out) plus BT_SLIPPAGE_BPS per side.

Portfolio = the live bot's limits (0.5% risk/trade, 5 positions, 3 per side, 20%/position, 150%
gross, 2.5% daily loss limit approximation) via backtest.portfolio.

Universe: Alpaca's active AND inactive (delisted) US equities, exchange-listed, no leveraged or
inverse funds. Delisted names are included where Alpaca still has their bars, which reduces (but
may not remove) survivorship bias.

Env: BT_END (YYYY-MM-DD, blank = yesterday), BT_MONTHS (12), BT_SLIPPAGE_BPS (3).
Writes data/backtest/wide/end-<date>/REPORT.md and trades.csv.
"""
import csv
import math
import os
import statistics
import time
from collections import defaultdict, deque
from datetime import date, timedelta

import alpaca
import config as C
import universe
import backtest as B
from backtest_small import daily_history, or_volume, spread_pct, atr14

MONTHS = int(os.getenv("BT_MONTHS", "12"))
SLIP = float(os.getenv("BT_SLIPPAGE_BPS", "3")) / 1e4
END = os.getenv("BT_END", "").strip()
TOP = 20
MIN_PRICE = 5.0
MIN_AVG_VOL = 1_000_000
MIN_ATR = 0.50


_base_get = B.get


def get(base, path, **params):
    """backtest.get with extra patience (parallel jobs share one API rate limit)."""
    for attempt in range(8):
        try:
            return _base_get(base, path, **params)
        except RuntimeError as e:
            if "gave up" not in str(e):
                raise
            time.sleep(30)
    return _base_get(base, path, **params)


B.get = get  # backtest_small's helpers call backtest.get through their own import; patch both
import backtest_small as S  # noqa: E402
S.get = get


def listed_symbols():
    out = set()
    for status in ("active", "inactive"):
        for a in get(alpaca.TRADE, "/v2/assets", status=status, asset_class="us_equity"):
            s = a["symbol"]
            if (a.get("exchange") in ("NYSE", "NASDAQ", "AMEX", "ARCA", "BATS")
                    and s.isalpha() and len(s) <= 5 and s not in C.EXCLUDE
                    and not universe.LEVERAGED.search(a.get("name", ""))):
                out.add(s)
    return sorted(out)


def main():
    end = date.fromisoformat(END) if END else date.today() - timedelta(days=1)
    start = end - timedelta(days=round(MONTHS * 30.44))
    warm = start - timedelta(days=45)
    out_dir = B.Path(__file__).resolve().parent.parent / "data" / "backtest" / "wide" / f"end-{end}"
    cal = B.calendar(warm, end)
    syms = listed_symbols()
    print(f"Wide backtest {start} -> {end}: {len(syms)} symbols (active + delisted), {len(cal)} sessions",
          flush=True)
    daily = daily_history(syms, warm, end)
    daily = {s: r for s, r in daily.items() if r}
    print(f"  {len(daily)} symbols have bars in the window", flush=True)
    dates = [d for d, _ in cal]
    or_hist = defaultdict(lambda: deque(maxlen=14))
    trades, t0, watched = [], time.time(), []
    spy = []

    for n, (d, close_min) in enumerate(cal):
        if "SPY" in daily and d in daily["SPY"] and date.fromisoformat(d) >= start:
            spy.append((d, daily["SPY"][d][2]))
        prev = [x for x in dates if x < d][-15:]
        if len(prev) < 15:
            continue
        cand = {}
        for s, rows in daily.items():
            if d not in rows:
                continue
            hist = [rows[x] for x in prev if x in rows]
            if len(hist) < 15:
                continue
            c = hist[-1][2]
            avgv = sum(r[3] for r in hist[-14:]) / 14
            if c >= 0.8 * MIN_PRICE and avgv >= 0.7 * MIN_AVG_VOL:  # wider watch band keeps relvol history
                cand[s] = (c, avgv, atr14(hist))
        vols = or_volume(sorted(cand), d)
        picks = []
        if date.fromisoformat(d) >= start:
            watched.append(len(cand))
            for s, (c, avgv, a) in cand.items():
                h = [v for v in or_hist[s] if v > 0]
                if c < MIN_PRICE or avgv < MIN_AVG_VOL or a is None or a < MIN_ATR or len(h) < 10:
                    continue
                rv = vols.get(s, 0) / (sum(h) / len(h))
                if rv >= 1:
                    picks.append((rv, s, a))
            picks.sort(reverse=True)
            picks = picks[:TOP]
        for s in cand:
            or_hist[s].append(vols.get(s, 0))
        if not picks:
            continue
        bars = B.day_bars([s for _, s, _ in picks], d, close_min, "sip")
        flat = min(15 * 60 + 45, close_min - 15)
        cutoff = min(14 * 60 + 30, close_min - 90)
        for rv, s, a in picks:
            b = bars.get(s, [])
            if len(b) < 30:
                continue
            ent = B.find_entry(b, 5, "candle", False, None, cutoff)
            if not ent:
                continue
            i, side, px, hi, lo = ent
            if px < MIN_PRICE or px - hi > C.MAX_CHASE_ATR * a or lo - px > C.MAX_CHASE_ATR * a:
                continue
            r = B.run_exit(b, i, side, px, hi, lo, a, C.STOP_ATR, "close", flat)
            if not r:
                continue
            stop, risk, ex, how, m_out = r
            if risk < max(0.01, px * C.MIN_STOP_PCT):
                continue
            sp = spread_pct(s, d, b[i][0])
            if sp is None:
                continue
            gross = (ex - px) * side
            cost = px * (sp + 2 * SLIP)
            trades.append({"date": d, "symbol": s, "side": side, "score": rv, "t_in": b[i][0], "t_out": m_out,
                           "entry": px, "stop": stop, "exit": ex, "exit_type": how, "risk": risk,
                           "risk_pct": risk / px * 100, "atr": a, "spread_pct": sp * 100,
                           "pnl_gross": gross - px * 2 * SLIP, "pnl_net": gross - cost,
                           "r_gross": gross / risk, "r_net": (gross - cost) / risk})
        if n % 10 == 0:
            print(f"  {d}: {n + 1}/{len(cal)} sessions, {len(cand)} watched, {len(trades)} trades, "
                  f"{time.time() - t0:.0f}s", flush=True)
    report(trades, start, end, spy, out_dir, watched, len(syms))


def stats(ts, key="r_net"):
    if not ts:
        return "0 trades"
    rs = [t[key] for t in ts]
    n, avg = len(rs), sum(rs) / len(rs)
    sd = statistics.pstdev(rs) if n > 1 else 0
    tstat = avg / (sd / math.sqrt(n)) if sd else 0
    return f"{n} · win {sum(r > 0 for r in rs) / n * 100:.0f}% · avg {avg:+.3f}R · t {tstat:+.1f}"


def account(ts, days):
    cv = B.portfolio(ts, days, slipped=True, loss_limit=True)
    cs = B.curve_stats(cv)
    return cs, cv


def report(trades, start, end, spy, out_dir, watched, n_syms):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "trades.csv", "w", newline="") as f:
        cols = ["date", "symbol", "side", "score", "t_in", "t_out", "entry", "stop", "exit", "exit_type",
                "risk_pct", "atr", "spread_pct", "r_gross", "r_net"]
        w = csv.writer(f)
        w.writerow(cols)
        for t in trades:
            w.writerow([t["date"], t["symbol"], "long" if t["side"] > 0 else "short"] +
                       [round(t[c], 4) if isinstance(t[c], float) else t[c] for c in cols[3:]])
    days = [d for d, _ in spy]
    spy_ret = (spy[-1][1] / spy[0][1] - 1) * 100 if len(spy) > 1 else float("nan")
    cut = days[len(days) * 2 // 3] if days else ""
    tight = lambda t: t["spread_pct"] <= 0.25
    longs = lambda t: t["side"] > 0
    sets = [
        ("All signals (live rules, whole market)", lambda t: True),
        ("Skip if spread > 0.25%", tight),
        ("Long only", longs),
        ("Long only, spread ≤ 0.25%", lambda t: longs(t) and tight(t)),
        ("Shorts only", lambda t: t["side"] < 0),
        ("$5-10 stocks", lambda t: t["entry"] < 10),
        ("$10-50 stocks", lambda t: 10 <= t["entry"] < 50),
        ("$50+ stocks", lambda t: t["entry"] >= 50),
    ]
    L = [f"# Whole-market backtest: {start} to {end}", "",
         f"- Universe: {n_syms} listed US stocks/ETFs (active + delisted), median {statistics.median(watched) if watched else 0:.0f} "
         f"liquid enough to watch each day; top {TOP} by opening relative volume traded.",
         f"- Live bot rules: first-candle direction, 5-min range break, don't chase > 0.2 ATR, 10% ATR stop, "
         f"min stop 0.25%, hold to 15:45, price ≥ ${MIN_PRICE:.0f}, ATR ≥ ${MIN_ATR:.2f}, avg volume ≥ 1M.",
         f"- Costs: real SIP bid-ask spread at entry (half in, half out) + {SLIP * 1e4:.0f} bps/side.",
         f"- Account: $100k with the live bot's limits (0.5% risk, 5 positions, 3/side, 20%/position, 150% gross, "
         f"2.5% daily loss limit).",
         f"- **SPY buy & hold: {spy_ret:+.1f}%**", "",
         "## As an account", "",
         "| Rules | Return | vs SPY | Sharpe | Max drawdown | Green days | Train return | Test return |",
         "|---|---|---|---|---|---|---|---|"]
    for name, f in sets:
        ts = [t for t in trades if f(t)]
        cs, _ = account(ts, days)
        tr, _ = account([t for t in ts if t["date"] < cut], [d for d in days if d < cut])
        te, _ = account([t for t in ts if t["date"] >= cut], [d for d in days if d >= cut])
        if not cs:
            continue
        L.append(f"| {name} | {cs['return%']:+.1f}% | {cs['return%'] - spy_ret:+.1f} | {cs['sharpe']:.2f} | "
                 f"{cs['maxdd%']:.1f}% | {cs['green%']:.0f}% | {tr.get('return%', 0):+.1f}% | {te.get('return%', 0):+.1f}% |")
    L += ["", f"Train = before {cut}, test = from {cut} on.", "",
          "## Per trade (R = profit / risk to the stop)", "",
          "| Set | Before costs | After spread + slippage |", "|---|---|---|"]
    for name, f in sets:
        ts = [t for t in trades if f(t)]
        L.append(f"| {name} | {stats(ts, 'r_gross')} | {stats(ts)} |")
    L += ["", "## By entry spread", "", "| Spread | After costs |", "|---|---|"]
    for a, b in [(0, 0.05), (0.05, 0.1), (0.1, 0.25), (0.25, 0.5), (0.5, 100)]:
        L.append(f"| {a}–{b if b < 100 else '∞'}% | {stats([t for t in trades if a <= t['spread_pct'] < b])} |")
    by_m = defaultdict(list)
    for t in trades:
        by_m[t["date"][:7]].append(t["r_net"])
    L += ["", "## Net R by month", "", "| Month | Trades | Net R |", "|---|---|---|"]
    L += [f"| {m} | {len(v)} | {sum(v):+.1f} |" for m, v in sorted(by_m.items())]
    if trades:
        top = sorted((t["r_net"] for t in trades), reverse=True)
        L += ["", f"Top 20 trades: {sum(top[:20]):+.1f}R of {sum(top):+.1f}R total. "
                  f"Median entry spread {statistics.median(t['spread_pct'] for t in trades):.3f}%."]
    L += ["", "Caveats: no AI news filter, no correlation guard; 1-minute bars; spread measured at entry and "
              "reused for the exit; size could move a thin stock more than the spread; halts not modelled."]
    (out_dir / "REPORT.md").write_text("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
