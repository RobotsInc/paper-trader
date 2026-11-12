"""Writes data/live.json - everything the terminal dashboard (docs/index.html) shows."""
import csv
import json
from datetime import datetime
from pathlib import Path

import alpaca

DATA = Path(__file__).resolve().parent.parent / "data"


def _csv(name):
    p = DATA / name
    if not p.exists():
        return []
    with p.open() as f:
        return list(csv.DictReader(f))


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def write(state, now, is_open):
    acct = alpaca.account()
    positions = alpaca.positions()
    equity = float(acct["equity"])
    start = state.get("start_equity") or equity
    inc = state.get("inception", {})
    today = state.get("date", "")
    entered = {s["symbol"]: s for s in state.get("signals", []) if s.get("action") == "entered"}
    held = {p["symbol"]: p for p in positions}
    decisions = (state.get("ai") or {}).get("decisions", {})
    prices = state.get("last_prices", {})
    spy_now = (state.get("regime") or {}).get("spy") or prices.get("SPY")

    pos_rows = []
    for p in positions:
        sig = entered.get(p["symbol"], {})
        pos_rows.append({
            "symbol": p["symbol"], "side": p.get("side", "long"), "qty": abs(_num(p["qty"]) or 0),
            "entry": _num(p["avg_entry_price"]), "price": _num(p.get("current_price")),
            "upl": _num(p.get("unrealized_pl")), "upl_pct": (_num(p.get("unrealized_plpc")) or 0) * 100,
            "value": abs(_num(p.get("market_value")) or 0),
            "stop": sig.get("stop"), "target": sig.get("target"), "opened": sig.get("time", "")[11:16],
        })

    sig_by_sym = {s["symbol"]: s for s in state.get("signals", [])}
    uni = []
    for sym, r in (state.get("ranges") or {}).items():
        px = prices.get(sym)
        d = decisions.get(sym, {})
        if sym in held:
            status = held[sym].get("side", "long").upper()
        elif sym in sig_by_sym:
            status = sig_by_sym[sym]["action"].replace("_", " ").upper()
        elif d.get("decision") == "block":
            status = "AI BLOCK"
        elif px and px > r["high"]:
            status = "ABOVE RANGE"
        elif px and px < r["low"]:
            status = "BELOW RANGE"
        else:
            status = "WATCH"
        uni.append({**r, "price": px, "status": status, "ai": d.get("decision", ""),
                    "catalyst": d.get("catalyst", "")})

    equity_today = [{"t": row["time"][11:16], "v": _num(row["equity"])}
                    for row in _csv("equity.csv") if row["time"].startswith(today)]

    summary = {}
    if (DATA / "summary.json").exists():
        summary = json.loads((DATA / "summary.json").read_text())

    live = {
        "updated": now.isoformat(timespec="seconds"),
        "date": today,
        "market_open": is_open,
        "account": {"equity": equity, "cash": _num(acct.get("cash")),
                    "buying_power": _num(acct.get("buying_power")),
                    "start_equity": start, "day_pnl": equity - start,
                    "day_pnl_pct": (equity / start - 1) * 100 if start else 0},
        "inception": inc,
        "total": {"pnl": equity - inc["equity"] if inc else None,
                  "pct": (equity / inc["equity"] - 1) * 100 if inc else None,
                  "spy_pct": (spy_now / inc["spy"] - 1) * 100 if inc and spy_now else None},
        "regime": state.get("regime", {}),
        "scan": state.get("scan", {}),
        "halted": state.get("halted", False),
        "ai": {"model": (state.get("ai") or {}).get("model"),
               "briefing": (state.get("ai") or {}).get("briefing", ""),
               "error": (state.get("ai") or {}).get("error"),
               "flags": [{"symbol": s, **d} for s, d in decisions.items() if d.get("decision") != "both"]},
        "positions": pos_rows,
        "universe": sorted(uni, key=lambda x: x.get("score", 0), reverse=True),
        "signals": list(reversed(state.get("signals", []))),
        "equity_today": equity_today,
        "days": _csv("daily.csv")[-30:],
        "trades": list(reversed(_csv("trades.csv")[-30:])),
        "summary": summary,
    }
    (DATA / "live.json").write_text(json.dumps(live, indent=1, default=str))
