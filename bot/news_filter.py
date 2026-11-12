"""AI news filter: once a day, an LLM (Google Gemini, free tier) reads recent
headlines and can veto symbols whose price action is likely to be headline-driven.
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
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]

PROMPT = """You are a risk filter for an intraday long-only breakout trading bot.
It buys stocks that break above their first-15-minute range and closes everything
before the market close. Breakouts work best when price moves on normal flows, and
fail more often when a stock is whipsawed by news.

For each symbol, read the recent headlines and decide:
- "block" only if there is a specific, current event likely to make today's price
  action unusually erratic or headline-driven: earnings released today or due after
  today's close, a CEO/leadership crisis, a major lawsuit/regulatory/export action,
  an M&A announcement, a trading halt risk, or a big gap on breaking news.
- "allow" otherwise. Routine news, analyst notes, and general market commentary
  are NOT reasons to block. Default to allow.

Reply with JSON only, no prose, in exactly this form:
{"AAPL": {"decision": "allow", "reason": "short reason"}, ...}"""


def run(symbols, now):
    result = {"done": True, "enabled": True, "model": C.AI_MODEL, "decisions": {}}
    step = "fetching news"
    try:
        since = (now - timedelta(hours=C.NEWS_LOOKBACK_HOURS)).astimezone(timezone.utc)
        items = alpaca.news(symbols, since.strftime("%Y-%m-%dT%H:%M:%SZ"))
        step = "calling AI model"
        headlines = {s: [] for s in symbols}
        for n in items:
            for s in n.get("symbols", []):
                if s in headlines and len(headlines[s]) < 8:
                    headlines[s].append(n.get("headline", "").strip())
        lines = [f"{s}: " + (" | ".join(h) if h else "(no recent news)")
                 for s, h in headlines.items()]
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("no GEMINI_API_KEY secret set")
        user = f"Today is {now:%A, %B %d, %Y}.\n\n" + "\n".join(lines)
        text = _ask_gemini(key, user, result)
        step = "reading AI reply"
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        for s in symbols:
            d = data.get(s) or {}
            decision = "block" if str(d.get("decision", "allow")).lower() == "block" else "allow"
            result["decisions"][s] = {"decision": decision, "reason": str(d.get("reason", ""))[:200]}
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
        r = requests.post(ENDPOINT.format(model=model), json=body, timeout=60,
                          headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        if r.status_code == 200:
            result["model"] = model
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        errors.append(f"{model}: HTTP {r.status_code} {r.text[:120]!r}")
    raise RuntimeError("; ".join(errors))
