#!/usr/bin/env bash
# One-time upgrade to the demanding plan. Run it FROM THE PROJECT FOLDER while the loop is NOT running:
#   cd ~/MIACS/micrograd-animation
#   bash ~/Downloads/upgrade-demanding.sh ~/Downloads/PLAN.md
set -eu
newplan="${1:?usage: bash upgrade-demanding.sh /path/to/new/PLAN.md}"
[ -f verify.sh ] && [ -f hash.sh ] && [ -d prompts ] && [ -f PLAN.md ] || { echo "Run this from the project folder (verify.sh, hash.sh, prompts/ and PLAN.md must be here)."; exit 1; }
[ -f "$newplan" ] || { echo "New plan not found: $newplan"; exit 1; }
if pgrep -f "loop.sh" >/dev/null 2>&1; then echo "loop.sh is running. Stop it first (touch STOP, or Ctrl-C), then re-run."; exit 1; fi
rows=$(grep -cE '^- \[ \] S[0-9]+ \|' "$newplan" || true)
[ "$rows" -ge 1 ] || { echo "The new plan has no unticked scene rows."; exit 1; }
grep -q '^CAPTIONS_REQUIRED:' "$newplan" || { echo "The new plan has no CAPTIONS_REQUIRED line."; exit 1; }

echo "1/6 backing up the current plan and installing the new one ($rows scenes)"
cp PLAN.md "PLAN.md.bak.$(date +%Y%m%d-%H%M%S)"
cp "$newplan" PLAN.md
grep -qxF 'PLAN.md.bak.*' .gitignore 2>/dev/null || echo 'PLAN.md.bak.*' >> .gitignore

echo "2/6 hash.sh: a scene's fingerprint now covers ALL shared code (src/**/*.py and scenes/_*.py)"
cat > hash.sh << 'EOF'
#!/usr/bin/env bash
# Fingerprint of a scene = its file + all shared code (src/**/*.py and scenes/_*.py). Any shared-code change invalidates earlier reviews.
cd "$(dirname "$0")" || exit 1
cat "$1" $(find src -name '*.py' | sort) $(ls scenes/_*.py 2>/dev/null) 2>/dev/null | shasum -a 256 | awk '{print $1}'
EOF
chmod +x hash.sh

echo "3/6 verify.sh: fail any scene whose captions/<ID>.srt has fewer cues than CAPTIONS_REQUIRED in PLAN.md"
python3 - << 'PY'
p = 'verify.sh'
s = open(p).read()
if 'CAPTIONS_REQUIRED' in s:
    print('   already patched'); raise SystemExit(0)
anchor = '  rm -f frames/"$id"_*.png\n'
if anchor not in s:
    print('   ERROR: verify.sh differs from the expected version; not patched'); raise SystemExit(1)
check = '''  min_caps=$(sed -n 's/^CAPTIONS_REQUIRED: *\\([0-9][0-9]*\\).*/\\1/p' PLAN.md | head -1); min_caps=${min_caps:-0}
  if [ "$min_caps" -gt 0 ]; then
    n_cues=$(grep -c -- '-->' "captions/$id.srt" 2>/dev/null); n_cues=${n_cues:-0}
    if [ "$n_cues" -lt "$min_caps" ]; then
      echo "SCENE $id FAILED: captions/$id.srt has $n_cues cues, PLAN.md requires at least $min_caps (use the Narrator helper)"; fail=1; continue
    fi
  fi
'''
open(p, 'w').write(s.replace(anchor, check + anchor, 1))
print('   patched')
PY
bash -n verify.sh

echo "4/6 prompts: builder and reviewer now enforce the Global requirements"
if ! grep -q '^## Global requirements' prompts/builder.md; then cat >> prompts/builder.md << 'EOF'

## Global requirements (re-read PLAN.md before every iteration)
PLAN.md has a "Global requirements" section (G1 to G9). Every scene must satisfy all of them AND the storyboard in its own row.
Shared code (src/<package>/anim.py and the Narrator helper) is append-only after S00: add functions, never change the behaviour of existing ones.
Before ticking a row, inspect at least 8 frames evenly spread over the video (title card, one per storyboard beat, last frame) and confirm captions are visible and readable in them.
Update progress.md with the Edit tool, not with shell redirects (shell redirects are denied).
EOF
fi
if ! grep -q '^## Global requirements check' prompts/reviewer.md; then cat >> prompts/reviewer.md << 'EOF'

## Global requirements check
First read the "Global requirements" section of PLAN.md. FAIL a scene if any of these is visibly violated:
- subtitles: a readable caption in at least 6 of the 8 frames (title and recap cards excepted);
- text only: frames made only of rows of text and numbers with no diagram, plot, graph or surface;
- inconsistent look: colours or node style differ from the palette in PLAN.md (forward teal, backward orange, active yellow, data blue);
- text smaller than about 24 px tall, overlapping elements, anything clipped or off screen;
- the storyboard beats listed in the scene's row are not visible across the frames.
List each violation as a concrete issue that names the frame number.
EOF
fi

echo "5/6 resetting old review passes and telling the builder what changed"
: > reviews/passed.txt
cat > feedback.md << 'EOF'
The plan was upgraded: every scene must now satisfy the Global requirements in PLAN.md (subtitles through the Narrator helper, never text only, one visual language, honest numbers). Existing scene files from earlier iterations (S01, S02) predate these rules and must be reworked. Start with S00, which also creates src/micrograd_animation/anim.py.
EOF

echo "6/6 committing"
git add -A && git commit -q -m "demanding plan: global requirements, 11 scenes, caption check, wider hash" || echo "(nothing new to commit)"
echo
echo "Done. Rows to build: $(grep -cE '^- \[ \] S[0-9]+ \|' PLAN.md)."
echo "Start the run with:"
echo "  BUILDER_TURNS=60 BUILDER_BUDGET=4 MAX_ITER=60 TOTAL_BUDGET=50 caffeinate -i ./loop.sh; echo \"exit code: \$?\""
