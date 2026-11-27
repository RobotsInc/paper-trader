# Single-strategy vs multi-signal ensembles for intraday trading, and how to validate them

Context from the assignment: the user's bot runs 6 signal bots (vwap, relvol, trend, ORB, momentum, meanrev) plus filters. A trade needs at least 3 bots to agree and a score of at least 0.45, and an SPY regime gate applies. It has about 20 trades so far, a hit rate near 10%, and most trades lose money.

Note on sourcing: each item under "Cited Findings" was checked against the page linked to it during this session, unless the item says it was not. Items marked "(not fetched this session)" describe well-known content of a primary source that I could not re-check here. The report writer should give them less weight.

---

## 1. Does combining many correlated technical signals by majority vote help or hurt? Equal-weight vs inverse-vol vs regression/ML stacking; correlation; "agreement" filters

### Takeaway
Combining forecasts helps only when the components carry *different* information. Redundant or highly correlated signals add little and can make a simple average worse. When weights have to be estimated, equal weights usually beat "optimal" estimated weights out of sample, because estimation error swamps the theoretical gain (the "forecast combination puzzle"). A k-of-n vote built from six price/volume indicators on the same bars is probably close to the worst case: highly correlated inputs plus a hard threshold that throws away magnitude information.

### Cited Findings
- **Forecast combination puzzle.** Stock and Watson (2004) gave the name to "the repeated finding that simple combination forecasts outperform sophisticated adaptive combination methods." Smith and Wallis (2009) show that MSE-optimal estimated weights can have large variance and can end up further from the true optimal weights than equal weights are. Elliott (2011) argues that the largest possible gain over a simple average is often small enough to be swamped by estimation error. — [Qian, Rolling, Cheng & Yang, "On the Forecast Combination Puzzle" (arXiv 1505.00475)](https://arxiv.org/pdf/1505.00475)
- **When estimated weights do help.** Regression-based weights win only when each forecast uses a *different information set*, those sets are weakly correlated, and the signal-to-noise ratio is high, in a stable process. Under structural breaks, regression weights got worse because estimation error grew. — [arXiv 1505.00475](https://arxiv.org/pdf/1505.00475)
- **Correlation and redundancy.** The advantage of a simple average over the best single forecast "shrinks as the underlying information sets become more correlated." The simple average is also hurt by redundant candidates: adding an identical copy of a forecast, or one that uses only a subset of the same information, degraded its performance. — [arXiv 1505.00475](https://arxiv.org/pdf/1505.00475)
- **Effective breadth is far below the raw count.** Grinold's fundamental law (IR ≈ IC × √breadth) assumes independent bets. One empirical treatment estimates breadth from the eigenstructure of the correlation matrix and finds that 37 stocks gave an effective dimensionality of about 9 and an effective breadth of about 3. The authors state that the idea "that gambles are independent by their very nature, is simply incorrect." — [arXiv physics/0601166](https://arxiv.org/pdf/physics/0601166v2)
- **Composite score vs separate sleeves (cross-sectional factor evidence, not intraday).** AQR found that integrated (single composite score) long-only portfolios beat mixed ones under a tracking-error constraint, cited as roughly 3.2% vs 1.4% alpha over MSCI World. Part of the reason is that a composite avoids holding names that score well on one signal but badly on another. Vogel (2021), holding stock counts equal, found mixed sleeves ahead, especially for concentrated portfolios. Both results are hypothetical backtests. — [Alpha Architect, "Should Investors Combine or Separate Their Factor Exposures?"](https://alphaarchitect.com/should-investors-combine-or-separate-their-factor-exposures/); [AQR, "Long-Only Style Investing: Don't Just Mix, Integrate"](https://images.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Long-Only-Style-Investing-Dont-Just-Mix-Integrate.pdf)

### Inferences
- **The user's 6 signals are probably highly correlated.** "trend," "momentum," "ORB," and "vwap" (price above VWAP) are all functions of the same recent price path, and they tend to fire together on the same up-move. "relvol" is a volume condition, not a direction. "meanrev" tends to fire *against* the others. A vote of at least 3 of 6 is therefore effectively "price has already moved up and volume is up," not three independent confirmations. By the standard design-effect formula N_eff = N / (1 + (N−1)ρ), six signals with an average pairwise correlation of ρ = 0.6 are worth only about 1.5 independent signals. (This formula is standard statistics; I did not fetch a source for it.)
- **Agreement filters tend to add lateness.** Requiring several trend-type signals to agree usually means entering after the move is well underway. That is consistent with a very low hit rate on momentum-style entries, which then hit stops on normal pullbacks. This is a hypothesis to test against the bot's trade logs, not a documented finding.
- **Putting mean-reversion and momentum in one vote is internally contradictory.** At any moment they usually disagree. A vote containing both either cancels out or means meanrev is effectively outvoted, so the bot pays for a component it never uses. Treating them as separate strategies (Q2) is cleaner.
- **Preferred order of combination methods,** given the small data the user has: (a) pick the *one or two* signals with a documented intraday edge (see Q3: stocks-in-play ORB) and drop the rest, or (b) average continuous scores with equal weights after volatility-normalizing them, instead of counting votes. Regression or ML stacking is not justified with about 20 trades. It needs thousands of labeled out-of-sample observations to estimate weights better than equal weights would.

### Gaps
- I found no rigorous published study that tests k-of-n *majority voting of technical indicators* specifically for intraday US equities. The evidence here comes from the forecast-combination literature (mostly macro forecasting) and from cross-sectional factor research, applied by analogy.
- I did not fetch a direct source comparing inverse-volatility weighting with equal weighting for signal combination. It is commonly recommended as a scaling step, not as a source of alpha.

---

## 2. Multi-strategy portfolio (independent strategies with separate capital/risk) vs a single ensemble signal

### Takeaway
The evidence is split, and the answer depends on whether the components are truly different. With a small number of genuinely distinct, low-correlation strategies, separate sleeves with their own risk budgets keep each edge pure and make attribution clear: you can tell which one is losing. A single composite score is better when the signals interact (one vetoes the other's bad picks) and when turnover costs matter. For a retail intraday bot with no proven component, separate sleeves are the more useful design because they let each strategy be validated on its own.

### Cited Findings
- **Sleeves vs composite.** The mixed (siloed) approach lets "each sleeve target the purest version of its factor" and gives clearer attribution. Its drawbacks are offsetting trades (one sleeve buying while another sells the same name) and extra turnover. The integrated approach suits investors who weight many factors equally and care about tracking error. — [Alpha Architect](https://alphaarchitect.com/should-investors-combine-or-separate-their-factor-exposures/)
- **Evidence from day traders.** In Taiwan from 1992 to 2006, only about 13–15% of day traders were profitable net of fees in a typical year. Fewer than 1% (about 1,000 of about 360,000) were *predictably* profitable after costs the following year. Prior-year top performers kept an edge of about 28 bps per day net. — [Barber, Lee, Liu & Odean, "The Cross-Section of Speculator Skill: Evidence from Day Trading"](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)

### Inferences
- **Combining strategies does not create an edge.** Diversifying across uncorrelated strategies raises the portfolio Sharpe only if each component has a positive expected return net of costs. Averaging six zero-or-negative-edge signals gives a zero-or-negative-edge result with lower variance, which can make losses look smaller without making them go away.
- **Proposed design for the user's bot.** Run each candidate (for example ORB on stocks in play, a VWAP mean-reversion strategy) as its own sleeve with fixed, small risk per trade. Log each sleeve's trades separately and judge each with the statistics in Q5. Promote a sleeve to real capital only after it passes. This also removes the internal contradiction between momentum and mean-reversion noted in Q1.

### Gaps
- I did not retrieve AQR or Man primary research on *multi-strategy hedge-fund architecture* (pod/sleeve allocation) in this session. I found no rigorous study comparing "one ensemble bot" with "many independent bots" specifically for retail intraday equities.

---

## 3. Market regime filters (SPY trend gate, VIX, time-of-day) and the evidence that they help intraday

### Takeaway
The best-documented intraday "filter" is a *stock-selection* filter: only trade "stocks in play," meaning names with unusually high relative volume from news or earnings. Time-of-day and volatility-state effects are also well documented: intraday predictability is concentrated in the open and close and on high-volatility days. I found no rigorous evidence that a simple SPY trend gate or VIX threshold improves intraday single-stock strategies.

### Cited Findings
- **ORB on stocks in play.** Zarattini, Barbon & Aziz tested a 5-minute opening-range breakout on more than 7,000 US stocks from 2016 to 2023. Restricting trades to "stocks in play" (unusually high activity due to company-specific news) significantly improved results. The top-20 stocks-in-play portfolio reported a total net return above 1,600%, a Sharpe ratio of 2.81, and 36% annualized alpha, "even after accounting for transaction costs." The page I fetched did not list cost assumptions, stops, or win rate. — [Concretum Group summary of "A Profitable Day Trading Strategy for the U.S. Equity Market"](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/); [SSRN listing "Can Day Trading Really Be Profitable?"](https://papers.ssrn.com/abstract=4416622); there is also a public replication thread at [QuantConnect](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/) (thread not fetched).
- **Market intraday momentum (time-of-day).** On SPY from 1999 to 2012, the first half-hour return predicts the last half-hour return. R² is about 2% over the full sample and about 4.3% during the financial crisis. The effect is stronger on high-volatility days, recession days, and some macro-news days. A timing strategy earned 6.34% a year before costs. — [Alpha Architect summary of Gao, Han, Li & Zhou (JFE 2018)](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/); [JFE listing](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)
- **Volatility state.** ML predictability of 5-minute index returns was higher on high-volatility or illiquid days and during crises, was stronger mid-day, and fell after decimalization. — [Huddleston, Liu & Stentoft, "Intraday Market Predictability: A Machine Learning Approach" (SSRN 3726765)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3726765)
- **Timing rules overfit easily (daily/monthly, not intraday).** Dimensional tested 720 premium-timing strategies. Only 30 showed reliable outperformance in backtest, and for the best one, changing a single parameter (rebalance frequency or breakpoint) cut the excess return by more than half. — [Dimensional, "We Found 30 Timing Strategies that 'Worked'—and 690 that Didn't"](https://www.dimensional.com/at-de/insights/we-found-30-timing-strategies-that-worked-and-690-that-didnt)

### Inferences
- **Relative volume belongs in stock selection.** The user already has a "relvol" bot. The evidence says relative volume works best as a *universe filter* that decides which stocks to look at, not as one vote among six. Restructuring around "ORB only on high-relvol stocks in play" matches the best-documented intraday design.
- **The SPY gate is a parameter to test, not a known edge.** An SPY regime gate is a reasonable risk control, but each added gate is another chance to overfit (Q5) and reduces the number of trades, which slows validation. Test it as a switch with on/off results reported, not as a given.
- **High volatility helps and hurts.** Both intraday-momentum and ML studies find *more* predictability on high-volatility days. A VIX filter that blocks trading when volatility is high may remove the best opportunities. This is an inference from the two studies, not tested directly.

### Gaps
- I found no peer-reviewed study that isolates a "SPY above its moving average" gate or a VIX threshold as an intraday single-stock filter.
- I could not confirm that the stocks-in-play ORB results held out of sample after publication. The replication thread exists but was not read.

---

## 4. ML for intraday direction prediction (gradient boosting, deep learning, LLMs): realistic accuracy and net results

### Takeaway
Rigorous studies find small but real short-horizon predictability. Edges that were large before about 2010 have mostly been arbitraged away, and results depend heavily on transaction costs. LLM backtests are especially untrustworthy because models have memorized historical market data from their training period.

### Cited Findings
- **Intraday ML with costs.** Using lagged constituent returns to predict 5-minute index returns, regularized linear and tree-based models (Lasso, Elastic Net, Random Forest, Gradient Boosting) all showed significant predictability, and ensembles did best. The reported Sharpe ratio was 0.98 *after* transaction costs. The abstract gives no accuracy or R² figure. Predictability declined after decimalization. — [Huddleston, Liu & Stentoft (SSRN 3726765)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3726765)
- **Deep learning edge decayed (daily horizon).** On S&P 500 constituents, an LSTM strategy earned about 0.46% a day with a Sharpe ratio of 5.8 *before* costs from 1992 to 2009. From 2010 on, profitability was "fluctuating around zero after transaction costs," which the authors read as the edge being arbitraged away. — [Fischer & Krauss, EJOR 2018](https://econpapers.repec.org/RePEc:eee:ejores:v:270:y:2018:i:2:p:654-669)
- **LLM memorization.** GPT-4o recalls pre-cutoff S&P 500 levels, macro figures within a tenth of a point, and similar data, and shows "no recall" after its cutoff. Telling it to ignore post-2010 data left accuracy almost unchanged (97.6% vs 98.0%), against about 40% on genuinely post-cutoff data. It identified the company in anonymized earnings calls 100% of the time for Apple, Meta, and Microsoft. The authors warn that small post-cutoff samples lack the statistical power to separate skill from memorization. — [Lopez-Lira et al., "The Memorization Problem" (arXiv 2504.14765)](https://arxiv.org/html/2504.14765v2); related: ["A Test of Lookahead Bias in LLM Forecasts" (arXiv 2512.23847)](https://arxiv.org/html/2512.23847v1)

### Inferences
- **Realistic expectations.** Any ML direction model on 1–5 minute bars should be expected to land close to 50% accuracy. A few points above 50% can be economically meaningful only at very low costs and with many trades. Such models need thousands of labeled out-of-sample trades to validate, which is far beyond the user's current 20.
- **LLM backtests need post-cutoff data.** Any LLM-driven signal must be judged only on data *after* the model's training cutoff, which in practice means forward paper trading. Historical LLM backtests should be ignored.
- **ML cannot fix the current inputs.** Adding ML on top of six correlated, unvalidated signals would mostly fit noise. A pipeline problem should be fixed with validation before adding model complexity.

### Gaps
- I found no rigorous 2025–2026 study reporting *net-of-cost* results for gradient boosting or transformers on single-stock US intraday direction. The Frontiers (2026) and MDPI (Chinese market) results that came up in search were not fetched.

---

## 5. Backtest overfitting and validation: deflated Sharpe, PBO, walk-forward, minimum sample sizes, paper-trading duration

### Takeaway
Every configuration tried (thresholds such as "at least 3 agree" and "score ≥ 0.45," gates, lookbacks) counts as a trial and raises the bar a result must clear. Use the Deflated Sharpe Ratio or a Harvey–Liu haircut to account for the number of trials, and the Probability of Backtest Overfitting (PBO) to check whether the in-sample winner holds up. The rough sample sizes are hundreds of trades, or years of daily P&L, to establish an edge. Twenty trades is enough to reject "this works well" but not enough to confirm anything.

### Cited Findings
- **Deflated Sharpe Ratio (DSR).** The DSR is the Probabilistic Sharpe Ratio with its threshold replaced by the *expected maximum Sharpe ratio across N trials* under the null of no skill (the False Strategy Theorem). It rises with sample length and positive skew and falls with fat tails. N should be the number of *effectively independent* trials, estimated by clustering the trials' correlation matrix. "With enough trials, there is no Sharpe ratio sufficiently large" to reject that a strategy is false. All backtests run must be recorded, for example all 100 variants of a momentum strategy. — [Wikipedia, "Deflated Sharpe ratio"](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio); primary: [Bailey & López de Prado, SSRN 2460551](https://papers.ssrn.com/abstract=2460551)
- **Minimum Track Record Length (MinTRL).** MinTRL is the minimum sample needed to reject a zero Sharpe at a given confidence level, assuming only a single trial, so it is "a minimum requirement." In the Wikipedia example, about 3 years of daily returns are needed at 95% confidence, falling to about 2 years for annualized Sharpe ratios above 1.15. — [Wikipedia, "Deflated Sharpe ratio"](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio)
- **Harvey–Liu haircut.** Convert the Sharpe ratio to a t-ratio and adjust the p-value for the number of tests. A t-ratio of 3.0, which is highly significant as a single test, adjusts to about 2.0 after allowing for 316 prior tests. The haircut is nonlinear: marginal strategies are penalized heavily and strong ones lightly. Harvey calls a flat 50% haircut "a serious mistake" and recommends varying the assumptions to see how sensitive the result is. — [Man Group / Harvey, "Backtesting"](https://www.man.com/insights/backtesting); [Harvey & Liu, "Backtesting" (Duke PDF)](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF)
- **Probability of Backtest Overfitting (PBO).** Bailey, Borwein, López de Prado & Zhu propose combinatorially symmetric cross-validation (CSCV). The returns of all tried configurations are split into S blocks, and every half/half combination is formed. For each split, the in-sample-best configuration is found and its out-of-sample rank is recorded. PBO is the fraction of splits in which the in-sample best ranks below the out-of-sample median. *(Method description not fetched this session.)* — [SSRN 2326253](https://papers.ssrn.com/abstract=2326253); [Journal of Computational Finance](https://www.risk.net/journal-of-computational-finance/2471206/the-probability-of-backtest-overfitting)
- **Fragility under one-parameter changes.** Changing a single parameter in the best of 720 timing strategies cut its excess return by more than half. — [Dimensional](https://www.dimensional.com/at-de/insights/we-found-30-timing-strategies-that-worked-and-690-that-didnt)
- **Walk-forward is a single path.** López de Prado (*Advances in Financial Machine Learning*, ch. 11–12) argues that walk-forward testing gives only one historical path and is easy to overfit by repeating it. He recommends purged and embargoed k-fold and combinatorial purged cross-validation (CPCV), which produce a distribution of out-of-sample Sharpe ratios. *(Book content not fetched this session.)*

**Computed for the user's numbers** (binomial math run in this session; not taken from a source):
- With 2 wins in 20 trades (10%), the 95% Clopper–Pearson interval for the true hit rate is about **1.2% to 31.7%**.
- If the true hit rate were 40%, the chance of 2 or fewer wins in 20 trades is about **0.36%**. At 30% it is about 3.5%, and at 20% about 21%. So the data already strongly reject "hit rate ≥ 40%" but cannot tell a 15% strategy from a 25% one.
- To detect a hit-rate edge over 50% at about 95% confidence (z = 1.96) takes about 97 trades for a 10-point edge (60% vs 50%), about 385 trades for 5 points, and about 2,400 trades for 2 points.
- In terms of per-trade Sharpe (mean P&L / standard deviation of P&L per trade), reaching t = 2 takes n = (2/SR)² trades: about 45 trades at SR 0.3, 100 at 0.2, 400 at 0.1, and 1,600 at 0.05. Typical intraday edges sit at the low end of that range.

### Inferences
- **Roughly 20 trades is enough to stop, not to confirm.** A 10% hit rate is only acceptable if winners are about 9 or more times the size of losers (break-even payoff ratio = (1 − p)/p ≈ 9 at p = 0.1). If the logs show otherwise, the current configuration is very likely negative-expectancy and should not be scaled. The user can check whether the low hit rate comes from stop placement or entry lateness by comparing MAE/MFE (maximum adverse and favorable excursion) per trade.
- **How long to paper trade.** Count *trades and P&L per sleeve*, not calendar days. For a plausible per-trade Sharpe of 0.1–0.2, the user needs about 100–400 trades per strategy before reading much into the result. At a few trades a day, that is roughly 2–8 months of paper trading per sleeve. Every change of parameters restarts the clock, or at least counts as a new trial in the DSR.
- **Practical protocol:**
  1. Freeze a written spec before testing.
  2. Log *every* variant tried, to get N for the DSR.
  3. Backtest with realistic slippage and fees on intraday data.
  4. Use purged cross-validation (CPCV) or at least multiple walk-forward folds, plus a final untouched holdout.
  5. Compute PBO across the variant grid and the DSR for the chosen variant.
  6. Paper trade forward with no parameter changes until a pre-registered trade count is reached.
  7. Promote to live capital only if the paper results fall within the backtest's expected range.

### Gaps
- The PBO and CPCV descriptions were not verified against the primary text this session.
- I found no source giving an agreed "minimum number of trades" rule for intraday strategies. The figures above are derived from standard binomial and t-statistic math.

---

## 6. Adaptive weighting of sub-bots by recent performance (hit-rate scoreboard): helps or chases noise?

### Takeaway
With short windows and noisy, correlated components, performance-based reweighting mostly chases noise. Even the forecast-combination literature finds that adaptive schemes rarely beat equal weights except under specific conditions. A hit-rate scoreboard built on tens of trades per bot is far too noisy to tell skill from luck.

### Cited Findings
- **Adaptive schemes rarely win.** Simple averages "repeatedly" beat sophisticated adaptive combinations (Stock and Watson 2004). The adaptive scheme AFTER helps mainly when one candidate is close to the best achievable ("combining for adaptation"). Under structural breaks, shorter windows helped AFTER but made regression weights worse because estimation error grew. — [arXiv 1505.00475](https://arxiv.org/pdf/1505.00475)
- **Past winners persist only when estimated over long samples.** Among day traders, persistence exists but is rare: fewer than 1% are predictably profitable, identified from a *full prior year* of daily data. — [Barber, Lee, Liu & Odean](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)
- **Timing rules fail more often than they work.** Timing strategies (including momentum-of-premium rules) mostly failed in a 720-variant test. — [Dimensional](https://www.dimensional.com/at-de/insights/we-found-30-timing-strategies-that-worked-and-690-that-didnt)

### Inferences
- **A scoreboard of a few trades per bot measures noise.** Across about 20 trades split among 6 bots, each bot's "hit rate" rests on a handful of observations. The 95% interval for 1 win in 5 trades runs from about 0.5% to 72% (standard Clopper–Pearson; not computed this session). Reweighting on numbers like these is close to random.
- **Partial adaptation, if any.** If adaptive weighting is used at all, (a) shrink the weights strongly toward equal (for example w = λ·w_perf + (1 − λ)·equal, with λ small), (b) base it on long windows of hundreds of trades, (c) use expectancy or per-trade Sharpe instead of hit rate, since hit rate ignores payoff size, and (d) count the weighting scheme as another trial in the DSR.
- **Better use of a scoreboard: on/off decisions.** Use the scoreboard *diagnostically*, to decide whether each sleeve stays on or off after a pre-set trade count. Do not use it to reweight sub-bots continuously.

### Gaps
- I found no study that directly tests hit-rate-based reweighting of intraday technical sub-strategies.
