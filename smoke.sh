#!/usr/bin/env bash
# Run this BEFORE the loop. It proves the boundary holds and the toolchain works inside it.
# Usage: ./smoke.sh      (it re-launches itself inside the sandbox)
cd "$(dirname "$0")" || exit 1
if [ -z "${INSIDE_SMOKE:-}" ]; then
  INSIDE_SMOKE=1 ./sandboxed.sh ./smoke.sh; rc=$?
  echo; echo "== claude auth + network (through the sandbox)"
  ./sandboxed.sh ./agent.sh ping | jq -r '.result // .'
  echo; echo "== can the reviewer SEE an image? (should print text like: hello / the formula)"
  ./sandboxed.sh ./agent.sh visionping | jq -r '.result // .'
  echo; echo "== do the headless permission rules behave as intended? (real Claude, builder allow/deny list)"
  mkdir -p .smoke logs; cp prompts/canary.txt .smoke/canary.before; rm -f .smoke/perm_report.txt
  ./sandboxed.sh ./agent.sh permcheck > logs/permcheck.json 2>&1
  if [ -f .smoke/perm_report.txt ]; then cat .smoke/perm_report.txt; else echo "FAIL  no permission report was written (see logs/permcheck.json)"; rc=1; fi
  for n in 1 2 3 4; do grep -q "^$n: ALLOWED" .smoke/perm_report.txt 2>/dev/null && echo "PASS  step $n allowed" || { echo "FAIL  step $n should be ALLOWED"; rc=1; }; done
  for n in 5 6 7; do grep -q "^$n: DENIED" .smoke/perm_report.txt 2>/dev/null && echo "PASS  step $n denied" || { echo "FAIL  step $n should be DENIED"; rc=1; }; done
  cmp -s prompts/canary.txt .smoke/canary.before && echo "PASS  protected canary file unchanged" || { echo "FAIL  protected file was modified"; rc=1; }
  [ "$rc" = 0 ] && echo "PERMISSION CHECK PASSED" || echo "PERMISSION CHECK FAILED: do not run the loop"
  exit $rc
fi
export UV_OFFLINE=1 UV_CACHE_DIR="$PWD/.uv-cache" XDG_CACHE_HOME="$PWD/.cache"
export TMPDIR="$PWD/.tmp" TEXMFVAR="$PWD/.texmf-var" TEXMFCONFIG="$PWD/.texmf-var"
mkdir -p .smoke .tmp .cache .texmf-var
bad=0
pass() { echo "PASS  $1"; }
nope() { echo "FAIL  $1"; bad=1; }
echo "== toolchain must work inside the sandbox"
uv run python -c "import manim" >/dev/null 2>&1 && pass "python + manim import" || nope "python + manim import"
cat > .smoke/smoke_scene.py << 'PY'
from manim import *
class Smoke(Scene):
    def construct(self):
        t = MathTex(r"\frac{\partial d}{\partial a} = b")
        self.play(Write(t)); self.play(Write(Text("hello", font_size=28).next_to(t, DOWN)))
PY
uv run manim -ql -v WARNING .smoke/smoke_scene.py Smoke >/dev/null 2>&1 && pass "render Text + MathTex (LaTeX)" || nope "render Text + MathTex (LaTeX)"
mp4=media/videos/smoke_scene/480p15/Smoke.mp4
[ -f "$mp4" ] && ffprobe -v error -show_entries format=duration -of csv=p=0 "$mp4" >/dev/null 2>&1 && pass "ffprobe sees the video" || nope "ffprobe sees the video"
ffmpeg -loglevel error -y -sseof -0.3 -i "$mp4" -frames:v 1 .smoke/f.png 2>/dev/null && [ -s .smoke/f.png ] && pass "frame extraction" || nope "frame extraction"
echo "== boundary must HOLD (each of these should be blocked)"
ls "$HOME" >/dev/null 2>&1 && nope "could list your home directory" || pass "home directory unreadable"
touch "$HOME/.smoke_outside" 2>/dev/null && { rm -f "$HOME/.smoke_outside"; nope "could WRITE outside the project"; } || pass "write outside project blocked"
curl -sS -m 6 -o /dev/null https://example.com 2>/dev/null && nope "example.com reachable" || pass "arbitrary internet blocked"
echo "== allowed network"
code=$(curl -sS -m 8 -o /dev/null -w '%{http_code}' https://api.anthropic.com 2>/dev/null || true)
[ -n "$code" ] && [ "$code" != "000" ] && pass "api.anthropic.com reachable (HTTP $code)" || nope "api.anthropic.com NOT reachable"
[ "$bad" = 0 ] && echo "SMOKE TEST PASSED" || echo "SMOKE TEST FAILED: fix before running the loop"
exit $bad
