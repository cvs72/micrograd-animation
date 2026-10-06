from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, fmt,
    recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value
from micrograd_animation.nn import MLP

XS = [[2.0, 3.0, -1.0], [3.0, -1.0, 0.5], [0.5, 1.0, 1.0], [1.0, 1.0, -1.0]]
YS = [1.0, -1.0, -1.0, 1.0]
SIZES = [3, 4, 4, 1]
STEPS = 30
LRS = [0.001, 0.01, 0.05, 0.3, 1.0]
LR_COLORS = [GREY_B, BLUE, TEAL, GREEN, RED]
LR_NOTES = ["too slow: barely moves", "slow but steady", "good: smooth and fast",
            "fastest here", "overshoots, saturates, stuck"]


# ------------------------------------------------------------------ engine side
def loss_of(net):
    ypred = [net(x) for x in XS]
    return sum((yout - ygt) ** 2 for ygt, yout in zip(YS, ypred)), ypred


def train(lr, steps=STEPS, zero=True, seed=1):
    """Gradient descent exactly as in the notebook; records every step before its update."""
    net = MLP(3, [4, 4, 1], seed=seed)
    h = {"loss": [], "preds": [], "w": [], "g0": [], "fresh0": [], "net": net}
    for _ in range(steps):
        loss, ypred = loss_of(net)
        h["loss"].append(loss.data)
        h["preds"].append([p.data for p in ypred])
        h["w"].append([p.data for p in net.parameters()])
        p0 = net.parameters()[0]
        if zero:
            for p in net.parameters():
                p.grad = 0.0
        old = p0.grad
        loss.backward()
        h["g0"].append(p0.grad)
        h["fresh0"].append(p0.grad - old)
        for p in net.parameters():
            p.data += -lr * p.grad
    return h


def interp(seq, k):
    i = min(int(k), len(seq) - 1)
    j = min(i + 1, len(seq) - 1)
    f = k - i
    a, b = seq[i], seq[j]
    if isinstance(a, list):
        return [x + (y - x) * f for x, y in zip(a, b)]
    return a + (b - a) * f


def sci(x):
    m, e = f"{x:.1e}".split("e")
    return rf"{m}\times10^{{{int(e)}}}"


def signed(t):
    return f"{'-' if t > 0 else '+'}{abs(t):g}"


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


def style_net(net, w):
    """Edge thickness = |weight|, BLUE for positive, RED for negative."""
    off = 0
    for l in range(len(SIZES) - 1):
        nin, nout = SIZES[l], SIZES[l + 1]
        for i in range(nin):
            for j in range(nout):
                v = w[off + j * (nin + 1) + i]
                net.edges[l][i * nout + j].set_stroke(
                    color=DATA if v >= 0 else RED, width=0.8 + 4.5 * min(abs(v), 1.5) / 1.5, opacity=0.9)
        off += nout * (nin + 1)


def make_curve(axes, ys, k, color, ymax, width=4):
    n = int(k)
    pts = [axes.c2p(i, min(ys[i], ymax)) for i in range(n + 1)]
    if n < len(ys) - 1:
        pts.append(axes.c2p(k, min(interp(ys, k), ymax)))
    if len(pts) == 1:
        pts.append(pts[0] + RIGHT * 0.001)
    m = VMobject(stroke_color=color, stroke_width=width)
    m.set_points_as_corners(pts)
    return m


def make_bars(axes, preds):
    g = VGroup()
    for i, (p, t) in enumerate(zip(preds, YS)):
        for x0, v, c in ((i + 0.6, p, DATA), (i + 1.05, t, SECOND)):
            g.add(Polygon(axes.c2p(x0, 0), axes.c2p(x0 + 0.4, 0), axes.c2p(x0 + 0.4, v), axes.c2p(x0, v),
                          stroke_width=0, fill_color=c, fill_opacity=0.9))
    return g


def bars_axes(width=5.4, height=3.0):
    axes = Axes(x_range=[0, 5, 1], y_range=[-1, 1, 1], x_length=width, y_length=height,
                axis_config={"include_numbers": False}, y_axis_config={"include_numbers": True,
                                                                         "font_size": 24},
                tips=False)
    names = VGroup(*[Text(f"ex {i + 1}", font_size=24, color=SECOND)
                     .move_to(axes.c2p(i + 1.05, -1) + DOWN * 0.3) for i in range(4)])
    key = VGroup(
        VGroup(Square(0.2, fill_color=DATA, fill_opacity=1, stroke_width=0),
               Text("prediction", font_size=24, color=DATA)).arrange(RIGHT, buff=0.15),
        VGroup(Square(0.2, fill_color=SECOND, fill_opacity=1, stroke_width=0),
               Text("target", font_size=24, color=SECOND)).arrange(RIGHT, buff=0.15),
    ).arrange(RIGHT, buff=0.5).next_to(axes, UP, buff=0.15)
    return axes, names, key


def line_axes(xmax, ymax, ystep, width, height):
    axes = Axes(x_range=[0, xmax, 5], y_range=[0, ymax, ystep], x_length=width, y_length=height,
                axis_config={"include_numbers": True, "font_size": 24}, tips=False)
    xl = Text("step", font_size=24, color=SECOND).next_to(axes, DOWN, buff=0.1).align_to(axes, RIGHT)
    return axes, xl


class Scene11Training(MovingCameraScene):
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

    def readout(self, tracker, losses, pos, prefix="step"):
        def make():
            k = tracker.get_value()
            t = Text(f"{prefix} {int(round(k))}    loss {fmt(interp(losses, k))}", font_size=32, color=WHITE)
            return t.move_to(pos)
        return always_redraw(make)

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S11")
        title_card(self, "Chapter 11", "How does a network learn from its mistakes?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        self.clear_stage()
        recap_line(self, "Next: what does the loss look like as a landscape?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        run = self.run_a = train(0.05)
        lecture = train(0.1, 20)
        assert round(run["loss"][0], 3) == 6.244 and round(run["loss"][-1], 3) == 0.035
        net0 = MLP(3, [4, 4, 1], seed=1)
        loss0, ypred0 = loss_of(net0)
        assert abs(loss0.data - run["loss"][0]) < 1e-12
        p0 = [p.data for p in ypred0]
        ups = sum(1 for p, t in zip(p0, YS) if t > p)
        tag = self.open_act("Example A: the lecture's four examples and our 41-knob network.",
                            "Example A: the lecture's dataset", "Example A:")

        # dataset + network
        nar.say("Four examples, three inputs each, and the answer wanted for each.")
        rows = VGroup(*[
            MathTex(rf"x^{{({i + 1})}}=[{','.join(fmt(v) for v in x)}]\;\to\;y={fmt(t)}", font_size=38,
                    color=WHITE) for i, (x, t) in enumerate(zip(XS, YS))
        ]).arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to(LEFT * 3.9 + UP * 0.5)
        net = draw_net(SIZES, width=5.2, height=3.0).move_to(RIGHT * 3.2 + UP * 0.5)
        style_net(net, run["w"][0])
        self.play(FadeIn(rows), run_time=0.8)
        self.play(Create(net), run_time=1.2)
        self.wait(2.0)
        nar.say("The network starts with random weights, so it just guesses.")
        self.play(*[c.animate.set_fill(FWD, 0.9) for c in net.layers[0]], run_time=0.4)
        for i, edges in enumerate(net.edges):
            self.play(*[ShowPassingFlash(e.copy().set_stroke(FWD, 4, 1), time_width=0.7) for e in edges],
                      run_time=0.6)
            self.play(*[c.animate.set_fill(FWD, 0.9) for c in net.layers[i + 1]], run_time=0.3)
        self.wait(1.0)
        self.play(FadeOut(rows), FadeOut(net), run_time=0.6)

        # predictions against targets
        nar.say("Its four guesses (blue) beside the four right answers (grey).")
        axes, names, key = bars_axes()
        VGroup(axes, names, key).move_to(LEFT * 3.6 + UP * 0.5)
        zero = make_bars(axes, [0.0001] * 4)
        self.play(Create(axes), FadeIn(names), FadeIn(key), FadeIn(zero), run_time=1.2)
        bars = make_bars(axes, p0)
        self.play(Transform(zero, bars), run_time=1.5)
        self.wait(1.5)
        nar.say("Predict: must each blue bar move up or down to reach its target?")
        q = self.pulse_question("Which way must each bar move?", RIGHT * 3.3 + UP * 2.2, RIGHT * 3.3 + UP * 1.0)
        self.play(FadeOut(q), run_time=0.3)
        arrows = VGroup(*[
            Arrow(axes.c2p(i + 0.8, p), axes.c2p(i + 0.8, p) + (UP if t > p else DOWN) * 0.7, buff=0,
                  color=ACTIVE, stroke_width=8, max_tip_length_to_length_ratio=0.5)
            for i, (p, t) in enumerate(zip(p0, YS))])
        nar.say(f"{ups} must go up and {4 - ups} must go down: arrows point to the targets.")
        self.play(*[GrowArrow(a) for a in arrows], run_time=1.0)
        self.wait(2.5)
        self.play(FadeOut(arrows), run_time=0.4)

        # the loss
        nar.say("One number for the total mistake: square each error, then add.")
        self.show_callout("Loss", "one number: how wrong the network is (low is good)", RIGHT * 3.3 + UP * 2.3,
                          width=6.4)
        terms = "+".join(f"({p:.2f}{signed(t)})^2" for p, t in zip(p0, YS))
        w = working_line(self, r"L=\sum_i(\hat y_i-y_i)^2", "L=" + terms, "L=" + fmt(loss0.data),
                         pos=RIGHT * 3.3 + UP * 1.2, width=6.6, hold=2.5)
        self.play(Indicate(w, color=ACTIVE), run_time=1.0)
        self.wait(1.0)
        self.play(FadeOut(w), run_time=0.4)

        # the update rule
        nar.say("backward() gives each knob a gradient: its effect on the loss.")
        loss0.backward()
        params = net0.parameters()
        m = min(range(len(params)), key=lambda i: params[i].grad)  # steepest negative gradient
        wd, g = params[m].data, params[m].grad
        gcol = Text(f"knob #{m + 1}:  gradient {fmt(g)}", font_size=30, color=GRAD).move_to(RIGHT * 3.3 + UP * 2.2)
        self.play(FadeIn(gcol), run_time=0.6)
        nar.say("Predict: this gradient is negative. Knob up or down?")
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to(RIGHT * 3.3 + UP * 1.0)
        self.play(FadeIn(qm), run_time=0.4)
        for _ in range(3):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        self.play(FadeOut(qm), run_time=0.3)
        assert g < 0 and (wd + 0.05 * -g) > wd
        nar.say("Negative gradient: raising the knob lowers the loss, so go up.")
        self.show_callout("Learning rate", "how big a step we take: here 0.05", RIGHT * 3.3 + UP * 0.3, width=6.0)
        new = wd - 0.05 * g
        f0 = MathTex(r"p\leftarrow p-\eta\,g", font_size=44, color=WHITE).move_to(RIGHT * 3.3 + UP * 1.3)
        f1 = MathTex(rf"p\leftarrow {wd:.4f}-0.05\cdot({g:.4f})", font_size=44, color=DATA)
        f2 = MathTex(rf"p\leftarrow {wd:.4f}-0.05\cdot({g:.4f})={new:.4f}", font_size=44, color=WHITE)
        for f in (f1, f2):
            f.scale_to_fit_width(6.4).move_to(RIGHT * 3.3 + UP * 1.3)
        self.play(FadeIn(f0), run_time=0.6)
        self.wait(1.0)
        self.play(TransformMatchingTex(f0, f1), run_time=1.0)
        self.wait(2.0)
        self.play(ReplacementTransform(f1, f2), run_time=1.0)
        ans = Text(f"Answer: knob #{m + 1} goes UP, {wd:.4f} to {new:.4f}", font_size=30, color=ACTIVE)
        ans.scale_to_fit_width(min(ans.width, 6.4)).next_to(f2, DOWN, buff=0.4)
        self.play(FadeIn(ans), Indicate(f2, color=ACTIVE), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(f2), FadeOut(ans), FadeOut(gcol), run_time=0.4)
        self.show_callout("Gradient descent", "forward, backward, update: repeat many times",
                          RIGHT * 3.3 + UP * 1.4, width=6.4)

        # the training loop
        nar.say(f"30 steps at 0.05. The lecture: 0.1, 20 steps, loss {fmt(lecture['loss'][-1])}.")
        self.play(FadeOut(zero), run_time=0.3)
        k = ValueTracker(0)
        live_bars = always_redraw(lambda: make_bars(axes, interp(run["preds"], k.get_value())))
        laxes, lx = line_axes(STEPS - 1, 7, 1, 5.4, 2.6)
        laxes.move_to(RIGHT * 3.6 + UP * 0.9)
        lx.next_to(laxes, DOWN, buff=0.1).align_to(laxes, RIGHT)
        ly = Text("loss", font_size=24, color=SECOND).move_to(laxes.c2p(24, 6.2))
        curve = always_redraw(lambda: make_curve(laxes, run["loss"], k.get_value(), BWD, 7))
        ro = self.readout(k, run["loss"], UP * 3.3)
        upd_cache = {}

        def make_upd():
            i = min(int(round(k.get_value())), STEPS - 1)
            if i not in upd_cache:
                w0, g0 = run["w"][i][0], run["g0"][i]
                upd_cache[i] = MathTex(
                    rf"p\leftarrow p-\eta g={w0:.4f}-0.05\cdot({g0:.4f})={w0 - 0.05 * g0:.4f}",
                    font_size=40, color=WHITE).scale_to_fit_width(10.5).move_to(DOWN * 2.0)
            return upd_cache[i].copy()
        upd = always_redraw(make_upd)
        self.play(Create(laxes), FadeIn(lx), FadeIn(ly), FadeIn(live_bars), FadeIn(ro), run_time=1.2)
        self.play(FadeIn(upd), run_time=0.6)
        self.add(curve)
        self.play(k.animate.set_value(STEPS - 1), run_time=12, rate_func=linear)
        self.wait(1.5)
        nar.say(f"Loss fell from {fmt(run['loss'][0])} to {fmt(run['loss'][-1])}: blue bars meet grey.")
        self.play(Indicate(live_bars, color=ACTIVE), run_time=1.2)
        self.zoom_on(laxes, 0.55, 3.0, dy=-0.2)
        self.wait(1.0)

        # the network with changing weights
        nar.say("Same run in the network: line thickness shows weight size.")
        self.play(FadeOut(live_bars), FadeOut(curve), FadeOut(laxes), FadeOut(lx), FadeOut(ly),
                  FadeOut(axes), FadeOut(names), FadeOut(key), FadeOut(upd), FadeOut(ro), run_time=0.8)
        self.remove(ro, live_bars, curve)
        net = draw_net(SIZES, width=6.0, height=3.2).move_to(LEFT * 2.6 + UP * 0.3)
        style_net(net, run["w"][0])
        k2 = ValueTracker(0)
        net.add_updater(lambda m_: style_net(m_, interp(run["w"], k2.get_value())))
        legend = VGroup(Text("thick line = big weight", font_size=28, color=WHITE),
                        Text("blue: positive", font_size=28, color=DATA),
                        Text("red: negative", font_size=28, color=RED)).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        legend.move_to(RIGHT * 4.3 + UP * 1.2)
        ro2 = self.readout(k2, run["loss"], RIGHT * 4.3 + DOWN * 0.5)
        self.play(Create(net), FadeIn(legend), FadeIn(ro2), run_time=1.2)
        self.wait(1.5)
        self.play(k2.animate.set_value(STEPS - 1), run_time=6, rate_func=linear)
        self.wait(2.0)
        net.clear_updaters()
        self.A = (tag, net, legend, ro2)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        tag0, net, legend0, ro2 = self.A
        self.play(FadeOut(tag0), FadeOut(net), FadeOut(legend0), FadeOut(ro2), run_time=0.5)
        runs = [train(lr) for lr in LRS]
        finals = [r["loss"][-1] for r in runs]
        assert [round(f, 3) for f in finals[:4]] == [5.454, 0.509, 0.035, 0.002]
        assert abs(finals[4] - 8.0) < 0.01 and round(finals[2], 3) == 0.035
        assert all(abs(r["loss"][0] - runs[0]["loss"][0]) < 1e-12 for r in runs)
        ymax = 9.0
        tag = self.open_act("Example B: what if the learning rate changes? Five runs, same start.",
                            "Example B: what if the step size changes?", "Example B:")
        axes, xl = line_axes(STEPS - 1, ymax, 3, 6.6, 3.4)
        axes.move_to(LEFT * 2.8 + UP * 0.5)
        xl.next_to(axes, DOWN, buff=0.1).align_to(axes, RIGHT)
        yl = Text("loss", font_size=24, color=SECOND).next_to(axes, UP, buff=0.1).align_to(axes, LEFT)
        self.play(Create(axes), FadeIn(xl), FadeIn(yl), run_time=1.2)
        nar.say("Predict: all five start at the same loss. Which rate ends lowest?")
        q = self.pulse_question("Which learning rate wins?", RIGHT * 4.0 + UP * 2.0, RIGHT * 4.0 + UP * 0.8)
        self.play(FadeOut(q), run_time=0.3)

        k = ValueTracker(0)
        rows = VGroup()
        for lr, col, r in zip(LRS, LR_COLORS, runs):
            sw = Line(LEFT * 0.25, RIGHT * 0.25, color=col, stroke_width=6)
            nm = Text(f"lr {lr:g}", font_size=26, color=col)
            rows.add(VGroup(sw, nm).arrange(RIGHT, buff=0.2))
        rows.arrange(DOWN, buff=0.62, aligned_edge=LEFT).move_to(RIGHT * 4.1 + UP * 0.3)
        vals = always_redraw(lambda: VGroup(*[
            Text(fmt(interp(r["loss"], k.get_value())), font_size=26, color=c)
            .next_to(rows[i], RIGHT, buff=0.3).align_to(RIGHT * 5.2, LEFT)
            for i, (c, r) in enumerate(zip(LR_COLORS, runs))]))
        curves = [always_redraw(lambda r=r, c=c: make_curve(axes, r["loss"], k.get_value(), c, ymax))
                  for r, c in zip(runs, LR_COLORS)]
        nar.say("Each line is one run of 30 steps. We race them live.")
        self.play(FadeIn(rows), FadeIn(vals), run_time=0.8)
        self.add(*curves)
        self.play(k.animate.set_value(STEPS - 1), run_time=10, rate_func=linear)
        self.wait(1.0)
        nar.say("Fastest here is 0.3, not the biggest rate: 1.0 jumps and gets stuck.")
        self.play(Indicate(rows[3], color=ACTIVE), run_time=1.2)
        self.play(Indicate(rows[4], color=ACTIVE), run_time=1.2)
        notes = VGroup(*[Text(t, font_size=24, color=SECOND).next_to(rows[i], DOWN, buff=0.08)
                         .align_to(rows[i], LEFT) for i, t in enumerate(LR_NOTES)])
        self.play(FadeIn(notes), run_time=0.8)
        self.wait(4.0)

        # before / after: lr 0.3 against lr 1.0
        nar.say("Why is 1.0 stuck? Compare its predictions with those of 0.3.")
        self.play(FadeOut(Group(axes, xl, yl, rows, vals, notes, *curves)), run_time=0.6)
        self.remove(*curves, vals)
        pa, pb = runs[3]["preds"][-1], runs[4]["preds"][-1]
        la, lb = finals[3], finals[4]
        assert all((p > 0) == (t > 0) for p, t in zip(pa, YS))
        assert sum(1 for p, t in zip(pb, YS) if (p > 0) != (t > 0)) == 2
        baxes, bnames, bkey = bars_axes(5.6, 3.2)
        VGroup(baxes, bnames, bkey).move_to(LEFT * 3.6 + UP * 0.5)
        mix = ValueTracker(0)
        live = always_redraw(lambda: make_bars(baxes, [a + (b - a) * mix.get_value() for a, b in zip(pa, pb)]))
        title = Text("lr = 0.3", font_size=34, color=GREEN).move_to(RIGHT * 3.7 + UP * 2.4)
        lossro = always_redraw(lambda: Text(
            "loss " + fmt(la + (lb - la) * mix.get_value()), font_size=34, color=WHITE
        ).move_to(RIGHT * 3.7 + UP * 1.6))
        self.play(Create(baxes), FadeIn(bnames), FadeIn(bkey), FadeIn(live), FadeIn(title), FadeIn(lossro),
                  run_time=1.2)
        self.wait(2.5)
        nar.say("Now the same network trained with rate 1.0: every bar jumps to -1.")
        self.play(mix.animate.set_value(1), Transform(title, Text("lr = 1.0", font_size=34, color=RED)
                                                      .move_to(title)), run_time=3.0)
        self.wait(2.0)
        nar.say("Two answers are now wrong, and tanh is flat there, so the gradient dies.")
        o = pb[0]
        w = working_line(self, r"1-o^2", f"1-({o:.4f})^2", sci(1 - o * o), pos=RIGHT * 3.7 + UP * 0.2,
                         width=5.6, hold=2.5)
        assert 1 - o * o < 1e-4
        self.play(Indicate(w, color=ACTIVE), run_time=1.0)
        self.wait(2.0)
        self.B = (baxes, bnames, bkey, live, title, lossro, w, tag)

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        self.clear_stage()
        self.remove(*[m for m in self.mobjects if m is not self.nar.current])
        tag = self.open_act("Expert corner: what really goes wrong, and what real training adds.",
                            "Expert corner: pitfalls and real training", "Expert corner:")

        # 1. zero_grad
        zr, nz = train(0.05, zero=True), train(0.05, zero=False)
        assert abs(nz["g0"][3] - (nz["g0"][2] + nz["fresh0"][3])) < 1e-12
        assert nz["loss"][-1] < zr["loss"][-1] + 1.0 and nz["loss"][-1] < nz["loss"][0] / 10  # still falls
        gmax = max(abs(v) for v in nz["g0"] + zr["g0"])
        gtop = float(np.ceil(gmax))
        gaxes = Axes(x_range=[0, STEPS - 1, 10], y_range=[-gtop, gtop, gtop], x_length=5.4, y_length=2.8,
                     axis_config={"include_numbers": True, "font_size": 24}, tips=False)
        laxes = Axes(x_range=[0, STEPS - 1, 10], y_range=[0, 7, 2], x_length=5.4, y_length=2.8,
                     axis_config={"include_numbers": True, "font_size": 24}, tips=False)
        gaxes.move_to(LEFT * 3.4 + UP * 0.4)
        laxes.move_to(RIGHT * 3.4 + UP * 0.4)
        gt = Text("gradient of one weight", font_size=26, color=SECOND).next_to(gaxes, UP, buff=0.12)
        lt = Text("loss", font_size=26, color=SECOND).next_to(laxes, UP, buff=0.12)
        gx = Text("step", font_size=24, color=SECOND).next_to(gaxes, DOWN, buff=0.1).align_to(gaxes, RIGHT)
        lx = Text("step", font_size=24, color=SECOND).next_to(laxes, DOWN, buff=0.1).align_to(laxes, RIGHT)
        key = VGroup(Text("zeroed each step", font_size=26, color=TEAL),
                     Text("never zeroed", font_size=26, color=ORANGE)).arrange(RIGHT, buff=0.6)
        key.move_to(UP * 3.0 + RIGHT * 0.4)
        nar.say("The classic bug: forget to zero the gradients before backward().")
        self.play(Create(gaxes), Create(laxes), FadeIn(VGroup(gt, lt, gx, lx, key)), run_time=1.4)
        nar.say("Predict: if we never zero them, will the loss still go down?")
        q = self.pulse_question("Loss without zeroing?", DOWN * 2.1 + LEFT * 0.8, DOWN * 2.1 + RIGHT * 1.8)
        self.play(FadeOut(q), run_time=0.3)
        k = ValueTracker(0)
        cs = [always_redraw(lambda: make_curve(gaxes, zr["g0"], k.get_value(), TEAL, 1e9)),
              always_redraw(lambda: make_curve(gaxes, nz["g0"], k.get_value(), ORANGE, 1e9)),
              always_redraw(lambda: make_curve(laxes, zr["loss"], k.get_value(), TEAL, 7)),
              always_redraw(lambda: make_curve(laxes, nz["loss"], k.get_value(), ORANGE, 7))]
        self.add(*cs)
        self.play(k.animate.set_value(STEPS - 1), run_time=7, rate_func=linear)
        nar.say("Yes, it still falls here, which is why the bug is so easy to miss.")
        self.wait(1.5)
        nar.say("Kept gradients pile up, so every step is too big.")
        step = 3
        w = working_line(self, r"g_{\text{kept}}=g_{\text{old}}+g_{\text{new}}",
                         f"{nz['g0'][step - 1]:.4f}+({nz['fresh0'][step]:.4f})", fmt(nz["g0"][step]),
                         pos=DOWN * 1.9, width=6.4, hold=2.2)
        self.play(FadeOut(w), run_time=0.4)
        self.wait(1.0)
        self.play(FadeOut(Group(gaxes, laxes, gt, lt, gx, lx, key, *cs)), run_time=0.6)
        self.remove(*cs)

        # 2. memorising
        nar.say("41 knobs but only 4 examples: the network can simply memorise them.")
        net = zr["net"]
        npar = len(net.parameters())
        assert npar == 41
        knobs = VGroup(*[Dot(radius=0.1, color=DATA) for _ in range(npar)]).arrange_in_grid(
            rows=5, cols=9, buff=0.22).move_to(LEFT * 3.8 + UP * 0.7)
        pts = VGroup(*[Dot(radius=0.16, color=YELLOW) for _ in range(4)]).arrange(RIGHT, buff=0.5)
        pts.move_to(RIGHT * 3.8 + UP * 0.7)
        kl = Text("41 knobs", font_size=30, color=DATA).next_to(knobs, DOWN, buff=0.3)
        pl = Text("4 examples", font_size=30, color=YELLOW).next_to(pts, DOWN, buff=0.3)
        self.play(Create(knobs), Create(pts), FadeIn(kl), FadeIn(pl), run_time=1.5)
        self.wait(2.0)
        final_loss = zr["loss"][-1]
        unseen = [-1.0, 2.0, 0.5]
        guess = net(unseen).data
        nar.say("Low loss on these four says nothing about unseen examples.")
        t1 = Text(f"training loss {fmt(final_loss)}", font_size=30, color=TEAL).move_to(RIGHT * 3.8 + DOWN * 0.9)
        t2 = Text(f"new input: prediction {fmt(guess)}, target ?", font_size=28, color=WHITE
                  ).move_to(RIGHT * 2.2 + DOWN * 1.8)
        self.play(FadeIn(t1), run_time=0.6)
        self.play(FadeIn(t2), run_time=0.6)
        self.wait(2.5)
        self.show_callout("Overfitting", "great on the training set, unknown on new data", LEFT * 3.0 + DOWN * 1.8,
                          width=6.2)
        self.play(FadeOut(Group(knobs, pts, kl, pl, t1, t2)), run_time=0.6)

        # 3. the loss is a choice
        nar.say("The loss is a design choice: it decides what we aim for.")
        ax = Axes(x_range=[-2, 2, 1], y_range=[0, 4, 1], x_length=5.6, y_length=3.0,
                  axis_config={"include_numbers": True, "font_size": 24}, tips=False).move_to(LEFT * 3.4 + UP * 0.4)
        sq = lambda e: (Value(e) ** 2).data
        ab = lambda e: (Value(e).relu() + (-Value(e)).relu()).data
        cs_ = ax.plot(sq, x_range=[-2, 2], color=DATA)
        ca_ = ax.plot(ab, x_range=[-2, 2], color=TEAL, use_smoothing=False)
        el = Text("error = prediction - target", font_size=24, color=SECOND).next_to(ax, DOWN, buff=0.1)
        keys = VGroup(Text("squared", font_size=26, color=DATA), Text("absolute", font_size=26, color=TEAL)
                      ).arrange(RIGHT, buff=0.6).next_to(ax, UP, buff=0.12)
        self.play(Create(ax), FadeIn(el), FadeIn(keys), run_time=1.0)
        self.play(Create(cs_), Create(ca_), run_time=1.5)
        e = ValueTracker(0.5)
        d1 = always_redraw(lambda: Dot(ax.c2p(e.get_value(), sq(e.get_value())), radius=0.1, color=ACTIVE))
        d2 = always_redraw(lambda: Dot(ax.c2p(e.get_value(), ab(e.get_value())), radius=0.1, color=ACTIVE))
        self.add(d1, d2)
        self.play(e.animate.set_value(1.5), run_time=2.0)
        self.wait(1.0)
        ev = Value(1.5)
        (ev ** 2).backward()
        g_sq = ev.grad
        assert abs(g_sq - 3.0) < 1e-12
        nar.say("A mistake of 1.5 pulls with 3 under squared loss, 1 under absolute.")
        w = working_line(self, r"\frac{d}{de}\,e^2=2e", r"2\cdot1.5", fmt(g_sq),
                         pos=RIGHT * 3.6 + UP * 1.0, width=5.2, hold=2.2)
        self.wait(1.0)
        self.play(FadeOut(w), FadeOut(Group(ax, el, keys, cs_, ca_, d1, d2)), run_time=0.6)
        self.remove(d1, d2)

        # 4. what real training adds
        nar.say("Real training adds four things to this loop.")
        cards = [
            ("Mini-batches", "a random few examples per step", YELLOW),
            ("Other losses", "cross-entropy, max-margin", TEAL),
            ("L2 regularisation", "penalise big weights", ORANGE),
            ("Learning-rate decay", "big steps first, small later", GREEN),
        ]
        group = VGroup(*[callout(t, b, color=col, width=5.6) for t, b, col in cards])
        group.arrange_in_grid(rows=2, cols=2, buff=(0.5, 0.45)).move_to(UP * 0.5)
        for c in group:
            self.play(FadeIn(c), run_time=0.7)
            self.wait(1.2)
        self.play(Indicate(group[3], color=ACTIVE), run_time=1.2)
        self.wait(2.5)
        dax = Axes(x_range=[0, 10, 5], y_range=[0, 0.3, 0.1], x_length=3.0, y_length=1.3,
                   axis_config={"include_numbers": False}, tips=False).move_to(DOWN * 2.0 + RIGHT * 0.0)
        lrs = [0.3 * (0.8 ** i) for i in range(11)]
        dc = dax.plot_line_graph(list(range(11)), lrs, line_color=GREEN, add_vertex_dots=False)
        dl = Text("learning rate over time", font_size=24, color=SECOND).next_to(dax, RIGHT, buff=0.3)
        self.play(Create(dax), Create(dc), FadeIn(dl), run_time=1.5)
        self.wait(3.0)
