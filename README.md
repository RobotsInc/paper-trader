# Paper Trader

An automated day-trading bot that trades an **Alpaca paper account (fake money)**,
run for free by GitHub Actions. Results: **[SCORECARD.md](SCORECARD.md)**.

## Strategy (v1)
- **Watchlist:** SPY, QQQ, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD
- **Opening-range breakout, long only.** The first 15 minutes (9:30-9:45 ET) set a high/low range.
  After that, if a stock breaks above the range high (and is above VWAP), the bot buys.
- **Stop** at the middle of the range; **target** at 2x the risk. Alpaca holds both orders, so
  exits happen instantly even between bot runs.
- **Risk:** 0.5% of equity per trade, max 3 positions, max 20% of equity in any one stock.
  Down 2% on the day -> everything closes and the bot stops until tomorrow.
- No new trades after 2:30 PM; **everything closed by ~3:45 PM**. Never holds overnight.

## AI news filter
Once a day, a free AI model (Google Gemini's free tier) reads the last ~20 hours of headlines for each
stock and can **block** stocks with event risk (earnings today, CEO crisis, regulatory shock...).
Every blocked trade is still simulated, so the scorecard shows whether the AI saved or cost money.
If the AI call fails, the bot trades on rules alone.

- Turn it off: **Settings -> Secrets and variables -> Actions -> Variables -> New variable**
  `AI_FILTER` = `off`
- Needs repo secret `GEMINI_API_KEY` (free key from https://aistudio.google.com/apikey)
- Change model: variable `AI_MODEL` (default `auto` = tries free Flash models in order)

## Files
| File | What it is |
|---|---|
| `SCORECARD.md` | Bot vs. buy-and-hold SPY, win rate, drawdown, AI filter impact |
| `data/daily.csv` | One row per day |
| `data/trades.csv` | Every completed trade |
| `data/shadow.csv` | Trades the bot *didn't* take (blocked by AI / max positions) and what they would have done |
| `data/ai_log.csv` | The AI's daily allow/block decisions and reasons |
| `data/equity.csv` | Account equity every ~5 minutes |

## Controls
**Actions tab -> paper-trader -> Run workflow**, then pick a mode:
- `run` - a normal check (same as the schedule)
- `flatten` - close all positions right now
- `report` - rebuild the scorecard

To pause the bot: **Actions -> paper-trader -> ... -> Disable workflow**.

## Caveats
- GitHub's schedule can run 5-15 minutes late at busy times; entries may be late, but stops and
  targets live at Alpaca so exits aren't affected.
- Paper fills are kinder than real fills (no slippage, unlimited liquidity). Real results would be worse.
- GitHub pauses scheduled workflows in repos with no activity for 60 days; the bot's own commits
  normally keep it active.
- Judge it after 20+ trading days. One good or bad week is noise.
