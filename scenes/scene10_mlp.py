from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, code_panel, fmt,
    recap_line, title_card, working_line,
)
from micrograd_animation.nn import MLP, Layer, Neuron

X = [2.0, 3.0, -1.0]

CODE_NEURON = """class Neuron:
  def __init__(self, nin):
    self.w = [Value(random.uniform(-1,1)) for _ in range(nin)]
    self.b = Value(random.uniform(-1,1))
  def __call__(self, x):
    act = sum((wi*xi for wi, xi in zip(self.w, x)), self.b)
    return act.tanh()"""

CODE_LAYER = """class Layer:
  def __init__(self, nin, nout):
    self.neurons = [Neuron(nin) for _ in range(nout)]
  def __call__(self, x):
    outs = [n(x) for n in self.neurons]
    return outs[0] if len(outs) == 1 else outs"""

CODE_MLP = """class MLP:
  def __init__(self, nin, nouts):
    sz = [nin] + nouts
    self.layers = [Layer(sz[i], sz[i+1]) for i in range(len(nouts))]
  def __call__(self, x):
    for layer in self.layers:
      x = layer(x)
    return x"""

LAYER_COLORS = [BLUE, TEAL, YELLOW, RED]


# ------------------------------------------------------------------ engine side
def count(net):
    return len(net.parameters())


def per_layer(net):
    return [len(l.parameters()) for l in net.layers]


def formula_count(nin, nouts):
    sz = [nin] + nouts
    return sum((sz[i] + 1) * sz[i + 1] for i in range(len(nouts)))


def w0_grads(net, x=X):
    """Gradient of the output w.r.t. the first weight of every neuron in layers 1 and 2."""
    for p in net.parameters():
        p.grad = 0.0
    net(x).backward()
    return [[net.layers[k].neurons[j].w[0].grad for k in (0, 1)] for j in range(4)]


# ------------------------------------------------------------------ drawing side
def draw_net(sizes, width=6.0, height=3.6, r=0.18):
    xs = np.linspace(-width / 2, width / 2, len(sizes))
    layers = []
    for x, s in zip(xs, sizes):
        step = min(height / max(s - 1, 1), 0.9)
        ys = [(s - 1) / 2 * step - i * step for i in range(s)]
        layers.append(VGroup(*[
            Circle(radius=r, stroke_color=WHITE, stroke_width=2, fill_color=BLACK, fill_opacity=1)
            .move_to([x, y, 0]) for y in ys
        ]))
    edges = [
        VGroup(*[Line(ca.get_center(), cb.get_center(), stroke_width=1.5, stroke_color=GREY_B,
                      stroke_opacity=0.6) for ca in a for cb in b])
        for a, b in zip(layers[:-1], layers[1:])
    ]
    net = VGroup(*edges, *layers)
    net.layers, net.edges = layers, edges
    return net


def grad_table(title, rows, color):
    head = [Text(t, font_size=24, color=SECOND) for t in ("neuron", "layer 1", "layer 2")]
    cells = list(head)
    for j, row in enumerate(rows):
        cells.append(Text(str(j + 1), font_size=24, color=WHITE))
        cells += [Text(fmt(v), font_size=24, color=color) for v in row]
    grid = VGroup(*cells).arrange_in_grid(rows=5, cols=3, buff=(0.55, 0.22))
    t = Text(title, font_size=28, color=WHITE, weight=BOLD)
    g = VGroup(t, grid).arrange(DOWN, buff=0.3)
    box = SurroundingRectangle(g, color=color, buff=0.2, corner_radius=0.1)
    out = VGroup(box, g)
    out.title = t
    return out


class Scene10Mlp(MovingCameraScene):
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

    def show_callout(self, title, body, pos, color=ACTIVE, width=7.0):
        c = callout(title, body, color=color, width=width).move_to(pos)
        self.play(FadeIn(c), run_time=0.5)
        self.wait(3.2)
        self.play(FadeOut(c), run_time=0.4)

    def zoom_on(self, target, factor, hold, dy=-0.4):
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

    def pulse_net(self, net, run=0.6):
        reset = []
        self.play(*[c.animate.set_fill(TEAL, 0.9) for c in net.layers[0]], run_time=0.4)
        for i, edges in enumerate(net.edges):
            self.play(*[ShowPassingFlash(e.copy().set_stroke(TEAL, 4, 1), time_width=0.7) for e in edges],
                      run_time=run)
            self.play(*[c.animate.set_fill(TEAL, 0.9) for c in net.layers[i + 1]], run_time=0.3)
        self.wait(1.0)
        for layer in net.layers:
            reset += [c.animate.set_fill(BLACK, 1) for c in layer]
        self.play(*reset, run_time=0.5)

    def counter(self, tracker, pos):
        word = Text("parameters", font_size=30, color=WHITE).move_to(pos)

        def num():
            n = Integer(int(round(tracker.get_value())), font_size=56, color=DATA)
            return n.next_to(word, RIGHT, buff=0.35)

        return word, always_redraw(num)

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S10")
        title_card(self, "Chapter 10", "How do we build a network from Values?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        self.clear_stage()
        recap_line(self, "Next: how does the network learn from its mistakes?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        net_m = MLP(3, [4, 4, 1], seed=1)
        out = net_m(X)
        pl = per_layer(net_m)
        assert count(net_m) == 41 and pl == [16, 20, 5] == [(3 + 1) * 4, (4 + 1) * 4, (4 + 1) * 1]
        assert isinstance(Layer(2, 1)(X[:2]).data, float)  # one neuron: a value, not a list
        assert len(Layer(2, 3)(X[:2])) == 3
        tag = self.open_act("Example A: the lecture's own network, 3 inputs, 4, 4, then 1 output.",
                            "Example A: the lecture's network", "Example A:")

        # three classes, one idea at a time
        nar.say("A neuron is Value arithmetic: weights times inputs, plus a bias, then tanh.")
        p1 = code_panel(CODE_NEURON, highlight=[5, 6, 7])
        VGroup(p1, p1.highlight).scale_to_fit_width(10.5).move_to(UP * 0.5)
        self.play(FadeIn(p1), run_time=0.6)
        self.play(Create(p1.highlight), run_time=0.8)
        self.wait(3.0)
        self.show_callout("Neuron", "weights times inputs, plus a bias, then tanh", UP * 3.0 + RIGHT * 0.0)
        nar.say("A layer is just a list of neurons that all read the same inputs.")
        p2 = code_panel(CODE_LAYER, highlight=[3, 6])
        VGroup(p2, p2.highlight).scale_to_fit_width(10.5).move_to(UP * 0.5)
        self.play(FadeTransform(VGroup(p1, p1.highlight), VGroup(p2, p2.highlight)), run_time=0.8)
        self.wait(3.0)
        self.show_callout("Layer", "several neurons reading the same inputs", UP * 3.0)
        nar.say("An MLP chains layers: one layer's outputs feed the next layer.")
        p3 = code_panel(CODE_MLP, highlight=[3, 4, 7])
        VGroup(p3, p3.highlight).scale_to_fit_width(10.5).move_to(UP * 0.5)
        self.play(FadeTransform(VGroup(p2, p2.highlight), VGroup(p3, p3.highlight)), run_time=0.8)
        self.wait(3.0)
        self.show_callout("MLP", "a multi-layer perceptron: layers called in sequence", UP * 3.0)
        self.play(FadeOut(VGroup(p3, p3.highlight)), run_time=0.5)

        # the network diagram and the forward pulse
        nar.say("MLP(3, [4, 4, 1]) run on x = [2, 3, -1]: the signal moves layer by layer.")
        net = draw_net([3, 4, 4, 1], width=6.2, height=3.4).move_to(LEFT * 2.8 + UP * 0.3)
        xl = VGroup(*[Text(fmt(v), font_size=28, color=DATA).next_to(c, LEFT, buff=0.15)
                      for v, c in zip(X, net.layers[0])])
        self.play(Create(net), run_time=1.5)
        self.play(FadeIn(xl), run_time=0.6)
        self.wait(1.0)
        self.pulse_net(net)
        ol = Text("o = " + fmt(out.data), font_size=30, color=DATA).next_to(net.layers[3][0], RIGHT, buff=0.25)
        self.play(FadeIn(ol), run_time=0.6)
        self.wait(2.0)

        # one neuron close-up
        nar.say("Zoom in: a hidden neuron owns 3 weights and 1 bias to learn.")
        n0 = net_m.layers[0].neurons[0]
        hid = net.layers[1][0]
        labs = VGroup()
        for i in range(3):
            e = net.edges[0][i * 4 + 0]
            labs.add(Text(fmt(n0.w[i].data), font_size=24, color=DATA)
                     .move_to(e.point_from_proportion(0.35)).shift(UP * 0.2))
        labs.add(Text("b=" + fmt(n0.b.data), font_size=24, color=GRAD).next_to(hid, DOWN, buff=0.12))
        self.play(*[net.edges[0][i * 4].animate.set_stroke(YELLOW, 4, 1) for i in range(3)],
                  hid.animate.set_stroke(YELLOW, 4), FadeIn(labs), run_time=0.8)
        self.zoom_on(hid, 0.5, 3.0, dy=-0.2)
        self.play(FadeOut(labs), *[net.edges[0][i * 4].animate.set_stroke(GREY_B, 1.5, 0.6) for i in range(3)],
                  hid.animate.set_stroke(WHITE, 2), run_time=0.6)

        # counting parameters, predict then reveal
        nar.say("Predict: how many numbers does this network hold that we may turn?")
        q = self.pulse_question("How many parameters?", RIGHT * 3.7 + UP * 2.4, RIGHT * 3.7 + UP * 1.2)
        nar.say("Count them layer by layer: 16, then 20, then 5. Each is a knob.")
        self.play(FadeOut(q), run_time=0.4)
        tracker = ValueTracker(0)
        word, num = self.counter(tracker, RIGHT * 2.9 + UP * 2.4)
        self.play(FadeIn(word), FadeIn(num), run_time=0.5)
        acc = 0
        for k, p in enumerate(pl):
            hl = VGroup(net.edges[k], net.layers[k + 1]).copy().set_color(YELLOW)
            self.play(FadeIn(hl), run_time=0.4)
            acc += p
            self.play(tracker.animate.set_value(acc), run_time=1.2)
            self.play(FadeOut(hl), run_time=0.4)
        w = working_line(self, r"p_1+p_2+p_3", f"{pl[0]}+{pl[1]}+{pl[2]}", f"{count(net_m)}",
                         pos=RIGHT * 3.7 + DOWN * 0.3, width=4.8, hold=2.0)
        self.show_callout("Parameter", "a weight or a bias: one knob to turn", RIGHT * 3.7 + DOWN * 1.6,
                          width=5.4)
        self.play(FadeOut(w), run_time=0.4)
        self.wait(0.5)
        self.A = (net, xl, ol, word, num, tracker, tag)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        net, xl, ol, word, num, tracker, tag0 = self.A
        self.play(FadeOut(tag0), FadeOut(xl), FadeOut(ol), FadeOut(word), FadeOut(num), run_time=0.5)
        tag = self.open_act("Example B: what if we change the shape of the network?",
                            "Example B: what if the network changes shape?", "Example B:")
        word, num = self.counter(tracker, RIGHT * 2.9 + UP * 2.4)
        self.play(FadeIn(word), FadeIn(num), run_time=0.4)

        archs = [(3, [4, 4, 1]), (3, [8, 8, 1]), (2, [4, 1])]
        expected = [41, 113, 17]
        rows = VGroup()

        def add_row(i):
            nin, nouts = archs[i]
            a = Text(f"MLP({nin}, {nouts})", font_size=28, color=WHITE)
            b = Text(str(count(MLP(nin, nouts, seed=1))), font_size=28, color=DATA)
            r = VGroup(a, b).arrange(RIGHT, buff=0.5)
            return r

        for i, (nin, nouts) in enumerate(archs):
            assert count(MLP(nin, nouts, seed=1)) == expected[i] == formula_count(nin, nouts)
        rows.add(add_row(0))
        rows.add(add_row(1))
        rows.add(add_row(2))
        rows.arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to(RIGHT * 3.7 + DOWN * 1.5)
        self.play(FadeIn(rows[0]), run_time=0.5)

        nar.say("Predict: make both hidden layers 8 wide. Do the knobs double?")
        q = self.pulse_question("MLP(3, [8, 8, 1]): how many?", RIGHT * 3.7 + UP * 1.4, RIGHT * 3.7 + UP * 0.3)
        self.play(FadeOut(q), run_time=0.3)
        nar.say("More than double: 113 parameters, because the layers feed each other.")
        net2 = draw_net([3, 8, 8, 1], width=6.2, height=3.6).move_to(net.get_center())
        self.play(FadeTransform(net, net2), tracker.animate.set_value(113), run_time=2.0)
        self.play(FadeIn(rows[1]), run_time=0.5)
        w = working_line(self, r"(3+1)\,8+(8+1)\,8+(8+1)\,1", r"32+72+9", "113",
                         pos=RIGHT * 3.7 + UP * 1.6, width=4.8, hold=2.0)
        self.play(FadeOut(w), run_time=0.4)
        nar.say("Shrink it to MLP(2, [4, 1]): the diagram redraws, only 17 knobs remain.")
        net3 = draw_net([2, 4, 1], width=6.2, height=3.6).move_to(net2.get_center())
        self.play(FadeTransform(net2, net3), tracker.animate.set_value(17), run_time=2.0)
        self.play(FadeIn(rows[2]), run_time=0.5)
        w = working_line(self, r"(2+1)\,4+(4+1)\,1", r"12+5", "17",
                         pos=RIGHT * 3.7 + UP * 1.6, width=4.8, hold=2.0)
        self.play(FadeOut(w), run_time=0.4)
        self.wait(1.0)

        # three seeds
        self.play(FadeOut(net3), FadeOut(rows), FadeOut(word), FadeOut(num), run_time=0.6)
        outs = [MLP(3, [4, 4, 1], seed=s)(X).data for s in (1, 2, 3)]
        assert len(set(round(o, 6) for o in outs)) == 3
        nar.say("Predict: same network, same input, three random seeds. Same output?")
        axes = Axes(x_range=[0, 4, 1], y_range=[-1, 1, 0.5], x_length=6.0, y_length=3.6,
                    axis_config={"include_numbers": False, "font_size": 24},
                    y_axis_config={"include_numbers": True, "font_size": 24},
                    tips=False).move_to(LEFT * 2.5 + UP * 0.2)
        xl_ = VGroup(*[Text(f"seed {s}", font_size=24, color=SECOND).move_to(axes.c2p(s + 0.0, -1.0) + DOWN * 0.3)
                       for s in (1, 2, 3)])
        yl_ = Text("output", font_size=26, color=SECOND).next_to(axes, UP, buff=0.1).shift(LEFT * 1.8)
        self.play(Create(axes), FadeIn(xl_), FadeIn(yl_), run_time=1.5)
        q = self.pulse_question("Same output?", RIGHT * 3.7 + UP * 1.6, RIGHT * 3.7 + UP * 0.5)
        self.play(FadeOut(q), run_time=0.3)
        nar.say("No: each seed sets different knobs, so the output differs.")

        def bar(i, v):
            x0 = i + 0.6
            return Polygon(axes.c2p(x0, 0), axes.c2p(x0 + 0.8, 0), axes.c2p(x0 + 0.8, v), axes.c2p(x0, v),
                           stroke_width=0, fill_color=DATA if v >= 0 else RED, fill_opacity=0.9)

        bars = VGroup(*[bar(i, 0.0001) for i in range(3)])
        self.play(FadeIn(bars), run_time=0.3)
        self.play(*[Transform(bars[i], bar(i, v)) for i, v in enumerate(outs)], run_time=2.0)
        vals = VGroup(*[Text(fmt(v), font_size=26, color=DATA if v >= 0 else RED)
                        .next_to(bars[i], UP if v >= 0 else DOWN, buff=0.1) for i, v in enumerate(outs)])
        self.play(FadeIn(vals), run_time=0.6)
        self.wait(1.0)
        self.play(Indicate(bars, color=ACTIVE), run_time=1.2)
        self.wait(2.5)
        t = Text("the weights start random", font_size=30, color=WHITE).move_to(RIGHT * 3.7 + UP * 1.2)
        t2 = Text("so training must fix them", font_size=30, color=ACTIVE).next_to(t, DOWN, buff=0.3)
        self.play(FadeIn(t), run_time=0.5)
        self.play(FadeIn(t2), run_time=0.5)
        self.wait(3.0)
        self.B = (axes, xl_, yl_, bars, vals, t, t2, tag)

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        tag = self.B[-1]
        self.clear_stage()
        tag = self.open_act("Expert corner: why must the weights start random, not all equal?",
                            "Expert corner: breaking the symmetry", "Expert corner:")
        sym = MLP(3, [4, 4, 1], const=0.5)
        rnd = MLP(3, [4, 4, 1], seed=1)
        gs, gr = w0_grads(sym), w0_grads(rnd)
        for j in range(1, 4):
            assert all(abs(gs[j][k] - gs[0][k]) < 1e-12 for k in (0, 1))  # identical under symmetric start
        assert len({round(g[0], 8) for g in gr}) == 4

        net = draw_net([3, 4, 4, 1], width=5.4, height=3.2).move_to(LEFT * 3.4 + UP * 0.4)
        self.play(Create(net), run_time=1.2)
        nar.say("Start every weight at 0.5 and every bias at 0, and look at the gradients.")
        same = [c.animate.set_fill(ORANGE, 0.9) for L in (1, 2) for c in net.layers[L]]
        self.play(*same, run_time=0.8)
        nar.say("Predict: will the four neurons of a layer get different gradients?")
        q = self.pulse_question("Different gradients?", RIGHT * 3.5 + UP * 2.6, RIGHT * 3.5 + UP * 1.3)
        self.play(FadeOut(q), run_time=0.3)
        nar.say("No: identical. Each neuron sees the same inputs and acts the same.")
        t_sym = grad_table("same start", gs, ORANGE).scale(0.85).move_to(RIGHT * 3.5 + UP * 0.2)
        self.play(FadeIn(t_sym), run_time=0.8)
        self.play(Indicate(VGroup(*[t_sym[1][1][i] for i in (4, 7, 10, 13)]), color=ACTIVE), run_time=1.2)
        self.wait(2.5)
        nar.say("So they stay twins forever: extra neurons would add nothing new.")
        self.show_callout("Symmetry", "equal neurons get equal updates, forever", LEFT * 3.4 + DOWN * 2.0,
                          width=6.0)
        nar.say("Random weights break the tie: each neuron gets its own gradient.")
        t_rnd = grad_table("random start (seed 1)", gr, TEAL).scale(0.85).move_to(t_sym)
        recolor = [c.animate.set_fill(LAYER_COLORS[j], 0.9) for L in (1, 2) for j, c in enumerate(net.layers[L])]
        self.play(*recolor, Transform(t_sym, t_rnd), run_time=2.5)
        self.wait(3.0)
        self.zoom_on(t_sym, 0.6, 2.5, dy=0.0)

        # the general formula
        nar.say("Counting knobs in general: each layer has (inputs + 1) times neurons.")
        self.play(FadeOut(net), FadeOut(t_sym), run_time=0.6)
        f1 = MathTex(r"P=\sum_{l}(n_{l-1}+1)\,n_l", font_size=48, color=WHITE).move_to(UP * 2.4)
        self.play(FadeIn(f1), run_time=0.6)
        self.wait(1.0)
        pl = per_layer(rnd)
        w = working_line(self, r"(3+1)\,4+(4+1)\,4+(4+1)\,1", r"16+20+5", "41",
                         pos=UP * 1.1, width=7.0, hold=2.0)
        # stacked bar of the 41
        total = sum(pl)
        cols = [BLUE, TEAL, YELLOW]
        segs, x = VGroup(), 0.0
        for p, c in zip(pl, cols):
            wd = 9.0 * p / total
            r = Rectangle(width=wd, height=0.7, stroke_color=WHITE, stroke_width=2, fill_color=c, fill_opacity=0.8)
            r.move_to([-4.5 + x + wd / 2, -0.5, 0])
            lab = Text(str(p), font_size=28, color=BLACK, weight=BOLD).move_to(r)
            segs.add(VGroup(r, lab))
            x += wd
        names = VGroup(*[Text(n, font_size=24, color=SECOND).next_to(s, DOWN, buff=0.15)
                         for n, s in zip(("layer 1", "layer 2", "layer 3"), segs)])
        self.play(*[GrowFromEdge(s, LEFT) for s in segs], run_time=1.5)
        self.play(FadeIn(names), run_time=0.5)
        nar.say("Bigger layers cost more: parameters grow with width times width.")
        self.wait(3.0)
        self.play(Indicate(segs[1], color=ACTIVE), run_time=1.2)
        self.wait(2.0)
