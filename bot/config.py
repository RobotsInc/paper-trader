"""Strategy settings (v2). Change these to tune the bot."""
import os

# ---- Universe / scanner ----
# Strategy v3 = the "stocks in play" opening-range breakout from Zarattini, Barbon & Aziz
# ("A Profitable Day Trading Strategy for the U.S. Equity Market"), chosen by our 12-month
# backtest (data/backtest/REPORT.md). Each morning the bot scans CORE + Alpaca's most-active and
# top-mover lists and trades the MAX_UNIVERSE names with the highest relative volume.
SCAN_MOST_ACTIVES = 50
SCAN_MOVERS = 25              # top gainers + top losers each
MAX_UNIVERSE = 20             # trade the 20 names with the highest relative volume
MIN_PRICE = 10.0             # paper uses $5; our backtest only covered ~$10+ names, so stay there
MIN_AVG_VOLUME = 1_000_000    # 14-day average daily volume (all exchanges)
MIN_ATR = 0.50                # 14-day average true range, in dollars
MIN_RELVOL = 1.0              # first-5-min volume vs the same 5 minutes averaged over the last 14 days
# Leveraged / inverse ETFs: they just duplicate index bets at 2-3x, so the scanner skips them.
EXCLUDE = {
    "TQQQ", "SQQQ", "SPXL", "SPXS", "SPXU", "UPRO", "SSO", "SDS", "QLD", "QID", "TNA", "TZA", "UDOW", "SDOW",
    "SOXL", "SOXS", "TECL", "TECS", "FAS", "FAZ", "LABU", "LABD", "NUGT", "DUST", "JNUG", "JDST", "BOIL", "KOLD",
    "UCO", "SCO", "UVXY", "SVXY", "VXX", "VIXY", "TSLL", "TSLZ", "TSLQ", "NVDL", "NVDU", "NVDD", "NVDQ", "NVDX",
    "MSTU", "MSTX", "MSTZ", "CONL", "AMDL", "AAPU", "GGLL", "METU", "AMZU", "BITX", "ETHU", "SH", "PSQ", "DOG",
    "YINN", "YANG", "FNGU", "FNGD", "BULZ", "BERZ", "SMST", "PLTU", "HOOX",
}

MARKET_OPEN = "09:30"        # ET
OPENING_RANGE_MIN = 5        # opening range = first 5 minutes (9:30-9:35)
MIN_RANGE_BARS = 3
ENTRY_CUTOFF = "14:30"       # no new trades after this (ET)
FLATTEN_AT = "15:45"         # close everything after this (ET) - never hold overnight
CHECK_EVERY = 30             # seconds between checks within a run
LOOP_SECONDS = 250           # each run keeps checking this long (~5 min per run incl. setup)

# ---- Entries ----
DIRECTION = "candle"         # "candle": trade only the way the first 5-min candle closed (green -> long
                             # above the range, red -> short below it). "both": either breakout.
ALLOW_SHORTS = True
MARKET_FILTER = False        # True = longs only when SPY > its VWAP, shorts only when SPY < its VWAP.
VWAP_FILTER = False          # True = longs only above the stock's VWAP, shorts only below
MAX_CHASE = None             # skip if price is more than this many range-widths past the breakout (None = off)

# ---- Exits ----
STOP_ATR = 0.10              # stop = 10% of the stock's 14-day ATR from entry (None = middle of the range)
TARGET_R = None              # profit target as a multiple of risk; None = no target, hold until FLATTEN_AT
MIN_STOP_PCT = 0.0005        # skip if the stop would be closer than 0.05% of price
EST_SLIPPAGE_BPS = 3         # paper fills are perfect; the scorecard also shows P&L after this much
                             # slippage per side (0.03%) to estimate real-money results

# ---- Risk ----
RISK_PER_TRADE = 0.005       # risk 0.5% of equity per trade (entry -> stop)
MAX_POSITION_PCT = 0.20      # no single position larger than 20% of equity
MAX_OPEN_POSITIONS = 5
MAX_PER_SIDE = 3             # at most 3 longs and 3 shorts, so one direction can't fill every slot
# Don't stack the same bet: skip a new trade if it moves almost in lockstep with a position already
# held on the same side (5-min returns today, correlation >= MAX_CORRELATION), or shares a GROUP with one.
MAX_CORRELATION = 0.75
GROUPS = {
    "us_index": {"SPY", "QQQ", "IWM", "DIA", "XLK", "ARKK", "RSP", "VOO", "IVV", "VTI", "QQQM", "MDY"},
    "semis": {"SMH", "SOXX", "NVDA", "AMD", "AVGO", "MU", "TSM", "ARM", "SMCI", "MRVL", "QCOM", "TXN",
              "AMAT", "LRCX", "KLAC", "INTC", "ON"},
    "crypto": {"COIN", "MSTR", "HOOD", "IBIT", "FBTC", "BITO", "GBTC", "ETHA", "MARA", "RIOT", "CLSK"},
    "big_banks": {"XLF", "JPM", "BAC", "WFC", "C", "GS", "MS"},
    "energy": {"XLE", "XOM", "CVX", "OXY", "COP", "SLB", "USO"},
    "biotech": {"XBI", "IBB", "MRNA"},
    "metals": {"GLD", "SLV", "GDX", "IAU"},
}
MAX_GROSS_EXPOSURE = 1.5     # longs + shorts combined capped at 150% of equity
DAILY_LOSS_LIMIT = 0.025     # down 2.5% on the day -> close everything, stop for the day

# ---- AI desk (Google Gemini free tier). Set repo variable AI_FILTER=off to disable. ----
AI_FILTER = os.getenv("AI_FILTER", "on").lower() == "on"
AI_MODEL = os.getenv("AI_MODEL", "auto")  # "auto" tries free Flash models in order
NEWS_LOOKBACK_HOURS = 20
