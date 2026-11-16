# Small-stock ($5-10) backtest

2026-10-16 -> 2026-11-15. Paper recipe: top 15 by opening relative volume, 5-min range, first-candle direction, 10% ATR stop, hold to 15:45. Costs: real median SIP bid-ask spread at entry (charged in and out) + 3 bps slippage per side.

## Per trade (R = profit / initial risk)

| Set | Before costs | After spread + slippage |
|---|---|---|
| All (no ATR floor) | 247 trades · win 20% · avg +1.172R · t = +2.7 | 247 trades · win 19% · avg +0.293R · t = +0.7 |
| Live rules (ATR ≥ $0.50) | 63 trades · win 19% · avg +0.336R · t = +0.7 | 63 trades · win 14% · avg -0.451R · t = -0.9 |
| Train (first 2/3) | 167 trades · win 20% · avg +0.877R · t = +2.3 | 167 trades · win 19% · avg -0.047R · t = -0.1 |
| Test (last 1/3) | 80 trades · win 20% · avg +1.786R · t = +1.7 | 80 trades · win 18% · avg +1.001R · t = +1.0 |
| Longs | 119 trades · win 21% · avg +1.287R · t = +2.3 | 119 trades · win 20% · avg +0.382R · t = +0.7 |
| Shorts | 128 trades · win 19% · avg +1.064R · t = +1.6 | 128 trades · win 17% · avg +0.209R · t = +0.3 |

## By opening spread

| Spread at entry | After costs |
|---|---|
| 0–0.1% | 5 trades · win 0% · avg -1.192R · t = -5.3 |
| 0.1–0.25% | 140 trades · win 21% · avg +0.169R · t = +0.5 |
| 0.25–0.5% | 48 trades · win 17% · avg +0.417R · t = +0.5 |
| 0.5–1% | 38 trades · win 13% · avg +0.620R · t = +0.3 |
| 1–∞% | 16 trades · win 19% · avg +0.692R · t = +0.2 |

Median entry spread: 0.20%

## As an account ($100k, one small-stock position at a time, 0.5% risk)

| Rules | Size cap | Return | Max drawdown | Trades taken |
|---|---|---|---|---|
| All | 10% | -1.4% | -2.9% | 49 |
| All | 20% | -2.8% | -5.7% | 49 |
| Live rules (ATR ≥ $0.50) | 10% | -3.7% | -3.9% | 26 |
| Live rules (ATR ≥ $0.50) | 20% | -7.4% | -7.6% | 26 |
| Skip if spread > 0.25% | 10% | -0.0% | -0.9% | 45 |
| Skip if spread > 0.25% | 20% | -0.0% | -1.9% | 45 |
| ATR ≥ $0.50 and spread ≤ 0.25% | 10% | +1.1% | -0.8% | 16 |
| ATR ≥ $0.50 and spread ≤ 0.25% | 20% | +2.3% | -1.6% | 16 |

Caveats: stocks delisted during the year are missing; 1-minute bars; the spread is measured, but the fill could be worse on size in a thin stock; halts aren't modelled.
