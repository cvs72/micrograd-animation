import math
import sys

from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, arrow_between, callout,
    code_panel, fmt, particle_flow, recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value


# ------------------------------------------------------------------ engine side
class NaiveAdd:
    """The first draft of Value: __add__ assumes `other` is a Value."""

    def __init__(self, data):
        self.data = data

    def __add__(self, other):
        return NaiveAdd(self.data + other.data)


class NaiveMul:
    """Second draft: wraps plain numbers, but has no __rmul__."""

    def __init__(self, data):
        self.data = data

    def __mul__(self, other):
        other = other if isinstance(other, NaiveMul) else NaiveMul(other)
        return NaiveMul(self.data * other.data)


NaiveAdd.__name__ = NaiveAdd.__qualname__ = "Value"
NaiveMul.__name__ = NaiveMul.__qualname__ = "Value"


def error_text(fn):
    try:
        fn()
    except Exception as e:  # the real message, shown on screen
        return type(e).__name__, str(e)
    raise AssertionError("expected an error")


def neuron(pieces):
    """The S05 neuron; the activation is one fused tanh or rebuilt from exp, plus, times, power."""
    d = dict(x1=Value(2.0), x2=Value(0.0), w1=Value(-3.0), w2=Value(1.0), b=Value(6.8813735870195432))
    d["x1w1"] = d["x1"] * d["w1"]
    d["x2w2"] = d["x2"] * d["w2"]
    d["s"] = d["x1w1"] + d["x2w2"]
    d["n"] = d["s"] + d["b"]
    if pieces:
        d["t"] = d["n"] * 2
        d["e"] = d["t"].exp()
        d["u"] = d["e"] - 1
        d["v"] = d["e"] + 1
        d["w"] = d["v"] ** -1
        d["o"] = d["u"] * d["w"]
    else:
        d["o"] = d["n"].tanh()
    return d


def sigmoid_chain(x0):
    x = Value(x0)
    m = x * -1
    e = m.exp()
    p = e + 1
    s = p**-1
    return dict(x=x, m=m, e=e, p=p, s=s)


def sig(x):
    return sigmoid_chain(x)["s"].data


def sig_slope(x):
    c = sigmoid_chain(x)
    c["s"].grad = 1.0
    for k in ("s", "p", "e", "m"):
        c[k]._backward()
    return c["x"].grad


def tanh_from_sigmoid(x):
    v = Value(x) * 2
    out = ((((v * -1).exp() + 1) ** -1) * 2) - 1
    return out.data


def naive_tanh(x):
    e = (x * 2).exp()
    return (e - 1) / (e + 1)


def stable_tanh(x):
    sign = 1 if x.data >= 0 else -1
    z = (x * (-2 * sign)).exp()
    return ((1 - z) / (1 + z)) * sign


def overflow_point():
    lo, hi = 0.0, 800.0
    for _ in range(60):
        mid = (lo + hi) / 2
        try:
            math.exp(mid)
            lo = mid
        except OverflowError:
            hi = mid
    return lo


# ------------------------------------------------------------------ drawing side
def chip(op, data, grad, compact=False, w=1.6):
    o = Text(op, font_size=24, color=WHITE, weight=BOLD)
    d = Text(fmt(data), font_size=24, color=DATA)
    g = Text(fmt(grad), font_size=24, color=GRAD)
    if compact:
        row = VGroup(d, g).arrange(RIGHT, buff=0.7)
        body = VGroup(o, row).arrange(DOWN, buff=0.08)
        h = 0.85
    else:
        body = VGroup(o, d, g).arrange(DOWN, buff=0.06)
        h = 1.2
    box = RoundedRectangle(corner_radius=0.12, width=max(w, body.width + 0.25), height=h,
                           stroke_color=WHITE, stroke_width=2)
    body.move_to(box)
    node = VGroup(box, body)
    node.box, node.d, node.g, node.op = box, d, g, o
    return node


CODE_ADD = '''a = Value(2.0)
b = a + 1'''
CODE_ADD_FIX = '''if not isinstance(other, Value):
    other = Value(other)'''
CODE_MUL = '''a = Value(2.0)
b = 2 * a'''
CODE_NAIVE = '''x = Value(400.0)
e = (2 * x).exp()
o = (e - 1) / (e + 1)'''
CODE_STABLE = '''z = (-2 * x).exp()
o = (1 - z) / (1 + z)'''


class Scene08MoreOperations(MovingCameraScene):
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

    def placed(self, code, line, width, pos):
        """Code panel and its highlight scaled and moved together."""
        p = code_panel(code, highlight=[line])
        g = VGroup(p, p.highlight)
        g.scale_to_fit_width(width).move_to(pos)
        return g

    def show_callout(self, title, body, pos, color=ACTIVE, width=6.4):
        c = callout(title, body, color=color, width=width).move_to(pos)
        self.play(FadeIn(c), run_time=0.5)
        self.wait(3.2)
        return c

    def zoom_on(self, target, factor, hold, dy=-0.4):
        """Zoom the camera onto target; the caption follows the frame."""
        frame = self.camera.frame
        cap = self.nar.current
        base_w = cap.width

        def follow(m):
            k = frame.width / config.frame_width
            m.set_width(base_w * k)
            m.move_to(frame.get_bottom() + UP * (m.height / 2 + 0.2 * k))

        cap.add_updater(follow)
        self.play(frame.animate.scale(factor).move_to(target.get_center() + UP * dy), run_time=0.9)
        self.wait(hold)
        self.play(frame.animate.scale(1 / factor).move_to(ORIGIN), run_time=0.9)
        cap.remove_updater(follow)
        follow(cap)

    def error_box(self, kind, msg, pos, width=6.0):
        t = Text(f"{kind}:", font_size=28, color=RED, weight=BOLD)
        m = Text(msg, font_size=26, color=WHITE)
        g = VGroup(t, m).arrange(DOWN, buff=0.12)
        if g.width > width - 0.4:
            g.scale_to_fit_width(width - 0.4)
        box = RoundedRectangle(corner_radius=0.15, width=g.width + 0.4, height=g.height + 0.35,
                               stroke_color=RED, stroke_width=3, fill_color=BLACK, fill_opacity=0.9)
        g.move_to(box)
        return VGroup(box, g).move_to(pos)

    def new_grad(self, c, value):
        new = Text(fmt(value), font_size=24, color=GRAD).move_to(c.g)
        return Transform(c.g, new)

    def flows(self, arrs, color, reverse, rt=0.9):
        fl = [particle_flow(a, 1, color=color, n=2, reverse=reverse, run_time=rt) for a in arrs]
        dots = VGroup(*[f.dots for f in fl])
        self.add(dots)
        return fl, dots

    def drop(self, fl, dots):
        self.remove(dots, *dots.submobjects, *[f.mobject for f in fl])
        self.remove(*[d for f in fl for d in f.dots.submobjects])

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S08")
        title_card(self, "Chapter 8", "Do operations have to be tiny?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        self.clear_stage()
        recap_line(self, "Next: can we run all of this in PyTorch?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        nar.say("Example A: our Value class meets plain Python numbers for the first time.")
        act_banner(self, "Example A: more operations", hold=2.6)
        tag = self.tag("Example A:")
        self.play(FadeIn(tag), run_time=0.4)

        # (1) a + 1
        kind, msg = error_text(lambda: NaiveAdd(2.0) + 1)
        assert msg == "'int' object has no attribute 'data'"
        a = Value(2.0)
        b = a + 1
        assert b.data == 3.0
        panel = self.placed(CODE_ADD, 2, 5.4, [-3.6, 1.4, 0])
        nar.say("We write a + 1. A plain number sits next to our Value. Will it work?")
        self.play(FadeIn(panel), run_time=0.8)
        q = self.pulse_question("Does a + 1 work?", [3.6, 2.1, 0], [3.6, 0.7, 0])
        err = self.error_box(kind, msg, [3.6, 1.2, 0])
        nar.say("No. The plain number 1 has no data attribute, so Python raises an error.")
        self.play(ReplacementTransform(q, err), run_time=0.8)
        self.wait(2.0)
        fix = self.placed(CODE_ADD_FIX, 2, 5.6, [-3.6, 1.4, 0])
        nar.say("The fix: if other is not a Value, wrap it in one before adding.")
        self.play(ReplacementTransform(panel, fix), run_time=0.8)
        ca, cc, cb = chip("a", a.data, 0.0), chip("Value(1)", 1.0, 0.0, w=1.9), chip("b = a + 1", b.data, 0.0, w=1.9)
        ca.move_to([-3.2, -1.0, 0])
        cc.move_to([0.6, -1.9, 0])
        cb.move_to([3.2, -1.0, 0])
        ar1, ar2 = arrow_between(ca, cb), arrow_between(cc, cb)
        self.play(FadeOut(err), FadeIn(ca), FadeIn(cc), run_time=0.8)
        self.play(Create(ar1), Create(ar2), FadeIn(cb), run_time=1.0)
        self.wait(1.5)

        # (2) 2 * a
        kind2, msg2 = error_text(lambda: 2 * NaiveMul(2.0))
        assert "unsupported operand" in msg2
        b2 = 2 * a
        assert b2.data == 4.0
        self.play(FadeOut(Group(fix, ca, cc, cb, ar1, ar2)), run_time=0.6)
        nar.say("Now the other order: 2 * a. Python asks the number 2 first.")
        boxes = [
            ("2 * a", [-5.6, 1.8, 0], WHITE),
            ("int.__mul__(2, a)", [-2.5, 1.8, 0], WHITE),
            ("a.__rmul__(2)", [1.7, 1.8, 0], FWD),
            ("a * 2 = " + fmt(b2.data), [5.4, 1.8, 0], ACTIVE),
        ]
        nodes = []
        for text, p, col in boxes:
            t = Text(text, font_size=24, color=col)
            bx = RoundedRectangle(corner_radius=0.12, width=t.width + 0.4, height=0.7, stroke_color=col)
            t.move_to(bx)
            nodes.append(VGroup(bx, t).move_to(p))
        self.play(FadeIn(nodes[0]), FadeIn(nodes[1]), run_time=0.8)
        arr = arrow_between(nodes[0], nodes[1], color=ACTIVE)
        self.play(Create(arr), run_time=0.6)
        em = self.error_box(kind2, msg2, [0, 0.0, 0], width=12.0)
        nar.say("The int can't handle our class, so Python tries the other side.")
        self.play(FadeIn(em), run_time=0.8)
        self.wait(2.0)
        self.play(FadeOut(em), run_time=0.4)
        nar.say("Next it calls a.__rmul__(2), which swaps the operands: a * 2.")
        arr2 = arrow_between(nodes[1], nodes[2], color=FWD)
        arr3 = arrow_between(nodes[2], nodes[3], color=FWD)
        self.play(FadeIn(nodes[2]), Create(arr2), run_time=0.8)
        self.play(FadeIn(nodes[3]), Create(arr3), run_time=0.8)
        self.play(Indicate(nodes[3], color=ACTIVE), run_time=1.0)
        self.wait(1.0)
        c1 = self.show_callout("Operator overloading",
                               "Our class defines what + and * mean for it.", [0, -0.9, 0])
        self.play(FadeOut(c1), run_time=0.4)
        self.play(FadeOut(Group(*nodes, arr, arr2, arr3)), run_time=0.6)

        # (3) the table of recipes
        x = Value(2.0)
        ex = x.exp()
        ex.backward()
        assert abs(x.grad - ex.data) < 1e-12
        p = Value(3.0)
        pw = p**2
        pw.backward()
        pa, pb = Value(6.0), Value(3.0)
        dv = pa / pb
        dv.backward()
        sa, sb = Value(5.0), Value(2.0)
        sd = sa - sb
        sd.backward()
        na = Value(4.0)
        ng = -na
        ng.backward()
        assert abs(pa.grad - 1 / 3) < 1e-12 and abs(pb.grad + 6 / 9) < 1e-12
        rows = [
            (r"\frac{d}{dx}\,e^{x}=e^{x}",
             rf"\text{{grad}}=e^{{{fmt(x.data)}}}={fmt(ex.data)}"),
            (r"\frac{d}{dx}\,x^{k}=k\,x^{k-1}",
             rf"{2}\cdot {fmt(p.data)}^{{1}}={fmt(p.grad)}"),
            (r"a/b=a\cdot b^{-1}",
             rf"\tfrac{{1}}{{{fmt(pb.data)}}}={fmt(pa.grad)},\ \ -\tfrac{{{fmt(pa.data)}}}{{{fmt(pb.data**2)}}}={fmt(pb.grad)}"),
            (r"a-b=a+(-b)",
             rf"\text{{grads}}\ {fmt(sa.grad)},\ {fmt(sb.grad)}"),
            (r"-a=a\cdot(-1)",
             rf"\text{{grad}}={fmt(na.grad)}"),
        ]
        names = ["exp", "power", "divide", "subtract", "negate"]
        nar.say("Each new operation needs only a forward value and a local slope.")
        group = VGroup()
        for i, ((rule, work), nm) in enumerate(zip(rows, names)):
            y = 2.3 - 0.85 * i
            label = Text(nm, font_size=26, color=SECOND).move_to([-6.0, y, 0], aligned_edge=LEFT)
            r = MathTex(rule, font_size=38, color=FWD)
            r.scale_to_fit_width(min(r.width, 4.6))
            r.move_to([-1.9, y, 0])
            w = MathTex(work, font_size=36, color=WHITE)
            w.scale_to_fit_width(min(w.width, 5.0))
            w.move_to([4.0, y, 0])
            self.play(FadeIn(label), FadeIn(r), run_time=0.7)
            self.play(FadeIn(w), run_time=0.7)
            group.add(label, r, w)
            self.wait(1.2)
            if i == 1:
                nar.say("Division and subtraction need nothing new: they reuse power, plus and times.")
        self.play(Indicate(group[7], color=ACTIVE), run_time=1.0)  # the division recipe
        self.wait(1.5)
        self.play(FadeOut(group), run_time=0.6)

        # (4) tanh from pieces
        fused, pcs = neuron(False), neuron(True)
        for d in (fused, pcs):
            d["o"].backward()
        assert abs(fused["o"].data - pcs["o"].data) < 1e-9
        assert abs(fused["o"].data - 0.7071) < 1e-4
        for k in ("x1", "w1", "x2", "w2"):
            assert abs(fused[k].grad - pcs[k].grad) < 1e-9
        n_fused, n_pieces = len(fused["o"].topo()), len(pcs["o"].topo())
        ops_pieces = len([v for v in pcs["o"].topo() if v._op]) - len([v for v in fused["o"].topo() if v._op]) + 1
        assert ops_pieces == 6
        nar.say("Back to the neuron. Can tanh be rebuilt from exp, plus and times?")
        # fused row
        cn = chip("n", fused["n"].data, fused["n"].grad).move_to([-5.9, 2.3, 0])
        co = chip("tanh = o", fused["o"].data, fused["o"].grad, w=1.9).move_to([-3.1, 2.3, 0])
        self.play(FadeIn(cn), FadeIn(co), Create(arrow_between(cn, co)), run_time=1.0)
        fl_title = Text("one fused tanh node", font_size=24, color=SECOND).next_to(co, RIGHT, buff=0.3)
        self.play(FadeIn(fl_title), run_time=0.5)
        # exploded row built from the engine's own nodes
        pos = {"n": [-5.9, -0.6], "t": [-3.7, -0.6], "e": [-1.5, -0.6], "u": [0.7, 0.3],
               "v": [0.7, -1.5], "w": [3.0, -1.5], "o": [5.4, -0.6]}
        ops = {"n": "n", "t": "*2", "e": "exp", "u": "+(-1)", "v": "+1", "w": "**-1", "o": "* = o"}
        chips = {k: chip(ops[k], pcs[k].data, 0.0).move_to([*pos[k], 0]) for k in pos}
        edges = [("n", "t"), ("t", "e"), ("e", "u"), ("e", "v"), ("v", "w"), ("u", "o"), ("w", "o")]
        arrows = {ed: arrow_between(chips[ed[0]], chips[ed[1]]) for ed in edges}
        self.play(FadeIn(chips["n"]), run_time=0.6)
        nar.say("Yes: n times 2, then exp, then minus 1 and plus 1, then divide.")
        for col in (["t"], ["e"], ["u", "v"], ["w"], ["o"]):
            ins = [arrows[ed] for ed in edges if ed[1] in col]
            fl, dots = self.flows(ins, FWD, False)
            self.play(*[FadeIn(chips[k]) for k in col], *[Create(a) for a in ins], *fl, run_time=1.0)
            self.drop(fl, dots)
        self.wait(0.8)
        self.zoom_on(VGroup(chips["u"], chips["v"], chips["w"]), 0.55, 2.5)
        nar.say("Six small nodes do the work of one. Watch the gradient flow back.")
        self.wait(0.5)
        # stepwise real backward on the pieces graph
        inst = neuron(True)
        inst["o"].grad = 1.0
        chips["o"].g.become(Text(fmt(1.0), font_size=24, color=GRAD).move_to(chips["o"].g))
        for key in ("o", "w", "v", "u", "e", "t"):
            v = inst[key]
            v._backward()
            kids = [k for k in "ntevuwo" if k != key and inst[k] in v._prev]
            arrs = [arrows[(k, key)] for k in kids]
            fl, dots = self.flows(arrs, BWD, True, rt=0.7)
            self.play(chips[key].box.animate.set_stroke(BWD, width=6), *fl,
                      *[self.new_grad(chips[k], inst[k].grad) for k in kids], run_time=1.0)
            self.drop(fl, dots)
            self.play(chips[key].box.animate.set_stroke(WHITE, width=2), run_time=0.2)
        for v in reversed(inst["o"].topo()):
            if v not in [inst[k] for k in "otwvue"] and v is not inst["t"]:
                v._backward()
        self.play(Indicate(chips["n"], color=ACTIVE), run_time=1.0)
        assert abs(inst["x1"].grad - fused["x1"].grad) < 1e-9
        lines = VGroup(
            Text("x1, w1, x2, w2 grads", font_size=24, color=SECOND),
            Text("fused:   " + ", ".join(fmt(fused[k].grad) for k in ("x1", "w1", "x2", "w2")),
                 font_size=26, color=GRAD),
            Text("pieces:  " + ", ".join(fmt(inst[k].grad) for k in ("x1", "w1", "x2", "w2")),
                 font_size=26, color=GRAD),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT).move_to([4.4, 2.2, 0])
        nar.say("Same value 0.7071, same gradients: the size of an operation does not matter.")
        self.play(FadeIn(lines), run_time=0.8)
        self.wait(2.5)
        c2 = self.show_callout("The lecture's point",
                               f"{n_fused} nodes or {n_pieces}: same gradients, if local slopes are right.",
                               [0, -2.0, 0], width=11.0)
        self.play(FadeOut(c2), run_time=0.4)
        self.stats = (n_fused, n_pieces)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        self.clear_stage()
        tag = self.open_act("Example B: what if we build a sigmoid from the same pieces?",
                            "Example B: sigmoid from exp", "Example B:")
        c = self.show_callout("Sigmoid", "Squashes any number into the range 0 to 1.", [0, 1.8, 0])
        self.play(FadeOut(c), run_time=0.4)
        axes = Axes(x_range=[-4, 4, 2], y_range=[-1, 1, 1], x_length=6.6, y_length=3.2,
                    axis_config={"color": GREY_B, "include_ticks": True, "tick_size": 0.06})
        axes.move_to([-3.1, -0.3, 0])
        axes.x_axis.add_numbers([-4, -2, 0, 2, 4], font_size=24)
        axes.y_axis.add_numbers([-1, 0, 1], font_size=24)
        xlab = Text("x", font_size=26, color=WHITE).next_to(axes.x_axis, RIGHT, buff=0.1)
        ylab = Text("output", font_size=24, color=WHITE).next_to(axes.y_axis, UP, buff=0.1)
        sig_curve = axes.plot(lambda x: sig(x), x_range=[-4, 4], color=DATA, stroke_width=5)
        form = MathTex(r"\sigma(x)=\frac{1}{1+e^{-x}}", font_size=44, color=WHITE).move_to([-3.0, 2.55, 0])
        nar.say("Sigmoid needs only exp, plus, times and power: 1 over 1 + e^-x.")
        self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=1.2)
        self.play(Create(sig_curve), FadeIn(form), run_time=1.5)

        t = ValueTracker(1.0)
        dot = always_redraw(lambda: Dot(axes.c2p(t.get_value(), sig(t.get_value())), radius=0.1, color=ACTIVE))
        tang = always_redraw(lambda: Line(
            axes.c2p(t.get_value() - 0.9, sig(t.get_value()) - 0.9 * sig_slope(t.get_value())),
            axes.c2p(t.get_value() + 0.9, sig(t.get_value()) + 0.9 * sig_slope(t.get_value())),
            color=GRAD, stroke_width=4))
        self.play(FadeIn(dot), run_time=0.5)

        chain = sigmoid_chain(1.0)
        keys = ["x", "m", "e", "p", "s"]
        ops = {"x": "x", "m": "*(-1)", "e": "exp", "p": "+1", "s": "**-1 = s"}
        ys = [2.3, 1.25, 0.2, -0.85, -1.9]
        chips = {k: chip(ops[k], chain[k].data, 0.0, compact=True, w=3.2).move_to([4.7, y, 0])
                 for k, y in zip(keys, ys)}
        arrows = {(a, b): arrow_between(chips[a], chips[b]) for a, b in zip(keys, keys[1:])}
        nar.say("Predict: how steep is the sigmoid at x = 1? Above 0.25, or below?")
        q = self.pulse_question("slope at x = 1?", [-3.0, 2.55, 0], [-0.4, 1.6, 0])
        self.play(FadeOut(form), run_time=0.3)
        self.play(FadeOut(q), run_time=0.4)
        nar.say("The same x flows through four small nodes and gives s = 0.7311.")
        self.play(FadeIn(chips["x"]), run_time=0.5)
        for a, b in zip(keys, keys[1:]):
            fl, dots = self.flows([arrows[(a, b)]], FWD, False, rt=0.6)
            self.play(Create(arrows[(a, b)]), FadeIn(chips[b]), *fl, run_time=0.8)
            self.drop(fl, dots)
        s_val = chain["s"].data
        assert abs(s_val - 0.7311) < 1e-4
        self.play(Indicate(chips["s"], color=ACTIVE), run_time=0.8)
        # real backward, node by node
        chain["s"].grad = 1.0
        chips["s"].g.become(Text(fmt(1.0), font_size=24, color=GRAD).move_to(chips["s"].g))
        nar.say("Backward, each node multiplies in its own slope, as in chapter 4.")
        for k, kid in zip(reversed(keys[1:]), reversed(keys[:-1])):
            chain[k]._backward()
            fl, dots = self.flows([arrows[(kid, k)]], BWD, True, rt=0.6)
            self.play(*fl, self.new_grad(chips[kid], chain[kid].grad), run_time=0.9)
            self.drop(fl, dots)
        g1 = chain["x"].grad
        assert abs(g1 - 0.1966) < 1e-4 and abs(g1 - s_val * (1 - s_val)) < 1e-9
        assert abs(g1 - sig_slope(1.0)) < 1e-12
        nar.say("Out comes 0.1966, which is exactly s times one minus s: a neat shortcut.")
        res = working_line(self, r"s\,(1-s)", rf"{fmt(s_val)}\,(1-{fmt(s_val)})", rf"{fmt(g1)}",
                           pos=[-3.0, 2.55, 0], width=5.8)
        self.play(FadeIn(tang), run_time=0.8)
        self.wait(1.0)
        self.play(FadeOut(res), run_time=0.4)

        # slide the dot: the slope flattens at the ends
        nar.say("Slide the dot: the tangent flattens far from zero, so gradients vanish.")
        self.play(t.animate.set_value(3.5), run_time=2.5)
        self.play(t.animate.set_value(-3.5), run_time=3.5)
        self.play(t.animate.set_value(0.0), run_time=2.0)
        self.wait(1.0)
        # relation to tanh
        tanh_curve = axes.plot(lambda x: Value(x).tanh().data, x_range=[-4, 4], color=FWD, stroke_width=5)
        for xv in (-2.0, -0.7, 0.0, 0.7, 2.0):
            assert abs(tanh_from_sigmoid(xv) - math.tanh(xv)) < 1e-12
        leg = VGroup(Text("sigmoid", font_size=24, color=DATA), Text("tanh", font_size=24, color=FWD)
                     ).arrange(DOWN, buff=0.1, aligned_edge=LEFT).move_to(axes.c2p(-3.0, 0.7))
        nar.say("Now compare it with tanh from chapter 5: same S shape, but from -1 to 1.")
        self.play(FadeOut(tang), FadeOut(dot), Create(tanh_curve), FadeIn(leg), run_time=1.5)
        self.wait(1.0)
        morph = axes.plot(lambda x: tanh_from_sigmoid(x), x_range=[-4, 4], color=ACTIVE, stroke_width=5)
        f1 = MathTex(r"\sigma(x)", font_size=44, color=DATA).move_to([-3.0, 2.55, 0])
        f2 = MathTex(r"2\,\sigma(2x)-1", font_size=44, color=ACTIVE).move_to([-3.0, 2.55, 0])
        f3 = MathTex(r"\tanh(x)=2\,\sigma(2x)-1", font_size=44, color=WHITE).move_to([-3.0, 2.55, 0])
        nar.say("Squeeze sigmoid sideways by 2, double it, subtract 1: it is tanh.")
        self.play(FadeIn(f1), run_time=0.5)
        self.play(Transform(sig_curve, morph), TransformMatchingTex(f1, f2), run_time=3.0)
        self.wait(1.0)
        self.play(TransformMatchingTex(f2, f3), run_time=1.5)
        self.wait(2.5)
        self.play(Indicate(tanh_curve, color=ACTIVE), run_time=1.0)
        self.wait(1.0)

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        self.clear_stage()
        tag = self.open_act("Expert corner: what happens when the rebuilt tanh gets a huge input?",
                            "Expert corner: numerical stability", "Expert corner:")
        x = Value(400.0)
        kind, msg = error_text(lambda: naive_tanh(x))
        assert kind == "OverflowError" and "range" in msg
        fused_out = Value(400.0).tanh().data
        assert fused_out == 1.0
        t_star = overflow_point()
        assert 709.7 < t_star < 709.9
        lim = math.log10(sys.float_info.max)
        panel = self.placed(CODE_NAIVE, 2, 6.0, [3.7, 2.0, 0])
        q = self.pulse_question("tanh(400) from the pieces?", [0, 2.2, 0], [0, 0.8, 0])
        nar.say("Predict: what does the six-node tanh return for x = 400?")
        self.play(FadeOut(q), run_time=0.4)
        axes = Axes(x_range=[0, 800, 200], y_range=[0, 400, 100], x_length=5.6, y_length=3.0,
                    axis_config={"color": GREY_B, "include_ticks": True, "tick_size": 0.06})
        axes.move_to([-3.6, 0.0, 0])
        axes.x_axis.add_numbers([0, 200, 400, 600, 800], font_size=24)
        axes.y_axis.add_numbers([0, 100, 200, 300], font_size=24)
        xlab = MathTex(r"2x", font_size=34).next_to(axes.x_axis, RIGHT, buff=0.1)
        ylab = MathTex(r"\log_{10} e^{2x}", font_size=34).next_to(axes.y_axis, UP, buff=0.1).shift(RIGHT * 0.9)
        ln = axes.plot(lambda v: v * math.log10(math.e), x_range=[0, 800], color=DATA, stroke_width=5)
        limit = DashedLine(axes.c2p(0, lim), axes.c2p(800, lim), color=RED)
        lim_t = Text("largest float", font_size=24, color=RED).next_to(limit, UP, buff=0.08).align_to(limit, LEFT)
        nar.say("The pieces need e^(2x), which grows too fast for a float to hold.")
        self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), FadeIn(panel), run_time=1.5)
        self.play(Create(ln), Create(limit), FadeIn(lim_t), run_time=1.5)
        tr = ValueTracker(0.0)
        dot = always_redraw(lambda: Dot(axes.c2p(tr.get_value(), tr.get_value() * math.log10(math.e)),
                                        radius=0.1, color=ACTIVE))
        self.add(dot)
        self.play(tr.animate.set_value(t_star), run_time=3.0, rate_func=linear)
        cross = Cross(Dot(axes.c2p(t_star, lim), radius=0.18), stroke_color=RED, stroke_width=6)
        self.play(Create(cross), run_time=0.5)
        self.play(Indicate(dot, color=RED), run_time=0.8)
        err = self.error_box(kind, msg, [3.7, -0.3, 0])
        nar.say(f"Past 2x = {t_star:.2f} exp raises OverflowError, so x = 400 crashes.")
        self.play(FadeIn(err), run_time=0.8)
        self.wait(2.5)
        c = self.show_callout("Overflow", "A number too big for a float: Python raises an error.",
                              [3.7, -2.0, 0], color=RED, width=6.4)
        self.play(FadeOut(c), run_time=0.4)

        # stable rewrite
        st = stable_tanh(Value(400.0))
        z_val = math.exp(-800.0)
        assert st.data == 1.0
        x2 = Value(0.5)
        a, b = stable_tanh(x2), Value(0.5).tanh()
        a.backward()
        b.backward()
        assert abs(a.data - b.data) < 1e-12 and abs(x2.grad - (1 - b.data**2)) < 1e-12
        stable = self.placed(CODE_STABLE, 1, 6.0, [3.7, 1.9, 0])
        nar.say("Fix: divide top and bottom by e^(2x), so only negative powers remain.")
        self.play(FadeOut(err), FadeOut(panel), FadeIn(stable), run_time=0.8)
        res = working_line(
            self, r"\frac{1-e^{-2x}}{1+e^{-2x}}",
            rf"\frac{{1-e^{{-{fmt(2 * 400)}}}}}{{1+e^{{-{fmt(2 * 400)}}}}}",
            rf"\frac{{1-{fmt(z_val)}}}{{1+{fmt(z_val)}}}={fmt(st.data)}",
            pos=[3.7, -0.4, 0], width=6.0)
        nar.say("The tiny power rounds to 0, so the answer is exactly 1, like fused tanh.")
        self.play(Indicate(res, color=ACTIVE), run_time=1.0)
        self.wait(1.5)

        # fusing: fewer nodes
        self.clear_stage()
        n_fused, n_pieces = self.stats
        nar.say("So frameworks fuse operations: fewer nodes, less memory, safer maths.")
        base = Line([-4.5, -1.8, 0], [4.5, -1.8, 0], color=GREY_B)
        scale = 3.0 / n_pieces
        bars = VGroup()
        labels = VGroup()
        for i, (name, cnt, col) in enumerate([("fused tanh", n_fused, FWD), ("from pieces", n_pieces, DATA)]):
            cx = -2.0 + 4.0 * i
            r = Rectangle(width=1.8, height=cnt * scale, fill_color=col, fill_opacity=0.85, stroke_width=0)
            r.move_to([cx, -1.8 + cnt * scale / 2, 0])
            nm = Text(name, font_size=26, color=WHITE).next_to(r, DOWN, buff=0.15)
            num = Text(f"{cnt} nodes", font_size=28, color=ACTIVE).next_to(r, UP, buff=0.15)
            bars.add(r)
            labels.add(nm, num)
        self.play(Create(base), run_time=0.5)
        self.play(GrowFromEdge(bars[0], DOWN), GrowFromEdge(bars[1], DOWN), run_time=1.5)
        self.play(FadeIn(labels), run_time=0.8)
        self.wait(2.0)
        q = MathTex(r"\text{nodes saved}=" + f"{n_pieces}-{n_fused}={n_pieces - n_fused}",
                    font_size=40, color=ACTIVE).move_to([0, 2.7, 0])
        self.play(FadeIn(q), run_time=0.8)
        self.play(Indicate(bars[1], color=ACTIVE), run_time=1.0)
        self.wait(2.5)
