from manim import *

from micrograd_animation.anim import (
    ACTIVE, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, fmt,
    make_value_node, particle_flow, recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value

LIGHT = BLUE_B  # readable data colour on black
POS = {
    "a": [-5.6, 2.0, 0], "b": [-5.6, 0.4, 0], "e": [-2.0, 1.2, 0], "c": [-2.0, -0.8, 0],
    "d": [1.6, 0.2, 0], "f": [1.6, -1.7, 0], "L": [5.2, -0.75, 0],
}
A_IN = (2.0, -3.0, 10.0, -2.0)    # a, b, c, f: the notebook
B1_IN = (-2.0, 5.0, -3.0, 0.5)
B2_IN = (2.0, -3.0, 10.0, 0.0)
H = 0.0001
STEP = 0.01
SPOT = [3.2, 2.35, 0]  # where callouts, workings and questions appear


def p(x):
    return f"({fmt(x)})" if x < 0 else fmt(x)


def graph(a, b, c, f):
    """L = (a*b + c) * f, built from Values."""
    va, vb, vc, vf = (Value(x, label=n) for x, n in zip((a, b, c, f), "abcf"))
    e = va * vb
    e.label = "e"
    d = e + vc
    d.label = "d"
    L = d * vf
    L.label = "L"
    return {"a": va, "b": vb, "c": vc, "e": e, "d": d, "f": vf, "L": L}


def backprop(vals):
    vals["L"].backward()
    return vals


def L_of(a, b, c, f):
    return graph(a, b, c, f)["L"].data


def op_circle(op):
    """Operation circle: a drawing helper made by draw_dot, NOT a Value."""
    c = Circle(radius=0.3, color=SECOND, stroke_width=3, fill_color=BLACK, fill_opacity=1)
    t = Text(op, font_size=30, color=WHITE).move_to(c)
    return VGroup(c, t)


def build_graph(vals, scale=0.95):
    nodes = {k: make_value_node(k, v.data, v.grad, width=2.0).scale(scale).move_to(POS[k])
             for k, v in vals.items()}
    ops, arrows = {}, {}
    for k, v in vals.items():
        if not v._op:
            continue
        kids = sorted((ch.label for ch in v._prev), key=lambda n: -POS[n][1])
        right = max(nodes[n].get_right()[0] for n in kids)
        x = (right + nodes[k].get_left()[0]) / 2
        circ = op_circle(v._op).move_to([x, POS[k][1], 0])
        ops[k] = circ
        kw = dict(buff=0.05, color=FWD, stroke_width=4, tip_length=0.16)
        arrows[k] = [Arrow(nodes[n].get_right(), circ.get_left(), **kw) for n in kids]
        arrows[k].append(Arrow(circ.get_right(), nodes[k].get_left(), **kw))
        arrows[k] = arrows[k]
        circ.kids = kids
    return nodes, ops, arrows


def node_anims(nodes, vals, names, data=True, grad=True):
    """Transforms that rewrite the data and/or grad text of the named nodes."""
    out = []
    for k in names:
        n2 = make_value_node(k, vals[k].data, vals[k].grad, width=2.0).scale(0.95).move_to(POS[k])
        if data:
            out.append(Transform(nodes[k].data_t, n2.data_t))
        if grad:
            out.append(Transform(nodes[k].grad_t, n2.grad_t))
    return out


def zero_grads(vals):
    z = {}
    for k, v in vals.items():
        w = Value(v.data, label=k)
        z[k] = w
    return z


def grad_grid(old, new):
    """2 by 2 before/after table of the leaf gradients."""
    cells = []
    for k in "abcf":
        cells.append(MathTex(rf"\frac{{dL}}{{d{k}}}:\;{fmt(old[k].grad)}\to {fmt(new[k].grad)}",
                             font_size=36, color=GRAD))
    g = VGroup(*cells).arrange_in_grid(rows=2, cols=2, buff=(0.5, 0.35))
    return g.move_to([3.6, 2.35, 0])


def vehicle_bar(x, speed, name, color):
    bar = Rectangle(width=1.4, height=0.4 * speed, fill_color=color, fill_opacity=0.85,
                    stroke_color=WHITE, stroke_width=2)
    bar.move_to([x, -1.5 + bar.height / 2, 0])
    lab = Text(name, font_size=28, color=WHITE).move_to([x, -1.9, 0])
    return VGroup(bar, lab)


class Scene04BackwardManual(Scene):
    # ---------------------------------------------------------------- helpers
    def tag(self, text):
        return Tex(r"\textbf{" + text + "}", font_size=34, color=ACTIVE).to_corner(UL, buff=0.5)

    def pulse_question(self, text, n=3):
        """Predict-then-reveal: question plus a pulsing question mark, held about 3 s."""
        q = Text(text, font_size=30, color=WHITE).move_to([0.9, 2.5, 0])
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to([5.9, 2.5, 0])
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        self.play(FadeOut(VGroup(q, qm)), run_time=0.4)

    def flow(self, arrows, mags, reverse=True, color=GRAD, run_time=0.9):
        fls = [particle_flow(a, m, color=color, n=2, reverse=reverse, run_time=run_time)
               for a, m in zip(arrows, mags)]
        dots = VGroup(*[f.dots for f in fls])
        self.add(dots)
        self.play(*fls)
        self.remove(dots, *dots.submobjects, *[f.mobject for f in fls])
        self.remove(*[d for f in fls for d in f.dots.submobjects])

    def recolour(self, arrows, color):
        self.play(*[a.animate.set_color(color) for a in arrows], run_time=0.4)

    def back_through(self, k, arrows, vals, color=GRAD):
        """Orange particles from node k, through its operation, to its children."""
        arr = arrows[k]
        kids = sorted((ch.label for ch in vals[k]._prev), key=lambda n: -POS[n][1])
        self.flow(arr[-1:], [vals[k].grad], reverse=True, color=color)
        self.flow(arr[:-1], [vals[n].grad for n in kids], reverse=True, color=color)
        self.recolour(arr, GRAD)

    def show_callout(self, title, body, color=ACTIVE, hold=3.2, width=6.2):
        c = callout(title, body, color=color, width=width).move_to(SPOT)
        self.play(FadeIn(c), run_time=0.5)
        self.wait(hold)
        self.play(FadeOut(c), run_time=0.4)

    def work(self, *args, **kw):
        w = working_line(self, *args, pos=SPOT, width=6.2, hold=1.6, colors=(WHITE, WHITE, GRAD),
                         **kw)
        self.play(FadeOut(w), run_time=0.4)

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = CrossfadeNarrator(self, "S04")
        title_card(self, "Chapter 4", "How does each node learn how much it matters?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        recap_line(self, "Next: can one neuron with tanh learn the same way?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        va = graph(*A_IN)
        vb = backprop(graph(*A_IN))
        want = {"L": 1, "d": -2, "f": 4, "e": -2, "c": -2, "a": 6, "b": -4}
        assert all(abs(vb[k].grad - g) < 1e-12 for k, g in want.items()), want
        nar.say("Example A: the lecture's graph, with every gradient still zero.")
        act_banner(self, "Example A: backprop by hand", hold=2.6)
        tag = self.tag("Example A:")
        nodes, ops, arrows = build_graph(va)
        title = MathTex(r"L=(a\cdot b+c)\cdot f", font_size=44).move_to([-1.0, 3.1, 0])
        group = VGroup(*nodes.values(), *ops.values(), *[a for l in arrows.values() for a in l])
        self.play(FadeIn(tag), FadeIn(title), FadeIn(group), run_time=1.0)
        self.wait(1.5)
        self.group, self.tag_now = group, tag

        # --- base case
        nar.say("Base case: nudge L by h and L moves by h, so L.grad is 1.")
        self.work(r"\frac{dL}{dL}=\frac{(L+h)-L}{h}", r"\frac{dL}{dL}=\frac{(-8+h)-(-8)}{h}",
                  r"\frac{dL}{dL}=1")
        self.play(*node_anims(nodes, vb, ["L"], data=False), run_time=0.9)
        self.play(Indicate(nodes["L"], color=ACTIVE), run_time=0.8)
        self.wait(0.5)

        # --- local derivative, times node
        nar.say("A local derivative is how one node reacts to its own inputs.")
        self.show_callout("Local derivative", "how a node reacts to its own inputs")
        nar.say("Predict: if d grows by 1, L changes by f. What number is that?")
        self.pulse_question("What is dL/dd, with f = -2?")
        nar.say("The times node swaps in the other input: dL/dd is f, dL/df is d.")
        self.back_through("L", arrows, vb)
        self.work(r"\frac{dL}{dd}=f,\;\frac{dL}{df}=d", r"\frac{dL}{dd}=(-2),\;\frac{dL}{df}=4",
                  r"\frac{dL}{dd}=-2,\;\frac{dL}{df}=4")
        self.play(*node_anims(nodes, vb, ["d", "f"], data=False), run_time=0.9)
        self.play(Indicate(nodes["d"], color=ACTIVE), Indicate(nodes["f"], color=ACTIVE), run_time=1.0)
        self.wait(0.5)

        # --- chain rule intuition: car, bicycle, man
        nar.say("Chain rule: rates multiply along a path, like a car and a bicycle.")
        self.play(FadeOut(group), FadeOut(title), run_time=0.6)
        man, bike_x, car_x = 1.0, 4.0, 8.0
        assert bike_x == 4 * man and car_x == 2 * bike_x
        v_man = vehicle_bar(-4.0, man, "walking man", GREY_B)
        v_bike = vehicle_bar(-1.2, bike_x, "bicycle", FWD)
        v_car = vehicle_bar(1.6, car_x, "car", GRAD)
        self.play(FadeIn(v_man), run_time=0.6)
        self.play(FadeIn(v_bike), run_time=0.8)
        self.play(FadeIn(v_car), run_time=0.8)
        times4 = MathTex(r"\times 4", font_size=44, color=FWD).move_to([-2.6, 0.2, 0])
        times2 = MathTex(r"\times 2", font_size=44, color=GRAD).move_to([0.2, 1.4, 0])
        self.play(FadeIn(times4), Indicate(v_bike[0], color=ACTIVE), run_time=1.0)
        self.play(FadeIn(times2), Indicate(v_car[0], color=ACTIVE), run_time=1.0)
        eight = MathTex(r"2\cdot 4=8", font_size=48).move_to([5.0, 0.3, 0])
        self.play(Write(eight), run_time=1.0)
        self.play(Indicate(v_car[0], color=ACTIVE), run_time=1.0)
        self.wait(2.0)
        nar.say("The car is 8 times the man: multiply the two rates along the way.")
        c = callout("Chain rule", "multiply the local derivatives along a path", width=7.0)
        c.move_to(SPOT)
        self.play(FadeIn(c), run_time=0.5)
        self.wait(3.2)
        self.play(*[FadeOut(m) for m in (v_man, v_bike, v_car, times4, times2, eight, c)],
                  FadeIn(group), FadeIn(title), run_time=0.8)

        # --- plus node: the router (zoom)
        nar.say("The plus node is a router: it hands the gradient to both inputs.")
        group.save_state()
        keep = [nodes["d"], nodes["e"], nodes["c"], ops["d"], *arrows["d"]]
        others = [m for m in group.submobjects if m not in keep]
        centre = ops["d"].get_center()
        self.play(*[m.animate.set_opacity(0.0) for m in others], FadeOut(title), run_time=0.6)
        self.play(group.animate.scale(1.5, about_point=centre), run_time=1.2)
        self.back_through("d", arrows, vb)
        self.play(Indicate(ops["d"], color=ACTIVE, scale_factor=1.4), run_time=1.0)
        self.wait(1.5)
        self.play(Restore(group), FadeIn(title), run_time=1.0)
        self.work(r"\frac{dL}{dc}=\frac{dL}{dd}\cdot\frac{dd}{dc}",
                  r"\frac{dL}{dc}=(-2)\cdot 1", r"\frac{dL}{dc}=-2")
        self.play(*node_anims(nodes, vb, ["e", "c"], data=False), run_time=0.9)
        self.play(Indicate(nodes["e"], color=ACTIVE), Indicate(nodes["c"], color=ACTIVE), run_time=1.0)
        self.wait(0.5)

        # --- a and b
        nar.say("Predict: e.grad is minus 2 and b is minus 3. What is a.grad?")
        self.pulse_question("What is dL/da = e.grad * b ?")
        nar.say("Multiply along the path: minus 2 times 1 times minus 3 is 6.")
        self.back_through("e", arrows, vb)
        self.work(r"\frac{dL}{da}=\frac{dL}{dd}\cdot\frac{dd}{de}\cdot\frac{de}{da}",
                  r"\frac{dL}{da}=(-2)\cdot 1\cdot(-3)", r"\frac{dL}{da}=6")
        self.play(*node_anims(nodes, vb, ["a"], data=False), run_time=0.9)
        self.play(Indicate(nodes["a"], color=ACTIVE), run_time=0.8)
        self.work(r"\frac{dL}{db}=\frac{dL}{de}\cdot a", r"\frac{dL}{db}=(-2)\cdot 2",
                  r"\frac{dL}{db}=-4")
        self.play(*node_anims(nodes, vb, ["b"], data=False), run_time=0.9)
        self.play(Indicate(nodes["b"], color=ACTIVE), run_time=0.8)
        self.wait(1.0)

        # --- numerical check
        nar.say("Check by nudging a a tiny bit: L should move about 6 times as far.")
        L0 = L_of(*A_IN)
        L1 = L_of(A_IN[0] + H, *A_IN[1:])
        slope = (L1 - L0) / H
        assert abs(slope - 6.0) < 1e-3
        self.work(r"\frac{L(a+h)-L(a)}{h}",
                  rf"\frac{{({fmt(L1)})-({fmt(L0)})}}{{{H}}}", r"\approx 6")
        self.play(Indicate(nodes["a"], color=GRAD), run_time=1.0)
        self.wait(0.8)

        # --- one optimisation step: number line and chips
        nar.say("One step: push every leaf a little along its own gradient.")
        self.play(FadeOut(group), FadeOut(title), run_time=0.6)
        new_in = tuple(x + STEP * vb[k].grad for x, k in zip(A_IN, "abcf"))
        L_new = L_of(*new_in)
        assert round(L_new, 4) == -7.2865 and L0 == -8.0
        rule = MathTex(r"x\leftarrow x+0.01\cdot\frac{dL}{dx}", font_size=44).move_to([0, 3.0, 0])
        chips = VGroup()
        for k, x0, x1 in zip("abcf", A_IN, new_in):
            g = vb[k].grad
            arr = Arrow(ORIGIN, UP * 0.7 * (1 if g > 0 else -1), color=GRAD, buff=0, stroke_width=6)
            nm = Text(k, font_size=30, color=WHITE, weight=BOLD)
            val = MathTex(rf"{p(x0)}\to {fmt(x1)}", font_size=36, color=LIGHT)
            chips.add(VGroup(nm, arr, val).arrange(RIGHT, buff=0.25))
        chips.arrange(RIGHT, buff=0.6).move_to([0, 1.5, 0])
        nl = NumberLine(x_range=[-9, -6, 1], length=9, include_numbers=True, font_size=28,
                        color=GREY_B).move_to([0, -0.6, 0])
        tr = ValueTracker(L0)
        dot = always_redraw(lambda: Dot(nl.n2p(tr.get_value()), radius=0.14, color=ACTIVE))
        lab = always_redraw(lambda: MathTex(rf"L={tr.get_value():.4f}", font_size=40,
                                            color=LIGHT).next_to(nl.n2p(tr.get_value()), UP, buff=0.35))
        self.play(FadeIn(rule), FadeIn(chips), Create(nl), run_time=1.2)
        self.add(dot, lab)
        self.wait(1.5)
        nar.say("Run the forward pass again: L rises from minus 8 to minus 7.2865.")
        self.play(tr.animate.set_value(L_new), run_time=2.5)
        self.play(Indicate(lab, color=ACTIVE), run_time=1.0)
        self.wait(2.5)
        self.remove(dot, lab)
        self.play(*[FadeOut(m) for m in (rule, chips, nl)], run_time=0.6)
        self.vb_a = vb

    # ------------------------------------------------------------------- ACT B
    def recompute(self, nodes, arrows, old, new):
        """Forward pulse with new data, then orange gradients flowing back with new numbers."""
        names = list(new.keys())
        self.recolour([a for l in arrows.values() for a in l], FWD)
        self.flow([a for l in arrows.values() for a in l], [1.0] * 9, reverse=False, color=FWD,
                  run_time=1.2)
        fresh = zero_grads(new)
        for k in names:
            fresh[k].data = new[k].data
        self.play(*node_anims(nodes, fresh, names), run_time=1.5)
        for k in ("L", "d", "e"):
            self.back_through(k, arrows, new)
        self.play(*node_anims(nodes, new, names, data=False), run_time=1.2)

    def act_b(self, nar):
        group, tag = self.group, self.tag_now
        vb_a = self.vb_a
        # rebuild the A graph so its nodes carry the final A numbers
        nodes, ops, arrows = build_graph(vb_a)
        old_group = group
        group = VGroup(*nodes.values(), *ops.values(), *[a for l in arrows.values() for a in l])
        nar.say("Example B: what if we change the four inputs? Watch the numbers morph.")
        self.play(FadeOut(tag), run_time=0.3)
        act_banner(self, "Example B: what if?", hold=2.6)
        tag_b = self.tag("Example B:")
        title = MathTex(r"L=(a\cdot b+c)\cdot f", font_size=44).move_to([-1.0, 3.1, 0])
        self.play(FadeIn(tag_b), FadeIn(group), FadeIn(title), run_time=1.0)
        self.wait(1.0)

        # B1
        b1 = backprop(graph(*B1_IN))
        assert abs(b1["L"].data + 6.5) < 1e-12
        assert [b1[k].grad for k in "abcf"] == [2.5, -1.0, 0.5, -13.0]
        nar.say("Set a = -2, b = 5, c = -3, f = 0.5. Every number is recomputed.")
        grid_a = grad_grid(vb_a, vb_a)
        self.play(FadeIn(grid_a), run_time=0.5)
        self.recompute(nodes, arrows, vb_a, b1)
        grid_b1 = grad_grid(vb_a, b1)
        self.play(Transform(grid_a, grid_b1), run_time=1.0)
        nar.say("L is now -6.5. Each gradient follows its own path of local derivatives.")
        self.play(Indicate(nodes["L"], color=ACTIVE), run_time=1.0)
        self.wait(2.5)
        nar.say("a.grad is e.grad times b: 0.5 times 5 is 2.5, down from 6.")
        self.play(Indicate(nodes["a"], color=GRAD), Indicate(grid_a[0], color=ACTIVE), run_time=1.2)
        self.wait(2.5)

        # B2
        b2 = backprop(graph(*B2_IN))
        assert b2["L"].data == 0.0 and b2["a"].grad == 0 and b2["b"].grad == 0
        assert b2["c"].grad == 0 and b2["f"].grad == 4.0
        nar.say("Now back to the notebook inputs, but with f = 0.")
        self.play(FadeOut(grid_a), run_time=0.3)
        self.pulse_question("With f = 0, what are a.grad and b.grad?")
        self.play(FadeIn(grid_a), run_time=0.3)
        nar.say("L is multiplied by zero, so nothing upstream can matter.")
        self.recompute(nodes, arrows, b1, b2)
        stop = MathTex(r"\times 0", font_size=56, color=RED).next_to(ops["L"], UP, buff=0.5)
        self.play(FadeIn(stop), Indicate(ops["L"], color=RED), run_time=1.0)
        grid_b2 = grad_grid(vb_a, b2)
        self.play(Transform(grid_a, grid_b2), run_time=1.0)
        self.wait(3.0)
        nar.say("Only f.grad survives. This is why a dead branch stops learning.")
        self.play(Indicate(nodes["f"], color=ACTIVE), run_time=1.2)
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in (group, title, grid_a, stop, tag_b)], run_time=0.8)

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        nar.say("Expert corner: how do we know backprop is right? Check it live.")
        act_banner(self, "Expert corner: gradient checking", hold=2.6)
        tag = self.tag("Expert corner:")
        self.play(FadeIn(tag), run_time=0.4)
        vals = backprop(graph(*A_IN))
        hh = 1e-6
        head = ["leaf", "backprop", "finite difference", "error"]
        xs = [-4.8, -2.4, 0.8, 4.4]
        header = VGroup(*[Text(t, font_size=28, color=ACTIVE).move_to([x, 2.5, 0])
                          for t, x in zip(head, xs)])
        line = Line([-6.0, 2.1, 0], [6.0, 2.1, 0], color=GREY_B)
        self.play(FadeIn(header), Create(line), run_time=0.8)
        rows = []
        worst = 0.0
        for i, k in enumerate("abcf"):
            lo = list(A_IN)
            hi = list(A_IN)
            j = "abcf".index(k)
            lo[j] -= hh
            hi[j] += hh
            num = (L_of(*hi) - L_of(*lo)) / (2 * hh)
            err = abs(num - vals[k].grad)
            worst = max(worst, err)
            assert err < 1e-8, (k, err)
            y = 1.5 - 0.8 * i
            cells = [
                Text(k, font_size=30, color=WHITE, weight=BOLD).move_to([xs[0], y, 0]),
                Text(fmt(vals[k].grad), font_size=30, color=GRAD).move_to([xs[1], y, 0]),
                Text(f"{num:.7f}", font_size=30, color=LIGHT).move_to([xs[2], y, 0]),
                Text(f"{err:.1e}", font_size=30, color=FWD).move_to([xs[3], y, 0]),
            ]
            rows.append(VGroup(*cells))
        nar.say("For every leaf, nudge it both ways and measure how L reacts.")
        for r in rows[:2]:
            self.play(FadeIn(r[0]), FadeIn(r[1]), run_time=0.5)
            self.play(FadeIn(r[2]), run_time=0.6)
            self.play(FadeIn(r[3]), run_time=0.6)
        nar.say("Backprop and finite differences agree to about ten decimals.")
        for r in rows[2:]:
            self.play(FadeIn(r[0]), FadeIn(r[1]), run_time=0.5)
            self.play(FadeIn(r[2]), run_time=0.6)
            self.play(FadeIn(r[3]), run_time=0.6)
        self.play(*[Indicate(r[3], color=ACTIVE) for r in rows], run_time=1.2)
        self.wait(2.5)
        nar.say("This costs two forward passes per leaf, so it is only a test.")
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in (header, line, *rows)], run_time=0.6)

        # --- reverse-mode against forward-mode
        n = 1000
        xs_v = [Value(0.001 * (i + 1), label=f"x{i}") for i in range(n)]
        terms = [x * x for x in xs_v]
        while len(terms) > 1:  # pairwise sum keeps the graph shallow
            terms = [terms[i] + terms[i + 1] if i + 1 < len(terms) else terms[i]
                     for i in range(0, len(terms), 2)]
        y = terms[0]
        y.backward()  # ONE backward pass
        assert all(abs(x.grad - 2 * x.data) < 1e-12 for x in xs_v)
        passes_rev, passes_fwd = 1, len(xs_v)
        nar.say("Reverse mode: one backward pass gives the slope for ALL inputs.")
        setup = MathTex(r"f:\mathbb{R}^{1000}\to\mathbb{R}", font_size=48).move_to([0, 2.7, 0])
        W = 7.0
        t = ValueTracker(0)
        lab_r = Text("reverse (backprop)", font_size=28, color=GRAD).move_to([-4.3, 1.1, 0])
        lab_f = Text("forward mode", font_size=28, color=FWD).move_to([-4.3, -0.3, 0])
        x0 = -2.2

        def bar(color, passes, y_pos):
            def make():
                w = max(0.02, W * min(t.get_value() / passes, 1.0))
                return Rectangle(width=w, height=0.6, fill_color=color, fill_opacity=0.9,
                                 stroke_width=0).move_to([x0 + w / 2, y_pos, 0])
            return always_redraw(make)

        def count(passes, y_pos):
            return always_redraw(lambda: Text(
                f"{min(int(t.get_value()), passes)} of {passes} passes", font_size=28,
                color=WHITE).move_to([x0 + W / 2, y_pos - 0.65, 0]))

        bars = [bar(GRAD, passes_rev, 1.1), bar(FWD, passes_fwd, -0.3)]
        counts = [count(passes_rev, 1.1), count(passes_fwd, -0.3)]
        self.play(FadeIn(setup), FadeIn(lab_r), FadeIn(lab_f), run_time=0.8)
        self.add(*bars, *counts)
        self.wait(1.0)
        nar.say("Forward mode needs one pass per input. Watch them race.")
        self.play(t.animate.set_value(passes_fwd), run_time=6.0, rate_func=linear)
        done = Text("done at pass 1", font_size=28, color=GRAD).move_to([x0 + W / 2, 1.75, 0])
        self.play(FadeIn(done), Indicate(bars[0], color=ACTIVE), run_time=1.0)
        self.wait(1.5)
        nar.say("Millions of weights and one loss: that is why networks use reverse mode.")
        c = callout("Reverse mode", "1 pass for all gradients of 1 output", width=7.0)
        c.move_to([0, -1.95, 0])
        self.play(FadeIn(c), run_time=0.5)
        self.wait(3.2)
        self.remove(*bars, *counts)
        self.play(*[FadeOut(m) for m in (setup, lab_r, lab_f, done, c, tag)], run_time=0.8)
        self.wait(0.3)
