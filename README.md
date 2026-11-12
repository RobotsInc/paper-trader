# Paper Trader v2

An automated day-trading bot on an **Alpaca paper account (fake money)**, run free by GitHub Actions.

- **Live terminal:** https://robotsinc.github.io/paper-trader/
- **Scorecard:** [SCORECARD.md](SCORECARD.md)

## How it trades
1. **Scanner (~9:46 ET).** Scans ~110 liquid stocks/ETFs plus Alpaca's most-active and top-mover lists,
   filters for price >= $10 and real liquidity, and ranks by **opening gap x relative volume**.
   The top **40** names become today's trading list.
2. **AI desk.** Google Gemini (free tier) reads the last ~20h of headlines for those 40 and writes a
   market briefing plus, for each name, a catalyst and a bias: `both`, `long` only, `short` only, or
   `block` (event risk: earnings today, CEO crisis, M&A, regulatory...).
3. **Opening-range breakouts, long and short.** The first 15 minutes set each stock's range.
   Break **above** (and above VWAP) -> buy. Break **below** (and below VWAP) -> short.
   Market filter: longs only while SPY is above its VWAP, shorts only while it's below.
4. **Exits.** Stop at the middle of the range, target at 2x risk, both held by Alpaca. No new trades
   after 2:30 PM; **everything closed by ~3:45 PM**. Never holds overnight.

## Risk limits
0.5% of equity risked per trade - max **5** positions - max 20% of equity per position -
longs + shorts capped at 150% of equity - down 2.5% on the day -> close all, stop for the day.
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

## Caveats
- GitHub's schedule can run 5-15 min late; stops/targets live at Alpaca, so exits aren't affected.
- Paper fills are kinder than real ones (no slippage). Shorts assume easy-to-borrow shares.
- Volume data is from the free IEX feed (a slice of total volume); fine for ranking, not exact.
- Judge it after 20+ trading days.
