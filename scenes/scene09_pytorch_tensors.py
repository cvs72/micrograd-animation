import random

from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, arrow_between, callout,
    fmt, make_value_node, recap_line, title_card, working_line,
)
from micrograd_animation.anim import code_panel
from micrograd_animation.engine import Value

# What the lecture's PyTorch cell prints for the same neuron (checked against the engine below).
NOTEBOOK = {"x1": -1.5, "x2": 0.5, "w1": 1.0, "w2": 0.0, "o": 0.7071}

CODE_MICRO = """x1 = Value(2.0)
x2 = Value(0.0)
w1 = Value(-3.0)
w2 = Value(1.0)
b = Value(6.8813735870195432)
n = x1*w1 + x2*w2 + b
o = n.tanh()
o.backward()"""

CODE_TORCH = """x1 = torch.Tensor([2.0]).double()
x1.requires_grad = True
# x2, w1, w2, b are built the same way
n = x1*w1 + x2*w2 + b
o = torch.tanh(n)
o.backward()
print(x1.grad.item())"""

CODE_LEGENDRE = """class LegendrePolynomial3(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return 0.5 * (5 * x**3 - 3 * x)

    @staticmethod
    def backward(ctx, grad_output):
        x, = ctx.saved_tensors
        return grad_output * 1.5 * (5 * x**2 - 1)"""

XS = [[2.0, 3.0, -1.0], [3.0, -1.0, 0.5], [0.5, 1.0, 1.0], [1.0, 1.0, -1.0]]


# ------------------------------------------------------------------ engine side
def neuron():
    d = dict(x1=Value(2.0), x2=Value(0.0), w1=Value(-3.0), w2=Value(1.0), b=Value(6.8813735870195432))
    d["n"] = d["x1"] * d["w1"] + d["x2"] * d["w2"] + d["b"]
    d["o"] = d["n"].tanh()
    d["o"].backward()
    return d


def layer_weights(nout, seed=1):
    rng = random.Random(seed)
    return [[round(rng.uniform(-1, 1), 1) for _ in range(nout)] for _ in range(3)]


def layer_outputs(w):
    """Pre-activations of a layer with len(w[0]) neurons on the 4 examples, built from Values."""
    nout = len(w[0])
    return [[sum(Value(XS[i][k]) * Value(w[k][j]) for k in range(3)) for j in range(nout)] for i in range(4)]


def count_products(outs):
    seen = set()
    for row in outs:
        for v in row:
            for node in v.topo():
                if node._op == "*":
                    seen.add(id(node))
    return len(seen)


def legendre(x):
    return 0.5 * (5 * x**3 - 3 * x)


# ------------------------------------------------------------------ drawing side
def cell_grid(vals, w=0.95, h=0.6, color=DATA):
    cells = VGroup()
    for r in vals:
        for v in r:
            sq = Rectangle(width=w, height=h, stroke_color=GREY_B, stroke_width=1.5)
            t = Text(fmt(v), font_size=24, color=color).move_to(sq)
            cells.add(VGroup(sq, t))
    cells.arrange_in_grid(rows=len(vals), cols=len(vals[0]), buff=0.05)
    return cells


def place(code, width, pos, lines=()):
    """Code panel scaled and moved together with the highlight boxes of `lines`."""
    p = code_panel(code, highlight=list(lines) or None)
    g = VGroup(p, p.highlight) if lines else VGroup(p)
    g.scale_to_fit_width(width).move_to(pos)
    p.hl = dict(zip(lines, p.highlight)) if lines else {}
    return p


def line_box(panel, i):
    return panel.hl[i]


class Scene09PytorchTensors(MovingCameraScene):
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
        return c

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

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S09")
        title_card(self, "Chapter 9", "Is PyTorch just micrograd with tensors?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        self.clear_stage()
        recap_line(self, "Next: can we build a whole network from Values?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        d = neuron()
        for k, v in NOTEBOOK.items():
            got = d["o"].data if k == "o" else d[k].grad
            assert abs(got - v) < 1e-4, (k, got, v)
        nar.say("Example A: the same neuron from chapter 5, now written twice.")
        act_banner(self, "Example A: the same neuron in PyTorch", hold=2.6)
        tag = self.tag("Example A:")
        self.play(FadeIn(tag), run_time=0.4)

        micro = place(CODE_MICRO, 5.6, [-3.6, 0.7, 0])
        torch_ = place(CODE_TORCH, 6.6, [3.4, 0.7, 0], lines=(1, 2, 6, 7))
        lm = Text("micrograd", font_size=28, color=FWD, weight=BOLD).next_to(micro, UP, buff=0.2)
        lt = Text("PyTorch", font_size=28, color=GRAD, weight=BOLD).next_to(torch_, UP, buff=0.2)
        nar.say("On the left our Value version, on the right the same thing in PyTorch.")
        self.play(FadeIn(micro), FadeIn(lm), run_time=0.8)
        self.play(FadeIn(torch_), FadeIn(lt), run_time=0.8)
        self.wait(1.0)

        h1 = line_box(torch_, 1)
        nar.say("PyTorch uses 32-bit floats; .double() matches Python's 64-bit.")
        self.play(Create(h1), run_time=0.6)
        self.wait(1.0)
        h2 = line_box(torch_, 2)
        nar.say("Leaf tensors skip gradients unless asked: requires_grad = True.")
        self.play(ReplacementTransform(h1, h2), run_time=0.6)
        self.zoom_on(h2, 0.55, 2.0, dy=-0.3)
        c1 = self.show_callout("requires_grad", "Switch on gradient tracking for this tensor.", [0, -1.9, 0])
        self.play(FadeOut(c1), run_time=0.4)
        h3 = line_box(torch_, 6)
        nar.say("o.backward() is the same call as ours. It fills in every .grad.")
        self.play(ReplacementTransform(h2, h3), run_time=0.6)
        self.wait(1.0)
        h4 = line_box(torch_, 7)
        nar.say("A tensor is a box of numbers, so .item() pulls out one plain number.")
        self.play(ReplacementTransform(h3, h4), run_time=0.6)
        self.wait(1.0)
        self.play(FadeOut(Group(micro, torch_, lm, lt, h4)), run_time=0.6)

        # predict then reveal, with the real numbers
        o = d["o"].data
        nar.say("Before comparing: what should x1.grad be? Think 1 - o squared.")
        q = self.pulse_question("What is x1.grad?", [-2.5, 1.9, 0], [1.4, 1.9, 0])
        self.play(FadeOut(q), run_time=0.4)
        working_line(
            self, r"x_1.\text{grad}=w_1\,(1-o^2)",
            rf"x_1.\text{{grad}}={fmt(d['w1'].data)}\,(1-{fmt(o)}^2)",
            rf"x_1.\text{{grad}}={fmt(d['x1'].grad)}", pos=[0, 1.9, 0], width=7.5, hold=2.0)
        nar.say("Times w1 = -3, the local slope 0.5 gives -1.5: a downhill nudge.")
        self.wait(0.5)

        # the table: micrograd from the engine against what the lecture's PyTorch cell printed
        names = ["x1", "x2", "w1", "w2", "o"]
        head = ["", "x1.grad", "x2.grad", "w1.grad", "w2.grad", "o"]
        row1 = ["micrograd"] + [fmt(d[k].grad) for k in names[:4]] + [fmt(o)]
        row2 = ["PyTorch"] + [fmt(NOTEBOOK[k]) for k in names]
        tbl = self.make_table(head, [row1, row2])
        tbl.move_to([0, -0.6, 0])
        nar.say("The lecture's PyTorch run prints these same numbers (not run here).")
        self.play(FadeIn(tbl), run_time=1.0)
        self.play(Indicate(tbl[2][5], color=ACTIVE), Indicate(tbl[3][5], color=ACTIVE), run_time=1.0)
        self.wait(2.0)
        nar.say("Same maths, same gradients. PyTorch is micrograd plus speed.")
        self.wait(1.0)
        self.play(FadeOut(tag), run_time=0.3)
        self.clear_stage()

    def make_table(self, head, rows):
        """Two-row table: header, micrograd row, PyTorch row; returns VGroup(grid lines, row0, row1, row2)."""
        colw = 2.0
        out = VGroup()
        for r, cells in enumerate([head] + rows):
            row = VGroup()
            for c, s in enumerate(cells):
                col = SECOND if r == 0 else (FWD if (c == 0 and r == 1) else (GRAD if c == 0 else (DATA if c else WHITE)))
                t = Text(s, font_size=28, color=col)
                t.move_to([(c - 2.5) * colw, -r * 0.8, 0])
                row.add(t)
            out.add(row)
        box = SurroundingRectangle(out, color=GREY_B, buff=0.3)
        line1 = Line(box.get_left() + DOWN * 0.4, box.get_right() + DOWN * 0.4, color=GREY_B)
        group = VGroup(box, *out)
        group.add(line1)
        group.row_lines = line1
        # index 0: box, 1..3 rows, 4: line
        return group

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        w4 = layer_weights(4)
        out4 = layer_outputs(w4)
        n4 = count_products(out4)
        assert n4 == 4 * 3 * 4 == 48
        w8 = layer_weights(8)
        n8 = count_products(layer_outputs(w8))
        assert n8 == 96

        tag = self.open_act("Example B: what if the numbers are not single scalars?",
                            "Example B: tensors instead of scalars", "Example B:")

        # a 2 by 3 tensor and its shape
        t23 = cell_grid(XS[:2]).move_to([-3.0, 0.6, 0])
        br_r = Brace(t23, direction=LEFT, color=ACTIVE)
        br_c = Brace(t23, direction=UP, color=ACTIVE)
        lab_r = Text("2 rows", font_size=28, color=ACTIVE).next_to(br_r, LEFT, buff=0.15)
        lab_c = Text("3 columns", font_size=28, color=ACTIVE).next_to(br_c, UP, buff=0.15)
        shape = MathTex(r"\text{shape}=(2,\,3)", font_size=44, color=WHITE).move_to([3.4, 0.6, 0])
        nar.say("A tensor is a grid of numbers. This one has 2 rows and 3 columns.")
        self.play(FadeIn(t23), run_time=0.8)
        self.play(Create(br_r), Create(br_c), FadeIn(lab_r), FadeIn(lab_c), run_time=1.0)
        self.play(Write(shape), run_time=1.0)
        c = self.show_callout("Tensor", "An n-dimensional array of numbers.", [0, -1.9, 0])
        self.play(FadeOut(c), run_time=0.4)
        self.play(FadeOut(Group(br_r, br_c, lab_r, lab_c, shape)), run_time=0.5)

        # predict the number of multiplications
        nar.say("4 examples, 3 inputs, 4 neurons: how many multiplications?")
        self.play(t23.animate.scale(0.6).to_corner(UR, buff=0.7), run_time=0.6)
        q = self.pulse_question("How many scalar multiplications?", [-1.5, 0.8, 0], [2.7, 0.8, 0])
        self.play(FadeOut(q), FadeOut(t23), run_time=0.5)

        # the matmul picture
        X = cell_grid(XS).move_to([-5.0, 0.4, 0])
        W = cell_grid(w4).move_to([-0.6, 0.4, 0])
        O = cell_grid([[0.0] * 4] * 4).move_to([4.4, 0.4, 0])
        for cell in O:
            cell[1].set_opacity(0)
        times = MathTex(r"\times", font_size=48).move_to([-2.9, 0.4, 0])
        eq = MathTex(r"=", font_size=48).move_to([1.9, 0.4, 0])
        lx = Text("X: 4 x 3", font_size=26, color=SECOND).next_to(X, UP, buff=0.2)
        lw = Text("W: 3 x 4", font_size=26, color=SECOND).next_to(W, UP, buff=0.2)
        lo = Text("X W: 4 x 4", font_size=26, color=SECOND).next_to(O, UP, buff=0.2)
        nar.say("Examples times weights gives a 4 by 4 grid of sums.")
        self.play(FadeIn(X), FadeIn(lx), FadeIn(times), run_time=0.8)
        self.play(FadeIn(W), FadeIn(lw), FadeIn(eq), FadeIn(O), FadeIn(lo), run_time=0.8)
        self.wait(1.0)

        label = Text("micrograd multiplications:", font_size=28, color=WHITE).move_to([-2.0, -2.2, 0])
        tr = ValueTracker(0)
        cnt = Integer(0, font_size=44, color=YELLOW).next_to(label, RIGHT, buff=0.3)
        cnt.add_updater(lambda m: m.set_value(int(round(tr.get_value()))))
        rowr = SurroundingRectangle(VGroup(*X[0:3]), color=ACTIVE, buff=0.03)
        colr = SurroundingRectangle(VGroup(*[W[j] for j in (0, 4, 8)]), color=GRAD, buff=0.03)
        nar.say("micrograd builds each cell by hand: 3 products, then adds.")
        self.play(FadeIn(label), FadeIn(cnt), Create(rowr), Create(colr), run_time=0.8)
        done = 0
        for i in range(4):
            for j in range(4):
                v = out4[i][j].data
                new_t = Text(fmt(v), font_size=24, color=DATA).move_to(O[4 * i + j][1])
                O[4 * i + j].remove(O[4 * i + j][1])
                O[4 * i + j].add(new_t)
                done += 3
                row_t = SurroundingRectangle(VGroup(*X[3 * i:3 * i + 3]), color=ACTIVE, buff=0.03)
                col_t = SurroundingRectangle(VGroup(*[W[j + 4 * k] for k in range(3)]), color=GRAD, buff=0.03)
                self.play(
                    rowr.animate.move_to(row_t.get_center()), colr.animate.move_to(col_t.get_center()),
                    O[4 * i + j][0].animate.set_fill(FWD, opacity=0.45), tr.animate.set_value(done),
                    run_time=0.3 if (i or j) else 0.6)
        assert done == n4
        nar.say("16 cells, 3 products each: exactly 48 multiplications.")
        self.play(FadeOut(rowr), FadeOut(colr), Indicate(cnt, color=ACTIVE, scale_factor=1.3), run_time=1.0)
        self.wait(2.0)

        # the tensor library does it as one operation
        nar.say("A tensor library does the whole grid in one parallel call.")
        one = Text("tensor library: 1 matrix multiply", font_size=28, color=GRAD).move_to([2.2, -2.2, 0])
        self.play(FadeOut(label), FadeOut(cnt), run_time=0.4)
        self.play(FadeIn(one), O.animate.set_fill(GRAD, opacity=0.0), Flash(O, color=GRAD, flash_radius=2.4),
                  Indicate(VGroup(X, W, O), color=GRAD, scale_factor=1.05), run_time=1.5)
        self.wait(2.0)
        self.play(FadeOut(Group(X, W, O, times, eq, lx, lw, lo, one)), run_time=0.6)

        # what if: double the neurons
        nar.say("What if the layer had 8 neurons? Watch the scalar count double.")
        base = -2.0
        trk = ValueTracker(n4)
        bar = always_redraw(lambda: Rectangle(
            width=1.8, height=max(0.025 * trk.get_value(), 0.03), stroke_width=0, fill_color=DATA, fill_opacity=0.9
        ).move_to([-2.6, base + max(0.025 * trk.get_value(), 0.03) / 2, 0]))
        num = always_redraw(lambda: Integer(int(round(trk.get_value())), font_size=44, color=YELLOW).next_to(bar, UP, buff=0.15))
        bar1 = Rectangle(width=1.8, height=0.03, stroke_width=0, fill_color=GRAD, fill_opacity=0.9).move_to([2.6, base + 0.015, 0])
        num1 = Integer(1, font_size=44, color=YELLOW).next_to(bar1, UP, buff=0.15)
        base_line = Line([-4.5, base, 0], [4.5, base, 0], color=GREY_B)
        l_m = Text("micrograd scalar products", font_size=26, color=DATA).next_to(base_line, DOWN, buff=0.15).set_x(-2.6)
        l_t = Text("tensor calls", font_size=26, color=GRAD).next_to(base_line, DOWN, buff=0.15).set_x(2.6)
        l_n = MathTex(r"4\cdot 3\cdot 4", font_size=44, color=WHITE).move_to([-2.6, 2.6, 0])
        self.play(Create(base_line), FadeIn(bar), FadeIn(num), FadeIn(bar1), FadeIn(num1), FadeIn(l_m), FadeIn(l_t),
                  FadeIn(l_n), run_time=1.0)
        self.wait(3.0)
        l_n2 = MathTex(r"4\cdot 3\cdot 8", font_size=44, color=WHITE).move_to(l_n)
        self.play(trk.animate.set_value(n8), TransformMatchingTex(l_n, l_n2), run_time=1.0)
        nar.say("8 neurons: 4 * 3 * 8 = 96 products. Tensors: one call.")
        self.play(Indicate(num, color=ACTIVE, scale_factor=1.3), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(tag), run_time=0.3)
        self.clear_stage()

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        d = neuron()
        o = d["o"].data
        slope = 1 - o * o
        assert abs(slope - 0.5) < 1e-4
        x = Value(2.0)
        y = 0.5 * (5 * x**3 - 3 * x)
        y.backward()
        assert abs(y.data - 17.0) < 1e-9 and abs(x.grad - 28.5) < 1e-9
        assert abs(legendre(2.0) - y.data) < 1e-9

        tag = self.open_act("Expert corner: where does PyTorch hide tanh's backward pass?",
                            "Expert corner: inside PyTorch", "Expert corner:")

        # (1) tanh's kernel formula is micrograd's formula
        ax = Axes(x_range=[-3, 3, 1], y_range=[0, 1, 0.5], x_length=5.6, y_length=2.6, tips=False,
                  axis_config={"font_size": 24, "include_numbers": True}).move_to([-3.4, 0.4, 0])
        curve = ax.plot(lambda t: 1 - Value(t).tanh().data ** 2, x_range=[-3, 3], color=GRAD)
        nvals = d["n"].data
        dot = Dot(ax.c2p(nvals, slope), color=ACTIVE, radius=0.1)
        ylab = MathTex(r"1-o^2", font_size=36, color=GRAD).next_to(ax, UP, buff=0.1).shift(LEFT * 1.2)
        nar.say("The lecture hunted for tanh's backward in PyTorch for about 15 minutes.")
        self.play(Create(ax), run_time=1.0)
        self.play(Create(curve), FadeIn(ylab), run_time=1.5)
        self.play(FadeIn(dot), run_time=0.5)
        nar.say("The CPU and CUDA kernels hold one line: grad times (1 - o squared).")
        working_line(
            self, r"\text{grad}_{in}=\text{grad}_{out}\,(1-o^2)",
            rf"\text{{grad}}_{{in}}=1\cdot(1-{fmt(o)}^2)", rf"\text{{grad}}_{{in}}={fmt(slope)}",
            pos=[3.5, 0.4, 0], width=6.0, hold=2.0)
        nar.say("That is our tanh _backward: same formula, more hardware.")
        self.play(Indicate(dot, color=ACTIVE, scale_factor=2.0), run_time=1.0)
        self.wait(1.5)
        self.clear_stage()

        # (2) a custom operation as a torch.autograd.Function
        code = place(CODE_LEGENDRE, 6.8, [-3.3, 0.5, 0], lines=(5, 10))
        lc = Text("lecture's example, not run here", font_size=24, color=SECOND).next_to(code, UP, buff=0.15)
        nar.say("To add your own operation, write forward and backward by hand.")
        self.play(FadeIn(code), FadeIn(lc), run_time=0.8)
        hf = line_box(code, 5)
        hb = line_box(code, 10)
        self.play(Create(hf), run_time=0.6)
        self.wait(1.0)
        nar.say("Backward is the derivative you derive by hand: 1.5 (5x^2 - 1).")
        self.play(ReplacementTransform(hf, hb), run_time=0.6)
        ax2 = Axes(x_range=[-1.5, 2.5, 1], y_range=[-5, 25, 10], x_length=4.6, y_length=2.6, tips=False,
                   axis_config={"font_size": 24, "include_numbers": True}).move_to([4.0, 0.9, 0])
        ax2_curve = ax2.plot(lambda t: legendre(t), x_range=[-1.5, 2.3], color=DATA)
        p_dot = Dot(ax2.c2p(2.0, y.data), color=ACTIVE, radius=0.09)
        slope_line = Line(ax2.c2p(1.7, y.data - 0.3 * x.grad), ax2.c2p(2.15, y.data + 0.15 * x.grad), color=BWD, stroke_width=4)
        self.play(Create(ax2), run_time=0.8)
        self.play(Create(ax2_curve), run_time=1.2)
        self.play(FadeIn(p_dot), Create(slope_line), run_time=0.8)
        working_line(
            self, r"P_3'(x)=1.5\,(5x^2-1)",
            rf"P_3'({fmt(x.data)})=1.5\,(5\cdot {fmt(x.data)}^2-1)", rf"P_3'({fmt(x.data)})={fmt(x.grad)}",
            pos=[4.0, -1.7, 0], width=5.2, hold=2.0)
        self.wait(1.0)
        self.clear_stage()

        # (3) the lego block in the graph
        nx = make_value_node("x", x.data, x.grad, width=2.4).scale(0.85).move_to([-5.0, 0.4, 0])
        ny = make_value_node("y", y.data, 1.0, width=2.4).scale(0.85).move_to([5.0, 0.4, 0])
        blk_t = Text("your forward + backward", font_size=26, color=ACTIVE)
        blk = VGroup(RoundedRectangle(corner_radius=0.15, width=blk_t.width + 0.5, height=1.1, stroke_color=ACTIVE,
                                      stroke_width=3), blk_t)
        blk_t.move_to(blk[0])
        blk.move_to([0, 0.4, 0])
        f1 = arrow_between(nx, blk, color=FWD).shift(UP * 0.12)
        f2 = arrow_between(blk, ny, color=FWD).shift(UP * 0.12)
        b1 = arrow_between(blk, nx, color=BWD).shift(DOWN * 0.12)
        b2 = arrow_between(ny, blk, color=BWD).shift(DOWN * 0.12)
        nar.say("Your operation becomes a lego block: forward plus backward.")
        self.play(FadeIn(nx), FadeIn(blk), FadeIn(ny), run_time=0.8)
        self.play(Create(f1), Create(f2), run_time=1.0)
        self.play(Create(b2), Create(b1), run_time=1.0)
        self.play(Indicate(blk, color=ACTIVE), run_time=1.0)
        c = self.show_callout("Autograd", "Build the graph as code runs, then run backward.", [0, -1.6, 0], width=9.0)
        nar.say("PyTorch stores one derivative per operation, like our closures.")
        self.wait(1.0)
        self.play(FadeOut(c), run_time=0.4)
        nar.say("Micrograd is the whole idea. The rest of PyTorch is efficiency.")
        self.wait(1.0)
        self.play(FadeOut(tag), run_time=0.3)
