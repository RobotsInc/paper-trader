# Paper Trader v2

**Status (restart 2026-11-23):** v1 (below) is retired. The new bot lives in [`v2/`](v2/) and runs from
[`.github/workflows/v2.yml`](.github/workflows/v2.yml): a team of 11 bots (6 signal bots, 4 filters/managers, 1 AI news bot)
that day-trades ~30 liquid stocks on the Alpaca paper account, aiming for a high win rate with tight stops.
Dashboard: https://robotsinc.github.io/paper-trader/ (reads `data/v2/`). Tune everything in [`v2/config.py`](v2/config.py).
Test it without Alpaca: `python -m unittest tests.test_v2` (uses a simulated market).

| Bot | Role |
|---|---|
| vwap, relvol, trend, orb, momentum, meanrev | signal bots (each votes long / short / nothing, with confidence) |
| volume, liquidity | filters that can veto a trade (quiet volume, wide spread, costs too big vs the target) |
| risk | sizing (0.5% risk per trade, max 10% of equity per stock) + limits (15 positions, 3% open risk, 3% daily loss) |
| exits | takes profit at 1R unless the trade is still running; ratchets the stop up behind winners |
| news (AI) | Gemini free tier reads headlines once a day; can block or bias a stock |

Every trade logs each bot's vote (`data/v2/trades.csv`), and `data/v2/bots.json` scores each bot, so weak bots can be cut.
The dashboard shows P&L three ways: paper, estimated costs (slippage), and "if this were live".

---

# Old bot (v1, retired)

An automated day-trading bot on an **Alpaca paper account (fake money)**, run free by GitHub Actions.
A run starts every ~5 minutes and checks the market **every 30 seconds** while it's alive, so breakouts
are caught within about half a minute.

- **Live terminal:** https://robotsinc.github.io/paper-trader/
- **Scorecard:** [SCORECARD.md](SCORECARD.md)

## How it trades (v3: "stocks in play" opening-range breakout)
Rules follow Zarattini, Barbon & Aziz, *A Profitable Day Trading Strategy for the U.S. Equity Market*,
picked over the old rules by a 12-month backtest ([`data/backtest/REPORT.md`](data/backtest/REPORT.md)).

1. **Scanner (~9:36 ET).** Scans ~110 liquid stocks/ETFs plus Alpaca's most-active and top-mover lists.
   Keeps names >= $5 with 14-day average volume >= 1M shares and a 14-day ATR >= $0.50, then ranks by
   **relative volume**: the first 5 minutes' volume vs. the same 5 minutes averaged over the last 14 days.
   The top **20** with relative volume >= 1 are today's "stocks in play".
2. **AI desk.** Google Gemini (free tier) reads the last ~20h of headlines for those names and writes a
   market briefing plus, for each name, a catalyst and a bias: `both`, `long` only, `short` only, or
   `block` (event risk: earnings today, CEO crisis, M&A, regulatory...).
3. **Entries.** The first 5 minutes set each stock's range, and the first candle picks the direction:
   closed green -> buy if price breaks **above** the range; closed red -> short if it breaks **below**.
4. **Exits.** Stop at **10% of the stock's 14-day ATR** from entry, held by Alpaca. **No profit target** -
   winners ride until ~3:45 PM, when everything is closed. No new trades after 2:30 PM. Never holds overnight.

## Small-cap experiment ($5-$10, tracked - not traded)
The scanner also picks up to 15 in-play stocks priced $5-$10 and logs every breakout they give - but never
trades them, because paper fills on cheap stocks are unrealistic. After the close the bot pulls the real
all-exchange bid-ask spread at each signal and scores how the trade would have ended, before and after
paying that spread (`data/smallcap.csv`, summary in the scorecard). It also logs the real spread on the main
list's signals (`data/spreads.csv`) to check the backtest's 0.03%-per-side cost assumption.

## Risk limits
0.5% of equity risked per trade - max **5** positions, **no more than 3 on one side** -
max 20% of equity per position - longs + shorts capped at 150% of equity -
down 2.5% on the day -> close all, stop for the day.

**No doubling up:** a new trade is skipped if it's the same bet as a position already held on the
same side - either in the same group (index ETFs, semis, crypto-linked, big banks, energy, biotech,
metals) or moving in near-lockstep with it today (5-min return correlation >= 0.75).
A long in one and a short in a related name is allowed - that's a hedge.
All settings live in [`bot/config.py`](bot/config.py).

## Measuring what works
Every signal the bot *didn't* take (blocked by AI, against the market trend, no free slot) is still
simulated in `data/shadow.csv`, so you can see whether each filter is earning its keep.

| File | What it is |
|---|---|
| `SCORECARD.md` | Bot vs. buy-and-hold SPY, win rate, drawdown, long vs. short, AI impact |
| `data/live.json` | Everything the terminal shows (updated every run) |
| `data/daily.csv` / `trades.csv` | One row per day / per completed trade |
| `data/shadow.csv` | Signals not taken and what they would have done |
| `data/ai_log.csv` | The AI desk's daily calls |
| `data/equity.csv` | Account equity every ~5 minutes |

## Secrets and settings
Repo secrets: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` (paper keys), `GEMINI_API_KEY`
(free from https://aistudio.google.com/apikey).
Optional repo variables: `AI_FILTER=off` to disable the AI desk; `AI_MODEL` to pin a Gemini model.

## Controls
**Actions -> paper-trader -> Run workflow** with a mode:
`run` (normal check) - `flatten` (close everything now) - `report` (rebuild scorecard) - `ai` (re-run AI desk).
Pause: **Actions -> paper-trader -> ... -> Disable workflow**.
Backtest: **Actions -> backtest -> Run workflow** (months of history, slippage) -> results in `data/backtest/`.

## Caveats
- GitHub's schedule can run late or skip; stops live at Alpaca, so exits aren't affected.
- **Paper fills are perfect.** The scorecard also shows P&L after an estimated 0.03% slippage per fill;
  the backtest says this strategy's edge is about the size of real-world trading costs.
- Shorts assume easy-to-borrow shares.
- Volume data is from the free IEX feed (a slice of total volume); fine for ranking, not exact.
- Judge it after 20+ trading days.
