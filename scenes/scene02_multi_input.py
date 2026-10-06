from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, arrow_between, callout,
    fmt, make_value_node, particle_flow, recap_line, title_card,
)
from micrograd_animation.engine import Value

H = 0.0001  # the notebook's nudge
CASES = {
    "A": (2.0, -3.0, 10.0),
    "B1": (-1.0, 4.0, 0.5),
    "B2": (-1.0, 0.0, 0.5),
    "B3": (0.0, 0.0, 0.5),
}
POS = {
    "a": np.array([-5.4, 2.0, 0]), "b": np.array([-5.4, 0.0, 0]),
    "e": np.array([-2.0, 1.0, 0]), "c": np.array([-2.0, -1.6, 0]),
    "d": np.array([1.2, -0.3, 0]),
}
EDGES = [("a", "e"), ("b", "e"), ("e", "d"), ("c", "d")]
ROUTE = {"a": [("a", "e"), ("e", "d")], "b": [("b", "e"), ("e", "d")], "c": [("c", "d")]}
BX = {"a": 3.3, "b": 4.55, "c": 5.8}
Y0 = -0.6  # zero line of the sensitivity bars
BAR_SCALE = 0.33
LIGHT = BLUE_B  # readable data colour on black
TEAL_L = TEAL_B


def calc(av, bv, cv):
    """Forward and backward pass of d = a*b + c with the Value class."""
    a, b, c = Value(av), Value(bv), Value(cv)
    e = a * b
    d = e + c
    d.backward()
    return dict(a=av, b=bv, c=cv, e=e.data, d=d.data,
                ga=a.grad, gb=b.grad, gc=c.grad, ge=e.grad, gd=d.grad)


def fd(k, vals):
    """Finite-difference slope: nudge input k by H and divide the change in d by H."""
    new = dict(vals)
    new[k] += H
    return (calc(new["a"], new["b"], new["c"])["d"] - calc(vals["a"], vals["b"], vals["c"])["d"]) / H


def vals_of(case):
    return dict(zip("abc", CASES[case]))


def p(x):
    return f"({fmt(x)})" if x < 0 else fmt(x)


def node_mob(name, st, grads=True):
    g = st["g" + name] if grads else 0.0
    return make_value_node(name, st[name], g).scale(0.95).move_to(POS[name])


def bar_rect(v, x):
    h = max(abs(v) * BAR_SCALE, 0.02)
    r = Rectangle(width=0.7, height=h, fill_color=TEAL, fill_opacity=0.9, stroke_width=0)
    r.move_to([x, Y0 + (h / 2 if v >= 0 else -h / 2), 0])
    return r


def slope_label(k, v):
    t = MathTex(rf"\frac{{\partial d}}{{\partial {k}}}={fmt(round(v, 2))}", font_size=26, color=TEAL_L)
    return t.move_to([BX[k], -2.05, 0])


def table_row(st, y):
    xs = [2.5, 3.1, 3.7, 4.3, 5.0, 5.6, 6.2]
    vals = [st["a"], st["b"], st["c"], st["d"], st["ga"], st["gb"], st["gc"]]
    cols = [LIGHT] * 3 + [YELLOW] + [TEAL_L] * 3
    return VGroup(*[MathTex(fmt(v), font_size=26, color=c).move_to([x, y, 0])
                    for v, c, x in zip(vals, cols, xs)])


def fd_working(k, vals):
    """Three stages of the finite-difference working with the real numbers substituted."""
    a, b, c = vals["a"], vals["b"], vals["c"]
    d0 = calc(a, b, c)["d"]
    d1 = calc(a + H if k == "a" else a, b + H if k == "b" else b, c + H if k == "c" else c)["d"]
    sym = {"a": r"\frac{(a+h)\,b+c-d}{h}", "b": r"\frac{a\,(b+h)+c-d}{h}",
           "c": r"\frac{a\,b+(c+h)-d}{h}"}[k]
    aa = p(a + H) if k == "a" else p(a)
    bb = p(b + H) if k == "b" else p(b)
    cc = fmt(c + H) if k == "c" else fmt(c)
    sub = rf"\frac{{{aa}{bb}+{cc}-{p(d0)}}}{{{fmt(H)}}}"
    res = rf"\frac{{{fmt(round(d1 - d0, 6))}}}{{{fmt(H)}}}={(d1 - d0) / H:.4f}"
    return sym, sub, res


class FixedNarrator(CrossfadeNarrator):
    """Captions that stay flat on screen even while the 3D camera moves."""

    def _make(self, text):
        cap = super()._make(text)
        self.scene.add_fixed_in_frame_mobjects(cap)
        return cap


class Scene02MultiInput(ThreeDScene):
    # ---------------------------------------------------------------- helpers
    def fix(self, *mobs):
        self.add_fixed_in_frame_mobjects(*mobs)
        return mobs[0] if len(mobs) == 1 else mobs

    def pulse_question(self, text, pos, qpos, n=3):
        """Predict-then-reveal: question plus a pulsing question mark, held about 3 s."""
        q = Text(text, font_size=30, color=WHITE, line_spacing=0.8).move_to(pos)
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to(qpos)
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        return VGroup(q, qm)

    def live_state(self):
        return calc(self.ta.get_value(), self.tb.get_value(), self.tc.get_value())

    def setup_static(self):
        st = calc(*CASES["A"])
        self.nodes = {k: node_mob(k, st, grads=False) for k in "abced"}
        self.arrows = {(s, t): arrow_between(self.nodes[s], self.nodes[t], color=FWD)
                       for s, t in EDGES}

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = FixedNarrator(self, "S02")
        title_card(self, "Chapter 2", "What if there is more than one input?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        recap_line(self, "Next: how do we store this graph in code?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        base = vals_of("A")
        st0 = calc(*CASES["A"])
        assert st0["d"] == 4.0
        nar.say("Example A: the lecture's own function, d = a times b plus c.")
        act_banner(self, "Example A: the lecture's numbers", hold=2.6)

        title = MathTex(r"d=a\cdot b+c", font_size=48).move_to([-4.6, 3.35, 0])
        self.setup_static()
        n = self.nodes
        nar.say("Three inputs feed one output. Which input matters, and which way?")
        self.play(Write(title))
        self.play(LaggedStart(*[FadeIn(n[k]) for k in "abc"], lag_ratio=0.3), run_time=1.5)
        nar.say("Each box is a Value. Times gives e = a*b, then plus c gives d.")
        self.play(FadeIn(n["e"]), Create(self.arrows[("a", "e")]), Create(self.arrows[("b", "e")]))
        self.play(FadeIn(n["d"]), Create(self.arrows[("e", "d")]), Create(self.arrows[("c", "d")]))
        for s, t in (("a", "e"), ("e", "d")):
            fl = particle_flow(self.arrows[(s, t)], 1, color=FWD, n=3, run_time=1.0)
            self.add(fl.dots)
            self.play(fl)
            self.remove(fl.dots)
        self.wait(1.0)

        nar.say("A partial derivative: nudge ONE input and hold the others still.")
        co = callout("Partial derivative", "nudge ONE input,\nhold the rest fixed", width=4.1)
        co.move_to([4.7, 2.2, 0])
        self.play(FadeIn(co))
        self.wait(3.2)
        self.play(FadeOut(co))

        # zero line and flat bars
        zero = Line([2.9, Y0, 0], [6.7, Y0, 0], color=GREY_B, stroke_width=2)
        self.bars = {k: bar_rect(0.0, BX[k]) for k in "abc"}
        self.labels = {}
        htag = MathTex(rf"h={fmt(H)}", font_size=40, color=ACTIVE).move_to([0.2, 3.35, 0])
        self.play(Create(zero), FadeIn(htag), *[FadeIn(b) for b in self.bars.values()])

        # nudge a (predict first)
        nar.say("b is negative, so a bigger a adds less. Does d rise or fall?")
        q = self.pulse_question("Nudge a up.\nDoes d go UP or DOWN?", [4.8, 2.6, 0], [4.8, 1.3, 0])
        self.play(Indicate(n["b"], color=ACTIVE), run_time=1.2)
        self.play(FadeOut(q))
        nar.say("Nudge a by h = 0.0001 and watch the change travel along the arrows to d.")
        self.nudge("a", base, nar)
        # nudge b
        nar.say("Now b. Since a is positive, a bigger b pushes d up. The slope is 2.")
        self.nudge("b", base, nar)
        # nudge c (predict first)
        nar.say("Last, c. What slope do you expect? It is simply added to the product.")
        q = self.pulse_question("Nudge c up.\nWhat will the\nslope be?", [4.8, 2.5, 0], [4.8, 0.9, 0])
        self.play(FadeOut(q))
        nar.say("c just adds on, so d rises exactly as c does: the slope is 1.")
        self.nudge("c", base, nar)

        nar.say("Three slopes: -3, 2 and 1. The slope for a is b; the slope for b is a.")
        lines = VGroup(
            MathTex(rf"\frac{{\partial d}}{{\partial a}}=b={fmt(st0['gb'] * 0 + base['b'])}", font_size=38, color=TEAL_L),
            MathTex(rf"\frac{{\partial d}}{{\partial b}}=a={fmt(base['a'])}", font_size=38, color=TEAL_L),
            MathTex(rf"\frac{{\partial d}}{{\partial c}}={fmt(st0['gc'])}", font_size=38, color=TEAL_L),
        ).arrange(DOWN, buff=0.25).move_to([4.8, 2.0, 0])
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.2) for l in lines], lag_ratio=0.4), run_time=2.0)
        self.play(*[Indicate(self.bars[k], color=ACTIVE) for k in "abc"])
        self.wait(1.5)
        nar.say("The engine's backward pass writes these same slopes into grad.")
        full = calc(*CASES["A"])
        self.play(*[Transform(n[k], node_mob(k, full, grads=True)) for k in "abced"], run_time=1.5)
        self.play(Indicate(n["a"].grad_t, color=BWD), Indicate(n["b"].grad_t, color=BWD),
                  Indicate(n["c"].grad_t, color=BWD))
        self.wait(2.0)
        self.act_a_mobs = Group(title, htag, zero, lines, *n.values(), *self.arrows.values(),
                                *self.bars.values(), *self.labels.values())
        self.act_a_lines = lines
        self.act_a_title = title
        self.act_a_htag = htag

    def nudge(self, k, base, nar):
        n = self.nodes
        st0 = calc(base["a"], base["b"], base["c"])
        new = dict(base)
        new[k] += H
        st1 = calc(new["a"], new["b"], new["c"])
        # ghost copy of the nudged number slides up and becomes the new value
        ghost = n[k].data_t.copy().set_color(ACTIVE)
        self.add(ghost)
        self.play(ghost.animate.shift(UP * 0.8), run_time=0.8)
        newt = Text(f"data = {fmt(new[k])}", font_size=24, color=ACTIVE).move_to(ghost)
        self.play(ReplacementTransform(ghost, newt),
                  Transform(n[k], node_mob(k, {**st0, k: new[k]}, grads=False)),
                  run_time=0.8)
        self.play(FadeOut(newt), run_time=0.4)
        # the change travels along the arrows
        partial = {**st0, k: new[k]}
        for s, t in ROUTE[k]:
            fl = particle_flow(self.arrows[(s, t)], 1, color=FWD, n=3, run_time=1.2)
            self.add(fl.dots)
            self.play(fl)
            self.remove(fl.dots)
            partial[t] = st1[t]
            self.play(Transform(n[t], node_mob(t, partial, grads=False)), run_time=0.6)
        self.play(Indicate(n["d"], color=ACTIVE), run_time=1.0)
        # working with the real numbers substituted
        sym, sub, res = fd_working(k, base)
        out = self.working(sym, sub, res)
        slope = (st1["d"] - st0["d"]) / H
        assert abs(slope - st0["g" + k]) < 0.01, (k, slope)
        # bar grows from the zero line
        target = bar_rect(st0["g" + k], BX[k])
        lab = slope_label(k, st0["g" + k])
        self.play(Transform(self.bars[k], target), FadeIn(lab), run_time=1.5)
        self.labels[k] = lab
        self.wait(1.0)
        self.play(FadeOut(out), run_time=0.5)
        # restore the original values
        restore = {**st0}
        self.play(*[Transform(n[x], node_mob(x, restore, grads=False)) for x in ("a", "b", "c", "e", "d")],
                  run_time=0.8)

    def working(self, sym, sub, res):
        """working_line variant with readable colours, kept inside the right panel."""
        stages = []
        for s, col in zip((sym, sub, res), (WHITE, LIGHT, TEAL_L)):
            m = MathTex(s, font_size=40, color=col)
            if m.width > 3.9:
                m.scale_to_fit_width(3.9)
            m.move_to([4.8, 2.0, 0])
            stages.append(m)
        self.play(FadeIn(stages[0]), run_time=0.6)
        self.wait(0.8)
        self.play(TransformMatchingTex(stages[0], stages[1]), run_time=1.0)
        self.wait(2.0)
        self.play(TransformMatchingTex(stages[1], stages[2]), run_time=1.0)
        self.wait(2.0)
        return stages[2]

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        n = self.nodes
        nar.say("Example B: what if we change the inputs? Watch the slopes recompute.")
        self.play(FadeOut(self.act_a_lines), FadeOut(self.act_a_htag))
        act_banner(self, "Example B: what if?", hold=2.6)
        # swap static diagram for live, tracker-driven one
        self.ta, self.tb, self.tc = (ValueTracker(v) for v in CASES["A"])
        live_nodes = {k: always_redraw(lambda k=k: node_mob(k, self.live_state())) for k in "abced"}
        live_bars = always_redraw(lambda: VGroup(*[
            bar_rect(self.live_state()["g" + k], BX[k]) for k in "abc"]))
        live_labels = always_redraw(lambda: VGroup(*[
            slope_label(k, self.live_state()["g" + k]) for k in "abc"]))
        self.remove(*n.values(), *self.bars.values(), *self.labels.values())
        self.add(live_bars, live_labels, *live_nodes.values())
        before = MathTex(r"\text{before: }\ \partial d=(-3,\ 2,\ 1)", font_size=32, color=SECOND)
        before.move_to([4.7, 3.35, 0])
        self.play(FadeIn(before))

        # B1: a=-1, b=4, c=0.5
        b1 = calc(*CASES["B1"])
        assert b1["d"] == -3.5
        for k, want in zip("abc", (4, -1, 1)):
            assert abs(fd(k, vals_of("B1")) - want) < 0.01
        nar.say("Morph to a = -1, b = 4, c = 0.5: d becomes -3.5 and the bars recompute.")
        self.play(self.ta.animate.set_value(-1.0), self.tb.animate.set_value(4.0),
                  self.tc.animate.set_value(0.5), run_time=4.0)
        self.wait(1.0)
        nar.say("The slope for a is the OTHER input b, and the slope for b is a: they swap.")
        ga = MathTex("b=4", font_size=34, color=LIGHT).move_to(POS["b"] + RIGHT * 0.3)
        gb = MathTex("a=-1", font_size=34, color=LIGHT).move_to(POS["a"] + RIGHT * 0.3)
        self.add(ga, gb)
        self.play(ga.animate.move_to([BX["a"], 1.6, 0]), gb.animate.move_to([BX["b"], 1.6, 0]),
                  path_arc=-1.0, run_time=2.0)
        sym, sub, res = fd_working("a", vals_of("B1"))
        self.play(FadeOut(ga), FadeOut(gb))
        out = self.working(sym, sub, res)
        self.play(FadeOut(out))
        f1 = MathTex(r"\frac{\partial d}{\partial a}=b=4", font_size=38, color=TEAL_L).move_to([4.8, 2.3, 0])
        f2 = MathTex(r"\frac{\partial d}{\partial b}=a=-1", font_size=38, color=TEAL_L).move_to([4.8, 1.4, 0])
        self.play(FadeIn(f1), FadeIn(f2))
        self.wait(1.5)

        # B2: b = 0 (predict first)
        nar.say("Now set b to zero. What happens to the slope for a?")
        self.play(FadeOut(f1), FadeOut(f2))
        q = self.pulse_question("b = 0.\nSlope for a?", [4.8, 2.5, 0], [4.8, 1.2, 0])
        self.play(FadeOut(q))
        b2 = calc(*CASES["B2"])
        assert b2["ga"] == 0.0 and abs(fd("a", vals_of("B2"))) < 0.01
        nar.say("The slope for a is exactly 0: a times zero is zero, whatever a is.")
        self.play(self.tb.animate.set_value(0.0), run_time=3.0)
        f1 = MathTex(r"\frac{\partial d}{\partial a}=b=0", font_size=38, color=TEAL_L).move_to([4.8, 2.3, 0])
        self.play(FadeIn(f1))
        self.play(Indicate(live_nodes["b"], color=ACTIVE))
        self.wait(2.0)

        # B3: a = 0 and b = 0
        b3 = calc(*CASES["B3"])
        assert b3["ga"] == 0.0 and b3["gb"] == 0.0
        nar.say("Set a to zero as well: both slopes are 0, a flat point; only c matters.")
        f2 = MathTex(r"\frac{\partial d}{\partial b}=a=0", font_size=38, color=TEAL_L).move_to([4.8, 1.4, 0])
        self.play(self.ta.animate.set_value(0.0), run_time=3.0)
        self.play(FadeIn(f2))
        self.wait(2.5)

        # table of all four cases, row by row
        nar.say("All four cases side by side: each slope is just the other factor.")
        self.play(FadeOut(f1), FadeOut(f2), FadeOut(before))
        heads = VGroup(*[MathTex(t, font_size=26, color=c).move_to([x, 3.4, 0]) for t, c, x in zip(
            ["a", "b", "c", "d", r"\partial_a", r"\partial_b", r"\partial_c"],
            [LIGHT] * 3 + [YELLOW] + [TEAL_L] * 3, [2.5, 3.1, 3.7, 4.3, 5.0, 5.6, 6.2])])
        rule = Line([2.2, 3.15, 0], [6.5, 3.15, 0], color=GREY_B, stroke_width=2)
        self.play(FadeIn(heads), Create(rule))
        for i, case in enumerate(("A", "B1", "B2", "B3")):
            self.play(FadeIn(table_row(calc(*CASES[case]), 2.8 - 0.42 * i), shift=LEFT * 0.2), run_time=0.8)
            self.wait(0.6)
        self.wait(2.5)
        self.act_b_mobs = Group(heads, rule, live_bars, live_labels, *live_nodes.values(),
                                *self.arrows.values(), self.act_a_title)
        self.table_stuff = [m for m in self.mobjects if isinstance(m, VGroup) and len(m) == 7]

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        nar.say("Expert corner: with two inputs, d = a times b is a surface. Here a saddle.")
        stage = [m for m in self.mobjects if m not in self.foreground_mobjects]
        self.play(*[FadeOut(m) for m in stage], run_time=0.8)
        banner = act_banner(self, "Expert corner: the gradient", keep=True)
        self.fix(banner)
        self.wait(2.6)
        self.play(FadeOut(banner), run_time=0.5)

        axes = ThreeDAxes(x_range=[-4, 4, 2], y_range=[-4, 4, 2], z_range=[-6, 26, 8],
                          x_length=5, y_length=5, z_length=3.2)
        P = axes.c2p
        labels = [MathTex("a", color=LIGHT, font_size=44).move_to(P(4.7, 0, 0)),
                  MathTex("b", color=LIGHT, font_size=44).move_to(P(0, 4.7, 0)),
                  MathTex("d", color=YELLOW, font_size=44).move_to(P(0, 0, 28))]
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, frame_center=[0, 0, 0.9])
        self.play(Create(axes), *[FadeIn(l) for l in labels])
        self.add_fixed_orientation_mobjects(*labels)
        nar.say("Each point of the floor is a pair (a, b); the height above it is d.")
        surface = Surface(lambda u, v: P(u, v, u * v + 10), u_range=[-4, 4], v_range=[-4, 4],
                          resolution=(14, 14), fill_opacity=0.8, stroke_width=0.4, stroke_color=GREY_C)
        surface.set_fill_by_value(axes=axes, colorscale=[(BLUE_E, -6), (TEAL, 10), (YELLOW, 26)], axis=2)
        self.move_camera(phi=65 * DEGREES, theta=-55 * DEGREES, zoom=0.8, run_time=2.0,
                         added_anims=[FadeIn(surface)])
        self.begin_ambient_camera_rotation(rate=0.07)
        self.wait(2.0)

        nar.say("Contour lines on the floor join points that have the same d.")
        contours = VGroup()
        for k in (-12, -8, -4, 4, 8, 12):
            for s in (1, -1):
                contours.add(ParametricFunction(
                    lambda t, k=k, s=s: P(s * t, s * k / t, -6), t_range=[abs(k) / 4, 4],
                    color=GREY_A, stroke_width=3))
        contours.add(Line(P(-4, 0, -6), P(4, 0, -6), color=GREY_A, stroke_width=3),
                     Line(P(0, -4, -6), P(0, 4, -6), color=GREY_A, stroke_width=3))
        self.play(LaggedStart(*[Create(c) for c in contours], lag_ratio=0.1), run_time=3.0)

        st = calc(*CASES["A"])
        mark = Dot3D(P(2, -3, 4) + OUT * 0.1, radius=0.12, color=YELLOW)
        floor_pt = P(2, -3, -6)
        drop = DashedLine(P(2, -3, 4), floor_pt, color=YELLOW, stroke_width=3)
        nar.say("Our point (2, -3) sits at height 4. Which way is uphill?")
        self.play(FadeIn(mark), Create(drop))
        q = Text("Which way is uphill?", font_size=30, color=WHITE).move_to([0, 3.2, 0])
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to([3.4, 3.1, 0])
        self.fix(q, qm)
        self.play(FadeIn(q), FadeIn(qm))
        for _ in range(3):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        self.play(FadeOut(q), FadeOut(qm))

        nar.say("The gradient (b, a) = (-3, 2) points straight uphill, across the contours.")
        stages = [MathTex(s, font_size=40, color=c).move_to([0, 3.2, 0]) for s, c in zip(
            (r"\nabla d=\left(\frac{\partial d}{\partial a},\frac{\partial d}{\partial b}\right)",
             r"\nabla d=(b,\ a)\Big|_{a=2,\,b=-3}",
             rf"\nabla d=({fmt(st['ga'])},\ {fmt(st['gb'])})"), (WHITE, LIGHT, TEAL_L))]
        self.fix(*stages)
        self.play(FadeIn(stages[0]))
        self.wait(1.5)
        self.play(TransformMatchingTex(stages[0], stages[1]))
        self.wait(2.0)
        self.play(TransformMatchingTex(stages[1], stages[2]))
        k = 0.45
        tip = P(2 + k * st["ga"], -3 + k * st["gb"], -6)
        arrow = Arrow3D(floor_pt, tip, color=BWD, thickness=0.02)
        self.play(Create(arrow), run_time=1.5)
        self.wait(2.0)
        self.play(FadeOut(stages[2]))

        nar.say("The tangent plane touches the surface here: slope -3 along a, 2 along b.")
        plane = Surface(lambda u, v: P(u, v, 4 + st["ga"] * (u - 2) + st["gb"] * (v + 3)),
                        u_range=[1, 3], v_range=[-4, -2], resolution=(2, 2),
                        fill_color=WHITE, fill_opacity=0.55, stroke_width=1, stroke_color=WHITE)
        self.stop_ambient_camera_rotation()
        self.move_camera(zoom=1.3, frame_center=P(2, -3, 4), run_time=2.0, added_anims=[Create(plane)])
        self.wait(3.0)
        self.move_camera(zoom=0.8, frame_center=[0, 0, 0.9], run_time=2.0)
        self.begin_ambient_camera_rotation(rate=0.07)

        nar.say("A ball rolling against the gradient slides downhill, and d keeps falling.")
        a_, b_, lr = 2.0, -3.0, 0.03
        pts = []
        for _ in range(11):
            s_ = calc(a_, b_, 10.0)
            pts.append((a_, b_, s_["a"] * s_["b"] + 10.0))
            a_ -= lr * s_["ga"]
            b_ -= lr * s_["gb"]
        assert pts[-1][2] < pts[0][2]
        path = VMobject(color=ACTIVE, stroke_width=5).set_points_as_corners(
            [P(*q_) + OUT * 0.12 for q_ in pts])
        ball = Dot3D(P(*pts[0]) + OUT * 0.12, radius=0.14, color=ORANGE)
        self.play(FadeOut(mark), FadeIn(ball))
        self.play(MoveAlongPath(ball, path), Create(path), run_time=5.0, rate_func=linear)
        end = MathTex(rf"d:\ {fmt(pts[0][2])}\ \to\ {fmt(pts[-1][2])}", font_size=44, color=YELLOW)
        end.move_to([0, 3.2, 0])
        self.fix(end)
        self.play(FadeIn(end))
        self.wait(2.0)

        callbox = callout("Gradient", "the vector of all the slopes;\nit points straight uphill",
                          width=7.0)
        callbox.move_to([4.2, 2.6, 0])
        self.fix(callbox)
        nar.say("The gradient is the vector of all the slopes: a compass pointing uphill.")
        self.play(FadeOut(end), FadeIn(callbox))
        self.wait(3.5)
        self.stop_ambient_camera_rotation()
        nar.clear()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, zoom=1, frame_center=[0, 0, 0])
