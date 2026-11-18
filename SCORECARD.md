# Paper Trader Scorecard

_Simulated money only. Updated automatically after each trading day. Live view: the dashboard link in the README._

Since 2026-11-12 - 5 trading day(s)

**Beating buy-and-hold SPY by 3.22 points.** Only 5 trading day(s) so far - too early to judge (wait for 20+).

| | Bot | Buy & hold SPY |
|---|---|---|
| Return | -0.77% | -3.98% |
| Equity | $99,231.31 | $96,015.56 |

## Stats

| Metric | Value |
|---|---|
| Total P&L | -$768.69 |
| P&L after est. slippage (3 bps/side, what real money might see) | -$1,178.23 (-1.18%) |
| Trades | 35 |
| Win rate | 20% |
| Avg win / avg loss | $437.73 / -$136.50 |
| Profit factor | 0.80 |
| Max drawdown | -1.54% |
| Best / worst day | $882.79 / -$1,055.34 |
| Green days | 2 of 5 |
| Longs | 15 trades, -$1,400.77 |
| Shorts | 20 trades, $642.91 |

## Is the AI news filter helping?

The AI blocked 8 trade(s) the rules wanted. Simulated outcome of those trades: -$48.38 -> the filter has **saved $48.38**.

## Small-cap experiment ($5-$10 stocks: tracked, not traded)

Real bid-ask spread at signal time, main list: median **0.055%** over 74 signals (the backtest assumed 0.06% round trip).
Real spread, small caps: median **0.714%**.

| | Signals | Avg R before costs | Avg R after the spread | Won (after spread) |
|---|---|---|---|---|
| $5-$10 stocks | 2 | +3.298 | +2.876 | 1/2 |

R = profit as a multiple of the risk to the stop. Positive after the spread over 50+ signals would justify trading this tier; until then it's just watched.

![Equity vs SPY](data/equity.png)

## Recent days

| Date | P&L | Bot % | SPY % | Trades | AI blocked |
|---|---|---|---|---|---|
| 2026-11-18 | -$198.80 | -0.20% | -0.38% | 8 | 0 |
| 2026-11-17 | $882.79 | +0.90% | -1.03% | 8 | 0 |
| 2026-11-16 | $100.00 | +0.10% | -1.43% | 8 | 5 |
| 2026-11-13 | -$486.51 | -0.49% | -0.97% | 5 | 0 |
| 2026-11-12 | -$1,055.34 | -1.05% | +0.37% | 6 | 3 |

## Recent trades

| Date | Symbol | Side | Qty | Entry | Exit | P&L |
|---|---|---|---|---|---|---|
| 2026-11-18 | BRBR | short | 1554 | 12.83 | 12.96 | -$202.02 |
| 2026-11-18 | CRM | short | 105 | 188.8 | 189.91 | -$116.21 |
| 2026-11-18 | XLE | short | 320 | 62.22 | 62.39 | -$55.82 |
| 2026-11-18 | MSTR | short | 214 | 92.74 | 93.6 | -$184.76 |
| 2026-11-18 | DASH | long | 119 | 167.16 | 165.57 | -$189.21 |
| 2026-11-18 | SLV | short | 487 | 40.79 | 40.95 | -$77.92 |
| 2026-11-18 | PRMB | long | 883 | 22.5 | 22.37 | -$114.79 |
| 2026-11-18 | MDLN | long | 528 | 37.66 | 39.07 | $741.93 |
| 2026-11-17 | SLB | short | 396 | 49.95 | 49.04 | $360.36 |
| 2026-11-17 | DRAM | short | 511 | 38.72 | 39.09 | -$188.65 |
| 2026-11-17 | HD | long | 57 | 342.45 | 339.42 | -$172.90 |
| 2026-11-17 | SBUX | long | 179 | 109.8 | 109.4 | -$71.60 |
| 2026-11-17 | CRM | short | 95 | 205.32 | 194.42 | $1,035.50 |
| 2026-11-17 | UNH | short | 50 | 390.36 | 391.96 | -$80.32 |
| 2026-11-17 | MRNA | short | 94 | 208.32 | 210.38 | -$194.08 |
