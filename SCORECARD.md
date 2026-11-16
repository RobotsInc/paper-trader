# Paper Trader Scorecard

_Simulated money only. Updated automatically after each trading day. Live view: the dashboard link in the README._

Since 2026-11-12 - 3 trading day(s)

**Beating buy-and-hold SPY by 1.44 points.** Only 3 trading day(s) so far - too early to judge (wait for 20+).

| | Bot | Buy & hold SPY |
|---|---|---|
| Return | -1.45% | -2.89% |
| Equity | $98,553.79 | $97,109.57 |

## Stats

| Metric | Value |
|---|---|
| Total P&L | -$1,446.21 |
| P&L after est. slippage (3 bps/side, what real money might see) | -$1,666.28 (-1.67%) |
| Trades | 19 |
| Win rate | 16% |
| Avg win / avg loss | $243.94 / -$135.85 |
| Profit factor | 0.34 |
| Max drawdown | -1.54% |
| Best / worst day | $100.00 / -$1,055.34 |
| Green days | 1 of 3 |
| Longs | 10 trades, -$1,594.20 |
| Shorts | 9 trades, $152.35 |

## Is the AI news filter helping?

The AI blocked 8 trade(s) the rules wanted. Simulated outcome of those trades: -$48.38 -> the filter has **saved $48.38**.

## Small-cap experiment ($5-$10 stocks: tracked, not traded)

Real bid-ask spread at signal time, main list: median **0.034%** over 34 signals (the backtest assumed 0.06% round trip).
Real spread, small caps: median **0.169%**.

| | Signals | Avg R before costs | Avg R after the spread | Won (after spread) |
|---|---|---|---|---|
| $5-$10 stocks | 1 | -1.000 | -1.117 | 0/1 |

R = profit as a multiple of the risk to the stop. Positive after the spread over 50+ signals would justify trading this tier; until then it's just watched.

![Equity vs SPY](data/equity.png)

## Recent days

| Date | P&L | Bot % | SPY % | Trades | AI blocked |
|---|---|---|---|---|---|
| 2026-11-16 | $100.00 | +0.10% | -1.43% | 8 | 5 |
| 2026-11-13 | -$486.51 | -0.49% | -0.97% | 5 | 0 |
| 2026-11-12 | -$1,055.34 | -1.05% | +0.37% | 6 | 3 |

## Recent trades

| Date | Symbol | Side | Qty | Entry | Exit | P&L |
|---|---|---|---|---|---|---|
| 2026-11-16 | ADBE | long | 78 | 249.97 | 249.0 | -$75.66 |
| 2026-11-16 | XLK | short | 118 | 165.37 | 166.01 | -$76.35 |
| 2026-11-16 | TSM | short | 51 | 378.22 | 373.66 | $232.40 |
| 2026-11-16 | COIN | long | 161 | 121.8 | 120.61 | -$191.39 |
| 2026-11-16 | USO | short | 138 | 142.03 | 142.65 | -$85.53 |
| 2026-11-16 | NFLX | short | 319 | 61.67 | 61.88 | -$66.04 |
| 2026-11-16 | IBIT | long | 530 | 37.07 | 36.95 | -$64.31 |
| 2026-11-16 | DE | short | 29 | 668.84 | 654.12 | $426.88 |
| 2026-11-13 | NFLX | long | 310 | 63.78 | 63.61 | -$53.56 |
| 2026-11-13 | CSCO | short | 205 | 96.18 | 96.63 | -$92.25 |
| 2026-11-13 | AMAT | short | 54 | 360.46 | 363.82 | -$181.23 |
| 2026-11-13 | IBIT | short | 508 | 38.88 | 39.03 | -$78.06 |
| 2026-11-13 | KDP | long | 544 | 36.35 | 36.2 | -$81.41 |
| 2026-11-12 | NKE | short | 524 | 37.95 | 37.81 | $72.53 |
| 2026-11-12 | TQQQ | long | 234 | 60.87 | 59.72 | -$269.10 |
