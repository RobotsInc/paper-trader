"""Plain-Python indicators. Inputs are lists of floats (oldest first)."""


def ema(vals, n):
    if not vals:
        return []
    k = 2.0 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def rsi(vals, n=14):
    if len(vals) < n + 1:
        return None
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = vals[i] - vals[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    ag, al = gains / n, losses / n
    for i in range(n + 1, len(vals)):
        d = vals[i] - vals[i - 1]
        ag = (ag * (n - 1) + max(d, 0)) / n
        al = (al * (n - 1) + max(-d, 0)) / n
    if al == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + ag / al)


def macd_hist(vals, fast=12, slow=26, sig=9):
    """(latest histogram, previous histogram) or (None, None)."""
    if len(vals) < slow + sig:
        return None, None
    f, s = ema(vals, fast), ema(vals, slow)
    m = [a - b for a, b in zip(f, s)]
    h = [a - b for a, b in zip(m, ema(m, sig))]
    return h[-1], h[-2]


def bollinger(vals, n=20, k=2.0):
    """(mid, upper, lower) or None."""
    if len(vals) < n:
        return None
    w = vals[-n:]
    mid = sum(w) / n
    sd = (sum((x - mid) ** 2 for x in w) / n) ** 0.5
    return mid, mid + k * sd, mid - k * sd


def atr(highs, lows, closes, n=14):
    if len(closes) < 2:
        return None
    trs = [max(h - l, abs(h - pc), abs(l - pc)) for h, l, pc in zip(highs[1:], lows[1:], closes[:-1])]
    trs = trs[-n:]
    return sum(trs) / len(trs) if trs else None


def vwap_sd(bars):
    """Volume-weighted average price and the volume-weighted std dev around it (today's bars)."""
    vol = sum(b["v"] for b in bars)
    if vol <= 0:
        return None, 0.0
    tp = [(b["h"] + b["l"] + b["c"]) / 3 for b in bars]
    vw = sum(t * b["v"] for t, b in zip(tp, bars)) / vol
    var = sum(b["v"] * (t - vw) ** 2 for t, b in zip(tp, bars)) / vol
    return vw, var ** 0.5


def resample(bars, n=5):
    """Group 1-minute bars (dicts with ts, idx, o, h, l, c, v) into n-minute bars."""
    out, cur, key = [], None, None
    for b in bars:
        k = (b["ts"].date(), b["idx"] // n)
        if k != key:
            if cur:
                out.append(cur)
            cur, key = {"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"], "ts": b["ts"], "idx": b["idx"]}, k
        else:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
            cur["v"] += b["v"]
            cur["ts"] = b["ts"]
    if cur:
        out.append(cur)
    return out
