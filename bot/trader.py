"""Paper day-trading bot v2: market scanner + opening-range breakouts (long & short)
+ AI news desk.

GitHub Actions starts this every ~5 minutes on weekdays; each run then checks the market
every 30 seconds for ~4 minutes. Each check:
  1. logs account equity,
  2. at ~9:36 ET, scans the market for the 20 "stocks in play" (highest relative volume)
     and asks the AI desk for a briefing and a long/short/block bias on each,
  3. until 14:30 ET, trades breakouts of the 5-minute opening range in the direction of the
     first candle, with a stop at 10% of the stock's daily ATR held by Alpaca; no profit
     target - winners ride until the close,
  4. after 15:45 ET, closes everything and writes the day's results,
  5. writes data/live.json for the dashboard.

Usage: python bot/trader.py [run|flatten|report|ai]
"""
import csv
import json
import math
import sys
import time as _clock
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import alpaca
import config as C
import dashboard
import news_filter
import report
import universe

ET = ZoneInfo("America/New_York")
DATA = Path(__file__).resolve().parent.parent / "data"
STATE = DATA / "state.json"


# ---------- helpers ----------
def now_et():
    return datetime.now(ET)


def log(msg):
    print(f"[{now_et():%Y-%m-%d %H:%M:%S} ET] {msg}", flush=True)


_said = set()


def log_once(msg):
    """Log a status line only the first time this run (the run checks every 30s)."""
    if msg not in _said:
        _said.add(msg)
        log(msg)


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
    if not path.exists():
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            w.writeheader()
            w.writerow(row)
        return
    with path.open() as f:
        header = next(csv.reader(f), None) or []
    missing = [k for k in row if k not in header]
    if missing:  # file written by an older version: add the new columns
        with path.open() as f:
            rows = list(csv.DictReader(f))
        header = header + missing
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    with path.open("a", newline="") as f:
        csv.DictWriter(f, fieldnames=header, extrasaction="ignore").writerow(row)


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
    if prev and state.get("eod_done") and not state.get("small_scored"):
        score_spreads_and_smallcaps(state, prev)
    keep = {k: state[k] for k in ("inception",) if k in state}
    state.clear()
    state.update(date=today, start_equity=equity, ranges={}, scan={}, regime={},
                 ai={"done": False, "decisions": {}, "briefing": ""}, traded=[], signals=[],
                 shortable={}, last_prices={}, halted=False, eod_done=False, session_seen=False,
                 small={}, small_signals=[], small_scored=False)
    state.update(keep)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "report":
        report.build()
        return
    if mode == "scantest":  # dry run of the scanner on today's (or the last) session - no trading, no state
        d = now_et().date().isoformat()
        or_start = et_dt(d, C.MARKET_OPEN)
        rows, stats, small = universe.build(or_start, or_start + timedelta(minutes=C.OPENING_RANGE_MIN), log)
        log(f"Scan test {d}: {stats}")
        for r in rows + [dict(x, symbol=x["symbol"] + "*") for x in small]:
            log(f"  {r['symbol']:6} relvol {r['relvol']:5.2f}x gap {r['gap_pct']:+5.2f}% dir {r['dir']:+d} "
                f"range {r['low']:.2f}-{r['high']:.2f} ATR {r['atr']:.2f} -> stop distance "
                f"{C.STOP_ATR * r['atr']:.2f} ({C.STOP_ATR * r['atr'] / r['high'] * 100:.2f}%)")
        log("(* = $5-10 small-cap experiment: tracked, not traded)")
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
    for k, v in (("scan", {}), ("regime", {}), ("shortable", {}), ("last_prices", {}), ("small", {}),
                 ("small_signals", [])):
        state.setdefault(k, v)
    if mode == "rescan":  # rebuild today's scanner list + AI desk now (keeps today's trades)
        state["ranges"] = {}
        state["ai"] = {"done": False, "decisions": {}, "briefing": ""}
        mode = "run"

    # Each run watches the market for ~LOOP_SECONDS, checking every CHECK_EVERY seconds, so
    # breakouts are caught within ~30s instead of waiting for the next 5-minute run.
    deadline = _clock.monotonic() + (C.LOOP_SECONDS if mode == "run" else 0)
    first = True
    while True:
        is_open = tick(state, mode, now, equity, acct, first)
        first = False
        if not is_open or _clock.monotonic() + C.CHECK_EVERY > deadline:
            break
        _clock.sleep(C.CHECK_EVERY)
        now = now_et()
        try:
            acct = alpaca.account()
            equity = float(acct["equity"])
        except Exception as e:
            log(f"Account check failed ({type(e).__name__}: {e}) - ending this run early")
            break


def tick(state, mode, now, equity, acct, first):
    """One check of the market. Returns whether the market is open."""
    is_open = False
    try:
        if mode == "ai":  # re-run today's AI desk (e.g. after it failed)
            run_ai_filter(state, now)
            return False

        is_open = alpaca.clock()["is_open"]
        if is_open:
            if first:  # one equity point per run is plenty for the chart
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
            log_once("Market closed - nothing to do")
    except Exception as e:
        if first:
            raise
        log(f"Check failed, will retry next check: {type(e).__name__}: {e}")  # keep the loop alive
    finally:
        save_state(state)
        try:
            dashboard.write(state, now, is_open)
        except Exception as e:
            log(f"Dashboard update failed: {type(e).__name__}: {e}")
    return is_open and mode == "run"


def trade(state, now, equity):
    if state["halted"]:
        log_once("Halted for the day (daily loss limit)")
        return
    if equity <= state["start_equity"] * (1 - C.DAILY_LOSS_LIMIT):
        log("Daily loss limit hit - closing everything and stopping for today")
        alpaca.close_all()
        state["halted"] = True
        return

    or_start = et_dt(state["date"], C.MARKET_OPEN)
    or_end = or_start + timedelta(minutes=C.OPENING_RANGE_MIN)
    if now < or_end + timedelta(minutes=1):
        log_once("Waiting for the opening range to form")
        return
    if not state["ranges"]:
        rows, stats, small = universe.build(or_start, or_end, log)
        state["ranges"] = {r["symbol"]: r for r in rows}
        state["small"] = {r["symbol"]: r for r in small}
        state["scan"] = stats
        log(f"Scanner: {stats['scanned']} scanned, {stats['liquid']} liquid, "
            f"{stats['qualified']} in play -> trading top {stats['selected']}: "
            + ", ".join(f"{r['symbol']}({r['gap_pct']:+.1f}%,{r['relvol']:.1f}x)" for r in rows[:15])
            + (" ..." if len(rows) > 15 else ""))
        if small:
            log(f"Small-cap experiment (tracked, not traded): " + ", ".join(r["symbol"] for r in small))
    if not state["ai"]["done"]:
        run_ai_filter(state, now)
    if now.time() > hm(C.ENTRY_CUTOFF):
        log_once("Past entry cutoff - managing open trades only")
        return
    scan(state, now, equity)


def run_ai_filter(state, now):
    if not C.AI_FILTER:
        state["ai"] = {"done": True, "enabled": False, "decisions": {}, "briefing": ""}
        log("AI desk is off")
        return
    rows = list(state["ranges"].values()) or [{"symbol": s} for s in universe.CORE[:40]]
    state["ai"] = news_filter.run(rows, now)
    if state["ai"].get("error"):
        log(f"AI desk failed, trading on rules only: {state['ai']['error']}")
        return
    log(f"AI desk ({state['ai'].get('model')}): {state['ai'].get('briefing', '')}")
    for s, d in state["ai"]["decisions"].items():
        append_csv("ai_log.csv", {"date": state["date"], "symbol": s, "decision": d["decision"],
                                  "catalyst": d.get("catalyst", ""), "reason": d["reason"]})
        if d["decision"] != "both":
            log(f"AI {d['decision'].upper()} {s}: {d.get('catalyst', '')} - {d['reason']}")


def is_shortable(state, s):
    if s not in state["shortable"]:
        try:
            a = alpaca.asset(s)
            state["shortable"][s] = bool(a.get("shortable") and a.get("easy_to_borrow"))
        except Exception:
            state["shortable"][s] = False
    return state["shortable"][s]


def scan(state, now, equity):
    if not C.MARKET_FILTER:  # signals skipped only for SPY trend get another chance
        skipped = {x["symbol"] for x in state["signals"] if x["action"] == "skipped_market"}
        state["traded"] = [s for s in state["traded"] if s not in skipped]
        state["signals"] = [x for x in state["signals"] if x["action"] != "skipped_market"]
    cands = [s for s in state["ranges"] if s not in state["traded"]]
    held = {p["symbol"]: p["side"] for p in alpaca.positions()}
    prices = alpaca.latest_prices(sorted(set(state["ranges"]) | set(state["small"]) | {"SPY"}))  # all names
    day_bars = alpaca.bars(sorted(set(cands) | set(held) | {"SPY"}), utc_iso(et_dt(state["date"], C.MARKET_OPEN)))
    state["last_prices"] = {s: prices[s] for s in prices}

    spy_px, spy_vw = prices.get("SPY"), vwap(day_bars.get("SPY", []))
    market = ("up" if spy_px > spy_vw else "down") if spy_px and spy_vw else "unknown"
    spy_open = (day_bars.get("SPY") or [{}])[0].get("o")
    state["regime"] = {"spy": spy_px, "spy_vwap": round(spy_vw, 2) if spy_vw else None,
                       "spy_day_pct": round((spy_px / spy_open - 1) * 100, 2) if spy_px and spy_open else None,
                       "bias": market, "time": now.isoformat(timespec="minutes")}
    track_small(state, now, prices)
    if not cands:
        return

    signals = []
    for s in cands:
        r = state["ranges"][s]
        hi, lo, px = r["high"], r["low"], prices.get(s)
        if not px:
            continue
        w = hi - lo
        d = r.get("dir", 0)
        vw = vwap(day_bars.get(s, [])) if C.VWAP_FILTER else None
        if C.MAX_CHASE_ATR and r.get("atr") and (px - hi > C.MAX_CHASE_ATR * r["atr"] or lo - px > C.MAX_CHASE_ATR * r["atr"]):
            continue  # already ran too far past the range - don't chase
        go_long = C.DIRECTION == "both" or d > 0
        go_short = C.ALLOW_SHORTS and (C.DIRECTION == "both" or d < 0)
        if go_long and px > hi and (C.MAX_CHASE is None or px <= hi + C.MAX_CHASE * w) and (not vw or px > vw):
            signals.append((r.get("score", 0), s, "long", px))
        elif go_short and px < lo and (C.MAX_CHASE is None or px >= lo - C.MAX_CHASE * w) and (not vw or px < vw):
            signals.append((r.get("score", 0), s, "short", px))
    if not signals:
        return
    signals.sort(reverse=True)  # most in-play names get the open slots first

    positions = alpaca.positions()
    open_count = len(positions)
    held = {p["symbol"]: p["side"] for p in positions}
    gross = sum(abs(float(p["market_value"])) for p in positions)
    buying_power = float(alpaca.account()["buying_power"])

    for score, s, side, px in signals:
        r = state["ranges"][s]
        sgn = 1 if side == "long" else -1
        if C.STOP_ATR and r.get("atr"):
            stop = round(px - sgn * C.STOP_ATR * r["atr"], 2)   # a slice of the stock's normal daily move
        else:
            stop = round((r["high"] + r["low"]) / 2, 2)         # middle of the opening range
        risk = abs(px - stop)
        if risk < max(0.01, px * C.MIN_STOP_PCT):
            continue
        target = round(px + sgn * C.TARGET_R * risk, 2) if C.TARGET_R else None  # None = hold to the close
        room = max(0.0, min(buying_power, equity * C.MAX_GROSS_EXPOSURE - gross))
        qty = min(math.floor(equity * C.RISK_PER_TRADE / risk),
                  math.floor(equity * C.MAX_POSITION_PCT / px),
                  math.floor(room / px))
        sig = {"time": now.isoformat(timespec="minutes"), "symbol": s, "side": side, "price": px,
               "stop": stop, "target": target, "qty": qty, "or_high": r["high"], "or_low": r["low"],
               "action": "", "reason": "", "market": market}
        state["traded"].append(s)  # one signal per symbol per day

        ai = state["ai"]["decisions"].get(s, {})
        bias = ai.get("decision", "both")
        if bias == "block" or bias in ("long", "short") and bias != side:
            sig.update(action="blocked_by_ai", reason=f"AI {bias}: {ai.get('reason', '')}")
        elif C.MARKET_FILTER and ((side == "long" and market == "down") or (side == "short" and market == "up")):
            sig.update(action="skipped_market", reason=f"SPY trend {market}")
        elif open_count >= C.MAX_OPEN_POSITIONS:
            sig["action"] = "skipped_max_positions"
        elif sum(1 for v in held.values() if v == side) >= C.MAX_PER_SIDE:
            sig.update(action="skipped_side_cap", reason=f"already {C.MAX_PER_SIDE} {side}s")
        elif (twin := overlapping(s, side, held, day_bars)):
            sig.update(action="skipped_correlated", reason=twin)
        elif qty < 1:
            sig["action"] = "skipped_size"
        elif side == "short" and not is_shortable(state, s):
            sig["action"] = "skipped_not_shortable"
        else:
            try:
                try:
                    alpaca.submit_bracket(s, qty, "buy" if side == "long" else "sell", target, stop,
                                          f"orb-{state['date']}-{s}-{side}")
                except RuntimeError as e:
                    if target or not str(e).startswith("4"):
                        raise
                    # Stop-only order rejected: use a bracket whose target is far enough away
                    # (10x risk) that in practice it still means "hold to the close".
                    log(f"Stop-only order rejected for {s} ({str(e)[:80]}) - retrying as a bracket")
                    alpaca.submit_bracket(s, qty, "buy" if side == "long" else "sell",
                                          round(px + sgn * 10 * risk, 2), stop, f"orb-{state['date']}-{s}-{side}-b")
                sig["action"] = "entered"
                held[s] = side
                open_count += 1
                gross += qty * px
                buying_power -= qty * px
            except Exception as e:
                sig.update(action="order_error", reason=str(e)[:200])
        state["signals"].append(sig)
        log(f"{side.upper()} {s} @ {px:.2f} (range {r['low']:.2f}-{r['high']:.2f}) -> {sig['action']} "
            f"qty {qty} stop {stop} target {target or 'close'} {sig['reason']}")


def _returns_5m(bars):
    """5-minute returns keyed by bucket time, so two stocks line up even if IEX skipped some minutes."""
    last = {}
    for b in bars:
        t = b["t"]  # e.g. 2026-11-12T14:37:00Z
        last[t[:14] + f"{int(t[14:16]) // 5 * 5:02d}"] = b["c"]
    keys = sorted(last)
    return {k: last[k] / last[p] - 1 for p, k in zip(keys, keys[1:])}


def overlapping(sym, side, held, day_bars):
    """Name of a same-side position that is effectively the same bet as `sym`, else ''."""
    group = next((g for g, names in C.GROUPS.items() if sym in names), None)
    for h, h_side in held.items():
        if h_side != side:
            continue  # long A + short B is a hedge, not a duplicate
        if group and h in C.GROUPS[group]:
            return f"same group as {h} ({group})"
        a, b = _returns_5m(day_bars.get(sym, [])), _returns_5m(day_bars.get(h, []))
        keys = sorted(set(a) & set(b))
        if len(keys) >= 8:
            x, y = [a[k] for k in keys], [b[k] for k in keys]
            mx, my = sum(x) / len(x), sum(y) / len(y)
            cov = sum((i - mx) * (j - my) for i, j in zip(x, y))
            vx, vy = sum((i - mx) ** 2 for i in x), sum((j - my) ** 2 for j in y)
            if vx and vy and cov / math.sqrt(vx * vy) >= C.MAX_CORRELATION:
                return f"moves with {h} (corr {cov / math.sqrt(vx * vy):.2f})"
    return ""


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
    if (state["eod_done"] and not state.get("small_scored")
            and now_et() >= et_dt(state["date"], C.FLATTEN_AT) + timedelta(minutes=16)):
        try:
            score_spreads_and_smallcaps(state, state["date"])
        except Exception as e:
            log(f"Spread / small-cap scoring failed: {type(e).__name__}: {e}")
            state["small_scored"] = True


# ---------- end-of-day accounting ----------
def round_trips(d, fills):
    by = {}
    for f in fills:  # fills arrive oldest first
        e = by.setdefault(f["symbol"], {"bq": 0.0, "bc": 0.0, "sq": 0.0, "sp": 0.0, "first": f["side"]})
        q, p = float(f["qty"]), float(f["price"])
        if f["side"] == "buy":
            e["bq"] += q
            e["bc"] += q * p
        else:  # sell or sell_short
            e["sq"] += q
            e["sp"] += q * p
    trips = []
    for s, e in by.items():
        q = min(e["bq"], e["sq"])
        if q <= 0:
            continue
        buy_avg, sell_avg = e["bc"] / e["bq"], e["sp"] / e["sq"]
        short = e["first"] != "buy"
        entry, exit_ = (sell_avg, buy_avg) if short else (buy_avg, sell_avg)
        pnl = (sell_avg - buy_avg) * q
        trips.append({"date": d, "symbol": s, "side": "short" if short else "long", "qty": q,
                      "entry": round(entry, 2), "exit": round(exit_, 2), "pnl": round(pnl, 2),
                      "pnl_pct": round(pnl / (entry * q) * 100, 2)})
    return trips


def breakout(r, px):
    """'long' / 'short' if px breaks the opening range in the allowed direction, else None."""
    d = r.get("dir", 0)
    if (C.DIRECTION == "both" or d > 0) and px > r["high"]:
        return "long"
    if C.ALLOW_SHORTS and (C.DIRECTION == "both" or d < 0) and px < r["low"]:
        return "short"
    return None


def track_small(state, now, prices):
    """Small-cap experiment: log $5-10 breakouts (never traded) with the IEX quote at that moment."""
    done = {x["symbol"] for x in state["small_signals"]}
    hits = []
    for s, r in state["small"].items():
        px = prices.get(s)
        side = breakout(r, px) if px and s not in done else None
        if side and r.get("atr"):
            sgn = 1 if side == "long" else -1
            hits.append({"time": now.isoformat(timespec="seconds"), "symbol": s, "side": side, "price": px,
                         "stop": round(px - sgn * C.STOP_ATR * r["atr"], 4), "atr": r["atr"],
                         "relvol": r.get("relvol"), "gap_pct": r.get("gap_pct")})
    if not hits:
        return
    try:
        q = alpaca.latest_quotes([h["symbol"] for h in hits])
    except Exception:
        q = {}
    for h in hits:
        bid, ask = q.get(h["symbol"], (0, 0))
        h["iex_spread_pct"] = round((ask - bid) / ((ask + bid) / 2) * 100, 3) if bid > 0 and ask > bid else None
        state["small_signals"].append(h)
        log(f"[small-cap, not traded] {h['side'].upper()} {h['symbol']} @ {h['price']:.2f} stop {h['stop']:.2f} "
            f"IEX spread {h['iex_spread_pct']}%")


def market_spread_pct(symbol, at):
    """Median all-exchange bid-ask spread (% of mid) in the minute after `at`. Needs data 15+ min old."""
    try:
        qs = alpaca.quotes(symbol, utc_iso(at), utc_iso(at + timedelta(minutes=1)))
    except Exception:
        return None
    sp = sorted((q["ap"] - q["bp"]) / ((q["ap"] + q["bp"]) / 2) * 100 for q in qs
                if q.get("bp", 0) > 0 and q.get("ap", 0) > q.get("bp", 0))
    return round(sp[len(sp) // 2], 4) if sp else None


def simulate(sig, bars, flatten_at):
    """What a skipped/blocked signal would have done: stop or target, whichever hit
    first (stop assumed first if both in one bar), else exit at flatten time."""
    short = sig.get("side", "long") == "short"
    sig_time = datetime.fromisoformat(sig["time"])
    after = [b for b in bars if sig_time < parse_ts(b["t"]) <= flatten_at]
    if not after:
        return sig["price"], "no_data"
    for b in after:
        if (b["h"] >= sig["stop"]) if short else (b["l"] <= sig["stop"]):
            return sig["stop"], "stop"
        tgt = sig.get("target")
        if tgt and ((b["l"] <= tgt) if short else (b["h"] >= tgt)):
            return tgt, "target"
    return after[-1]["c"], "time_exit"


def score_spreads_and_smallcaps(state, d):
    """Runs once 15+ minutes after the flatten, when all-exchange (SIP) data is free to query:
    real bid-ask spreads at each signal, and the small-cap experiment's outcomes."""
    open_dt, flat_dt = et_dt(d, C.MARKET_OPEN), et_dt(d, C.FLATTEN_AT)
    # Real spreads at signal time for the main list, to check the 3 bps/side cost assumption.
    for sig in state["signals"]:
        sp = market_spread_pct(sig["symbol"], datetime.fromisoformat(sig["time"]))
        if sp is not None:
            append_csv("spreads.csv", {"date": d, "symbol": sig["symbol"], "tier": "main",
                                       "price": sig["price"], "spread_pct": sp})

    # Small-cap experiment: how each tracked $5-10 signal would have ended, before and after the spread.
    smalls = state.get("small_signals", [])
    if smalls:
        try:
            sbars = alpaca.bars(sorted({x["symbol"] for x in smalls}), utc_iso(open_dt), utc_iso(flat_dt), feed="sip")
        except Exception:
            sbars = alpaca.bars(sorted({x["symbol"] for x in smalls}), utc_iso(open_dt), utc_iso(flat_dt))
        for sig in smalls:
            exit_, how = simulate(sig, sbars.get(sig["symbol"], []), flat_dt)
            sgn = -1 if sig["side"] == "short" else 1
            risk = abs(sig["price"] - sig["stop"])
            per_share = (exit_ - sig["price"]) * sgn
            sp = market_spread_pct(sig["symbol"], datetime.fromisoformat(sig["time"]))
            spread = sp if sp is not None else sig.get("iex_spread_pct")
            cost = sig["price"] * spread / 100 if spread is not None else None  # half spread in + half out
            append_csv("smallcap.csv", {
                "date": d, "time": sig["time"][11:16], "symbol": sig["symbol"], "side": sig["side"],
                "entry": round(sig["price"], 4), "stop": sig["stop"], "risk_pct": round(risk / sig["price"] * 100, 3),
                "exit": round(exit_, 4), "exit_type": how, "spread_pct": sp, "iex_spread_pct": sig.get("iex_spread_pct"),
                "r_gross": round(per_share / risk, 3) if risk else "",
                "r_after_spread": round((per_share - cost) / risk, 3) if risk and cost is not None else "",
                "relvol": sig.get("relvol"), "gap_pct": sig.get("gap_pct")})
            if sp is not None:
                append_csv("spreads.csv", {"date": d, "symbol": sig["symbol"], "tier": "small",
                                           "price": sig["price"], "spread_pct": sp})

    state["small_scored"] = True
    log(f"Logged spreads and {len(smalls)} small-cap experiment signal(s)")
    report.build()


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
            short = sig.get("side", "long") == "short"
            per_share = (sig["price"] - exit_) if short else (exit_ - sig["price"])
            pnl = round(per_share * max(sig["qty"], 0), 2)
            r_mult = round(per_share / abs(sig["price"] - sig["stop"]), 2)
            if sig["action"] == "blocked_by_ai":
                blocked_pnl += pnl
            append_csv("shadow.csv", {"date": d, "symbol": sig["symbol"], "side": sig.get("side", "long"),
                                      "action": sig["action"], "reason": sig["reason"], "entry": sig["price"],
                                      "exit": round(exit_, 2), "exit_type": how, "qty": sig["qty"],
                                      "pnl": pnl, "r_multiple": r_mult})

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
        "longs": sum(1 for t in trips if t.get("side") == "long"),
        "shorts": sum(1 for t in trips if t.get("side") == "short"),
    })
    state["eod_done"] = True
    log(f"Day done: P&L ${end_equity - start:,.2f} on {len(trips)} trade(s)")
    report.build()


if __name__ == "__main__":
    main()
