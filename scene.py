from manim import *

IDLE, FWD, BWD = GRAY, TEAL, ORANGE
NODE_W, NODE_H, OP_R = 2.3, 1.35, 0.35

A_POS, B_POS = [-4.6, 1.4, 0], [-4.6, -0.8, 0]
MUL_POS, E_POS, C_POS = [-2.3, 0.3, 0], [0, 0.3, 0], [0, -1.9, 0]
ADD_POS, D_POS = [2.3, -0.8, 0], [4.6, -0.8, 0]


def fmt(x):
    return f"{x:g}".replace("-", "−")


def value_line(label, x):
    return Text(f"{label} = {fmt(x)}", font_size=24)


def make_node(name, data, pos):
    """Rounded box showing a Value: name, data and grad (starts at 0)."""
    box = RoundedRectangle(corner_radius=0.15, width=NODE_W, height=NODE_H, color=IDLE)
    data_t, grad_t = value_line("data", data), value_line("grad", 0)
    content = VGroup(Text(name, font_size=30, weight=BOLD), data_t, grad_t).arrange(
        DOWN, buff=0.12
    )
    node = VGroup(box, content).move_to(pos)
    node.box, node.data, node.grad = box, data_t, grad_t
    return node


def make_op(symbol, pos):
    """Small circle for an operation (× or +)."""
    box = Circle(radius=OP_R, color=IDLE)
    node = VGroup(box, MathTex(symbol, font_size=40)).move_to(pos)
    node.box = box
    return node


def make_arrow(src, dst):
    start = src.get_right()
    if isinstance(dst.box, Circle):
        end = dst.get_center() + OP_R * normalize(start - dst.get_center())
    else:
        end = dst.get_left()
    return Arrow(
        start,
        end,
        buff=0.08,
        stroke_width=4,
        color=IDLE,
        max_tip_length_to_length_ratio=0.2,
    )


def highlight(node, color):
    return node.box.animate.set_stroke(color).set_fill(
        color, opacity=0 if color == IDLE else 0.15
    )


def flow(arrow, color, backward=False):
    """Color an arrow and send a pulse along it (against it when backward)."""
    start, end = arrow.get_start(), arrow.get_end()
    if backward:
        start, end = end, start
    pulse = Line(start, end, stroke_width=10, color=color)
    return AnimationGroup(
        arrow.animate.set_color(color), ShowPassingFlash(pulse, time_width=0.6)
    )


def set_value(node, field, x):
    old = getattr(node, field)
    return Transform(old, value_line(field, x).move_to(old))


class MicrogradForwardBackward(Scene):
    def construct(self):
        self.caption = self.work = None

        # 1. Title and expression
        self.next_section("title")
        title = Text("micrograd: forward and backward pass", font_size=40)
        expr = MathTex(r"d = a \cdot b + c", font_size=64)
        VGroup(title, expr).arrange(DOWN, buff=0.6)
        self.play(Write(title), run_time=1.5)
        self.play(FadeIn(expr, shift=UP * 0.3), run_time=1)
        self.wait(1.5)
        self.play(
            FadeOut(title), expr.animate.scale(0.6).to_corner(UL, buff=0.4), run_time=1
        )

        # 2. Leaf nodes
        self.next_section("leaves")
        a, b, c = (
            make_node("a", 2, A_POS),
            make_node("b", -3, B_POS),
            make_node("c", 10, C_POS),
        )
        self.play(
            LaggedStart(*[FadeIn(n, scale=0.9) for n in (a, b, c)], lag_ratio=0.3),
            run_time=1.5,
        )
        self.say(
            "Each Value holds a number (data) and a gradient (grad), which starts at 0."
        )
        self.play(*[Indicate(n.data) for n in (a, b, c)], run_time=1)
        self.play(*[Indicate(n.grad) for n in (a, b, c)], run_time=1)
        self.wait(1.5)

        # 3. Forward through ×
        self.next_section("forward_mul")
        mul, e = make_op(r"\times", MUL_POS), make_node("e", -6, E_POS)
        a_mul, b_mul, mul_e = make_arrow(a, mul), make_arrow(b, mul), make_arrow(mul, e)
        self.play(Create(mul), GrowArrow(a_mul), GrowArrow(b_mul), run_time=1)
        self.say("Forward pass: a and b flow into × and are multiplied.")
        self.play(highlight(a, FWD), highlight(b, FWD), run_time=1)
        self.play(flow(a_mul, FWD), flow(b_mul, FWD), highlight(mul, FWD), run_time=1.5)
        self.play(
            GrowArrow(mul_e.set_color(FWD)), FadeIn(e), highlight(e, FWD), run_time=1
        )
        self.say(
            "The result is a new Value, e = −6.", r"e = a \cdot b = 2 \cdot (-3) = -6"
        )
        self.wait(2)
        self.play(
            *[highlight(n, IDLE) for n in (a, b, mul, e)],
            *[ar.animate.set_color(IDLE) for ar in (a_mul, b_mul, mul_e)],
            run_time=1,
        )

    def say(self, text, work=None):
        """Replace the bottom caption and, optionally, the equation in the top-right corner."""
        anims = [FadeOut(m) for m in (self.caption, self.work) if m]
        self.caption = Text(text, font_size=26).to_edge(DOWN, buff=0.35)
        if self.caption.width > 13:
            self.caption.scale_to_fit_width(13)
        anims.append(FadeIn(self.caption, shift=UP * 0.2))
        self.work = None
        if work:
            self.work = MathTex(work, font_size=40).to_corner(UR, buff=0.4)
            anims.append(Write(self.work))
        self.play(*anims, run_time=1)
