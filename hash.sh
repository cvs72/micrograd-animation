#!/usr/bin/env bash
# Fingerprint of a scene = its file plus the shared engine (a changed engine invalidates earlier reviews).
cd "$(dirname "$0")" || exit 1
cat "$1" src/*/engine.py 2>/dev/null | shasum -a 256 | awk '{print $1}'
