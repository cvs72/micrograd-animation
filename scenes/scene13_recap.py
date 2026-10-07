import math

from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, chapter_icon,
    fmt, title_card, working_line,
)
from micrograd_animation.nn import MLP

XS = [[2.0, 3.0, -1.0], [3.0, -1.0, 0.5], [0.5, 1.0, 1.0], [1.0, 1.0, -1.0]]
YS = [1.0, -1.0, -1.0, 1.0]
LABELS = ["slope", "inputs", "graph", "backward", "neuron", "order",
          "add up", "more ops", "tensors", "network", "training", "surface"]
LR = 0.05


def one_knob():
    """Knob 0 of the seed-1 network: value, gradient and the value after one step."""
    net = MLP(3, [4, 4, 1], seed=1)
    loss = sum((net(x) - y) ** 2 for x, y in zip(XS, YS))
    for p in net.parameters():
        p.grad = 0.0
    loss.backward()
    p = net.parameters()[0]
    return len(net.parameters()), p.data, p.grad, p.data - LR * p.grad, loss.data


class Scene13Recap(Scene):
    def tag(self, text):
        return Tex(r"\textbf{" + text + "}", font_size=34, color=ACTIVE).to_corner(UL, buff=0.5)

    def fade_all(self):
        cur = self.nar.current
        old = [m for m in self.mobjects if m is not cur]
        if old:
            self.play(FadeOut(Group(*old)), run_time=0.6)
            self.remove(*old)

    def construct(self):
        n_params, w0, g0, w1, loss0 = one_knob()
        assert n_params == 41
        assert abs(w1 - (w0 - LR * g0)) < 1e-12
        self.nar = nar = CrossfadeNarrator(self, "S13")

        title_card(self, "Chapter 13", "What did we build, and where next?")

        # ---------------------------------------------------------- roadmap replay
        banner = act_banner(self, "The twelve chapters, replayed", keep=True)
        nar.say("The whole journey: twelve chapters, each in one tiny picture.")
        icons = VGroup()
        for k in range(1, 13):
            ic, anim = chapter_icon(k)
            ic.anim = anim
            icons.add(ic)
        icons.arrange_in_grid(2, 6, buff=(0.45, 0.85))
        icons.move_to([0, 0.35, 0])
        labels = VGroup()
        for k, ic in enumerate(icons):
            num = Text(f"{k + 1}  {LABELS[k]}", font_size=24, color=WHITE if k else WHITE)
            num.next_to(ic, DOWN, buff=0.12)
            labels.add(num)
        self.play(FadeIn(icons, lag_ratio=0.1), FadeIn(labels, lag_ratio=0.1), run_time=2.0)
        self.wait(1.0)
        caps = {
            0: "Slopes first: how fast does the output move if an input moves?",
            2: "Several inputs: each one gets its own slope, its own sensitivity.",
            5: "Order matters: a node goes backward only after all nodes after it.",
            8: "Tensors pack many scalars together, purely for speed.",
            11: "The loss surface is an analogy: real networks cannot be pictured.",
            3: "Then graphs: each number remembers its inputs, so we can walk back.",
            6: "Gradients add up, and any operation works if its slope is right.",
            9: "Then networks: layers of neurons, trained by gradient descent.",
        }
        for k, ic in enumerate(icons):
            if k in caps:
                nar.say(caps[k])
            self.play(Indicate(ic.box, color=ACTIVE, scale_factor=1.12), *ic.anim(), run_time=1.8)
            ic.box.set_stroke(TEAL, 3)
        self.wait(1.0)
        self.play(FadeOut(banner), run_time=0.4)

        # ---------------------------------------------------------- three-act pattern
        self.play(FadeOut(icons), FadeOut(labels), run_time=0.6)
        nar.say("Every chapter had three acts. Keep that pattern for your own study.")
        cards = VGroup()
        specs = [
            ("Example A", "the lecture's own numbers", BLUE),
            ("Example B", "change the values, watch", TEAL),
            ("Expert corner", "what an expert adds", ORANGE),
        ]
        for title, body, col in specs:
            t = Text(title, font_size=36, color=col, weight=BOLD)
            b = Text(body, font_size=26, color=WHITE)
            g = VGroup(t, b).arrange(DOWN, buff=0.25)
            box = RoundedRectangle(corner_radius=0.15, width=4.2, height=2.2, stroke_color=col,
                                   stroke_width=3)
            g.move_to(box)
            cards.add(VGroup(box, g))
        cards.arrange(RIGHT, buff=0.3).move_to([0, 0.4, 0])
        # a small picture above each card: a fixed value, a morphing value, a star
        sq = Square(0.5, color=BLUE, fill_opacity=0.8).next_to(cards[0], UP, buff=0.35)
        sq2 = Square(0.5, color=TEAL, fill_opacity=0.8).next_to(cards[1], UP, buff=0.35)
        star = Star(color=ORANGE, fill_opacity=0.8, outer_radius=0.3).next_to(cards[2], UP, buff=0.35)
        self.play(FadeIn(cards[0]), FadeIn(sq), run_time=0.8)
        self.wait(1.0)
        self.play(FadeIn(cards[1]), FadeIn(sq2), run_time=0.8)
        self.play(Transform(sq2, Circle(radius=0.3, color=TEAL, fill_opacity=0.8).move_to(sq2)),
                  run_time=1.0)
        self.wait(1.0)
        self.play(FadeIn(cards[2]), FadeIn(star), run_time=0.8)
        self.play(Indicate(star, color=YELLOW), run_time=1.0)
        self.wait(2.0)

        # ---------------------------------------------------------- scale ladder
        self.play(FadeOut(cards), FadeOut(sq), FadeOut(sq2), FadeOut(star), run_time=0.6)
        nar.say("Our network had 41 parameters; real language models have billions.")
        banner = act_banner(self, "A scale ladder", keep=True)
        rungs = [(n_params, "41", "this video"), (1e6, r"10^{6}", "millions"),
                 (1e9, r"10^{9}", "billions"), (1e11, r"10^{11}", "hundreds of billions")]
        base = -2.0
        unit = 0.25
        bars, tags, caps_t = VGroup(), VGroup(), VGroup()
        xs = [-4.5, -1.5, 1.5, 4.5]
        axis = Line([-6, base, 0], [6, base, 0], color=GREY_B)
        for (n, ml, name), x in zip(rungs, xs):
            h = max(math.log10(n), 0.2) * unit
            bar = Rectangle(width=1.4, height=h, fill_color=DATA, fill_opacity=0.85,
                            stroke_width=0).move_to([x, base + h / 2, 0])
            bars.add(bar)
            tags.add(MathTex(ml, font_size=40, color=DATA).move_to([x, base + h + 0.35, 0]))
            caps_t.add(Text(name, font_size=24, color=WHITE).move_to([x, base - 0.3, 0]))
        ylab = Text("height = number of digits", font_size=24, color=SECOND).move_to([0, 2.2, 0])
        self.play(Create(axis), FadeIn(caps_t), FadeIn(ylab), run_time=1.0)
        for bar, tg in zip(bars, tags):
            self.play(GrowFromEdge(bar, DOWN), FadeIn(tg), run_time=1.2)
        self.wait(1.5)
        nar.say("They learn to guess the next word, with the very same arithmetic.")
        self.play(Indicate(bars[3], color=ACTIVE), Indicate(bars[0], color=ACTIVE), run_time=1.5)
        self.wait(1.5)
        self.play(FadeOut(banner), run_time=0.4)

        # ---------------------------------------------------------- the big sentence
        self.play(FadeOut(VGroup(axis, bars, tags, caps_t, ylab)), run_time=0.6)
        nar.say("Remember: the gradient tells every knob which way to turn.")
        big = MathTex(r"\nabla L = \left(\frac{\partial L}{\partial w_1}, \ldots, "
                      r"\frac{\partial L}{\partial w_{41}}\right)", font_size=44, color=GRAD)
        big.move_to([0, 1.8, 0])
        sentence = Text("which way to turn, and how much it matters", font_size=30, color=WHITE)
        sentence.next_to(big, DOWN, buff=0.4)
        self.play(FadeIn(big), run_time=0.8)
        self.play(FadeIn(sentence), run_time=0.8)
        self.wait(2.0)
        nar.say("Here it is on one real knob: its gradient decides the step.")
        step = working_line(
            self,
            r"w \leftarrow w - \eta \, \frac{\partial L}{\partial w}",
            rf"w \leftarrow {fmt(w0)} - {LR} \cdot ({fmt(g0)})",
            rf"w \leftarrow {fmt(w1)}",
            pos=[0, -0.7, 0], width=7.0, hold=2.0, colors=(WHITE, DATA, GRAD))
        self.wait(1.0)
        self.play(FadeOut(VGroup(big, sentence, step)), run_time=0.6)

        # ---------------------------------------------------------- what next
        nar.say("Next in Karpathy's series: makemore, a small language model.")
        c1 = callout("Next lecture: makemore", "a language model that predicts the next letter",
                     color=TEAL, width=9.0).move_to([0, 1.3, 0])
        c2 = callout("What you can now do", "explain backprop with your own numbers",
                     color=ACTIVE, width=9.0).move_to([0, -0.6, 0])
        self.play(FadeIn(c1), run_time=0.6)
        self.wait(3.0)
        self.play(FadeIn(c2), run_time=0.6)
        self.wait(3.2)
        nar.clear()
        self.play(FadeOut(c1), FadeOut(c2), run_time=0.6)

        # ---------------------------------------------------------- credit card
        line1 = Text("Based on Andrej Karpathy's micrograd lecture", font_size=36, color=WHITE)
        line2 = Text("(Neural Networks: Zero to Hero)", font_size=30, color=SECOND)
        credit = VGroup(line1, line2).arrange(DOWN, buff=0.3)
        if credit.width > 12.5:
            credit.scale_to_fit_width(12.5)
        self.play(FadeIn(credit), run_time=0.6)
        self.wait(4.0)
        self.play(FadeOut(credit), run_time=0.5)
        nar.finish()
