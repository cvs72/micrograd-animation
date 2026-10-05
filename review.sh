#!/usr/bin/env bash
# Runs OUTSIDE the sandbox but only talks to the reviewer agent (which itself runs sandboxed).
# The loop, not the agent, records pass/fail and un-ticks failed scenes.
cd "$(dirname "$0")" || exit 1
[ -s frames/index.txt ] || { echo "nothing new to review"; echo "REVIEW_COST=0"; exit 0; }
out="logs/review-$(date +%s).json"
./sandboxed.sh ./agent.sh reviewer > "$out" 2> "$out.err" || echo "reviewer exited non-zero"
echo "REVIEW_COST=$(jq -r '.total_cost_usd // 0' "$out" 2>/dev/null || echo 0)"
verdict=$(jq -c '.structured_output // empty' "$out" 2>/dev/null)
[ -n "$verdict" ] || { echo "reviewer returned no structured output"; exit 2; }
: > feedback.md
anyfail=0
while IFS= read -r line; do
  id=$(echo "$line" | cut -d'|' -f1 | xargs)
  file=$(grep -E "^- \[.\] $id \|" PLAN.md | cut -d'|' -f2 | xargs)
  pass=$(echo "$verdict" | jq -r --arg id "$id" '.scenes[] | select(.id==$id) | .pass' | head -1)
  grep -v "^$id " reviews/passed.txt > reviews/passed.tmp 2>/dev/null; mv reviews/passed.tmp reviews/passed.txt 2>/dev/null
  if [ "$pass" = "true" ]; then
    echo "$id $(./hash.sh "$file")" >> reviews/passed.txt; echo "review PASS $id"
  else
    anyfail=1; echo "review FAIL $id"
    perl -pi -e "s/^- \[x\] $id \|/- [ ] $id |/" PLAN.md
    { echo "## Reviewer feedback for $id (row un-ticked; fix and re-render)"
      echo "$verdict" | jq -r --arg id "$id" '.scenes[] | select(.id==$id) | .issues[]? | "- " + .'
      echo; } >> feedback.md
  fi
done < frames/index.txt
[ "$anyfail" = 0 ] && echo "No outstanding review issues." > feedback.md
exit 0
