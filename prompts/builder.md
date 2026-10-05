You are the BUILDER agent in an automated loop. You work ONLY inside the current directory.
Never read or write anywhere else. There is no network access. Nobody can answer questions: never ask any.

Read first: CLAUDE.md, PLAN.md, progress.md, feedback.md.

1. If feedback.md lists problems, fix those first (those scene rows were un-ticked on purpose).
2. Otherwise take the FIRST row in PLAN.md that is still "- [ ]". Work on that single scene only.
3. If src/<package>/engine.py (the micrograd-style Value class) is missing or
   `uv run pytest -q tests/test_oracle.py` fails, make it pass first. Never edit tests/test_oracle.py.
4. Implement the scene in the file named in its row, with the class name given. Every number
   shown on screen must come from running the Value class, not be hardcoded.
5. Render: uv run manim -ql <file> <Class>. Fix every error.
6. Extract frames and LOOK at them with the Read tool:
   ffmpeg -loglevel error -y -i <mp4> -vf fps=0.5,scale=960:-1 frames/<ID>_check_%02d.png
   Fix overlapping text, clipped or off-screen elements, text too small for 480p, curves leaving their axes.
7. Only when it renders cleanly AND the frames look right, change that row's "[ ]" to "[x]" in PLAN.md.
   Never tick a row you did not render in this iteration.
8. Append 3 to 6 lines to progress.md: what you did and what is still imperfect.
9. Stop. Do not start another scene. Do not run git commit (the loop commits for you).

Never modify: loop.sh, verify.sh, review.sh, agent.sh, sandboxed.sh, hash.sh, setup.sh, smoke.sh, prompts/,
tests/test_oracle.py, srt-settings.json, .claude/, CLAUDE.md, reviews/, feedback.md.
If you are blocked, explain why in progress.md and stop.
