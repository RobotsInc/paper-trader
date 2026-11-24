# v2 backtest: 2025-01-02 to 2025-12-30

128 trading days, 865 trades. Each day replayed on a fresh $100,000 account with the real v2 engine.

## Result

| | Paper (perfect fills) | After est. slippage ("if live") |
|---|---|---|
| Total P&L | $2,228 | -$2,898 |
| Return on $100k (not compounded) | +2.23% | -2.90% |
| Win rate | 54.3% | 46.4% |
| Avg win / avg loss | $41 / -$43 | $42 / -$42 |
| Profit factor | 1.13 | 0.85 |
| Expectancy per trade | $3 | -$3 |

Estimated costs: $5,126 (230% of gross P&L). Max drawdown (daily, after costs): -$4,860. Green days: 43 of 128. Sharpe (daily, annualised): -1.75. Best / worst day: $1,220 / -$522.

S&P 500 (SPY) over the same period: +16.55%.

## By month

| Month | Trades | Win rate (after costs) | Paper P&L | Costs | After costs |
|---|---|---|---|---|---|
| 2025-01 | 102 | 38% | -$124 | -$603 | -$727 |
| 2025-02 | 85 | 55% | $1,239 | -$504 | $735 |
| 2025-03 | 58 | 55% | $800 | -$344 | $455 |
| 2025-04 | 119 | 56% | $1,361 | -$710 | $651 |
| 2025-05 | 71 | 46% | -$163 | -$421 | -$583 |
| 2025-06 | 49 | 43% | $125 | -$290 | -$165 |
| 2025-07 | 46 | 35% | -$175 | -$273 | -$448 |
| 2025-08 | 86 | 47% | -$253 | -$510 | -$763 |
| 2025-09 | 62 | 44% | $12 | -$367 | -$355 |
| 2025-10 | 66 | 44% | -$47 | -$390 | -$437 |
| 2025-11 | 72 | 42% | -$430 | -$426 | -$855 |
| 2025-12 | 49 | 41% | -$117 | -$289 | -$406 |

## Long vs short

| Side | Trades | Win rate (after costs) | After costs |
|---|---|---|---|
| long | 411 | 44% | -$1,973 |
| short | 454 | 49% | -$925 |

## How trades ended

| Exit | Trades | After costs |
|---|---|---|
| trailing stop | 423 | $11,081 |
| stop loss | 262 | -$17,020 |
| time stop | 93 | -$1,483 |
| target | 68 | $4,204 |
| flatten | 19 | $321 |

## Bot scorecard (trades each bot voted WITH)

| Bot | Trades | Win rate (after costs) | Avg after costs |
|---|---|---|---|
| trend | 865 | 46% | -$3 |
| relvol | 854 | 47% | -$3 |
| vwap | 836 | 46% | -$3 |
| momentum | 657 | 45% | -$5 |
| orb | 403 | 48% | -$2 |

## Read this before trusting any number above

- **Fills are idealised.** Entries/exits happen at bar prices (stops at the stop price). The "after costs" column subtracts a modeled 3 bps per side (more when the spread is wide); real fills on fast moves are often worse.
- **Free IEX data only** (about 2.5% of US volume). Prices are real, volume is thin and noisy, and historical bid/ask spreads are not available, so the liquidity filter saw a fixed 3 bps spread.
- **No news bot** in the backtest (no free historical headline feed), so the AI veto never fired.
- **Days are independent** ($100k each day, nothing compounds), and the bot weights restart each month.
- **The settings were not tuned on this period unless the run is labelled otherwise.** Adjusting them to improve these numbers makes this period in-sample.
- A backtest says what the rules would have done, not what they will do. Paper trading for a few weeks is the real test.
