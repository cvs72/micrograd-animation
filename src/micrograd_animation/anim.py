"""Shared helpers for every scene. Append-only: never change existing behaviour."""
import os
import textwrap

from manim import *

# palette (G4)
BG = BLACK
DATA = BLUE
GRAD = ORANGE
FWD = TEAL
BWD = ORANGE
ACTIVE = YELLOW
SECOND = GREY_B

CAPTION_DIR = "captions"


def fmt(x):
    """One number format: 4 decimals, fewer when the value is exact."""
    r = round(float(x), 4)
    if r == int(r):
        return str(int(r)) if abs(r) >= 1 or r == 0 else f"{r:.1f}"
    return f"{r:.4f}".rstrip("0")


def _srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class Narrator:
    """Bottom-centre captions on a translucent box; writes captions/<ID>.srt."""

    FADE = 0.3

    def __init__(self, scene, scene_id):
        self.scene = scene
        self.scene_id = scene_id
        self.cues = []  # [start, end, text]
        self.current = None
        self.start = 0.0
        self.min_hold = 0.0

    def _now(self):
        return self.scene.renderer.time

    def _make(self, text):
        lines = textwrap.wrap(text, 38)
        assert len(lines) <= 2, f"caption too long: {text}"
        txt = VGroup(*[Text(l, font_size=30, color=WHITE) for l in lines]).arrange(DOWN, buff=0.1)
        box = Rectangle(
            width=txt.width + 0.6, height=txt.height + 0.3,
            fill_color=BLACK, fill_opacity=0.7, stroke_width=0,
        )
        cap = VGroup(box, txt)
        txt.move_to(box)
        cap.to_edge(DOWN, buff=0.2)
        return cap

    def say(self, text):
        """Swap in a new caption; waits first so the old one stays >= 2.5 s."""
        scene = self.scene
        if self.current is not None:
            left = self.min_hold - (self._now() - self.start)
            if left > 0:
                scene.wait(left)
            self.cues[-1][1] = self._now()
            scene.play(FadeOut(self.current), run_time=self.FADE)
        cap = self._make(text)
        scene.add_foreground_mobject(cap)
        scene.play(FadeIn(cap), run_time=self.FADE)
        self.current = cap
        self.start = self._now()
        self.min_hold = max(2.5, 0.35 * len(text.split()))
        self.cues.append([self.start, None, text])

    def play(self, *anims, **kw):
        self.scene.play(*anims, **kw)

    def clear(self):
        """Fade the caption out (honouring its minimum time) without ending."""
        if self.current is None:
            return
        left = self.min_hold - (self._now() - self.start)
        if left > 0:
            self.scene.wait(left)
        self.cues[-1][1] = self._now()
        self.scene.play(FadeOut(self.current), run_time=self.FADE)
        self.scene.remove_foreground_mobject(self.current)
        self.current = None

    def finish(self):
        self.clear()
        os.makedirs(CAPTION_DIR, exist_ok=True)
        with open(os.path.join(CAPTION_DIR, f"{self.scene_id}.srt"), "w") as f:
            for i, (a, b, t) in enumerate(self.cues, 1):
                f.write(f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{t}\n\n")


def make_value_node(name, data, grad=0.0, width=2.8):
    """Rounded rectangle with name, data = x, grad = y (always the same look)."""
    n = Text(name, font_size=26, color=WHITE, weight=BOLD)
    d = Text(f"data = {fmt(data)}", font_size=26, color=DATA)
    g = Text(f"grad = {fmt(grad)}", font_size=26, color=GRAD)
    body = VGroup(n, d, g).arrange(DOWN, buff=0.12)
    box = RoundedRectangle(
        corner_radius=0.15, width=max(width, body.width + 0.3), height=body.height + 0.3,
        stroke_color=WHITE, stroke_width=2,
    )
    body.move_to(box)
    node = VGroup(box, body)
    node.box, node.name_t, node.data_t, node.grad_t = box, n, d, g
    return node


def arrow_between(a, b, color=FWD, buff=0.1, **kw):
    """Arrow from the edge of a to the edge of b (a, b: Mobjects)."""
    d = b.get_center() - a.get_center()
    d = d / np.linalg.norm(d)
    return Arrow(a.get_critical_point(d), b.get_critical_point(-d), color=color, buff=buff,
                 stroke_width=4, max_tip_length_to_length_ratio=0.15, **kw)


def title_card(scene, chapter, question):
    """3 second card: chapter number and a one-line question."""
    ch = Text(chapter, font_size=36, color=ACTIVE)
    q = Text(question, font_size=36, color=WHITE)
    if q.width > 12.5:
        q.scale_to_fit_width(12.5)
    card = VGroup(ch, q).arrange(DOWN, buff=0.4)
    scene.play(FadeIn(card), run_time=0.5)
    scene.wait(2.0)
    scene.play(FadeOut(card), run_time=0.5)


def recap_line(scene, text, color=WHITE):
    """4 second closing line (no captions)."""
    t = Text(text, font_size=34, color=color)
    if t.width > 12.5:
        t.scale_to_fit_width(12.5)
    scene.play(FadeIn(t), run_time=0.5)
    scene.wait(3.0)
    scene.play(FadeOut(t), run_time=0.5)


def code_panel(code, language="python", highlight=None, font_size=24):
    """Code mobject; `highlight` is a list of 1-based line numbers to mark YELLOW."""
    c = Code(code_string=code, language=language, formatter_style="monokai",
             background="rectangle", add_line_numbers=True,
             paragraph_config={"font_size": font_size})
    if highlight:
        c.highlight = VGroup(*[
            SurroundingRectangle(c.code_lines[i - 1], color=ACTIVE, buff=0.05)
            for i in highlight
        ])
    return c
