#!/usr/bin/env bash
# Objective gate. Runs INSIDE the sandbox (it executes agent-written code).
# Exit 0 = oracle tests pass AND every scene marked [x] in PLAN.md renders with a sane duration.
cd "$(dirname "$0")" || exit 1
export UV_OFFLINE=1 UV_FROZEN=1 UV_CACHE_DIR="$PWD/.uv-cache" XDG_CACHE_HOME="$PWD/.cache"
export TMPDIR="$PWD/.tmp" TEXMFVAR="$PWD/.texmf-var" TEXMFCONFIG="$PWD/.texmf-var"
mkdir -p frames logs .tmp .cache .texmf-var
fail=0
: > frames/index.txt
echo "== oracle tests"
uv run pytest -q --noconftest -p no:cacheprovider tests/test_oracle.py || { echo "ORACLE FAILED"; fail=1; }
echo "== scenes marked done"
while IFS='|' read -r head file cls dur desc; do
  id=$(echo "$head" | awk '{print $NF}'); file=$(echo "$file" | xargs); cls=$(echo "$cls" | xargs)
  dur=$(echo "$dur" | xargs); desc=$(echo "$desc" | xargs)
  min=${dur%-*}; max=${dur#*-}
  echo "-- $id $file $cls"
  [ -f "$file" ] || { echo "SCENE $id FAILED: $file does not exist"; fail=1; continue; }
  if ! uv run manim -ql -v WARNING "$file" "$cls" > "logs/render-$id.txt" 2>&1; then
    echo "SCENE $id FAILED: render error: $(grep -E '^[A-Za-z_.]*(Error|Exception)' "logs/render-$id.txt" | tail -2 | tr '\n' ' ')"; tail -n 25 "logs/render-$id.txt"; fail=1; continue
  fi
  mp4="media/videos/$(basename "$file" .py)/480p15/$cls.mp4"
  [ -f "$mp4" ] || { echo "SCENE $id FAILED: expected $mp4"; fail=1; continue; }
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$mp4" 2>/dev/null || echo 0)
  if ! awk -v d="$d" -v lo="$min" -v hi="$max" 'BEGIN{exit !(d>=lo && d<=hi)}'; then
    echo "SCENE $id FAILED: duration ${d}s outside ${min}-${max}s"; fail=1; continue
  fi
  rm -f frames/"$id"_*.png
  fps=$(awk -v d="$d" 'BEGIN{printf "%.4f", 8/d}')
  ffmpeg -loglevel error -y -i "$mp4" -vf "fps=$fps,scale=960:-1" "frames/${id}_%02d.png" || { echo "SCENE $id FAILED: frame extraction"; fail=1; continue; }
  if grep -q "^$id $(./hash.sh "$file")\$" reviews/passed.txt 2>/dev/null; then
    echo "scene $id already review-passed (unchanged), not re-queued for review"
  else
    echo "$id | $desc | $(ls frames/"$id"_*.png | tr '\n' ' ')" >> frames/index.txt
  fi
  echo "SCENE $id OK (${d}s)"
done < <(grep -E '^- \[x\] S[0-9]+ \|' PLAN.md)
exit $fail
