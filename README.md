# Animation loop kit 
## (Claude Code + Manim, unattended, confined to one folder)

This is just a project to create animations of Andrej Karpaty's lecture nn-zero-to-hero, and more speciphically on the firt lecture on 'micrograd' and the video 'The spelled-out intro to neural networks and backpropagation: building micrograd
'.

Builder agent writes scenes, objective checks gate them, an independent read-only reviewer agent
looks at rendered frames, and a bash loop you own decides when it is finished. Nothing the agents
can edit decides when the loop stops.

## What is and is not guaranteed
- Confinement: the WHOLE Claude Code process (file tools, shell, scripts it writes) runs inside the
  OS sandbox `srt`: writes only in this folder (plus /tmp), reads of /Users blocked except this folder
  and the toolchain, network only to Anthropic. `smoke.sh` proves this on your machine before any loop.
- Not guaranteed: srt is a beta research preview; allowed network hosts can in principle leak data
  (domain fronting); the API token is inside the boundary. Do not put secrets in this folder.
- Not automatable: whether it looks as good as 3Blue1Brown. The reviewer catches layout defects;
  you review the final MP4s.

## One-time setup (macOS)
    brew install uv ffmpeg jq ripgrep node
    npm install -g @anthropic-ai/sandbox-runtime
    cd micrograd-animation
    unzip -o ~/Downloads/animation-loop-kit.zip -d .     # copies files into the project
    uv add --dev pytest
    # add to pyproject.toml:   [tool.pytest.ini_options]  pythonpath = ["src"]
    cat CLAUDE.md.template >> CLAUDE.md                  # keep your existing rules too
    chmod +x *.sh
    ./setup.sh                                           # checks tools, writes srt-settings.json
    claude setup-token                                   # copy the token it prints
    export CLAUDE_CODE_OAUTH_TOKEN=<token>               # or: export ANTHROPIC_API_KEY=<key>
    ./smoke.sh                                           # MUST print SMOKE TEST PASSED

If smoke.sh reports `Operation not permitted`, watch what was blocked:
    log stream --predicate 'process == "sandbox-exec"' --style syslog
and add ONLY the needed read path to `allowRead` in srt-settings.json (agents cannot edit that file).
Also confirm the vision check printed the text from the test frame, and that the final PERMISSION CHECK PASSED.
Why flags and not settings: in headless `claude -p`, allow rules in a project's .claude/settings.json are ignored
unless the folder was trusted interactively, so the rules live in agent.sh as CLI flags (agents cannot edit it).

## Before the first loop
1. Get PLAN.md approved: edit the rows (scene, file, class, duration range, what it must show).
2. Put reference material (e.g. Karpathy's notebooks) in reference/ yourself. The loop has no network.
3. Commit everything: `git add -A && git commit -m "kit"`.

## Run
    MAX_ITER=4 TOTAL_BUDGET=8 ./loop.sh        # pilot: should finish scene 1 and stop at the cap
    MAX_ITER=30 TOTAL_BUDGET=55 ./loop.sh      # real run, after you have seen the pilot cost and quality
Keep the Mac awake and plugged in: `caffeinate -i ./loop.sh`.
After the pilot, measure real cost per iteration: `jq -s 'map(.total_cost_usd) | add/length' logs/iter-*.json`
Stop at any time: `touch STOP` (checked before every iteration). Everything is committed per
iteration, so `git log` / `git diff` show what happened; logs are in logs/ (loop.log, iter-N.json).

Exit codes: 0 done and verified, 1 iteration cap, 3 STOP file, 4 budget, 5 builder failing, 6 stalled, 7 PLAN.md tampered,
8 usage limit did not lift in time.

## Running on a subscription (5-hour and weekly limits)
`claude -p` currently draws from your subscription limits (Anthropic paused the planned separate credit; check the
help center before a long run). The loop shares one pool with your chat and interactive Claude Code, so run it
overnight and expect to be locked out of Claude while it works.
When the limit is hit the loop does NOT quit: it probes every 10 minutes with a one-turn "ping" session and resumes
as soon as that succeeds. A limit wait does not use up an iteration, budget or failure count; state lives in files and git.
It gives up after 7 hours (exit 8), which is what a weekly limit looks like; re-run `./loop.sh` later and it resumes.
Detection does not depend on the message text (its format in headless mode is not documented): any failed builder run
is followed by a probe, and a failing probe means "limited". Knobs: WAIT_POLL (600 s), WAIT_MAX_SECS (25200),
MAX_LIMIT_WAITS (8).
If you enabled extra usage / usage credits on your plan, past-the-limit work is billed at API rates; turn that off or
cap it if you want a hard stop.

## Knobs (environment variables)
MAX_ITER, TOTAL_BUDGET (USD, client-side estimate), STALL_LIMIT, FAIL_LIMIT, CLAUDE_MODEL (default sonnet),
FAIL_SLEEP (seconds to wait after a failed run, default 300), BUILDER_TURNS/BUILDER_BUDGET, REVIEWER_TURNS/REVIEWER_BUDGET. SANDBOX_OFF=1 disables srt (testing only).

## Files agents cannot change (enforced by srt denyWrite AND permission deny rules)
loop.sh verify.sh review.sh agent.sh sandboxed.sh hash.sh setup.sh smoke.sh prompts/ srt-settings.json .claude/
CLAUDE.md tests/ pyproject.toml uv.lock conftest.py reviews/ feedback.md
PLAN.md may only be changed by ticking boxes: any other edit stops the loop (exit 7).
