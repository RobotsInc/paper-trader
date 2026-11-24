# v2 backtest: 2024-01-02 to 2024-12-30

127 trading days, 4042 trades. Each day replayed on a fresh $100,000 account with the real v2 engine.

## Result

| | Paper (perfect fills) | After est. slippage ("if live") |
|---|---|---|
| Total P&L | $11,295 | -$12,757 |
| Return on $100k (not compounded) | +11.29% | -12.76% |
| Win rate | 54.5% | 45.0% |
| Avg win / avg loss | $34 / -$34 | $34 / -$34 |
| Profit factor | 1.18 | 0.83 |
| Expectancy per trade | $3 | -$3 |

Estimated costs: $24,051 (213% of gross P&L). Max drawdown (daily, after costs): -$13,048. Green days: 43 of 127. Sharpe (daily, annualised): -4.91. Best / worst day: $930 / -$815.

S&P 500 (SPY) over the same period: +24.59%.

## By month

| Month | Trades | Win rate (after costs) | Paper P&L | Costs | After costs |
|---|---|---|---|---|---|
| 2024-01 | 403 | 41% | $578 | -$2,402 | -$1,824 |
| 2024-02 | 290 | 43% | -$585 | -$1,727 | -$2,312 |
| 2024-03 | 299 | 45% | $1,773 | -$1,780 | -$7 |
| 2024-04 | 351 | 46% | $1,409 | -$2,092 | -$683 |
| 2024-05 | 252 | 46% | $1,117 | -$1,500 | -$383 |
| 2024-06 | 270 | 48% | $2,146 | -$1,606 | $539 |
| 2024-07 | 339 | 40% | -$1,152 | -$2,014 | -$3,166 |
| 2024-08 | 441 | 46% | $925 | -$2,622 | -$1,697 |
| 2024-09 | 338 | 51% | $2,048 | -$2,014 | $34 |
| 2024-10 | 439 | 44% | $956 | -$2,612 | -$1,657 |
| 2024-11 | 330 | 49% | $2,245 | -$1,964 | $281 |
| 2024-12 | 290 | 42% | -$165 | -$1,718 | -$1,883 |

## Long vs short

| Side | Trades | Win rate (after costs) | After costs |
|---|---|---|---|
| long | 2014 | 45% | -$7,510 |
| short | 2028 | 45% | -$5,247 |

## How trades ended

| Exit | Trades | After costs |
|---|---|---|
| trailing stop | 1938 | $37,911 |
| stop loss | 1382 | -$67,978 |
| target | 456 | $20,337 |
| time stop | 195 | -$3,045 |
| flatten | 71 | $18 |

## Bot scorecard (trades each bot voted WITH)

| Bot | Trades | Win rate (after costs) | Avg after costs |
|---|---|---|---|
| trend | 3911 | 45% | -$3 |
| vwap | 3808 | 45% | -$3 |
| relvol | 3774 | 45% | -$3 |
| momentum | 2024 | 44% | -$4 |
| orb | 1144 | 47% | -$2 |
| meanrev | 7 | 29% | -$12 |

## Read this before trusting any number above

- **Fills are idealised.** Entries/exits happen at bar prices (stops at the stop price). The "after costs" column subtracts a modeled 3 bps per side (more when the spread is wide); real fills on fast moves are often worse.
- **Free IEX data only** (about 2.5% of US volume). Prices are real, volume is thin and noisy, and historical bid/ask spreads are not available, so the liquidity filter saw a fixed 3 bps spread.
- **No news bot** in the backtest (no free historical headline feed), so the AI veto never fired.
- **Days are independent** ($100k each day, nothing compounds), and the bot weights restart each month.
- **The settings were not tuned on this period unless the run is labelled otherwise.** Adjusting them to improve these numbers makes this period in-sample.
- A backtest says what the rules would have done, not what they will do. Paper trading for a few weeks is the real test.
