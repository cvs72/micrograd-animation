#!/usr/bin/env bash
# Fingerprint of a scene = its file + all shared code (src/**/*.py and scenes/_*.py). Any shared-code change invalidates earlier reviews.
cd "$(dirname "$0")" || exit 1
cat "$1" $(find src -name '*.py' | sort) $(ls scenes/_*.py 2>/dev/null) 2>/dev/null | shasum -a 256 | awk '{print $1}'
