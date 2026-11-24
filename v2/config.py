"""Paper Trader v2 settings. Everything tunable lives here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "v2"

# ---- Universe: liquid large caps (edit freely) ----
WATCHLIST = [
    "SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    "AMD", "AVGO", "NFLX", "JPM", "BAC", "XOM", "WMT", "COST", "DIS", "BA",
    "INTC", "PLTR", "COIN", "UBER", "CRM", "ORCL", "MU", "UNH", "V", "SOFI",
]
ALLOW_SHORTS = True

# ---- Timing (ET). Open/close come from Alpaca's calendar, so half days work. ----
SCAN_SECONDS = 30            # one full scan of the watchlist this often
FIRST_ENTRY_MIN_AFTER_OPEN = 15     # opening range = first 15 minutes; no trades before it's set
LAST_ENTRY_MIN_BEFORE_CLOSE = 30
FLATTEN_MIN_BEFORE_CLOSE = 10       # everything is closed by then: nothing is held overnight
MAX_NEW_ENTRIES_PER_SCAN = 3
COOLDOWN_MIN = 20

# ---- Risk (the risk bot enforces all of these) ----
RISK_PER_TRADE = 0.005       # risk 0.5% of equity per trade (entry -> stop) ...
MAX_POSITION_PCT = 0.10      # ... but never more than 10% of equity in one stock
MAX_OPEN_POSITIONS = 15
MAX_OPEN_RISK = 0.03         # total risk still on the table (stops that are not yet at breakeven) <= 3% of equity
MAX_GROSS = 2.0              # longs + shorts <= 200% of equity (paper account has 4x intraday buying power)
DAILY_LOSS_LIMIT = 0.03      # down 3% on the day -> close everything, stop for the day

# ---- Entries / stops ----
STOP_ATR_MULT = 4.0          # stop distance = 4 x the 1-minute ATR ...
MIN_STOP_PCT = 0.0035
MAX_STOP_PCT = 0.0080
TARGET_R = 1.0               # take profit at 1x risk unless the exit manager sees it running
ENTRY_SCORE = 0.45
MIN_AGREE = 3                # at least this many signal bots must agree
MIN_RVOL = 1.2               # volume filter
MAX_SPREAD_BPS = 15          # liquidity filter (free IEX quotes are noisy, so this is generous)
MAX_COST_TO_TARGET = 0.20

# ---- Exit manager ----
MAX_HOLD_MIN = 60            # close a trade that has gone nowhere (< 0.3R) after an hour
# peak R reached -> lock in this much (in R). Only ever tightens.
RATCHET = [(1.5, "trail"), (1.0, 0.5), (0.6, 0.2), (0.4, 0.0)]
TRAIL_BEHIND_R = 0.5

# ---- Cost model (what the report calls "if this were live") ----
SLIPPAGE_BPS_PER_SIDE = 3    # floor, per side; matches the 0.03%/side used in the old backtest
SLIPPAGE_SPREAD_FRACTION = 0.5   # or half the quoted spread, whichever is larger
SLIPPAGE_CAP_BPS = 15

# ---- Reporting / bot weights ----
MIN_VOTES_FOR_WEIGHT = 30    # a bot's weight moves off 1.0 only after this many trades it agreed with
GIT_SYNC_SECONDS = 180

# Market-direction gate (from the 2024/2026 analysis: the bots only made money when aligned with the market's trend).
MARKET_GATE = True
MARKET_MIN_MOVE = 0.0010      # SPY must be this far (0.10%) from its open AND on the same side of its VWAP
