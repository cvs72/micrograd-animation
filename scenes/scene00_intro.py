import random

from manim import *

from micrograd_animation.anim import (
    ACTIVE, DATA, FWD, GRAD, SECOND, Narrator, arrow_between, code_panel, fmt,
    make_value_node, recap_line, title_card,
)
from micrograd_animation.engine import Value

config.background_color = BLACK

XS = [1.0, -0.5, 0.8]
TARGET = 1.0
LAYER_X = [-5.8, -3.3, -0.8]
CHAPTERS = ["Slope", "Nudges", "Graph", "Backward pass",
            "Neuron", "Automation", "Accumulation", "Training"]


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


class Scene00Intro(Scene):
    def construct(self):
        nar = Narrator(self, "S00")
        title_card(self, "Chapter 0",
                   "Which way should we turn each knob?")

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
        self.play(FadeIn(VGroup(*[n for l in layers for n in l])), FadeIn(heading),
                  run_time=1)
        nar.say("This tiny network has sixteen knobs, called weights.")
        self.wait(1)
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
        nar.say("A real network has thousands, or millions of them.")
        self.wait(1.5)

        # ---- code panel + value node: a knob is a number
        code = code_panel(f"w = Value({fmt(W2[1])})\nloss = (out - 1) ** 2", font_size=24)
        code.move_to([3.9, 2.2, 0])
        knob_node = make_value_node("knob w", W2[1])
        knob_node.move_to([4.6, 0.1, 0])
        nar.say("In code, every knob is just a number.")
        self.play(FadeIn(code), FadeIn(knob_node))
        self.play(Indicate(knob_node.data_t, color=ACTIVE))
        self.wait(1)

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
        nar.say("The loss measures how wrong we are. Lower is better.")
        self.play(FadeOut(code), FadeOut(knob_node))
        r = always_redraw(readout)
        b = always_redraw(bar)
        self.play(FadeIn(r), Create(frame_bar), FadeIn(bar_label), FadeIn(b),
                  Create(base_tick))
        self.wait(1.5)

        # ---- blind turn makes it worse
        nar.say("Let us turn one knob blindly and watch the loss.")
        self.play(ta.animate.set_value(1.0), run_time=3, rate_func=smooth)
        q = Text("?", font_size=80, color="#FF5555", weight=BOLD).move_to([6.1, 1.6, 0])
        nar.say("Oops. The mistake got bigger. We turned the wrong way.")
        self.play(FadeIn(q, scale=1.5))
        self.play(Indicate(q, color=RED))
        self.wait(1)
        self.play(ta.animate.set_value(0.0), FadeOut(q), run_time=1.5)

        # ---- another knob, lucky
        nar.say("Another knob, other direction: lucky, the loss falls.")
        self.play(tb.animate.set_value(1.0), run_time=3, rate_func=smooth)
        self.wait(1)
        nar.say("With thousands of knobs, guessing is hopeless. We need a direction.")
        self.play(Circumscribe(r, color=ACTIVE), run_time=2)
        self.wait(1)
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
        dd = Text("a", font_size=24).get_bottom()[1] - Text("g", font_size=24).get_bottom()[1]
        for bx, c in zip(boxes, CHAPTERS):
            bx[1].move_to(bx[0])
            base = bx[1].get_bottom()[1] + (dd if any(ch in "gjpqy" for ch in c) else 0)
            bx[1].shift(UP * (bx[0].get_center()[1] - 0.09 - base))
            if c == "Training":  # glyph bbox quirk: measured 3 px high
                bx[1].shift(DOWN * 0.04)
        row1 = VGroup(*boxes[:4]).arrange(RIGHT, buff=0.4).move_to([0, 1.1, 0])
        row2 = VGroup(*boxes[4:]).arrange(RIGHT, buff=0.4).move_to([0, -0.9, 0])
        arrows = [arrow_between(boxes[i][0], boxes[i + 1][0], color=SECOND, buff=0.02)
                  for i in range(7) if i != 3]
        p1, p4 = row1[3][0].get_bottom(), row2[0][0].get_top()
        p2, p3 = p1 + DOWN * 0.5, np.array([p4[0], p1[1] - 0.5, 0])
        turn = VGroup(Line(p1, p2, color=SECOND, stroke_width=3),
                      Line(p2, p3, color=SECOND, stroke_width=3),
                      Arrow(p3, p4, color=SECOND, buff=0, stroke_width=3, tip_length=0.2))
        title = Text("Roadmap", font_size=34, color=ACTIVE).to_edge(UP, buff=0.5)
        nar.say("Here is our plan for the next chapters.")
        self.play(FadeIn(title), Create(row1), Create(row2),
                  *[Create(a) for a in arrows], Create(turn))
        self.wait(1)
        for i, bx in enumerate(boxes):
            if i == 0:
                nar.say("First we learn about slopes, then about nudges.")
            if i == 2:
                nar.say("Next, the graph and the backward pass.")
            if i == 4:
                nar.say("Then one neuron, and automating the backward pass.")
            if i == 6:
                nar.say("Last, adding up gradients, and training a network.")
            self.play(bx[0].animate.set_fill(ACTIVE, opacity=0.35).set_stroke(ACTIVE),
                      bx[1].animate.set_color(ACTIVE), run_time=0.5)
            self.wait(0.8)
            self.play(bx[0].animate.set_fill(ACTIVE, opacity=0).set_stroke(FWD),
                      bx[1].animate.set_color(WHITE), run_time=0.4)
        nar.say("It all starts with a question about slopes.")
        self.play(Indicate(boxes[0][0], color=ACTIVE), run_time=1.5)
        nar.finish()
        self.play(FadeOut(Group(*self.mobjects)))
        recap_line(self, "What is a derivative, really?", color=ACTIVE)
