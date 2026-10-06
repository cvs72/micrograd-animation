#!/usr/bin/env bash
# Runs OUTSIDE the sandbox but only talks to the reviewer agent (which itself runs sandboxed).
# A scene passes when the reviewer reports no BLOCKING issue. After MAX_REVIEW_REJECTS rejections a scene is accepted with notes,
# so one stubborn scene can never stall the whole project. The loop, not the agent, records verdicts and un-ticks rejected scenes.
cd "$(dirname "$0")" || exit 1
[ -s frames/index.txt ] || { echo "nothing new to review"; echo "REVIEW_COST=0"; exit 0; }
trim() { sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'; }
max_rej=$(sed -n 's/^MAX_REVIEW_REJECTS: *\([0-9][0-9]*\).*/\1/p' PLAN.md | head -1); max_rej=${max_rej:-4}
mkdir -p reviews/notes; touch reviews/rejects.txt reviews/passed.txt
out="logs/review-$(date +%s).json"
./sandboxed.sh ./agent.sh reviewer > "$out" 2> "$out.err" || echo "reviewer exited non-zero"
echo "REVIEW_COST=$(jq -r '.total_cost_usd // 0' "$out" 2>/dev/null || echo 0)"
verdict=$(jq -c '.structured_output // empty' "$out" 2>/dev/null)
[ -n "$verdict" ] || { echo "reviewer returned no structured output"; exit 2; }
: > feedback.md
anyfail=0
while IFS= read -r line; do
  id=$(echo "$line" | cut -d'|' -f1 | awk '{print $1}')
  [ -n "$id" ] || continue
  file=$(grep -E "^- \[.\] $id \|" PLAN.md | cut -d'|' -f2 | trim)
  mentioned=$(echo "$verdict" | jq -r --arg id "$id" '[.scenes[] | select(.id==$id)] | length')
  if [ "$mentioned" = "0" ]; then echo "review MISSING $id (no verdict returned)"; anyfail=1; continue; fi
  blocking=$(echo "$verdict" | jq -r --arg id "$id" '[.scenes[] | select(.id==$id) | .issues[]? | select(.severity=="blocking")] | length')
  nminor=$(echo "$verdict" | jq -r --arg id "$id" '[.scenes[] | select(.id==$id) | .issues[]? | select(.severity!="blocking")] | length')
  blist=$(echo "$verdict" | jq -r --arg id "$id" '.scenes[] | select(.id==$id) | [.issues[]? | select(.severity=="blocking")][:5][] | "- BLOCKING: " + .text')
  mlist=$(echo "$verdict" | jq -r --arg id "$id" '.scenes[] | select(.id==$id) | [.issues[]? | select(.severity!="blocking")][:3][] | "- optional polish: " + .text')
  grep -v "^$id " reviews/passed.txt > reviews/passed.tmp 2>/dev/null; mv reviews/passed.tmp reviews/passed.txt 2>/dev/null
  if [ "$blocking" = "0" ]; then
    echo "$id $(./hash.sh "$file")" >> reviews/passed.txt
    grep -v "^$id " reviews/rejects.txt > reviews/rejects.tmp 2>/dev/null; mv reviews/rejects.tmp reviews/rejects.txt 2>/dev/null
    { echo "# $id: passed review"; [ -n "$mlist" ] && { echo "Minor polish ideas:"; echo "$mlist"; }; } > "reviews/notes/$id.md"
    echo "review PASS $id (minor notes: $nminor)"
    continue
  fi
  n=$(awk -v id="$id" '$1==id{print $2}' reviews/rejects.txt | tail -1); n=$(( ${n:-0} + 1 ))
  grep -v "^$id " reviews/rejects.txt > reviews/rejects.tmp 2>/dev/null; echo "$id $n" >> reviews/rejects.tmp; mv reviews/rejects.tmp reviews/rejects.txt
  if [ "$n" -ge "$max_rej" ]; then
    echo "$id $(./hash.sh "$file")" >> reviews/passed.txt
    grep -v "^$id " reviews/rejects.txt > reviews/rejects.tmp 2>/dev/null; mv reviews/rejects.tmp reviews/rejects.txt 2>/dev/null
    { echo "# $id: ACCEPTED WITH NOTES after $n rejections (polish later)"; echo "$blist"; [ -n "$mlist" ] && echo "$mlist"; } > "reviews/notes/$id.md"
    echo "review ACCEPTED-WITH-NOTES $id after $n rejections"
  else
    anyfail=1; echo "review FAIL $id (rejection $n of $max_rej)"
    perl -pi -e "s/^- \[x\] $id \|/- [ ] $id |/" PLAN.md
    { echo "## Reviewer feedback for $id (row un-ticked; fix ONLY the blocking items, rejection $n of $max_rej)"; echo "$blist"; [ -n "$mlist" ] && { echo "(optional, ignore unless you have time:)"; echo "$mlist"; }; echo; } >> feedback.md
  fi
done < frames/index.txt
[ "$anyfail" = 0 ] && echo "No outstanding review issues." > feedback.md
exit 0
