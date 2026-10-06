import numpy as np
from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, fmt, recap_line,
    code_panel, title_card, working_line,
)
from micrograd_animation.engine import Value

config.background_color = BLACK

MID = np.array([3.8, 0.0, 0])
TOPR = np.array([3.8, 2.3, 0])
QPOS = np.array([3.8, 1.3, 0])
H = 0.001


def f(x):
    """The notebook's function; works on floats and on Value objects."""
    return 3 * x**2 - 4 * x + 5


def g3(x):
    return x**3 - 3 * x


def F(x):
    return f(Value(x)).data


def G(x):
    return g3(Value(x)).data


def ABS(x):
    v = Value(x)
    return (v.relu() + (-v).relu()).data


def exact(fn, x):
    """Exact slope from the engine's backward pass."""
    v = Value(x)
    fn(v).backward()
    return v.grad


def fd(fn, x, h):
    return (fn(x + h) - fn(x)) / h


def sci(x):
    m, e = f"{x:.1e}".split("e")
    return rf"{m}\times 10^{{{int(e)}}}"


# numbers the plan asks us to assert (G9)
XS = np.arange(-5, 5, 0.25)
assert F(3.0) == 20.0 and len(XS) == 40
S3, SM3, S23 = fd(F, 3.0, H), fd(F, -3.0, H), fd(F, 2 / 3, H)
assert round(S3, 4) == 14.0030 and round(SM3, 4) == -21.9970 and round(S23, 4) == 0.0030
assert round(exact(f, 3.0), 4) == 14.0 and round(exact(f, -3.0), 4) == -22.0
assert fd(lambda x: f(x), 3.0, 1e-16) == 0.0
assert round(fd(F, 3.0, 1.0), 4) == 17.0
FORWARD = {k: abs(fd(lambda x: f(x), 3.0, 10.0**-k) - 14.0) for k in range(1, 17)}
CENTRAL = {k: abs((f(3.0 + 10.0**-k) - f(3.0 - 10.0**-k)) / (2 * 10.0**-k) - 14.0) for k in range(1, 17)}
assert 2.9e-4 < FORWARD[4] < 3.1e-4 and 3.0e-11 < CENTRAL[4] < 5.0e-11


def slope_color(s):
    t = min(1.0, abs(s) / 3.0)
    return interpolate_color(WHITE, ORANGE if s < 0 else TEAL, t)


def make_axes(xr, yr, w, h, xl, yl, nfs=24):
    ax = Axes(x_range=xr, y_range=yr, x_length=w, y_length=h, tips=False,
              axis_config={"include_numbers": True, "font_size": nfs, "color": GREY_B,
                           "decimal_number_config": {"num_decimal_places": 0}})
    labs = VGroup(MathTex(xl, font_size=34).next_to(ax.x_axis, RIGHT, buff=0.15),
                  MathTex(yl, font_size=34).next_to(ax.y_axis, UP, buff=0.15))
    return ax, labs


def zero_tick(ax):
    return MathTex("0", font_size=24, color=GREY_B).next_to(ax.c2p(0, 0), DL, buff=0.08)


def make_probe(axes, fn, xt, ht, reach):
    """Dot on the curve, secant through (x, f(x)) and (x+h, f(x+h)), rise-over-run corner."""
    def slope():
        x, h = xt.get_value(), ht.get_value()
        return (fn(x + h) - fn(x)) / h

    dot = always_redraw(lambda: Dot(axes.c2p(xt.get_value(), fn(xt.get_value())), radius=0.09,
                                    color=ACTIVE))

    def sec():
        x, s = xt.get_value(), slope()
        w = min(reach[0], reach[1] / max(abs(s), 1e-9))
        y = fn(x)
        return Line(axes.c2p(x - w, y - s * w), axes.c2p(x + w, y + s * w), color=ACTIVE,
                    stroke_width=4)

    def tri():
        x, h = xt.get_value(), ht.get_value()
        y, y2 = fn(x), fn(x + h)
        a, c, b = axes.c2p(x, y), axes.c2p(x + h, y), axes.c2p(x + h, y2)
        return VGroup(Line(a, c, color=WHITE, stroke_width=5), Line(c, b, color=GRAD, stroke_width=5),
                      Dot(b, radius=0.06, color=WHITE))

    return dot, always_redraw(sec), always_redraw(tri), slope


def make_readout(slope_fn, pos, label=r"\text{slope}="):
    lab = MathTex(label, font_size=44).move_to(pos)
    num = DecimalNumber(0, num_decimal_places=4, font_size=44)

    def upd(m):
        s = slope_fn()
        m.set_value(s)
        m.set_color(slope_color(s))
        m.next_to(lab, RIGHT, buff=0.15)

    num.add_updater(upd)
    upd(num)
    return lab, num


def table_rows(rows, header, xs=(-1.95, -0.65, 0.65, 2.0)):
    """Small table of MathTex cells; columns at fixed offsets so rows can be added one by one."""
    head = VGroup(*[MathTex(h, font_size=30, color=GREY_B).move_to([x, 0, 0]) for h, x in zip(header, xs)])
    out = [head]
    for i, r in enumerate(rows):
        row = VGroup(*[MathTex(c, font_size=30, color=col).move_to([x, -0.5 * (i + 1), 0])
                       for (c, col), x in zip(r, xs)])
        out.append(row)
    return out, xs


class Scene01Derivative(MovingCameraScene):
    # ---- small helpers -------------------------------------------------
    def zoom_on(self, target, factor, hold):
        frame = self.camera.frame
        cap = self.nar.current
        base_w = cap.width

        def follow(m):
            k = frame.width / config.frame_width
            m.set_width(base_w * k)
            m.move_to(frame.get_bottom() + UP * (m.height / 2 + 0.2 * k))

        cap.add_updater(follow)
        self.play(frame.animate.scale(factor).move_to(target), run_time=0.9)
        self.wait(hold)
        self.play(frame.animate.scale(1 / factor).move_to(ORIGIN), run_time=0.9)
        cap.remove_updater(follow)
        follow(cap)

    def ask(self, tex, pos=QPOS, color=YELLOW, pulses=3):
        q = MathTex(tex, font_size=36, color=color).move_to(pos)
        if q.width > 5.4:
            q.scale_to_fit_width(5.4)
        self.add(q)
        for _ in range(pulses):
            self.play(Indicate(q, scale_factor=1.15, color=color), run_time=1.0)
        return q

    def define(self, title, body, hold=3.3):
        c = callout(title, body, width=5.4).move_to(MID)
        self.play(FadeIn(c), run_time=0.3)
        self.wait(hold)
        self.play(FadeOut(c), run_time=0.4)

    def open_act(self, text, hold=3.0):
        self.act_label = text
        old = getattr(self, "act_tag", None)
        if old is not None:
            self.play(FadeOut(old), run_time=0.3)
            self.act_tag = None
        banner = act_banner(self, text, keep=True)
        if hold:
            self.wait(hold)
        return banner

    def close_act(self, banner):
        old = getattr(self, "act_tag", None)
        label = self.act_label
        tag = Tex(r"\textbf{" + label.split(":")[0] + ":}", font_size=36, color=YELLOW)
        tag.to_corner(UL, buff=0.5)
        anims = [FadeOut(banner), FadeIn(tag)]
        if old is not None:
            anims.append(FadeOut(old))
        self.play(*anims, run_time=0.6)
        self.act_tag = tag

    def retarget(self, cur, ax2, labs2, graph2, morph=True, pre=()):
        """Swap axes and labels with a short cross-fade, then morph the curve itself.
        `pre` are extra mobjects faded in the same step (no empty frames in between)."""
        extra = [] if morph else [FadeOut(cur[2])]
        self.play(FadeOut(cur[0]), FadeOut(cur[1]), *extra, *[FadeOut(m) for m in pre], run_time=0.2)
        self.remove(cur[0], cur[1], *pre, *([cur[2]] if not morph else []))
        if morph:
            self.play(FadeIn(ax2), FadeIn(labs2), run_time=0.3)
            self.play(Transform(cur[2], graph2), run_time=2.0)
        else:
            self.play(FadeIn(ax2), FadeIn(labs2), Create(graph2), run_time=0.6)
            return VGroup(ax2, labs2, graph2)
        self.wait(0.5)
        return VGroup(ax2, labs2, cur[2])

    def was_line(self, tex=r"\text{Example A: } f'(3)=14.0030"):
        t = MathTex(tex, font_size=32, color=GREY_B).move_to([3.8, 3.0, 0])
        self.play(FadeIn(t), run_time=0.5)
        return t

    def wipe(self, *mobs):
        mobs = [m for m in mobs if m is not None]
        self.play(*[FadeOut(m) for m in mobs], run_time=0.4)
        self.remove(*mobs)

    # ---- the scene -----------------------------------------------------
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S01")
        title_card(self, "Chapter 1", "What is a derivative, really?")
        keep = self.act_a(nar)
        self.act_b(nar, keep)
        self.act_c(nar)
        nar.finish()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        recap_line(self, "Next: what if there is more than one input?", color=ACTIVE)

    # ---- ACT A ---------------------------------------------------------
    def act_a(self, nar):
        nar.say("Example A: the lecture's own function, a parabola we can plot.")
        banner = self.open_act("Example A: the lecture's own function")
        ax, labs = make_axes([-5, 5, 1], [0, 100, 20], 7.0, 3.7,"x", "f(x)")
        ax.to_edge(LEFT, buff=0.9).shift(UP * 0.0)
        labs[0].next_to(ax.x_axis, RIGHT, buff=0.15)
        labs[1].next_to(ax.y_axis, UP, buff=0.15)
        labs.add(zero_tick(ax))
        self.play(Create(ax), FadeIn(labs), run_time=1.5)
        self.close_act(banner)
        nar.say("Forty x values from -5 up in steps of 0.25, each with its f(x).")
        dots = VGroup(*[Dot(ax.c2p(x, F(x)), radius=0.055, color=DATA) for x in XS])
        self.play(LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.05), run_time=2.0)
        self.wait(1.5)
        graph = ax.plot(F, x_range=[-5, 5], color=DATA, stroke_width=5)
        self.play(Create(graph), run_time=1.5)
        self.play(FadeOut(dots), run_time=0.4)

        nar.say("Slope tells how steeply the curve climbs when we step right.")
        self.define("Slope", "rise over run")

        xt, ht = ValueTracker(3.0), ValueTracker(1.0)
        dot, sec, tri, slope = make_probe(ax, F, xt, ht, (1.3, 16.0))
        nar.say("Pick x = 3. First, plain arithmetic: what is f(3)?")
        self.play(FadeIn(dot), run_time=0.6)
        w = working_line(self, r"f(x)=3x^{2}-4x+5",
                         r"f(3)=3\cdot 3^{2}-4\cdot 3+5",
                         rf"f(3)=27-12+5={fmt(F(3.0))}", pos=MID, width=5.6)
        self.wipe(w)

        nar.say("Predict: if x moves a bit right of 3, is f above or below 20?")
        q = self.ask(r"f(3+h)\ \text{above or below}\ 20\,?")
        lab, num = make_readout(slope, TOPR + LEFT * 0.9)
        nar.say("Above: the curve climbs. White is the step h, orange the rise.")
        ans = MathTex(rf"f(3+{fmt(1.0)})={fmt(F(4.0))}>{fmt(F(3.0))}", font_size=36, color=FWD).move_to(QPOS)
        hl = MathTex(r"h=", font_size=36, color=GREY_B).move_to(TOPR + LEFT * 1.55 + DOWN * 0.5)
        hn = DecimalNumber(0, num_decimal_places=3, font_size=36, color=WHITE)
        hn.add_updater(lambda m: m.set_value(ht.get_value()).next_to(hl, RIGHT, buff=0.15))
        hn.update()
        self.play(ReplacementTransform(q, ans), FadeIn(sec), FadeIn(tri), FadeIn(lab), FadeIn(num),
                  FadeIn(hl), FadeIn(hn), run_time=1.0)
        self.wait(1.0)
        self.play(ht.animate.set_value(0.5), run_time=1.0)
        nar.say("Zoom in: a line through two curve points is a secant.")
        self.zoom_on(ax.c2p(3.25, F(3.0) + 5) + DOWN * 0.9, 0.3, 2.2)
        self.define("Secant", "line through two points")
        self.play(FadeOut(ans), run_time=0.3)

        nar.say("Now shrink h. The secant turns into the tangent, which only touches.")
        tang_len = 1.3
        tangent = Line(ax.c2p(3 - tang_len, 20 - 14 * tang_len), ax.c2p(3 + tang_len, 20 + 14 * tang_len),
                       color=GREEN, stroke_width=8, stroke_opacity=0.9)
        self.play(FadeIn(tangent), run_time=0.5)
        for hv, rt in ((0.5, 0.4), (0.1, 0.5), (0.01, 0.5), (H, 0.5)):
            self.play(ht.animate.set_value(hv), run_time=rt)
            self.wait(0.5 if hv != H else 0.2)
        self.define("Tangent", "line that just touches")

        nar.say("Slope is rise over run; the run from x to x+h is just h.")
        d1 = MathTex(r"\text{slope}=\frac{\text{rise}}{\text{run}}", font_size=40)
        d2 = MathTex(r"\text{slope}=\frac{f(x+h)-f(x)}{(x+h)-x}", font_size=40)
        d3 = MathTex(r"\text{slope}=\frac{f(x+h)-f(x)}{h}", font_size=40)
        d4 = MathTex(r"\text{slope}=\frac{f(3+h)-f(3)}{h}", font_size=40)
        for d in (d1, d2, d3, d4):
            if d.width > 5.6:
                d.scale_to_fit_width(5.6)
            d.move_to(MID)
        self.play(FadeIn(d1), run_time=0.6)
        self.wait(1.0)
        self.play(TransformMatchingTex(d1, d2), run_time=1.2)
        self.wait(1.2)
        self.play(TransformMatchingTex(d2, d3), run_time=1.2)
        self.wait(1.2)
        self.play(TransformMatchingTex(d3, d4), run_time=1.2)
        self.wait(1.0)
        self.wipe(d4)
        nar.say("Real numbers in the formula: nudge by h = 0.001 and divide by h.")
        f3h = F(3.0 + H)
        w = working_line(self, r"\frac{f(x+h)-f(x)}{h}",
                         rf"\frac{{f(3.001)-f(3)}}{{0.001}}=\frac{{{fmt(f3h)}-{fmt(F(3.0))}}}{{0.001}}",
                         rf"\frac{{{fmt(f3h)}-{fmt(F(3.0))}}}{{0.001}}={fmt(S3)}", pos=np.array([4.2, 0.0, 0]), width=4.8,
                         hold=3.0)
        self.wait(1.5)
        self.wipe(w)

        # table, filled one row at a time
        rows_data = [("3", F(3.0), F(3.0 + H), S3), ("-3", F(-3.0), F(-3.0 + H), SM3),
                     ("0.6667", F(2 / 3), F(2 / 3 + H), S23)]

        def cells(x, y0, y1, s):
            return [(x, WHITE), (fmt(y0), DATA), (fmt(y1), DATA), (fmt(s), slope_color(s))]

        trs, _ = table_rows([cells(*r) for r in rows_data], [r"x", r"f(x)", r"f(x+h)", r"\text{slope}"])
        table = VGroup(*trs).move_to([3.8, -0.45, 0])
        # keep the layout of an empty row set: place full table first, then reveal rows
        self.play(FadeIn(trs[0]), run_time=0.5)
        self.play(FadeIn(trs[1]), run_time=0.8)
        self.wait(1.0)

        nar.say("Predict: at x = -3, will the slope be positive or negative?")
        q = self.ask(r"\text{slope at } x=-3:\ +\ \text{or}\ -\,?", pulses=4)
        nar.say("Sliding left, the readout passes white at the bottom, then turns orange.")
        ans = MathTex(rf"\text{{slope}}={fmt(SM3)}<0", font_size=36, color=ORANGE).move_to(QPOS)
        self.play(xt.animate.set_value(-3.0), FadeOut(tangent), ReplacementTransform(q, ans),
                  FadeIn(trs[2]), run_time=1.5)
        self.wait(2.5)
        self.play(FadeOut(ans), run_time=0.3)

        nar.say("Sliding right, the slope shrinks toward 0 near the bottom.")
        self.play(xt.animate.set_value(2 / 3), run_time=3.0)
        self.play(FadeIn(trs[3]), run_time=0.3)
        nar.say("Near x = 2/3 the tangent is flat: slope about 0, nudges do nothing.")
        self.play(Indicate(num, color=WHITE), run_time=1.2)
        fl = MathTex(r"f'(x)=6x-4=0\ \Rightarrow\ x=\tfrac{2}{3}", font_size=36, color=WHITE).move_to(QPOS)
        self.play(FadeIn(fl), run_time=0.5)
        self.wait(3.0)
        self.wipe(table, fl)
        self.play(FadeOut(dot), FadeOut(sec), FadeOut(tri), FadeOut(lab), FadeOut(num), FadeOut(tangent),
                  FadeOut(hl), FadeOut(hn), run_time=0.5)
        self.remove(dot, sec, tri, lab, num, hl, hn)

        nar.say("Warning: too many zeros in h and floats run out of digits.")
        hs_w = [1e-4, 1e-8, 1e-12, 1e-16]
        rows_w = [[(sci(h), WHITE), (fmt(fd(f, 3.0, h)), slope_color(1.0)), (fmt(fd(f, 3.0, h) - 14.0), GRAD)]
                  for h in hs_w]
        trs_w, _ = table_rows(rows_w, [r"h", r"\text{slope}", r"\text{error}"],
                              xs=(-1.9, 0.1, 1.6))
        tbl_w = VGroup(*trs_w).move_to([3.8, 1.7, 0])
        for r in trs_w:
            self.play(FadeIn(r), run_time=0.6)
        self.wait(2.5)
        tiny = 1e-16
        w = working_line(self, r"\frac{f(3+h)-f(3)}{h}",
                         rf"\frac{{f(3+10^{{-16}})-f(3)}}{{10^{{-16}}}}=\frac{{{fmt(f(3.0 + tiny))}-{fmt(F(3.0))}}}{{10^{{-16}}}}",
                         rf"\frac{{{fmt(f(3.0 + tiny))}-{fmt(F(3.0))}}}{{10^{{-16}}}}={fmt(fd(f, 3.0, tiny))}\neq {fmt(exact(f, 3.0))}",
                         pos=np.array([4.2, -0.5, 0]), width=4.8, hold=3.0)
        self.wipe(w, tbl_w)
        nar.say("So the derivative is the slope at one point: rise over run, h tiny.")
        self.define("Derivative", "slope at one point")
        return [ax, labs, graph, dot, sec, tri, lab, num, trs[0], trs[1], trs[2], trs[3], xt, ht]

    # ---- ACT B ---------------------------------------------------------
    def act_b(self, nar, keep):
        ax, labs, graph, dot, sec, tri, lab, num = keep[:8]
        nar.say("Example B: what if we change the function? A cubic, then a kink.")
        self.play(FadeOut(dot), FadeOut(sec), FadeOut(tri), FadeOut(lab), FadeOut(num), run_time=0.6)
        self.remove(dot, sec, tri, lab, num)
        banner = self.open_act("Example B: what if the function changes?")

        # B1: morph f into g(x) = x^3 - 3x
        ax2, labs2 = make_axes([-3, 3, 1], [-4, 4, 2], 7.0, 3.7,"x", "g(x)")
        ax2.move_to(ax.get_center())
        labs2[0].next_to(ax2.x_axis, RIGHT, buff=0.15)
        labs2[1].next_to(ax2.y_axis, UP, buff=0.15)
        labs2.add(zero_tick(ax2))
        graph2 = ax2.plot(G, x_range=[-2.15, 2.15], color=DATA, stroke_width=5)
        nar.say("Same idea, new curve g of x: it has a hump and a valley.")
        cur = self.retarget(VGroup(ax, labs, graph), ax2, labs2, graph2)
        ax, labs, graph = cur
        self.close_act(banner)
        was = self.was_line()
        xt, ht = ValueTracker(-2.0), ValueTracker(H)
        dot, sec, tri, slope = make_probe(ax2, G, xt, ht, (1.0, 0.8))
        lab, num = make_readout(slope, TOPR + LEFT * 0.9)
        xlab = MathTex("x=", font_size=34, color=GREY_B)
        xnum = DecimalNumber(0, num_decimal_places=1, font_size=34, color=WHITE)

        def follow_x(m):
            xnum.set_value(xt.get_value())
            xlab.move_to(ax2.c2p(-2.5, 3.2))
            xnum.next_to(xlab, RIGHT, buff=0.08)

        xnum.add_updater(follow_x)
        follow_x(xnum)
        self.play(FadeIn(dot), FadeIn(sec), FadeIn(lab), FadeIn(num), FadeIn(xlab), FadeIn(xnum),
                  run_time=0.3)
        self.wait(1.0)
        nar.say("Predict: where on this curve is the tangent perfectly flat?")
        q = self.ask(r"\text{Where is the slope } 0\,?", pos=np.array([3.8, 1.2, 0]), color=WHITE)
        self.play(FadeOut(q), xt.animate.set_value(-1.0), run_time=1.5)
        nar.say("The slope reads about 0 at x = -1 (hump top) and x = 1 (valley).")
        flat1 = Line(ax2.c2p(-1.7, G(-1.0)), ax2.c2p(-0.5, G(-1.0)), color=GREEN, stroke_width=8)
        flat2 = Line(ax2.c2p(0.5, G(1.0)), ax2.c2p(1.7, G(1.0)), color=GREEN, stroke_width=8)
        self.play(Create(flat1), run_time=0.6)
        e1 = MathTex(rf"g'(-1)=3\cdot(-1)^{{2}}-3={fmt(exact(g3, -1.0))}", font_size=36,
                     color=WHITE).move_to([3.8, 1.6, 0])
        assert exact(g3, -1.0) == 0.0 and exact(g3, 1.0) == 0.0
        m1 = Dot(ax2.c2p(-1, G(-1.0)), radius=0.12, color=TEAL)
        m2 = Dot(ax2.c2p(1, G(1.0)), radius=0.12, color=TEAL)
        self.play(FadeIn(e1), FadeIn(m1), run_time=0.3)
        self.play(Indicate(m1, scale_factor=2.0, color=TEAL), run_time=1.0)
        self.wait(1.0)
        e2 = MathTex(rf"g'(1)=3\cdot 1^{{2}}-3={fmt(exact(g3, 1.0))}", font_size=36,
                     color=WHITE).move_to([3.8, 1.0, 0])
        self.play(xt.animate.set_value(1.0), FadeIn(m2), run_time=2.0)
        self.play(FadeIn(e2), run_time=0.3)
        self.play(Create(flat2), run_time=0.6)
        self.play(Indicate(m2, scale_factor=2.0, color=TEAL), run_time=1.0)
        xs_t = [-2.0, -1.0, 0.0, 1.0]
        gs = [(exact(g3, x), G(x)) for x in xs_t]
        rows = [[(fmt(x), WHITE), (fmt(gv), DATA), (fmt(G(x + H)), DATA), (fmt(fd(G, x, H)), slope_color(sv))]
                for x, (sv, gv) in zip(xs_t, gs)]
        trs, _ = table_rows(rows, [r"x", r"g(x)", r"g(x+h)", r"\text{slope}"])
        tbl = VGroup(*trs).move_to([3.8, -1.2, 0])
        self.play(FadeIn(trs[0]), run_time=0.4)
        nar.say("The table shows slope 0 only at x = -1 and 1; elsewhere it is 9 or -3.")
        for r in trs[1:]:
            self.play(FadeIn(r), run_time=0.6)
        self.wait(4.0)
        nar.say("Now the absolute value: a V with a sharp corner at x = 0.")
        xnum.clear_updaters()
        pre_b2 = [xlab, xnum, e1, e2, dot, sec, lab, num, tri, tbl, m1, m2, flat1, flat2]

        # B2: abs(x) has a kink at 0
        ax3, labs3 = make_axes([-3, 3, 1], [0, 3, 1], 7.0, 3.7,"x", r"|x|")
        ax3.move_to(ax.get_center())
        labs3[0].next_to(ax3.x_axis, RIGHT, buff=0.15)
        labs3[1].next_to(ax3.y_axis, UP, buff=0.15)
        labs3.add(zero_tick(ax3))
        graph3 = ax3.plot(ABS, x_range=[-3, 3], color=DATA, stroke_width=5, use_smoothing=False)
        ax, labs, graph = self.retarget(VGroup(ax, labs, graph), ax3, labs3, graph3, morph=False,
                                          pre=pre_b2)
        code = code_panel("def my_abs(x):\n    return x.relu() + (-x).relu()", font_size=28)
        code.scale_to_fit_width(5.6)
        code.move_to([3.8, -1.0, 0])
        code.highlight = SurroundingRectangle(code.code_lines[1], color=ACTIVE, buff=0.0, stroke_width=2)
        ht2 = ValueTracker(1.0)

        def sec_left():
            h = ht2.get_value()
            return Line(ax3.c2p(-1.5 * h, ABS(-1.5 * h)), ax3.c2p(0, 0), color=ORANGE, stroke_width=5)

        def sec_right():
            h = ht2.get_value()
            return Line(ax3.c2p(0, 0), ax3.c2p(1.5 * h, ABS(1.5 * h)), color=TEAL, stroke_width=5)

        def legs():
            h = ht2.get_value()
            return VGroup(
                Line(ax3.c2p(-h, 0), ax3.c2p(-h, h), color=ORANGE, stroke_width=5),
                Line(ax3.c2p(h, 0), ax3.c2p(h, h), color=TEAL, stroke_width=5),
                Dot(ax3.c2p(-h, h), radius=0.08, color=ORANGE), Dot(ax3.c2p(0, 0), radius=0.08, color=ACTIVE),
                Dot(ax3.c2p(h, h), radius=0.08, color=TEAL))

        sl, sr = always_redraw(sec_left), always_redraw(sec_right)
        lg = always_redraw(legs)
        self.play(Create(sl), Create(sr), FadeIn(lg), FadeIn(code), FadeIn(code.highlight), run_time=1.0)
        nar.say("Predict: what single slope does the corner have at x = 0?")
        q = self.ask(r"\text{Slope at } x=0\,?")
        h0 = ht2.get_value()
        left_val = (ABS(0) - ABS(-h0)) / h0
        right_val = (ABS(h0) - ABS(0)) / h0
        assert left_val == -1.0 and right_val == 1.0
        nar.say("Two answers: from the left the secant gives -1, from the right +1.")
        ml = MathTex(rf"\frac{{|0|-|-1|}}{{1}}={fmt(left_val)}", font_size=40, color=ORANGE).move_to([3.8, 2.1, 0])
        mr = MathTex(rf"\frac{{|1|-|0|}}{{1}}={fmt(right_val)}", font_size=40, color=TEAL).move_to([3.8, 0.9, 0])
        self.play(FadeOut(q), FadeIn(ml), Indicate(sl, color=ORANGE), run_time=1.2)
        self.play(FadeIn(mr), Indicate(sr, color=TEAL), run_time=1.2)
        nar.say("Shrink h: the secants never agree, so no derivative exists at 0.")
        self.play(ht2.animate.set_value(0.4), run_time=1.5)
        self.play(Indicate(ml), Indicate(mr), run_time=1.2)
        nod = MathTex(r"-1\neq +1:\ \text{no derivative at } 0", font_size=36, color=RED).move_to([3.8, 0.0, 0])
        self.play(FadeIn(nod), run_time=0.4)
        self.wait(3.5)
        pre_b3 = [sl, sr, lg, ml, mr, code, code.highlight, nod]

        # B3: h too big
        ax4, labs4 = make_axes([-5, 5, 1], [0, 100, 20], 7.0, 3.7,"x", "f(x)")
        ax4.move_to(ax.get_center())
        labs4[0].next_to(ax4.x_axis, RIGHT, buff=0.15)
        labs4[1].next_to(ax4.y_axis, UP, buff=0.15)
        labs4.add(zero_tick(ax4))
        graph4 = ax4.plot(F, x_range=[-5, 5], color=DATA, stroke_width=5)
        self.add(was)
        ax, labs, graph = self.retarget(VGroup(ax, labs, graph), ax4, labs4, graph4, morph=False,
                                        pre=pre_b3)
        nar.say("Back to f. If h is far too big, the secant leaves the tangent.")
        xt3, ht3 = ValueTracker(3.0), ValueTracker(H)
        dot, sec, tri, slope = make_probe(ax4, F, xt3, ht3, (1.3, 16.0))
        tangent = Line(ax4.c2p(3 - 1.3, 20 - 14 * 1.3), ax4.c2p(3 + 1.3, 20 + 14 * 1.3), color=GREEN,
                       stroke_width=8, stroke_opacity=0.9)
        lab, num = make_readout(slope, TOPR + LEFT * 0.9)
        self.play(FadeIn(tangent), FadeIn(dot), FadeIn(sec), FadeIn(tri), FadeIn(lab), FadeIn(num),
                  run_time=0.8)
        self.play(ht3.animate.set_value(1.0), run_time=1.2)
        self.wait(2.0)
        nar.say("With h = 1 the slope reads 17, not 14: the step is too coarse.")
        self.remove(was)
        w = working_line(self, r"\frac{f(3+h)-f(3)}{h}",
                         rf"\frac{{f(4)-f(3)}}{{1}}=\frac{{{fmt(F(4.0))}-{fmt(F(3.0))}}}{{1}}",
                         rf"={fmt(fd(F, 3.0, 1.0))}\neq 14", pos=np.array([3.8, 1.0, 0]), width=5.6, hold=3.0)
        hs = [1.0, 0.1, 0.001]
        rows = [[(fmt(h), WHITE), (fmt(F(3.0 + h)), DATA), (fmt(fd(F, 3.0, h)), slope_color(1.0)),
                 (fmt(fd(F, 3.0, h) - 14.0), GRAD)] for h in hs]
        trs, _ = table_rows(rows, [r"h", r"f(3+h)", r"\text{slope}", r"\text{error}"])
        tbl = VGroup(*trs).move_to([3.8, -0.7, 0])
        self.play(FadeIn(trs[0]), run_time=0.4)
        for r in trs[1:]:
            self.play(FadeIn(r), run_time=0.7)
        self.wait(3.5)
        self.wipe(w, dot, sec, tri, lab, num, tangent, tbl)
        self.bkeep = VGroup(ax, labs, graph)

    # ---- ACT C ---------------------------------------------------------
    def act_c(self, nar):
        old_tag = getattr(self, "act_tag", None)
        self.act_tag = None
        outs = [FadeOut(m) for m in self.bkeep]
        if old_tag is not None:
            outs.append(FadeOut(old_tag))
        ks = list(range(1, 17))
        ly = lambda d: [float(np.log10(d[k])) for k in ks]
        ax = Axes(x_range=[0, 16, 4], y_range=[-14, 2, 2], x_length=7.0, y_length=3.7, tips=False,
                  axis_config={"include_numbers": True, "font_size": 24, "color": GREY_B,
                               "decimal_number_config": {"num_decimal_places": 0}})
        ax.to_edge(LEFT, buff=0.9).shift(UP * 0.0)
        ax.shift(UP * 0.55)
        ax.x_axis.move_to(ax.c2p(8, -14))  # axis along the bottom, not through y = 0
        xl = MathTex(r"k\ \ (h=10^{-k})", font_size=30).next_to(ax.x_axis, DOWN, buff=0.3)
        yl = MathTex(r"\log_{10}|\text{error}|", font_size=30).next_to(ax.y_axis, UP, buff=0.15)
        zero = MathTex("0", font_size=24, color=GREY_B).next_to(ax.c2p(0, -14), DOWN, buff=0.1)
        zero_y = MathTex("0", font_size=24, color=GREY_B).next_to(ax.c2p(0, 0), LEFT, buff=0.12)
        zero_y.shift(RIGHT * 0.0)
        self.play(*outs, Create(ax), FadeIn(xl), FadeIn(yl), FadeIn(zero), FadeIn(zero_y), run_time=0.8)
        self.remove(*self.bkeep)
        nar.say("Expert corner: how good is this nudge, and can we do better?")
        banner = self.open_act("Expert corner: the size of h", hold=1.0)
        self.close_act(banner)
        leg1 = MathTex(r"\frac{f(x+h)-f(x)}{h}", font_size=34, color=DATA).move_to([3.9, 2.8, 0])
        leg2 = MathTex(r"\frac{f(x+h)-f(x-h)}{2h}", font_size=34, color=FWD).move_to([3.9, 1.7, 0])
        sw1 = Line(ORIGIN, RIGHT * 0.5, color=DATA, stroke_width=6).next_to(leg1, LEFT, buff=0.2)
        sw2 = Line(ORIGIN, RIGHT * 0.5, color=FWD, stroke_width=6).next_to(leg2, LEFT, buff=0.2)
        t1 = Text("forward", font_size=26, color=DATA).next_to(leg1, DOWN, buff=0.1)
        t2 = Text("central", font_size=26, color=FWD).next_to(leg2, DOWN, buff=0.1)
        self.play(FadeIn(leg1), FadeIn(t1), FadeIn(sw1), FadeIn(leg2), FadeIn(t2), FadeIn(sw2), run_time=0.8)
        nar.say("We measure the error against the true slope 14, for h = 10^-k.")
        fw = ax.plot_line_graph(ks, ly(FORWARD), line_color=DATA, add_vertex_dots=True,
                                vertex_dot_radius=0.05, stroke_width=4)
        ce = ax.plot_line_graph(ks, ly(CENTRAL), line_color=FWD, add_vertex_dots=True,
                                vertex_dot_radius=0.05, stroke_width=4)
        nar.say("Predict: at h = 0.0001, which formula lands closer to 14?")
        q = self.ask(r"\text{Closer to 14 at } h=10^{-4}\,?", pos=np.array([4.0, -0.2, 0]), color=WHITE)
        nar.say("Blue forward step looks only right; teal central looks both sides.")
        self.play(FadeOut(q), Create(fw), run_time=0.4)
        self.play(Create(ce), run_time=0.4)
        nar.say("At k = 4 the forward error is about 3e-4, the central one about 4e-11.")
        mark = DashedLine(ax.c2p(4, -14), ax.c2p(4, 2), color=ACTIVE, stroke_width=3, stroke_opacity=0.6)
        w = MathTex(rf"h=10^{{-4}}:\ {sci(FORWARD[4])}\ \text{{vs}}\ {sci(CENTRAL[4])}", font_size=38, color=WHITE)
        w.scale_to_fit_width(4.6)
        w.move_to([4.3, 0.6, 0])
        mk = MathTex(r"k=4", font_size=30, color=ACTIVE).next_to(ax.c2p(4, 2), RIGHT, buff=0.1)
        self.add(w, mk)
        self.play(Create(mark), run_time=1.0)
        win = MathTex(rf"\text{{Answer: central, }}\text{{about }}10^{{{round(float(np.log10(FORWARD[4] / CENTRAL[4])))}}}\times\ \text{{closer}}",
                      font_size=34, color=ACTIVE).move_to([4.3, 0.05, 0])
        win.scale_to_fit_width(4.3)
        self.play(FadeIn(win), Indicate(w), run_time=1.0)
        self.wait(1.0)
        nar.say("So micrograd never nudges: each operation knows its exact slope.")
        c = callout("No h at all", "exact local derivatives", color=ACTIVE, width=4.6).move_to([4.2, -0.6, 0])
        self.play(FadeOut(win), FadeIn(c), run_time=0.5)
        self.wait(2.0)
        nar.say("In code, central costs one more call of f but is far more exact.")
        cp = code_panel("fwd = (f(x+h) - f(x)) / h\ncen = (f(x+h) - f(x-h)) / (2*h)", font_size=24)
        cp.scale_to_fit_width(4.6)
        cp.move_to([4.3, -1.8, 0])
        hl = SurroundingRectangle(cp.code_lines[1], color=ACTIVE, buff=0.05)
        self.play(FadeIn(cp), run_time=0.6)
        self.play(Create(hl), run_time=0.8)
        self.wait(3.0)
        nar.say("Errors shrink to k = 8, then rounding noise wins.")
        noise = MathTex(r"\text{rounding noise, } k>8", font_size=34, color=WHITE).move_to(ax.c2p(11.5, -10.5))
        self.play(FadeOut(xl), FadeIn(noise), run_time=0.3)
        self.zoom_on(ax.c2p(10, -6) + DOWN * 1.0, 0.45, 2.0)
        self.play(FadeIn(xl), run_time=0.3)
        nar.say("At k = 16 both slopes read 0, so the error is the full 14.")
        out = MathTex(rf"h=10^{{-16}}:\ \text{{slope}}={fmt(fd(f, 3.0, 1e-16))}", font_size=38,
                      color=WHITE).move_to([4.3, -2.45, 0])
        out.scale_to_fit_width(4.4)
        assert (f(3.0 + 1e-16) - f(3.0 - 1e-16)) / 2e-16 == 0.0
        err16 = abs(fd(f, 3.0, 1e-16) - 14.0)
        assert err16 == 14.0
        e16 = MathTex(rf"k=16:\ \text{{error}}={fmt(err16)}", font_size=30, color=WHITE)
        e16.next_to(ax.c2p(16, 2), UP, buff=0.12).shift(LEFT * 1.0)
        self.add(out, e16)
        self.play(Indicate(fw["vertex_dots"][-1], scale_factor=2.5),
                  Indicate(ce["vertex_dots"][-1], scale_factor=2.5),
                  run_time=1.5)
        self.wait(1.6)
