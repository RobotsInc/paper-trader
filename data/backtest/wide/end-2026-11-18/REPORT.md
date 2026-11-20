# Whole-market backtest: 2025-11-18 to 2026-11-18

- Universe: 13757 listed US stocks/ETFs (active + delisted), median 2416 liquid enough to watch each day; top 20 by opening relative volume traded.
- Live bot rules: first-candle direction, 5-min range break, don't chase > 0.2 ATR, 10% ATR stop, min stop 0.25%, hold to 15:45, price ≥ $5, ATR ≥ $0.50, avg volume ≥ 1M.
- Costs: real SIP bid-ask spread at entry (half in, half out) + 3 bps/side.
- Account: $100k with the live bot's limits (0.5% risk, 5 positions, 3/side, 20%/position, 150% gross, 2.5% daily loss limit).
- **SPY buy & hold: +10.6%**

## As an account

| Rules | Return | vs SPY | Sharpe | Max drawdown | Green days | Train return | Test return |
|---|---|---|---|---|---|---|---|
| All signals (live rules, whole market) | -78.7% | -89.3 | -5.34 | -79.2% | 27% | -61.4% | -44.7% |
| Skip if spread > 0.25% | +35.4% | +24.8 | 1.46 | -9.7% | 36% | +28.3% | +5.5% |
| Long only | -58.6% | -69.2 | -3.85 | -60.4% | 24% | -41.0% | -29.9% |
| Long only, spread ≤ 0.25% | +25.7% | +15.1 | 1.35 | -7.7% | 23% | +21.6% | +3.4% |
| Shorts only | -52.1% | -62.7 | -3.60 | -53.3% | 28% | -38.0% | -22.7% |
| $5-10 stocks | -29.1% | -39.7 | -3.07 | -31.4% | 11% | -16.7% | -14.9% |
| $10-50 stocks | -62.2% | -72.9 | -4.10 | -62.5% | 29% | -36.0% | -41.0% |
| $50+ stocks | -43.7% | -54.3 | -3.15 | -45.5% | 21% | -41.7% | -3.5% |

Train = before 2026-07-23, test = from 2026-07-23 on.

## Per trade (R = profit / risk to the stop)

| Set | Before costs | After spread + slippage |
|---|---|---|
| All signals (live rules, whole market) | 3177 · win 14% · avg +0.330R · t +3.9 | 3177 · win 13% · avg -0.635R · t -7.2 |
| Skip if spread > 0.25% | 1466 · win 17% · avg +0.541R · t +3.9 | 1466 · win 16% · avg +0.104R · t +0.7 |
| Long only | 1663 · win 13% · avg +0.363R · t +2.7 | 1663 · win 13% · avg -0.633R · t -4.7 |
| Long only, spread ≤ 0.25% | 749 · win 17% · avg +0.756R · t +3.2 | 749 · win 17% · avg +0.297R · t +1.3 |
| Shorts only | 1514 · win 15% · avg +0.294R · t +2.8 | 1514 · win 14% · avg -0.638R · t -5.8 |
| $5-10 stocks | 233 · win 13% · avg -0.032R · t -0.2 | 233 · win 13% · avg -0.590R · t -3.1 |
| $10-50 stocks | 1823 · win 15% · avg +0.332R · t +3.4 | 1823 · win 14% · avg -0.604R · t -5.9 |
| $50+ stocks | 1121 · win 13% · avg +0.402R · t +2.3 | 1121 · win 12% · avg -0.695R · t -3.8 |

## By entry spread

| Spread | After costs |
|---|---|
| 0–0.05% | 195 · win 23% · avg +0.615R · t +2.0 |
| 0.05–0.1% | 360 · win 19% · avg +0.339R · t +1.5 |
| 0.1–0.25% | 911 · win 14% · avg -0.098R · t -0.5 |
| 0.25–0.5% | 831 · win 13% · avg -0.612R · t -4.2 |
| 0.5–∞% | 880 · win 9% · avg -1.889R · t -12.1 |

## Net R by month

| Month | Trades | Net R |
|---|---|---|
| 2025-11 | 94 | -7.0 |
| 2025-12 | 261 | -116.6 |
| 2026-01 | 201 | -226.4 |
| 2026-02 | 247 | -183.4 |
| 2026-03 | 300 | -232.8 |
| 2026-04 | 269 | -118.9 |
| 2026-05 | 281 | -32.8 |
| 2026-06 | 271 | -175.3 |
| 2026-07 | 291 | -309.9 |
| 2026-08 | 268 | +71.1 |
| 2026-09 | 257 | -200.8 |
| 2026-10 | 257 | -277.3 |
| 2026-11 | 180 | -207.6 |

Top 20 trades: +717.0R of -2017.8R total. Median entry spread 0.278%.

Caveats: no AI news filter, no correlation guard; 1-minute bars; spread measured at entry and reused for the exit; size could move a thin stock more than the spread; halts not modelled.
