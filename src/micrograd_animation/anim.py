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


# ---- mini drawings for the recap (S13)

def _dots(n, w, color=WHITE, r=0.07):
    return VGroup(*[Dot(radius=r, color=color) for _ in range(n)]).arrange(RIGHT, buff=w)


def chapter_icon(k, size=1.4):
    """Small drawing for chapter k (1..12) in a rounded box, plus a function that returns
    its 2 second mini animation (call it after the icon is on screen)."""
    box = RoundedRectangle(corner_radius=0.12, width=size, height=size, stroke_color=GREY_B,
                           stroke_width=2)
    s = size * 0.36
    if k in (1, 5, 11):  # curve with a sliding dot
        xs = np.linspace(-1, 1, 30)
        if k == 1:
            f = lambda x: x * x
        elif k == 5:
            f = lambda x: np.tanh(2.5 * x) * 0.9
        else:
            f = lambda x: 0.9 * np.exp(-1.6 * (x + 1))
        pts = [np.array([x * s, (f(x) - 0.35) * s, 0]) for x in xs]
        curve = VMobject(color=DATA, stroke_width=3).set_points_smoothly(pts)
        dot = Dot(pts[0], radius=0.07, color=ACTIVE)
        art = VGroup(curve, dot)
        anim = lambda: [MoveAlongPath(dot, curve, run_time=1.8)]
    elif k == 2:  # three slopes as bars
        hs = [-0.9, 0.6, 0.3]
        bars = VGroup(*[Rectangle(width=0.2, height=0.02, fill_color=c, fill_opacity=1, stroke_width=0)
                        for c in (ORANGE, TEAL, TEAL)]).arrange(RIGHT, buff=0.2)
        for b, h in zip(bars, hs):
            b.target_h = abs(h) * size * 0.45
        line = Line(LEFT * s, RIGHT * s, color=GREY_B, stroke_width=2)
        art = VGroup(line, bars)
        bars.move_to(line.get_center())
        for b, h in zip(bars, hs):
            b.move_to(line.get_center() + np.array([b.get_x() - line.get_center()[0], 0, 0]))
        def anim():
            outs = []
            for b, h in zip(bars, hs):
                new = Rectangle(width=0.2, height=b.target_h, fill_color=b.get_fill_color(),
                                fill_opacity=1, stroke_width=0)
                new.move_to([b.get_x(), line.get_y() + (1 if h > 0 else -1) * b.target_h / 2, 0])
                outs.append(Transform(b, new, run_time=1.6))
            return outs
    elif k in (3, 4):  # tiny graph with a pulse
        a, b, e = (Dot(p * s, radius=0.09, color=WHITE) for p in
                   (np.array([-1, 0.6, 0]), np.array([-1, -0.6, 0]), np.array([0, 0, 0])))
        d = Dot(np.array([1, 0, 0]) * s, radius=0.09, color=WHITE)
        ar = VGroup(Line(a.get_center(), e.get_center()), Line(b.get_center(), e.get_center()),
                    Line(e.get_center(), d.get_center())).set_color(GREY_B).set_stroke(width=2)
        path = Line(a.get_center(), e.get_center()).append_points(
            Line(e.get_center(), d.get_center()).points)
        path.set_opacity(0)
        if k == 3:
            pulse = Dot(a.get_center(), radius=0.08, color=FWD)
            anim = lambda: [MoveAlongPath(pulse, path, run_time=1.8)]
        else:
            pulse = Dot(d.get_center(), radius=0.08, color=BWD)
            anim = lambda: [MoveAlongPath(pulse, path.copy().reverse_points(), run_time=1.8)]
        art = VGroup(ar, a, b, e, d, path, pulse)
    elif k == 6:  # topological order, nodes light up
        sq = VGroup(*[Square(0.2, stroke_color=WHITE, stroke_width=2) for _ in range(5)]
                    ).arrange(RIGHT, buff=0.08)
        art = sq
        anim = lambda: [LaggedStart(*[sq[i].animate.set_fill(YELLOW, 1) for i in range(5)],
                                    lag_ratio=0.5, run_time=1.8)]
    elif k == 7:  # gradients add up
        parts = VGroup(*[Rectangle(width=0.35, height=0.35, fill_color=c, fill_opacity=0.9,
                                   stroke_width=0) for c in (ORANGE, ORANGE)]).arrange(RIGHT, buff=0.1)
        plus = MathTex("+", font_size=36, color=WHITE)
        art = VGroup(parts[0], plus, parts[1]).arrange(RIGHT, buff=0.1)
        anim = lambda: [Indicate(parts[0], color=YELLOW), Indicate(parts[1], color=YELLOW)]
    elif k == 8:  # more operations
        t1 = MathTex(r"e^x", font_size=34, color=TEAL)
        t2 = MathTex(r"x^k", font_size=34, color=DATA)
        art = VGroup(t1, t2).arrange(RIGHT, buff=0.25)
        anim = lambda: [Indicate(t1, color=YELLOW, run_time=0.9), Indicate(t2, color=YELLOW, run_time=0.9)]
    elif k == 9:  # tensor grid
        grid = VGroup(*[Square(0.22, stroke_color=WHITE, stroke_width=1.5) for _ in range(9)]
                      ).arrange_in_grid(3, 3, buff=0.04)
        art = grid
        anim = lambda: [LaggedStart(*[sq.animate.set_fill(TEAL, 0.9) for sq in grid],
                                    lag_ratio=0.1, run_time=1.8)]
    elif k == 10:  # tiny network with a pulse
        cols = []
        for x, n in zip((-1, 0, 1), (3, 4, 1)):
            cols.append([np.array([x * s, (n - 1) / 2 * 0.28 * size / 1.4 - i * 0.28 * size / 1.4, 0])
                         for i in range(n)])
        edges = VGroup(*[Line(p, q, stroke_width=1, color=GREY_B)
                         for c0, c1 in zip(cols[:-1], cols[1:]) for p in c0 for q in c1])
        nodes = VGroup(*[Dot(p, radius=0.06, color=WHITE) for c in cols for p in c])
        art = VGroup(edges, nodes)
        anim = lambda: [LaggedStart(*[Indicate(nodes[i], color=ACTIVE, scale_factor=1.8)
                                      for i in range(len(nodes))], lag_ratio=0.2, run_time=1.8)]
    else:  # k == 12, a bowl with a ball spiralling in
        rings = VGroup(*[Ellipse(width=r * s * 2, height=r * s * 1.2, stroke_color=BLUE,
                                 stroke_width=2) for r in (1.0, 0.65, 0.3)])
        pts = [np.array([np.cos(t) * r * s, np.sin(t) * r * s * 0.6, 0])
               for t, r in zip(np.linspace(0, 5, 30), np.linspace(1.0, 0.05, 30))]
        path = VMobject().set_points_smoothly(pts).set_opacity(0)
        dot = Dot(pts[0], radius=0.07, color=ACTIVE)
        art = VGroup(rings, path, dot)
        anim = lambda: [MoveAlongPath(dot, path, run_time=1.8)]
    art.move_to(box)
    icon = VGroup(box, art)
    icon.box, icon.art = box, art
    return icon, anim
