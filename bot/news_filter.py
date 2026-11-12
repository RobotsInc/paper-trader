"""AI desk: once a day, after the scanner picks today's names, Google Gemini (free
tier) reads recent headlines for all of them and returns
  - a short market briefing, and
  - per symbol: a catalyst summary and a bias: "both", "long", "short", or "block".
If anything fails, it fails open: the bot trades on its rules alone."""
import json
import os
import re
from datetime import timedelta, timezone

import requests

import alpaca
import config as C

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Tried in order until one works (free-tier Flash models). Override with repo variable AI_MODEL.
FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]

PROMPT = """You are the news desk for an intraday opening-range breakout bot. It goes
LONG stocks breaking above their first-15-minute range and SHORT stocks breaking below
it, and closes everything before the market close.

You get today's scanned list: each symbol's opening gap %, relative volume, and recent
headlines. For each symbol return:
- "catalyst": the main driver in <= 8 words ("none" if no real news)
- "decision":
    "both"  - no reason to restrict (the default)
    "long"  - a clear positive catalyst; shorting into it is risky
    "short" - a clear negative catalyst; buying into it is risky
    "block" - binary/erratic event risk today: earnings due today or after the close,
              pending FDA/court/regulatory decision, CEO/leadership crisis, M&A rumor
              or deal news, halt risk
- "reason": <= 15 words

Routine news, analyst notes and general commentary are NOT reasons to restrict.
Also write "briefing": 2-4 sentences on today's market tone and the biggest stories.

Reply with JSON only:
{"briefing": "...", "symbols": {"AAPL": {"decision": "both", "catalyst": "...", "reason": "..."}}}"""


def run(rows, now):
    """rows: list of dicts with symbol, gap_pct, relvol (today's universe)."""
    symbols = [r["symbol"] for r in rows]
    result = {"done": True, "enabled": True, "model": C.AI_MODEL, "decisions": {}, "briefing": ""}
    step = "fetching news"
    try:
        since = (now - timedelta(hours=C.NEWS_LOOKBACK_HOURS)).astimezone(timezone.utc)
        items = alpaca.news(symbols, since.strftime("%Y-%m-%dT%H:%M:%SZ"))
        headlines = {s: [] for s in symbols}
        for n in items:
            for s in n.get("symbols", []):
                if s in headlines and len(headlines[s]) < 6:
                    headlines[s].append(n.get("headline", "").strip())
        lines = []
        for r in rows:
            h = headlines.get(r["symbol"]) or []
            lines.append(f"{r['symbol']} (gap {r.get('gap_pct', 0):+.1f}%, relvol {r.get('relvol', 0):.1f}x): "
                         + (" | ".join(h) if h else "(no recent news)"))

        step = "calling AI model"
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("no GEMINI_API_KEY secret set")
        text = _ask_gemini(key, f"Today is {now:%A, %B %d, %Y}.\n\n" + "\n".join(lines), result)

        step = "reading AI reply"
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        result["briefing"] = str(data.get("briefing", ""))[:800]
        per = data.get("symbols") or {k: v for k, v in data.items() if isinstance(v, dict)}
        for s in symbols:
            d = per.get(s) or {}
            dec = str(d.get("decision", "both")).lower()
            dec = {"allow": "both"}.get(dec, dec)
            if dec not in ("both", "long", "short", "block"):
                dec = "both"
            result["decisions"][s] = {"decision": dec,
                                      "catalyst": str(d.get("catalyst", ""))[:80],
                                      "reason": str(d.get("reason", ""))[:160]}
    except Exception as e:  # fail open
        result["error"] = f"while {step}: {type(e).__name__}: {e}"[:400]
        result["decisions"] = {}
    return result


def _ask_gemini(key, user, result):
    models = [C.AI_MODEL] if C.AI_MODEL and C.AI_MODEL != "auto" else FALLBACK_MODELS
    body = {
        "systemInstruction": {"parts": [{"text": PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    errors = []
    for model in models:
        try:
            r = requests.post(ENDPOINT.format(model=model), json=body, timeout=75,
                              headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        except requests.RequestException as e:
            errors.append(f"{model}: {type(e).__name__}")
            continue
        if r.status_code == 200:
            result["model"] = model
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        errors.append(f"{model}: HTTP {r.status_code} {r.text[:120]!r}")
    raise RuntimeError("; ".join(errors))
