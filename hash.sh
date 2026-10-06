#!/usr/bin/env bash
# Fingerprint of a scene = its file + the numeric engine (engine.py, nn.py). anim.py is append-only by rule, so adding helpers must not re-open scenes that already passed.
cd "$(dirname "$0")" || exit 1
cat "$1" $(find src \( -name engine.py -o -name nn.py \) | sort) 2>/dev/null | shasum -a 256 | awk '{print $1}'
