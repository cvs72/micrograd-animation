import random

from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, Narrator, act_banner, arrow_between, callout,
    code_panel, fmt, make_value_node, particle_flow, recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value

config.background_color = BLACK

XS = [1.0, -0.5, 0.8]
TARGET = 1.0
LAYER_X = [-5.6, -2.9, -0.2]
CHAPTERS = ["1 Derivative", "2 Many inputs", "3 Graph", "4 Backward pass",
            "5 Neuron", "6 Automation", "7 Accumulation", "8 More operations",
            "9 PyTorch", "10 Network", "11 Training", "12 Loss surface"]

README_CODE = """a = Value(-4.0)
b = Value(2.0)
c = a + b
d = a * b + b**3
c += c + 1
c += 1 + c + (-a)
d += d * 2 + (b + a).relu()
d += 3 * d + (b - a).relu()
e = c - d
f = e**2
g = f / 2.0
g += 10.0 / f"""


def readme(da=0.0):
    """The README expression (same steps as test_readme_example); da nudges a."""
    a = Value(-4.0 + da)
    b = Value(2.0)
    c = a + b
    d = a * b + b**3
    c += c + 1
    c += 1 + c + (-a)
    d += d * 2 + (b + a).relu()
    d += 3 * d + (b - a).relu()
    e = c - d
    f = e**2
    g = f / 2.0
    g += 10.0 / f
    return a, b, g


RA, RB, RG = readme()
RG.backward()
assert round(RG.data, 4) == 24.7041
assert round(RA.grad, 4) == 138.8338 and round(RB.grad, 4) == 645.5773
NUDGE_H = 0.001
G_NUDGED = readme(NUDGE_H)[2].data
NUDGE_SLOPE = (G_NUDGED - RG.data) / NUDGE_H
assert abs(NUDGE_SLOPE - RA.grad) < 1.0


def make_weights():
    rng = random.Random(3)
    w1 = [[rng.uniform(-1, 1) for _ in range(3)] for _ in range(4)]
    w2 = [rng.uniform(-1, 1) for _ in range(4)]
    return w1, w2


W1, W2 = make_weights()


def loss_with(knob_a, da, knob_b, db):
    """Loss of the 3-4-1 network with two knobs shifted; every number comes from Value."""
    w1 = [[Value(w) for w in row] for row in W1]
    w2 = [Value(w) for w in W2]
    for (kind, idx), d in ((knob_a, da), (knob_b, db)):
        tgt = w1[idx[0]][idx[1]] if kind == "w1" else w2[idx[0]]
        tgt.data += d
    hidden = []
    for j in range(4):
        s = Value(0.0)
        for i in range(3):
            s = s + w1[j][i] * XS[i]
        hidden.append(s.tanh())
    out = Value(0.0)
    for j in range(4):
        out = out + w2[j] * hidden[j]
    out = out.tanh()
    loss = (out - TARGET) ** 2
    return loss, w1, w2


def knob_grad(knob):
    loss, w1, w2 = loss_with(knob, 0.0, knob, 0.0)
    loss.backward()
    kind, idx = knob
    return (w1[idx[0]][idx[1]] if kind == "w1" else w2[idx[0]]).grad


KNOB_A = ("w2", (1,))
KNOB_B = ("w1", (2, 0))
SA = 1.0 if knob_grad(KNOB_A) > 0 else -1.0  # uphill: blind turn makes loss worse
SB = -1.0 if knob_grad(KNOB_B) > 0 else 1.0  # downhill: a lucky turn
AMP = 1.5
BASE_LOSS = loss_with(KNOB_A, 0, KNOB_B, 0)[0].data
WORSE = loss_with(KNOB_A, SA * AMP, KNOB_B, 0)[0].data
BETTER = loss_with(KNOB_A, 0, KNOB_B, SB * AMP)[0].data
assert WORSE > BASE_LOSS + 0.1 and BETTER < BASE_LOSS - 0.05
LMAX = max(WORSE, BASE_LOSS) * 1.15


class Scene00Intro(MovingCameraScene):
    def zoom_on(self, nar, target, factor, hold):
        """Zoom the camera onto target for `hold` seconds; the caption follows the frame."""
        frame = self.camera.frame
        cap = nar.current
        base_w = cap.width

        def follow(m):
            k = frame.width / config.frame_width
            m.set_width(base_w * k)
            m.move_to(frame.get_bottom() + UP * (m.height / 2 + 0.2 * k))

        cap.add_updater(follow)
        self.play(frame.animate.scale(factor).move_to(target.get_center()), run_time=0.9)
        self.wait(hold)
        self.play(frame.animate.scale(1 / factor).move_to(ORIGIN), run_time=0.9)
        cap.remove_updater(follow)
        follow(cap)

    def readme_demo(self, nar):
        code = code_panel(README_CODE, font_size=24)
        code.scale_to_fit_width(6.8)
        code.to_edge(LEFT, buff=0.5).to_edge(UP, buff=0.6)
        nar.say("This is the demo from the micrograd README: a and b go in.")
        self.play(FadeIn(code), run_time=1)
        nar.say("The expression is meaningless. It only shows what the engine can do.")
        hl = SurroundingRectangle(code.code_lines[3], color=ACTIVE, buff=0.05)
        self.play(Create(hl))
        for i in (6, 7, 11):
            self.play(Transform(hl, SurroundingRectangle(code.code_lines[i], color=ACTIVE, buff=0.05)),
                      run_time=0.8)
        self.play(FadeOut(hl))
        # forward value
        g_q = MathTex(r"g = ?", font_size=44, color=DATA).move_to([3.7, 2.7, 0])
        nar.say("Run it forward and out comes one number, g.")
        self.play(FadeIn(g_q))
        g_tex = MathTex(rf"g = {fmt(RG.data)}", font_size=44, color=DATA).move_to(g_q)
        fwd = Arrow([code.get_right()[0] + 0.15, 2.7, 0], [g_tex.get_left()[0] - 0.15, 2.7, 0],
                    color=FWD, buff=0, stroke_width=5)
        self.play(FadeIn(fwd), run_time=0.6)
        self.play(TransformMatchingTex(g_q, g_tex), Indicate(g_tex, color=FWD))
        # predict then reveal the slope of a
        qa = MathTex(r"\frac{\partial g}{\partial a} = ?", font_size=44, color=GRAD).move_to([3.9, 1.3, 0])
        qb = MathTex(r"\frac{\partial g}{\partial b} = ?", font_size=44, color=GRAD).move_to([3.9, 0.0, 0])
        nar.say("Backward asks: how fast does g change if we nudge a or b?")
        self.play(FadeIn(qa), FadeIn(qb))
        for _ in range(3):  # pulse the question marks for about 3 seconds
            self.play(Indicate(qa, color=ACTIVE, scale_factor=1.12),
                      Indicate(qb, color=ACTIVE, scale_factor=1.12), run_time=1.0)
        ra = MathTex(rf"\frac{{\partial g}}{{\partial a}} = {fmt(RA.grad)}", font_size=44,
                     color=GRAD).move_to(qa)
        rb = MathTex(rf"\frac{{\partial g}}{{\partial b}} = {fmt(RB.grad)}", font_size=44,
                     color=GRAD).move_to(qb)
        bwd_a = Arrow(ra.get_left() + LEFT * 0.1, [code.get_right()[0] + 0.1, 1.3, 0],
                      color=BWD, buff=0, stroke_width=5)
        bwd_b = Arrow(rb.get_left() + LEFT * 0.1, [code.get_right()[0] + 0.1, 0.0, 0],
                      color=BWD, buff=0, stroke_width=5)
        nar.say(f"Nudge a up a little and g grows about {RA.grad:.1f} times as fast.")
        self.play(ReplacementTransform(qa, ra), ReplacementTransform(qb, rb))
        self.play(FadeIn(bwd_a), FadeIn(bwd_b), run_time=0.6)
        # check the slope with a real nudge, zoomed in
        pos = np.array([3.9, -1.9, 0.0])
        nar.say("Check it: nudge a by h = 0.001 and see how far g really moves.")
        step = MathTex(rf"\text{{check }}\partial g/\partial a:\ a = {fmt(-4.0)} \to {fmt(-4.0 + NUDGE_H)},\ h = {NUDGE_H}",
                       font_size=36, color=DATA).scale_to_fit_width(6.0).move_to([3.9, -0.95, 0])
        self.play(FadeIn(step))
        w = working_line(
            self, r"\frac{g(a+h)-g(a)}{h}",
            rf"\frac{{{fmt(G_NUDGED)}-{fmt(RG.data)}}}{{{NUDGE_H}}}",
            rf"\frac{{{fmt(G_NUDGED)}-{fmt(RG.data)}}}{{{NUDGE_H}}} = {fmt(NUDGE_SLOPE)}",
            pos=pos, width=6.0, hold=0.5)
        code.save_state()
        self.play(code.animate.set_opacity(0.0), run_time=0.4)
        self.zoom_on(nar, w, 0.6, 0.3)
        nar.say(f"A bigger h gives {fmt(NUDGE_SLOPE)}; as h shrinks it closes in on {fmt(RA.grad)}.")
        self.play(FadeOut(w), FadeOut(step), Restore(code))
        # gradient callout, below the two gradients so it covers nothing
        co = callout("Gradient", "how fast the output moves\nwhen an input is nudged",
                     color=GRAD, width=5.4).move_to([3.7, -1.55, 0])
        nar.say("Backprop works on any expression. Neural nets are a calmer one.")
        self.play(FadeIn(co))
        self.wait(3.0)
        nar.say("micrograd uses single numbers on purpose; tensors only add speed.")
        self.play(FadeOut(co))
        self.play(FadeOut(Group(code, g_tex, ra, rb, fwd, bwd_a, bwd_b)))

    def construct(self):
        nar = Narrator(self, "S00")
        title_card(self, "Chapter 0",
                   "Which way should we turn each knob?")
        self.readme_demo(nar)

        # ---- network drawn as circles and lines
        ys = [[0.3 + 1.6 * (1 - i) for i in range(3)],
              [0.3 + 1.3 * (1.5 - j) for j in range(4)],
              [0.3]]
        layers = []
        for x, col_y in zip(LAYER_X, ys):
            layers.append([Circle(radius=0.28, color=WHITE, stroke_width=3)
                           .move_to([x, y, 0]) for y in col_y])
        lines = {}
        for li in range(2):
            for a, na in enumerate(layers[li]):
                for b, nb in enumerate(layers[li + 1]):
                    lines[(li, a, b)] = Line(na.get_right(), nb.get_left(),
                                             color=GREY_B, stroke_width=2)
        heading = Text("A tiny network: 16 knobs (weights)", font_size=30, color=SECOND)
        heading.to_edge(UP, buff=0.5)
        net = VGroup(*[n for l in layers for n in l], *lines.values())
        assert len(lines) == 16
        self.play(Create(VGroup(*lines.values())), run_time=1.5)
        layer_names = VGroup(*[
            Text(t, font_size=28, color=WHITE).move_to([x, -2.2, 0])
            for t, x in zip(["inputs", "hidden", "output"], LAYER_X)])
        self.play(FadeIn(VGroup(*[n for l in layers for n in l])), FadeIn(heading),
                  FadeIn(layer_names), run_time=1)
        nar.say("This tiny network has sixteen knobs; real ones have millions.")
        # slider handles on a few lines
        ka = lines[(1, 1, 0)]   # hidden 1 -> output  (KNOB_A)
        kb = lines[(0, 0, 2)]   # input 0 -> hidden 2 (KNOB_B)
        others = [lines[(0, 1, 0)], lines[(0, 2, 3)], lines[(1, 3, 0)]]
        ta, tb = ValueTracker(0), ValueTracker(0)

        def handle(line, tracker, sign):
            return always_redraw(lambda: Dot(
                line.point_from_proportion(0.5 + 0.18 * sign * tracker.get_value()),
                radius=0.2, color=ACTIVE).set_stroke(WHITE, 3))

        h_a, h_b = handle(ka, ta, SA), handle(kb, tb, SB)
        h_o = [Dot(l.point_from_proportion(0.5), radius=0.2, color=ACTIVE).set_stroke(WHITE, 3)
               for l in others]
        tracks = VGroup(*[
            Line(l.point_from_proportion(0.28), l.point_from_proportion(0.72),
                 color=GREY_A, stroke_width=10, stroke_opacity=0.6)
            for l in [ka, kb] + others])
        self.add(tracks)
        self.bring_to_front(*[m for m in self.mobjects if isinstance(m, Circle)])
        self.play(FadeIn(h_a), FadeIn(h_b), *[FadeIn(h) for h in h_o],
                  ka.animate.set_color(ACTIVE).set_stroke(width=7),
                  kb.animate.set_color(ACTIVE).set_stroke(width=7))
        self.wait(0.4)

        # ---- code panel + value node: a knob is a number
        code = code_panel(f"w = Value({fmt(W2[1])})\nloss = (out - 1) ** 2", font_size=24)
        code.move_to([3.9, 2.2, 0])
        knob_node = make_value_node("knob w", W2[1])
        knob_node.move_to([4.6, 0.1, 0])
        nar.say("In code, every knob is just a number.")
        self.play(FadeIn(code), FadeIn(knob_node))
        self.play(Indicate(knob_node.data_t, color=ACTIVE))

        # ---- loss readout and bar
        def current_loss():
            return loss_with(KNOB_A, SA * AMP * ta.get_value(),
                             KNOB_B, SB * AMP * tb.get_value())[0].data

        def readout():
            L = current_loss()
            col = GRAD if L > BASE_LOSS + 1e-3 else (FWD if L < BASE_LOSS - 1e-3 else DATA)
            return Text(f"loss = {fmt(L)}", font_size=34, color=col).move_to([3.5, 1.6, 0])

        def bar():
            L = current_loss()
            col = GRAD if L > BASE_LOSS + 1e-3 else (FWD if L < BASE_LOSS - 1e-3 else DATA)
            h = max(0.05, min(L / LMAX, 1.0) * 3.0)
            return Rectangle(width=0.9, height=h, fill_color=col, fill_opacity=0.9,
                             stroke_width=0).move_to([5.6, -2.4 + h / 2, 0])

        frame_bar = Rectangle(width=0.9, height=3.0, color=GREY_B, stroke_width=2)
        frame_bar.move_to([5.6, -0.9, 0])
        ty = -2.4 + BASE_LOSS / LMAX * 3.0
        base_tick = Line([5.0, ty, 0], [6.2, ty, 0], color=WHITE, stroke_width=2)
        bar_label = Text("mistake", font_size=24, color=SECOND).next_to(frame_bar, LEFT, buff=0.3)
        tick_label = Text("start", font_size=24, color=WHITE).next_to(base_tick, LEFT, buff=0.1)
        bar_label.next_to(frame_bar, DOWN, buff=0.15)
        nar.say("The loss measures how wrong we are. Lower is better.")
        self.play(FadeOut(code), FadeOut(knob_node))
        r = always_redraw(readout)
        b = always_redraw(bar)
        self.play(FadeIn(r), Create(frame_bar), FadeIn(bar_label), FadeIn(b),
                  Create(base_tick), FadeIn(tick_label))
        self.wait(0.2)

        # ---- blind turn makes it worse
        nar.say("Turn one knob blindly and the mistake grows: wrong way!")
        self.play(ta.animate.set_value(1.0), run_time=1.0, rate_func=smooth)
        q = Text("?", font_size=80, color=ACTIVE, weight=BOLD).next_to(h_a, UP, buff=0.25)
        self.play(FadeIn(q, scale=1.5))
        self.play(Indicate(q, color=WHITE))
        self.play(ta.animate.set_value(0.0), FadeOut(q), run_time=1.0)

        # ---- another knob, lucky
        nar.say("Another knob, other direction: lucky this time, the loss falls.")
        self.play(tb.animate.set_value(1.0), run_time=1.0, rate_func=smooth)
        nar.say("But luck will not scale to thousands of knobs. We need a direction.")
        flow = particle_flow(ka, knob_grad(KNOB_A), reverse=True, run_time=1.5)
        self.play(Circumscribe(r, color=ACTIVE), flow)
        self.remove(flow.dots)
        nar.clear()
        r.clear_updaters()
        b.clear_updaters()
        self.remove(h_a, h_b)
        self.play(FadeOut(Group(*self.mobjects)))

        # ---- roadmap, lights up chapter by chapter
        boxes = VGroup(*[
            VGroup(RoundedRectangle(corner_radius=0.15, width=3.0, height=1.0,
                                    stroke_color=GREY_B, stroke_width=3),
                   Text(c, font_size=24, color=WHITE))
            for c in CHAPTERS])
        for bx in boxes:
            bx[1].move_to(bx[0])
        grid = VGroup(*boxes).arrange_in_grid(rows=3, cols=4, buff=(0.3, 0.4)).move_to([0, 0.3, 0])
        title = Text("Roadmap: twelve chapters", font_size=34, color=ACTIVE).to_edge(UP, buff=0.5)
        nar.say("Here is our plan: twelve short chapters, one idea each.")
        self.play(FadeIn(title), Create(grid))
        notes = {0: "First slopes, several inputs, and the computation graph.",
                 3: "Then the backward pass, one neuron, and automating it.",
                 6: "Next, adding up gradients, more operations, and PyTorch.",
                 9: "Finally a whole network, training it, and a loss surface."}
        for i, bx in enumerate(boxes):
            if i in notes:
                nar.say(notes[i])
            self.play(bx[0].animate.set_fill(ACTIVE, opacity=0.35).set_stroke(ACTIVE),
                      bx[1].animate.set_color(ACTIVE), run_time=0.35)
            self.play(bx[0].animate.set_fill(FWD, opacity=0.12).set_stroke(FWD),
                      bx[1].animate.set_color(WHITE), run_time=0.2)
        self.play(FadeOut(grid), FadeOut(title))

        # ---- the three-act pattern
        nar.say("Every chapter has three acts, so you see each idea three times.")
        specs = [("Example A: the lecture's numbers", DATA, 2.5),
                 ("Example B: what if?", ACTIVE, 0.9),
                 ("Expert corner: what experts add", GRAD, -0.7)]
        banners = VGroup()
        for t, c, y in specs:
            banners.add(act_banner(self, t, color=c, keep=True, pos=[2.2, y, 0]))
        axes = [Axes(x_range=[-2, 2], y_range=[0, 4], x_length=1.8, y_length=1.2,
                     tips=False, axis_config={"stroke_width": 2}).move_to([-4.6, y, 0])
                for y in (2.5, 0.9)]
        curve_a = axes[0].plot(lambda x: x * x, color=DATA)
        curve_b = axes[1].plot(lambda x: x * x, color=DATA)
        curve_b2 = axes[1].plot(lambda x: 0.5 * x ** 3 - x + 2, color=ACTIVE)
        lens = VGroup(Circle(radius=0.35, color=GRAD),
                      Line(DL * 0.25, DL * 0.6, color=GRAD, stroke_width=6)
                      ).move_to([-4.6, -0.7, 0])
        self.play(Create(axes[0]), Create(curve_a), Create(axes[1]), Create(curve_b), Create(lens))
        nar.say("A uses the lecture's numbers; B changes them and watches what moves.")
        self.play(Transform(curve_b, curve_b2), run_time=1.0)
        self.play(Indicate(banners[0]), run_time=0.5)
        self.play(Indicate(banners[1]), run_time=0.5)
        nar.say("The expert corner adds what a specialist would warn you about.")
        self.play(Indicate(banners[2]), Indicate(lens), run_time=1.0)
        question = MathTex(r"\text{Next: what is a derivative, really?}", font_size=48,
                           color=WHITE).move_to([0, -1.9, 0])
        qbox = SurroundingRectangle(question, color=ACTIVE, buff=0.2, corner_radius=0.1)
        self.play(FadeIn(question), Create(qbox), run_time=0.5)
        nar.say("Chapter 1 answers it, starting with simple slopes.")
        nar.finish()
        self.play(FadeOut(Group(*self.mobjects)))
        recap_line(self, "What is a derivative, really?", color=ACTIVE)
