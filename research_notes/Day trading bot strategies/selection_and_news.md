# Stock Selection ("What to Trade Today") and News/LLM Signals for Intraday Bots

Context: the user's bot trades a fixed list of 30 large/mid-cap symbols and has a Gemini-based news filter that currently crashes because a module is missing. Scope: US equities, intraday, current as of Nov 2026.

## "Stocks in Play" selection: what screens do documented profitable strategies use?

### Takeaway
The best-documented rigorous result is Zarattini, Barbon & Aziz, "A Profitable Day Trading Strategy For The U.S. Equity Market" (2016-2023). Their screen is: price > $5, 14-day average volume >= 1M shares, 14-day ATR > $0.50, relative volume in the first 5-minute bar >= 100% of its 14-day average, and only the top 20 by relative volume that day. It uses no gap-size, float or premarket-volume filters. The edge rises with relative volume. Common retail thresholds for gap %, float and premarket volume have no rigorous published backing that I could find.

### Cited Findings
- Screen, applied daily to about 7,000 US stocks: opening price > $5; 14-day average daily volume >= 1,000,000 shares; 14-day ATR > $0.50; opening-range (first 5-minute) volume / 14-day average for that interval >= 100%; and rank in the top 20 by Relative Volume that day. — [CXO Advisory summary](https://www.cxoadvisory.com/individual-investing/intraday-trading-of-overactive-stocks-via-opening-range-breakout/)
- Trade rules: the direction is set by the first 5-minute candle. A stop order enters at the high of that range (long) or the low (short). The stop-loss is 10% of the 14-day ATR from entry, otherwise the trade exits at the close. Each trade risks 1% of capital, with leverage capped at 4x. Commissions are $0.0035/share (IBKR Pro Tiered). Starting capital is $25k. — [CXO Advisory](https://www.cxoadvisory.com/individual-investing/intraday-trading-of-overactive-stocks-via-opening-range-breakout/)
- Results, 2016-2023, net of commissions: total return >1,600% (1,637%), IRR 41.6%, Sharpe 2.81, annualized alpha 36%. The S&P 500 returned about 198% (Sharpe 0.78) over the same period. — [Concretum Group](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/); [paper PDF (Univ. St. Gallen repository)](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Relative volume vs PnL: average PnL is -0.02R for trades with Relative Volume < 100%, +0.08R above 100%, and +0.38R above 30x. The authors report "a strong positive correlation between Relative Volume and subsequent realized PnL." — [paper PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- Opening-range length matters a lot, even with the RelVol filter: 5-min ORB Sharpe 2.81 (IRR 41.6%); 15-min 1.43 (17.4%); 30-min 0.21 (2.3%); 60-min 0.40 (4.1%). — [paper PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- The paper tests only top-20. It reports no top-50/100 results, no year-by-year decay, no long/short split, no market-cap breakdown and no slippage modelling (commissions only). — [paper PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- QuantConnect community replication: universe of the 1,000 most liquid US stocks (> $5, ATR > $0.50), top 20 by 5-min RelVol. 2016 Sharpe was 2.396 with beta -0.04. 17 of 25 parameter combinations beat SPY. Dollar-ATR thresholds from $0-$2 gave Sharpe about 1.5-2.7, and a unitless 1%-of-price ATR filter gave Sharpe 2.24. Universe sizes from 500 to 1,500 all gave Sharpe > 2. The replication modelled no commissions or slippage. — [QuantConnect research post](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- Practitioner caveats from the same thread:
  - The win rate is low, about 17%. Most trades hit the stop, and a few big winners carry the result.
  - Fees "look like a major issue."
  - Minute-bar backtests place the stop one bar late compared with live trading.
  - Alpaca paper trading rejected some bracket/stop orders as "wash trades."
  - One user reports weak periods (the dot-com era) and suspects stock selection matters more than the ATR mechanics.
  - Source: [QuantConnect thread](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- Concretum defines "Stocks in Play" as stocks with unusually high activity due to company-specific news, earnings, or other fundamental developments. — [Concretum Group](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/)

### Inferences
- Relative volume in the first minutes after the open is the variable the evidence supports. It works as a stand-in for "there is news or a catalyst," so the screen captures catalysts without parsing any news.
- The edge sits in very short opening ranges: 5 minutes, or 1 minute per one QuantConnect user's anecdote. Fills, slippage and stop placement in the first minutes therefore decide whether it works live. A 17% win rate with a 10%-ATR stop is very sensitive to slippage on the stop.
- The paper's universe includes small and mid caps. A $5 price floor, 1M average volume and $0.50 ATR still admit many names far less liquid than a large-cap list, so spreads will be wider.

### Gaps
- I found no rigorous (peer-reviewed or SSRN) evidence for the usual retail "gapper" thresholds: gap > 2-4%, float < 20M, premarket volume > 100k-1M, price $2-$20. These are practitioner conventions without published backtests.
- There are no published out-of-sample (2024-2026) results for the Stocks-in-Play ORB, and no year-by-year decay table.
- No study isolates the effect of slippage. The QuantConnect replication ignores costs, and the paper models commissions only.

## Fixed large-cap watchlist vs dynamic daily scan

### Takeaway
The only direct comparison comes from the same paper. Running the identical 5-min ORB on all eligible stocks earned Sharpe 0.48 (IRR 3.2%, 29% total, worse than buy-and-hold). Restricting it to the daily top-20 by relative volume raised that to Sharpe 2.81 (IRR 41.6%). Nearly all of the edge came from daily selection. A fixed 30-name large/mid-cap list is effectively the "base" (unfiltered) case, and most days those names are not in play.

### Cited Findings
- Base ORB on all eligible stocks: 29% total return, 3.2% IRR, Sharpe 0.48. The authors say it "underperformed" the benchmark. The top-20 Relative Volume (>= 100%) version: 1,637%, 41.6% IRR, Sharpe 2.81. — [paper PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)
- A QuantConnect practitioner who tested across decades concluded performance "depends more on stock selection than the ATR process." This is anecdotal. — [QuantConnect thread](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- Even after restricting to the 1,000 most liquid stocks, which is closer to a large/mid-cap list, the daily top-20 RelVol selection still gave Sharpe > 2 before costs. — [QuantConnect research post](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
- The best-performer tables in the paper include large caps such as TSLA and NVDA. Large caps can qualify when they are in play. — [paper PDF](https://www.alexandria.unisg.ch/server/api/core/bitstreams/3c2989c4-688d-4d78-8a71-f02690990d51/content)

### Inferences
- A practical hybrid for the user's bot: keep the 30-name list as the eligible universe for liquidity and safety, or widen it to roughly the 500-1,500 most liquid names. Each morning, trade only the names whose first-5-min relative volume is >= 100% (ideally the top few by RelVol), rather than all 30. Per the QuantConnect result, a liquid universe with daily RelVol ranking keeps most of the documented edge.
- With only 30 names, many days will have zero or few names at RelVol >= 100%. That is a feature: low-RelVol trades had negative expectancy (-0.02R) in the paper.

### Gaps
- There is no published head-to-head of a fixed list of the same 30 large caps vs a dynamic scan. The evidence is all-stocks vs top-20.
- I found no study of how many symbols the selection should return (top 5 vs 20 vs 50).

## Earnings-day / news-catalyst intraday drift

### Takeaway
Price reaction to news happens fast. For earnings press releases (97% released outside market hours), prices fully reflect the content at the open, and a 9:45-to-close long-short on surprise plus text had negative alpha. For general headlines, Lopez-Lira & Tang find no predictability from 1 to 15 minutes after release but significant drift from 15 minutes after release to the close and into the next day, concentrated in small caps and negative news. Catalyst drift is real but small and is best harvested in less-liquid names. On large caps the news is largely priced by the open.

### Cited Findings
- Wu, Akin, Martineau, Grégoire & Veneris ("Extracting the Structure of Press Releases for Predicting Earnings Announcement Returns", arXiv 2509.24254):
  - "Stock prices fully reflect the content of press releases at market open."
  - A long-short entered at 9:45 and exited at 16:00 had negative alpha: -0.0004 to -0.0055 using surprise, and -0.0007 to -0.0051 using text-based soft information, the latter significant after costs.
  - Surprise explains about 3.3% of announcement-day return variance; adding FinBERT soft information raises that to about 4.4% (N=134,354).
  - Source: [arXiv 2509.24254](https://arxiv.org/pdf/2509.24254v2)
- Lopez-Lira & Tang intraday timing:
  - ChatGPT score vs returns from 1 to 15 minutes after an intraday headline: statistically insignificant.
  - From 15 minutes after release to the close: coefficient 0.189 (t=5.12). Close-to-close: 0.116 (t=2.31).
  - Going from neutral to positive is worth about 30 bps for a position entered 15 minutes after release and held to the next close.
  - Source: [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Drift is concentrated in small firms. The overnight-news drift coefficient is 0.087 (t=4.09), and the small-firm interaction adds 0.404 (t=4.75). For intraday news, the small-firm interaction is 0.683 (t=3.29). The effect is stronger for negative news: the short leg averages 26 bps/day (Sharpe 2.01) vs 8 bps/day (Sharpe 0.78) for the long leg. — [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Classic multi-day PEAD still appears in recent data but varies by investor base. In 2010-2021, stocks dominated by long-horizon retail investors (StockTwits) show +2.08 pp more drift over days 2-75. A long/short strategy on this earns about 30-40 bps/month (five-factor alpha). This is a multi-day effect, not intraday. — [Vamossy, arXiv 2512.00280](https://www.arxiv.org/pdf/2512.00280)

### Inferences
- For an intraday bot, an earnings or news catalyst is most useful as the reason a stock is in play: it produces relative volume and range. It is weak as a directional forecast once the bell rings. The ORB mechanic lets price set the direction after the open, which fits the evidence that the content is already priced at the open.
- Reading news minutes after release and trading its sign is unlikely to beat the market on large caps.

### Gaps
- I found no rigorous 2024-2026 study of intraday (minute-level) continuation after gaps specifically ("gap-and-go" vs "gap fill") for US stocks.
- Did not locate the classic intraday PEAD/news-momentum literature numbers (e.g., minute-level studies with RavenPack) within the tool budget.

## LLMs for trading: Lopez-Lira & Tang and follow-ups, decay, cost/latency, veto vs directional

### Takeaway
GPT-4 headline scores predicted next-day drift with a gross Sharpe of about 2.6-3.0 for Oct 2021 to May 2024. The effect decayed fast, with Sharpe falling from 6.54 to 1.22 by early 2024. It does not survive about 20 bps round-trip costs and works mainly in small caps and on bad news. Smaller or older models (FinBERT, BERT, GPT-2) failed to predict drift. Backtests can be inflated by look-ahead and "distraction" bias. Recent follow-ups that use LLM news as a tilt or filter on a base strategy show modest, statistically weak improvements. For a large-cap intraday bot, the evidence favors news or LLM output as a risk or veto filter (avoid or flag names with major pending or just-released news), not as a directional alpha source.

### Cited Findings
- Lopez-Lira & Tang, "Can ChatGPT Forecast Stock Price Movements? Return Predictability and Large Language Models":
  - Versions run from v1 (Apr 2023) to v6 (28 Oct 2025).
  - GPT-4 captures the initial reaction with about 90% hit rates; that component is not tradable.
  - It also predicts subsequent drift, especially in small stocks and on negative news.
  - Predictive ability rises with model size.
  - "Strategy returns decline as LLM adoption grows."
  - Source: [arXiv abstract v6](https://arxiv.org/abs/2304.07619v6)
- Data and design:
  - Oct 2021 to May 2024, after the gpt-4-0314 knowledge cutoff of Sep 2021.
  - 159,137 firm-headline-date observations across 4,123 companies, with headlines matched to RavenPack.
  - About 82% of headlines are overnight news.
  - Prompt: "Is this headline good or bad for the stock price of _company_name_ in the short term?" The model answers YES/NO/UNKNOWN.
  - Source: [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Drift strategy, gross: overnight news has a 58% hit rate, 0.34%/day and Sharpe 2.97; intraday news has a 55% hit rate, 0.50%/day and Sharpe 2.63. — [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Decay: annualized Sharpe was 6.54 (2021Q4), 3.68 (2022), 2.33 (2023) and 1.22 (Jan-May 2024). — [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Costs:
  - About 700% cumulative gross return. At 5 bps round-trip it is >300%, at 10 bps >100%, and at 20 bps it is unprofitable.
  - Turnover is about 190%/day.
  - Sharpe at 10 bps is about 1.29-1.34.
  - Source: [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Model comparison on overnight-news drift: GPT-4 Sharpe 2.97, GPT-3.5 1.66, DistilBART-MNLI 1.26, BART-large 1.05, Llama2-70b 0.97. FinBERT scored -0.33, and BERT/GPT-1/GPT-2 were negative. Embeddings plus supervised learning reached 2.53. GPT-4 subsumes RavenPack sentiment in a horse race. — [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)
- Glasserman & Lin, "Assessing Look-Ahead Bias in Stock Return Predictions Generated by GPT Sentiment Analysis":
  - In-sample, anonymized headlines (company names removed) performed better than original ones. The authors attribute this to a "distraction effect" from the model's general knowledge of the company, which they find larger than look-ahead bias and largest for large companies.
  - Out-of-sample, look-ahead bias is not a concern, but distraction may persist.
  - Source: [arXiv 2309.17322](https://arxiv.org/abs/2309.17322)
- Anic, Barbon, Seiz & Zarattini, "ChatGPT in Systematic Investing" (Oct 2025):
  - Design: GPT-4o-mini scores S&P 500 news, collected up to about 15:45-15:55, to tilt a long-only momentum portfolio.
  - Full sample 2019-2025, net of 2 bps: Sharpe rose from 0.57 to 0.69.
  - Out-of-sample Jan 2024-Mar 2025: Sharpe rose from 0.79 to 1.06. Alpha was 3.26%/yr, significant only at the 10% level. Turnover rose from 0.48 to 0.80.
  - A basic prompt was as good as or better than an advanced prompt.
  - Monthly rebalancing beat weekly.
  - Source: [arXiv 2510.26228](https://arxiv.org/html/2510.26228v1)
- FinBERT, a smaller domain model, failed to predict drift (Sharpe -0.33) and made directional calls on only about 25% of headlines. — [arXiv 2304.07619v6](https://arxiv.org/html/2304.07619v6)

### Inferences
- Size of the effect for this bot: on large/mid caps, after costs and after 2024 decay, a directional LLM headline signal is likely near zero. The surviving drift is mostly in small caps and on negative news, which this bot doesn't trade.
- Best use for this bot is a veto or risk filter, because it doesn't need to beat the market:
  - Skip or flatten names with an earnings release or major headline in the last N minutes or pending today.
  - Or skip longs when the headline is clearly negative.
  - This matches the strongest evidence, which is on the short and negative side.
  - It is cheap: one call per symbol per morning, plus calls only when a new headline arrives.
- The veto filter should fail open. A crash such as the current missing module should log and allow trading, or apply a deterministic rule like "earnings today → skip," rather than kill the bot. Because the documented directional value of LLM sentiment for large caps is small, losing the filter costs little.
- Latency: the significant window starts about 15 minutes after release, so a bot doesn't need sub-second LLM latency. Any API model responding within seconds is enough. The 1-15 minute window has no predictable edge.
- To reduce the "distraction" bias, prompt with anonymized headlines ("the company"). Keep prompts simple, since the basic prompt performed as well as the advanced one.
- Gemini specifically: no rigorous study found that evaluates Gemini on headline-return prediction. The model-size finding suggests modern frontier models are at least GPT-4-class, but that is an inference.

### Gaps
- I found no rigorous paper specifically on LLMs scoring headlines for minute-level intraday trading of large caps (2025-2026) with live or out-of-sample results.
- FinGPT: not researched in depth within the tool budget, and no performance figures collected.
- I found no published per-call cost or latency benchmarks for LLM headline scoring in trading. Cost depends on current model pricing, which I did not verify.
- No study directly compares "news as a veto" vs "news as a directional signal" in an intraday strategy. The recommendation above is an inference.

## Free/cheap news and screener data sources via API (2026)

### Takeaway
Alpaca, which the user's bot likely already uses, provides the three things the selection approach needs:
- a most-actives screener (by volume or trades, top up to 100, real-time SIP)
- a top-movers screener
- a news REST endpoint (Benzinga-sourced articles)

The live relative-volume computation still has to be done by the bot from bars, since the screeners rank raw volume or % change, not relative volume. Finnhub's free tier (60 calls/min) works as a backup news source. Massive (formerly Polygon) is EOD-only on its free tier.

### Cited Findings
- Alpaca Most Actives: `GET https://data.alpaca.markets/v1beta1/screener/stocks/most-actives`, with `by` = `volume` | `trades` (default volume) and `top` = 1-100 (default 10). Based on real-time SIP data. A 403 means the subscription doesn't cover the data. — [Alpaca docs: Most active stocks](https://docs.alpaca.markets/reference/screener-2)
- Alpaca Top Market Movers: returns gainers and losers, measured from the previous close to the latest price, using real-time SIP data. Stock movers reset at market open; before the open, the endpoint shows the previous day's movers. Split-adjusted, and only exchange-tradable symbols are included. — [Alpaca docs: Top market movers](https://docs.alpaca.markets/reference/movers)
- alpaca-py: `ScreenerClient.get_most_actives(MostActivesRequest)` and `ScreenerClient.get_market_movers(MarketMoversRequest)`, in module `alpaca.data.historical.screener`. — [alpaca-py Screener API reference](https://alpaca.markets/sdks/python/api_reference/data/stock/screener.html)
- Alpaca News: `GET https://data.alpaca.markets/v1beta1/news`.
  - Parameters: `symbols`, `start`, `end`, `limit` (1-50, default 10), `include_content`, `exclude_contentless`, `sort`, `page_token`.
  - Without real-time access, results are delayed by 15 minutes.
  - Rate limits are reported in X-RateLimit headers; the example shows 100.
  - Articles are attributed to sources such as "benzinga."
  - Source: [Alpaca docs: News](https://docs.alpaca.markets/us/reference/news-3.md)
- Alpaca partnered with Benzinga to provide real-time news through its API. — [Alpaca blog: Alpaca partners with Benzinga](https://alpaca.markets/blog/alpaca-partners-with-benzinga-to-deliver-real-time-embedded-financial-news); [Business Wire, Feb 2022](https://www.businesswire.com/news/home/20220222005083/en/Alpaca-and-Benzinga-Partner-to-Offer-Fintech-Apps-Stock-Market-News)
- Finnhub free tier: 60 calls/min, US coverage, WebSocket for 50 symbols, personal use only. Stock candles are premium (403 on free). Paid US plans cost $49.99-$199.99/mo with 150-900 calls/min. — [Massive vs Finnhub comparison, prices checked Nov 4, 2026](https://massive.com/compare/massive-vs-finnhub) (vendor-authored by a competitor; verify on [Finnhub pricing](https://finnhub.io/pricing))
- Massive (formerly Polygon): the free tier allows 5 calls/min, end-of-day data and 2 years of history. Paid plans cost $29/$79/$199 per month per market with unlimited calls. Benzinga news is a $99/mo add-on. — [Massive vs Finnhub](https://massive.com/compare/massive-vs-finnhub)

### Inferences
- Minimal implementation for the user's bot:
  1. At 9:35 ET, pull 5-min bars for the universe: the 30 names, or a broader liquid list seeded from most-actives `top=100`.
  2. Compute RelVol = first-5-min volume / 14-day average first-5-min volume.
  3. Keep names with RelVol >= 1.0 that pass the price > $5 and ATR > $0.50 filters, and rank them.
  4. Optionally drop names where Alpaca news shows earnings or major headlines and the LLM veto flags them.
  5. Trade the top N.
- The most-actives `by=trades` or `by=volume` list is a cheap proxy for in-play names but is biased toward mega-caps and high-share-count names. RelVol normalizes for that.
- On the free/basic Alpaca plan, the screener (SIP) and news real-time access may return 403 or 15-minute delayed data. The bot should handle a 403 by falling back gracefully.

### Gaps
- I could not confirm from the docs whether the Alpaca Basic (free) plan includes real-time screener and news access, or the exact movers endpoint path and `top` maximum. The SDK lists `MarketMoversRequest`, but the docs page I read did not show its parameters.
- The Alpaca news WebSocket stream was not verified in the docs page I read.
- The exact date of Polygon's rebrand to Massive was not found.
- Finnhub's free-tier news endpoint scope and delay were not confirmed from Finnhub's own page.
