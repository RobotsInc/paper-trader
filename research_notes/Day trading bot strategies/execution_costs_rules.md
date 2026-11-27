# Execution Realities, Costs, Rules and Base Rates for a Retail Alpaca Day-Trading Bot (as of 2026-11-27)

Context: the bot polls 1-minute bars, trades 30 large/mid-cap symbols long and short, runs on an Alpaca paper account (~$98.5k equity), and is scheduled through GitHub Actions jobs.

## Q1. Alpaca specifics: data feeds (IEX vs SIP), PFOF, paper fill model, shorting, scheduling

### Takeaway
On the free Basic plan, real-time equity data is IEX only, about 4% of US share volume, so live 1-minute bars and volumes are a thin, noisy sample of the market. Full SIP data costs $99/month (Algo Trader Plus). Paper fills are simulated at the SIP NBBO. They ignore order size versus displayed liquidity, latency slippage, market impact, queue position and dividends, and they add random partial fills. Paper P&L is therefore optimistic for anything that trades often. Alpaca routes orders to wholesalers for payment for order flow (PFOF). Easy-to-borrow (ETB) shorts carry no borrow fee, and since June 2026 hard-to-borrow (HTB) shorts need paid, single-use locates. GitHub Actions cron is not reliable enough for intraday timing.

### Cited Findings
**Market data plans**
- Basic (free): real-time equities from "IEX only", 30 WebSocket symbols, historical data limited to "Latest 15 minutes" (no SIP data from the most recent 15 minutes), 200 historical API calls/min. Algo Trader Plus: $99/month, "All US stock exchanges" (SIP), unlimited WebSocket symbols, no historical restriction, 10,000 calls/min. Historical data goes back to 2016 on both plans. — [Alpaca: About Market Data API](https://docs.alpaca.markets/docs/about-market-data-api)
- Alpaca staff (2022): on the free plan, SIP data is available only when more than 15 minutes old. When the historical `feed` parameter is not set, it defaults to whichever source returns the most data. That caused a user's live IEX stream to be 10x to 100x sparser than the historical trades he compared it against (QQQ: about one trade every 1-5 s live versus 10-20/s historical). Passing `feed='iex'` gave parity. — [Alpaca forum: Realtime data much less dense than Historical](https://forum.alpaca.markets/t/realtime-data-much-less-dense-than-historical-data/10751)
- IEX market share in February 2026 was 3.9% of US equity share volume (3.7% of notional). Off-exchange trading was 47.8% of shares. — [SIFMA Insights Monthly Metrics, Feb 2026](https://www.sifma.org/wp-content/uploads/2026/02/SIFMA-Insights-Equities-and-Options-Monthly-Metrics_February_2026.pdf). This is a little higher than the "~2-3%" in the brief.
- Paper-only accounts receive only IEX market data. — [Alpaca: Paper Trading](https://docs.alpaca.markets/docs/paper-trading)

**Paper trading fill model**
- Paper orders are "matched against the best available current market price (NBBO)" and fill only when marketable. Once eligible, an order gets "partial fills for a random size 10% of the time." "Your order quantity is not checked against the NBBO quantities." Not modeled: "price slippage due to latency", market impact, information leakage, queue position for non-marketable limit orders, price improvement, regulatory fees and dividends. Borrow fees are "Coming Soon" for paper. — [Alpaca: Paper Trading](https://docs.alpaca.markets/docs/paper-trading)
- Alpaca staff (Dec 2025): paper fills use real-time SIP NBBO quotes with no batching. Buys check the ask and sells check the bid. The last trade price does not matter, the simulator "does not model volatility or liquidity", and fill behavior cannot be configured. Initial order latency is about 10-40 ms. A user saw limit orders fill 50-260 s "late" even though prints traded through his limit. The ask had stayed above his limit, so a limit order does not fill on a trade-through, only when the NBBO crosses it. — [Alpaca forum: Paper Trading Fill Delays](https://forum.alpaca.markets/t/paper-trading-fill-delays-of-50-260-seconds-limit-orders-filled-minutes-after-price-crossed/18223)

**Payment for order flow and routing (live)**
- Alpaca's Rule 606 report, June 2026: S&P 500 non-directed orders went to Citadel (45.7%), Virtu (21.7%), Jane Street (17.1%) and GTS (15.5%). Net PFOF for S&P 500 market orders was 132-167 cents per 100 shares (about $0.013-0.017/share). For non-S&P 500 stocks it was 14-21 cents per 100 shares. Disclosed terms: marketable orders in the core session earn Alpaca "12% of the spread per share, capped at 5 cents per share", and non-marketable orders priced at $1 or more earn 20 mils/share. Alpaca states that PFOF and price improvement come from the same market-maker expected profit, so more of one means less of the other. — [Alpaca SEC 606a1 2026Q2](https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2026Q2.pdf); index at [Alpaca 606 Reports](https://alpaca.markets/disclosures/606-reports)

**Short selling**
- ETB shorts carry "$0 borrow fees" across Alpaca's 5,000+ ETB names. Since June 24, 2026, HTB names (check `GET /v2/assets/{symbol}`, field `borrow_status`) need a locate before a short is opened (`POST /v1/locates`). Locates are single use (a new one is needed after covering), come in round lots of 100 shares, and cost a per-share fee that is "not credited back if a locate is not used". Availability and price "can change quickly". The article does not say whether locates work in paper. — [Alpaca blog: HTB short selling with locates](https://alpaca.markets/blog/htb-trading-api-locates/)

**GitHub Actions scheduling**
- A July 2026 GitHub Community report: a daily `schedule` workflow ran 8-14.5 hours late on 6 consecutive days, and 2 runs never fired. Other replies say GitHub documents that scheduled workflows "may be delayed during periods of high loads", that the top of the hour is a high-load time, and that queued jobs can be dropped. Those replies quote the docs secondhand. — [GitHub Community discussion #201738](https://github.com/orgs/community/discussions/201738)
- Practitioner write-ups describe the same cron drift and silently skipped runs. — [Hackernoon: your GitHub Actions cron job can disappear without failing](https://hackernoon.com/your-github-actions-cron-job-can-disappear-without-failing); [Crontap: GitHub Actions cron drift problem](https://crontap.com/blog/github-actions-cron-drift-problem)

### Inferences
- IEX-only bars come from about 4% of volume, so 1-minute bar volume is roughly 1/25 of consolidated volume and noisier. Some low-activity minutes may have no IEX print, which means missing bars or a stale close. Bar highs and lows can miss the true consolidated extremes. Signals that rely on volume (relative volume, VWAP, volume-confirmed breakouts) or exact range highs and lows (opening-range breakouts) are the most distorted. Price direction for very liquid names should still track the SIP fairly closely.
- Backtest/live mismatch: if the backtest pulls historical bars without `feed='iex'`, it may use SIP bars (older than 15 minutes) while live trading sees IEX bars. Signals then fire on different data in each setting. The bot should pin the `feed` parameter explicitly in both.
- Paper P&L is an upper bound on live results: fills happen at the NBBO with unlimited size and no latency slippage. Paper also gets no price improvement, which is the one thing that makes live market orders cheaper. The net bias depends on order type. Limit orders on paper fill only once the NBBO crosses the limit, with no queue modeling, so passive-fill rates on paper may differ from live in either direction.
- PFOF implication (rough estimate): at 12% of the spread, about 1.46-1.67 cents/share of S&P 500 PFOF implies average quoted spreads of roughly 12-14 cents/share on Alpaca's S&P 500 flow. This is weighted by Alpaca's flow mix. At a $150-300 share price that is about 4-9 bps quoted spread. Treat this as an order-of-magnitude check only.
- A $98.5k paper balance does not represent a "small US account". Live position sizes, margin and borrow availability would differ.
- A GitHub Actions cron that is supposed to fire every few minutes may actually fire 0-60+ minutes late or not at all. A breakout bot that enters on stale signals and cannot reliably run exit or flatten-by-close jobs carries real risk. Options include a long-running process (a VM or container with a WebSocket stream), broker-side bracket or OCO and stop orders so exits do not depend on the next cron tick, or an external scheduler that triggers `workflow_dispatch`.

### Gaps
- GitHub's official docs page was not fetched. The commonly cited "shortest interval is every 5 minutes" and "public-repo schedules disabled after 60 days of inactivity" are from background knowledge and were not verified here.
- No measured study was found of IEX-versus-SIP 1-minute OHLC differences (missing-bar rate, high/low error) for large caps.
- Whether paper accounts simulate HTB locate requirements, or reject HTB shorts, was not confirmed.
- Not confirmed whether paper accounts use the new intraday margin buying-power logic (see Q2).
- Live slippage on Alpaca specifically (Rule 605 effective/quoted spread) was not found. Only routing and PFOF data were obtained.

## Q2. Pattern Day Trader rule status in 2026 and implications for a sub-$25k account

### Takeaway
The PDT rule and its $25,000 minimum are gone. The SEC approved FINRA's amendments to Rule 4210 on April 14, 2026, and they took effect June 4, 2026. Alpaca switched to an "Intraday Margin Framework" that same day. Firms may phase in until October 20, 2027, so other brokers' timing may differ. A sub-$25k live margin account at Alpaca can now day trade without a day-trade count. It is limited by real-time intraday buying power and margin-deficit rules instead. Leverage-enabled accounts with $2,000 or more get 4x intraday buying power.

### Cited Findings
- FINRA Regulatory Notice 26-10: the new intraday margin standard replaces the day-trading margin requirements "in their entirety". That eliminates the day-trade-count PDT designation and the $25,000 minimum. SEC approval order dated April 14, 2026; notice published April 20, 2026; effective June 4, 2026; optional phase-in for members until October 20, 2027. Members compute an "intraday margin deficit" on days with IML-reducing transactions (for example, short sales and opening purchases). Real-time monitoring is not required. Deficits must be met "as promptly as possible", and stay outstanding until met or until the 15th business day. A customer who makes a practice of failing to meet deficits by the 5th business day faces a 90-day restriction on increasing debit or short positions. Deficits at or below the lesser of 5% of equity or $1,000 are excluded from that test. Regular maintenance margin is unchanged. — [FINRA Regulatory Notice 26-10](https://www.finra.org/rules-guidance/notices/26-10); [FINRA notice PDF](https://www.finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf)
- Law-firm summary of the SEC approval. — [WilmerHale client alert, Apr 23 2026](https://www.wilmerhale.com/en/insights/client-alerts/20260423-sec-approves-amendments-to-finra-rule-4210-replacing-day-trading-margin-requirements-with-a-modernized-intraday-margin-standard)
- Alpaca implemented its Intraday Margin Framework on June 4, 2026. "Intraday Buying Power" replaces Day Trade Buying Power and updates through the day based on equity, positions and intraday P&L. Pre-trade checks reject orders that would create a margin deficit. Repeatedly failing to meet intraday margin calls within 5 business days can restrict the account for up to 90 calendar days. For leverage-enabled accounts, the minimum equity for 4x intraday buying power drops from $25,000 to $2,000. Day-trade and PDT fields were to be removed from the Trading API by July 6, 2026. Accounts previously restricted under PDT were unrestricted. — [Alpaca blog: FINRA Retires the PDT Rule](https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/); [Alpaca on X, Jun 4 2026](https://x.com/AlpacaHQ/status/2062566639325917446)
- Alpaca has separate docs pages for the rule and for non-leverage margin accounts (not fetched in detail). — [Alpaca docs: The Intraday Margin Rule](https://docs.alpaca.markets/us/docs/the-intraday-margin-rule); [Alpaca docs: Intraday Margin Rule for Non-Leverage Margin Accounts](https://docs.alpaca.markets/us/docs/intraday-margin-rule-for-non-leverage-margin-accounts)

### Inferences
- Any code that reads `daytrade_count`, `pattern_day_trader` or `daytrading_buying_power` from the account endpoint may break or return fixed values after July 6, 2026. It should switch to the intraday buying-power fields.
- The binding constraint for a small account is now economic, not regulatory. Fixed per-share costs (spread, slippage, regulatory fees) are a constant fraction of notional, but small accounts buy fewer shares and are more exposed to the 100-share round-lot minimum for HTB locates. Shorting still requires a margin account, and Reg T end-of-day margin still applies.
- Cash accounts were not addressed by the notice. Settlement rules (T+1) and good-faith-violation constraints presumably still apply to cash accounts.

### Gaps
- The exact Alpaca intraday buying-power formula for non-leverage (1x) margin accounts, and any general margin-account minimum for those accounts, was not extracted.
- No confirmation of how Alpaca paper accounts model the new framework.

## Q3. Realistic spread and slippage costs (large vs small caps; market vs limit vs stop)

### Takeaway
For liquid large caps, the half-spread is roughly 0.5-5 bps per side, and wholesaler price improvement on small market orders recovers part of it. For $1-5B mid caps, the effective spread was about 4.5-21 bps round trip in SEC data (2013). For sub-$500M small caps it is tens to hundreds of bps. A reasonable conservative assumption for a polling bot trading large/mid caps is 2-5 bps per side for marketable orders in mega caps, 5-15 bps per side for mid caps, and more for stop orders that trigger during fast moves. Limit orders save the spread but suffer adverse selection and non-fills.

### Cited Findings
- SEC DERA (Collver, 2014; 2013 data): median relative effective spreads were 4.5-21 bps for $2-5B stocks, 7-19 bps for $1-2B, 10-21 bps for $500M-1B, 17-37 bps for $250-500M, 36-64 bps for $100-250M and 92-124 bps for stocks under $100M. Quoted spreads were higher (for example, 7-24 bps for $2-5B and 175-264 bps for stocks under $100M). Spreads fall steeply as market cap rises. — [SEC: A characterization of market quality for small capitalization US equities](https://www.sec.gov/marketstructure/research/small_cap_liquidity.pdf)
- Fidelity Rule 605-eligible market orders (100-1,999 shares), July-December 2025: 92-98% of shares received price improvement, and about 98-99.5% executed at or inside the NBBO. — [Fidelity Capital Markets execution quality statistics](https://capitalmarkets.fidelity.com/trade-execution-quality/statistics)
- Alpaca PFOF terms (12% of spread, capped at 5c/share) and the trade-off between PFOF and price improvement are described under Q1. — [Alpaca SEC 606a1 2026Q2](https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2026Q2.pdf)
- Barber, Lee, Liu and Odean assume a 10 bps round-trip commission plus a 30 bps sell tax for Taiwan. That is far higher than US costs, which is one reason Taiwan and Brazil base rates should be read with care for a US large-cap bot (see Q4). — [Barber et al., Cross-Section of Speculator Skill](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)

### Inferences
- Rules of thumb (inferred from the sources above, not measured on Alpaca):
  - Mega caps (AAPL, MSFT, NVDA, SPY-type liquidity; one-cent spreads on a $100-500 stock = 0.2-1 bps quoted): about 1-3 bps per side all-in for small marketable orders, including some latency slippage.
  - Large/mid caps ($5-50B, multi-cent spreads): about 3-8 bps per side.
  - Mid caps ($1-5B): about 5-15 bps per side.
  - Small caps (under $1B): 10-50+ bps per side, which is usually unworkable for intraday edges.
- Order types:
  - Market orders pay the half-spread minus price improvement.
  - Marketable limit orders cap slippage but can miss fills in fast markets.
  - Passive limit orders earn the spread but get adversely selected: fills come disproportionately when price is moving against you.
  - Stop-market orders trigger in momentum and execute into a moving book. They often slip several bps beyond the stop in large caps, and much more on gaps, halts or news.
  - Breakout entries are effectively buy-stops and inherit the same adverse slippage.
- Polling latency adds slippage beyond the spread, because the signal price is minutes old by the time the order is sent (see Q5).
- Regulatory fees (SEC Section 31 fee and FINRA TAF on sells) are small relative to spread, but paper ignores them.
- Break-even arithmetic: at about 5 bps per side (10 bps round trip), a strategy making 4 round trips/day across the book needs more than 10 bps of average gross edge per trade just to break even. Most published intraday anomalies on liquid large caps are of that size or smaller.

### Gaps
- No current (2025-2026) source was found giving large-cap effective spreads in bps by cap tier. The SEC data is from 2013, and spreads in large caps have likely tightened since, though tick-constrained names are already at minimum.
- No measured data was found on stop-order slippage for US large caps.
- No Alpaca-specific Rule 605 execution-quality numbers were obtained.

## Q4. Base rates: what fraction of real day traders profit after costs

### Takeaway
Across the largest datasets (complete Taiwan exchange records 1992-2006; every Brazilian equity-futures day trader 2013-2015), the large majority lose money. Only about 13-15% are profitable net of costs in a given year. Less than 1% are predictably profitable year after year. Of Brazilians who persisted at least 300 days, 97% lost money and only 0.4% earned more than a bank teller.

### Cited Findings
- Barber, Lee, Liu and Odean, "The Cross-Section of Speculator Skill: Evidence from Day Trading" (Taiwan, 1992-2006, complete TSE transaction data):
  - "about 15%" of day traders earn abnormal returns net of fees; elsewhere, "13% of day traders earn profits net of costs in the average year".
  - "less than 1% of day traders (1,000 out of 360,000)" earn predictable, reliably positive net returns.
  - The top 500 by prior-year return earn 28.1 bps/day net (49.5 bps gross).
  - Prior-year losers earn -34.2 bps/day net.
  - Cost assumptions: 10 bps round-trip commission plus 30 bps sell tax.
  - — [Barber et al. 2011 working paper (Haas)](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)
- Barber, Lee, Liu, Odean and Zhang, "Learning, Fast or Slow," *Review of Asset Pricing Studies* 10(1):61-93 (2020): day traders in aggregate lose money, 74% of day-trading volume comes from traders with a history of losses, and "97% of day traders are likely to lose money in future day trading". Results fit overconfidence and biased learning better than rational learning. — [IDEAS/RePEc record](https://ideas.repec.org/a/oup/rasset/v10y2020i1p61-93..html); earlier version "Do Day Traders Rationally Learn About Their Ability?" — [Haas PDF](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/day%20trading%20and%20learning%20110217.pdf)
- Chague, De-Losso and Giovannetti, "Day Trading for a Living?" (FGV EESP Textos para discussão No. 525, 2019/2020): covers all individuals who began day trading Brazilian equity mini-index futures in 2013-2015 and persisted 300 or more days. 97% lost money; only 0.4% earned more than a bank teller's first salary (about US$54/day); the best individual earned about US$310/day with a daily standard deviation of US$2,560; no evidence of learning. — [IDEAS/RePEc: FGV TD 525](https://ideas.repec.org/p/fgv/eesptd/525.html); [SSRN 3423101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101); [Quantpedia summary](https://quantpedia.com/retail-day-trading-is-an-uphill-battle/)

### Inferences
- The prior for any new retail intraday strategy should be "loses after costs". A bot removes some behavioral errors (overtrading after losses, disposition effect), but the core finding is lack of persistent edge against faster, better-informed counterparties. Automation does not change that.
- The Taiwan cost structure (40 bps+ round trip) was much harsher than US commission-free large-cap trading (about 2-20 bps round trip). Gross skill that failed in Taiwan might survive in the US, so the percentages are not directly transferable. The Brazil study is futures, where costs are low, and it still found 97% losers, which suggests costs are not the only problem.
- Survivorship matters in both directions. Brazil's 300-day filter keeps the most committed traders, and they still lost. Taiwan's 13-15% profitable in a given year is mostly luck, because fewer than 1% stay profitable predictably.
- Paper results over a few weeks or months cannot distinguish skill from luck. Even the top Taiwan cohort's edge (about 28 bps/day net) came with high variance.

### Gaps
- No large-sample US-specific retail day-trader profitability study was retrieved in this pass. Older US work (for example, Jordan & Diltz 2003; Barber-Odean on discount-broker accounts) was not fetched.
- No published base rates for retail algorithmic bots specifically.

## Q5. Data latency: polling 1-minute bars every few minutes vs streaming; effect on breakouts

### Takeaway
No source directly measuring this was found. The sourced mechanics (IEX-only live data on Basic, a 15-minute SIP restriction on free historical data, GitHub cron delays) imply that a bot polling 1-minute bars every few minutes acts on signals that are minutes stale. Breakout strategies are hit hardest, because the move they are meant to capture happens in the first seconds to minutes after the level breaks.

### Cited Findings
- Free plan: live data is IEX only, and SIP historical data is restricted to bars older than 15 minutes. A poll for "latest" bars on Basic without `feed='iex'` may silently return older SIP data, or less dense data than expected. — [Alpaca: About Market Data API](https://docs.alpaca.markets/docs/about-market-data-api); [Alpaca forum: feed defaults](https://forum.alpaca.markets/t/realtime-data-much-less-dense-than-historical-data/10751)
- Basic allows 30 WebSocket symbols, which equals the bot's 30-symbol universe, so streaming IEX bars, quotes and trades for all 30 is within free limits. — [Alpaca: About Market Data API](https://docs.alpaca.markets/docs/about-market-data-api)
- Paper order latency is about 10-40 ms once submitted. Delay comes from the signal pipeline, not the broker. — [Alpaca forum staff reply](https://forum.alpaca.markets/t/paper-trading-fill-delays-of-50-260-seconds-limit-orders-filled-minutes-after-price-crossed/18223)
- Scheduled GitHub workflows can be delayed by hours or dropped under load. — [GitHub Community discussion #201738](https://github.com/orgs/community/discussions/201738)

### Inferences
- With an N-minute poll, the average lag between a breakout and the bot's order is about N/2 minutes plus bar-completion lag (up to 1 minute) plus scheduler delay. A breakout that moves 20-50 bps in its first 2-3 minutes would see much of the move gone before entry, leaving the bot to buy late into the move. This turns paper "breakout" profits computed on bar closes into live slippage.
- In backtests on 1-minute bars, assuming entry at the signal bar's close is optimistic for a poller. Entry should be modeled at a later bar (open of bar t+k, where k reflects poll interval plus scheduler delay), plus the spread.
- Mean-reversion and slower signals (5-15 minute horizons, VWAP reversion, end-of-day effects) are less sensitive to minute-level lag than breakouts. Lag still adds cost.
- A WebSocket stream on a persistent host removes most of the lag at zero data cost (30 symbols on IEX). Paying $99/month for SIP fixes the volume and range distortion. On a small live account, $99/month is a fixed cost that needs real edge to cover. For example, on a $10k account it is about 1% of equity per month.

### Gaps
- No empirical study was found quantifying alpha decay or slippage from minute-level signal delay for retail breakout strategies on US large caps.
- Alpaca's bar finalization timing (how soon after the minute closes the 1-minute bar is available via REST and stream, and whether late trades revise it) was not documented in the sources fetched.
