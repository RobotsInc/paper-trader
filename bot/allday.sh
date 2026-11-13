#!/usr/bin/env bash
# All-day driver: one GitHub job that stays up from before the open until after the
# end-of-day report, running the bot back to back instead of relying on 5-minute cron starts.
#
# - Exits at once on weekends/holidays (Alpaca calendar).
# - Waits for any 5-minute trader run already in progress, so two bots never overlap.
# - Each bot run watches the market ~4 min; between runs it commits data so the dashboard updates.
# - GitHub caps a job at 6 h, so near that limit it starts a fresh copy of itself (relay) and exits.
set -u
START=$(date +%s)
LIMIT=$((5 * 3600 + 30 * 60))   # relay after 5h30m
STOP_HM=1625                    # done after the 16:01 spread scoring + report
API="repos/$GITHUB_REPOSITORY/actions/workflows"

hm() { TZ=America/New_York date +%-H%M; }
log() { echo "[$(TZ=America/New_York date +%H:%M:%S)] $*"; }

commit() {
  git add -A data SCORECARD.md
  git diff --cached --quiet && return 0
  git commit -q -m "bot: $(TZ=America/New_York date '+%Y-%m-%d %H:%M ET')"
  # This job is the only writer while it runs, so on a conflict keep our (newer) data.
  # (During a rebase, "-X theirs" means the commit being replayed = ours.)
  for i in 1 2 3; do
    git pull -q --rebase -X theirs && git push -q && return 0
    git rebase --abort 2>/dev/null
    sleep 5
  done
  log "push failed (will retry next round)"
}

git config user.name "paper-trader-bot"
git config user.email "paper-trader-bot@users.noreply.github.com"

if ! python - <<'PY'
import sys, datetime, zoneinfo
sys.path.insert(0, "bot")
import alpaca
d = datetime.datetime.now(zoneinfo.ZoneInfo("America/New_York")).date().isoformat()
sys.exit(0 if any(x["date"] == d for x in alpaca.calendar(d, d)) else 1)
PY
then
  log "Market is closed today - nothing to do."
  exit 0
fi

if [ "$(hm)" -ge "$STOP_HM" ]; then log "Past $STOP_HM ET - day already finished."; exit 0; fi

for i in $(seq 1 40); do
  n=$(gh api "$API/trader.yml/runs?status=in_progress" --jq .total_count 2>/dev/null || echo 0)
  [ "$n" = "0" ] && break
  log "waiting for a 5-minute run already in progress..."
  sleep 15
done

# Start from the latest data (a 5-minute run may have just committed).
git pull -q --rebase || { git rebase --abort 2>/dev/null; git fetch -q && git reset -q --hard origin/HEAD; }
log "All-day bot started."
while :; do
  if [ "$(hm)" -ge "$STOP_HM" ]; then log "Day finished."; break; fi
  if [ $(( $(date +%s) - START )) -ge $LIMIT ]; then
    log "Near GitHub's 6h job limit - handing off to a fresh job."
    gh api -X POST "$API/allday.yml/dispatches" -f ref=main && break
    log "hand-off failed; continuing in this job"
    LIMIT=$((LIMIT + 600))
  fi
  t0=$(date +%s)
  timeout 600 python bot/trader.py run || log "bot run exited with an error (continuing)"
  commit
  # Market closed (pre-open / after close) makes runs return instantly: idle a bit between checks.
  [ $(( $(date +%s) - t0 )) -lt 60 ] && sleep 120
done
commit
