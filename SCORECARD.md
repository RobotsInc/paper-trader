# Paper Trader Scorecard

_Simulated money only. Updated automatically after each trading day. Live view: the dashboard link in the README._

Since 2026-11-12 - 7 trading day(s)

**Beating buy-and-hold SPY by 7.56 points.** Only 7 trading day(s) so far - too early to judge (wait for 20+).

| | Bot | Buy & hold SPY |
|---|---|---|
| Return | -1.30% | -8.87% |
| Equity | $98,698.12 | $91,134.88 |

## Stats

| Metric | Value |
|---|---|
| Total P&L | -$1,301.88 |
| P&L after est. slippage (3 bps/side, what real money might see) | -$2,007.07 (-2.01%) |
| Trades | 60 |
| Win rate | 18% |
| Avg win / avg loss | $491.34 / -$136.51 |
| Profit factor | 0.81 |
| Max drawdown | -1.54% |
| Best / worst day | $916.84 / -$1,443.03 |
| Green days | 3 of 7 |
| Longs | 28 trades, -$2,969.79 |
| Shorts | 32 trades, $1,685.74 |

## Is the AI news filter helping?

The AI blocked 9 trade(s) the rules wanted. Simulated outcome of those trades: -$354.89 -> the filter has **saved $354.89**.

## Small-cap experiment ($5-$10 stocks: tracked, not traded)

Real bid-ask spread at signal time, main list: median **0.061%** over 107 signals (the backtest assumed 0.06% round trip).
Real spread, small caps: median **0.714%**.

| | Signals | Avg R before costs | Avg R after the spread | Won (after spread) |
|---|---|---|---|---|
| $5-$10 stocks | 2 | +3.298 | +2.876 | 1/2 |

R = profit as a multiple of the risk to the stop. Positive after the spread over 50+ signals would justify trading this tier; until then it's just watched.

![Equity vs SPY](data/equity.png)

## Recent days

| Date | P&L | Bot % | SPY % | Trades | AI blocked |
|---|---|---|---|---|---|
| 2026-11-20 | -$1,443.03 | -1.44% | -2.81% | 16 | 0 |
| 2026-11-19 | $916.84 | +0.92% | -2.80% | 9 | 1 |
| 2026-11-18 | -$198.80 | -0.20% | -0.38% | 8 | 0 |
| 2026-11-17 | $882.79 | +0.90% | -1.03% | 8 | 0 |
| 2026-11-16 | $100.00 | +0.10% | -1.43% | 8 | 5 |
| 2026-11-13 | -$486.51 | -0.49% | -0.97% | 5 | 0 |
| 2026-11-12 | -$1,055.34 | -1.05% | +0.37% | 6 | 3 |

## Recent trades

| Date | Symbol | Side | Qty | Entry | Exit | P&L |
|---|---|---|---|---|---|---|
| 2026-11-20 | GM | short | 243 | 80.74 | 79.3 | $350.43 |
| 2026-11-20 | C | short | 175 | 112.07 | 112.58 | -$89.11 |
| 2026-11-20 | MS | short | 116 | 169.47 | 170.17 | -$81.20 |
| 2026-11-20 | PINS | long | 1141 | 17.25 | 17.17 | -$86.75 |
| 2026-11-20 | UNH | long | 57 | 345.92 | 343.8 | -$120.56 |
| 2026-11-20 | COP | long | 145 | 135.87 | 137.05 | $170.71 |
| 2026-11-20 | GS | short | 24 | 814.37 | 819.38 | -$120.24 |
| 2026-11-20 | SLV | long | 519 | 38.22 | 38.03 | -$98.96 |
| 2026-11-20 | QQQ | short | 31 | 633.98 | 636.07 | -$64.87 |
| 2026-11-20 | SNDK | short | 230 | 86.19 | 87.83 | -$377.06 |
| 2026-11-20 | HOOD | short | 295 | 67.25 | 67.88 | -$185.85 |
| 2026-11-20 | AMGN | short | 45 | 440.18 | 441.87 | -$76.05 |
| 2026-11-20 | NFLX | long | 338 | 59.0 | 58.77 | -$77.74 |
| 2026-11-20 | ZS | long | 97 | 206.23 | 203.33 | -$281.30 |
| 2026-11-20 | SPOT | long | 33 | 594.39 | 588.79 | -$184.80 |
