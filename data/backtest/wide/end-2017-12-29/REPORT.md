# Whole-market backtest: 2016-12-29 to 2017-12-29

- Universe: 13757 listed US stocks/ETFs (active + delisted), median 1249 liquid enough to watch each day; top 20 by opening relative volume traded.
- Live bot rules: first-candle direction, 5-min range break, don't chase > 0.2 ATR, 10% ATR stop, min stop 0.25%, hold to 15:45, price ≥ $5, ATR ≥ $0.50, avg volume ≥ 1M.
- Costs: real SIP bid-ask spread at entry (half in, half out) + 3 bps/side.
- Account: $100k with the live bot's limits (0.5% risk, 5 positions, 3/side, 20%/position, 150% gross, 2.5% daily loss limit).
- **SPY buy & hold: +19.0%**

## As an account

| Rules | Return | vs SPY | Sharpe | Max drawdown | Green days | Train return | Test return |
|---|---|---|---|---|---|---|---|
| All signals (live rules, whole market) | -36.7% | -55.7 | -3.21 | -37.2% | 31% | -24.2% | -16.5% |
| Skip if spread > 0.25% | -14.9% | -33.9 | -1.30 | -15.9% | 29% | -7.3% | -8.2% |
| Long only | -23.0% | -42.0 | -2.36 | -25.0% | 21% | -11.6% | -12.9% |
| Long only, spread ≤ 0.25% | -7.2% | -26.2 | -0.72 | -12.9% | 18% | -3.3% | -4.1% |
| Shorts only | -19.0% | -38.0 | -2.14 | -19.0% | 26% | -14.5% | -5.2% |
| $5-10 stocks | +2.9% | -16.1 | 0.43 | -3.1% | 2% | +1.8% | +1.1% |
| $10-50 stocks | -29.9% | -48.9 | -3.16 | -30.5% | 32% | -16.3% | -16.3% |
| $50+ stocks | -10.7% | -29.7 | -2.27 | -10.7% | 13% | -6.5% | -4.4% |

Train = before 2017-08-30, test = from 2017-08-30 on.

## Per trade (R = profit / risk to the stop)

| Set | Before costs | After spread + slippage |
|---|---|---|
| All signals (live rules, whole market) | 1622 · win 14% · avg +0.286R · t +2.8 | 1622 · win 14% · avg -0.410R · t -4.1 |
| Skip if spread > 0.25% | 1166 · win 14% · avg +0.257R · t +2.3 | 1166 · win 14% · avg -0.270R · t -2.4 |
| Long only | 766 · win 13% · avg +0.283R · t +1.8 | 766 · win 13% · avg -0.434R · t -2.8 |
| Long only, spread ≤ 0.25% | 534 · win 13% · avg +0.185R · t +1.1 | 534 · win 13% · avg -0.355R · t -2.1 |
| Shorts only | 856 · win 15% · avg +0.288R · t +2.2 | 856 · win 14% · avg -0.389R · t -2.9 |
| $5-10 stocks | 42 · win 17% · avg +1.013R · t +1.0 | 42 · win 17% · avg +0.429R · t +0.4 |
| $10-50 stocks | 1258 · win 14% · avg +0.279R · t +2.5 | 1258 · win 14% · avg -0.415R · t -3.7 |
| $50+ stocks | 322 · win 14% · avg +0.219R · t +1.0 | 322 · win 14% · avg -0.502R · t -2.3 |

## By entry spread

| Spread | After costs |
|---|---|
| 0–0.05% | 165 · win 19% · avg +0.091R · t +0.3 |
| 0.05–0.1% | 337 · win 13% · avg -0.205R · t -1.0 |
| 0.1–0.25% | 664 · win 13% · avg -0.392R · t -2.5 |
| 0.25–0.5% | 346 · win 13% · avg -0.764R · t -3.3 |
| 0.5–∞% | 110 · win 15% · avg -0.789R · t -1.6 |

## Net R by month

| Month | Trades | Net R |
|---|---|---|
| 2016-12 | 15 | -4.6 |
| 2017-01 | 111 | -112.5 |
| 2017-02 | 106 | -76.2 |
| 2017-03 | 150 | +58.3 |
| 2017-04 | 79 | -48.0 |
| 2017-05 | 155 | -50.6 |
| 2017-06 | 153 | -72.4 |
| 2017-07 | 108 | -58.7 |
| 2017-08 | 175 | +46.1 |
| 2017-09 | 119 | -28.0 |
| 2017-10 | 120 | -68.5 |
| 2017-11 | 189 | -102.3 |
| 2017-12 | 142 | -148.0 |

Top 20 trades: +452.8R of -665.4R total. Median entry spread 0.154%.

Caveats: no AI news filter, no correlation guard; 1-minute bars; spread measured at entry and reused for the exit; size could move a thin stock more than the spread; halts not modelled.
