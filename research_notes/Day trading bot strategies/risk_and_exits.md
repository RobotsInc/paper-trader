# Risk Management and Exit Design for Intraday Trading Bots (US equities)

Context: the bot uses an initial stop, a ratcheting trailing stop (e.g. "peak 0.53R, lock 0.00R", meaning it moves to breakeven after +0.53R), a flatten 10 minutes before the close, and a daily loss limit. Recent trades were stopped out within minutes.

## Stop-loss evidence: when stops add value, tight vs ATR-based stops, and noise stop-outs

### Takeaway
Theory (Kaminski & Lo) says a stop only adds expected return when returns are serially correlated (momentum or regime persistence). Under a random walk it always costs return, and under mean reversion it hurts. Short-horizon (daily/weekly) stops often had a negative "stopping premium" in their data. The documented profitable intraday systems use volatility-scaled stops (10% of 14-day ATR, or the opening range / noise band) and accept low hit rates (about 20 to 48%). Very tight stops also blow up cost-as-a-share-of-risk, which can turn a real gross edge into zero net.

### Cited Findings
- Kaminski & Lo define the "stopping premium" as Δµ = p_o(r_f − E[r | stopped out]). Under IID (random-walk) returns, Δµ = −p_o·π ≤ 0: "stop-loss rules never stop losses" in expected-return terms, although variance can fall. — [Kaminski & Lo, MIT DSpace PDF](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf)
- Under momentum (AR(1), ρ>0) a stop can add value. A sufficient condition is ρ ≥ the Sharpe ratio at the same frequency. Under mean reversion (ρ<0) stops lower expected return because they miss reversals. In a regime-switching model, the stop must be accurate enough at firing in the bad regime. — [Kaminski & Lo](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf)
- Empirically (daily S&P 500 and 10y Treasury futures, 1993–2011), short-horizon (daily/weekly) stops often had negative stopping premiums across wide parameter ranges. Monthly and longer windows could be positive: about +1.5% return, about 5% lower volatility, and Sharpe up to about 20% higher in one calibration. The exit threshold mattered more than the re-entry threshold. Transaction costs were zero in the main analysis. — [Kaminski & Lo](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf); also published J. Financial Markets 18 (2014) 234–254 — [RePEc](https://ideas.repec.org/a/eee/finmar/v18y2014icp234-254.html)
- Zarattini, Barbon & Aziz ORB "Stocks in Play" (2016–2023): stop at 10% of 14-day ATR from the executed entry price, no profit target, exit at 16:00. Base ORB on all stocks had a 41.4% hit ratio and Sharpe 0.48 (29% total return). Restricting to the top-20 relative-volume "stocks in play" (RelVol ≥100%) gave a 48.4% hit ratio, Sharpe 2.81, 12% max drawdown and 1,637% total return. The paper does not test alternative stop sizes or report stop-hit frequency. — [Zarattini, Barbon & Aziz, "A Profitable Day Trading Strategy for the U.S. Equity Market" (Univ. St. Gallen repository)](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- An independent replication of the earlier Zarattini & Aziz QQQ/NQ ORB (stop at the opposite side of the opening range, 10R target): gross results reproduce (+0.131R per trade, 23.2% hit rate on NQ, vs the paper's +0.13R and 24%). Only 2–4% of trades reach the 10R target. Net of spread and slippage (about 6–12% of risk per trade), no market is distinguishable from zero (NQ +0.002R; SPX −0.081R; Dow −0.081R). — [MQL5 replication blog](https://www.mql5.com/en/blogs/post/776235) (practitioner, not peer reviewed)
- The same replication found that tight stops are where costs "explode": if the first candle closes at its extreme, the stop can sit only 1–2 points from entry. The author therefore requires initial risk ≥ 2× round-trip cost. On a 25-point stop, 2.5 points of cost ≈ 0.1R, which equals the measured edge. — [MQL5 replication](https://www.mql5.com/en/blogs/post/776235)
- Stop-width simulation (daily S&P 500, 500 random investors, 2000–2005 entries): wider stops raise the win rate by absorbing noise but lower the payoff ratio. Total return forms a plateau, falling sharply when stops are too tight and only gradually when they are too wide. This is an illustrative simulation by the author with no costs and no academic citation. — [CFA Institute Enterprising Investor, Jan 2026](https://rpc.cfainstitute.org/blogs/enterprising-investor/2026/why-tight-stop-losses-often-hurt-investors-and-what-robust-capital-growth-really-requires)
- Intraday volatility is U-shaped and decays roughly as a power law (k^−0.3) over the first two hours. So a fixed-cents or fixed-% stop is relatively tighter vs noise in the first hour than at midday. — [Allez & Bouchaud, "Individual and collective stock dynamics: intra-day seasonalities" (126 NYSE stocks, 2000–2009, 5-min bins)](https://arxiv.org/pdf/1009.4785)

### Inferences
- Stop-outs within minutes are what you would expect when stop distance is small relative to the opening-period 5-min noise. The Concretum benchmark is 10% of daily ATR, but it is paired with entries only on high-relative-volume names and a hold-to-close exit, so winners are allowed to run to multiple R. A tight stop without a long right tail is the losing combination.
- A practical floor: stop distance ≥ max(k × recent 1–5-min ATR/realized noise, 2× round-trip cost). Re-express it in time-of-day-aware units (the noise-area approach does this by construction).
- Kaminski & Lo imply that stops make sense intraday only if the strategy is a momentum/trend bet (the stop exits when the thesis that momentum persists fails). For mean-reversion entries, tight stops are structurally negative-expectancy.

### Gaps
- I found no peer-reviewed intraday study that systematically sweeps stop width (e.g. 0.05/0.1/0.2/0.5× ATR) on US stocks with costs. The Concretum paper references earlier work on stop size and expected value, but I did not retrieve that analysis.
- The "10% hit rate" figure mentioned in the brief was not found. The closest documented numbers are a 23–24% hit rate (QQQ ORB with a 10R target) and 37–48% (SPY noise area; stocks-in-play ORB).

## Trailing stops vs fixed targets vs exit-at-close in documented intraday strategies

### Takeaway
The best-documented systematic intraday strategies (Concretum/Zarattini) use no fixed profit target. They exit at the close, or trail with a structural level (noise boundary / VWAP) checked only every 30 minutes, never a tick-by-tick breakeven ratchet. Their edge comes from a minority of large winners, so early breakeven locks are likely to cut exactly those trades.

### Cited Findings
- SPY "Beat the Market" intraday momentum: the noise area is built from the 14-day average absolute move from the open at each time of day, anchored at the higher (lower) of the open and the prior close. Signals and stops are evaluated only at HH:00 and HH:30, with the first trade at 10:00. The trailing stop for longs is max(upper band, VWAP), and for shorts min(lower band, VWAP). A crossover of the opposite band reverses the position. Everything is closed at 16:00. — [Zarattini, Aziz & Barbon, "Beat the Market" (St. Gallen repository)](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- Results (2007–early 2024, net of $0.0035/sh commission and $0.001/sh slippage): IRR 19.6%, vol 14.3%, Sharpe 1.33, max drawdown 25%, daily hit ratio 43%, trade hit ratio 37%, best trade +9.1%, worst trade −2.9%. Under an I-Star impact model the Sharpe falls to 1.17. — [Beat the Market](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- ORB stocks-in-play: 10% ATR stop, no target, hold to close. — [Zarattini, Barbon & Aziz](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- QQQ ORB (Zarattini & Aziz 2023): 10R target, otherwise exit at close. Only 2–4% of trades reach 10R in replication. — [MQL5 replication](https://www.mql5.com/en/blogs/post/776235); results summary (1,484% vs 169% QQQ, 2016–2023, 33% annualized alpha net of commissions) — [Concretum Group](https://concretumgroup.com/can-day-trading-really-be-profitable/)
- The first-half-hour SPY return predicts the last-half-hour return (R² about 2% full sample 1999–2012; 4.3% in the crisis). A simple timing strategy earned 6.34%/yr in-sample, with stronger predictability on high-volatility and news days. — [Alpha Architect summary of Gao, Han, Li & Zhou (JFE 2018)](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/); [JFE citation](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)

### Inferences
- "Peak 0.53R → lock 0.00R" is a breakeven ratchet after about half an R. With 37–48% hit rates and payoffs driven by fat right tails, documented strategies never use such early locks. It will convert many eventual winners into scratches and leave the full −1R on losers. Alternatives: (a) no ratchet until about 1–1.5R, then trail by a volatility unit; (b) a structural trail (VWAP / noise band); (c) evaluate the trail on bar closes (5/30-min), not ticks, to avoid noise triggers.
- Flattening 10 minutes before the close forgoes part of the last-half-hour momentum window. The documented strategies hold to 16:00 (in practice MOC orders or the final minute). Moving the flatten to MOC or about 15:58–15:59 is worth testing if broker/infra permits.

### Gaps
- No head-to-head published test was found of breakeven-ratchet trailing vs hold-to-close on the same intraday signal.

## Win rate vs payoff ratio, expectancy, and viable combos after costs

### Takeaway
Expectancy per trade (in R) = p·W − (1−p)·L − cost. Documented intraday strategies sit at 20–48% hit rates and need average-win/average-loss well above 1. Costs measured in R are decisive: about 0.1R of cost can erase the full edge of an ORB system.

### Cited Findings
- QQQ/NQ ORB: about 23–24% hit rate, gross +0.13R per trade, net about 0R after roughly 0.06–0.12R of cost per trade. — [MQL5 replication](https://www.mql5.com/en/blogs/post/776235)
- SPY noise area: 37% trade hit ratio, average $0.09/share per trade, Sharpe 1.33 net. — [Beat the Market](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- Stocks-in-play ORB: 48.4% hit ratio, Sharpe 2.81 (commission $0.0035/sh only). — [Zarattini, Barbon & Aziz](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Wider stops raise win rate and lower payoff ratio; the optimum is a plateau. — [CFA Institute blog](https://rpc.cfainstitute.org/blogs/enterprising-investor/2026/why-tight-stop-losses-often-hurt-investors-and-what-robust-capital-growth-really-requires)
- Fixed-fraction betting with n wins and n losses at fraction f leaves W0(1−f²)^n, below the starting wealth (volatility drag). — [MacLean, Thorp & Ziemba, "Good and bad properties of the Kelly criterion"](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)

### Inferences
- These are my arithmetic, not sourced figures. With full −1R losses, the breakeven win rate for an average win of W R and cost c R is p* = (1+c)/(W+1). Examples at c=0.1R: W=1 → 55%; W=2 → 36.7%; W=3 → 27.5%; W=5 → 18.3%.
- A breakeven ratchet at 0.5R lowers the average loss on some trades to about 0 (−cost), but it also caps many trades near 0. If most trades get stopped within minutes at −1R before ever reaching 0.5R, the ratchet does nothing for losers and the strategy behaves as a low-W system.
- Track the bot's R-multiple distribution (MAE/MFE per trade). If MFE often exceeds 1R on trades later stopped at 0R, the lock is too early. If MAE on eventual winners often exceeds the stop, the stop is too tight.

### Gaps
- Van Tharp's expectancy material is practitioner and was not fetched. The formula above is standard, but no specific Tharp numbers are cited.

## Position sizing: fixed-fractional risk, volatility targeting, Kelly, leverage caps, concurrency/correlation

### Takeaway
Documented intraday systems size so that a stop-out costs 1% of allocated capital (ORB), or scale to a 2% daily volatility target (SPY), with a hard 4× leverage cap. Kelly theory says to bet well below full Kelly: half Kelly keeps 75% of the growth with much higher safety, and 2× Kelly yields zero growth. Intraday cross-stock correlation rises from about 0.12 at the open to about 0.3 at the close, so many same-direction positions are increasingly one market bet.

### Cited Findings
- ORB: size each position so a stop-out loses 1% of capital allocated to it, with 4× max leverage, $25k starting capital, $0.0035/sh. Filters: price >$5, 14-day avg volume ≥1M, ATR >$0.50. Top 20 stocks by relative volume. — [Zarattini, Barbon & Aziz](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- SPY noise area: shares = prior-day equity × min(4, 2% daily target vol / 14-day realized SPY vol) / open. — [Beat the Market](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- Replication critique: 4× leverage on about a 20% hit rate produces long losing streaks, and 2015–2017 were negative in every market tested. — [MQL5 replication](https://www.mql5.com/en/blogs/post/776235)
- Kelly: half Kelly gives 0.75 of the growth rate with a 0.89 probability of doubling before halving, vs 0.67 at full Kelly. 2× Kelly gives growth ≈ 0 and a 0.50 probability. Errors in mean estimates matter about 20:2:1 vs variance and covariance errors. In a 700-bet example, full Kelly can turn $1000 into $18. — [MacLean, Thorp & Ziemba](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)
- Average intraday stock correlation (λ1/N) rises from about 0.12 at the open to about 0.3 near the close. Dispersion is relatively strongest in the morning. — [Allez & Bouchaud](https://arxiv.org/pdf/1009.4785)

### Inferences
- For a bot of this type, 0.25–1% equity risk per trade is consistent with documented practice. 1% is the ORB paper's figure, and lower is prudent given the cost/leverage critique.
- Because Kelly is very sensitive to mean-estimation error and intraday edges are small (about 0.1R), the honest Kelly fraction is small. Quarter Kelly or less is defensible.
- Cap aggregate same-direction risk, e.g. sum of open risk in the same direction ≤ 2–3R. Treat N concurrent shorts as about one market bet, especially after midday when correlation is highest. A simple approach: effective bets ≈ N / (1 + (N−1)ρ). With ρ≈0.3, 10 positions ≈ 2.7 independent bets (my calculation).

### Gaps
- No source found giving an empirical "max concurrent positions" rule. The ORB paper caps at 20 names via selection and 4× gross leverage.

## Daily loss limits / circuit breakers and drawdown control

### Takeaway
No academic evidence was found that daily loss limits raise expected return for a systematic strategy. Their justification is behavioral (losing traders escalate risk) and operational (bounding damage from bugs or regime breaks). Industry prop-firm practice is a 3–5% daily loss limit and 6–12% max drawdown.

### Cited Findings
- CBOT T-bond locals (1,082 traders, 1998): those with morning losses had a 31.2% chance of above-average afternoon risk vs 27% after profitable mornings. They were about 15% more likely to place price-moving trades, and their price impact reversed faster (noise trading). — [CFA Digest summary of Coval & Shumway, JF 2005](https://rpc.cfainstitute.org/en/research/cfa-digest/2005/11/do-behavioral-biases-affect-prices-digest-summary); [JF citation](https://ideas.repec.org/a/bla/jfinan/v60y2005i1p1-34.html)
- Prop-firm norms: daily loss limit about 3–5% of starting balance (e.g. 5% = $2,500 on $50k), static max drawdown about 6–12%, trailing drawdown about 3–10%. Equity-based limits count unrealized P&L, and intraday trailing is the strictest. — [Fortunly, prop firm drawdown rules](https://fortunly.com/articles/how-prop-firm-drawdown-rules-work/) (practitioner/aggregator)
- Kaminski & Lo's regime result suggests a portfolio-level stop helps only when losses signal persistence into a bad regime. — [Kaminski & Lo](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf)

### Inferences
- For a bot, set the daily limit in R (e.g. −3R to −4R, or about 2–3% equity at 0.5–1% per trade) and count unrealized P&L. On a breach, halt new entries and also flag for review, since rapid consecutive stop-outs are more likely a parameter/regime problem than bad luck.
- Add a weekly/monthly drawdown throttle (e.g. halve size after a −X% peak-to-trough). This is common practice but has no specific source found here.

### Gaps
- No peer-reviewed study was found testing daily loss limits on systematic intraday strategy returns.

## Time-of-day effects: first minutes, lunch lull, last 30 minutes, half-days

### Takeaway
Volatility is highest and most heavy-tailed-relative-to-noise right after the open and decays over about two hours. Cross-stock correlation rises through the day. The last half hour carries predictable momentum. Documented strategies wait at least 5 minutes (ORB) or 30 minutes (SPY noise area, first trade at 10:00) and hold to the close.

### Cited Findings
- U-shaped volatility with power-law decay (β≈0.3) over the first two hours. Kurtosis is about 3.5 at the open, rising to about 5 by 1 pm. Correlation is 0.12 at the open and 0.3 at the close. — [Allez & Bouchaud](https://arxiv.org/pdf/1009.4785)
- The noise-area approach measures the typical move at each time of day (14-day average), so stops and entries scale with the U-shape. First trade at 10:00, with checks only on the half-hour. — [Beat the Market](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)
- ORB timeframe matters: 5-min Sharpe 2.81 (stocks in play), 15-min Sharpe 1.43, 30-min 0.21, 60-min 0.40. An equal-weight combo has Sharpe 1.99. — [Zarattini, Barbon & Aziz](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- The first half hour predicts the last half hour (R² about 2%). — [Alpha Architect / Gao et al.](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)

### Inferences
- Entries in the first 5–15 minutes with stops sized off longer-horizon or midday volatility are the most likely to get "stopped within minutes." Either delay entries or scale the stop to time-of-day noise.
- On early-close days (13:00 ET), flatten relative to the actual close time. This needs an exchange calendar in the bot.

### Gaps
- No source was fetched quantifying the lunch-lull effect on strategy P&L, or half-day session behavior. Spread U-shape numbers were not retrieved.
