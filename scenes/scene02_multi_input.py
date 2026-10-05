from manim import *

from micrograd_animation.engine import Value

H = 0.01
BASE = {"a": 2.0, "b": -3.0, "c": 10.0}


def forward(vals):
    a, b, c = (Value(vals[k]) for k in "abc")
    return (a * b + c).data


def state_row(vals, d, nudged=None):
    """a=.., b=.., c=.., d=.. in one row; the nudged input is red."""
    items = []
    for k in "abc":
        col = RED if k == nudged else WHITE
        items.append(MathTex(f"{k}={vals[k]:.2f}", font_size=44, color=col))
    items.append(MathTex(f"d={d:.4f}", font_size=44, color=YELLOW))
    return VGroup(*items).arrange(RIGHT, buff=0.7)


def nudge_section(k, d0):
    """Nudge input k by H; return (state row, result lines, true gradient)."""
    vals = dict(BASE)
    vals[k] += H
    d1 = forward(vals)
    # true gradient from backprop in the Value class
    a, b, c = (Value(BASE[n]) for n in "abc")
    (a * b + c).backward()
    true = {"a": a.grad, "b": b.grad, "c": c.grad}[k]
    row = state_row(vals, d1, nudged=k)
    lines = VGroup(
        MathTex(rf"\Delta d = {d1:.4f} - {d0:.4f} = {d1 - d0:.4f}", font_size=44),
        MathTex(
            rf"\frac{{\Delta d}}{{h}} = \frac{{{d1 - d0:.4f}}}{{{H}}} \approx {(d1 - d0) / H:.2f}",
            font_size=44,
            color=TEAL,
        ),
        MathTex(rf"\frac{{\partial d}}{{\partial {k}}} = {true:.1f}", font_size=48, color=YELLOW),
    ).arrange(DOWN, buff=0.35)
    return row, lines, true


class Scene02MultiInput(Scene):
    def construct(self):
        title = MathTex(r"d = a \cdot b + c", font_size=56).to_edge(UP)
        self.play(Write(title))

        d0 = forward(BASE)
        base = state_row(BASE, d0).next_to(title, DOWN, buff=0.6)
        self.play(FadeIn(base))
        h_text = MathTex(rf"h = {H}", font_size=44, color=RED).to_edge(RIGHT).shift(UP * 2)
        self.play(Write(h_text))
        self.wait(0.5)

        row = lines = None
        for k in "abc":
            new_row, new_lines, _ = nudge_section(k, d0)
            new_row.next_to(base, DOWN, buff=0.7)
            new_lines.next_to(new_row, DOWN, buff=0.5)
            if row is None:
                self.play(TransformFromCopy(base, new_row))
                self.play(Indicate(new_row[ord(k) - ord("a")], color=RED))
                for line in new_lines:
                    self.play(FadeIn(line, shift=UP * 0.2), run_time=0.8)
            else:
                self.play(Transform(row, new_row), FadeOut(lines))
                self.play(Indicate(row[ord(k) - ord("a")], color=RED))
                for line in new_lines:
                    self.play(FadeIn(line, shift=UP * 0.2), run_time=0.8)
            if row is None:
                row = new_row
            lines = new_lines
            self.wait(1.5)

        self.play(FadeOut(lines), FadeOut(row), FadeOut(h_text))
        a, b, c = (Value(BASE[n]) for n in "abc")
        (a * b + c).backward()
        summary = VGroup(
            MathTex(rf"\frac{{\partial d}}{{\partial a}} = b = {a.grad:.0f}", font_size=48),
            MathTex(rf"\frac{{\partial d}}{{\partial b}} = a = {b.grad:.0f}", font_size=48),
            MathTex(rf"\frac{{\partial d}}{{\partial c}} = {c.grad:.0f}", font_size=48),
        ).arrange(DOWN, buff=0.5).next_to(base, DOWN, buff=0.8)
        self.play(LaggedStart(*[Write(s) for s in summary], lag_ratio=0.5))
        self.wait(2)
