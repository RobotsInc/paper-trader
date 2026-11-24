"""Replay the v2 engine over historical 1-minute bars (Alpaca free IEX data).

    python -m v2.backtest --month 2025-03 --out out/2025-03        # one month (needs Alpaca keys)
    python -m v2.backtest --aggregate out/* --report data/backtest_v2   # combine months into REPORT.md

Each trading day is replayed independently on a fresh $100,000 account with the real engine code (same bots,
same risk bot, same exit manager). Fills happen at bar prices; the report then subtracts the same modeled
slippage the live dashboard uses. No news bot (there is no historical headline feed in the free tier).
"""
import argparse
import calendar as _cal
import csv
import io
import statistics
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from v2 import config as C
from v2.engine import Engine
from v2.sim import SimBroker, SimEnv
from v2.util import ET, log, minute_index, parse_ts


# ---------------- data ----------------
def fetch(api, symbols, start, end):
    """{symbol: {date: [raw bar rows with _ts]}} for the regular session, from `start` to `end` (dates)."""
    s = (datetime.combine(start - timedelta(days=20), datetime.min.time(), tzinfo=ET)).astimezone(timezone.utc)
    e = (datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=ET)).astimezone(timezone.utc)
    raw = api.bars(list(symbols), s.strftime("%Y-%m-%dT%H:%M:%SZ"), e.strftime("%Y-%m-%dT%H:%M:%SZ"))
    out = {}
    for sym in symbols:
        days = defaultdict(list)
        for b in raw.get(sym, []):
            ts = parse_ts(b["t"])
            if 0 <= minute_index(ts) < 390:
                days[ts.date()].append(dict(b, _ts=ts))
        out[sym] = days
    return out


def densify(rows, nbars):
    """One bar per minute (IEX skips minutes with no trades): carry the last close forward."""
    by_idx = {minute_index(b["_ts"]): b for b in rows}
    out, last = [], None
    first = rows[0]["o"] if rows else 0
    for i in range(nbars):
        b = by_idx.get(i)
        if b:
            last = b["c"]
            out.append(b)
        else:
            px = last if last is not None else first
            ts = datetime(rows[0]["_ts"].year, rows[0]["_ts"].month, rows[0]["_ts"].day, 9, 30, tzinfo=ET) + timedelta(minutes=i)
            out.append({"t": "", "o": px, "h": px, "l": px, "c": px, "v": 0, "_ts": ts})
    return out


class HistBroker(SimBroker):
    """SimBroker's order/stop mechanics over real bars. The engine sees only the real (sparse) bars;
    internal marks use a dense one-bar-per-minute copy."""

    def __init__(self, env, data, day, nbars, equity=100000.0):
        self.env, self.day, self.nbars = env, day, nbars
        env.broker = self
        self.symbols = list(data)
        self.cash0, self.realized = equity, 0.0
        self.pos, self.orders, self.closed, self.oid, self.short_ok, self.cursor = {}, [], [], 0, True, None
        self.real = {s: [b for d in sorted(data[s]) for b in data[s][d] if d <= day] for s in self.symbols}
        self.bars_by_day = {s: {day: densify(data[s][day], nbars)} for s in self.symbols}
        self.advance(env.now())

    def calendar(self, start, end):
        close = datetime(self.day.year, self.day.month, self.day.day, 9, 30, tzinfo=ET) + timedelta(minutes=self.nbars)
        return [{"date": self.day.isoformat(), "open": "09:30", "close": close.strftime("%H:%M")}]

    def bars(self, symbols, start, end=None, timeframe="1Min"):
        st = datetime.fromisoformat(start.replace("Z", "+00:00"))
        en = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None
        now = self.env.now() - timedelta(seconds=1)
        out = {}
        for s in symbols:
            out[s] = [{k: v for k, v in b.items() if k != "_ts"} for b in self.real.get(s, [])
                      if b["_ts"] >= st and b["_ts"] <= now and (en is None or b["_ts"] <= en)]
        return out


# ---------------- replay ----------------
def replay(data, days, out_dir, scan_seconds=60):
    """Run the engine over each day; writes trades.csv / daily.csv under out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    old_dir, old_scan = C.DATA_DIR, C.SCAN_SECONDS
    C.DATA_DIR, C.SCAN_SECONDS = out_dir, scan_seconds
    try:
        for i, day in enumerate(days):
            spy = data["SPY"].get(day, [])
            if len(spy) < 100:
                log(f"{day}: skipped (SPY has {len(spy)} bars)")
                continue
            nbars = max(minute_index(b["_ts"]) for b in spy) + 1
            data_day = {s: v for s, v in data.items() if v.get(day)}
            env = SimEnv(day)
            broker = HistBroker(env, data_day, day, nbars)
            eng = Engine(broker, env, news_fn=lambda rows, now: ({}, ""), max_minutes=900, symbols=list(data_day))
            buf = io.StringIO()
            with redirect_stdout(buf):
                eng.run()
            n = sum(1 for _ in open(out_dir / "trades.csv")) - 1 if (out_dir / "trades.csv").exists() else 0
            print(f"[{i + 1}/{len(days)}] {day}: {n} trades so far", flush=True)
    finally:
        C.DATA_DIR, C.SCAN_SECONDS = old_dir, old_scan


def trading_days(data, start, end):
    ds = sorted(d for d in data.get("SPY", {}) if start <= d <= end)
    return [d for d in ds if len(data["SPY"][d]) >= 100]


# ---------------- aggregate ----------------
def _read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def aggregate(dirs, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    trades, daily = [], []
    for d in dirs:
        d = Path(d)
        if (d / "trades.csv").exists():
            trades += _read(d / "trades.csv")
        if (d / "daily.csv").exists():
            daily += _read(d / "daily.csv")
    trades.sort(key=lambda t: t["date"])
    daily.sort(key=lambda t: t["date"])
    if not daily:
        (out_dir / "REPORT.md").write_text("# v2 backtest\n\nNo data.\n")
        return
    f = float
    net = lambda t: f(t["pnl"]) - f(t["est_cost"])
    n = len(trades)
    gross = sum(f(t["pnl"]) for t in trades)
    cost = sum(f(t["est_cost"]) for t in trades)
    wins_g = [f(t["pnl"]) for t in trades if f(t["pnl"]) > 0]
    loss_g = [f(t["pnl"]) for t in trades if f(t["pnl"]) <= 0]
    wins_n = [net(t) for t in trades if net(t) > 0]
    loss_n = [net(t) for t in trades if net(t) <= 0]
    pf = lambda w, l: (sum(w) / -sum(l)) if l and sum(l) < 0 else float("inf")

    by_day = defaultdict(lambda: [0.0, 0.0, 0])      # date -> gross, cost, trades
    for t in trades:
        r = by_day[t["date"]]
        r[0] += f(t["pnl"]); r[1] += f(t["est_cost"]); r[2] += 1
    day_net = [(d["date"], by_day[d["date"]][0] - by_day[d["date"]][1]) for d in daily]
    cum, peak, dd, curve = 0.0, 0.0, 0.0, []
    for d, v in day_net:
        cum += v
        peak = max(peak, cum)
        dd = min(dd, cum - peak)
        curve.append((d, cum))
    start_eq = 100000.0
    vals = [v for _, v in day_net]
    sharpe = (statistics.mean(vals) / statistics.pstdev(vals) * (252 ** 0.5)) if len(vals) > 2 and statistics.pstdev(vals) > 0 else 0.0
    spy_first, spy_last = f(daily[0]["spy_open"]), f(daily[-1]["spy_close"])
    spy_ret = (spy_last / spy_first - 1) * 100 if spy_first else 0.0

    months = defaultdict(lambda: [0.0, 0.0, 0, 0])   # gross, cost, trades, wins(net)
    for t in trades:
        m = months[t["date"][:7]]
        m[0] += f(t["pnl"]); m[1] += f(t["est_cost"]); m[2] += 1; m[3] += 1 if net(t) > 0 else 0
    reasons = defaultdict(lambda: [0, 0.0])
    for t in trades:
        k = t["exit_reason"].split(" ")[0] + (" " + t["exit_reason"].split(" ")[1] if t["exit_reason"].startswith(("trailing", "stop", "time")) else "")
        reasons[k][0] += 1; reasons[k][1] += net(t)
    sides = {s: [t for t in trades if t["side"] == s] for s in ("long", "short")}

    bots = defaultdict(lambda: [0, 0, 0.0])
    for t in trades:
        side = 1 if t["side"] == "long" else -1
        for tok in t["votes"].split("|"):
            try:
                name, dr, _ = tok.split(":")
            except ValueError:
                continue
            if int(dr) == side:
                b = bots[name]; b[0] += 1; b[1] += 1 if net(t) > 0 else 0; b[2] += net(t)

    money = lambda v: ("-" if v < 0 else "") + "$" + f"{abs(v):,.0f}"
    L = []
    L.append(f"# v2 backtest: {daily[0]['date']} to {daily[-1]['date']}\n")
    L.append(f"{len(daily)} trading days, {n} trades. Each day replayed on a fresh $100,000 account with the real v2 engine.\n")
    L.append("## Result\n")
    L.append("| | Paper (perfect fills) | After est. slippage (\"if live\") |\n|---|---|---|")
    L.append(f"| Total P&L | {money(gross)} | {money(gross - cost)} |")
    L.append(f"| Return on $100k (not compounded) | {gross / start_eq * 100:+.2f}% | {(gross - cost) / start_eq * 100:+.2f}% |")
    L.append(f"| Win rate | {len(wins_g) / n * 100:.1f}% | {len(wins_n) / n * 100:.1f}% |")
    L.append(f"| Avg win / avg loss | {money(sum(wins_g) / max(1, len(wins_g)))} / {money(sum(loss_g) / max(1, len(loss_g)))} | {money(sum(wins_n) / max(1, len(wins_n)))} / {money(sum(loss_n) / max(1, len(loss_n)))} |")
    L.append(f"| Profit factor | {pf(wins_g, loss_g):.2f} | {pf(wins_n, loss_n):.2f} |")
    L.append(f"| Expectancy per trade | {money(gross / n)} | {money((gross - cost) / n)} |")
    L.append(f"\nEstimated costs: {money(cost)} ({cost / max(1, abs(gross)) * 100:.0f}% of gross P&L). Max drawdown (daily, after costs): {money(dd)}. "
             f"Green days: {sum(1 for v in vals if v > 0)} of {len(vals)}. Sharpe (daily, annualised): {sharpe:.2f}. "
             f"Best / worst day: {money(max(vals))} / {money(min(vals))}.\n")
    L.append(f"S&P 500 (SPY) over the same period: {spy_ret:+.2f}%.\n")
    L.append("## By month\n\n| Month | Trades | Win rate (after costs) | Paper P&L | Costs | After costs |\n|---|---|---|---|---|---|")
    for k in sorted(months):
        g, c, c_n, w = months[k]
        L.append(f"| {k} | {c_n} | {w / c_n * 100:.0f}% | {money(g)} | {money(-c)} | {money(g - c)} |")
    L.append("\n## Long vs short\n\n| Side | Trades | Win rate (after costs) | After costs |\n|---|---|---|---|")
    for s, ts in sides.items():
        if ts:
            L.append(f"| {s} | {len(ts)} | {sum(1 for t in ts if net(t) > 0) / len(ts) * 100:.0f}% | {money(sum(net(t) for t in ts))} |")
    L.append("\n## How trades ended\n\n| Exit | Trades | After costs |\n|---|---|---|")
    for k, (c_n, v) in sorted(reasons.items(), key=lambda kv: -kv[1][0]):
        L.append(f"| {k} | {c_n} | {money(v)} |")
    L.append("\n## Bot scorecard (trades each bot voted WITH)\n\n| Bot | Trades | Win rate (after costs) | Avg after costs |\n|---|---|---|---|")
    for k, (c_n, w, v) in sorted(bots.items(), key=lambda kv: -kv[1][0]):
        L.append(f"| {k} | {c_n} | {w / c_n * 100:.0f}% | {money(v / c_n)} |")
    L.append("""
## Read this before trusting any number above

- **Fills are idealised.** Entries/exits happen at bar prices (stops at the stop price). The "after costs" column subtracts a modeled 3 bps per side (more when the spread is wide); real fills on fast moves are often worse.
- **Free IEX data only** (about 2.5% of US volume). Prices are real, volume is thin and noisy, and historical bid/ask spreads are not available, so the liquidity filter saw a fixed 3 bps spread.
- **No news bot** in the backtest (no free historical headline feed), so the AI veto never fired.
- **Days are independent** ($100k each day, nothing compounds), and the bot weights restart each month.
- **The settings were not tuned on this period unless the run is labelled otherwise.** Adjusting them to improve these numbers makes this period in-sample.
- A backtest says what the rules would have done, not what they will do. Paper trading for a few weeks is the real test.
""")
    (out_dir / "REPORT.md").write_text("\n".join(L))
    for name, rows in (("trades.csv", trades), ("daily.csv", daily)):
        with open(out_dir / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    with open(out_dir / "daily_net.csv", "w") as fh:
        fh.write("date,net,cumulative\n")
        c = 0.0
        for d, v in day_net:
            c += v
            fh.write(f"{d},{v:.2f},{c:.2f}\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 3.6))
        ax.plot([d for d, _ in curve], [v for _, v in curve], color="#2f81f7")
        ax.axhline(0, color="#888", lw=0.8)
        ax.set_title("Cumulative P&L after est. costs ($100k per day, not compounded)")
        ax.set_xticks([d for d, _ in curve][:: max(1, len(curve) // 8)])
        ax.tick_params(axis="x", rotation=30, labelsize=8)
        fig.tight_layout()
        fig.savefig(out_dir / "equity.png", dpi=110)
    except Exception as e:  # noqa
        print("chart skipped:", e)
    print((out_dir / "REPORT.md").read_text()[:1500])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="YYYY-MM")
    ap.add_argument("--out")
    ap.add_argument("--aggregate", nargs="+")
    ap.add_argument("--report")
    ap.add_argument("--every", type=int, default=1, help="use every Nth trading day (speed-up)")
    ap.add_argument("--scan", type=int, default=60, help="seconds between scans in replay")
    a = ap.parse_args()
    if a.aggregate:
        aggregate(a.aggregate, a.report or "data/backtest_v2")
        return
    y, m = map(int, a.month.split("-"))
    start, end = date(y, m, 1), date(y, m, _cal.monthrange(y, m)[1])
    from v2.broker import AlpacaBroker
    api = AlpacaBroker()
    log(f"Fetching {a.month} bars for {len(C.WATCHLIST)} symbols...")
    data = fetch(api, C.WATCHLIST, start, end)
    days = trading_days(data, start, end)
    days = days[::max(1, a.every)]
    log(f"{len(days)} trading days (every {a.every})")
    replay(data, days, a.out, scan_seconds=a.scan)


if __name__ == "__main__":
    main()
