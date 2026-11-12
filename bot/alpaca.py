"""Minimal Alpaca REST client (paper trading + free IEX market data)."""
import os

import requests

TRADE = "https://paper-api.alpaca.markets"   # paper only - never the live endpoint
DATA = "https://data.alpaca.markets"
FEED = "iex"                                  # free data feed


def _headers():
    return {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    }


def _get(base, path, **params):
    r = requests.get(base + path, headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def clock():
    return _get(TRADE, "/v2/clock")


def account():
    return _get(TRADE, "/v2/account")


def positions():
    return _get(TRADE, "/v2/positions")


def orders(status="open"):
    return _get(TRADE, "/v2/orders", status=status, limit=500)


def submit_bracket(symbol, qty, take_profit, stop_loss, client_id):
    """Market buy with an attached take-profit and stop-loss, managed by Alpaca
    between bot runs."""
    body = {
        "symbol": symbol,
        "qty": str(int(qty)),
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "order_class": "bracket",
        "take_profit": {"limit_price": f"{take_profit:.2f}"},
        "stop_loss": {"stop_price": f"{stop_loss:.2f}"},
        "client_order_id": client_id,
    }
    r = requests.post(TRADE + "/v2/orders", headers=_headers(), json=body, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code} {r.text[:200]}")
    return r.json()


def close_all():
    r = requests.delete(TRADE + "/v2/positions", headers=_headers(),
                        params={"cancel_orders": "true"}, timeout=30)
    r.raise_for_status()
    return r.json() if r.content else []


def bars(symbols, start, end=None, timeframe="1Min"):
    out, token = {}, None
    while True:
        p = dict(symbols=",".join(symbols), timeframe=timeframe, start=start,
                 feed=FEED, limit=10000, adjustment="raw")
        if end:
            p["end"] = end
        if token:
            p["page_token"] = token
        j = _get(DATA, "/v2/stocks/bars", **p)
        for sym, b in (j.get("bars") or {}).items():
            out.setdefault(sym, []).extend(b)
        token = j.get("next_page_token")
        if not token:
            return out


def latest_prices(symbols):
    j = _get(DATA, "/v2/stocks/trades/latest", symbols=",".join(symbols), feed=FEED)
    return {s: float(t["p"]) for s, t in (j.get("trades") or {}).items()}


def news(symbols, start, limit=50):
    j = _get(DATA, "/v1beta1/news", symbols=",".join(symbols), start=start,
             limit=limit, sort="desc")
    return j.get("news", [])


def fills(after, until):
    out, token = [], None
    while True:
        p = dict(after=after, until=until, direction="asc", page_size=100)
        if token:
            p["page_token"] = token
        page = _get(TRADE, "/v2/account/activities/FILL", **p)
        out.extend(page)
        if len(page) < 100:
            return out
        token = page[-1]["id"]
