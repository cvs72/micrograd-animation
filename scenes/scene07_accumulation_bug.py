from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, arrow_between, callout,
    code_panel, fmt, particle_flow, recap_line, title_card,
)
from micrograd_animation.engine import Value

PATH1, PATH2 = GREEN, PURPLE_B
H = 0.001

CODE_BUGGY = '''self.grad = 1.0 * out.grad
other.grad = 1.0 * out.grad'''
CODE_REAL = '''self.grad += 1.0 * out.grad
other.grad += 1.0 * out.grad'''


# ------------------------------------------------------------------ engine side
class BValue:
    """The tiny buggy variant of Value: backward ASSIGNS (=) instead of adding (+=)."""

    def __init__(self, data, children=(), label=""):
        self.data = data
        self.grad = 0.0
        self._prev = tuple(children)
        self._backward = lambda: None
        self.label = label

    def __add__(self, other):
        other = other if isinstance(other, BValue) else BValue(other)
        out = BValue(self.data + other.data, (self, other))

        def _backward():
            self.grad = 1.0 * out.grad
            other.grad = 1.0 * out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, BValue) else BValue(other)
        out = BValue(self.data * other.data, (self, other))

        def _backward():
            self.grad = other.data * out.grad
            other.grad = self.data * out.grad

        out._backward = _backward
        return out

    def backward(self, order=None):
        if order is None:
            order, seen = [], set()

            def build(v):
                if id(v) not in seen:
                    seen.add(id(v))
                    for c in v._prev:
                        build(c)
                    order.append(v)

            build(self)
            order = list(reversed(order))
        self.grad = 1.0
        for v in order:
            v._backward()


def single_case(kind, cls, a0):
    a = cls(a0)
    if kind == "aa":
        out = a + a
    elif kind == "aaa":
        out = (a + a) + a
    else:
        out = a * a
    return a, out


def case_grad(kind, cls, a0):
    a, out = single_case(kind, cls, a0)
    out.backward()
    return a.grad, out.data


def nudge_slope(kind, a0, t):
    """(out(a0 + H*t) - out(a0)) / H, computed with the Value class."""
    _, base = single_case(kind, Value, a0)
    _, moved = single_case(kind, Value, a0 + H * t)
    return (moved.data - base.data) / H


def graph2(cls):
    """The notebook's second example: a=-2, b=3, d=a*b, e=a+b, f=d*e."""
    a, b = cls(-2.0), cls(3.0)
    d = a * b
    e = a + b
    f = d * e
    names = {"a": a, "b": b, "d": d, "e": e, "f": f}
    for k, v in names.items():
        v.label = k
    return names


EDGES2 = [("a", "d", 1), ("b", "d", 1), ("a", "e", 1), ("b", "e", 1), ("d", "f", 1), ("e", "f", 1)]


# ------------------------------------------------------------------ drawing side
def chip(label, data, grad, width=1.7):
    nm = Text(f"{label} = {fmt(data)}", font_size=24, color=WHITE)
    g = Text(f"grad = {fmt(grad)}", font_size=24, color=GRAD)
    body = VGroup(nm, g).arrange(DOWN, buff=0.06)
    box = RoundedRectangle(corner_radius=0.12, width=max(width, body.width + 0.2), height=0.8,
                           stroke_color=WHITE, stroke_width=2)
    body.move_to(box)
    node = VGroup(box, body)
    node.box, node.g = box, g
    return node


class Side:
    """One drawn graph: chips, arrows (several per edge when a node is used twice)."""

    def __init__(self, vals, pos, edges, buggy=False):
        self.vals, self.buggy = vals, buggy
        self.chips = {k: chip(k, v.data, v.grad).move_to(pos[k]) for k, v in vals.items()}
        self.arrows = {}
        for c, p, k in edges:
            arrs = []
            for i in range(k):
                ar = arrow_between(self.chips[c], self.chips[p], color=FWD)
                if k > 1:
                    ar.shift(RIGHT * 0.22 * (i - (k - 1) / 2) * 2)
                arrs.append(ar)
            self.arrows[(c, p)] = arrs

    def group(self):
        return VGroup(*self.chips.values(), *[a for arrs in self.arrows.values() for a in arrs])


class Scene07AccumulationBug(Scene):
    # ---------------------------------------------------------------- helpers
    def tag(self, text):
        return Tex(r"\textbf{" + text + "}", font_size=34, color=ACTIVE).to_corner(UL, buff=0.5)

    def clear_stage(self):
        cur = self.nar.current
        old = [m for m in self.mobjects if m is not cur]
        if old:
            self.play(FadeOut(Group(*old)), run_time=0.6)
            self.remove(*old)

    def open_act(self, cap, banner, tag):
        self.nar.say(cap)
        act_banner(self, banner, hold=2.6)
        t = self.tag(tag)
        self.play(FadeIn(t), run_time=0.4)
        return t

    def pulse_question(self, text, pos, qpos, n=3):
        q = Text(text, font_size=30, color=WHITE).move_to(pos)
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to(qpos)
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        return VGroup(q, qm)

    def set_grad(self, side, label, value, color=GRAD):
        c = side.chips[label]
        new = Text(f"grad = {fmt(value)}", font_size=24, color=color).move_to(c.g)
        return Transform(c.g, new)

    def make_flow(self, arrs, rt=1.0):
        flows = [particle_flow(a, 1, color=BWD, n=2, reverse=True, run_time=rt) for a in arrs]
        dots = VGroup(*[f.dots for f in flows])
        self.add(dots)
        return flows, dots

    def drop_flow(self, flows, dots):
        self.remove(dots, *dots.submobjects, *[f.mobject for f in flows])
        self.remove(*[d for f in flows for d in f.dots.submobjects])

    def ghost(self, side, label, old, direction):
        c = side.chips[label]
        t = Text(fmt(old), font_size=28, color=RED).next_to(c, direction, buff=0.3)
        x = Cross(t, stroke_color=RED, stroke_width=6)
        return VGroup(t, x)

    def step(self, side, label, rt=0.9):
        """Run the real _backward of one node and show the gradient reaching its children."""
        v = side.vals[label]
        kids = []
        for k in v._prev:
            if k.label not in [q.label for q in kids]:
                kids.append(k)
        before = {k.label: k.grad for k in kids}
        v._backward()
        arrs = [a for k in kids for a in side.arrows[(k.label, label)]]
        flows, dots = self.make_flow(arrs, rt)
        self.play(side.chips[label].box.animate.set_stroke(BWD, width=6), *flows,
                  *[self.set_grad(side, k.label, k.grad) for k in kids], run_time=rt + 0.4)
        self.drop_flow(flows, dots)
        self.play(side.chips[label].box.animate.set_stroke(WHITE, width=2), run_time=0.3)
        return before

    def label_row(self):
        l = Text("buggy:  grad = ...", font_size=30, color=RED).move_to([-3.4, 2.85, 0])
        r = Text("real:  grad += ...", font_size=30, color=GREEN).move_to([3.4, 2.85, 0])
        return VGroup(l, r)

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S07")
        title_card(self, "Chapter 7", "Why are gradients added up, not assigned?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        self.clear_stage()
        recap_line(self, "Next: what happens when we write a + 1 or 2 * a?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        nar.say("Example A: what is the gradient of b = a + a, with a = 3?")
        act_banner(self, "Example A: one node used twice", hold=2.6)
        tag = self.tag("Example A:")
        self.play(FadeIn(tag), run_time=0.4)

        # (1) b = a + a
        bug_a, bug_b = BValue(3.0, label="a"), None
        bug_b = bug_a + bug_a
        bug_b.label = "b"
        real_a = Value(3.0, label="a")
        real_b = real_a + real_a
        real_b.label = "b"
        assert real_b.data == 6.0 and bug_b.data == 6.0
        sides = []
        for cx, vals, buggy in ((-3.4, {"a": bug_a, "b": bug_b}, True),
                                (3.4, {"a": real_a, "b": real_b}, False)):
            pos = {"a": [cx, -1.1, 0], "b": [cx, 0.5, 0]}
            sides.append(Side(vals, pos, [("a", "b", 2)], buggy))
        sl, sr = sides
        labels = self.label_row()
        divider = DashedLine([0, 3.3, 0], [0, -2.5, 0], color=SECOND)
        self.play(FadeIn(labels), Create(divider), run_time=0.8)
        nar.say("Both sides add a to itself, so b is 6; the plus node reads a twice.")
        self.play(FadeIn(sl.group()), FadeIn(sr.group()), run_time=1.0)
        self.play(*[Indicate(s.chips["b"], color=FWD) for s in sides], run_time=1.0)
        self.wait(1.0)

        nar.say("Before the code runs: what should a.grad be? Nudge a, b moves twice.")
        q = self.pulse_question("a.grad after b.backward()?", [0, 1.9, 0], [0, 0.4, 0])
        self.play(FadeOut(q), run_time=0.4)

        nar.say("Same rule on both sides; the only difference is = against +=.")
        cb = code_panel(CODE_BUGGY, highlight=[1, 2], font_size=24)
        cr = code_panel(CODE_REAL, highlight=[1, 2], font_size=24)
        panels = []
        for c, cx in ((cb, -3.4), (cr, 3.4)):
            grp = VGroup(c, c.highlight)
            grp.scale_to_fit_width(5.6).move_to([cx, 1.95, 0])
            panels.append(grp)
        hl_b, hl_r = cb.highlight, cr.highlight
        self.play(FadeIn(VGroup(cb, cr)), run_time=0.8)
        self.wait(1.0)

        nar.say("The plus node starts with b.grad = 1, then passes it down the first arrow.")
        for s in sides:
            s.vals["b"].grad = 1.0
        self.play(*[self.set_grad(s, "b", 1.0) for s in sides], run_time=0.6)
        self.play(FadeIn(hl_b[0]), FadeIn(hl_r[0]), run_time=0.4)
        for s in sides:
            s.vals["b"]._backward()
        assert bug_a.grad == 1.0 and real_a.grad == 2.0
        flows, dots = self.make_flow([sl.arrows[("a", "b")][0], sr.arrows[("a", "b")][0]], 1.2)
        self.play(*flows, *[self.set_grad(s, "a", 1.0) for s in sides], run_time=1.4)
        self.drop_flow(flows, dots)
        self.wait(1.0)

        nar.say("The second arrow arrives: the left side overwrites, the right side adds.")
        self.play(ReplacementTransform(hl_b[0], hl_b[1]), ReplacementTransform(hl_r[0], hl_r[1]),
                  run_time=0.6)
        flows, dots = self.make_flow([sl.arrows[("a", "b")][1], sr.arrows[("a", "b")][1]], 1.2)
        gh = self.ghost(sl, "a", 1.0, LEFT)
        self.play(*flows, self.set_grad(sr, "a", real_a.grad), run_time=1.4)
        self.drop_flow(flows, dots)
        self.play(FadeIn(gh[0]), Create(gh[1]), run_time=0.6)
        self.play(Indicate(sl.chips["a"], color=RED), Indicate(sr.chips["a"], color=GREEN),
                  run_time=1.0)
        self.wait(0.6)
        self.play(FadeOut(gh), run_time=0.4)

        nar.say("Right: 1 + 1 = 2. Left: the first 1 is erased, so it keeps only 1. Wrong!")
        bad = Text("second write erases the first", font_size=26, color=RED).move_to([-3.4, -2.0, 0])
        good = MathTex(r"\frac{\partial b}{\partial a}=1+1=2", font_size=40, color=GRAD)
        good.move_to([3.4, -2.0, 0])
        self.play(FadeIn(bad), FadeIn(good), run_time=0.8)
        self.wait(3.0)

        cl = callout("Gradient accumulation", "every path into a node ADDS its share (+=)",
                     color=ACTIVE, width=7.5).move_to([1.0, 2.85, 0])
        nar.say("Gradient accumulation: shares from every path must be summed.")
        self.play(FadeOut(labels), FadeIn(cl), run_time=0.5)
        self.wait(3.2)
        self.play(FadeOut(cl), FadeIn(labels), run_time=0.5)
        self.play(FadeOut(Group(*panels)), FadeOut(bad), FadeOut(good), run_time=0.6)

        # (2) the notebook's second example
        nar.say("The lecture's bigger case: f = d * e, where a and b each feed d and e.")
        self.play(FadeOut(sl.group()), FadeOut(sr.group()), run_time=0.5)
        bug_v, real_v = graph2(BValue), graph2(Value)
        assert real_v["f"].data == -6.0 and bug_v["f"].data == -6.0
        sides = []
        for cx, vals, buggy in ((-3.4, bug_v, True), (3.4, real_v, False)):
            pos = {"f": [cx, 1.9, 0], "d": [cx - 1.35, 0.55, 0], "e": [cx + 1.35, 0.55, 0],
                   "a": [cx - 1.35, -0.8, 0], "b": [cx + 1.35, -0.8, 0]}
            sides.append(Side(vals, pos, EDGES2, buggy))
        sl, sr = sides
        self.play(FadeIn(sl.group()), FadeIn(sr.group()), run_time=1.2)
        self.play(*[Indicate(s.chips["f"], color=FWD) for s in sides], run_time=1.0)
        self.wait(1.0)

        nar.say("f starts at grad 1; the product node gives d.grad = 1 and e.grad = -6.")
        for v in (bug_v["f"], real_v["f"]):
            v.grad = 1.0
        self.play(*[self.set_grad(s, "f", 1.0) for s in sides], run_time=0.6)
        self.step(sl, "f")
        self.step(sr, "f")
        self.wait(0.8)

        nar.say("Now d runs first: a gets b * 1 = 3 and b gets a * 1 = -2, on both sides.")
        self.step(sl, "d")
        self.step(sr, "d")
        assert (bug_v["a"].grad, bug_v["b"].grad) == (3.0, -2.0)
        self.wait(1.0)

        nar.say("Then e runs. It sends -6 to a and b: left overwrites, right adds on top.")
        bl = self.step(sl, "e")
        ga = self.ghost(sl, "a", bl["a"], LEFT)
        gb = self.ghost(sl, "b", bl["b"], RIGHT)
        self.play(FadeIn(ga[0]), FadeIn(gb[0]), Create(ga[1]), Create(gb[1]), run_time=0.6)
        self.step(sr, "e")
        assert (bug_v["a"].grad, bug_v["b"].grad) == (-6.0, -6.0)
        assert (real_v["a"].grad, real_v["b"].grad) == (-3.0, -8.0)
        self.wait(1.5)
        self.play(FadeOut(ga), FadeOut(gb), run_time=0.4)

        nar.say("The buggy side lost d's share: -6 and -6 instead of -3 and -8.")
        bad = Text("d's share was overwritten", font_size=26, color=RED).move_to([-3.4, -1.95, 0])
        e_, b_, d_ = real_v["e"].data, real_v["b"].data, real_v["d"].data
        stages = [
            MathTex(r"a.\mathrm{grad}=e\cdot b+d\cdot 1", font_size=40, color=WHITE),
            MathTex(rf"=({fmt(e_)})({fmt(b_)})+({fmt(d_)})(1)", font_size=40, color=DATA),
            MathTex(rf"=3+({fmt(d_)})={fmt(real_v['a'].grad)}", font_size=40, color=GRAD),
        ]
        for st in stages:
            st.scale_to_fit_width(5.6)
            st.move_to([3.4, -1.95, 0])
        self.play(FadeIn(bad), FadeIn(stages[0]), run_time=0.8)
        self.wait(1.0)
        self.play(TransformMatchingTex(stages[0], stages[1]), run_time=1.0)
        self.wait(2.5)
        self.play(TransformMatchingTex(stages[1], stages[2]), run_time=1.0)
        self.wait(2.5)
        nar.say("Overwriting is only right when each node is used once; a shared node adds.")
        self.play(Indicate(sr.chips["a"], color=GREEN), Indicate(sl.chips["a"], color=RED),
                  run_time=1.2)
        self.wait(1.5)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        self.clear_stage()
        tag = self.open_act("Example B: what if a feeds the output two, three or more times?",
                            "Example B: more uses, more damage", "Example B:")
        kinds = [("aa", 3.0, r"b=a+a"), ("aaa", 3.0, r"z=a+a+a"), ("sq", 2.0, r"y=x\cdot x")]
        names = [("a", "b"), ("a", "z"), ("x", "y")]
        mult = [2, 3, 2]
        cxs = [-4.4, 0.0, 4.4]
        SC, BASE = 0.38, -1.9
        cols = []
        for (kind, a0, tex), (ln, on), k, cx in zip(kinds, names, mult, cxs):
            ga, go = case_grad(kind, Value, a0)
            ba, _ = case_grad(kind, BValue, a0)
            _, out = single_case(kind, Value, a0)
            leaf = chip(ln, a0, 0.0).move_to([cx, 0.6, 0])
            top = chip(on, out.data, 0.0).move_to([cx, 1.9, 0])
            arrs = []
            for i in range(k):
                ar = arrow_between(leaf, top, color=FWD)
                ar.shift(RIGHT * 0.3 * (i - (k - 1) / 2))
                arrs.append(ar)
            title = MathTex(tex, font_size=40, color=WHITE).move_to([cx, 2.95, 0])
            cols.append(dict(kind=kind, a0=a0, cx=cx, real=ga, bug=ba, leaf=leaf, top=top,
                             arrs=arrs, title=title))
        assert [c["real"] for c in cols] == [2.0, 3.0, 4.0]
        assert [c["bug"] for c in cols] == [1.0, 1.0, 2.0]

        nar.say("Three cases on one screen: b = a + a, z = a + a + a, and y = x times x.")
        graphs = VGroup(*[VGroup(c["title"], c["leaf"], c["top"], *c["arrs"]) for c in cols])
        self.play(FadeIn(graphs), run_time=1.2)
        self.wait(1.0)

        nar.say("Predict first: for z = a + a + a, what should a.grad be?")
        q = self.pulse_question("a.grad for z = a + a + a ?", [0, -0.2, 0], [0, -1.2, 0])
        self.play(FadeOut(q), run_time=0.4)

        def bar(x, val, color):
            h = max(abs(val), 0.001) * SC
            r = Rectangle(width=0.6, height=h, fill_color=color, fill_opacity=0.9, stroke_width=0)
            return r.move_to([x, BASE + (h / 2 if val >= 0 else -h / 2), 0])

        nar.say("Three arrows, three shares: the real gradient is 3, the bug says 1.")
        bars = []
        for c in cols:
            cx = c["cx"]
            bb, rb = bar(cx - 1.0, c["bug"], RED), bar(cx, c["real"], GREEN)
            bl = Text(fmt(c["bug"]), font_size=28, color=RED).next_to(bb, UP, buff=0.1)
            rl = Text(fmt(c["real"]), font_size=28, color=GREEN).next_to(rb, UP, buff=0.1)
            c["bars"] = (bb, rb, bl, rl)
            bars.append(c["bars"])
        order = [1, 0, 2]
        for i in order:
            bb, rb, bl, rl = cols[i]["bars"]
            self.play(GrowFromEdge(bb, DOWN), GrowFromEdge(rb, DOWN), run_time=0.8)
            self.play(FadeIn(bl), FadeIn(rl), run_time=0.4)
            if i == 1:
                self.wait(1.5)
        base = Line([-6.4, BASE, 0], [6.4, BASE, 0], color=SECOND, stroke_width=2)
        lab = VGroup()
        for c in cols:
            for dx, t, col in ((-1.0, "buggy", RED), (0.0, "real", GREEN), (1.0, "nudge", YELLOW)):
                lab.add(Text(t, font_size=24, color=col).move_to([c["cx"] + dx, BASE - 0.3, 0]))
        self.play(Create(base), FadeIn(lab), run_time=0.8)
        self.wait(1.5)

        nar.say("Check it: nudge a by 0.001 and watch how fast the output moves.")
        tr = ValueTracker(0.0)
        nudges = []
        for c in cols:
            def mk(c=c):
                s = nudge_slope(c["kind"], c["a0"], tr.get_value())
                r = bar(c["cx"] + 1.0, s, YELLOW)
                lab_ = Text(fmt(s), font_size=28, color=YELLOW).next_to(r, UP, buff=0.1)
                return VGroup(r, lab_)
            nudges.append(always_redraw(mk))
        work_sub, work_res = [], []
        for c in cols:
            a1 = c["a0"] + H
            if c["kind"] == "aa":
                sub = rf"\frac{{({fmt(a1)}+{fmt(a1)})-({fmt(c['a0'])}+{fmt(c['a0'])})}}{{0.001}}"
            elif c["kind"] == "aaa":
                sub = (rf"\frac{{({fmt(a1)}\cdot 3)-({fmt(c['a0'])}\cdot 3)}}{{0.001}}")
            else:
                sub = rf"\frac{{({fmt(a1)}\cdot{fmt(a1)})-({fmt(c['a0'])}\cdot{fmt(c['a0'])})}}{{0.001}}"
            slope = nudge_slope(c["kind"], c["a0"], 1.0)
            ws = MathTex(sub, font_size=34, color=DATA).move_to([c["cx"], 1.3, 0])
            wr = MathTex(rf"={fmt(slope)}", font_size=40, color=GRAD).move_to([c["cx"], 1.3, 0])
            if ws.width > 3.9:
                ws.scale_to_fit_width(3.9)
            work_sub.append(ws)
            work_res.append(wr)
            c["slope"] = slope
        assert abs(cols[0]["slope"] - 2) < 0.01 and abs(cols[1]["slope"] - 3) < 0.01
        assert abs(cols[2]["slope"] - 4) < 0.01
        self.play(FadeOut(graphs), run_time=0.6)
        self.play(*[FadeIn(w) for w in work_sub], *[Create(n) for n in nudges], run_time=0.6)
        self.add(*nudges)
        self.play(tr.animate.set_value(1.0), run_time=3.0, rate_func=linear)
        self.wait(2.0)
        self.play(*[ReplacementTransform(a, b) for a, b in zip(work_sub, work_res)], run_time=1.0)
        self.wait(2.5)

        nar.say("The yellow nudge always matches the green bar, never the red one.")
        self.play(*[Indicate(c["bars"][1], color=GREEN) for c in cols],
                  *[Indicate(n, color=YELLOW) for n in nudges], run_time=1.5)
        self.wait(2.0)
        nar.say("So the bug grows with the uses: a node used k times loses k - 1 shares.")
        self.wait(2.5)

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        self.clear_stage()
        tag = self.open_act("Expert corner: the chain rule adds one term for every path.",
                            "Expert corner: sum over paths", "Expert corner:")
        vals = graph2(Value)
        vals["f"].backward()
        pos = {"f": [-3.4, 1.9, 0], "d": [-4.9, 0.4, 0], "e": [-1.9, 0.4, 0],
               "a": [-4.9, -1.2, 0], "b": [-1.9, -1.2, 0]}
        side = Side(vals, pos, EDGES2)
        for k, c in side.chips.items():
            c.g.become(Text(f"grad = {fmt(vals[k].grad)}", font_size=24, color=GRAD).move_to(c.g))
        nar.say("Take the notebook graph again. Every route from f down to a is one path.")
        self.play(FadeIn(side.group()), run_time=1.2)
        self.wait(1.0)

        def paths(src):
            p1 = [side.arrows[(src, "d")][0], side.arrows[("d", "f")][0]]
            p2 = [side.arrows[(src, "e")][0], side.arrows[("e", "f")][0]]
            o1 = VGroup(*[a.copy().set_color(PATH1).set_stroke(width=9) for a in p1])
            o2 = VGroup(*[a.copy().set_color(PATH2).set_stroke(width=9) for a in p2])
            return p1, p2, o1, o2

        def sum_stages(src, other, p_other):
            # the two products come from the engine's own numbers
            e_, d_ = vals["e"].data, vals["d"].data
            t1 = e_ * other.data
            t2 = d_ * 1.0
            parts = [
                (rf"\frac{{\partial f}}{{\partial {src}}}=", r"e\cdot " + other.label, "+", r"d\cdot 1", ""),
                ("=", rf"({fmt(e_)})({fmt(other.data)})", "+", rf"({fmt(d_)})(1)", ""),
                ("=", fmt(t1), "+", f"({fmt(t2)})", f"={fmt(t1 + t2)}"),
            ]
            out = []
            for p in parts:
                m = MathTex(*[x for x in p if x != ""], font_size=40)
                idx = [i for i, x in enumerate([x for x in p if x != ""])]
                m[1].set_color(PATH1)
                m[3].set_color(PATH2)
                if len(m) > 4:
                    m[4].set_color(GRAD)
                if m.width > 5.6:
                    m.scale_to_fit_width(5.6)
                m.move_to([3.6, 0.9, 0])
                out.append(m)
            return out, t1 + t2

        cur = None
        for src, other in (("a", vals["b"]), ("b", vals["a"])):
            p1, p2, o1, o2 = paths(src)
            if src == "a":
                nar.say("Path one goes through d and carries e times b; path two goes through e.")
            else:
                nar.say("Same for b: one route through d, one through e, one product each.")
            anims = []
            if cur is None:
                anims += [Create(o1), Create(o2)]
            else:
                anims += [Transform(cur[0], o1), Transform(cur[1], o2)]
            self.play(*anims, run_time=1.2)
            if cur is None:
                cur = [o1, o2]
            fl1, d1 = self.make_flow(list(reversed(p1)), 1.0)
            fl2, d2 = self.make_flow(list(reversed(p2)), 1.0)
            self.play(*fl1, *fl2, run_time=1.4)
            self.drop_flow(fl1, d1)
            self.drop_flow(fl2, d2)
            stages, total = sum_stages(src, other, None)
            assert abs(total - vals[src].grad) < 1e-9
            self.play(FadeIn(stages[0]), run_time=0.6)
            self.wait(1.2)
            self.play(TransformMatchingTex(stages[0], stages[1]), run_time=1.0)
            self.wait(2.5)
            self.play(TransformMatchingTex(stages[1], stages[2]), run_time=1.0)
            self.play(Indicate(side.chips[src], color=GREEN), run_time=1.0)
            self.wait(2.5)
            self.play(FadeOut(stages[2]), run_time=0.4)
        nar.say("Each path adds its share: a node's gradient is the sum over paths.")
        self.wait(2.5)
        self.play(FadeOut(side.group()), FadeOut(cur[0]), FadeOut(cur[1]), run_time=0.6)

        # --- accumulation across steps: zero_grad
        nar.say("Frameworks keep adding on purpose, so you must zero grads before each step.")
        x = Value(3.0)
        nz, wz = [], []
        for _ in range(3):
            y = x * x
            y.backward()
            nz.append(x.grad)
        for _ in range(3):
            x.grad = 0.0
            y = x * x
            y.backward()
            wz.append(x.grad)
        assert nz == [6.0, 12.0, 18.0] and wz == [6.0, 6.0, 6.0]
        SC, BASE = 0.1, -1.7
        g1 = VGroup()
        for cx, series, col, ttl in ((-3.4, nz, RED, "no zeroing"), (3.4, wz, GREEN, "zero_grad first")):
            t = Text(ttl, font_size=28, color=col).move_to([cx, 1.6, 0])
            g1.add(t)
            for i, v in enumerate(series):
                h = v * SC
                r = Rectangle(width=0.8, height=h, fill_color=col, fill_opacity=0.9, stroke_width=0)
                r.move_to([cx - 1.4 + 1.4 * i, BASE + h / 2, 0])
                n = Text(fmt(v), font_size=28, color=WHITE).next_to(r, UP, buff=0.1)
                s = Text(f"step {i + 1}", font_size=24, color=SECOND).move_to([cx - 1.4 + 1.4 * i, BASE - 0.3, 0])
                g1.add(r, n, s)
        sums = VGroup(
            MathTex(r"x.\mathrm{grad}=6+6+6=18", font_size=36, color=RED).move_to([-3.4, 2.5, 0]),
            MathTex(r"x.\mathrm{grad}=6", font_size=36, color=GREEN).move_to([3.4, 2.5, 0]),
        )
        self.play(FadeIn(g1), FadeIn(sums), run_time=1.2)
        self.wait(1.0)
        nar.say("Here y = x times x, x = 3: the true slope is 6 each step, not 12 or 18.")
        self.play(Indicate(g1[0], color=RED), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(g1), FadeOut(sums), run_time=0.6)

        # --- gradient accumulation over micro-batches
        nar.say("Used on purpose: add the gradients of four small batches into one big one.")
        w = Value(0.5)
        incs, prev = [], 0.0
        for xi in (1.0, 2.0, 3.0, 4.0):
            loss = (w * xi + -1.0) ** 2
            loss.backward()
            incs.append(w.grad - prev)
            prev = w.grad
        assert [round(i, 6) for i in incs] == [-1.0, 0.0, 3.0, 8.0] and abs(w.grad - 10.0) < 1e-9
        SC2, BASE2 = 0.15, -0.6
        g2 = VGroup()
        xs = [-5.0, -3.6, -2.2, -0.8]
        for i, (xv, v) in enumerate(zip(xs, incs)):
            h = max(abs(v), 0.02) * SC2
            r = Rectangle(width=0.8, height=h, fill_color=YELLOW, fill_opacity=0.9, stroke_width=0)
            r.move_to([xv, BASE2 + (h / 2 if v >= 0 else -h / 2), 0])
            n = Text(fmt(v), font_size=28, color=WHITE).next_to(r, UP if v >= 0 else DOWN, buff=0.1)
            s = Text(f"batch {i + 1}", font_size=24, color=SECOND).move_to([xv, -1.7, 0])
            g2.add(r, n, s)
        axis = Line([-5.8, BASE2, 0], [0.2, BASE2, 0], color=SECOND, stroke_width=2)
        g2.add(axis)
        self.play(FadeIn(g2), run_time=1.0)
        self.wait(1.0)
        tot_h = w.grad * SC2
        tot = Rectangle(width=1.0, height=tot_h, fill_color=GREEN, fill_opacity=0.9, stroke_width=0)
        tot.move_to([3.2, BASE2 + tot_h / 2, 0])
        totn = Text(fmt(w.grad), font_size=28, color=WHITE).next_to(tot, UP, buff=0.1)
        tots = Text("w.grad", font_size=24, color=SECOND).move_to([3.2, -1.7, 0])
        work = MathTex(r"-1+0+3+8=10", font_size=40, color=GRAD).move_to([3.2, 2.3, 0])
        nar.say("Their sum is 10, the gradient of the whole batch, with less memory at once.")
        self.play(*[Indicate(m, color=YELLOW) for m in g2[0::3]], run_time=1.0)
        self.play(FadeIn(work), GrowFromEdge(tot, DOWN), FadeIn(totn), FadeIn(tots), run_time=1.2)
        self.wait(3.0)
        cl = callout("Zero, then accumulate", "zero_grad() once per step; += does the summing",
                     width=8.0).move_to([1.2, 2.6, 0])
        nar.say("The rule: += inside the engine, zero the grads once per optimizer step.")
        self.play(FadeOut(work), FadeIn(cl), run_time=0.5)
        self.wait(3.5)
