#!/usr/bin/env bash
# Runs any command inside the OS sandbox (srt). Everything that executes agent-written code
# or the agent itself MUST go through this script.
cd "$(dirname "$0")" || exit 1
if [ -n "${SANDBOX_OFF:-}" ]; then exec "$@"; fi
exec srt --settings "$PWD/srt-settings.json" "$@"
