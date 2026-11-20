# Whole-market backtest: 2021-12-30 to 2022-12-30

- Universe: 13757 listed US stocks/ETFs (active + delisted), median 1714 liquid enough to watch each day; top 20 by opening relative volume traded.
- Live bot rules: first-candle direction, 5-min range break, don't chase > 0.2 ATR, 10% ATR stop, min stop 0.25%, hold to 15:45, price ≥ $5, ATR ≥ $0.50, avg volume ≥ 1M.
- Costs: real SIP bid-ask spread at entry (half in, half out) + 3 bps/side.
- Account: $100k with the live bot's limits (0.5% risk, 5 positions, 3/side, 20%/position, 150% gross, 2.5% daily loss limit).
- **SPY buy & hold: -19.7%**

## As an account

| Rules | Return | vs SPY | Sharpe | Max drawdown | Green days | Train return | Test return |
|---|---|---|---|---|---|---|---|
| All signals (live rules, whole market) | -33.1% | -13.4 | -1.44 | -43.5% | 40% | +0.4% | -33.4% |
| Skip if spread > 0.25% | -21.0% | -1.3 | -1.28 | -26.3% | 36% | +0.8% | -21.6% |
| Long only | -31.7% | -12.0 | -1.86 | -35.5% | 29% | -15.9% | -18.7% |
| Long only, spread ≤ 0.25% | -17.9% | +1.7 | -1.64 | -19.5% | 28% | -10.6% | -8.2% |
| Shorts only | -10.7% | +9.0 | -0.51 | -23.9% | 32% | +13.1% | -21.0% |
| $5-10 stocks | -2.0% | +17.7 | -0.11 | -15.0% | 15% | -4.1% | +2.2% |
| $10-50 stocks | -22.7% | -3.0 | -0.94 | -31.8% | 35% | +2.8% | -24.8% |
| $50+ stocks | -30.3% | -10.6 | -3.04 | -33.4% | 24% | -23.5% | -8.9% |

Train = before 2022-08-31, test = from 2022-08-31 on.

## Per trade (R = profit / risk to the stop)

| Set | Before costs | After spread + slippage |
|---|---|---|
| All signals (live rules, whole market) | 3307 · win 15% · avg +0.312R · t +4.6 | 3307 · win 15% · avg -0.309R · t -4.6 |
| Skip if spread > 0.25% | 2003 · win 15% · avg +0.182R · t +2.3 | 2003 · win 15% · avg -0.241R · t -3.0 |
| Long only | 1641 · win 16% · avg +0.295R · t +3.2 | 1641 · win 15% · avg -0.356R · t -3.8 |
| Long only, spread ≤ 0.25% | 965 · win 16% · avg +0.168R · t +1.5 | 965 · win 15% · avg -0.270R · t -2.5 |
| Shorts only | 1666 · win 15% · avg +0.328R · t +3.3 | 1666 · win 15% · avg -0.262R · t -2.7 |
| $5-10 stocks | 247 · win 17% · avg +0.363R · t +1.5 | 247 · win 17% · avg -0.142R · t -0.6 |
| $10-50 stocks | 2013 · win 16% · avg +0.403R · t +4.4 | 2013 · win 16% · avg -0.192R · t -2.1 |
| $50+ stocks | 1047 · win 14% · avg +0.126R · t +1.2 | 1047 · win 13% · avg -0.572R · t -5.4 |

## By entry spread

| Spread | After costs |
|---|---|
| 0–0.05% | 310 · win 19% · avg +0.014R · t +0.1 |
| 0.05–0.1% | 521 · win 15% · avg -0.298R · t -2.3 |
| 0.1–0.25% | 1172 · win 13% · avg -0.283R · t -2.5 |
| 0.25–0.5% | 857 · win 16% · avg -0.301R · t -2.1 |
| 0.5–∞% | 447 · win 15% · avg -0.627R · t -2.9 |

## Net R by month

| Month | Trades | Net R |
|---|---|---|
| 2021-12 | 26 | -1.0 |
| 2022-01 | 238 | -19.8 |
| 2022-02 | 258 | -20.4 |
| 2022-03 | 313 | -55.4 |
| 2022-04 | 256 | -103.6 |
| 2022-05 | 320 | -61.2 |
| 2022-06 | 281 | -83.3 |
| 2022-07 | 254 | -147.3 |
| 2022-08 | 305 | -49.7 |
| 2022-09 | 233 | -165.9 |
| 2022-10 | 303 | -184.2 |
| 2022-11 | 271 | -76.1 |
| 2022-12 | 249 | -52.6 |

Top 20 trades: +478.8R of -1020.5R total. Median entry spread 0.198%.

Caveats: no AI news filter, no correlation guard; 1-minute bars; spread measured at entry and reused for the exit; size could move a thin stock more than the spread; halts not modelled.
