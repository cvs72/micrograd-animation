#!/usr/bin/env bash
# usage: ./sandboxed.sh ./agent.sh builder|reviewer|ping|visionping|permcheck
# Permission rules are passed as CLI flags on purpose: in `claude -p`, allow rules from a project's
# .claude/settings.json are ignored unless the folder was trusted interactively, and we also use a
# private CLAUDE_CONFIG_DIR (so no trust record exists). CLI flags always apply, and agents cannot edit this file.
set -eu
cd "$(dirname "$0")"
role="${1:?role}"
mkdir -p .claude-home .uv-cache .cache .tmp .texmf-var
export CLAUDE_CONFIG_DIR="$PWD/.claude-home"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export UV_OFFLINE=1 UV_FROZEN=1 UV_CACHE_DIR="$PWD/.uv-cache" XDG_CACHE_HOME="$PWD/.cache"
export TMPDIR="$PWD/.tmp" TEXMFVAR="$PWD/.texmf-var" TEXMFCONFIG="$PWD/.texmf-var"
model="${CLAUDE_MODEL:-sonnet}"
ALLOW="Read,Edit,Write,Bash(uv run manim *),Bash(uv run pytest *),Bash(uv run python *),Bash(ffmpeg *),Bash(ffprobe *),Bash(mkdir *),Bash(ls *),Bash(git status),Bash(git status *),Bash(git log *),Bash(git diff),Bash(git diff *)"
DENY="Edit(./loop.sh),Edit(./verify.sh),Edit(./review.sh),Edit(./agent.sh),Edit(./sandboxed.sh),Edit(./hash.sh),Edit(./setup.sh),Edit(./smoke.sh),Edit(./prompts/**),Edit(./srt-settings.json),Edit(./CLAUDE.md),Edit(./tests/**),Edit(./pyproject.toml),Edit(./uv.lock),Edit(./conftest.py),Edit(./reviews/**),Edit(./feedback.md),Bash(curl *),Bash(wget *),Bash(git push *),Bash(git commit *),Bash(sudo *)"
case "$role" in
  builder)
    exec claude -p --model "$model" --permission-mode dontAsk \
      --allowedTools "$ALLOW" --disallowedTools "$DENY" \
      --max-turns "${BUILDER_TURNS:-40}" --max-budget-usd "${BUILDER_BUDGET:-3}" \
      --output-format json < prompts/builder.md ;;
  reviewer)
    exec claude -p --model "$model" --permission-mode dontAsk --tools "Read" --allowedTools "Read" \
      --max-turns "${REVIEWER_TURNS:-30}" --max-budget-usd "${REVIEWER_BUDGET:-1}" \
      --output-format json --json-schema "$(cat prompts/review.schema.json)" < prompts/reviewer.md ;;
  ping)
    printf 'Reply with exactly: OK' | exec claude -p --model "$model" --permission-mode dontAsk --tools "" \
      --max-turns 1 --max-budget-usd 0.25 --output-format json ;;
  visionping)
    printf 'Use the Read tool on .smoke/f.png. Reply with only the text you can read in that image.' | exec claude -p --model "$model" \
      --permission-mode dontAsk --tools "Read" --allowedTools "Read" --max-turns 4 --max-budget-usd 0.25 --output-format json ;;
  permcheck)
    exec claude -p --model "$model" --permission-mode dontAsk --allowedTools "$ALLOW" --disallowedTools "$DENY" \
      --max-turns 14 --max-budget-usd 0.50 --output-format json < prompts/permcheck.md ;;
  *) echo "unknown role $role" >&2; exit 2 ;;
esac
