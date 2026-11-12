"""Paper day-trading bot: opening-range breakout + optional AI news filter.

GitHub Actions runs this every ~5 minutes on weekdays. Each run:
  1. logs account equity,
  2. once a day, asks the AI filter which symbols to avoid,
  3. after 9:45 ET, buys breakouts above the 15-minute opening range
     (with a stop and profit target that Alpaca manages between runs),
  4. after 15:45 ET, closes everything and writes the day's results.

Usage: python bot/trader.py [run|flatten|report]
"""
import csv
import json
import math
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import alpaca
import config as C
import news_filter
import report

ET = ZoneInfo("America/New_York")
DATA = Path(__file__).resolve().parent.parent / "data"
STATE = DATA / "state.json"


# ---------- helpers ----------
def now_et():
    return datetime.now(ET)


def log(msg):
    print(f"[{now_et():%Y-%m-%d %H:%M:%S} ET] {msg}", flush=True)


def hm(s):
    h, m = map(int, s.split(":"))
    return time(h, m)


def et_dt(d, hhmm):
    return datetime.combine(date.fromisoformat(d), hm(hhmm), tzinfo=ET)


def utc_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    DATA.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2))


def append_csv(name, row):
    path = DATA / name
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)


def vwap(bars):
    vol = sum(b["v"] for b in bars)
    if not vol:
        return None
    return sum(b.get("vw", (b["h"] + b["l"] + b["c"]) / 3) * b["v"] for b in bars) / vol


# ---------- day lifecycle ----------
def start_new_day(state, today, equity):
    prev = state.get("date")
    if prev and state.get("session_seen") and not state.get("eod_done"):
        log(f"Finishing missed end-of-day summary for {prev}")
        end_of_day(state, prev)
    inception = state.get("inception")
    state.clear()
    state.update(date=today, start_equity=equity, ranges={},
                 ai={"done": False, "decisions": {}}, traded=[], signals=[],
                 halted=False, eod_done=False, session_seen=False)
    if inception:
        state["inception"] = inception


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "report":
        report.build()
        return

    state = load_state()
    now = now_et()
    today = now.date().isoformat()
    acct = alpaca.account()
    equity = float(acct["equity"])

    if "inception" not in state:
        spy = alpaca.latest_prices(["SPY"])["SPY"]
        state["inception"] = {"date": today, "equity": equity, "spy": spy}
        log(f"First run. Starting equity ${equity:,.2f}; SPY benchmark ${spy:.2f}")
    if state.get("date") != today:
        start_new_day(state, today, equity)

    if mode == "ai":  # re-run today's AI news filter (e.g. after it failed)
        state["ai"] = {"done": False, "decisions": {}}
        run_ai_filter(state, now)
        save_state(state)
        return

    is_open = alpaca.clock()["is_open"]
    try:
        if is_open:
            append_csv("equity.csv", {"time": now.isoformat(timespec="minutes"),
                                      "equity": round(equity, 2), "cash": acct["cash"]})
            if not state["session_seen"]:
                state["session_seen"] = True
                state["start_equity"] = equity
                if alpaca.positions():
                    log("Closing positions left over from a previous day")
                    alpaca.close_all()

        after_flatten = is_open and now.time() >= hm(C.FLATTEN_AT)
        after_close = not is_open and state["session_seen"]
        if mode == "flatten" or after_flatten or after_close:
            wrap_up(state, is_open)
        elif is_open:
            trade(state, now, equity)
        else:
            log("Market closed - nothing to do")
    finally:
        save_state(state)


def trade(state, now, equity):
    if state["halted"]:
        log("Halted for the day (daily loss limit)")
        return
    if equity <= state["start_equity"] * (1 - C.DAILY_LOSS_LIMIT):
        log("Daily loss limit hit - closing everything and stopping for today")
        alpaca.close_all()
        state["halted"] = True
        return

    if not state["ai"]["done"]:
        run_ai_filter(state, now)

    or_end = et_dt(state["date"], C.MARKET_OPEN) + timedelta(minutes=C.OPENING_RANGE_MIN)
    if now < or_end + timedelta(minutes=1):
        log("Waiting for the opening range to form")
        return
    if not state["ranges"]:
        state["ranges"] = compute_ranges(state["date"], or_end)
    if now.time() > hm(C.ENTRY_CUTOFF):
        log("Past entry cutoff - managing open trades only")
        return
    scan(state, now, equity)


def run_ai_filter(state, now):
    if not C.AI_FILTER:
        state["ai"] = {"done": True, "enabled": False, "decisions": {}}
        log("AI filter is off")
        return
    state["ai"] = news_filter.run(C.WATCHLIST, now)
    if state["ai"].get("error"):
        log(f"AI filter failed, trading on rules only: {state['ai']['error']}")
    for s, d in state["ai"]["decisions"].items():
        append_csv("ai_log.csv", {"date": state["date"], "symbol": s,
                                  "decision": d["decision"], "reason": d["reason"]})
        log(f"AI {d['decision']}s {s}: {d['reason']}")


def compute_ranges(d, or_end):
    start = et_dt(d, C.MARKET_OPEN)
    raw = alpaca.bars(C.WATCHLIST, utc_iso(start), utc_iso(or_end - timedelta(seconds=1)))
    ranges = {}
    for s in C.WATCHLIST:
        b = raw.get(s, [])
        if len(b) < C.MIN_RANGE_BARS:
            log(f"{s}: only {len(b)} bars in opening range - skipping today")
            continue
        ranges[s] = {"high": max(x["h"] for x in b), "low": min(x["l"] for x in b)}
    log("Opening ranges: " + ", ".join(f"{s} {r['low']:.2f}-{r['high']:.2f}" for s, r in ranges.items()))
    return ranges


def scan(state, now, equity):
    candidates = [s for s in state["ranges"] if s not in state["traded"]]
    if not candidates:
        return
    open_count = len(alpaca.positions())
    prices = alpaca.latest_prices(candidates)
    day_bars = alpaca.bars(candidates, utc_iso(et_dt(state["date"], C.MARKET_OPEN)))
    buying_power = float(alpaca.account()["buying_power"])

    for s in candidates:
        hi, lo = state["ranges"][s]["high"], state["ranges"][s]["low"]
        width = hi - lo
        price = prices.get(s)
        if not price or not (C.MIN_RANGE_PCT <= width / price <= C.MAX_RANGE_PCT):
            continue
        if price <= hi or price > hi + C.MAX_CHASE * width:
            continue  # no breakout yet, or it already ran too far to chase
        vw = vwap(day_bars.get(s, []))
        if vw and price < vw:
            continue

        stop = round((hi + lo) / 2, 2)
        risk = price - stop
        target = round(price + C.REWARD_RISK * risk, 2)
        qty = min(math.floor(equity * C.RISK_PER_TRADE / risk),
                  math.floor(equity * C.MAX_POSITION_PCT / price),
                  math.floor(buying_power / price))
        sig = {"time": now.isoformat(timespec="minutes"), "symbol": s, "price": price,
               "stop": stop, "target": target, "qty": qty, "or_high": hi, "or_low": lo,
               "action": "", "reason": ""}
        state["traded"].append(s)  # one signal per symbol per day

        ai = state["ai"]["decisions"].get(s, {})
        if ai.get("decision") == "block":
            sig.update(action="blocked_by_ai", reason=ai.get("reason", ""))
        elif open_count >= C.MAX_OPEN_POSITIONS:
            sig["action"] = "skipped_max_positions"
        elif qty < 1:
            sig["action"] = "skipped_size"
        else:
            try:
                alpaca.submit_bracket(s, qty, target, stop, f"orb-{state['date']}-{s}")
                sig["action"] = "entered"
                open_count += 1
                buying_power -= qty * price
            except Exception as e:
                sig.update(action="order_error", reason=str(e)[:200])
        state["signals"].append(sig)
        log(f"{s} breakout at {price:.2f} (range {lo:.2f}-{hi:.2f}) -> {sig['action']} "
            f"qty {qty}, stop {stop}, target {target} {sig['reason']}")


def wrap_up(state, is_open):
    pos = alpaca.positions()
    if pos or alpaca.orders():
        if is_open:
            log(f"Flattening {len(pos)} position(s) before the close")
            alpaca.close_all()
        else:
            log("Market closed with positions still open - they'll be closed at the next open")
        return
    if state["session_seen"] and not state["eod_done"]:
        end_of_day(state, state["date"])


# ---------- end-of-day accounting ----------
def round_trips(d, fills):
    by = {}
    for f in fills:
        e = by.setdefault(f["symbol"], {"bq": 0.0, "bc": 0.0, "sq": 0.0, "sp": 0.0})
        q, p = float(f["qty"]), float(f["price"])
        if f["side"] == "buy":
            e["bq"] += q
            e["bc"] += q * p
        else:
            e["sq"] += q
            e["sp"] += q * p
    trips = []
    for s, e in by.items():
        q = min(e["bq"], e["sq"])
        if q <= 0:
            continue
        entry, exit_ = e["bc"] / e["bq"], e["sp"] / e["sq"]
        trips.append({"date": d, "symbol": s, "qty": q, "entry": round(entry, 2),
                      "exit": round(exit_, 2), "pnl": round((exit_ - entry) * q, 2),
                      "pnl_pct": round((exit_ / entry - 1) * 100, 2)})
    return trips


def simulate(sig, bars, flatten_at):
    """What a skipped/blocked signal would have done: stop or target, whichever
    hit first (stop assumed first if both in one bar), else exit at flatten time."""
    sig_time = datetime.fromisoformat(sig["time"])
    after = [b for b in bars if sig_time < parse_ts(b["t"]) <= flatten_at]
    if not after:
        return sig["price"], "no_data"
    for b in after:
        if b["l"] <= sig["stop"]:
            return sig["stop"], "stop"
        if b["h"] >= sig["target"]:
            return sig["target"], "target"
    return after[-1]["c"], "time_exit"


def end_of_day(state, d):
    end_equity = float(alpaca.account()["equity"])
    day0 = et_dt(d, "00:00")
    trips = round_trips(d, alpaca.fills(utc_iso(day0), utc_iso(day0 + timedelta(days=1))))
    for t in trips:
        append_csv("trades.csv", t)

    open_dt, flat_dt = et_dt(d, C.MARKET_OPEN), et_dt(d, C.FLATTEN_AT)
    spy_bars = alpaca.bars(["SPY"], utc_iso(open_dt), utc_iso(et_dt(d, "15:59"))).get("SPY", [])
    spy_open = spy_bars[0]["o"] if spy_bars else None
    spy_close = spy_bars[-1]["c"] if spy_bars else None

    others = [s for s in state["signals"] if s["action"] != "entered"]
    blocked_pnl = 0.0
    if others:
        bars = alpaca.bars(sorted({s["symbol"] for s in others}), utc_iso(open_dt), utc_iso(flat_dt))
        for sig in others:
            exit_, how = simulate(sig, bars.get(sig["symbol"], []), flat_dt)
            per_share = exit_ - sig["price"]
            pnl = round(per_share * max(sig["qty"], 0), 2)
            r_mult = round(per_share / (sig["price"] - sig["stop"]), 2)
            if sig["action"] == "blocked_by_ai":
                blocked_pnl += pnl
            append_csv("shadow.csv", {"date": d, "symbol": sig["symbol"], "action": sig["action"],
                                      "reason": sig["reason"], "entry": sig["price"],
                                      "exit": round(exit_, 2), "exit_type": how,
                                      "qty": sig["qty"], "pnl": pnl, "r_multiple": r_mult})

    start = state["start_equity"]
    append_csv("daily.csv", {
        "date": d, "start_equity": round(start, 2), "end_equity": round(end_equity, 2),
        "pnl": round(end_equity - start, 2), "pnl_pct": round((end_equity / start - 1) * 100, 3),
        "trades": len(trips), "wins": sum(1 for t in trips if t["pnl"] > 0),
        "signals": len(state["signals"]),
        "ai_blocked": sum(1 for s in others if s["action"] == "blocked_by_ai"),
        "ai_blocked_pnl": round(blocked_pnl, 2),
        "spy_open": spy_open, "spy_close": spy_close,
        "spy_pct": round((spy_close / spy_open - 1) * 100, 3) if spy_open else "",
    })
    state["eod_done"] = True
    log(f"Day done: P&L ${end_equity - start:,.2f} on {len(trips)} trade(s)")
    report.build()


if __name__ == "__main__":
    main()
