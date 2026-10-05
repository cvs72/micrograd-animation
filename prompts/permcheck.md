This is a permissions self-test. Do the numbered steps in order, each with the exact tool named.
After all steps, use the Write tool to create .smoke/perm_report.txt containing exactly one line per step,
formatted "N: ALLOWED" or "N: DENIED" depending on whether that tool call was permitted.
Do not retry a denied step and do not try workarounds.
1. Bash tool: uv run manim --version
2. Bash tool: ffprobe -version
3. Bash tool: mkdir -p .smoke/permdir
4. Bash tool: uv run python -c "print(1)"
5. Bash tool: curl -sS -m 5 https://example.com   (expected to be denied)
6. Edit tool: append the text "x" to the file prompts/canary.txt   (expected to be denied)
7. Bash tool: git commit --allow-empty -m test   (expected to be denied)
