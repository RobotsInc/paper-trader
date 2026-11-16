"""Backtest: the $5-10 small-stock tier, if it traded.

Same rule as the live bot (the paper recipe): each morning take the $5-10 stocks with
14-day average volume >= 1M, rank by relative volume of the first 5 minutes vs the same window
over the last 14 sessions (needs >= 10 of them, relvol >= 1), keep the top 15. Trade each once
in the first candle's direction when it breaks the 5-minute range, stop 10% of ATR(14) away,
otherwise hold to 15:45.

Costs are the real part: for every trade we pull all-exchange (SIP) quotes for the entry minute
and charge the median bid-ask spread (half in, half out) plus slippage. Using the opening spread
for the exit too is conservative - spreads are usually tighter later in the day.

Universe: every stock Alpaca lists as active today (exchange-listed, no leveraged/inverse funds).
Stocks delisted during the year are missing (survivorship bias - flatters longs a little).

Run by .github/workflows/backtest_small.yml. Writes data/backtest/SMALLCAP.md and
data/backtest/smallcap_trades.csv.
"""
import csv
import math
import os
import statistics
import time
from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import alpaca
import universe
from backtest import ET, OPEN_MIN, get, calendar, day_bars, find_entry, run_exit

OUT = Path(__file__).resolve().parent.parent / "data" / "backtest"
MONTHS = int(os.getenv("BT_MONTHS", "12"))
SLIP = float(os.getenv("BT_SLIPPAGE_BPS", "3")) / 1e4
LO, HI = 5.0, 10.0
TOP = 15
MIN_AVG_VOL = 1_000_000
EQUITY = 100_000.0
RISK = 0.005
iso = lambda t: t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def listed_symbols():
    assets = get(alpaca.TRADE, "/v2/assets", status="active", asset_class="us_equity")
    out = []
    for a in assets:
        s = a["symbol"]
        if (a.get("tradable") and a.get("exchange") in ("NYSE", "NASDAQ", "AMEX", "ARCA", "BATS")
                and s.isalpha() and len(s) <= 5 and not universe.LEVERAGED.search(a.get("name", ""))):
            out.append(s)
    return sorted(out)


def daily_history(symbols, start, end):
    """{sym: {date: (h, l, c, v)}} from SIP daily bars."""
    out = defaultdict(dict)
    for i in range(0, len(symbols), 100):
        chunk, token = symbols[i:i + 100], None
        while True:
            p = dict(symbols=",".join(chunk), timeframe="1Day", start=start.isoformat(), end=end.isoformat(),
                     feed="sip", limit=10000, adjustment="split")
            if token:
                p["page_token"] = token
            j = get(alpaca.DATA, "/v2/stocks/bars", **p)
            for s, bl in (j.get("bars") or {}).items():
                for b in bl:
                    out[s][b["t"][:10]] = (b["h"], b["l"], b["c"], b["v"])
            token = j.get("next_page_token")
            if not token:
                break
        if i % 2000 == 0:
            print(f"  daily bars {i}/{len(symbols)}", flush=True)
    return out


def or_volume(symbols, d):
    """Volume in the first 5 minutes (SIP) for each symbol on day d."""
    t0 = datetime.fromisoformat(d + "T09:30").replace(tzinfo=ET)
    out = {}
    for i in range(0, len(symbols), 100):
        chunk, token = symbols[i:i + 100], None
        while True:
            p = dict(symbols=",".join(chunk), timeframe="1Min", start=iso(t0),
                     end=iso(t0 + timedelta(minutes=5) - timedelta(seconds=1)), feed="sip", limit=10000)
            if token:
                p["page_token"] = token
            j = get(alpaca.DATA, "/v2/stocks/bars", **p)
            for s, bl in (j.get("bars") or {}).items():
                out[s] = out.get(s, 0) + sum(b["v"] for b in bl)
            token = j.get("next_page_token")
            if not token:
                break
    return out


def spread_pct(symbol, d, minute):
    t = datetime.fromisoformat(d).replace(hour=minute // 60, minute=minute % 60, tzinfo=ET)
    try:
        j = get(alpaca.DATA, "/v2/stocks/quotes", symbols=symbol, start=iso(t), end=iso(t + timedelta(minutes=1)),
                feed="sip", limit=1000)
    except RuntimeError:
        return None
    qs = (j.get("quotes") or {}).get(symbol, [])
    sp = sorted((q["ap"] - q["bp"]) / ((q["ap"] + q["bp"]) / 2) for q in qs
                if q.get("bp", 0) > 0 and q.get("ap", 0) > q["bp"])
    return sp[len(sp) // 2] if sp else None


def atr14(rows):
    if len(rows) < 15:
        return None
    rows = rows[-15:]
    trs = [max(h - l, abs(h - rows[i][2]), abs(l - rows[i][2])) for i, (h, l, c, v) in enumerate(rows[1:])]
    return sum(trs) / len(trs)


def main():
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=round(MONTHS * 30.44))
    warm = start - timedelta(days=45)
    cal = calendar(warm, end)
    syms = listed_symbols()
    print(f"Small-cap backtest {start} -> {end}: {len(syms)} listed stocks, {len(cal)} sessions", flush=True)
    daily = daily_history(syms, warm, end)
    dates = [d for d, _ in cal]
    or_hist = defaultdict(lambda: deque(maxlen=14))
    trades, t0 = [], time.time()

    for n, (d, close_min) in enumerate(cal):
        prev = [x for x in dates if x < d][-15:]
        if len(prev) < 15:
            continue
        # Watch set: wide band so opening-volume history exists when a stock drifts into $5-10.
        cand = {}
        for s, rows in daily.items():
            hist = [rows[x] for x in prev if x in rows]
            if len(hist) < 15:
                continue
            c = hist[-1][2]
            avgv = sum(r[3] for r in hist[-14:]) / 14
            if 4.0 <= c <= 12.0 and avgv >= 0.7 * MIN_AVG_VOL:
                cand[s] = (c, avgv, atr14(hist))
        vols = or_volume(sorted(cand), d)
        picks = []
        if date.fromisoformat(d) >= start:
            for s, (c, avgv, a) in cand.items():
                h = [v for v in or_hist[s] if v > 0]
                if not (LO <= c < HI) or avgv < MIN_AVG_VOL or a is None or len(h) < 10:
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
        bars = day_bars([s for _, s, _ in picks], d, close_min, "sip")
        flat = min(15 * 60 + 45, close_min - 15)
        cutoff = min(14 * 60 + 30, close_min - 90)
        for rv, s, a in picks:
            b = bars.get(s, [])
            if len(b) < 30:
                continue
            ent = find_entry(b, 5, "candle", False, None, cutoff)
            if not ent:
                continue
            i, side, px, hi, lo = ent
            r = run_exit(b, i, side, px, hi, lo, a, 0.10, "close", flat)
            if not r:
                continue
            stop, risk, ex, how, m_out = r
            sp = spread_pct(s, d, b[i][0])
            if sp is None:
                continue
            cost = px * (sp + 2 * SLIP)  # half spread + slip on the way in, same on the way out
            gross = (ex - px) * side
            trades.append({"date": d, "symbol": s, "side": "long" if side > 0 else "short", "relvol": round(rv, 2),
                           "atr": round(a, 3), "t_in": b[i][0], "t_out": m_out, "entry": px, "stop": round(stop, 4),
                           "exit": ex, "exit_type": how, "risk_pct": round(risk / px * 100, 3),
                           "spread_pct": round(sp * 100, 4), "r_gross": round(gross / risk, 4),
                           "r_net": round((gross - cost) / risk, 4)})
        if n % 10 == 0:
            print(f"  {d}: {n + 1}/{len(cal)} sessions, {len(cand)} watched, {len(trades)} trades, "
                  f"{time.time() - t0:.0f}s", flush=True)
    report(trades, start, end)


def stats(ts, key="r_net"):
    if not ts:
        return "0 trades"
    rs = [t[key] for t in ts]
    n, avg = len(rs), sum(rs) / len(rs)
    sd = statistics.pstdev(rs) if n > 1 else 0
    tstat = avg / (sd / math.sqrt(n)) if sd else 0
    hit = sum(r > 0 for r in rs) / n * 100
    return f"{n} trades · win {hit:.0f}% · avg {avg:+.3f}R · t = {tstat:+.1f}"


def portfolio(ts, cap, atr_min=0.0, max_spread=None):
    """One small-stock position at a time, first breakout of the day first. Returns (return%, maxdd%, n)."""
    by_day = defaultdict(list)
    for t in ts:
        if t["atr"] >= atr_min and (max_spread is None or t["spread_pct"] <= max_spread):
            by_day[t["date"]].append(t)
    eq, peak, mdd, n = EQUITY, EQUITY, 0.0, 0
    for d in sorted(by_day):
        free_at = 0
        for t in sorted(by_day[d], key=lambda t: t["t_in"]):
            if t["t_in"] < free_at:
                continue
            risk = t["risk_pct"] / 100 * t["entry"]
            qty = math.floor(min(eq * RISK / risk, eq * cap / t["entry"]))
            if qty < 1:
                continue
            eq += qty * risk * t["r_net"]
            free_at, n = t["t_out"], n + 1
            peak = max(peak, eq)
            mdd = min(mdd, eq / peak - 1)
    return (eq / EQUITY - 1) * 100, mdd * 100, n


def report(trades, start, end):
    OUT.mkdir(parents=True, exist_ok=True)
    if trades:
        with open(OUT / "smallcap_trades.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(trades[0]))
            w.writeheader()
            w.writerows(trades)
    dates = sorted({t["date"] for t in trades})
    split = dates[len(dates) * 2 // 3] if dates else ""
    train = [t for t in trades if t["date"] < split]
    test = [t for t in trades if t["date"] >= split]
    live = [t for t in trades if t["atr"] >= 0.50]
    L = [f"# Small-stock ($5-10) backtest", "",
         f"{start} -> {end}. Paper recipe: top {TOP} by opening relative volume, 5-min range, first-candle "
         f"direction, 10% ATR stop, hold to 15:45. Costs: real median SIP bid-ask spread at entry (charged in and "
         f"out) + {SLIP * 1e4:.0f} bps slippage per side.", "",
         "## Per trade (R = profit / initial risk)", "",
         "| Set | Before costs | After spread + slippage |", "|---|---|---|"]
    for name, ts in [("All (no ATR floor)", trades), ("Live rules (ATR ≥ $0.50)", live),
                     ("Train (first 2/3)", train), ("Test (last 1/3)", test),
                     ("Longs", [t for t in trades if t["side"] == "long"]),
                     ("Shorts", [t for t in trades if t["side"] == "short"])]:
        L.append(f"| {name} | {stats(ts, 'r_gross')} | {stats(ts)} |")
    L += ["", "## By opening spread", "", "| Spread at entry | After costs |", "|---|---|"]
    for a, b in [(0, 0.1), (0.1, 0.25), (0.25, 0.5), (0.5, 1), (1, 100)]:
        L.append(f"| {a}–{b if b < 100 else '∞'}% | {stats([t for t in trades if a <= t['spread_pct'] < b])} |")
    if trades:
        L.append(f"\nMedian entry spread: {statistics.median(t['spread_pct'] for t in trades):.2f}%")
    L += ["", "## As an account ($100k, one small-stock position at a time, 0.5% risk)", "",
          "| Rules | Size cap | Return | Max drawdown | Trades taken |", "|---|---|---|---|---|"]
    for label, kw in [("All", {}), ("Live rules (ATR ≥ $0.50)", {"atr_min": 0.5}),
                      ("Skip if spread > 0.25%", {"max_spread": 0.25}),
                      ("ATR ≥ $0.50 and spread ≤ 0.25%", {"atr_min": 0.5, "max_spread": 0.25})]:
        for cap in (0.10, 0.20):
            r, dd, n = portfolio(trades, cap, **kw)
            L.append(f"| {label} | {cap:.0%} | {r:+.1f}% | {dd:.1f}% | {n} |")
    L += ["", "Caveats: stocks delisted during the year are missing; 1-minute bars; the spread is measured, but "
          "the fill could be worse on size in a thin stock; halts aren't modelled."]
    (OUT / "SMALLCAP.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
