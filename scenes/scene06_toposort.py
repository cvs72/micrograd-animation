import sys
import textwrap

from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, arrow_between, callout,
    code_panel, fmt, particle_flow, recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value

CODE_CLOSURES = '''def _backward():  # inside plus
    self.grad += out.grad
    other.grad += out.grad
def _backward():  # inside times
    self.grad += other.data * out.grad
    other.grad += self.data * out.grad
def _backward():  # inside tanh
    self.grad += (1 - t**2) * out.grad'''
CODE_RECURSIVE = '''def build_topo(v):
    if v not in visited:
        visited.add(v)
        for child in v._prev:
            build_topo(child)
        topo.append(v)'''
CODE_ITERATIVE = '''def topo_iterative(root):
    order, seen = [], set()
    stack = [(root, False)]
    while stack:
        v, done = stack.pop()
        if done:
            order.append(v)
        elif v not in seen:
            seen.add(v)
            stack += [(v, True)]
            stack += [(c, False) for c in v._prev]
    return order'''
HUD = {
    "+": "self.grad += out.grad",
    "*": "self.grad += other.data * out.grad",
    "tanh": "self.grad += (1 - t**2) * out.grad",
    "": "pass  # a leaf has nothing to pass on",
}

POS_N = {
    "x1": [-5.7, 2.5, 0], "w1": [-5.7, 1.65, 0], "x2": [-5.7, 0.8, 0], "w2": [-5.7, -0.05, 0],
    "x1w1": [-3.2, 2.07, 0], "x2w2": [-3.2, 0.38, 0], "sum": [-0.6, 1.22, 0], "b": [-0.6, 2.5, 0],
    "n": [2.0, 1.9, 0], "o": [4.9, 1.9, 0],
}
POS_D = {"a": [-4.6, 0.9, 0], "b": [-1.0, 1.9, 0], "c": [-1.0, -0.1, 0], "d": [3.0, 0.9, 0]}
LIST_Y = -1.35


# ------------------------------------------------------------------ engine side
def neuron():
    """The neuron of chapter 5 (the notebook's numbers), ten labelled Values."""
    x1, x2 = Value(2.0, label="x1"), Value(0.0, label="x2")
    w1, w2 = Value(-3.0, label="w1"), Value(1.0, label="w2")
    b = Value(6.8813735870195432, label="b")
    x1w1 = x1 * w1
    x1w1.label = "x1w1"
    x2w2 = x2 * w2
    x2w2.label = "x2w2"
    s = x1w1 + x2w2
    s.label = "sum"
    n = s + b
    n.label = "n"
    o = n.tanh()
    o.label = "o"
    vals = {v.label: v for v in (x1, w1, x2, w2, x1w1, x2w2, s, b, n, o)}
    return vals


def diamond():
    a = Value(2.0, label="a")
    b = a * 2.0
    b.label = "b"
    c = a + 3.0
    c.label = "c"
    d = b * c
    d.label = "d"
    return {"a": a, "b": b, "c": c, "d": d}


def trace_dfs(root):
    """The depth-first walk of build_topo, recorded as (visit|done, node) events."""
    events, visited = [], set()

    def build(v):
        if v not in visited:
            visited.add(v)
            events.append(("visit", v))
            for ch in v._prev:
                build(ch)
            events.append(("done", v))

    build(root)
    return events


def topo_iterative(root):
    """A NEW function (engine.backward is untouched): topological sort with an explicit stack."""
    order, seen, stack, deepest = [], set(), [(root, False)], 0
    while stack:
        deepest = max(deepest, len(stack))
        v, done = stack.pop()
        if done:
            order.append(v)
        elif v not in seen:
            seen.add(v)
            stack.append((v, True))
            for ch in v._prev:
                stack.append((ch, False))
    return order, deepest


def reset(nodes):
    for v in nodes:
        v.grad = 0.0


def run_order(vals, out, order):
    """Zero all grads, seed the output with 1 and call each _backward in the given order."""
    for v in topo_iterative(out)[0]:
        v.grad = 0.0
    out.grad = 1.0
    for v in order:
        v._backward()
    return vals["a"].grad if "a" in vals else None


def chain(n):
    x = Value(1.0, label="x")
    s = x
    for _ in range(n):
        s = s + 1.0
    return x, s


def count_graph(root):
    order, _ = topo_iterative(root)
    return len(order), sum(len(v._prev) for v in order)


def valid_order(order):
    pos = {id(v): i for i, v in enumerate(order)}
    return all(pos[id(ch)] < pos[id(v)] for v in order for ch in v._prev if id(ch) in pos)


# ------------------------------------------------------------------ drawing side
def chip(label, data, grad, width=1.7):
    nm = Text(f"{label} = {fmt(data)}", font_size=24, color=WHITE)
    g = Text(f"grad = {fmt(grad)}", font_size=24, color=GRAD)
    body = VGroup(nm, g).arrange(DOWN, buff=0.06)
    box = RoundedRectangle(corner_radius=0.12, width=max(width, body.width + 0.2), height=0.8,
                           stroke_color=WHITE, stroke_width=2)
    body.move_to(box)
    node = VGroup(box, body)
    node.box, node.g = box, g
    return node


def tile(label):
    r = RoundedRectangle(corner_radius=0.1, width=1.0, height=0.5, stroke_color=WHITE,
                         stroke_width=2)
    t = Text(label, font_size=24, color=WHITE)
    if t.width > 0.92:
        t.scale_to_fit_width(0.92)
    t.move_to(r)
    g = VGroup(r, t)
    g.box = r
    return g


def slot_a(i):
    return [-5.0 + 1.1 * i, LIST_Y, 0]


def slot_b(i):
    return [-3.2 + 1.2 * i, -1.4, 0]


class FlatNarrator(CrossfadeNarrator):
    pass


class Scene06TopoSort(Scene):
    # ---------------------------------------------------------------- helpers
    def tag(self, text):
        return Tex(r"\textbf{" + text + "}", font_size=34, color=ACTIVE).to_corner(UL, buff=0.5)

    def pulse_question(self, text, pos, qpos, n=3):
        q = Text(text, font_size=30, color=WHITE).move_to(pos)
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to(qpos)
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        return VGroup(q, qm)

    def build_graph(self, vals, pos):
        self.vals = vals
        self.chips = {k: chip(k, v.data, v.grad).move_to(pos[k]) for k, v in vals.items()}
        self.arrows = {}
        for k, v in vals.items():
            for ch in v._prev:
                if ch.label in self.chips:
                    self.arrows[(ch.label, k)] = arrow_between(self.chips[ch.label],
                                                               self.chips[k], color=FWD)
        return VGroup(*self.chips.values()), VGroup(*self.arrows.values())

    def grad_anim(self, v, color=GRAD, run_time=0.8):
        c = self.chips[v.label]
        new = Text(f"grad = {fmt(v.grad)}", font_size=24, color=color).move_to(c.g)
        return Transform(c.g, new, run_time=run_time)

    def reset_grads(self, instant=True):
        anims = []
        for k, v in self.vals.items():
            v.grad = 0.0
            c = self.chips[k]
            new = Text("grad = 0", font_size=24, color=GRAD).move_to(c.g)
            if instant:
                c.g.become(new)
                c.box.set_stroke(WHITE, width=2)
            else:
                anims += [Transform(c.g, new), c.box.animate.set_stroke(WHITE, width=2)]
        if anims:
            self.play(*anims, run_time=0.8)

    def back_step(self, v, run_time=0.8, gcolor=GRAD):
        """Call the real _backward of v and show the gradient travelling to its children."""
        c = self.chips[v.label]
        kids = [k for k in v._prev if k.label in self.chips]
        v._backward()
        flows = [particle_flow(self.arrows[(k.label, v.label)], 1, color=BWD, n=2, reverse=True,
                               run_time=run_time) for k in kids]
        dots = VGroup(*[f.dots for f in flows])
        self.add(dots)
        self.play(c.box.animate.set_stroke(BWD, width=6), *flows,
                  *[self.grad_anim(k, color=gcolor, run_time=run_time) for k in kids])
        self.remove(dots, *dots.submobjects, *[f.mobject for f in flows])
        self.remove(*[d for f in flows for d in f.dots.submobjects])
        if not kids:
            self.play(Indicate(c, color=BWD), run_time=0.5)

    def set_hud(self, op):
        new = code_panel(HUD[op], font_size=24)
        if new.width > 6.5:
            new.scale_to_fit_width(6.5)
        new.move_to([2.0, 3.3, 0])
        if getattr(self, "hud", None) is None:
            self.play(FadeIn(new), run_time=0.3)
        else:
            self.play(FadeTransform(self.hud, new), run_time=0.3)
        self.hud = new

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = FlatNarrator(self, "S06")
        self.hud = None
        title_card(self, "Chapter 6", "In which order should the backward pass visit the nodes?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        recap_line(self, "Next: what goes wrong when one node is used twice?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        ref = neuron()
        ref["o"].backward()
        want = {k: ref[k].grad for k in ("x1", "w1", "x2", "w2")}
        assert [round(want[k], 4) for k in ("x1", "w1", "x2", "w2")] == [-1.5, 1.0, 0.5, 0.0]
        vals = neuron()
        o = vals["o"]
        assert round(o.data, 4) == 0.7071

        nar.say("Example A: the neuron from chapter 5, with its gradients still empty.")
        act_banner(self, "Example A: who goes first?", hold=2.6)
        tag = self.tag("Example A:")
        nodes, arrows = self.build_graph(vals, POS_N)
        self.play(FadeIn(tag), FadeIn(nodes), run_time=1.0)
        self.play(Create(arrows), run_time=1.2)
        self.wait(1.0)

        nar.say("Which node's backward must run first? Think about who needs whose gradient.")
        q = self.pulse_question("Which node goes first?", [-0.5, -1.3, 0], [4.2, -1.3, 0])
        nar.say("The output o goes first: its own gradient is 1, and it feeds the rest.")
        o.grad = 1.0
        self.play(FadeOut(q), Indicate(self.chips["o"], color=ACTIVE), self.grad_anim(o),
                  run_time=1.2)
        self.wait(1.0)

        nar.say("By hand, each step hands a gradient to children, so the order matters.")
        for v in [o, vals["n"], vals["sum"], vals["x2w2"], vals["x1w1"]]:
            self.back_step(v)
        for k in want:
            assert abs(vals[k].grad - want[k]) < 1e-12
        self.wait(1.5)
        nar.say("That works, but we want the computer to find a safe order itself.")
        self.wait(1.5)

        # --- closures
        self.reset_grads(instant=True)
        stage = VGroup(nodes, arrows)
        panel = code_panel(CODE_CLOSURES, font_size=24)
        panel.scale_to_fit_width(9.0).move_to([0, -0.2, 0])
        cl = callout("Closure", "a small function that remembers its own node", width=9.5)
        cl.move_to([0, 3.0, 0])
        nar.say("Each operation stores a closure: its own little backward rule.")
        self.play(FadeOut(stage), FadeIn(panel), FadeIn(cl), run_time=0.9)
        self.wait(2.0)
        hl = SurroundingRectangle(panel.code_lines[1:3], color=ACTIVE, buff=0.05)
        nar.say("Plus passes it on, times swaps the inputs, tanh uses one minus o squared.")
        self.play(Create(hl), run_time=0.5)
        self.wait(1.5)
        for rows in (slice(4, 6), slice(7, 8)):
            self.play(Transform(hl, SurroundingRectangle(panel.code_lines[rows], color=ACTIVE,
                                                         buff=0.05)), run_time=0.6)
            self.wait(1.6)
        self.play(FadeOut(panel), FadeOut(hl), FadeOut(cl), FadeIn(stage), run_time=0.8)

        # --- depth-first walk
        nar.say("Topological order: every node comes after all of its children.")
        top = callout("Topological order", "every node comes after all of its children", width=9.5)
        top.move_to([0, -1.5, 0])
        self.play(FadeIn(top), run_time=0.5)
        self.wait(3.0)
        self.play(FadeOut(top), run_time=0.4)
        lab = Text("order list", font_size=24, color=SECOND).move_to([-4.4, -0.82, 0])
        self.play(FadeIn(lab), run_time=0.4)
        nar.say("Walk down from o. A node turns yellow when we step into it.")
        events = trace_dfs(o)
        order = [v for kind, v in events if kind == "done"]
        assert order == o.topo() and len(order) == 10
        tiles, k = [], 0
        for kind, v in events:
            c = self.chips[v.label]
            if kind == "visit":
                self.play(c.box.animate.set_stroke(ACTIVE, width=6), run_time=0.35)
            else:
                if k == 0:
                    nar.say("It drops into the list only after all its children are in it.")
                t = tile(v.label).move_to(c.get_center())
                self.add(t)
                self.play(t.animate.move_to(slot_a(k)), c.box.animate.set_stroke(FWD, width=4),
                          run_time=0.5)
                tiles.append(t)
                k += 1
        self.wait(0.8)
        nar.say("Children first, output last. Now we flip the list around.")
        brace = Brace(VGroup(*tiles), DOWN, buff=0.1, color=FWD)
        rule = Text("children first, parent last", font_size=24, color=FWD)
        rule.next_to(brace, DOWN, buff=0.1)
        self.play(GrowFromCenter(brace), FadeIn(rule), run_time=0.8)
        self.wait(1.5)
        self.play(FadeOut(brace), FadeOut(rule), run_time=0.4)
        self.play(*[t.animate.move_to(slot_a(len(tiles) - 1 - i)) for i, t in enumerate(tiles)],
                  run_time=1.4)
        self.wait(0.8)

        nar.say("Backward now runs along the flipped list and fills every gradient.")
        self.reset_grads(instant=False)
        o.grad = 1.0
        self.play(self.grad_anim(o), run_time=0.5)
        by_label = {v.label: t for v, t in zip(order, tiles)}
        for v in reversed(order):
            self.set_hud(v._op if v._op in HUD else "")
            self.play(by_label[v.label].box.animate.set_stroke(BWD, width=6), run_time=0.3)
            self.back_step(v, run_time=0.6)
        for kk in want:
            assert abs(vals[kk].grad - want[kk]) < 1e-12
        nar.say("Same answers as by hand: x1 gets minus 1.5 and w1 gets 1.0.")
        self.play(*[Indicate(self.chips[kk], color=BWD) for kk in ("x1", "w1")], run_time=1.2)
        self.wait(2.0)
        self.play(FadeOut(self.hud), FadeOut(VGroup(*tiles)), FadeOut(lab), run_time=0.6)
        self.hud = None

        # --- wrong order
        nar.say("Wrong order: x1w1 runs before its parent has pushed a gradient to it.")
        self.reset_grads(instant=False)
        o.grad = 1.0
        self.play(self.grad_anim(o), run_time=0.4)
        x1w1 = vals["x1w1"]
        self.play(Indicate(self.chips["x1w1"], color=RED), run_time=1.0)
        self.back_step(x1w1, gcolor=RED)
        assert vals["x1"].grad == 0.0 and vals["w1"].grad == 0.0
        assert abs(want["x1"] - vals["x1"].grad) > 1.0
        nar.say("It pushes a zero into x1 and w1. Their true values need the order.")
        note = VGroup(
            Text("x1w1 still holds grad 0, so x1 and w1 get 0", font_size=28, color=RED),
            Text(f"the right answers are {fmt(want['x1'])} and {fmt(want['w1'])}", font_size=28,
                 color=WHITE),
        ).arrange(DOWN, buff=0.15).move_to([0, -1.4, 0])
        self.play(FadeIn(note), run_time=0.6)
        self.wait(3.0)
        self.play(FadeOut(note), FadeOut(stage), FadeOut(tag), run_time=0.8)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        nar.say("Example B: a diamond, where one node feeds two different nodes.")
        act_banner(self, "Example B: more than one valid order", hold=2.6)
        tag = self.tag("Example B:")
        vals = diamond()
        a, b, c, d = (vals[k] for k in "abcd")
        assert (b.data, c.data, d.data) == (4.0, 5.0, 20.0)
        # expected answers come from fresh copies of the graph
        fresh = diamond()
        order1 = [v for v in fresh["d"].topo() if v.label]
        assert valid_order(fresh["d"].topo())
        order2 = list(order1)
        i, j = order2.index(fresh["b"]), order2.index(fresh["c"])
        order2[i], order2[j] = order2[j], order2[i]
        assert valid_order(order1) and valid_order(order2)
        res1 = run_order(fresh, fresh["d"], list(reversed(order1)))
        res2 = run_order(fresh, fresh["d"], list(reversed(order2)))
        bad_list = [fresh["a"], fresh["b"], fresh["d"], fresh["c"]]
        assert not valid_order(bad_list)
        res3 = run_order(fresh, fresh["d"], list(reversed(bad_list)))
        assert res1 == 14.0 and res2 == 14.0 and res3 != 14.0
        names1 = [v.label for v in order1]
        names2 = [v.label for v in order2]
        names3 = [v.label for v in bad_list]

        nodes, arrows = self.build_graph(vals, POS_D)
        self.play(FadeIn(tag), FadeIn(nodes), run_time=0.9)
        self.play(Create(arrows), run_time=1.0)
        self.wait(1.0)
        lab = Text("order list:", font_size=24, color=SECOND).move_to([-5.3, -1.4, 0])
        tiles = {n: tile(n).move_to(slot_b(i)) for i, n in enumerate(names1)}
        nar.say("Here b and c do not depend on each other, so either may come first.")
        self.play(FadeIn(lab), *[FadeIn(t) for t in tiles.values()], run_time=0.8)
        self.wait(1.5)

        nar.say("Predict: will the other valid order change the gradient of a?")
        q = self.pulse_question("Does the order change a.grad?", [-0.5, 3.2, 0], [4.2, 3.2, 0])
        self.play(FadeOut(q), run_time=0.4)

        def run_list(names, wrong=False):
            lst = {v.label: v for v in vals.values()}
            d.grad = 1.0
            self.play(self.grad_anim(d), run_time=0.4)
            for nm in reversed(names):
                self.play(tiles[nm].box.animate.set_stroke(RED if wrong else BWD, width=6),
                          run_time=0.25)
                self.back_step(lst[nm], run_time=0.6, gcolor=RED if wrong else GRAD)

        nar.say("First order: the engine's own topological list, run from the end.")
        run_list(names1)
        assert a.grad == 14.0
        wl = working_line(
            self, r"\frac{\partial d}{\partial a}=c\cdot 2+b\cdot 1",
            rf"\frac{{\partial d}}{{\partial a}}={fmt(c.data)}\cdot 2+{fmt(b.data)}\cdot 1",
            rf"\frac{{\partial d}}{{\partial a}}={fmt(a.grad)}", pos=[3.6, -1.4, 0], width=4.4)
        self.wait(0.5)

        nar.say("Second order: b and c swapped. Same gradient for a, nothing changes.")
        self.play(FadeOut(wl), run_time=0.4)
        self.reset_grads(instant=False)
        pos_by_name = {n: slot_b(i) for i, n in enumerate(names2)}
        self.play(*[t.animate.move_to(pos_by_name[n]).set_stroke(WHITE, width=2)
                    for n, t in tiles.items()], run_time=1.0)
        run_list(names2)
        assert a.grad == 14.0
        ok = Text(f"a.grad = {fmt(a.grad)} again", font_size=30, color=FWD).move_to([3.6, -1.4, 0])
        self.play(FadeIn(ok), Indicate(self.chips["a"], color=FWD), run_time=1.0)
        self.wait(2.0)

        nar.say("Invalid order: c runs before d, so c's gradient is still zero.")
        self.play(FadeOut(ok), run_time=0.4)
        self.reset_grads(instant=False)
        pos_by_name = {n: slot_b(i) for i, n in enumerate(names3)}
        self.play(*[t.animate.move_to(pos_by_name[n]).set_stroke(WHITE, width=2)
                    for n, t in tiles.items()], run_time=1.0)
        bad = Text("d comes before c: not allowed", font_size=28, color=RED).move_to([3.6, -1.9, 0])
        self.play(FadeIn(bad), run_time=0.4)
        run_list(names3, wrong=True)
        assert a.grad == res3 and a.grad != 14.0
        wrong = Text(f"a.grad = {fmt(a.grad)}, not {fmt(res1)}", font_size=30, color=RED)
        wrong.move_to([3.6, -1.4, 0])
        self.play(FadeIn(wrong), Indicate(self.chips["a"], color=RED), run_time=1.0)
        self.wait(3.0)
        self.play(FadeOut(VGroup(nodes, arrows, lab, wrong, bad, tag, *tiles.values())),
                  run_time=0.8)

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        nar.say("Expert corner: how much work is the sort, and can it fail?")
        act_banner(self, "Expert corner: cost and recursion", hold=2.6)
        tag = self.tag("Expert corner:")
        self.play(FadeIn(tag), run_time=0.4)

        ns = [50, 100, 150, 200, 250, 300]
        counts = []
        for n in ns:
            x, s = chain(n)
            nn, ee = count_graph(s)
            assert nn == 2 * n + 1 and ee == 2 * n
            counts.append(nn + ee)
        ax = Axes(x_range=[0, 300, 100], y_range=[0, 1200, 400], x_length=6.5, y_length=2.9,
                  axis_config={"include_numbers": True, "font_size": 24}, tips=False)
        ax.move_to([-1.2, 0.0, 0])
        xl = Text("chain of n additions", font_size=24, color=SECOND)
        xl.move_to(ax.c2p(150, 0) + DOWN * 0.85)
        yl = Text("nodes + edges", font_size=24, color=SECOND).rotate(PI / 2)
        yl.next_to(ax.y_axis, LEFT, buff=0.95)
        line = ax.plot_line_graph(ns, counts, line_color=FWD, vertex_dot_radius=0.08,
                                  stroke_width=4)
        nar.say("The sort visits every node once, so the cost is nodes plus edges.")
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), run_time=1.5)
        self.play(Create(line), run_time=1.8)
        n_last, tot = ns[-1], counts[-1]
        wl = working_line(
            self, r"N+E=(2n+1)+2n",
            rf"N+E=(2\cdot {n_last}+1)+2\cdot {n_last}", rf"N+E={tot}",
            pos=[1.8, 3.0, 0], width=6.0)
        assert tot == 4 * n_last + 1
        cl = callout("Straight line", "twice the nodes means twice the work", width=7.5)
        cl.move_to([1.8, 3.0, 0])
        nar.say("Twice the nodes, twice the work: a straight line on the plot.")
        self.play(FadeOut(wl), FadeIn(cl), run_time=0.5)
        self.wait(3.0)
        self.play(FadeOut(cl), FadeOut(VGroup(ax, xl, yl, line)), run_time=0.6)

        # --- recursion limit
        limit = sys.getrecursionlimit()
        assert limit == 1000
        x, big = chain(2000)
        err = None
        try:
            big.topo()
        except RecursionError as e:
            err = e
        assert err is not None
        msg = str(err)
        order2, deepest = topo_iterative(big)
        assert len(order2) == 4001
        big.grad = 1.0
        for v in reversed(order2):
            v._backward()
        assert x.grad == 1.0 and valid_order(order2)

        expr = MathTex(r"x+1+1+\cdots+1\;(2000\ \mathrm{times})", font_size=40, color=WHITE)
        expr.move_to([0, 2.9, 0])
        pred = self.pulse_question("Can the recursive sort handle 2000?", [-0.5, 1.9, 0],
                                   [4.4, 1.9, 0])
        panel = code_panel(CODE_RECURSIVE, font_size=24)
        panel.scale_to_fit_width(6.2).move_to([-3.1, -0.1, 0])
        nar.say("Now one long chain: 2000 additions in a row, sorted with recursion.")
        self.play(FadeIn(expr), FadeOut(pred), FadeIn(panel), run_time=0.8)
        depth = ValueTracker(0)
        frame = Rectangle(width=4.0, height=0.5, stroke_color=WHITE, stroke_width=3)
        frame.move_to([3.7, 0.6, 0])
        bar = always_redraw(lambda: Rectangle(
            width=max(0.01, 4.0 * depth.get_value() / limit), height=0.5, stroke_width=0,
            fill_color=FWD, fill_opacity=1).align_to(frame, LEFT).align_to(frame, UP))
        count = always_redraw(lambda: Text(f"call depth {int(depth.get_value())}", font_size=28,
                                           color=WHITE).next_to(frame, UP, buff=0.2))
        lim = Text(f"Python's limit: {limit}", font_size=28, color=SECOND).next_to(frame, DOWN,
                                                                                    buff=0.2)
        self.play(Create(frame), FadeIn(lim), FadeIn(bar), FadeIn(count), run_time=0.8)
        self.play(depth.animate.set_value(limit), run_time=3.0, rate_func=linear)
        wrapped = textwrap.wrap(msg, 30)
        etext = VGroup(Text("RecursionError:", font_size=28, color=RED, weight=BOLD),
                       *[Text(w, font_size=26, color=RED) for w in wrapped])
        etext.arrange(DOWN, buff=0.1).move_to([3.7, -0.95, 0])
        if etext.width > 5.2:
            etext.scale_to_fit_width(5.2)
        nar.say("Python stops us at depth 1000: a RecursionError, with 2000 to go.")
        self.play(bar.animate.set_fill(RED), FadeIn(etext), Flash(frame, color=RED), run_time=1.0)
        self.wait(2.5)

        nar.say("The fix is a new function with its own stack, so no deep recursion.")
        it = code_panel(CODE_ITERATIVE, font_size=24)
        it.scale_to_fit_width(6.2).move_to([-3.2, -0.1, 0])
        self.play(ReplacementTransform(panel, it), FadeOut(etext), FadeOut(lim), run_time=1.0)
        self.play(depth.animate.set_value(0), bar.animate.set_fill(FWD), run_time=0.6)
        done = ValueTracker(0)
        counter = always_redraw(lambda: Text(f"sorted {int(done.get_value())} of {len(order2)}",
                                             font_size=28, color=FWD).move_to([3.7, -0.6, 0]))
        self.play(FadeIn(counter), run_time=0.3)
        self.play(done.animate.set_value(len(order2)), run_time=3.0, rate_func=linear)
        res = MathTex(rf"\frac{{\partial\,\mathrm{{out}}}}{{\partial x}}={fmt(x.grad)}",
                      font_size=40, color=GRAD).move_to([3.7, -1.6, 0])
        nar.say("It sorts all 4001 nodes, and backward then reaches x without any error.")
        self.play(FadeIn(res), Indicate(counter, color=FWD), run_time=1.0)
        self.wait(2.0)
        cl2 = callout("Heap stack", "a list on the heap can grow; the call stack cannot",
                      width=9.5).move_to([1.0, 2.9, 0])
        nar.say("Real frameworks avoid deep recursion for exactly this reason.")
        self.play(FadeOut(expr), FadeIn(cl2), run_time=0.5)
        self.wait(3.0)
        self.play(FadeOut(VGroup(cl2, it, frame, bar, count, counter, res, tag)), run_time=0.8)
        self.remove(bar, count, counter)
