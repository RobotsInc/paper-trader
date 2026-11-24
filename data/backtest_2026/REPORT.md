# v2 backtest: 2026-01-02 to 2026-10-29

107 trading days, 1178 trades. Each day replayed on a fresh $100,000 account with the real v2 engine.

## Result

| | Paper (perfect fills) | After est. slippage ("if live") |
|---|---|---|
| Total P&L | $1,230 | -$5,738 |
| Return on $100k (not compounded) | +1.23% | -5.74% |
| Win rate | 55.3% | 46.6% |
| Avg win / avg loss | $37 / -$44 | $38 / -$43 |
| Profit factor | 1.05 | 0.79 |
| Expectancy per trade | $1 | -$5 |

Estimated costs: $6,969 (566% of gross P&L). Max drawdown (daily, after costs): -$6,873. Green days: 48 of 107. Sharpe (daily, annualised): -3.66. Best / worst day: $825 / -$705.

S&P 500 (SPY) over the same period: +12.25%.

## By month

| Month | Trades | Win rate (after costs) | Paper P&L | Costs | After costs |
|---|---|---|---|---|---|
| 2026-01 | 228 | 50% | $1,641 | -$1,352 | $289 |
| 2026-02 | 95 | 43% | $145 | -$564 | -$419 |
| 2026-03 | 65 | 54% | $461 | -$383 | $77 |
| 2026-04 | 128 | 49% | $709 | -$758 | -$49 |
| 2026-05 | 97 | 41% | -$651 | -$573 | -$1,225 |
| 2026-06 | 116 | 54% | $602 | -$685 | -$83 |
| 2026-07 | 130 | 45% | -$390 | -$767 | -$1,157 |
| 2026-08 | 77 | 51% | $356 | -$456 | -$99 |
| 2026-09 | 116 | 32% | -$1,660 | -$686 | -$2,346 |
| 2026-10 | 126 | 45% | $17 | -$744 | -$727 |

## Long vs short

| Side | Trades | Win rate (after costs) | After costs |
|---|---|---|---|
| long | 619 | 48% | -$1,813 |
| short | 559 | 45% | -$3,926 |

## How trades ended

| Exit | Trades | After costs |
|---|---|---|
| trailing stop | 538 | $13,029 |
| stop loss | 344 | -$22,451 |
| time stop | 153 | -$2,615 |
| target | 101 | $6,244 |
| flatten | 42 | $55 |

## Bot scorecard (trades each bot voted WITH)

| Bot | Trades | Win rate (after costs) | Avg after costs |
|---|---|---|---|
| trend | 1178 | 47% | -$5 |
| relvol | 1173 | 47% | -$5 |
| vwap | 1146 | 47% | -$4 |
| momentum | 868 | 45% | -$6 |
| orb | 580 | 48% | -$3 |

## Read this before trusting any number above

- **Fills are idealised.** Entries/exits happen at bar prices (stops at the stop price). The "after costs" column subtracts a modeled 3 bps per side (more when the spread is wide); real fills on fast moves are often worse.
- **Free IEX data only** (about 2.5% of US volume). Prices are real, volume is thin and noisy, and historical bid/ask spreads are not available, so the liquidity filter saw a fixed 3 bps spread.
- **No news bot** in the backtest (no free historical headline feed), so the AI veto never fired.
- **Days are independent** ($100k each day, nothing compounds), and the bot weights restart each month.
- **The settings were not tuned on this period unless the run is labelled otherwise.** Adjusting them to improve these numbers makes this period in-sample.
- A backtest says what the rules would have done, not what they will do. Paper trading for a few weeks is the real test.
