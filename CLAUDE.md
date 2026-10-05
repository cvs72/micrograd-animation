# Manim animation project

- Library: Manim Community Edition (`from manim import *`), NOT ManimGL (no ShowCreation, use Create).
- Run with `uv run manim -pql scene.py <SceneClass>`. Add dependencies only with `uv add`.
- LaTeX is installed: use `MathTex` for derivative and equation notation (e.g. ∂d/∂a), and `Text` for node labels.
- Always run the scene after editing it, read the traceback, and fix errors before reporting back.
- Keep one file `scene.py`, with small helper functions (e.g. `make_node`) instead of repeated code.
- 16:9, dark background, font sizes readable at 480p, no text overlapping.
# Manim animation project (autonomous loop)

- Library: Manim Community Edition (`from manim import *`), NOT ManimGL (no ShowCreation, use Create).
- Python via uv only: `uv run manim -ql <file> <Class>`, `uv run pytest -q tests/test_oracle.py`. No installs: the sandbox has no package network.
- LaTeX is installed: use `MathTex` for derivative and chain-rule notation, `Text` for node labels.
- One scene per file in `scenes/`, class names as given in PLAN.md. The shared micrograd-style `Value` class lives in `src/<package>/engine.py`; scenes take their numbers from running it.
- Style: black background, 3Blue1Brown-like palette (BLUE, YELLOW, TEAL, RED), real `Axes` plots, `ValueTracker` + `always_redraw` for sliding things, `Transform`/`Indicate` instead of things simply appearing. 16:9, readable at 480p, nothing overlapping or off screen.
- Keep each command simple: one command per tool call, no pipes, no `&&`, no `cd`.
- You work only inside this directory. No network. Never touch the control files listed in prompts/builder.md.
- If reference/ exists, read it for the math and the order of ideas; never copy its text.
