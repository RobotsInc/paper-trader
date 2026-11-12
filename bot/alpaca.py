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
    if r.status_code >= 400:
        raise RuntimeError(f"Alpaca {path} HTTP {r.status_code}: {r.text[:200]!r}")
    return r.json()


def clock():
    return _get(TRADE, "/v2/clock")


def account():
    return _get(TRADE, "/v2/account")


def positions():
    return _get(TRADE, "/v2/positions")


def orders(status="open"):
    return _get(TRADE, "/v2/orders", status=status, limit=500)


def asset(symbol):
    return _get(TRADE, f"/v2/assets/{symbol}")


def submit_bracket(symbol, qty, side, take_profit, stop_loss, client_id):
    """Market entry (side 'buy' = long, 'sell' = short) with an attached stop-loss (and
    take-profit, if given) that Alpaca holds between bot runs."""
    body = {
        "symbol": symbol,
        "qty": str(int(qty)),
        "side": side,
        "type": "market",
        "time_in_force": "day",
        "order_class": "bracket" if take_profit else "oto",
        "stop_loss": {"stop_price": f"{stop_loss:.2f}"},
        "client_order_id": client_id,
    }
    if take_profit:
        body["take_profit"] = {"limit_price": f"{take_profit:.2f}"}
    r = requests.post(TRADE + "/v2/orders", headers=_headers(), json=body, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code} {r.text[:200]}")
    return r.json()


def close_all():
    r = requests.delete(TRADE + "/v2/positions", headers=_headers(),
                        params={"cancel_orders": "true"}, timeout=30)
    r.raise_for_status()
    return r.json() if r.content else []


def calendar(start, end):
    return _get(TRADE, "/v2/calendar", start=start, end=end)


def bars(symbols, start, end=None, timeframe="1Min", feed=FEED):
    out = {}
    for i in range(0, len(symbols), 100):
        chunk, token = symbols[i:i + 100], None
        while True:
            p = dict(symbols=",".join(chunk), timeframe=timeframe, start=start,
                     feed=feed, limit=10000, adjustment="raw" if timeframe == "1Min" else "split")
            if end:
                p["end"] = end
            if token:
                p["page_token"] = token
            j = _get(DATA, "/v2/stocks/bars", **p)
            for sym, b in (j.get("bars") or {}).items():
                out.setdefault(sym, []).extend(b)
            token = j.get("next_page_token")
            if not token:
                break
    return out


def latest_prices(symbols):
    out = {}
    for i in range(0, len(symbols), 100):
        j = _get(DATA, "/v2/stocks/trades/latest", symbols=",".join(symbols[i:i + 100]), feed=FEED)
        out.update({s: float(t["p"]) for s, t in (j.get("trades") or {}).items()})
    return out


def snapshots(symbols):
    out = {}
    for i in range(0, len(symbols), 100):
        j = _get(DATA, "/v2/stocks/snapshots", symbols=",".join(symbols[i:i + 100]), feed=FEED)
        out.update(j or {})
    return out


def most_actives(top=50):
    j = _get(DATA, "/v1beta1/screener/stocks/most-actives", by="volume", top=top)
    return [x["symbol"] for x in j.get("most_actives", [])]


def movers(top=25):
    j = _get(DATA, "/v1beta1/screener/stocks/movers", top=top)
    return [x["symbol"] for x in (j.get("gainers") or []) + (j.get("losers") or [])]


def news(symbols, start, max_items=200):
    out, token = [], None
    while len(out) < max_items:
        p = dict(symbols=",".join(symbols), start=start, limit=50, sort="desc")
        if token:
            p["page_token"] = token
        j = _get(DATA, "/v1beta1/news", **p)
        out.extend(j.get("news", []))
        token = j.get("next_page_token")
        if not token:
            break
    return out


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
