from manim import *

from micrograd_animation.anim import (
    ACTIVE, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, code_panel, fmt,
    make_value_node, particle_flow, recap_line, title_card, working_line,
)
from micrograd_animation.engine import Value

LIGHT = BLUE_B  # readable data colour on black
CODE_VALUE = '''class Value:
    def __init__(self, data,
                 _children=(), _op="", label=""):
        self.data = data
        self.grad = 0.0
        self._prev = set(_children)
        self._op = _op
        self.label = label'''
WS = [1.0, 2.0, 3.0, 4.0, 5.0]

POS_A = {
    "a": [-5.6, 2.0, 0], "b": [-5.6, 0.4, 0], "e": [-2.0, 1.2, 0], "c": [-2.0, -0.8, 0],
    "d": [1.6, 0.2, 0], "f": [1.6, -1.7, 0], "L": [5.2, -0.75, 0],
}
POS_B = {
    "a": [-5.6, 2.0, 0], "b": [-5.6, 0.7, 0], "c": [-5.6, -0.6, 0], "f": [-5.6, -1.9, 0],
    "s": [-2.0, 1.35, 0], "t": [-2.0, -1.25, 0], "L2": [1.8, 0.05, 0],
}
PAIRS = [("a", "a"), ("b", "b"), ("c", "c"), ("f", "f"), ("e", "s"), ("d", "t"), ("L", "L2")]


def p(x):
    return f"({fmt(x)})" if x < 0 else fmt(x)


def graph_a():
    """The notebook's L = (a*b + c) * f, built with the Value class."""
    a = Value(2.0, label="a")
    b = Value(-3.0, label="b")
    c = Value(10.0, label="c")
    e = a * b
    e.label = "e"
    d = e + c
    d.label = "d"
    f = Value(-2.0, label="f")
    L = d * f
    L.label = "L"
    return {"a": a, "b": b, "c": c, "e": e, "d": d, "f": f, "L": L}


def graph_b():
    """The what-if: L2 = (a + b) * (c + f)."""
    a = Value(3.0, label="a")
    b = Value(-1.0, label="b")
    c = Value(2.0, label="c")
    f = Value(4.0, label="f")
    s = a + b
    s.label = "s"
    t = c + f
    t.label = "t"
    L2 = s * t
    L2.label = "L2"
    return {"a": a, "b": b, "c": c, "f": f, "s": s, "t": t, "L2": L2}


def count_ops(vals, op):
    return sum(1 for v in vals.values() if v._op == op)


def op_circle(op):
    """Operation circle: a drawing helper made by draw_dot, NOT a Value."""
    c = Circle(radius=0.3, color=SECOND, stroke_width=3, fill_color=BLACK, fill_opacity=1)
    t = Text(op, font_size=30, color=WHITE).move_to(c)
    return VGroup(c, t)


def build_graph(vals, pos, scale=0.95):
    """Nodes (rounded rectangles), operation circles and arrows for a dict of Values."""
    nodes = {k: make_value_node(k, v.data, v.grad, width=2.0).scale(scale).move_to(pos[k])
             for k, v in vals.items()}
    ops, arrows = {}, {}
    for k, v in vals.items():
        if not v._op:
            continue
        kids = sorted((ch.label for ch in v._prev), key=lambda n: -pos[n][1])
        right = max(nodes[n].get_right()[0] for n in kids)
        x = (right + nodes[k].get_left()[0]) / 2
        circ = op_circle(v._op).move_to([x, pos[k][1], 0])
        ops[k] = circ
        kw = dict(buff=0.05, color=FWD, stroke_width=4, tip_length=0.16)
        arrows[k] = [Arrow(nodes[n].get_right(), circ.get_left(), **kw) for n in kids]
        arrows[k].append(Arrow(circ.get_right(), nodes[k].get_left(), **kw))
    return nodes, ops, arrows


def chip(label, data):
    t = Text(f"{label} = {fmt(data)}", font_size=24, color=WHITE)
    box = RoundedRectangle(corner_radius=0.12, width=1.45, height=0.55, stroke_color=WHITE,
                           stroke_width=2)
    t.move_to(box)
    return VGroup(box, t)


def run_loop(n):
    """The define-by-run loop: the graph exists only because this code ran."""
    s = Value(0.0, label="s0")
    vals = {"s0": s}
    for i, w in enumerate(WS[:n], 1):
        wv = Value(w, label=f"w{i}")
        s = s + wv
        s.label = f"s{i}"
        vals[f"w{i}"] = wv
        vals[f"s{i}"] = s
    return vals, s


def build_chain(vals, n):
    """Chips for the loop graph; returns chips and one (arrow, circle, up-arrow) per turn."""
    xs = [-5.6 + 2.3 * i for i in range(n + 1)]
    chips = {}
    for i in range(n + 1):
        chips[f"s{i}"] = chip(f"s{i}", vals[f"s{i}"].data).move_to([xs[i], 0.2, 0])
    for i in range(1, n + 1):
        chips[f"w{i}"] = chip(f"w{i}", vals[f"w{i}"].data).move_to([xs[i] - 1.15, -1.3, 0])
    steps = []
    kw = dict(buff=0.03, color=FWD, stroke_width=4, tip_length=0.14)
    for i in range(1, n + 1):
        main = Arrow(chips[f"s{i-1}"].get_right(), chips[f"s{i}"].get_left(), **kw)
        circ = Circle(radius=0.2, color=SECOND, stroke_width=3, fill_color=BLACK,
                      fill_opacity=1).move_to([xs[i] - 1.15, 0.2, 0])
        plus = Text("+", font_size=24, color=WHITE).move_to(circ)
        up = Arrow(chips[f"w{i}"].get_top(), circ.get_bottom(), **kw)
        steps.append((main, VGroup(circ, plus), up))
    return chips, steps


class FlatNarrator(CrossfadeNarrator):
    pass


class Scene03GraphForward(Scene):
    # ---------------------------------------------------------------- helpers
    def tag(self, text):
        return Tex(r"\textbf{" + text + "}", font_size=34, color=ACTIVE).to_corner(UL, buff=0.5)

    def pulse_question(self, text, pos, qpos, n=3):
        """Predict-then-reveal: question plus a pulsing question mark, held about 3 s."""
        q = Text(text, font_size=30, color=WHITE).move_to(pos)
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to(qpos)
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        return VGroup(q, qm)

    def flow(self, arrows, run_time=0.9):
        fls = [particle_flow(a, 1, color=FWD, n=2, run_time=run_time) for a in arrows]
        dots = VGroup(*[f.dots for f in fls])
        self.add(dots)
        self.play(*fls)
        self.remove(dots, *dots.submobjects, *[f.mobject for f in fls])
        self.remove(*[d for f in fls for d in f.dots.submobjects])

    def code_hud(self, text):
        c = code_panel(text, font_size=24)
        c.scale_to_fit_height(0.75)
        return c.move_to([-2.0, 3.3, 0])

    # --------------------------------------------------------------- the scene
    def construct(self):
        nar = self.nar = FlatNarrator(self, "S03")
        title_card(self, "Chapter 3", "How do we store a calculation as a graph?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        recap_line(self, "Next: how does each node learn how much it matters?", color=ACTIVE)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        va = graph_a()
        assert va["e"].data == -6.0 and va["d"].data == 4.0 and va["L"].data == -8.0
        nar.say("Example A: the lecture's own graph, built from four plain numbers.")
        act_banner(self, "Example A: the lecture's graph", hold=2.6)
        tag = self.tag("Example A:")
        self.play(FadeIn(tag), run_time=0.4)

        # --- the Value class, mirrored on a card
        panel = code_panel(CODE_VALUE, font_size=24)
        panel.scale_to_fit_width(7.8).move_to([-2.75, -0.1, 0])
        e = va["e"]
        rows = [
            ("data", f"data = {fmt(e.data)}", 4, LIGHT),
            ("grad", f"grad = {fmt(e.grad)}", 5, GRAD),
            ("_prev", "_prev = {" + ", ".join(sorted(ch.label for ch in e._prev)) + "}", 6, FWD),
            ("_op", f"_op = '{e._op}'", 7, FWD),
            ("label", f"label = '{e.label}'", 8, WHITE),
        ]
        card_box = RoundedRectangle(corner_radius=0.2, width=3.5, height=4.2, stroke_color=WHITE,
                                    stroke_width=3).move_to([5.0, -0.1, 0])
        card_title = Text("one Value: e", font_size=30, color=ACTIVE, weight=BOLD)
        card_title.move_to(card_box.get_top() + DOWN * 0.45)
        nar.say("A scalar is one single number, like 2.0 or minus 3.0.")
        c1 = callout("Scalar", "one single number, like 2.0", width=8).move_to([0, 2.75, 0])
        self.play(FadeIn(panel), FadeIn(c1), run_time=0.8)
        self.wait(2.4)
        nar.say("A Value wraps a scalar and remembers where it came from.")
        c2 = callout("Value", "a scalar that remembers its origin", width=8).move_to([0, 2.75, 0])
        self.play(FadeTransform(c1, c2), Create(card_box), FadeIn(card_title), run_time=0.8)
        self.wait(2.4)
        hl = SurroundingRectangle(panel.code_lines[3], color=ACTIVE, buff=0.05)
        self.play(Create(hl), run_time=0.5)
        captions = {
            "data": "data holds the number. grad will hold its slope, starting at zero.",
            "_prev": "_prev lists the children, and _op names the operation that made it.",
        }
        row_mobs = []
        for key, text, line, col in rows:
            if key in captions:
                nar.say(captions[key])
            row = Text(text, font_size=28, color=col)
            y = card_box.get_top()[1] - 1.15 - 0.55 * [r[0] for r in rows].index(key)
            row.move_to([card_box.get_center()[0], y, 0])
            row.align_to(card_box.get_left() + RIGHT * 0.4, LEFT)
            new_hl = SurroundingRectangle(panel.code_lines[line - 1], color=ACTIVE, buff=0.05)
            self.play(Transform(hl, new_hl), FadeIn(row, shift=LEFT * 0.3), run_time=0.8)
            self.wait(1.0 if key not in ("data", "_prev") else 1.6)
            row_mobs.append(row)
        self.wait(0.5)
        self.play(*[FadeOut(m) for m in (panel, hl, card_box, card_title, c2, *row_mobs)],
                  run_time=0.6)

        # --- leaves
        title = MathTex(r"L=(a\cdot b+c)\cdot f", font_size=44).move_to([3.7, 3.3, 0])
        nodes, ops, arrows = build_graph(va, POS_A)
        for k in ("e", "d", "L"):
            nodes[k].data_t.set_opacity(0)
        nar.say("Four leaf Values: a, b, c and f. Nothing has been computed yet.")
        self.play(FadeIn(title), FadeIn(nodes["a"]), FadeIn(nodes["b"]), run_time=0.8)
        self.wait(0.4)
        self.play(FadeIn(nodes["c"]), FadeIn(nodes["f"]), run_time=0.8)
        self.wait(1.2)
        nar.say("Before we compute: will L end up positive or negative?")
        q = self.pulse_question("Will L be positive or negative?", [1.2, 2.5, 0], [5.9, 2.5, 0])
        self.play(FadeOut(q), run_time=0.4)

        # --- the graph grows one operation at a time, out of the code lines
        steps = [
            ("e", "e = a * b", "First, e = a times b. The numbers flow forward along the arrows.",
             r"e=a\cdot b", rf"e={p(va['a'].data)}\cdot{p(va['b'].data)}", rf"e={fmt(va['e'].data)}"),
            ("d", "d = e + c", "Then d = e plus c. Each new node is born from its children.",
             r"d=e+c", rf"d={p(va['e'].data)}+{p(va['c'].data)}", rf"d={fmt(va['d'].data)}"),
            ("L", "L = d * f", "Finally L = d times f, which gives minus 8. The forward pass is done.",
             r"L=d\cdot f", rf"L={p(va['d'].data)}\cdot{p(va['f'].data)}", rf"L={fmt(va['L'].data)}"),
        ]
        hud = None
        for k, code, cap, sym, sub, res in steps:
            nar.say(cap)
            new_hud = self.code_hud(code)
            if hud is None:
                self.play(FadeIn(new_hud), run_time=0.5)
            else:
                self.play(FadeOut(hud), FadeIn(new_hud), run_time=0.5)
            hud = new_hud
            self.play(FadeIn(ops[k]), *[Create(a) for a in arrows[k]], run_time=0.8)
            self.play(FadeIn(nodes[k]), run_time=0.6)
            self.flow(arrows[k][:-1])
            self.flow(arrows[k][-1:])
            res_m = working_line(self, sym, sub, res, pos=[3.7, 2.1, 0], width=5.0,
                                 colors=(WHITE, WHITE, LIGHT))
            self.play(nodes[k].data_t.animate.set_opacity(1), FadeOut(res_m), run_time=0.6)
            self.play(Indicate(nodes[k], color=ACTIVE), run_time=0.8)
            self.wait(0.4)
        # the circles are only drawing helpers
        nar.say("The round circles are only drawing helpers. Only rectangles are Values.")
        c3 = callout("Drawing helper", "only the rectangles are Values", width=8).move_to([3.0, 2.4, 0])
        self.play(FadeOut(hud), FadeOut(title), FadeIn(c3), run_time=0.5)
        self.play(*[Indicate(ops[k], color=ACTIVE, scale_factor=1.3) for k in ops], run_time=1.2)
        self.wait(2.0)
        self.play(FadeOut(c3), run_time=0.4)

        # --- zoom on d: a child is just an input
        group = VGroup(*nodes.values(), *ops.values(), *[a for l in arrows.values() for a in l])
        group.save_state()
        nar.say("Zoom on d: its children are just the inputs it was computed from.")
        keep = [nodes["d"], nodes["e"], nodes["c"], ops["d"], *arrows["d"]]
        others = [m for m in group.submobjects if m not in keep]
        centre = nodes["d"].get_center()
        self.play(*[m.animate.set_opacity(0.0) for m in others], run_time=0.6)
        self.play(group.animate.scale(1.6, about_point=centre), run_time=1.2)
        d_prev = Text("d._prev = {" + ", ".join(sorted(ch.label for ch in va["d"]._prev)) + "}",
                      font_size=30, color=ACTIVE).move_to(nodes["d"].get_bottom() + DOWN * 0.75)
        c4 = callout("Child", "an input a node was computed from", width=8).move_to([2.6, 2.6, 0])
        self.play(FadeIn(d_prev), FadeIn(c4), Indicate(nodes["e"], color=ACTIVE),
                  Indicate(nodes["c"], color=ACTIVE), run_time=1.2)
        self.wait(3.0)
        nar.say("That is a computation graph: Values joined by operations.")
        c5 = callout("Computation graph", "Values joined by operations", width=8).move_to([2.6, 2.6, 0])
        self.play(FadeOut(d_prev), FadeTransform(c4, c5), Restore(group), run_time=1.2)
        self.wait(3.0)
        self.play(FadeOut(c5), run_time=0.4)
        self.graph_a = (group, tag)
        self.wait(0.5)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        group, tag = self.graph_a
        va = graph_a()
        vb = graph_b()
        assert vb["s"].data == 2.0 and vb["t"].data == 6.0 and vb["L2"].data == 12.0
        nar.say("Example B: what if we build a different shape from the same pieces?")
        self.play(FadeOut(group), FadeOut(tag), *[FadeOut(m) for m in self.mobjects
                                                  if isinstance(m, MathTex)], run_time=0.6)
        act_banner(self, "Example B: what if?", hold=2.6)
        tag_b = self.tag("Example B:")
        title_a = MathTex(r"L=(a\cdot b+c)\cdot f", font_size=44).move_to([3.7, 3.3, 0])
        self.play(FadeIn(group), FadeIn(tag_b), FadeIn(title_a), run_time=0.8)
        # recover the mobjects of graph A in a fixed order from the group
        n_a, o_a, ar_a = self._split(group, va)
        self.wait(1.0)

        nar.say("Think first: with (a + b) times (c + f), how many plus nodes appear?")
        q = self.pulse_question("How many plus nodes in (a + b)(c + f)?", [0.9, 2.5, 0], [5.9, 2.5, 0])
        self.play(FadeOut(q), run_time=0.4)

        nodes_b, ops_b, arrows_b = build_graph(vb, POS_B, scale=0.8)
        title_b = MathTex(r"L_2=(a+b)\cdot(c+f)", font_size=44).move_to([3.7, 3.3, 0])
        hud = self.code_hud("L2 = (a + b) * (c + f)")
        nar.say("Same two operations, new shape: two plus nodes feed one times node.")
        anims = [Transform(title_a, title_b), FadeIn(hud)]
        for xa, xb in PAIRS:
            anims.append(Transform(n_a[xa], nodes_b[xb]))
            if xa in o_a:
                anims.append(Transform(o_a[xa], ops_b[xb]))
                for ma, mb in zip(ar_a[xa], arrows_b[xb]):
                    anims.append(Transform(ma, mb))
        self.play(*anims, run_time=3.5)
        self.wait(1.0)
        nar.say("Now the numbers: 3 minus 1 is 2, 2 plus 4 is 6, and 2 times 6 is 12.")
        w1 = working_line(self, r"s=a+b,\; t=c+f", rf"s={p(3.0)}+{p(-1.0)},\; t={p(2.0)}+{p(4.0)}",
                          rf"s={fmt(vb['s'].data)},\; t={fmt(vb['t'].data)}", pos=[4.9, 1.5, 0],
                          width=3.9, hold=1.6, colors=(WHITE, WHITE, LIGHT))
        self.play(FadeOut(w1), run_time=0.4)
        w2 = working_line(self, r"L_2=s\cdot t", rf"L_2={p(vb['s'].data)}\cdot{p(vb['t'].data)}",
                          rf"L_2={fmt(vb['L2'].data)}", pos=[4.9, 1.5, 0], width=3.9, hold=1.6,
                          colors=(WHITE, WHITE, LIGHT))
        self.play(Indicate(n_a["L"], color=ACTIVE), run_time=0.9)
        nar.say("Same pieces, different graph: the shape comes from the expression.")
        cmp_a = Text(f"A: {count_ops(va, '+')} plus, {count_ops(va, '*')} times", font_size=28,
                     color=WHITE).move_to([4.9, -0.2, 0])
        cmp_b = Text(f"B: {count_ops(vb, '+')} plus, {count_ops(vb, '*')} times", font_size=28,
                     color=ACTIVE).move_to([4.9, -0.85, 0])
        self.play(FadeOut(w2), FadeIn(cmp_a), run_time=0.6)
        self.play(FadeIn(cmp_b), Indicate(cmp_b, color=ACTIVE), run_time=1.0)
        self.wait(3.0)
        self.graph_b = (n_a, o_a, ar_a, title_a, hud, cmp_a, cmp_b, tag_b)

    def _split(self, group, va):
        """Rebuild the name -> mobject maps for graph A from the saved group order."""
        subs = list(group.submobjects)
        names = list(va.keys())
        nodes = dict(zip(names, subs[:len(names)]))
        rest = subs[len(names):]
        opnames = [k for k in names if va[k]._op]
        ops = dict(zip(opnames, rest[:len(opnames)]))
        arr, i = {}, len(opnames)
        for k in opnames:
            n = len(va[k]._prev) + 1
            arr[k] = rest[i:i + n]
            i += n
        return nodes, ops, arr

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        n_a, o_a, ar_a, title_a, hud, cmp_a, cmp_b, tag_b = self.graph_b
        nar.say("Expert corner: the graph is built while the code runs.")
        everything = VGroup(*n_a.values(), *o_a.values(), *[a for l in ar_a.values() for a in l],
                            title_a, hud, cmp_a, cmp_b, tag_b)
        self.play(FadeOut(everything), run_time=0.6)
        act_banner(self, "Expert corner: define by run", hold=2.6)
        tag = self.tag("Expert corner:")
        self.play(FadeIn(tag), run_time=0.4)

        code = code_panel("ws = [1.0, 2.0, 3.0, 4.0, 5.0]\ns = Value(0.0)\n"
                          "for w in ws[:n]:\n    s = s + Value(w)", font_size=24)
        code.scale_to_fit_height(1.6).move_to([-3.6, 2.15, 0])
        nlab = Text("n = 3", font_size=34, color=ACTIVE).move_to([0.3, 2.15, 0])
        counter_t = Text("Values in memory:", font_size=28, color=WHITE).move_to([4.0, 2.15, 0])
        counter = Integer(1, font_size=36, color=LIGHT).next_to(counter_t, RIGHT, buff=0.2)

        vals3, s3 = run_loop(3)
        assert len(s3.topo()) == 7
        chips3, steps3 = build_chain(vals3, 3)
        nar.say("This loop adds one number per turn. Watch the graph grow with it.")
        self.play(FadeIn(code), FadeIn(nlab), FadeIn(counter_t), FadeIn(counter), run_time=0.8)
        self.play(FadeIn(chips3["s0"]), run_time=0.6)
        count = 1
        for i, (main, circ, up) in enumerate(steps3, 1):
            self.play(Indicate(code.code_lines[3], color=ACTIVE), FadeIn(chips3[f"w{i}"]), run_time=0.7)
            self.play(FadeIn(circ), Create(main), Create(up), run_time=0.6)
            self.play(FadeIn(chips3[f"s{i}"]), ChangeDecimalToValue(counter, count + 2), run_time=0.7)
            count += 2
            self.wait(0.3)
        assert count == 7
        nar.say("With three turns we get seven Values: one start, three inputs, three sums.")
        self.play(Indicate(counter, color=ACTIVE), run_time=1.0)
        self.wait(2.0)

        nar.say("Predict: change three to five. How many Values will the graph hold?")
        q = self.pulse_question("How many Values for n = 5?", [-1.0, -2.2, 0], [2.2, -2.2, 0])
        self.play(FadeOut(q), run_time=0.4)
        vals5, s5 = run_loop(5)
        n5 = len(s5.topo())
        assert n5 == 11
        chips5, steps5 = build_chain(vals5, 5)
        nlab5 = Text("n = 5", font_size=34, color=ACTIVE).move_to(nlab)
        old3 = VGroup(*chips3.values(), *[m for st in steps3 for m in st])
        new5 = VGroup(*chips5.values(), *[m for st in steps5 for m in st])
        self.play(ReplacementTransform(nlab, nlab5), FadeOut(old3), run_time=0.8)
        nar.say(f"{n5} Values! Same code, a different graph: the data decides the shape.")
        self.play(LaggedStart(*[FadeIn(m) for m in new5], lag_ratio=0.06),
                  ChangeDecimalToValue(counter, n5), run_time=3.0)
        self.play(Indicate(counter, color=ACTIVE), run_time=1.0)
        self.wait(1.5)

        nar.say("Every node keeps its children in _prev, so backprop can walk back.")
        prev_note = Text("each node keeps _prev: a link to its children", font_size=28,
                         color=FWD).move_to([0.5, -2.1, 0])
        back = [Arrow(chips5[f"s{i}"].get_bottom() + DOWN * 0.0, chips5[f"s{i-1}"].get_bottom(),
                      path_arc=0.9, color=GRAD, stroke_width=3, tip_length=0.14, buff=0.05)
                for i in range(1, 6)]
        self.play(*[Create(a) for a in back], run_time=1.5)
        self.play(FadeIn(prev_note), run_time=0.5)
        self.wait(2.2)
        nar.say("That is why training uses so much memory: nothing is freed early.")
        self.play(Indicate(counter, color=GRAD, scale_factor=1.5), run_time=1.2)
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in (new5, *back, prev_note, code, nlab5, counter_t, counter)],
                  run_time=0.8)

        # --- rebinding
        a, b, c0 = Value(2.0, label="a"), Value(-3.0, label="b"), Value(10.0, label="c")
        e = a * b
        d = e + c0
        d.label = "d"
        c = c0
        c = c + Value(1.0)
        assert c is not c0 and c0 in d._prev and c0 in c._prev and c.data == 11.0
        one = next(ch for ch in c._prev if ch is not c0)
        old_c = make_value_node("c (old)", c0.data, c0.grad).scale(0.75).move_to([-4.3, 1.3, 0])
        d_node = make_value_node("d", d.data, d.grad).scale(0.75).move_to([4.3, 1.3, 0])
        one_n = make_value_node("1.0", one.data, one.grad).scale(0.75).move_to([-4.3, -1.4, 0])
        new_c = make_value_node("c (new)", c.data, c.grad).scale(0.75).move_to([0.8, -0.6, 0])
        circ = op_circle("+").move_to([-1.9, -0.6, 0])
        kw = dict(buff=0.05, color=FWD, stroke_width=4, tip_length=0.16)
        a_old_d = Arrow(old_c.get_right(), d_node.get_left(), **kw)
        a_old_n = Arrow(old_c.get_right(), circ.get_top(), **kw)
        a_one_n = Arrow(one_n.get_right(), circ.get_left(), **kw)
        a_n_new = Arrow(circ.get_right(), new_c.get_left(), **kw)
        note = Text("d = e + c still uses the old c", font_size=28, color=SECOND).move_to([0.2, 1.85, 0])
        line = self.code_hud("c = c + Value(1.0)").move_to([0.3, 3.3, 0])

        def make_tag(node):
            lab = Text("name: c", font_size=28, color=ACTIVE, weight=BOLD).move_to(node.get_top() + UP * 0.85)
            ar = Arrow(lab.get_bottom(), node.get_top(), buff=0.05, color=ACTIVE, stroke_width=4,
                       tip_length=0.16)
            return VGroup(lab, ar)

        nar.say("Rebinding: c = c plus 1 does not change the old c node at all.")
        name_tag = make_tag(old_c)
        self.play(FadeIn(old_c), FadeIn(d_node), Create(a_old_d), FadeIn(line), run_time=0.9)
        self.play(FadeIn(name_tag), FadeIn(note), run_time=0.7)
        self.wait(2.0)
        nar.say("It builds a brand new node and moves the name c onto it.")
        self.play(FadeIn(one_n), FadeIn(circ), Create(a_old_n), Create(a_one_n), run_time=1.0)
        self.play(FadeIn(new_c), Create(a_n_new), run_time=0.8)
        self.play(Transform(name_tag, make_tag(new_c)), run_time=1.4)
        self.wait(1.0)
        nar.say("The old node stays in the graph, and d still points to it.")
        self.play(Indicate(old_c, color=ACTIVE), Indicate(a_old_d, color=ACTIVE), run_time=1.5)
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in (old_c, d_node, one_n, new_c, circ, a_old_d, a_old_n,
                                         a_one_n, a_n_new, note, line, name_tag, tag)],
                  run_time=0.6)
