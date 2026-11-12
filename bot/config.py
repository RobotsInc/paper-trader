"""Strategy settings. Change these to tune the bot."""
import os

# Liquid names that move enough intraday to trade breakouts.
WATCHLIST = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD"]

MARKET_OPEN = "09:30"        # ET
OPENING_RANGE_MIN = 15       # opening range = first 15 minutes (9:30-9:45)
MIN_RANGE_BARS = 5           # need at least this many 1-min bars to trust the range
ENTRY_CUTOFF = "14:30"       # no new trades after this (ET)
FLATTEN_AT = "15:45"         # close everything after this (ET) - never hold overnight

RISK_PER_TRADE = 0.005       # risk 0.5% of equity per trade (entry -> stop)
MAX_POSITION_PCT = 0.20      # no single position larger than 20% of equity
MAX_OPEN_POSITIONS = 3
REWARD_RISK = 2.0            # profit target = 2x the risk
MAX_CHASE = 0.5              # skip if price is already > 0.5 range-widths above the breakout
MIN_RANGE_PCT = 0.002        # skip if opening range is tighter than 0.2% of price
MAX_RANGE_PCT = 0.03         # skip if opening range is wider than 3% of price
DAILY_LOSS_LIMIT = 0.02      # down 2% on the day -> close everything, stop for the day

# AI news filter (GitHub Models, free). Set repo variable AI_FILTER=off to disable.
AI_FILTER = os.getenv("AI_FILTER", "on").lower() == "on"
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-4o-mini")
NEWS_LOOKBACK_HOURS = 20
