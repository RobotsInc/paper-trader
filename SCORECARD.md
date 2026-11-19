# Paper Trader Scorecard

_Simulated money only. Updated automatically after each trading day. Live view: the dashboard link in the README._

Since 2026-11-12 - 6 trading day(s)

**Beating buy-and-hold SPY by 5.93 points.** Only 6 trading day(s) so far - too early to judge (wait for 20+).

| | Bot | Buy & hold SPY |
|---|---|---|
| Return | +0.14% | -5.79% |
| Equity | $100,144.83 | $94,211.26 |

## Stats

| Metric | Value |
|---|---|
| Total P&L | $144.83 |
| P&L after est. slippage (3 bps/side, what real money might see) | -$370.76 (-0.37%) |
| Trades | 44 |
| Win rate | 20% |
| Avg win / avg loss | $542.62 / -$134.99 |
| Profit factor | 1.03 |
| Max drawdown | -1.54% |
| Best / worst day | $916.84 / -$1,055.34 |
| Green days | 3 of 6 |
| Longs | 20 trades, -$2,170.71 |
| Shorts | 24 trades, $2,329.69 |

## Is the AI news filter helping?

The AI blocked 9 trade(s) the rules wanted. Simulated outcome of those trades: -$354.89 -> the filter has **saved $354.89**.

## Small-cap experiment ($5-$10 stocks: tracked, not traded)

Real bid-ask spread at signal time, main list: median **0.061%** over 89 signals (the backtest assumed 0.06% round trip).
Real spread, small caps: median **0.714%**.

| | Signals | Avg R before costs | Avg R after the spread | Won (after spread) |
|---|---|---|---|---|
| $5-$10 stocks | 2 | +3.298 | +2.876 | 1/2 |

R = profit as a multiple of the risk to the stop. Positive after the spread over 50+ signals would justify trading this tier; until then it's just watched.

![Equity vs SPY](data/equity.png)

## Recent days

| Date | P&L | Bot % | SPY % | Trades | AI blocked |
|---|---|---|---|---|---|
| 2026-11-19 | $916.84 | +0.92% | -2.80% | 9 | 1 |
| 2026-11-18 | -$198.80 | -0.20% | -0.38% | 8 | 0 |
| 2026-11-17 | $882.79 | +0.90% | -1.03% | 8 | 0 |
| 2026-11-16 | $100.00 | +0.10% | -1.43% | 8 | 5 |
| 2026-11-13 | -$486.51 | -0.49% | -0.97% | 5 | 0 |
| 2026-11-12 | -$1,055.34 | -1.05% | +0.37% | 6 | 3 |

## Recent trades

| Date | Symbol | Side | Qty | Entry | Exit | P&L |
|---|---|---|---|---|---|---|
| 2026-11-19 | WMT | long | 157 | 125.37 | 125.11 | -$40.82 |
| 2026-11-19 | MSTR | short | 215 | 92.38 | 86.88 | $1,183.17 |
| 2026-11-19 | IREN | long | 1216 | 16.28 | 16.05 | -$274.69 |
| 2026-11-19 | BA | long | 120 | 164.15 | 163.51 | -$76.75 |
| 2026-11-19 | MCD | short | 74 | 267.78 | 268.88 | -$81.41 |
| 2026-11-19 | AMGN | short | 45 | 440.53 | 441.67 | -$51.33 |
| 2026-11-19 | MRK | short | 145 | 136.57 | 132.18 | $636.35 |
| 2026-11-19 | DDOG | long | 110 | 179.77 | 177.75 | -$222.20 |
| 2026-11-19 | ZS | long | 92 | 214.38 | 212.69 | -$155.48 |
| 2026-11-18 | BRBR | short | 1554 | 12.83 | 12.96 | -$202.02 |
| 2026-11-18 | CRM | short | 105 | 188.8 | 189.91 | -$116.21 |
| 2026-11-18 | XLE | short | 320 | 62.22 | 62.39 | -$55.82 |
| 2026-11-18 | MSTR | short | 214 | 92.74 | 93.6 | -$184.76 |
| 2026-11-18 | DASH | long | 119 | 167.16 | 165.57 | -$189.21 |
| 2026-11-18 | SLV | short | 487 | 40.79 | 40.95 | -$77.92 |
