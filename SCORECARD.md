# Paper Trader Scorecard

_Simulated money only. Updated automatically after each trading day. Live view: the dashboard link in the README._

Since 2026-11-12 - 2 trading day(s)

**Trailing buy-and-hold SPY by 0.44 points.** Only 2 trading day(s) so far - too early to judge (wait for 20+).

| | Bot | Buy & hold SPY |
|---|---|---|
| Return | -1.54% | -1.10% |
| Equity | $98,455.83 | $98,900.07 |

## Stats

| Metric | Value |
|---|---|
| Total P&L | -$1,544.17 |
| P&L after est. slippage (3 bps/side, what real money might see) | -$1,670.73 (-1.67%) |
| Trades | 11 |
| Win rate | 9% |
| Avg win / avg loss | $72.53 / -$161.44 |
| Profit factor | 0.04 |
| Max drawdown | -1.54% |
| Best / worst day | -$486.51 / -$1,055.34 |
| Green days | 0 of 2 |
| Longs | 7 trades, -$1,262.84 |
| Shorts | 4 trades, -$279.01 |

## Is the AI news filter helping?

The AI blocked 3 trade(s) the rules wanted. Simulated outcome of those trades: -$365.45 -> the filter has **saved $365.45**.

## Small-cap experiment ($5-$10 stocks: tracked, not traded)

Real bid-ask spread at signal time, main list: median **0.034%** over 26 signals (the backtest assumed 0.06% round trip).


![Equity vs SPY](data/equity.png)

## Recent days

| Date | P&L | Bot % | SPY % | Trades | AI blocked |
|---|---|---|---|---|---|
| 2026-11-13 | -$486.51 | -0.49% | -0.97% | 5 | 0 |
| 2026-11-12 | -$1,055.34 | -1.05% | +0.37% | 6 | 3 |

## Recent trades

| Date | Symbol | Side | Qty | Entry | Exit | P&L |
|---|---|---|---|---|---|---|
| 2026-11-13 | NFLX | long | 310 | 63.78 | 63.61 | -$53.56 |
| 2026-11-13 | CSCO | short | 205 | 96.18 | 96.63 | -$92.25 |
| 2026-11-13 | AMAT | short | 54 | 360.46 | 363.82 | -$181.23 |
| 2026-11-13 | IBIT | short | 508 | 38.88 | 39.03 | -$78.06 |
| 2026-11-13 | KDP | long | 544 | 36.35 | 36.2 | -$81.41 |
| 2026-11-12 | NKE | short | 524 | 37.95 | 37.81 | $72.53 |
| 2026-11-12 | TQQQ | long | 234 | 60.87 | 59.72 | -$269.10 |
| 2026-11-12 | ARKK | long | 258 | 77.23 | 76.47 | -$194.94 |
| 2026-11-12 | HOOD | long | 239 | 83.73 | 81.79 | -$463.65 |
| 2026-11-12 | MSFT | long | 37 | 528.25 | 525.25 | -$111.00 |
| 2026-11-12 | QQQ | long | 28 | 690.73 | 687.54 | -$89.18 |
