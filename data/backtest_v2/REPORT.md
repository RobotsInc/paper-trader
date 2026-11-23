# v2 backtest: 2025-01-02 to 2025-12-31

249 trading days, 10223 trades. Each day replayed on a fresh $100,000 account with the real v2 engine.

## Result

| | Paper (perfect fills) | After est. slippage ("if live") |
|---|---|---|
| Total P&L | $12,705 | -$47,986 |
| Return on $100k (not compounded) | +12.71% | -47.99% |
| Win rate | 55.0% | 44.8% |
| Avg win / avg loss | $32 / -$36 | $33 / -$35 |
| Profit factor | 1.08 | 0.76 |
| Expectancy per trade | $1 | -$5 |

Estimated costs: $60,691 (478% of gross P&L). Max drawdown (daily, after costs): -$48,079. Green days: 64 of 249. Sharpe (daily, annualised): -6.42. Best / worst day: $1,642 / -$4,327.

S&P 500 (SPY) over the same period: +15.68%.

## By month

| Month | Trades | Win rate (after costs) | Paper P&L | Costs | After costs |
|---|---|---|---|---|---|
| 2025-01 | 1110 | 45% | $1,678 | -$6,591 | -$4,913 |
| 2025-02 | 881 | 45% | $2,171 | -$5,236 | -$3,065 |
| 2025-03 | 934 | 46% | $1,800 | -$5,543 | -$3,743 |
| 2025-04 | 1242 | 50% | $6,369 | -$7,424 | -$1,055 |
| 2025-05 | 764 | 41% | -$2,055 | -$4,533 | -$6,588 |
| 2025-06 | 741 | 43% | $1,608 | -$4,400 | -$2,792 |
| 2025-07 | 662 | 43% | -$1,291 | -$3,925 | -$5,215 |
| 2025-08 | 710 | 46% | $1,094 | -$4,216 | -$3,122 |
| 2025-09 | 785 | 42% | -$444 | -$4,650 | -$5,094 |
| 2025-10 | 968 | 45% | $339 | -$5,728 | -$5,389 |
| 2025-11 | 876 | 46% | $1,873 | -$5,193 | -$3,320 |
| 2025-12 | 550 | 42% | -$438 | -$3,253 | -$3,690 |

## Long vs short

| Side | Trades | Win rate (after costs) | After costs |
|---|---|---|---|
| long | 4965 | 44% | -$28,367 |
| short | 5258 | 45% | -$19,619 |

## How trades ended

| Exit | Trades | After costs |
|---|---|---|
| trailing stop | 5116 | $88,705 |
| stop loss | 3488 | -$180,110 |
| target | 1090 | $48,495 |
| time stop | 421 | -$5,934 |
| flatten | 108 | $858 |

## Bot scorecard (trades each bot voted WITH)

| Bot | Trades | Win rate (after costs) | Avg after costs |
|---|---|---|---|
| trend | 9938 | 45% | -$5 |
| vwap | 9733 | 45% | -$5 |
| relvol | 9442 | 45% | -$5 |
| momentum | 4982 | 44% | -$5 |
| orb | 2609 | 46% | -$4 |
| meanrev | 19 | 26% | -$22 |

## Read this before trusting any number above

- **Fills are idealised.** Entries/exits happen at bar prices (stops at the stop price). The "after costs" column subtracts a modeled 3 bps per side (more when the spread is wide); real fills on fast moves are often worse.
- **Free IEX data only** (about 2.5% of US volume). Prices are real, volume is thin and noisy, and historical bid/ask spreads are not available, so the liquidity filter saw a fixed 3 bps spread.
- **No news bot** in the backtest (no free historical headline feed), so the AI veto never fired.
- **Days are independent** ($100k each day, nothing compounds), and the bot weights restart each month.
- **The settings were chosen in advance, not tuned on 2025.** If you now adjust them to improve these numbers, the next backtest becomes in-sample and will flatter the bot.
- A backtest says what the rules would have done, not what they will do. Paper trading for a few weeks is the real test.
