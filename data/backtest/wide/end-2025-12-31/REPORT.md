# Whole-market backtest: 2024-12-31 to 2025-12-31

- Universe: 13757 listed US stocks/ETFs (active + delisted), median 2092 liquid enough to watch each day; top 20 by opening relative volume traded.
- Live bot rules: first-candle direction, 5-min range break, don't chase > 0.2 ATR, 10% ATR stop, min stop 0.25%, hold to 15:45, price ≥ $5, ATR ≥ $0.50, avg volume ≥ 1M.
- Costs: real SIP bid-ask spread at entry (half in, half out) + 3 bps/side.
- Account: $100k with the live bot's limits (0.5% risk, 5 positions, 3/side, 20%/position, 150% gross, 2.5% daily loss limit).
- **SPY buy & hold: +16.4%**

## As an account

| Rules | Return | vs SPY | Sharpe | Max drawdown | Green days | Train return | Test return |
|---|---|---|---|---|---|---|---|
| All signals (live rules, whole market) | -74.6% | -90.9 | -4.37 | -75.0% | 26% | -58.4% | -38.9% |
| Skip if spread > 0.25% | -6.1% | -22.4 | -0.27 | -24.3% | 33% | -8.0% | +2.1% |
| Long only | -44.9% | -61.2 | -2.01 | -46.3% | 25% | -28.6% | -22.9% |
| Long only, spread ≤ 0.25% | -1.5% | -17.8 | -0.06 | -8.8% | 23% | -1.9% | +0.5% |
| Shorts only | -57.0% | -73.3 | -5.14 | -58.1% | 24% | -44.9% | -21.9% |
| $5-10 stocks | -28.2% | -44.6 | -3.06 | -29.5% | 6% | -17.8% | -12.7% |
| $10-50 stocks | -48.4% | -64.8 | -2.23 | -48.9% | 30% | -30.9% | -25.4% |
| $50+ stocks | -33.3% | -49.7 | -3.01 | -36.2% | 25% | -23.5% | -12.9% |

Train = before 2025-09-03, test = from 2025-09-03 on.

## Per trade (R = profit / risk to the stop)

| Set | Before costs | After spread + slippage |
|---|---|---|
| All signals (live rules, whole market) | 2895 · win 13% · avg +0.389R · t +4.0 | 2895 · win 13% · avg -0.485R · t -5.0 |
| Skip if spread > 0.25% | 1437 · win 14% · avg +0.377R · t +3.2 | 1437 · win 14% · avg -0.089R · t -0.8 |
| Long only | 1478 · win 13% · avg +0.476R · t +3.1 | 1478 · win 12% · avg -0.431R · t -2.8 |
| Long only, spread ≤ 0.25% | 734 · win 14% · avg +0.340R · t +2.1 | 734 · win 13% · avg -0.146R · t -0.9 |
| Shorts only | 1417 · win 13% · avg +0.299R · t +2.6 | 1417 · win 13% · avg -0.542R · t -4.6 |
| $5-10 stocks | 230 · win 9% · avg -0.076R · t -0.3 | 230 · win 9% · avg -0.619R · t -2.5 |
| $10-50 stocks | 1711 · win 13% · avg +0.427R · t +3.1 | 1711 · win 12% · avg -0.419R · t -3.1 |
| $50+ stocks | 954 · win 14% · avg +0.433R · t +2.8 | 954 · win 14% · avg -0.572R · t -3.6 |

## By entry spread

| Spread | After costs |
|---|---|
| 0–0.05% | 150 · win 16% · avg +0.237R · t +0.7 |
| 0.05–0.1% | 383 · win 17% · avg +0.100R · t +0.5 |
| 0.1–0.25% | 904 · win 12% · avg -0.224R · t -1.5 |
| 0.25–0.5% | 824 · win 11% · avg -0.654R · t -3.6 |
| 0.5–∞% | 634 · win 12% · avg -1.164R · t -4.3 |

## Net R by month

| Month | Trades | Net R |
|---|---|---|
| 2024-12 | 7 | -13.6 |
| 2025-01 | 214 | -97.8 |
| 2025-02 | 222 | -154.7 |
| 2025-03 | 282 | -136.9 |
| 2025-04 | 289 | -25.0 |
| 2025-05 | 263 | -100.5 |
| 2025-06 | 203 | -88.0 |
| 2025-07 | 221 | -56.2 |
| 2025-08 | 230 | -186.3 |
| 2025-09 | 213 | -172.1 |
| 2025-10 | 258 | -147.1 |
| 2025-11 | 229 | -125.0 |
| 2025-12 | 264 | -102.4 |

Top 20 trades: +792.6R of -1405.5R total. Median entry spread 0.252%.

Caveats: no AI news filter, no correlation guard; 1-minute bars; spread measured at entry and reused for the exit; size could move a thin stock more than the spread; halts not modelled.
