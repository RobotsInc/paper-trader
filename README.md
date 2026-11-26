# Paper Trader v2

**Status (restart 2026-11-23):** v1 is retired and was removed from the repo (it's still in git history). The new bot lives in [`v2/`](v2/) and runs from
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

## Secrets and settings
Repo secrets: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` (paper keys), `GEMINI_API_KEY`
(free from https://aistudio.google.com/apikey).
Optional repo variables: `AI_FILTER=off` to disable the AI news bot; `AI_MODEL` to pin a Gemini model.
