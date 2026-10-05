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


class Scene01Derivative(Scene):
    def construct(self):
        title = MathTex(r"f(x)=3x^2-4x+5", font_size=44).to_corner(UL)
        self.play(Write(title))

        axes = Axes(
            x_range=[-1, 3.5, 1],
            y_range=[0, 30, 10],
            x_length=7.5,
            y_length=4.6,
            axis_config={"include_tip": False, "font_size": 24},
            y_axis_config={"include_numbers": True},
            x_axis_config={"include_numbers": True},
        ).to_edge(DOWN, buff=0.5).shift(LEFT * 1.8)
        curve = axes.plot(lambda t: f(Value(t)).data, x_range=[-1, 3.2], color=BLUE)
        self.play(Create(axes), run_time=1.5)
        self.play(Create(curve), run_time=2)

        # --- tangent line sliding along the curve ---
        xt = ValueTracker(-0.8)

        def point():
            return axes.c2p(xt.get_value(), f(xt.get_value()))

        dot = always_redraw(lambda: Dot(point(), color=YELLOW))

        def tangent():
            x0 = xt.get_value()
            m = slope_at(x0)
            line = axes.plot(
                lambda t: f(x0) + m * (t - x0),
                x_range=[max(-1, x0 - 1), min(3.2, x0 + 1)],
                color=YELLOW,
            )
            return line

        tan_line = always_redraw(tangent)

        def readout():
            x0 = xt.get_value()
            g = VGroup(
                MathTex(rf"x = {x0:.2f}", font_size=34),
                MathTex(rf"\text{{slope}} = {slope_at(x0):.2f}", font_size=34, color=YELLOW),
            ).arrange(DOWN, aligned_edge=LEFT)
            return g.to_corner(UR).shift(DOWN * 0.3)

        info = always_redraw(readout)
        self.play(FadeIn(dot), Create(tan_line), FadeIn(info))
        self.play(xt.animate.set_value(3.0), run_time=6, rate_func=linear)
        self.play(xt.animate.set_value(2 / 3), run_time=2)
        flat = Text("slope 0 at the minimum", font_size=26, color=TEAL).next_to(info, DOWN, buff=0.4)
        self.play(FadeIn(flat))
        self.wait(1)
        self.play(FadeOut(flat), FadeOut(tan_line), FadeOut(info))

        # --- nudge h shrinks toward 0 ---
        x0 = 1.0
        ht = ValueTracker(1.5)
        base = axes.c2p(x0, f(x0))
        self.play(xt.animate.set_value(x0), run_time=1)

        def secant():
            h = ht.get_value()
            m = secant_slope(x0, h)
            return axes.plot(
                lambda t: f(x0) + m * (t - x0),
                x_range=[x0 - 0.9, x0 + 1.6],
                color=RED,
            )

        sec_line = always_redraw(secant)
        far_dot = always_redraw(
            lambda: Dot(axes.c2p(x0 + ht.get_value(), f(x0 + ht.get_value())), color=RED)
        )

        def h_readout():
            h = ht.get_value()
            return VGroup(
                MathTex(rf"h = {h:.3f}", font_size=34, color=RED),
                MathTex(
                    r"\frac{f(x+h)-f(x)}{h} = " + f"{secant_slope(x0, h):.3f}",
                    font_size=34,
                ),
                MathTex(rf"\text{{true slope}} = {slope_at(x0):.3f}", font_size=34, color=YELLOW),
            ).arrange(DOWN, aligned_edge=LEFT).to_corner(UR).shift(DOWN * 0.3)

        h_info = always_redraw(h_readout)
        at_x = MathTex(r"x = 1", font_size=30).next_to(base, UP + LEFT, buff=0.2)
        self.play(FadeIn(sec_line), FadeIn(far_dot), FadeIn(h_info), FadeIn(at_x))
        self.play(ht.animate.set_value(0.5), run_time=3)
        self.play(ht.animate.set_value(0.05), run_time=3)
        self.play(ht.animate.set_value(0.001), run_time=3)
        self.play(Indicate(h_info[1]), Indicate(h_info[2]))
        self.wait(2)
