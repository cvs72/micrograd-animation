from manim import *

from micrograd_animation.anim import (
    ACTIVE, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, fmt,
    make_value_node, particle_flow, recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value

LIGHT = BLUE_B  # readable data colour on black
B_NICE = 6.8813735870195432  # the lecture's bias, chosen so that o = 0.7071
SC = 0.66
RS = 0.85 # node scale in the ReLU panels
NAME = {"s": "x1w1+x2w2"}
POS = {
    "x1": [-5.64, 1.95, 0], "w1": [-5.64, 0.95, 0], "x2": [-5.64, -0.05, 0], "w2": [-5.64, -1.05, 0],
    "x1w1": [-2.82, 1.45, 0], "x2w2": [-2.82, -0.55, 0], "s": [0.0, 0.45, 0], "b": [0.0, -1.55, 0],
    "n": [2.82, 0.45, 0], "o": [5.64, 0.45, 0],
}
SPOT = [3.1, 2.5, 0]  # callouts, workings and questions while the graph is up
BAND = [1.2, 3.05, 0]  # same, when the top band is free


def neuron(x1=2.0, x2=0.0, w1=-3.0, w2=1.0, b=B_NICE, backward=True):
    """The lecture's neuron built from Values; leaves x1, w1, x2, w2, b."""
    v = {k: Value(val, label=k) for k, val in zip(("x1", "w1", "x2", "w2", "b"), (x1, w1, x2, w2, b))}
    v["x1w1"] = v["x1"] * v["w1"]
    v["x2w2"] = v["x2"] * v["w2"]
    v["s"] = v["x1w1"] + v["x2w2"]
    v["n"] = v["s"] + v["b"]
    v["o"] = v["n"].tanh()
    for k, val in v.items():
        val.label = k
    if backward:
        v["o"].backward()
    return v


def tanh_val(n):
    return Value(n).tanh().data


def tanh_grad(n):
    """Local derivative of tanh at n, taken from the engine's backward pass."""
    x = Value(n)
    x.tanh().backward()
    return x.grad


def p(x):
    return f"({fmt(x)})" if x < 0 else fmt(x)


def mk(k, data, grad, pos=None, scale=SC):
    n = make_value_node(NAME.get(k, k), data, grad, width=2.6).scale(scale)
    return n.move_to(POS[k] if pos is None else pos)


def op_circle(op):
    """Operation circle: a drawing helper (draw_dot), NOT a Value."""
    c = Circle(radius=0.24, color=SECOND, stroke_width=3, fill_color=BLACK, fill_opacity=1)
    if op == "tanh":
        return VGroup(c, Text("tanh", font_size=24, color=FWD).next_to(c, UP, buff=0.08))
    return VGroup(c, Text("*" if op == "*" else "+", font_size=28, color=WHITE).move_to(c))


def build_graph(vals, blank=True):
    """Nodes, op circles and arrows. blank=True shows 0 in every non-leaf data field."""
    nodes = {k: mk(k, 0.0 if (blank and v._op) else v.data, 0.0) for k, v in vals.items()}
    ops, arrows = {}, {}
    kw = dict(buff=0.04, color=FWD, stroke_width=4, tip_length=0.14)
    for k, v in vals.items():
        if not v._op:
            continue
        kids = sorted((ch.label for ch in v._prev), key=lambda n: -POS[n][1])
        right = max(nodes[n].get_right()[0] for n in kids)
        x = (right + nodes[k].get_left()[0]) / 2
        circ = op_circle("tanh" if v._op == "tanh" else v._op).move_to([x, POS[k][1], 0])
        if v._op == "tanh":
            circ.move_to([x, POS[k][1] + 0.0, 0])
        ops[k] = circ
        ring = circ[0]
        arr = []
        for n in kids:
            start = nodes[n].get_right()
            d = start - ring.get_center()
            d = d / np.linalg.norm(d)
            arr.append(Arrow(start, ring.get_center() + 0.24 * d, **kw))
        arr.append(Arrow(ring.get_center() + [0.24, 0, 0], nodes[k].get_left(), **kw))
        arrows[k] = arr
    return nodes, ops, arrows


def node_anims(nodes, vals, names, data=True, grad=True):
    out = []
    for k in names:
        n2 = mk(k, vals[k].data, vals[k].grad)
        if data:
            out.append(Transform(nodes[k].data_t, n2.data_t))
        if grad:
            out.append(Transform(nodes[k].grad_t, n2.grad_t))
    return out


def graph_group(nodes, ops, arrows):
    return VGroup(*nodes.values(), *ops.values(), *[a for l in arrows.values() for a in l])


def tanh_axes(x_range, length, height):
    ax = Axes(x_range=[x_range[0], x_range[1], 2], y_range=[-1.25, 1.25, 1], x_length=length,
              y_length=height, tips=False,
              axis_config={"font_size": 24, "color": GREY_B, "include_numbers": True,
                           "decimal_number_config": {"num_decimal_places": 0}})
    labels = ax.get_axis_labels(x_label=MathTex(r"n", font_size=36),
                                y_label=MathTex(r"\tanh(n)", font_size=34))
    return ax, labels


class Scene05NeuronTanh(Scene):
    # ---------------------------------------------------------------- helpers
    def tag(self, text):
        return Tex(r"\textbf{" + text + "}", font_size=34, color=ACTIVE).to_corner(UL, buff=0.5)

    def pulse_question(self, text, pos=SPOT, n=3, wide=False):
        """Predict-then-reveal: question plus a pulsing question mark, held about 3 s."""
        q = Text(text, font_size=30, color=WHITE).move_to(pos)
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).next_to(q, RIGHT, buff=0.3)
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        self.play(FadeOut(VGroup(q, qm)), run_time=0.4)

    def flow(self, arrows, mags, reverse=True, color=GRAD, run_time=0.9):
        fls = [particle_flow(a, m, color=color, n=2, reverse=reverse, run_time=run_time)
               for a, m in zip(arrows, mags)]
        dots = VGroup(*[f.dots for f in fls])
        self.add(dots)
        self.play(*fls)
        self.remove(dots, *dots.submobjects, *[f.mobject for f in fls])
        self.remove(*[d for f in fls for d in f.dots.submobjects])

    def recolour(self, arrows, color):
        self.play(*[a.animate.set_color(color) for a in arrows], run_time=0.4)

    def back_through(self, k, arrows, vals, color=GRAD):
        arr = arrows[k]
        kids = sorted((ch.label for ch in vals[k]._prev), key=lambda n: -POS[n][1])
        self.flow(arr[-1:], [vals[k].grad], reverse=True, color=color)
        self.flow(arr[:-1], [vals[n].grad for n in kids], reverse=True, color=color)
        self.recolour(arr, GRAD)

    def fwd_through(self, k, arrows):
        self.recolour(arrows[k], FWD)
        self.flow(arrows[k], [1.0] * len(arrows[k]), reverse=False, color=FWD, run_time=0.8)

    def show_callout(self, title, body, pos=SPOT, color=ACTIVE, hold=3.2, width=6.2):
        c = callout(title, body, color=color, width=width).move_to(pos)
        self.play(FadeIn(c), run_time=0.5)
        self.wait(hold)
        self.play(FadeOut(c), run_time=0.4)

    def work(self, symbolic, substituted, result, pos=SPOT, width=6.4, fly_to=None):
        w = working_line(self, symbolic, substituted, result, pos=pos, width=width, hold=1.6,
                         colors=(WHITE, WHITE, GRAD))
        if fly_to is not None:
            self.play(w.animate.move_to(fly_to).scale(0.3).set_opacity(0.0), run_time=0.6)
        else:
            self.play(FadeOut(w), run_time=0.4)

    def set_grad(self, nodes, vals, names, indicate=None):
        self.play(*node_anims(nodes, vals, names, data=False), run_time=0.9)
        self.play(*[Indicate(nodes[k], color=ACTIVE) for k in (indicate or names)], run_time=0.9)

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S05")
        title_card(self, "Chapter 5", "What does one neuron do, and what is tanh for?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        recap_line(self, "Next: can the computer run every backward step for us?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def sketch(self, nar):
        """The lecture's biological cartoon, drawn with shapes."""
        def inp(name, pos):
            c = Circle(radius=0.45, color=DATA, stroke_width=4).move_to(pos)
            return VGroup(c, MathTex(name, font_size=40, color=LIGHT).move_to(c))
        i1, i2 = inp("x_1", [-5.2, 1.2, 0]), inp("x_2", [-5.2, -1.0, 0])
        body = Circle(radius=1.05, color=WHITE, stroke_width=4).move_to([-0.6, 0.1, 0])
        body_t = MathTex(r"\sum w_i x_i + b", font_size=34).move_to(body)
        squash = RoundedRectangle(corner_radius=0.2, width=1.9, height=1.1, color=FWD,
                                  stroke_width=4).move_to([3.0, 0.1, 0])
        squash_t = MathTex(r"\tanh", font_size=40, color=FWD).move_to(squash)
        out = Circle(radius=0.45, color=GRAD, stroke_width=4).move_to([5.7, 0.1, 0])
        out_t = MathTex(r"o", font_size=40, color=WHITE).move_to(out)
        kw = dict(buff=0.05, stroke_width=4, tip_length=0.18)
        a1 = Arrow(i1.get_right(), body.get_critical_point([-0.9, 0.5, 0]), color=FWD, **kw)
        a2 = Arrow(i2.get_right(), body.get_critical_point([-0.9, -0.5, 0]), color=FWD, **kw)
        w1 = MathTex(r"w_1", font_size=36, color=LIGHT).next_to(a1, UP, buff=0.05).shift(LEFT * 0.2)
        w2 = MathTex(r"w_2", font_size=36, color=LIGHT).next_to(a2, DOWN, buff=0.05).shift(LEFT * 0.2)
        a3 = Arrow(body.get_right(), squash.get_left(), color=FWD, **kw)
        a4 = Arrow(squash.get_right(), out.get_left(), color=FWD, **kw)

        def label(text, color=WHITE):
            return Text(text, font_size=30, color=color).move_to([0.6, 2.6, 0])

        nar.say("Example A: a neuron takes numbers in and gives one number out.")
        self.play(FadeIn(i1), FadeIn(i2), run_time=0.8)
        l1 = label("Synapses multiply each input by a weight")
        self.play(Create(a1), Create(a2), FadeIn(w1), FadeIn(w2), FadeIn(l1), run_time=1.5)
        self.play(Indicate(w1, color=ACTIVE), Indicate(w2, color=ACTIVE), run_time=1.0)
        nar.say("Each weight scales its input: a big weight makes that input matter more.")
        self.wait(1.0)
        l2 = label("The cell body adds them up, plus a bias")
        self.play(FadeIn(body), FadeIn(body_t), FadeTransform(l1, l2), run_time=1.2)
        self.play(Indicate(body, color=ACTIVE), run_time=1.0)
        self.show_callout("Bias", "the neuron's innate trigger happiness", pos=[0.6, -2.0, 0])
        nar.say("The bias shifts the sum up or down, whatever the inputs say.")
        l3 = label("An activation function squashes the result", color=FWD)
        self.play(Create(a3), FadeIn(squash), FadeIn(squash_t), FadeTransform(l2, l3), run_time=1.2)
        self.play(Create(a4), FadeIn(out), FadeIn(out_t), run_time=1.0)
        self.show_callout("Activation function", "squashes n into a fixed range", pos=[0.6, -2.0, 0])
        self.play(*[FadeOut(m) for m in (i1, i2, body, body_t, squash, squash_t, out, out_t, a1, a2,
                                         a3, a4, w1, w2, l3)], run_time=0.8)

    def tanh_plot(self, nar):
        """Axes plot of tanh with a sliding dot: bias 8 gives n = 2 in the flat tail."""
        v8 = neuron(b=8.0)
        assert v8["n"].data == 2.0 and round(v8["o"].data, 4) == 0.9640
        ax, labs = tanh_axes((-5, 5), 8.0, 3.4)
        ax.move_to([-1.2, -0.2, 0])
        labs = ax.get_axis_labels(x_label=MathTex(r"n", font_size=36),
                                  y_label=MathTex(r"\tanh(n)", font_size=34))
        curve = ax.plot(lambda x: tanh_val(x), x_range=[-5, 5], color=DATA, stroke_width=5)
        t = ValueTracker(0.0)
        dot = always_redraw(lambda: Dot(ax.c2p(t.get_value(), tanh_val(t.get_value())), radius=0.12,
                                        color=ACTIVE))
        drop = always_redraw(lambda: DashedLine(ax.c2p(t.get_value(), 0),
                                                ax.c2p(t.get_value(), tanh_val(t.get_value())),
                                                color=ACTIVE, stroke_width=3))

        def readout():
            n = t.get_value()
            return VGroup(Text(f"n = {fmt(n)}", font_size=30, color=LIGHT),
                          Text(f"tanh(n) = {fmt(tanh_val(n))}", font_size=30, color=WHITE)
                          ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([5.1, 0.6, 0])
        ro = always_redraw(readout)
        nar.say("The squashing function tanh maps any number into the range minus 1 to 1.")
        self.play(Create(ax), FadeIn(labs), run_time=1.2)
        self.play(Create(curve), run_time=1.5)
        self.add(drop, dot, ro)
        self.wait(1.0)
        self.show_callout("tanh", "squashes any n into -1 to 1", pos=[2.8, 2.5, 0])
        nar.say("Big inputs flatten toward 1 and big negative inputs toward minus 1.")
        self.play(t.animate.set_value(4.5), run_time=2.5)
        self.play(t.animate.set_value(-4.5), run_time=3.0)
        self.play(t.animate.set_value(0.0), run_time=1.5)
        nar.say("Predict: with bias 8 the sum is n = 2. Is tanh(2) near 2 or near 1?")
        self.pulse_question("n = 2: is tanh(2) near 2, or near 1?", pos=[0.2, 2.75, 0])
        self.play(t.animate.set_value(2.0), run_time=1.5)
        self.play(Indicate(dot, color=ACTIVE, scale_factor=2.0), run_time=1.0)
        nar.say("It is 0.9640: already in the flat tail, so the output barely moves.")
        self.work(r"o=\tanh(n)", rf"o=\tanh({fmt(v8['n'].data)})", rf"o={fmt(v8['o'].data)}",
                  pos=[3.1, 2.5, 0])
        self.wait(0.5)
        self.remove(drop, dot, ro)
        self.play(*[FadeOut(m) for m in (ax, labs, curve)], run_time=0.8)

    def act_a(self, nar):
        nar.say("Example A: the lecture's neuron, first as a cartoon of a brain cell.")
        act_banner(self, "Example A: one neuron", hold=2.6)
        tag = self.tag("Example A:")
        self.play(FadeIn(tag), run_time=0.4)
        self.sketch(nar)
        self.tanh_plot(nar)

        # --- the graph, bias 8 first
        v8 = neuron(b=8.0)
        va = neuron()
        want = {"x1": -1.5, "w1": 1.0, "x2": 0.5, "w2": 0.0}
        got = {"x1": va["x1"].grad, "w1": va["w1"].grad, "x2": va["x2"].grad, "w2": va["w2"].grad}
        assert round(va["n"].data, 4) == 0.8814 and round(va["o"].data, 4) == 0.7071
        assert all(abs(got[k] - want[k]) < 1e-4 for k in want), got
        nar.say("Now the same neuron as Value nodes: inputs, weights and a bias of 8.")
        nodes, ops, arrows = build_graph(v8, blank=True)
        title = MathTex(r"o=\tanh(x_1w_1+x_2w_2+b)", font_size=40).move_to([2.6, 2.7, 0])
        group = graph_group(nodes, ops, arrows)
        self.play(FadeIn(group), FadeIn(title), run_time=1.2)
        self.wait(1.0)
        self.group, self.tag_now = group, tag
        nar.say("The forward pass fills in each number, column by column, left to right.")
        self.play(FadeOut(title), run_time=0.3)
        for k in ("x1w1", "x2w2", "s", "n", "o"):
            self.fwd_through(k, arrows)
            self.play(*node_anims(nodes, v8, [k], grad=False), run_time=0.7)
        self.wait(0.5)
        nar.say("With bias 8 the sum is 2 and tanh gives 0.9640, as in the plot.")
        self.play(Indicate(nodes["n"], color=ACTIVE), Indicate(nodes["o"], color=ACTIVE), run_time=1.2)
        self.wait(1.0)

        # --- morph the bias to the lecture's value
        nar.say("Predict: lower the bias to 6.8814. Does o go up or down from 0.9640?")
        self.pulse_question("b: 8 to 6.8814. Does o rise or fall?")
        nodes_b = node_anims(nodes, va, ["b"], grad=False)
        self.play(*nodes_b, run_time=1.2)
        nar.say("The sum drops to 0.8814 and tanh leaves the flat tail: o is 0.7071.")
        for k in ("s", "n", "o"):
            self.fwd_through(k, arrows)
        self.play(*node_anims(nodes, va, ["n", "o"], grad=False), run_time=1.2)
        self.work(r"n=x_1w_1+x_2w_2+b", rf"n=({fmt(va['x1w1'].data)})+{fmt(va['x2w2'].data)}+{fmt(B_NICE)}",
                  rf"n={fmt(va['n'].data)}")
        self.work(r"o=\tanh(n)", rf"o=\tanh({fmt(va['n'].data)})", rf"o={fmt(va['o'].data)}")
        nar.say("tanh is a single node here: it cannot be built from plus and times.")
        self.show_callout("Level of abstraction", "only its local derivative matters", hold=3.4)

        # --- backward pass
        self.backward_a(nar, nodes, ops, arrows, va, group)

    def backward_a(self, nar, nodes, ops, arrows, va, group):
        nar.say("Backward pass: start at the output, where o.grad is 1.")
        self.work(r"\frac{do}{do}=\frac{(o+h)-o}{h}",
                  rf"\frac{{do}}{{do}}=\frac{{({fmt(va['o'].data)}+h)-{fmt(va['o'].data)}}}{{h}}",
                  r"\frac{do}{do}=1")
        self.set_grad(nodes, va, ["o"])
        nar.say("Predict: o is 0.7071. What is one minus o squared?")
        self.pulse_question("o = 0.7071, so 1 - o squared = ?")
        # zoom on the tanh node
        group.save_state()
        keep = [nodes["n"], nodes["o"], ops["o"], *arrows["o"]]
        others = [m for m in group.submobjects if m not in keep]
        centre = nodes["o"].get_center()
        self.play(*[m.animate.set_opacity(0.0) for m in others], run_time=0.6)
        self.play(group.animate.scale(1.3, about_point=centre), run_time=1.2)
        nar.say("The local derivative of tanh is 1 minus o squared.")
        self.back_through("o", arrows, va)
        self.wait(1.0)
        self.play(Restore(group), run_time=1.0)
        loc = 1 - va["o"].data ** 2
        assert abs(loc - 0.5) < 1e-4
        self.work(r"n.grad=(1-o^2)\cdot o.grad",
                  rf"n.grad=(1-{fmt(va['o'].data)}^2)\cdot 1", rf"n.grad={fmt(va['n'].grad)}",
                  fly_to=nodes["n"].get_center())
        self.set_grad(nodes, va, ["n"])

        nar.say("A plus node is a router: it hands the same gradient to both inputs.")
        self.back_through("n", arrows, va)
        self.work(r"s.grad=b.grad=n.grad\cdot 1", rf"s.grad=b.grad={fmt(va['n'].grad)}\cdot 1",
                  rf"s.grad=b.grad={fmt(va['s'].grad)}")
        self.set_grad(nodes, va, ["s", "b"])
        self.back_through("s", arrows, va)
        self.work(r"x_1w_1.grad=x_2w_2.grad=s.grad",
                  rf"x_1w_1.grad=x_2w_2.grad={fmt(va['s'].grad)}",
                  rf"x_1w_1.grad=x_2w_2.grad={fmt(va['x1w1'].grad)}")
        self.set_grad(nodes, va, ["x1w1", "x2w2"])

        nar.say("Predict: x2 is 0 and the product gets 0.5. What is w2.grad?")
        self.pulse_question("x2 = 0 and 0.5 arrives. w2.grad = ?")
        self.back_through("x2w2", arrows, va)
        nar.say("A times node swaps in the other input: w2.grad is x2 times 0.5.")
        self.work(r"w_2.grad=x_2\cdot x_2w_2.grad", rf"w_2.grad={p(va['x2'].data)}\cdot {fmt(va['x2w2'].grad)}",
                  rf"w_2.grad={fmt(va['w2'].grad)}", fly_to=nodes["w2"].get_center())
        self.set_grad(nodes, va, ["w2"])
        self.work(r"x_2.grad=w_2\cdot x_2w_2.grad", rf"x_2.grad={p(va['w2'].data)}\cdot {fmt(va['x2w2'].grad)}",
                  rf"x_2.grad={fmt(va['x2'].grad)}", fly_to=nodes["x2"].get_center())
        self.set_grad(nodes, va, ["x2"])
        nar.say("w2.grad is 0 because x2 is 0: wiggling w2 changes nothing.")
        self.play(Indicate(nodes["w2"].grad_t, color=YELLOW, scale_factor=1.6),
                  Indicate(nodes["x2"].data_t, color=YELLOW, scale_factor=1.6), run_time=1.5)
        self.wait(1.0)

        self.back_through("x1w1", arrows, va)
        nar.say("Same swap for x1: w1.grad is x1 times 0.5, and x1.grad is w1 times 0.5.")
        self.work(r"w_1.grad=x_1\cdot x_1w_1.grad", rf"w_1.grad={p(va['x1'].data)}\cdot {fmt(va['x1w1'].grad)}",
                  rf"w_1.grad={fmt(va['w1'].grad)}", fly_to=nodes["w1"].get_center())
        self.set_grad(nodes, va, ["w1"])
        self.work(r"x_1.grad=w_1\cdot x_1w_1.grad", rf"x_1.grad={p(va['w1'].data)}\cdot {fmt(va['x1w1'].grad)}",
                  rf"x_1.grad={fmt(va['x1'].grad)}", fly_to=nodes["x1"].get_center())
        self.set_grad(nodes, va, ["x1"])
        nar.say("w1.grad is 1.0: to raise this neuron's output, push w1 up.")
        self.play(Circumscribe(nodes["w1"], color=ACTIVE), run_time=1.5)
        self.wait(2.0)
        self.play(FadeOut(group), FadeOut(self.tag_now), run_time=0.8)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        nar.say("Example B: what if the bias is 0, or x2 is 1? Watch the gradients.")
        act_banner(self, "Example B: what if?", hold=2.6)
        tag = self.tag("Example B:")
        self.play(FadeIn(tag), run_time=0.4)

        tb, tx2 = ValueTracker(B_NICE), ValueTracker(0.0)

        def cur():
            return neuron(2.0, tx2.get_value(), -3.0, 1.0, tb.get_value())

        ax = Axes(x_range=[-7, 3, 1], y_range=[-1.25, 1.25, 1], x_length=6.6, y_length=3.2, tips=False,
                  axis_config={"font_size": 24, "color": GREY_B, "include_numbers": True,
                               "decimal_number_config": {"num_decimal_places": 0}}
                  ).move_to([-3.2, -0.1, 0])
        labs = ax.get_axis_labels(x_label=MathTex(r"n", font_size=36),
                                  y_label=MathTex(r"\tanh(n)", font_size=34))
        curve = ax.plot(lambda x: tanh_val(x), x_range=[-7, 3], color=DATA, stroke_width=5)
        dot = always_redraw(lambda: Dot(ax.c2p(cur()["n"].data, cur()["o"].data), radius=0.12,
                                        color=ACTIVE))
        drop = always_redraw(lambda: DashedLine(ax.c2p(cur()["n"].data, 0),
                                                ax.c2p(cur()["n"].data, cur()["o"].data),
                                                color=ACTIVE, stroke_width=3))

        def readout():
            v = cur()
            return VGroup(Text(f"n = {fmt(v['n'].data)}", font_size=26, color=LIGHT),
                          Text(f"o = {v['o'].data:.5f}".rstrip("0"), font_size=26, color=WHITE)
                          ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(ax.c2p(-5.2, 0.85))
        ro = always_redraw(readout)

        # bars of the four leaf gradients, with a grey outline for the "before" state
        zero_y = 0.7
        bx = {"x1": 2.1, "w1": 3.4, "x2": 4.7, "w2": 6.0}

        def bar_rect(g, k, **kw):
            h = max(abs(g), 0.02)
            r = Rectangle(width=0.7, height=h, **kw)
            return r.move_to([bx[k], zero_y + (h / 2 if g >= 0 else -h / 2), 0])

        def bars():
            v = cur()
            return VGroup(*[bar_rect(v[k].grad, k, fill_color=GRAD, fill_opacity=0.9,
                                     stroke_color=WHITE, stroke_width=2) for k in bx])

        def bar_numbers():
            v = cur()
            return VGroup(*[Text(fmt(v[k].grad), font_size=24, color=GRAD).move_to([bx[k], -1.75, 0])
                            for k in bx])
        va = neuron()
        ghost = VGroup(*[bar_rect(va[k].grad, k, fill_opacity=0.0, stroke_color=GREY_B, stroke_width=3)
                         for k in bx])
        zero = Line([1.4, zero_y, 0], [6.5, zero_y, 0], color=GREY_B)
        names = VGroup(*[Text(k, font_size=28, color=WHITE).move_to([bx[k], -1.3, 0]) for k in bx])
        head = Text("gradients of the four inputs", font_size=28, color=GRAD).move_to([4.1, 2.35, 0])
        key = Text("grey outline = before", font_size=24, color=SECOND).move_to([4.1, 1.9, 0])
        bar_live, num_live = always_redraw(bars), always_redraw(bar_numbers)

        nar.say("Same neuron, but now the tanh curve and the four gradients live together.")
        self.play(Create(ax), FadeIn(labs), run_time=1.0)
        self.play(Create(curve), FadeIn(zero), FadeIn(names), FadeIn(head), run_time=1.2)
        self.add(drop, dot, ro, bar_live, num_live)
        self.play(FadeIn(ghost), FadeIn(key), run_time=0.8)
        self.wait(1.5)

        # B1: bias 0
        b1 = neuron(b=0.0)
        loc1 = 1 - b1["o"].data ** 2
        assert b1["n"].data == -6 and round(b1["o"].data, 5) == -0.99999
        assert round(loc1, 6) == 0.000025 and round(b1["x1"].grad, 4) == -0.0001
        nar.say("Predict: set the bias to 0. Will the gradients grow or shrink?")
        self.pulse_question("Bias 0: do the gradients grow or shrink?", pos=BAND)
        nar.say("The sum slides left to n = -6, deep in the flat tail of tanh.")
        self.play(tb.animate.set_value(0.0), run_time=4.0)
        self.play(Indicate(dot, color=ACTIVE, scale_factor=2.0), run_time=1.0)
        self.work(r"1-o^2", rf"1-({b1['o'].data:.5f})^2", rf"\approx {loc1:.6f}", pos=BAND, width=6.5)
        nar.say("The local derivative is almost 0, so every gradient is almost 0.")
        self.show_callout("Saturation", "tanh stuck in a flat tail", pos=[-2.2, 2.75, 0], hold=3.4)
        self.wait(1.5)

        # B2: x2 = 1, bias back to the nice value
        b2 = neuron(x2=1.0)
        loc2 = 1 - b2["o"].data ** 2
        assert round(b2["o"].data, 4) == 0.9546 and round(b2["w2"].grad, 4) == 0.0887
        assert round(b2["x1"].grad, 4) == -0.2661 and round(b2["w1"].grad, 4) == 0.1774
        nar.say("Now restore the bias and give x2 the value 1 instead of 0.")
        self.play(tb.animate.set_value(B_NICE), run_time=2.5)
        nar.say("Predict: x2 goes from 0 to 1. What happens to w2.grad?")
        self.pulse_question("x2: 0 to 1. What happens to w2.grad?", pos=BAND)
        nar.say("The sum rises to 1.8814 and the dot slides right along the curve.")
        self.play(tx2.animate.set_value(1.0), run_time=3.5)
        self.play(Indicate(dot, color=ACTIVE, scale_factor=2.0), run_time=1.0)
        nar.say("w2.grad wakes up: x2 times the local derivative, 1 times 0.0887.")
        self.work(r"w_2.grad=x_2\cdot(1-o^2)",
                  rf"w_2.grad={fmt(b2['x2'].data)}\cdot(1-{fmt(b2['o'].data)}^2)",
                  rf"w_2.grad={fmt(b2['w2'].grad)}", pos=BAND, width=6.5)
        nar.say("x2 now sits closer to the tail, so every gradient is smaller than before.")
        self.play(Indicate(bar_live[3], color=ACTIVE), run_time=1.2)
        self.wait(2.5)
        self.remove(drop, dot, ro, bar_live, num_live)
        self.play(*[FadeOut(m) for m in (ax, labs, curve, zero, names, head, ghost, key, tag)],
                  run_time=0.8)

    # ------------------------------------------------------------------- ACT C
    def relu_panel(self, y0, w, x, title, color):
        """x and w feed p = w*x, then relu. Nodes are Values; returns (vals, group, arrows)."""
        X, W = Value(x, label="x"), Value(w, label="w")
        P = X * W
        P.label = "p"
        R = P.relu()
        R.label = "r"
        R.backward()
        vals = {"x": X, "w": W, "p": P, "r": R}
        pos = {"x": [-1.9, y0 + 0.6, 0], "w": [-1.9, y0 - 0.6, 0], "p": [1.11, y0, 0],
               "r": [4.12, y0, 0]}
        nm = {"x": "x", "w": "w", "p": "p = w*x", "r": "r = relu(p)"}
        nodes = {k: make_value_node(nm[k], 0.0 if k in "pr" else vals[k].data, 0.0, width=2.6)
                 .scale(RS).move_to(pos[k]) for k in vals}
        kw = dict(buff=0.04, color=FWD, stroke_width=4, tip_length=0.14)
        arrows = [Arrow(nodes["x"].get_right(), nodes["p"].get_left() + [0, 0.15, 0], **kw),
                  Arrow(nodes["w"].get_right(), nodes["p"].get_left() + [0, -0.15, 0], **kw),
                  Arrow(nodes["p"].get_right(), nodes["r"].get_left(), **kw)]
        lab = Text(title, font_size=30, color=color, weight=BOLD).move_to([-5.4, y0, 0])
        rl = Text("relu", font_size=24, color=FWD).next_to(arrows[2], UP, buff=0.05)
        grp = VGroup(lab, rl, *nodes.values(), *arrows)
        return vals, nodes, arrows, grp

    def panel_anims(self, vals, nodes, k, data=True, grad=True):
        n2 = make_value_node({"x": "x", "w": "w", "p": "p = w*x", "r": "r = relu(p)"}[k],
                             vals[k].data, vals[k].grad, width=2.6).scale(RS).move_to(nodes[k])
        out = []
        if data:
            out.append(Transform(nodes[k].data_t, n2.data_t))
        if grad:
            out.append(Transform(nodes[k].grad_t, n2.grad_t))
        return out

    def run_panel(self, vals, nodes, arrows):
        self.flow(arrows[:2], [1.0, 1.0], reverse=False, color=FWD, run_time=0.8)
        self.play(*self.panel_anims(vals, nodes, "p", grad=False), run_time=0.7)
        self.flow(arrows[2:], [1.0], reverse=False, color=FWD, run_time=0.8)
        self.play(*self.panel_anims(vals, nodes, "r", grad=False), run_time=0.7)

    def back_panel(self, vals, nodes, arrows):
        self.flow(arrows[2:], [vals["r"].grad], reverse=True, run_time=0.8)
        self.play(*self.panel_anims(vals, nodes, "r", data=False), run_time=0.6)
        self.flow(arrows[:2], [vals["p"].grad] * 2, reverse=True, run_time=0.8)
        self.play(*self.panel_anims(vals, nodes, "p", data=False), run_time=0.6)
        self.play(*self.panel_anims(vals, nodes, "x", data=False), *self.panel_anims(vals, nodes, "w", data=False),
                  run_time=0.8)

    def act_c(self, nar):
        nar.say("Expert corner: tanh gradients vanish in the tails, and ReLU can die.")
        act_banner(self, "Expert corner: vanishing and dead gradients", hold=2.6)
        tag = self.tag("Expert corner:")
        self.play(FadeIn(tag), run_time=0.4)

        # --- tanh and its derivative, flat regions shaded
        ax = Axes(x_range=[-5, 5, 1], y_range=[-1.25, 1.25, 1], x_length=8.6, y_length=3.2, tips=False,
                  axis_config={"font_size": 24, "color": GREY_B, "include_numbers": True,
                               "decimal_number_config": {"num_decimal_places": 0}}).move_to([0, 0.5, 0])
        labs = ax.get_axis_labels(x_label=MathTex(r"n", font_size=36),
                                  y_label=MathTex(r"y", font_size=34))
        x0 = next(x / 100 for x in range(0, 500) if tanh_grad(x / 100) < 0.1)
        assert 1.5 < x0 < 2.0
        c_t = ax.plot(lambda x: tanh_val(x), x_range=[-5, 5], color=DATA, stroke_width=5)
        c_d = ax.plot(lambda x: tanh_grad(x), x_range=[-5, 5], color=GRAD, stroke_width=5)
        lt = MathTex(r"\tanh(n)", font_size=34, color=LIGHT).move_to(ax.c2p(2.3, 0.4))
        ld = MathTex(r"1-\tanh(n)^2", font_size=34, color=GRAD).move_to(ax.c2p(-3.2, 0.9))
        band_r = Rectangle(width=ax.c2p(5, 0)[0] - ax.c2p(x0, 0)[0], height=ax.c2p(0, 1.25)[1] - ax.c2p(0, -1.25)[1],
                           fill_color=RED, fill_opacity=0.18, stroke_width=0
                           ).move_to([(ax.c2p(5, 0)[0] + ax.c2p(x0, 0)[0]) / 2, ax.c2p(0, 0)[1], 0])
        band_l = band_r.copy().move_to([-(band_r.get_center()[0] - ax.c2p(0, 0)[0]) + ax.c2p(0, 0)[0],
                                        ax.c2p(0, 0)[1], 0])
        nar.say("Expert corner: tanh and its slope, 1 minus tanh squared, drawn together.")
        self.play(Create(ax), FadeIn(labs), run_time=1.0)
        self.play(Create(c_t), FadeIn(lt), run_time=1.5)
        self.play(Create(c_d), FadeIn(ld), run_time=1.5)
        self.wait(1.0)
        nar.say("In the red bands the slope is under 0.1: the gradient vanishes.")
        self.play(FadeIn(band_r), FadeIn(band_l), run_time=1.2)
        vt = Text("vanishing", font_size=28, color=RED).move_to(ax.c2p(3.4, -0.55))
        self.play(FadeIn(vt), run_time=0.6)
        self.wait(1.0)
        nar.say("Predict: far out on the tail, is the slope big or tiny?")
        self.pulse_question("At n = 4, is the slope big or tiny?", pos=[0.2, 2.9, 0])
        t = ValueTracker(0.0)
        dd = always_redraw(lambda: Dot(ax.c2p(t.get_value(), tanh_grad(t.get_value())), radius=0.12, color=ACTIVE))
        ro = always_redraw(lambda: Text(f"n = {fmt(t.get_value())}   slope = {tanh_grad(t.get_value()):.4f}",
                                        font_size=28, color=WHITE).move_to([0.2, 2.9, 0]))
        self.add(dd, ro)
        self.play(t.animate.set_value(4.0), run_time=4.0)
        self.play(Indicate(dd, color=ACTIVE, scale_factor=2.0), run_time=1.0)
        s4 = tanh_grad(4.0)
        assert s4 < 0.002
        nar.say("At n = 4 the slope is 0.0013: weights feeding this neuron barely learn.")
        self.show_callout("Vanishing gradient", "slope so small that learning stalls", pos=[0.2, -2.05, 0],
                          hold=3.4)
        nar.say("So the scale of weights and inputs matters: huge sums land in the tails.")
        self.wait(2.0)
        self.remove(dd, ro)
        self.play(*[FadeOut(m) for m in (ax, labs, c_t, c_d, lt, ld, band_r, band_l, vt)], run_time=0.8)

        # --- dead ReLU
        hv, hn, ha, hg = self.relu_panel(1.3, 1.0, 2.0, "healthy ReLU", TEAL)
        dv, dn, da, dg = self.relu_panel(-1.2, -1.0, 2.0, "dead ReLU", RED)
        assert hv["r"].data == 2.0 and hv["x"].grad == 1.0 and hv["w"].grad == 2.0
        assert dv["r"].data == 0.0 and dv["x"].grad == 0.0 and dv["w"].grad == 0.0
        nar.say("ReLU keeps positive numbers and zeroes the negatives. Meet two ReLU neurons.")
        self.play(FadeIn(hg), run_time=1.0)
        self.show_callout("ReLU", "keeps positives, zeroes negatives", pos=[0.0, 3.05, 0], hold=3.2, width=5.4)
        self.run_panel(hv, hn, ha)
        nar.say("The healthy one passes x times w = 2 straight through.")
        self.back_panel(hv, hn, ha)
        self.play(Indicate(hn["w"], color=ACTIVE), run_time=1.0)
        self.wait(1.0)
        nar.say("Predict: now w = -1 and x = 2. Does any gradient get through?")
        self.play(FadeIn(dg), run_time=1.0)
        self.pulse_question("w = -1, x = 2: does any gradient reach w?", pos=[0.2, 2.9, 0])
        self.run_panel(dv, dn, da)
        self.work(r"r=\max(0,\,w\cdot x)", rf"r=\max(0,\,{p(dv['w'].data)}\cdot {fmt(dv['x'].data)})",
                  rf"r={fmt(dv['r'].data)}", pos=[0.0, 2.9, 0], width=6.0)
        stop = MathTex(r"\times", font_size=60, color=RED).move_to(da[2])
        nar.say("The sum is -2, so relu outputs 0 and blocks the backward flow.")
        self.play(FadeIn(stop), run_time=0.6)
        self.back_panel(dv, dn, da)
        self.play(Indicate(dn["w"].grad_t, color=RED, scale_factor=1.6),
                  Indicate(dn["x"].grad_t, color=RED, scale_factor=1.6), run_time=1.5)
        nar.say("Both gradients are exactly 0.0: this neuron can never recover on its own.")
        self.show_callout("Dead ReLU", "zero gradient, so no update, ever", pos=[0.2, 3.05, 0], hold=3.4, width=5.8)
        self.wait(1.5)
        self.play(*[FadeOut(m) for m in (hg, dg, stop, tag)], run_time=0.8)
