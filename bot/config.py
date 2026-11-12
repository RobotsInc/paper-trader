"""Strategy settings (v2). Change these to tune the bot."""
import os

# ---- Universe / scanner ----
# Each morning the bot scans CORE + Alpaca's most-active and top-mover lists,
# then trades the MAX_UNIVERSE names most "in play" (gap x relative volume).
SCAN_MOST_ACTIVES = 50
SCAN_MOVERS = 25              # top gainers + top losers each
MAX_UNIVERSE = 40
MIN_PRICE = 10.0
MIN_PREV_DOLLAR_VOL = 3_000_000   # prior-day dollar volume on the IEX feed (~2-3% of all volume)
# Leveraged / inverse ETFs: they just duplicate index bets at 2-3x, so the scanner skips them.
EXCLUDE = {
    "TQQQ", "SQQQ", "SPXL", "SPXS", "SPXU", "UPRO", "SSO", "SDS", "QLD", "QID", "TNA", "TZA", "UDOW", "SDOW",
    "SOXL", "SOXS", "TECL", "TECS", "FAS", "FAZ", "LABU", "LABD", "NUGT", "DUST", "JNUG", "JDST", "BOIL", "KOLD",
    "UCO", "SCO", "UVXY", "SVXY", "VXX", "VIXY", "TSLL", "TSLZ", "TSLQ", "NVDL", "NVDU", "NVDD", "NVDQ", "NVDX",
    "MSTU", "MSTX", "MSTZ", "CONL", "AMDL", "AAPU", "GGLL", "METU", "AMZU", "BITX", "ETHU", "SH", "PSQ", "DOG",
    "YINN", "YANG", "FNGU", "FNGD", "BULZ", "BERZ", "SMST", "PLTU", "HOOX", "DRAM",
}

MARKET_OPEN = "09:30"        # ET
OPENING_RANGE_MIN = 15       # opening range = first 15 minutes (9:30-9:45)
MIN_RANGE_BARS = 5
ENTRY_CUTOFF = "14:30"       # no new trades after this (ET)
FLATTEN_AT = "15:45"         # close everything after this (ET) - never hold overnight

# ---- Entries ----
ALLOW_SHORTS = True          # short breakdowns below the opening range
MARKET_FILTER = True         # longs only when SPY > its VWAP, shorts only when SPY < its VWAP
MAX_CHASE = 0.5              # skip if price is already > 0.5 range-widths past the breakout
MIN_RANGE_PCT = 0.002        # skip if opening range is tighter than 0.2% of price
MAX_RANGE_PCT = 0.04         # skip if opening range is wider than 4% of price

# ---- Risk ----
RISK_PER_TRADE = 0.005       # risk 0.5% of equity per trade (entry -> stop)
MAX_POSITION_PCT = 0.20      # no single position larger than 20% of equity
MAX_OPEN_POSITIONS = 5
MAX_GROSS_EXPOSURE = 1.5     # longs + shorts combined capped at 150% of equity
REWARD_RISK = 2.0            # profit target = 2x the risk
DAILY_LOSS_LIMIT = 0.025     # down 2.5% on the day -> close everything, stop for the day

# ---- AI desk (Google Gemini free tier). Set repo variable AI_FILTER=off to disable. ----
AI_FILTER = os.getenv("AI_FILTER", "on").lower() == "on"
AI_MODEL = os.getenv("AI_MODEL", "auto")  # "auto" tries free Flash models in order
NEWS_LOOKBACK_HOURS = 20
