# Small-stock ($5-10) backtest

2025-11-15 -> 2026-11-15. Paper recipe: top 15 by opening relative volume, 5-min range, first-candle direction, 10% ATR stop, hold to 15:45. Costs: real median SIP bid-ask spread at entry (charged in and out) + 3 bps slippage per side.

## Per trade (R = profit / initial risk)

| Set | Before costs | After spread + slippage |
|---|---|---|
| All (no ATR floor) | 2854 trades · win 16% · avg +0.317R · t = +4.1 | 2854 trades · win 15% · avg -0.447R · t = -5.7 |
| Live rules (ATR ≥ $0.50) | 793 trades · win 17% · avg +0.377R · t = +2.6 | 793 trades · win 16% · avg -0.218R · t = -1.5 |
| Train (first 2/3) | 1908 trades · win 15% · avg +0.297R · t = +3.2 | 1908 trades · win 15% · avg -0.458R · t = -4.9 |
| Test (last 1/3) | 946 trades · win 17% · avg +0.359R · t = +2.5 | 946 trades · win 16% · avg -0.426R · t = -3.0 |
| Longs | 1492 trades · win 14% · avg +0.266R · t = +2.5 | 1492 trades · win 14% · avg -0.519R · t = -4.9 |
| Shorts | 1362 trades · win 17% · avg +0.374R · t = +3.3 | 1362 trades · win 17% · avg -0.369R · t = -3.2 |

## By opening spread

| Spread at entry | After costs |
|---|---|
| 0–0.1% | 61 trades · win 15% · avg +0.304R · t = +0.5 |
| 0.1–0.25% | 1606 trades · win 15% · avg -0.415R · t = -4.9 |
| 0.25–0.5% | 674 trades · win 16% · avg -0.351R · t = -2.2 |
| 0.5–1% | 358 trades · win 15% · avg -0.371R · t = -1.1 |
| 1–∞% | 155 trades · win 14% · avg -1.675R · t = -3.9 |

Median entry spread: 0.20%

## As an account ($100k, one small-stock position at a time, 0.5% risk)

| Rules | Size cap | Return | Max drawdown | Trades taken |
|---|---|---|---|---|
| All | 10% | -18.7% | -21.6% | 710 |
| All | 20% | -33.5% | -38.1% | 710 |
| Live rules (ATR ≥ $0.50) | 10% | -11.2% | -14.1% | 427 |
| Live rules (ATR ≥ $0.50) | 20% | -21.0% | -26.0% | 427 |
| Skip if spread > 0.25% | 10% | -7.0% | -10.8% | 629 |
| Skip if spread > 0.25% | 20% | -13.6% | -20.4% | 629 |
| ATR ≥ $0.50 and spread ≤ 0.25% | 10% | +6.7% | -3.7% | 258 |
| ATR ≥ $0.50 and spread ≤ 0.25% | 20% | +13.6% | -7.2% | 258 |

Caveats: stocks delisted during the year are missing; 1-minute bars; the spread is measured, but the fill could be worse on size in a thin stock; halts aren't modelled.
