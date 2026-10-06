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


# ---- helpers added in the three-act rework (append-only from here on)

def act_banner(scene, text, color=ACTIVE, hold=2.6, keep=False, pos=None):
    """Act banner, font 36, held at least 2.5 s. keep=True leaves it on screen and returns it.
    pos: centre point; default is the top edge."""
    t = Text(text, font_size=36, color=color, weight=BOLD)
    if t.width > 12.5:
        t.scale_to_fit_width(12.5)
    box = RoundedRectangle(corner_radius=0.15, width=t.width + 0.6, height=t.height + 0.4,
                           stroke_color=color, stroke_width=3, fill_color=BLACK, fill_opacity=0.8)
    banner = VGroup(box, t)
    t.move_to(box)
    if pos is None:
        banner.to_edge(UP, buff=0.5)
    else:
        banner.move_to(pos)
    scene.play(FadeIn(banner, shift=DOWN * 0.3), run_time=0.5)
    if keep:
        return banner
    scene.wait(max(hold, 2.5))
    scene.play(FadeOut(banner), run_time=0.5)
    return banner


def working_line(scene, symbolic, substituted, result, pos=ORIGIN, width=6.2, hold=2.0,
                 colors=(WHITE, DATA, GRAD)):
    """Animated arithmetic: formula -> real numbers substituted -> result (all MathTex)."""
    stages = [MathTex(s, font_size=40, color=c) for s, c in zip((symbolic, substituted, result), colors)]
    for s in stages:
        if s.width > width:
            s.scale_to_fit_width(width)
        s.move_to(pos)
    scene.play(FadeIn(stages[0]), run_time=0.6)
    scene.wait(0.8)
    scene.play(TransformMatchingTex(stages[0], stages[1]), run_time=1.0)
    scene.wait(hold)
    scene.play(TransformMatchingTex(stages[1], stages[2]), run_time=1.0)
    scene.wait(hold)
    return stages[2]


def particle_flow(path, magnitude, color=GRAD, n=3, reverse=False, run_time=2.0):
    """Dots travelling along `path`; dot size grows with |magnitude|. Returns an animation."""
    r = 0.05 + 0.03 * min(abs(magnitude), 4.0)
    p = path.copy().reverse_points() if reverse else path
    dots = [Dot(p.get_start(), radius=r, color=color) for _ in range(n)]
    anim = AnimationGroup(
        *[MoveAlongPath(d, p, run_time=run_time, rate_func=linear) for d in dots],
        lag_ratio=0.3,
    )
    anim.dots = VGroup(*dots)  # remove these after playing
    return anim


def callout(title, body, color=ACTIVE, width=6.0):
    """Boxed definition: a coloured title and one line of body text (hold it >= 3 s)."""
    t = Text(title, font_size=28, color=color, weight=BOLD)
    b = Text(body, font_size=28, color=WHITE)
    g = VGroup(t, b).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
    if g.width > width:
        g.scale_to_fit_width(width)
    box = RoundedRectangle(corner_radius=0.15, width=g.width + 0.5, height=g.height + 0.4,
                           stroke_color=color, stroke_width=3, fill_color=BLACK, fill_opacity=0.9)
    g.move_to(box)
    return VGroup(box, g)


class CrossfadeNarrator(Narrator):
    """Narrator whose swaps cross-fade in 0.2 s (old and new together) and then idle,
    so the total time per swap is unchanged but a caption is rarely caught half faded."""

    SWAP = 0.2

    def say(self, text):
        scene = self.scene
        if self.current is not None:
            left = self.min_hold - (self._now() - self.start)
            if left > 0:
                scene.wait(left)
            self.cues[-1][1] = self._now()
        cap = self._make(text)
        scene.add_foreground_mobject(cap)
        old = self.current
        anims = [FadeIn(cap)] + ([FadeOut(old)] if old is not None else [])
        scene.play(*anims, run_time=self.SWAP)
        if old is not None:
            scene.remove_foreground_mobject(old)
        scene.wait(2 * self.FADE - self.SWAP)
        self.current = cap
        self.start = self._now()
        self.min_hold = max(2.5, 0.35 * len(text.split()))
        self.cues.append([self.start, None, text])
