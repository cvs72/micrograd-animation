#!/usr/bin/env bash
# One-time, run by YOU in a normal terminal (not by an agent). Checks tools, writes srt-settings.json.
set -eu
cd "$(dirname "$0")"
miss=0
need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1   -> $2"; miss=1; }; }
need uv "brew install uv"; need ffmpeg "brew install ffmpeg"; need ffprobe "comes with ffmpeg"
need jq "brew install jq"; need rg "brew install ripgrep (needed by srt on macOS)"
need srt "npm install -g @anthropic-ai/sandbox-runtime"; need claude "install Claude Code"; need git "xcode-select --install"
need python3 "xcode-select --install"; need perl "ships with macOS"
[ "$miss" = 0 ] || { echo "Install the missing tools, then re-run ./setup.sh"; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Not a git repo. Run: git init"; exit 1; }
mkdir -p logs reviews frames scenes tests prompts; touch feedback.md progress.md reviews/passed.txt
for p in media/ frames/ logs/ .claude-home/ .uv-cache/ .cache/ .tmp/ .texmf-var/ .smoke/ STOP; do
  grep -qxF "$p" .gitignore 2>/dev/null || echo "$p" >> .gitignore
done
python3 - << 'PY'
import json, os, shutil, subprocess
def real(p): return os.path.realpath(p)
allow = ["."]
def add(p):
    if p and p.startswith("/Users") and p not in allow: allow.append(p)
for exe in ("claude", "uv", "node"):
    p = shutil.which(exe)
    if p: add(os.path.dirname(p)); add(os.path.dirname(real(p)))
try:
    add(subprocess.run(["uv", "python", "dir"], capture_output=True, text=True).stdout.strip())
except Exception: pass
cfg = {
  "network": {"allowedDomains": ["api.anthropic.com", "claude.ai", "platform.claude.com"], "deniedDomains": []},
  "filesystem": {
    "denyRead": ["/Users"],
    "allowRead": allow,
    "allowWrite": [".", "/tmp", "/private/tmp"],
    "denyWrite": ["./loop.sh", "./verify.sh", "./review.sh", "./agent.sh", "./sandboxed.sh", "./hash.sh", "./setup.sh",
                  "./smoke.sh", "./prompts", "./srt-settings.json", "./.claude", "./CLAUDE.md",
                  "./tests", "./pyproject.toml", "./uv.lock", "./conftest.py", "./reviews", "./feedback.md", "./.git/hooks", "./.git/config"]
  }
}
json.dump(cfg, open("srt-settings.json", "w"), indent=2)
print("wrote srt-settings.json with read access to:", allow)
PY
echo
echo "Next: run 'claude setup-token', copy the token it prints, then:"
echo "  export CLAUDE_CODE_OAUTH_TOKEN=<token>     (or export ANTHROPIC_API_KEY=<key>)"
echo "  ./smoke.sh"
