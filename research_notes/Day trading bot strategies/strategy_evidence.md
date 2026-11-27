# Empirical Evidence on Intraday / Day-Trading Strategies for US Equities and ETFs (net of costs)

Research date: 2026-11-27. Scope: US equities/ETFs, flat by the close. Context: Alpaca paper bot, fixed list of 30 large/mid caps, vote-combined VWAP / relative-volume / trend / ORB / momentum / mean-reversion signals, about a 10% hit rate and mostly losing.

Source-quality note: the original papers (Zarattini/Aziz/Barbon on SSRN; Gao-Han-Li-Zhou in JFE 2018; Lou-Polk-Skouras in JFE 2019; Heston-Korajczyk-Sadka in JF 2010) are primary sources. Several of the 2026 out-of-sample replications cited below are independent GitHub or Substack write-ups, not peer-reviewed. Their methods are disclosed and they agree with one another, but treat them as rigorous practitioner evidence, not settled findings.

---

## Q1. Which intraday strategies have documented positive net returns, and on what universe?

### Takeaway
Only two intraday families show large positive net results in well-documented work: (a) the 5-minute opening-range breakout restricted to dynamically selected "Stocks in Play" (Sharpe 2.81, 2016-2023) and (b) the SPY "noise area" intraday momentum strategy (Sharpe 1.33, 2007-2024). Both come from one research group (Concretum: Zarattini, Aziz, Barbon), both assume minimal slippage, and both look much weaker in independent out-of-sample tests from 2026. Academic intraday-predictability results (first-half-hour momentum, intraday periodicity, overnight/intraday splits) are statistically real but small next to realistic trading costs.

### Cited Findings

**Comparison table (headline numbers, as reported by each source)**

| Strategy (source) | Universe | Period | Ann. return | Sharpe | Hit rate | Avg trade | MDD | Costs assumed |
|---|---|---|---|---|---|---|---|---|
| 5-min ORB + Stocks in Play, top 20 by RelVol (Zarattini, Barbon, Aziz 2024) | Over 7,000 US stocks, price > $5, avg vol ≥ 1M, ATR > $0.50 | 2016-2023 | 41.6% IRR (1,637% total) | 2.81 | 48.4% | Not reported for portfolio; +0.08R for RelVol > 100% bucket, +0.38R for RelVol > 30x | 12% | $0.0035/sh commission; no explicit slippage |
| 5-min ORB, all stocks, no RelVol filter (same paper) | Same | 2016-2023 | 3.2% | 0.48 | 41.4% | about −0.02R for RelVol < 100% bucket | 13% | Same |
| 15/30/60-min ORB + RelVol (same paper) | Same | 2016-2023 | 17.4% / 2.3% / 4.1% | 1.43 / 0.21 / 0.40 | 44.7 / 42.4 / 42.3% | n/a | 11 / 35 / 21% | Same |
| QQQ 5-min ORB, 10R target (Zarattini & Aziz 2023) | QQQ only | Jan 2016 - Feb 2023 | 33.2% CAGR (4x leverage) | not in visible summary | about 24% | +0.13R | n/a | $0.0005/sh; zero spread and slippage |
| SPY "Beat the Market" noise-area momentum (Zarattini, Aziz, Barbon) | SPY only | 2007-2024 | 19.6% | 1.33 | 43% | n/a | 25% | Replicator used $0.0035/sh + $0.001/sh slippage |
| Same strategy, independent OOS (Serpa / PazSheimy, 2026) | SPY | May 2024 - Mar 2026 | 4.8% | 0.39 | 45% | n/a | 18.5% | $0.0035 + $0.001/sh |
| ORB Stocks in Play, independent pre-registered OOS (Sun / js3872, 2026) | Top 500 liquid US, top 5 by RelVol | 2020 - Jun 2026 | account went from $100k to about $141 | −0.686 | n/a | −0.0855R net (t = −2.16) | n/a | 1.5bp half-spread + 0.025×ATR adverse selection + commission + 3%/yr borrow |
| VWAP trend "Holy Grail" (Zarattini & Aziz 2023) | QQQ | per paper | 671% total (net of commissions) | 2.1 | n/a | n/a | 9.4% | Commission only |
| Market intraday momentum (Gao, Han, Li, Zhou JFE 2018) | SPY | 1993-2013 | n/a (R² about 1.6%) | n/a | n/a | n/a | n/a | Not a cost-adjusted rule |

**ORB on Stocks in Play: rules and results**
- Paper: "A Profitable Day Trading Strategy For The U.S. Equity Market," Carlo Zarattini, Andrea Barbon, Andrew Aziz, dated Feb 16, 2024 (SSRN 4729284). Data: CRSP (survivorship-bias free) plus IQFeed intraday, Jan 1, 2016 to Dec 31, 2023 — [Paper PDF, Univ. St.Gallen repository](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Universe filters: opening price above $5, 14-day average volume of at least 1,000,000 shares, 14-day ATR above $0.50 — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Stock-in-play selection: Relative Volume is the volume of the first 5-minute bar divided by the average volume of the same 5-minute window over the prior 14 days. Only stocks with RelVol ≥ 100% qualify, and only the top 20 by RelVol are traded each day — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Entry: a stop order at the high of the first 5-minute bar if that bar is bullish (long), or at its low if bearish (short). No trade on a doji (open equals close) — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Stop: 10% of the 14-day ATR from entry. No profit target. Exit at 4:00 pm ET. Risk 1% of capital per position. Maximum leverage 4x. Commission $0.0035/share. Starting capital $25,000 — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Top-20 RelVol: 1,637% total, 41.6% IRR, 14.8% vol, Sharpe 2.81, hit ratio 48.4%, MDD 12%, alpha 35.8%, beta 0.00. Base ORB on all stocks: 29% total, 3.2% IRR, Sharpe 0.48, hit 41.4%. S&P 500 buy-and-hold over the same period: 198% total, Sharpe 0.78 — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content); headline numbers confirmed on [Concretum summary page](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/)
- The paper reports average PnL by RelVol bucket: about −0.02R below 100% RelVol, +0.08R above 100%, +0.38R above 30x — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)

**QQQ 5-minute ORB ("Can Day Trading Really Be Profitable?")**
- Rules: if the first 5-minute bar is up (down), buy (sell) at the start of the second bar. Stop at the low (high) of the first bar. Target 10× the entry-to-stop distance. Otherwise exit at 4:00 pm. Risk 1% per trade, $25k start, 4x max leverage, 1,795 trades from Jan 2016 to Feb 2023. Result 33.2% CAGR vs 14.9% for QQQ buy-and-hold. Commission $0.0005/share with no bid-ask spread or slippage. A TQQQ variant used a stop at 5% of the 14-day ATR and no target — [CXO Advisory summary](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy); paper at [SSRN 4416622](https://papers.ssrn.com/abstract=4416622)
- The paper reports a 24% hit rate and +0.13R per trade — [MQL5 replication blog](https://www.mql5.com/en/blogs/post/776235)

**SPY intraday momentum, "Beat the Market" (Zarattini, Aziz, Barbon)**
- Reported 2007-2024: 19.6% annualized, Sharpe 1.33, near-zero market correlation. Rules: a 14-day lookback defines a "Noise Area," decisions are made at 30-minute intervals, exits are VWAP-based trailing stops, and positions are volatility-targeted — [Larry Swedroe, Oct 22, 2026](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real); [Concretum page](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
- Rule detail from the replication: the noise-area band width is the 14-day average absolute move from the open at each time of day. Entry when the close is beyond both the band and VWAP, checked on half-hour marks. Trailing stop at max(boundary, VWAP). Sizing targets 2% daily vol with 4x max leverage. Costs $0.0035/sh commission + $0.001/sh slippage — [PazSheimy OOS repo](https://github.com/PazSheimy/spy-intraday-momentum-oos)

**Market intraday momentum (academic)**
- Gao, Han, Li, Zhou (JFE 2018, vol 129(2), pp. 394-414): the first half-hour return on the market (previous close to 10:00) predicts the last half-hour return (15:30-16:00) for SPY. R² about 1.6% over 1993-2013. Stronger on volatile, high-volume, and macro-news days — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414); [Temperance replication](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates)

**Cross-sectional intraday periodicity (academic)**
- Heston, Korajczyk, Sadka: NYSE stocks 2001-2005. A stock's half-hour return predicts its return in the same half-hour on later days (decile spread about 3.01 bps per half-hour, significant for up to 40 days), strongest in the first and last half-hours. Short-lag returns reverse, mostly from bid-ask bounce. Strategies that pay the spread lose money, and the authors conclude the pattern "does not present a profit opportunity." One-way spread cost: about 4-7 bps for small stocks, under 5 bps for medium and large — [arXiv/ar5iv version](https://ar5iv.arxiv.org/html/1005.3535)

**Retail day-trader base rates (context)**
- Brazil equity-futures day traders who started 2013-2015: 97% of those who persisted more than 300 days lost money, and 1.1% earned more than the minimum wage. Taiwan 1992-2006: about 15% of day traders beat fees net. Barber and Odean (Schwab accounts 1991-1996): the most active traders returned 11.4%/yr vs 17.9% for the market — [CNBC summary](https://www.cnbc.com/2020/11/20/attention-robinhood-power-users-most-day-traders-lose-money.html); underlying papers [Barber, Lee, Lin, Odean (Berkeley)](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf), [Chague et al. (IDEAS)](https://ideas.repec.org/p/fgv/eesptd/525.html)

### Inferences
- The only edge with a large documented net return (Stocks-in-Play ORB) depends on a dynamic, news-driven universe chosen each morning by opening relative volume. Applied to "all stocks" it drops to Sharpe 0.48, before any slippage. A fixed list of 30 large/mid caps is structurally much closer to the "base ORB" case than to the top-20 case.
- The SPY/QQQ strategies are the most relevant to a fixed-list bot because they trade one very liquid instrument, where spread costs are about 1 bp. Even so, their OOS performance has dropped sharply (see Q3).
- Base rates from retail studies show that most day trading loses after costs. A bot that is "mostly losing" is the expected outcome, not an anomaly.

### Gaps
- Could not retrieve the exact Sharpe and alpha of the QQQ ORB paper (CXO page paywalled), or the exact noise-area formula from the original Beat-the-Market PDF. The replicator's description is used instead.
- No peer-reviewed journal publication found for the Concretum papers. They are SSRN working papers.
- Taiwan study figures come via a CNBC summary, not the primary PDF.

---

## Q2. How sensitive are results to costs/slippage and to the universe (fixed 30 large caps vs dynamic Stocks in Play)?

### Takeaway
Extremely sensitive. In practically every independent test, the gross edge of ORB-type rules (about 0.1-0.2R per trade) is the same size as one realistic round-trip cost. The Stocks-in-Play universe is also where spreads and adverse selection are worst: news-driven, high-RelVol stocks at the open. Universe choice matters most: in the original paper, removing the RelVol filter takes Sharpe from 2.81 to 0.48. Shortening the opening-range window from 60 to 5 minutes also matters, but that window is exactly where fills are worst.

### Cited Findings
- **Pricing-the-Fill (David Sun, 2026; pre-registered OOS of the Stocks-in-Play ORB).** QuantConnect LEAN, minute bars, top-500 liquid US stocks point-in-time, top 5 by RelVol. Costs: 1.5 bp half-spread, 0.025×ATR adverse selection on entry (a constant 0.125R per trade, since R = 0.20×ATR), commission, and 3%/yr borrow. In-sample 2016-19 (3,370 trades): true gross +0.206R, net +0.0025R. OOS 2020 to June 2026 (5,294 trades): gross +0.078R, net −0.0855R (t = −2.16), Sharpe −0.686 — [GitHub js3872/Pricing-the-Fill](https://github.com/js3872/Pricing-the-Fill)
- Same source: a labelling bug ("gross" computed from fill prices that already included slippage) understated true trading cost about tenfold (0.02R vs about 0.203R per trade). Breakeven adverse selection was about 0.055×ATR in-sample and about 0.008×ATR OOS ("essentially free fills"). Even with 2¢/side and zero adverse selection, the frozen config lost 89.5% in 2024 and 51.1% in 2025, and commissions ($838,627) exceeded total profit ($712,153) — [GitHub js3872/Pricing-the-Fill](https://github.com/js3872/Pricing-the-Fill)
- The Stocks-in-Play paper charges $0.0035/sh commission but states no slippage assumption — [Pricing-the-Fill](https://github.com/js3872/Pricing-the-Fill); consistent with [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- **QQQ ORB replication on five indices (MQL5 blog, 2026).** Index CFDs, Jan 2015 to June 2026, about 2,900 sessions each. Gross reproduces (NQ +0.131R, hit 23.2%; others +0.048R to +0.119R). Net of spread and slippage: NQ +0.002R, SPX −0.081R, Dow −0.081R, DAX −0.038R, FTSE −0.079R, none significantly different from zero. Costs ate about 6-12% of risk per trade. The first candle beats random direction by about +0.10 to +0.13R (t ≥ 2) on NQ, DAX, FTSE, which is roughly one round-trip cost. 2015-2017 was negative in every market — [MQL5 blog](https://www.mql5.com/en/blogs/post/776235)
- The QQQ ORB paper assumed no bid-ask spread, no slippage, and fills at exactly 9:35 and 16:00 prices — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)
- **VWAP "Holy Grail" (QQQ).** QuantConnect users could not reproduce it without adding a minimum price-to-VWAP distance filter, or a 2% deadband, which improved results but stayed "far below the paper's." QC's Jared Broad said the strategy is very sensitive to that filter and "gets eaten alive by covid." Evgenii Lazarev's config-matched version reproduced in-sample but was "much less impressive" OOS after realistic spreads. The key implementation details were flattening one minute before the close and waiting one minute after the open — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/)
- **Intraday momentum costs.** The SPY last-half-hour mean absolute return is 20.1 bps, and the regression explains about 1.4% of its variance. A round trip costs about 2 bps at 1 bp/side, or 10 bps at 5 bps/side — [Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates)
- **Cross-sectional intraday patterns.** Strategies that pay the spread lose money. Effective one-way spreads (under 5 bps for mid/large caps) are comparable to the 3 bps/half-hour signal — [Heston, Korajczyk, Sadka](https://ar5iv.arxiv.org/html/1005.3535)
- **Overnight anomaly (contrast).** SPY 1993-2020: buy-close/sell-open grew 717% gross vs 12% intraday-only. After historical bid-ask spread plus $0.01/sh, the overnight strategy is −32% cumulative. MOO/MOC slippage was not modeled — [Alpha Architect (Bartolini)](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/)

### Inferences
- Rule of thumb from these sources: ORB-style gross edges are about 0.1-0.2R per trade. With stops at 10% of ATR, typical slippage of even 2-3% of ATR consumes most of that. Tight stops measured in ATR fractions make the strategy a bet on fill quality.
- For a fixed 30-symbol large/mid-cap list, spreads are cheaper than for Stocks in Play, but the paper's own data say the edge mostly vanishes without the RelVol/news filter (−0.02R for RelVol under 100%). The bot's universe sits in the low-edge regime.
- Paper-trading fills on Alpaca are simulated and tend to be optimistic for stop/market orders at the open. Live costs would likely be worse than paper results. This is inferred from the adverse-selection findings above, not measured for Alpaca.
- A roughly 10% hit rate is far below every documented version (24% for the 10R-target QQQ ORB, 41-48% for exit-at-close ORB, 43-45% for Beat the Market). That points to stops placed inside normal opening noise and/or signal-vote conflicts, not to a known high-payoff/low-hit design.

### Gaps
- No rigorous source found that quantifies Alpaca paper-vs-live fill differences.
- No independent study found that runs the Stocks-in-Play ORB on a fixed list of about 30 large caps. The paper's "all stocks / RelVol under 100%" buckets are the closest proxy.

---

## Q3. Which strategies have documented decay after publication / out-of-sample?

### Takeaway
Every strategy family examined shows weaker OOS or post-publication results. Market intraday momentum (GHLZ) is flat in SPY from 2013 to 2019. "Beat the Market" falls from Sharpe 1.33 to 0.39 OOS (May 2024 to 2026). The Stocks-in-Play ORB's gross edge falls from +0.21R to +0.08R per trade after 2019 and turns negative net. The QQQ VWAP and ORB results do not survive realistic costs. The overnight anomaly weakened after the dot-com era and after Reg FD.

### Cited Findings
- **GHLZ intraday momentum.** SPY 1-minute bars, Aug 2000 to Dec 2019 (4,785 sessions). Full-window slope 0.060 (t = 3.30), R² 1.39%. By sub-period: 2000-07 slope 0.053 (t 3.31); 2008-12 slope 0.091 (t 2.64), with 2008 alone at R² 7.0%; 2013-19 slope 0.003 (t 0.20), with yearly slopes zero or negative in 2015-2019. The author can't separate regime change from post-publication decay. Note the signal weakened before the 2018 publication — [Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates). A separate "eight years later" replication exists but was not read — [Dead Signals Lab](https://deadsignalslab.substack.com/p/replication-intraday-momentum-eight)
- **Beat the Market (SPY).** In-sample replication on 2015-2024 matched the paper (19.8%, Sharpe 1.34, hit 44.8%, MDD 26.2%). OOS May 2024 to March 2026 with frozen parameters: 4.8% annualized, Sharpe 0.39, hit 45.0%, MDD 18.5%, underperforming SPY buy-and-hold. The Sharpe drop is reported as significant (p < 0.001). Caveat: 4.8%/14.7% vol is about 0.33, so the 0.39 Sharpe figure is internally inconsistent — [PazSheimy repo](https://github.com/PazSheimy/spy-intraday-momentum-oos); covered by [Swedroe, Oct 2026](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real), which says the OOS "told a very different story"
- A second independent replication with "ex-ante frozen anti-overfitting protocols" on SPY and ES exists, along with an SSRN "Beat the Market Revisited... Statistical Audit" by José Enrique Delgado (SSRN 7323419). Neither could be read in this session — [GitHub giovannibrusco](https://github.com/giovannibrusco/zarattini-2024-momentum-spy); [SSRN 7323419](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7323419)
- **Stocks-in-Play ORB.** Gross edge +0.206R (2016-19) falls to +0.078R (2020 to Jun 2026). The author says the edge "disappeared even before execution costs" after 2023. 4 of 12 pre-registered predictions were correct — [Pricing-the-Fill](https://github.com/js3872/Pricing-the-Fill)
- **QQQ ORB.** OOS 2021-2026, NQ reached +0.06R at best (gross). The 2016-2023 paper window omits weaker years: 2015-2017 was negative everywhere — [MQL5 blog](https://www.mql5.com/en/blogs/post/776235)
- **Overnight SPY.** Overnight beat buy-and-hold in 64% of rolling one-year periods before the dot-com bubble but only 34% afterward. The high-earnings overnight spread was significant over the full sample but not after Reg FD (Oct 2000) — [Alpha Architect](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/)

### Inferences
- The pattern matches the McLean-Pontiff style of decay: published intraday edges shrink sharply, and the cleanest intraday ones (SPY momentum) had weakened even before the paper appeared.
- None of the headline Concretum numbers should be taken as a forward estimate. A realistic prior for a faithful, cost-aware implementation is Sharpe between 0 and about 0.5, with big regime dependence (2008, 2020 and 2022 volatility helped momentum/ORB).

### Gaps
- McLean & Pontiff (2016, Journal of Finance) cross-anomaly decay figures were not retrieved in this session, so no numbers are cited for them.
- The Delgado SSRN audit and the Brusco replication were not accessible. Their OOS numbers are unknown.

---

## Q4. What exact rules do the best-documented versions use (entry time, stop, target, exit)? Also: VWAP, mean reversion, gap trading, end-of-day/overnight, pairs.

### Takeaway
The best-documented rules are simple and fully specified: first 5-minute candle direction, stop-order entry, ATR-fraction or candle-extreme stop, exit at 16:00 (optional 10R target), and 1% risk per trade. For SPY momentum: a noise band from the 14-day average move-from-open by time of day, checks every 30 minutes, max(band, VWAP) trailing stop, and vol-targeted size. Intraday mean reversion and gap fades lack strong net-of-cost public evidence for large caps. Short-term reversal is earned overnight and lost intraday, so a pure intraday reversal trade fights the documented pattern.

### Cited Findings

**ORB (Stocks in Play), full rule set**
- 09:30-09:35 first bar. Filters: price > $5, 14d avg vol ≥ 1M, 14d ATR > $0.50, RelVol (first-5-min volume / 14-day average of the same window) ≥ 1.0. Pick the top 20 by RelVol. Stop order at the bar's high (bullish bar) or low (bearish). Skip dojis. Stop at 10% of 14d ATR. Exit at 16:00. Risk 1% per trade. Leverage ≤ 4x — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)

**ORB (QQQ)**
- Enter at 09:35 in the direction of the first bar. Stop at the first bar's opposite extreme. Target 10R. Otherwise exit at 16:00. Risk 1%. Leverage ≤ 4x — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)

**Intraday momentum (SPY)**
- GHLZ: signal is the return from the previous close to 10:00; trade 15:30-16:00 in the same direction — [Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates)
- Beat the Market: noise band = open ± the 14-day average absolute move from the open at each minute of the day. Evaluate at :00/:30. Go long (short) when price closes above the upper (below the lower) band and above (below) VWAP. Trailing stop at max(band, VWAP) for longs, mirrored for shorts. Size for 2% daily vol, capped at 4x. Flat at the close — [PazSheimy repo](https://github.com/PazSheimy/spy-intraday-momentum-oos); [Swedroe](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real)

**VWAP trend (QQQ)**
- Paper claim: $25k grows to $192,656 net of commissions (671%), MDD 9.4%, Sharpe 2.1. The implied rule is long above VWAP / short below on 1-minute bars, with a one-minute wait after the open and flat one minute before the close. Independent coders needed a price-to-VWAP distance filter or deadband to get anywhere close, and OOS results with spreads were "much less impressive" — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/16706/bear-bull-traders-039-paper-on-quot-the-holy-grail-quot-not-so-fast/); paper page [Concretum](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/)

**Intraday mean reversion / overnight-vs-intraday**
- Lou, Polk, Skouras (JFE 2019), CRSP 1993-2013 excluding microcaps. The CRSP VW market earns about 0.55%/month overnight vs 0.38% intraday. Momentum, industry momentum, time-series momentum, SUE and short-term reversal earn their premia overnight (for example MOM overnight alpha 0.98%/month, t 3.84; intraday about 0). Size, value, profitability, investment, beta, IVOL, etc. earn theirs intraday (IVOL about 2.48%/month intraday, −1.46% overnight). Short-term reversal: +0.93%/month overnight, −1.05%/month intraday (t −3.25), offsetting. The authors say costs make exploiting these much less attractive — [Lou, Polk, Skouras PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf); [LSE record](https://researchonline.lse.ac.uk/id/eprint/87481)
- Short-lag (under 1 hour) intraday reversals in individual stocks are mostly bid-ask bounce and liquidity recovery (depth recovers in under 60 minutes). Not profitable when paying the spread — [Heston, Korajczyk, Sadka](https://ar5iv.arxiv.org/html/1005.3535)

**Gap-and-go / premarket gappers / small-cap momentum**
- Concretum has research on "identifying stocks to fade" in less-covered (small-cap) segments and on short-seller-driven overnight effects, but it is paywalled. No rules or numbers could be extracted — [Concretum Substack: stocks to fade](https://concretumgroup.substack.com/p/identifying-stocks-to-fade); [Concretum: short sellers & overnight](https://concretumgroup.substack.com/p/when-short-sellers-create-overnight)
- The Stocks-in-Play ORB is effectively the best-documented "gapper/news momentum" proxy, and its edge rises sharply with RelVol (+0.38R above 30x RelVol) — [Paper PDF](https://alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)

**End-of-day / overnight (contrast)**
- SPY buy-close/sell-open: +717% gross 1993-2020 but −32% after spread and $0.01/sh. Statistically weak (t 1.90) — [Alpha Architect](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/)
- Practitioner updates on whether the overnight drift persisted into 2025 exist but were not read — [Elm Wealth "Night Shift" (Mar 2025)](https://elmwealth.com/night-shift/)

### Inferences
- If the bot keeps a fixed 30-symbol list, the evidence-backed adaptations are:
  - Add a daily RelVol gate so that only names with first-5-minute RelVol ≥ 1, ideally ≫ 1, are traded. Of the 30, most days only a few will qualify.
  - Use one fully specified rule per trade instead of a vote. Every documented edge comes from a single coherent rule, and a vote mixing trend and mean-reversion signals averages opposing bets.
  - Exit at the close (no tight targets) with stops sized to ATR (10% of ATR for ORB, max(band, VWAP) for momentum).
  - Model at least 1-2 bp half-spread plus adverse selection on stop entries, and require a net positive R per trade in walk-forward tests before going live.
- Intraday mean reversion in large caps has no documented net edge in these sources. Short-term reversal returns accrue overnight, and the intraday leg actually loses, so a flat-by-close mean-reversion signal is fighting the documented direction.
- The most robust intraday structure in this evidence is "trend after a significant early move, hold to the close" (ORB, noise-area momentum, last-half-hour momentum). Even that edge is about one round-trip cost and has decayed.

### Gaps
- No rigorous, cost-adjusted public study was found for: RSI(2)-style intraday mean reversion on US equities, gap-fade strategies on large caps, small-cap premarket gapper momentum (gap-and-go), or intraday pairs/stat-arb on US equities in recent years. Treat practitioner claims in these areas (e.g. QuantifiedStrategies posts) as unverified.
- Intraday stat-arb: no source was retrieved this session. Literature on intraday pairs exists, but no numbers are cited here.
- The Concretum small-cap fade research is paywalled. Its rules and performance are unknown.
