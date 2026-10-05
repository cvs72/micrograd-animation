from manim import *

from micrograd_animation.engine import Value


def f(x):
    return 3 * x**2 - 4 * x + 5


def slope_at(x0):
    """Exact slope from the Value class: backprop through f."""
    x = Value(x0)
    y = 3 * x**2 - 4 * x + 5
    y.backward()
    return x.grad


def secant_slope(x0, h):
    return (f(Value(x0 + h)).data - f(Value(x0)).data) / h


PANEL = np.array([2.6, 2.6, 0])  # fixed top-left anchor of the readout panel


def panel(*rows):
    return VGroup(*rows).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(PANEL, aligned_edge=UL)


class Scene01Derivative(Scene):
    def construct(self):
        title = MathTex(r"f(x)=3x^2-4x+5", font_size=48).to_corner(UL)
        self.play(Write(title))

        axes = Axes(
            x_range=[-1, 3.5, 1],
            y_range=[0, 30, 10],
            x_length=8.2,
            y_length=5.0,
            axis_config={"include_tip": False, "font_size": 32, "include_numbers": True},
        ).move_to(LEFT * 2.2 + DOWN * 0.7)
        labels = axes.get_axis_labels(
            MathTex("x", font_size=38), MathTex("f(x)", font_size=38)
        )
        curve = axes.plot(lambda t: f(Value(t)).data, x_range=[-1, 3.2], color=BLUE)
        self.play(Create(axes), FadeIn(labels), run_time=1.5)
        self.play(Create(curve), run_time=2)
        self.wait(0.5)

        # --- tangent line sliding along the curve ---
        xt = ValueTracker(-0.8)
        dot = always_redraw(
            lambda: Dot(axes.c2p(xt.get_value(), f(xt.get_value())), color=YELLOW)
        )

        def tangent():
            x0 = xt.get_value()
            m = slope_at(x0)
            return axes.plot(
                lambda t: f(x0) + m * (t - x0),
                x_range=[max(-0.8, x0 - 1), min(3.0, x0 + 1)],
                color=YELLOW,
            )

        tan_line = always_redraw(tangent)

        def readout():
            x0 = xt.get_value()
            return panel(
                MathTex(rf"x = {x0:+.2f}", font_size=40),
                MathTex(rf"\text{{slope}} = {slope_at(x0):+.2f}", font_size=40, color=YELLOW),
            )

        info = always_redraw(readout)
        tag = Text("tangent at the yellow dot", font_size=26, color=YELLOW)
        tag.move_to(PANEL + DOWN * 1.5, aligned_edge=UL)
        self.play(FadeIn(dot), Create(tan_line), FadeIn(info), FadeIn(tag))
        self.wait(0.5)
        self.play(xt.animate.set_value(3.0), run_time=6, rate_func=linear)
        self.play(xt.animate.set_value(2 / 3), run_time=2)
        flat = Text("slope 0 at the minimum", font_size=28, color=TEAL)
        flat.move_to(PANEL + DOWN * 2.2, aligned_edge=UL)
        self.play(FadeIn(flat))
        self.wait(1)
        self.play(FadeOut(flat), FadeOut(tag), FadeOut(tan_line), FadeOut(info), FadeOut(dot))

        # --- nudge h shrinks toward 0 ---
        x0 = 1.0
        ht = ValueTracker(1.5)
        base = Dot(axes.c2p(x0, f(x0)), color=YELLOW, radius=0.11)
        true_line = axes.plot(
            lambda t: f(x0) + slope_at(x0) * (t - x0), x_range=[x0 - 1, x0 + 1.5],
            color=GREEN, stroke_width=6,
        )
        base_lbl = MathTex(r"x=1", font_size=36, color=YELLOW).next_to(base, UP, buff=0.3).shift(LEFT * 0.6)
        self.play(FadeIn(base), FadeIn(base_lbl), Create(true_line))
        self.wait(0.5)

        def secant():
            m = secant_slope(x0, ht.get_value())
            return axes.plot(
                lambda t: f(x0) + m * (t - x0), x_range=[x0 - 1, x0 + 1.5], color=RED
            )

        sec_line = always_redraw(secant)
        far_dot = always_redraw(
            lambda: Dot(
                axes.c2p(x0 + ht.get_value(), f(x0 + ht.get_value())), color=RED, radius=0.07
            )
        )
        h_seg = always_redraw(
            lambda: Line(
                axes.c2p(x0, f(x0)), axes.c2p(x0 + ht.get_value(), f(x0)), color=RED
            )
        )
        far_lbl = always_redraw(
            lambda: MathTex(r"x+h", font_size=32, color=RED).next_to(
                axes.c2p(x0 + ht.get_value(), f(x0 + ht.get_value())), DR, buff=0.25
            )
        )

        def h_readout():
            h = ht.get_value()
            return panel(
                MathTex(rf"h = {h:.3f}", font_size=40, color=RED),
                MathTex(r"\frac{f(x+h)-f(x)}{h}", font_size=40),
                MathTex(rf"= {secant_slope(x0, h):.3f}", font_size=40, color=RED),
                MathTex(rf"\text{{true slope}} = {slope_at(x0):.3f}", font_size=40, color=GREEN),
            )

        h_info = always_redraw(h_readout)
        self.play(FadeIn(sec_line), FadeIn(far_dot), FadeIn(far_lbl), FadeIn(h_info))
        self.play(ht.animate.set_value(0.5), run_time=3)
        self.play(ht.animate.set_value(0.05), run_time=3)
        self.play(ht.animate.set_value(0.001), run_time=3)
        self.play(Indicate(h_info[2]), Indicate(h_info[3]))
        self.wait(2)
