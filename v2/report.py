"""Writes the files the dashboard reads (data/v2/): live.json, trades.csv, daily.csv, equity.csv, bots.json."""
import csv
import json
import os
import subprocess

from v2 import config as C
from v2 import orchestrator
from v2.bots import NAMES
from v2.util import log

TRADE_COLS = ["date", "symbol", "side", "qty", "entry", "exit", "pnl", "pnl_pct", "est_cost", "hold_min",
              "exit_reason", "score", "votes"]
DAILY_COLS = ["date", "start_equity", "end_equity", "pnl", "pnl_pct", "trades", "wins", "signals", "ai_blocked",
              "ai_blocked_pnl", "spy_open", "spy_close", "spy_pct", "longs", "shorts"]
EQUITY_COLS = ["time", "equity", "cash"]


def _dir():
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return C.DATA_DIR


def append_csv(name, cols, row):
    p = _dir() / name
    new = not p.exists() or p.stat().st_size == 0
    with open(p, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)


def read_csv(name):
    p = _dir() / name
    if not p.exists():
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def write_json(name, obj):
    tmp = _dir() / (name + ".tmp")
    tmp.write_text(json.dumps(obj))
    os.replace(tmp, _dir() / name)


def write_live(now, is_open, halted, acct, start_equity, positions, metas, equity_today, ai_briefing="", paused_note=""):
    equity = float(acct["equity"])
    rows = []
    for p in positions:
        m = metas.get(p["symbol"], {})
        qty, entry, price = abs(float(p["qty"])), float(p["avg_entry_price"]), float(p["current_price"])
        rows.append({"symbol": p["symbol"], "side": p["side"], "qty": qty, "entry": entry, "price": price,
                     "upl": float(p["unrealized_pl"]), "upl_pct": float(p.get("unrealized_plpc") or 0) * 100,
                     "value": qty * price, "stop": m.get("stop"), "target": None,
                     "opened": (m.get("opened") or "")[11:16]})
    write_json("live.json", {
        "version": "v2", "updated": now.isoformat(timespec="seconds"), "date": now.date().isoformat(),
        "market_open": is_open, "halted": halted,
        "account": {"equity": equity, "cash": float(acct["cash"]), "buying_power": float(acct.get("buying_power") or 0),
                    "start_equity": start_equity, "day_pnl": equity - start_equity,
                    "day_pnl_pct": (equity / start_equity - 1) * 100 if start_equity else 0.0},
        "positions": rows, "equity_today": equity_today, "briefing": ai_briefing, "note": paused_note})


def update_bots_json():
    """Per-bot scorecard from trades.csv: of the trades a bot voted WITH, how many won, and what they netted."""
    trades = read_csv("trades.csv")
    stats = {n: {"votes": 0, "wins": 0, "net": 0.0} for n in NAMES}
    for t in trades:
        side = 1 if t["side"] == "long" else -1
        net = float(t["pnl"]) - float(t.get("est_cost") or 0)
        for tok in (t.get("votes") or "").split("|"):
            try:
                name, d, conf = tok.split(":")
            except ValueError:
                continue
            if name in stats and int(d) == side:
                stats[name]["votes"] += 1
                stats[name]["wins"] += 1 if net > 0 else 0
                stats[name]["net"] += net
    out = []
    for n in NAMES:
        s = stats[n]
        kind = "ai" if n == "news" else "code"
        if n in ("volume", "liquidity", "risk", "exits"):
            out.append({"name": n, "type": kind, "role": "filter", "votes": None, "weight": None})
            continue
        hit = s["wins"] / s["votes"] if s["votes"] else None
        weight = 1.0
        if s["votes"] >= C.MIN_VOTES_FOR_WEIGHT and hit is not None:
            weight = round(min(1.5, max(0.25, 0.5 + hit)), 2)
        out.append({"name": n, "type": kind, "votes": s["votes"], "hit_rate": hit,
                    "avg_pnl_agree": (s["net"] / s["votes"]) if s["votes"] else None, "weight": weight})
    write_json("bots.json", {"updated": "", "bots": out})


def git_sync(msg="v2: data"):
    """Commit data/v2 and push (used by the GitHub job so the dashboard stays fresh)."""
    def run(*a):
        return subprocess.run(a, cwd=C.ROOT, capture_output=True, text=True)
    run("git", "config", "user.name", "paper-trader-bot")
    run("git", "config", "user.email", "paper-trader-bot@users.noreply.github.com")
    run("git", "add", "-A", "data/v2")
    if run("git", "diff", "--cached", "--quiet").returncode == 0:
        return
    run("git", "commit", "-q", "-m", msg)
    for _ in range(3):
        run("git", "pull", "-q", "--rebase", "-X", "theirs")
        if run("git", "push", "-q").returncode == 0:
            return
        run("git", "rebase", "--abort")
    log("git push failed (will retry)")
