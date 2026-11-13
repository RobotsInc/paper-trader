"""Builds SCORECARD.md (and data/equity.png) from the bot's logs."""
import csv
import json
from pathlib import Path

import config as C

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _read(name):
    p = DATA / name
    if not p.exists():
        return []
    with p.open() as f:
        return list(csv.DictReader(f))


def _money(x):
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def _smallcap_section():
    """Small-cap experiment ($5-10 names, tracked not traded) + real spreads vs our cost assumption."""
    small, spreads = _read("smallcap.csv"), _read("spreads.csv")
    out = ["", "## Small-cap experiment ($5-$10 stocks: tracked, not traded)", ""]
    main_sp = [float(x["spread_pct"]) for x in spreads if x["tier"] == "main" and x["spread_pct"]]
    small_sp = [float(x["spread_pct"]) for x in spreads if x["tier"] == "small" and x["spread_pct"]]
    assumed = 2 * getattr(C, "EST_SLIPPAGE_BPS", 3) / 100
    if main_sp:
        out.append(f"Real bid-ask spread at signal time, main list: median **{_median(main_sp):.3f}%** over "
                   f"{len(main_sp)} signals (the backtest assumed {assumed:.2f}% round trip).")
    if not small:
        out.append("No small-cap signals logged yet." if not main_sp else "")
        return out
    g = [float(x["r_gross"]) for x in small if x["r_gross"] != ""]
    n = [float(x["r_after_spread"]) for x in small if x["r_after_spread"] != ""]
    out += [f"Real spread, small caps: median **{_median(small_sp):.3f}%**." if small_sp else "",
            "",
            "| | Signals | Avg R before costs | Avg R after the spread | Won (after spread) |",
            "|---|---|---|---|---|",
            f"| $5-$10 stocks | {len(small)} | {sum(g) / len(g):+.3f} | "
            + (f"{sum(n) / len(n):+.3f} | {sum(1 for x in n if x > 0)}/{len(n)} |" if n else "- | - |"),
            "",
            "R = profit as a multiple of the risk to the stop. Positive after the spread over 50+ signals "
            "would justify trading this tier; until then it's just watched."]
    return out


def build():
    days, trades, shadow = _read("daily.csv"), _read("trades.csv"), _read("shadow.csv")
    state = json.loads((DATA / "state.json").read_text()) if (DATA / "state.json").exists() else {}
    inc = state.get("inception", {})

    out = ["# Paper Trader Scorecard", "",
           "_Simulated money only. Updated automatically after each trading day. Live view: the dashboard link in the README._", ""]
    if not days or not inc:
        out.append("No completed trading days yet. Check back after the first market close.")
        (ROOT / "SCORECARD.md").write_text("\n".join(out) + "\n")
        return

    start_eq = float(inc["equity"])
    end_eq = float(days[-1]["end_equity"])
    bot_ret = (end_eq / start_eq - 1) * 100
    spy_last = next((float(d["spy_close"]) for d in reversed(days) if d["spy_close"]), None)
    spy_ret = (spy_last / float(inc["spy"]) - 1) * 100 if spy_last else None

    curve = [start_eq] + [float(d["end_equity"]) for d in days]
    peak, max_dd = curve[0], 0.0
    for v in curve:
        peak = max(peak, v)
        max_dd = min(max_dd, (v / peak - 1) * 100)

    pnls = [float(t["pnl"]) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) else None
    day_pnls = [float(d["pnl"]) for d in days]
    side_of = lambda t: t.get("side") or "long"
    by_side = {}
    for side in ("long", "short"):
        ps = [float(t["pnl"]) for t in trades if side_of(t) == side]
        by_side[side] = {"trades": len(ps), "pnl": round(sum(ps), 2),
                         "win_rate": round(sum(1 for x in ps if x > 0) / len(ps) * 100, 1) if ps else None}
    blocked_rows = [x for x in shadow if x["action"] == "blocked_by_ai"]
    # Paper fills are perfect. Estimate real-money slippage on every entry and exit.
    bps = getattr(C, "EST_SLIPPAGE_BPS", 3) / 1e4
    est_cost = sum(abs(float(t["qty"])) * (float(t["entry"]) + float(t["exit"])) * bps for t in trades)
    after_cost_ret = ((end_eq - est_cost) / start_eq - 1) * 100
    (DATA / "summary.json").write_text(json.dumps({
        "days": len(days), "start_equity": start_eq, "end_equity": end_eq,
        "return_pct": round(bot_ret, 3), "spy_return_pct": round(spy_ret, 3) if spy_ret is not None else None,
        "trades": len(pnls), "win_rate": round(len(wins) / len(pnls) * 100, 1) if pnls else None,
        "avg_win": round(sum(wins) / len(wins), 2) if wins else None,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else None,
        "profit_factor": round(pf, 2) if pf else None, "max_drawdown_pct": round(max_dd, 2),
        "best_day": max(day_pnls), "worst_day": min(day_pnls),
        "green_days": sum(1 for x in day_pnls if x > 0), "by_side": by_side,
        "est_slippage": round(est_cost, 2), "return_after_slippage_pct": round(after_cost_ret, 3),
        "ai_blocked": len(blocked_rows),
        "ai_blocked_pnl": round(sum(float(x["pnl"]) for x in blocked_rows), 2),
    }, indent=1))

    verdict = ""
    if spy_ret is not None:
        diff = bot_ret - spy_ret
        verdict = f"**{'Beating' if diff > 0 else 'Trailing'} buy-and-hold SPY by {abs(diff):.2f} points.**"
    if len(days) < 20:
        verdict += f" Only {len(days)} trading day(s) so far - too early to judge (wait for 20+)."

    out += [
        f"Since {inc['date']} - {len(days)} trading day(s)", "", verdict, "",
        "| | Bot | Buy & hold SPY |", "|---|---|---|",
        f"| Return | {bot_ret:+.2f}% | {spy_ret:+.2f}% |" if spy_ret is not None else f"| Return | {bot_ret:+.2f}% | n/a |",
        f"| Equity | {_money(end_eq)} | {_money(start_eq * (1 + spy_ret / 100)) if spy_ret is not None else 'n/a'} |",
        "", "## Stats", "",
        "| Metric | Value |", "|---|---|",
        f"| Total P&L | {_money(end_eq - start_eq)} |",
        f"| P&L after est. slippage ({bps * 1e4:.0f} bps/side, what real money might see) | "
        f"{_money(end_eq - start_eq - est_cost)} ({after_cost_ret:+.2f}%) |",
        f"| Trades | {len(pnls)} |",
        f"| Win rate | {len(wins) / len(pnls) * 100:.0f}% |" if pnls else "| Win rate | n/a |",
        f"| Avg win / avg loss | {_money(sum(wins) / len(wins)) if wins else 'n/a'} / {_money(sum(losses) / len(losses)) if losses else 'n/a'} |",
        f"| Profit factor | {pf:.2f} |" if pf else "| Profit factor | n/a |",
        f"| Max drawdown | {max_dd:.2f}% |",
        f"| Best / worst day | {_money(max(day_pnls))} / {_money(min(day_pnls))} |",
        f"| Green days | {sum(1 for p in day_pnls if p > 0)} of {len(day_pnls)} |",
        f"| Longs | {by_side['long']['trades']} trades, {_money(by_side['long']['pnl'])} |",
        f"| Shorts | {by_side['short']['trades']} trades, {_money(by_side['short']['pnl'])} |",
    ]

    blocked = [s for s in shadow if s["action"] == "blocked_by_ai"]
    out += ["", "## Is the AI news filter helping?", ""]
    if blocked:
        bp = sum(float(s["pnl"]) for s in blocked)
        effect = f"saved {_money(-bp)}" if bp < 0 else f"cost {_money(bp)} in missed profit"
        out.append(f"The AI blocked {len(blocked)} trade(s) the rules wanted. "
                   f"Simulated outcome of those trades: {_money(bp)} -> the filter has **{effect}**.")
    else:
        out.append("No trades blocked by the AI yet.")

    out += _smallcap_section()

    if _chart(days, inc, start_eq) or (DATA / "equity.png").exists():
        out += ["", "![Equity vs SPY](data/equity.png)"]

    out += ["", "## Recent days", "", "| Date | P&L | Bot % | SPY % | Trades | AI blocked |",
            "|---|---|---|---|---|---|"]
    for d in reversed(days[-10:]):
        out.append(f"| {d['date']} | {_money(float(d['pnl']))} | {float(d['pnl_pct']):+.2f}% | "
                   f"{(float(d['spy_pct']) if d['spy_pct'] else 0):+.2f}% | {d['trades']} | {d['ai_blocked']} |")

    if trades:
        out += ["", "## Recent trades", "", "| Date | Symbol | Side | Qty | Entry | Exit | P&L |",
                "|---|---|---|---|---|---|---|"]
        for t in reversed(trades[-15:]):
            out.append(f"| {t['date']} | {t['symbol']} | {side_of(t)} | {float(t['qty']):g} | {t['entry']} | "
                       f"{t['exit']} | {_money(float(t['pnl']))} |")

    (ROOT / "SCORECARD.md").write_text("\n".join(out) + "\n")


def _chart(days, inc, start_eq):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    dates = [inc["date"]] + [d["date"] for d in days]
    bot = [start_eq] + [float(d["end_equity"]) for d in days]
    spy = [start_eq] + [start_eq * float(d["spy_close"]) / float(inc["spy"]) if d["spy_close"] else None
                        for d in days]
    fig, ax = plt.subplots(figsize=(9, 4), dpi=110)
    ax.plot(dates, bot, label="Bot", color="#2563eb", linewidth=2)
    ax.plot(dates, spy, label="Buy & hold SPY", color="#9ca3af", linewidth=2, linestyle="--")
    ax.set_ylabel("Equity ($)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    step = max(1, len(dates) // 8)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels(dates[::step], rotation=30, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(DATA / "equity.png")
    plt.close(fig)
    return True


if __name__ == "__main__":
    build()
