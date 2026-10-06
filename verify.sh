#!/usr/bin/env bash
# Objective gate. Runs INSIDE the sandbox (it executes agent-written code).
# Exit 0 = oracle tests pass AND every scene marked [x] in PLAN.md renders and passes the mechanical checks.
cd "$(dirname "$0")" || exit 1
export UV_OFFLINE=1 UV_FROZEN=1 UV_CACHE_DIR="$PWD/.uv-cache" XDG_CACHE_HOME="$PWD/.cache"
export TMPDIR="$PWD/.tmp" TEXMFVAR="$PWD/.texmf-var" TEXMFCONFIG="$PWD/.texmf-var"
mkdir -p frames logs .tmp .cache .texmf-var
trim() { sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'; }
# Frame times: the middle of caption cues (a caption is fully visible there), always including the cue that opens each act.
cue_times() {  # $1 = srt file, $2 = number of frames wanted
  awk -v n="$2" '
    function secs(t,   a) { split(t, a, /[:,.]/); return a[1]*3600 + a[2]*60 + a[3] + a[4]/1000 }
    /-->/ { split($0, p, / --> /); k++; mid[k] = (secs(p[1]) + secs(p[2])) / 2; if ((getline line) > 0) txt[k] = line }
    END {
      for (i = 1; i <= k; i++) { keep[i] = (txt[i] ~ /^(Example A|Example B|Expert corner):/) ? 1 : 0; c += keep[i] }
      rest = n - c
      if (k > 0 && rest > 0) for (j = 0; j < rest; j++) { i = int((j + 0.5) * k / rest) + 1; if (i > k) i = k; keep[i] = 1 }
      for (i = 1; i <= k; i++) if (keep[i]) printf "%.2f\n", mid[i]
    }' "$1" 2>/dev/null
}
fail=0
: > frames/index.txt
echo "== oracle tests"
uv run pytest -q --noconftest -p no:cacheprovider tests/test_oracle.py || { echo "ORACLE FAILED"; fail=1; }
echo "== scenes marked done"
while IFS='|' read -r head file cls dur desc; do
  id=$(echo "$head" | awk '{print $NF}'); file=$(printf '%s' "$file" | trim); cls=$(printf '%s' "$cls" | trim)
  dur=$(printf '%s' "$dur" | trim); desc=$(printf '%s' "$desc" | trim)
  min=${dur%-*}; max=${dur#*-}
  echo "-- $id $file $cls"
  [ -f "$file" ] || { echo "SCENE $id FAILED: $file does not exist"; fail=1; continue; }
  if grep -q "^$id $(./hash.sh "$file")\$" reviews/passed.txt 2>/dev/null && [ -f "media/videos/$(basename "$file" .py)/480p15/$cls.mp4" ]; then
    echo "SCENE $id cached (unchanged since its review pass)"; continue
  fi
  if ! uv run manim -ql -v WARNING "$file" "$cls" > "logs/render-$id.txt" 2>&1; then
    echo "SCENE $id FAILED: render error: $(grep -E '^[A-Za-z_.]*(Error|Exception)' "logs/render-$id.txt" | tail -2 | tr '\n' ' ')"; tail -n 25 "logs/render-$id.txt"; fail=1; continue
  fi
  mp4="media/videos/$(basename "$file" .py)/480p15/$cls.mp4"
  [ -f "$mp4" ] || { echo "SCENE $id FAILED: expected $mp4"; fail=1; continue; }
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$mp4" 2>/dev/null || echo 0)
  if ! awk -v d="$d" -v lo="$min" -v hi="$max" 'BEGIN{exit !(d>=lo && d<=hi)}'; then
    echo "SCENE $id FAILED: duration ${d}s outside ${min}-${max}s (these limits are tolerances: do not cut content to fit, adjust a few waits)"; fail=1; continue
  fi
  min_caps=$(sed -n 's/^CAPTIONS_REQUIRED: *\([0-9][0-9]*\).*/\1/p' PLAN.md | head -1); min_caps=${min_caps:-0}
  if [ "$min_caps" -gt 0 ]; then
    n_cues=$(grep -c -- '-->' "captions/$id.srt" 2>/dev/null); n_cues=${n_cues:-0}
    if [ "$n_cues" -lt "$min_caps" ]; then
      echo "SCENE $id FAILED: captions/$id.srt has $n_cues cues, PLAN.md requires at least $min_caps (use the Narrator helper)"; fail=1; continue
    fi
  fi
  min_desc=$(sed -n 's/^DESCRIPTIONS_REQUIRED: *\([0-9][0-9]*\).*/\1/p' PLAN.md | head -1); min_desc=${min_desc:-0}
  if [ "$min_desc" -gt 0 ]; then
    n_lines=$(grep -c . "descriptions/$id.md" 2>/dev/null); n_lines=${n_lines:-0}
    if [ "$n_lines" -lt "$min_desc" ]; then
      echo "SCENE $id FAILED: descriptions/$id.md has $n_lines non-empty lines, PLAN.md requires at least $min_desc"; fail=1; continue
    fi
  fi
  act_ids=$(sed -n 's/^ACT_SCENES: *//p' PLAN.md | head -1)
  case " $act_ids " in
    *" $id "*)
      for phrase in "Example A" "Example B" "Expert corner"; do
        if ! grep -qi -- "$phrase" "captions/$id.srt" 2>/dev/null; then
          echo "SCENE $id FAILED: captions/$id.srt never says \"$phrase\" (each act needs a caption that begins with it)"; fail=1; continue 2
        fi
      done;;
  esac
  rm -f frames/"$id"_*.png
  nfr=0
  for t in $(cue_times "captions/$id.srt" 12); do
    nfr=$((nfr + 1))
    ffmpeg -loglevel error -y -ss "$t" -i "$mp4" -frames:v 1 -vf scale=960:-1 "frames/${id}_$(printf '%02d' "$nfr").png" 2>/dev/null || true
  done
  if ! ls frames/"$id"_*.png >/dev/null 2>&1; then   # no usable captions: evenly spaced frames instead
    fps=$(awk -v d="$d" 'BEGIN{printf "%.4f", 12/d}')
    ffmpeg -loglevel error -y -i "$mp4" -vf "fps=$fps,scale=960:-1" "frames/${id}_%02d.png" || { echo "SCENE $id FAILED: frame extraction"; fail=1; continue; }
  fi
  if grep -q "^$id $(./hash.sh "$file")\$" reviews/passed.txt 2>/dev/null; then
    echo "scene $id already review-passed (unchanged), not re-queued for review"
  else
    echo "$id | $desc | $(ls frames/"$id"_*.png | tr '\n' ' ')" >> frames/index.txt
  fi
  echo "SCENE $id OK (${d}s)"
done < <(grep -E '^- \[x\] S[0-9]+ \|' PLAN.md)
exit $fail
