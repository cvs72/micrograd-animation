#!/usr/bin/env bash
# Outer loop. Run this yourself (NOT inside Claude). Agents never get write access to this file.
set -u
cd "$(dirname "$0")"
MAX_ITER=${MAX_ITER:-8}; TOTAL_BUDGET=${TOTAL_BUDGET:-15}; STALL_LIMIT=${STALL_LIMIT:-3}; FAIL_LIMIT=${FAIL_LIMIT:-3}
WAIT_POLL=${WAIT_POLL:-600}            # seconds between "has the usage limit lifted?" probes
WAIT_MAX_SECS=${WAIT_MAX_SECS:-25200}  # give up waiting after 7 h (a 5-hour window plus margin; a weekly limit takes longer)
MAX_LIMIT_WAITS=${MAX_LIMIT_WAITS:-8}
export GIT_AUTHOR_NAME=loop GIT_AUTHOR_EMAIL=loop@localhost GIT_COMMITTER_NAME=loop GIT_COMMITTER_EMAIL=loop@localhost
command -v jq >/dev/null || { echo "jq missing (brew install jq)"; exit 1; }
[ -n "${SANDBOX_OFF:-}" ] || command -v srt >/dev/null || { echo "srt missing (npm install -g @anthropic-ai/sandbox-runtime)"; exit 1; }
[ -n "${SANDBOX_OFF:-}" ] || [ -f srt-settings.json ] || { echo "run ./setup.sh first"; exit 1; }
[ -n "${ANTHROPIC_API_KEY:-}${CLAUDE_CODE_OAUTH_TOKEN:-}" ] || { echo "set CLAUDE_CODE_OAUTH_TOKEN (claude setup-token) or ANTHROPIC_API_KEY"; exit 1; }
mkdir -p logs reviews; touch feedback.md progress.md reviews/passed.txt
spent=0; stall=0; fails=0; waits=0
plan_sig() { sed -E 's/^- \[[ x]\]/- [ ]/' PLAN.md | shasum -a 256 | awk '{print $1}'; }
sig0=$(plan_sig)
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a logs/loop.log; }
add_cost() { spent=$(awk -v a="$spent" -v b="${1:-0}" 'BEGIN{printf "%.4f", a+b}'); }
over_budget() { awk -v a="$spent" -v b="$TOTAL_BUDGET" 'BEGIN{exit !(a>=b)}'; }
commit_all() { git add -A >/dev/null 2>&1; git diff --cached --quiet && return 1; git -c core.hooksPath=/dev/null commit -q --no-verify -m "$1"; return 0; }
# Cheap session that only succeeds when the account can currently make requests (usage limit lifted, API reachable).
probe() { ./sandboxed.sh ./agent.sh ping 2>/dev/null | jq -e '(.is_error != true) and ((.result // "") | test("OK"))' >/dev/null 2>&1; }
# Output that says the subscription limit / rate limit was hit (format varies by version, so this is only a hint).
looks_limited() { [ -s "$1" ] && jq -e '(.is_error == true) and ((.result // "") | test("limit|resets|rate"; "i"))' "$1" >/dev/null 2>&1; }
wait_for_quota() {
  waits=$((waits+1)); [ "$waits" -gt "$MAX_LIMIT_WAITS" ] && { log "hit the usage limit too many times ($MAX_LIMIT_WAITS waits). Stopping."; exit 8; }
  local t0; t0=$(date +%s)
  log "usage limit (or API outage) detected. Probing every ${WAIT_POLL}s; giving up after ${WAIT_MAX_SECS}s. Nothing is lost: state is in files and git."
  while :; do
    sleep "$WAIT_POLL"
    [ -e STOP ] && { log "STOP file found while waiting"; exit 3; }
    if probe; then log "limit lifted after $(( $(date +%s) - t0 ))s, resuming"; return 0; fi
    [ $(( $(date +%s) - t0 )) -ge "$WAIT_MAX_SECS" ] && { log "still limited after ${WAIT_MAX_SECS}s (weekly limit?). Re-run ./loop.sh later; it resumes from the files."; exit 8; }
  done
}
all_done() {
  grep -q '^- \[x\] S[0-9]* |' PLAN.md || return 1
  grep -q '^- \[ \] S[0-9]* |' PLAN.md && return 1
  while IFS='|' read -r head file rest; do
    id=$(echo "$head" | awk '{print $NF}'); file=$(echo "$file" | xargs)
    grep -q "^$id $(./hash.sh "$file")\$" reviews/passed.txt || return 1
  done < <(grep -E '^- \[x\] S[0-9]+ \|' PLAN.md)
  return 0
}
i=0
while [ "$i" -lt "$MAX_ITER" ]; do
  [ -e STOP ] && { log "STOP file found"; exit 3; }
  over_budget && { log "budget reached ($spent USD)"; exit 4; }
  i=$((i+1))
  log "iteration $i/$MAX_ITER, spent so far $spent USD"
  if grep -q '^- \[ \] S[0-9]* |' PLAN.md; then
    ./sandboxed.sh ./agent.sh builder > "logs/iter-$i.json" 2> "logs/iter-$i.err"; rc=$?
    add_cost "$(jq -r '.total_cost_usd // 0' "logs/iter-$i.json" 2>/dev/null || echo 0)"
    limited=0
    if [ "$rc" -ne 0 ] && ! probe; then limited=1; fi
    looks_limited "logs/iter-$i.json" && limited=1
    if [ "$limited" = 1 ]; then wait_for_quota; i=$((i-1)); continue; fi   # a limit wait does not use up an iteration
    if [ "$rc" -ne 0 ] && [ ! -s "logs/iter-$i.json" ]; then fails=$((fails+1)); log "builder failed rc=$rc (see logs/iter-$i.err), consecutive failures $fails/$FAIL_LIMIT"
    else fails=0; fi
    [ "$fails" -ge "$FAIL_LIMIT" ] && { log "too many consecutive failures"; exit 5; }
    [ "$(plan_sig)" = "$sig0" ] || { log "PLAN.md was changed beyond ticking boxes (durations/scenes edited?). Review with git diff, then re-run."; commit_all "iteration $i: builder (PLAN.md tampered)"; exit 7; }
    if commit_all "iteration $i: builder"; then stall=0; else stall=$((stall+1)); log "builder changed no files (stall $stall/$STALL_LIMIT)"; fi
    [ "$stall" -ge "$STALL_LIMIT" ] && { log "stalled: no progress in $STALL_LIMIT iterations"; exit 6; }
  else
    log "every scene row is ticked; only verification and review are pending"
  fi
  ./sandboxed.sh ./verify.sh > "logs/verify-$i.txt" 2>&1; vrc=$?
  if [ "$vrc" -eq 0 ]; then
    ./review.sh > "logs/review-$i.txt" 2>&1; rrc=$?
    add_cost "$(sed -n 's/^REVIEW_COST=//p' "logs/review-$i.txt" | tail -1)"
    if [ "$rrc" -eq 2 ] && ! probe; then commit_all "iteration $i: loop bookkeeping" || true; wait_for_quota; i=$((i-1)); continue; fi
  else
    { echo "# Objective check failed after iteration $i"; tail -n 60 "logs/verify-$i.txt"; } > feedback.md
    log "objective checks failed (see logs/verify-$i.txt)"
  fi
  commit_all "iteration $i: loop bookkeeping" || true
  if [ "$vrc" -eq 0 ] && all_done; then
    log "ALL SCENES DONE and verified. Spent about $spent USD."
    log "Review the videos yourself:"; ls media/videos/*/480p15/*.mp4 2>/dev/null | tee -a logs/loop.log
    exit 0
  fi
done
log "iteration cap reached without finishing"; exit 1
