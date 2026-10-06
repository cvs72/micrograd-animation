import math
from functools import lru_cache

import numpy as np
from manim import *

from micrograd_animation.anim import (
    ACTIVE, BWD, DATA, FWD, GRAD, SECOND, CrossfadeNarrator, act_banner, callout, fmt,
    recap_line, title_card,
)
from micrograd_animation.engine import Value
from micrograd_animation.nn import MLP

# ---- the neuron of this chapter: first two inputs of the S11 dataset, one tanh neuron, bias fixed
XS = [[2.0, 3.0], [3.0, -1.0], [0.5, 1.0], [1.0, 1.0]]
YS = [1.0, -1.0, -1.0, 1.0]
BIAS = 0.5
LIM = 3.0
LR_SMALL, LR_BIG, STEPS = 0.05, 1.0, 25
START = (-2.5, 2.0)
STARTS = [(-2.5, 2.0), (3.0, -3.0), (0.0, 0.0)]
PLATEAU = (-2.5, -2.5)


@lru_cache(maxsize=None)
def loss_grad(w1, w2):
    """Loss and gradient of the neuron at (w1, w2), straight from the Value engine."""
    a, b = Value(w1), Value(w2)
    loss = sum(((a * x[0] + b * x[1] + BIAS).tanh() - y) ** 2 for x, y in zip(XS, YS))
    loss.backward()
    return loss.data, a.grad, b.grad


def outputs(w1, w2):
    return [(Value(w1) * x[0] + Value(w2) * x[1] + BIAS).tanh().data for x in XS]


def descend(w1, w2, lr, n=STEPS):
    """n gradient-descent steps; returns n+1 points (w1, w2, loss)."""
    pts = []
    for _ in range(n + 1):
        L, g1, g2 = loss_grad(w1, w2)
        pts.append((w1, w2, L))
        w1, w2 = w1 - lr * g1, w2 - lr * g2
    return pts


def clamp(v):
    return max(-LIM, min(LIM, v))


def on_map(pts):
    """Display points: clamp to the plotted square so nothing leaves the axes."""
    return [(clamp(a), clamp(b), loss_grad(round(clamp(a), 6), round(clamp(b), 6))[0]) for a, b, _ in pts]


def contour_segments(grid, ws, level):
    """Marching squares on the engine grid: list of ((w1, w2), (w1, w2)) segments."""
    segs = []
    n = len(ws)
    for i in range(n - 1):
        for j in range(n - 1):
            corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            pts = []
            for a, b in zip(corners, corners[1:] + corners[:1]):
                va, vb = grid[a], grid[b]
                if (va - level) * (vb - level) < 0:
                    t = (level - va) / (vb - va)
                    pts.append((ws[a[0]] + (ws[b[0]] - ws[a[0]]) * t,
                                ws[a[1]] + (ws[b[1]] - ws[a[1]]) * t))
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
            elif len(pts) == 4:
                segs += [(pts[0], pts[1]), (pts[2], pts[3])]
    return segs


class FixedNarrator(CrossfadeNarrator):
    """Captions that stay flat on screen even while the 3D camera moves."""

    def _make(self, text):
        cap = super()._make(text)
        self.scene.add_fixed_in_frame_mobjects(cap)
        return cap


class Scene12LossSurface(ThreeDScene):
    def fix(self, *mobs):
        self.add_fixed_in_frame_mobjects(*mobs)
        return mobs[0] if len(mobs) == 1 else mobs

    def pulse_question(self, text, n=3):
        q = Text(text, font_size=30, color=WHITE).move_to([-3.6, 3.25, 0])
        qm = Text("?", font_size=72, color=ACTIVE, weight=BOLD).move_to([q.get_right()[0] + 0.6, 3.2, 0])
        self.fix(q, qm)
        self.play(FadeIn(q), FadeIn(qm), run_time=0.5)
        for _ in range(n):
            self.play(Indicate(qm, scale_factor=1.4, color=ACTIVE), run_time=1.0)
        return VGroup(q, qm)

    def wipe(self, keep=(), run_time=0.8):
        keep = set(id(k) for k in keep)
        stage = [m for m in self.mobjects if m not in self.foreground_mobjects and id(m) not in keep]
        if stage:
            self.play(*[FadeOut(m) for m in stage], run_time=run_time)

    def working(self, stages, pos, width=8.0, hold=2.0):
        """Fixed-in-frame MathTex chain: symbolic -> real numbers -> result."""
        ms = []
        for s, c in stages:
            m = MathTex(s, font_size=40, color=c)
            if m.width > width:
                m.scale_to_fit_width(width)
            m.move_to(pos)
            ms.append(m)
        self.fix(*ms)
        self.play(FadeIn(ms[0]), run_time=0.6)
        self.wait(1.0)
        for a, b in zip(ms, ms[1:]):
            self.play(TransformMatchingTex(a, b), run_time=1.0)
            self.wait(hold)
        return ms[-1]

    def roll(self, pts, color, run_time, ball_color=ORANGE, counter=None, keep_ball=False):
        """Ball rolls along pts (display points) leaving a path; returns (ball, trail)."""
        P = self.P
        n = len(pts) - 1
        tr = ValueTracker(0)

        def at(t):
            i = min(int(t), n - 1)
            f = t - i
            a, b = pts[i], pts[i + 1]
            return [a[k] + (b[k] - a[k]) * f for k in range(3)]

        def pos(t):
            w1, w2, z = at(t)
            return P(w1, w2, z) + OUT * 0.12

        ball = Dot3D(pos(0), radius=0.14, color=ball_color)
        trail = VMobject(color=color, stroke_width=5)
        trail.set_points_as_corners([pos(0), pos(0) + OUT * 0.01])

        def upd_trail(m):
            t = tr.get_value()
            m.set_points_as_corners([pos(j) for j in range(int(t) + 1)] + [pos(t)])

        trail.add_updater(upd_trail)
        ball.add_updater(lambda m: m.move_to(pos(tr.get_value())))
        if counter is not None:
            def upd_counter(m):
                m.set_value(at(tr.get_value())[2])
                self.add_fixed_in_frame_mobjects(m)  # new digits must stay flat too
            counter.add_updater(upd_counter)
        self.add(trail, ball)
        self.play(tr.animate.set_value(n), run_time=run_time, rate_func=linear)
        trail.clear_updaters()
        ball.clear_updaters()
        if counter is not None:
            counter.clear_updaters()
        if not keep_ball:
            self.remove(ball)
        return ball, trail

    # ------------------------------------------------------------------ scene
    def construct(self):
        nar = self.nar = FixedNarrator(self, "S12")
        self.build_world()
        title_card(self, "Chapter 12", "Can we see what gradient descent is doing?")
        self.act_a(nar)
        self.act_b(nar)
        self.act_c(nar)
        nar.finish()
        recap_line(self, "Next: the full story, from slope to training.", color=ACTIVE)

    def build_world(self):
        n = 25
        self.ws = np.linspace(-LIM, LIM, n)
        self.grid = np.array([[loss_grad(round(float(a), 6), round(float(b), 6))[0] for b in self.ws]
                              for a in self.ws])
        self.zmin, self.zmax = float(self.grid.min()), float(self.grid.max())
        self.zmax_ax = math.ceil(self.zmax)
        # every path used later
        self.small = {s: descend(*s, LR_SMALL) for s in STARTS}
        self.big = {s: descend(*s, LR_BIG) for s in STARTS}
        a = self.small[START]
        b = self.big[START]
        assert a[-1][2] < a[0][2], "small-step path must end lower than it starts"
        assert b[-1][2] >= a[-1][2], "big-step path must end no better than the small-step path"

    def make_axes(self):
        axes = ThreeDAxes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[0, self.zmax_ax, 4],
                          x_length=5, y_length=5, z_length=3.2)
        self.axes = axes
        self.P = axes.c2p
        labels = [MathTex("w_1", color=WHITE, font_size=44).move_to(self.P(3.9, 0, 0)),
                  MathTex("w_2", color=WHITE, font_size=44).move_to(self.P(0, 3.9, 0)),
                  MathTex("L", color=YELLOW, font_size=44).move_to(self.P(0, 0, self.zmax_ax + 1.6))]
        self.axis_labels = labels
        return axes, labels

    def make_surface(self):
        P = self.P
        s = Surface(lambda u, v: P(u, v, loss_grad(round(float(u), 6), round(float(v), 6))[0]),
                    u_range=[-LIM, LIM], v_range=[-LIM, LIM], resolution=(24, 24),
                    fill_opacity=0.85, stroke_width=0.4, stroke_color=GREY_C)
        mid = (self.zmin + self.zmax) / 2
        s.set_fill_by_value(axes=self.axes, colorscale=[(BLUE_E, self.zmin), (TEAL, mid),
                                                         (YELLOW, self.zmax)], axis=2)
        self.surface = s
        return s

    def make_contours(self):
        P = self.P
        levels = list(np.linspace(self.zmin + 0.3, self.zmax - 0.3, 8))
        groups = VGroup()
        self.contour_segs = {}
        for k, lv in enumerate(levels):
            segs = contour_segments(self.grid, self.ws, lv)
            self.contour_segs[lv] = segs
            m = VMobject(color=interpolate_color(BLUE_C, YELLOW, k / (len(levels) - 1)), stroke_width=3)
            for p0, p1 in segs:
                m.start_new_path(P(*p0, 0))
                m.add_line_to(P(*p1, 0))
            groups.add(m)
        self.contours = groups
        return groups

    def floor(self, w1, w2):
        return self.P(w1, w2, 0)

    # ------------------------------------------------------------------- ACT A
    def act_a(self, nar):
        P = self.P if hasattr(self, "P") else None
        nar.say("Example A: one tanh neuron with two weights, w1 and w2, and bias 0.5.")
        banner = act_banner(self, "Example A: a ball on the loss surface", keep=True)
        self.fix(banner)
        self.wait(2.6)
        self.play(FadeOut(banner), run_time=0.5)

        axes, labels = self.make_axes()
        P = self.P
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, frame_center=[0, 0, 0.9])
        self.play(Create(axes), *[FadeIn(l) for l in labels])
        self.add_fixed_orientation_mobjects(*labels)
        nar.say("Every pair (w1, w2) gives one loss: the height above that spot.")
        formula = MathTex(r"L(w_1,w_2)=\sum_{i=1}^{4}\left(\tanh(w_1x_{1i}+w_2x_{2i}+b)-y_i\right)^2",
                          font_size=40, color=WHITE)
        formula.scale_to_fit_width(9.0).move_to([0, 3.3, 0])
        self.fix(formula)
        self.play(FadeIn(formula))
        self.wait(2.0)

        w1, w2 = START
        outs = outputs(w1, w2)
        L0, g1, g2 = loss_grad(w1, w2)
        assert abs(L0 - sum((o - y) ** 2 for o, y in zip(outs, YS))) < 1e-9
        terms = "+".join(rf"({fmt(o)}-({fmt(y)}))^2" for o, y in zip(outs, YS))
        nar.say("At the start (-2.5, 2) the engine adds four squared errors.")
        self.play(formula.animate.move_to([0, 3.3, 0]).scale(0.75))
        res = self.working([
            (r"L=\sum_i(o_i-y_i)^2", WHITE),
            (rf"L={terms}", DATA),
            (rf"L={terms}={fmt(L0)}", GRAD)], [0, 2.3, 0], width=12.0, hold=2.5)
        self.play(FadeOut(res))
        self.play(FadeOut(formula))

        surface = self.make_surface()
        nar.say("Doing that for every grid point builds a landscape: low is good.")
        self.move_camera(phi=65 * DEGREES, theta=-55 * DEGREES, zoom=0.8, run_time=2.5,
                         added_anims=[FadeIn(surface)])
        self.begin_ambient_camera_rotation(rate=0.07)
        note = callout("Analogy", "loss over two weights; real nets have millions", width=7.5)
        note.move_to([-3.4, 3.1, 0])
        self.fix(note)
        self.play(FadeIn(note))
        self.wait(3.2)
        self.play(FadeOut(note))

        contours = self.make_contours()
        nar.say("Contour lines on the floor join points with equal loss, like a map.")
        self.play(LaggedStart(*[Create(c) for c in contours], lag_ratio=0.2), run_time=3.0)

        ball = Dot3D(P(w1, w2, L0) + OUT * 0.12, radius=0.14, color=ORANGE)
        drop = DashedLine(P(w1, w2, L0), P(w1, w2, 0), color=YELLOW, stroke_width=3)
        nar.say("Our ball starts at (-2.5, 2). Which way should it roll?")
        self.play(FadeIn(ball), Create(drop))
        q = self.pulse_question("Which way is downhill?")
        self.play(FadeOut(q))

        k = 0.25
        n2 = g1 * g1 + g2 * g2
        up = Arrow3D(P(w1, w2, L0) + OUT * 0.12, P(w1 + k * g1, w2 + k * g2, L0 + k * n2) + OUT * 0.12,
                     color=BWD, thickness=0.02)
        down = Arrow3D(P(w1, w2, L0) + OUT * 0.12, P(w1 - k * g1, w2 - k * g2, L0 - k * n2) + OUT * 0.12,
                       color=FWD, thickness=0.02)
        nar.say("The gradient (orange) points uphill; we step the opposite way (teal).")
        self.play(Create(up), run_time=1.5)
        self.wait(1.0)
        self.play(Create(down), run_time=1.5)
        gl = MathTex(rf"\nabla L=({fmt(g1)},\ {fmt(g2)})", font_size=44, color=GRAD).move_to([0, 3.3, 0])
        self.fix(gl)
        self.play(FadeIn(gl))
        self.wait(2.5)
        self.play(FadeOut(gl))

        nar.say("One update: w1 minus learning rate times its slope.")
        n1 = w1 - LR_SMALL * g1
        r = self.working([
            (r"w_1\leftarrow w_1-\eta\,\frac{\partial L}{\partial w_1}", WHITE),
            (rf"w_1\leftarrow({fmt(w1)})-{fmt(LR_SMALL)}\cdot({fmt(g1)})", DATA),
            (rf"w_1\leftarrow({fmt(w1)})-{fmt(LR_SMALL)}\cdot({fmt(g1)})={fmt(n1)}", GRAD)],
            [0, 3.3, 0], width=9.0, hold=2.0)
        self.play(FadeOut(r), FadeOut(up), FadeOut(down))

        small = self.small[START]
        disp = on_map(small)
        assert abs(small[1][0] - n1) < 1e-9
        counter = DecimalNumber(L0, num_decimal_places=4, font_size=44, color=YELLOW)
        lab = MathTex(r"L=", font_size=44, color=WHITE)
        grp = VGroup(lab, counter).arrange(RIGHT, buff=0.2).move_to([4.6, 3.3, 0])
        counter.next_to(lab, RIGHT, buff=0.2)
        self.fix(grp)
        self.play(FadeIn(grp))
        nar.say("Now 25 steps: each one re-asks the engine for the slope, then moves.")
        self.remove(ball)
        ball, trail = self.roll(disp, ACTIVE, 7.0, counter=counter, keep_ball=True)
        self.wait(1.0)

        nar.say("Seen from above, the path crosses contours toward the lower rings.")
        floor_path = VMobject(color=ACTIVE, stroke_width=4)
        floor_path.set_points_as_corners([P(a, b, 0) + OUT * 0.02 for a, b, _ in disp])
        self.play(Create(floor_path), run_time=2.0)
        end = MathTex(rf"L:\ {fmt(small[0][2])}\ \to\ {fmt(small[-1][2])}", font_size=44, color=YELLOW)
        end.move_to([-3.4, 3.3, 0])
        self.fix(end)
        self.play(FadeIn(end))
        self.wait(3.0)
        self.keep_a = [ball, trail, floor_path]
        self.a_extras = VGroup(end, grp)

    # ------------------------------------------------------------------- ACT B
    def act_b(self, nar):
        P = self.P
        nar.say("Example B: what if we start elsewhere, or take much bigger steps?")
        self.play(FadeOut(self.a_extras), *[FadeOut(m) for m in self.keep_a], run_time=0.8)
        banner = act_banner(self, "Example B: other starts, other steps", keep=True)
        self.fix(banner)
        self.wait(2.6)
        self.play(FadeOut(banner), run_time=0.5)

        cols = [-0.2, 1.7, 3.5]
        header = VGroup(Text("start", font_size=24, color=SECOND).move_to([cols[0], 0, 0]),
                        Text("lr 0.05", font_size=24, color=FWD).move_to([cols[1], 0, 0]),
                        Text("lr 1.0", font_size=24, color=RED).move_to([cols[2], 0, 0]))
        rows = []
        for i, s in enumerate(STARTS):
            y = -0.55 * (i + 1)
            cells = VGroup(
                Text(f"({fmt(s[0])}, {fmt(s[1])})", font_size=24, color=WHITE).move_to([cols[0], y, 0]),
                Text(fmt(self.small[s][-1][2]), font_size=24, color=FWD).move_to([cols[1], y, 0]),
                Text(fmt(self.big[s][-1][2]), font_size=24, color=RED).move_to([cols[2], y, 0]))
            rows.append(cells)
        table = VGroup(header, *rows)
        box = SurroundingRectangle(table, color=GREY_B, buff=0.25, fill_color=BLACK, fill_opacity=0.85)
        table_all = VGroup(box, table).move_to([4.3, 2.1, 0])
        label = Text("final loss after 25 steps", font_size=24, color=SECOND).next_to(table_all, DOWN, buff=0.1)
        self.fix(table_all, label)
        self.play(FadeIn(table_all), FadeIn(label))

        nar.say("Three starting points, each tried with a small and a huge step.")
        colors = [YELLOW_D, PURPLE_B, GREEN_B]
        marks = []
        for s, c in zip(STARTS, colors):
            L = loss_grad(*s)[0]
            d = Dot3D(P(s[0], s[1], L) + OUT * 0.12, radius=0.14, color=c)
            marks.append(d)
        self.play(*[FadeIn(m) for m in marks])
        self.wait(1.5)
        for m in marks:
            self.remove(m)

        q = None
        for idx, s in enumerate(STARTS):
            small = on_map(self.small[s])
            big = on_map(self.big[s])
            if idx == 0:
                nar.say("Small steps: the ball slides down and settles in the valley.")
            self.roll(small, FWD, 3.0)
            self.play(FadeIn(rows[idx][0]), FadeIn(rows[idx][1]))
            if idx == 0:
                nar.say("Predict: will a step twenty times bigger get there sooner?")
                q = self.pulse_question("Will a 20x bigger step win?")
            self.roll(big, RED, 3.0)
            self.play(FadeIn(rows[idx][2]))
            if idx == 0:
                a, b = self.small[s][-1][2], self.big[s][-1][2]
                ans = Text(f"No: {fmt(b)} against {fmt(a)}", font_size=30, color=WHITE).move_to([-3.6, 3.25, 0])
                self.fix(ans)
                self.play(FadeOut(q), FadeIn(ans))
                nar.say("No: it overshoots the valley and lands higher, worse than before.")
                self.wait(3.0)
                self.play(FadeOut(ans))
            else:
                self.wait(1.0)
        nar.say("Huge steps fly off the map; the small ones always finish lower.")
        self.wait(3.0)
        self.b_extras = VGroup(table_all, label)
        self.table_all = table_all

    # ------------------------------------------------------------------- ACT C
    def act_c(self, nar):
        P = self.P
        nar.say("Expert corner: the gradient is perpendicular to the contour lines.")
        self.stop_ambient_camera_rotation()
        keep = [self.axes, self.surface, self.contours] + list(self.contours) + list(self.axis_labels)
        self.wipe(keep)
        banner = act_banner(self, "Expert corner: gradients and plateaus", keep=True)
        self.fix(banner)
        self.wait(2.6)
        self.play(FadeOut(banner), run_time=0.5)

        # top view: the contour map with gradient arrows
        self.move_camera(phi=0, theta=-90 * DEGREES, zoom=1.5, run_time=2.0,
                         added_anims=[self.surface.animate.set_opacity(0.0)])
        self.remove(self.surface)
        arrows = VGroup()
        angles = []
        lv_list = list(self.contour_segs)
        for lv in (lv_list[1], lv_list[3], lv_list[5]):
            segs = self.contour_segs[lv]
            for p0, p1 in segs[:: max(1, len(segs) // 4)][:4]:
                m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                _, g1, g2 = loss_grad(round(m[0], 6), round(m[1], 6))
                gn = math.hypot(g1, g2)
                if gn < 1e-6:
                    continue
                t = (p1[0] - p0[0], p1[1] - p0[1])
                tn = math.hypot(*t)
                cosang = abs(t[0] * g1 + t[1] * g2) / (tn * gn)
                a_deg = math.degrees(math.acos(min(1.0, cosang)))
                if a_deg < 80:  # coarse grid cell: skip this segment
                    continue
                angles.append(a_deg)
                u = (g1 / gn * 0.45, g2 / gn * 0.45)
                arrows.add(Arrow(P(m[0], m[1], 0) + OUT * 0.05, P(m[0] + u[0], m[1] + u[1], 0) + OUT * 0.05,
                                 buff=0, color=BWD, stroke_width=5, max_tip_length_to_length_ratio=0.4))
        assert len(angles) >= 6, f"too few well-resolved contour segments: {len(angles)}"
        nar.say("Gradient arrows on the map cross every ring at right angles.")
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.15), run_time=3.0)
        self.wait(2.0)

        lv = lv_list[3]
        segs = self.contour_segs[lv]
        best = None
        for p0, p1 in segs[len(segs) // 2:] + segs[:len(segs) // 2]:
            m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            _, g1, g2 = loss_grad(round(m[0], 6), round(m[1], 6))
            t = (p1[0] - p0[0], p1[1] - p0[1])
            if math.hypot(g1, g2) < 1e-6 or math.hypot(*t) < 1e-6:
                continue
            ang = math.degrees(math.acos(min(1.0, abs(t[0] * g1 + t[1] * g2) / (math.hypot(*t) * math.hypot(g1, g2)))))
            if ang > 85:
                best = (p0, p1, m, g1, g2, t, ang)
                break
        assert best is not None
        p0, p1, m, g1, g2, t, ang = best
        seg = Line(P(p0[0], p0[1], 0) + OUT * 0.08, P(p1[0], p1[1], 0) + OUT * 0.08, color=YELLOW, stroke_width=8)
        nar.say("Check one ring: slope and contour meet at about 90 degrees.")
        self.play(Create(seg))
        r = self.working([
            (r"\cos\theta=\frac{|\nabla L\cdot t|}{|\nabla L|\,|t|}", WHITE),
            (rf"\theta=\arccos\frac{{|{fmt(g1)}\cdot{fmt(t[0])}+({fmt(g2)})\cdot{fmt(t[1])}|}}{{|\nabla L|\,|t|}}", DATA),
            (rf"\theta={ang:.1f}^\circ", GRAD)], [-2.6, 3.0, 0], width=8.0, hold=2.0)
        self.play(FadeOut(r), FadeOut(seg), FadeOut(arrows))

        # plateau: back to 3D
        self.add(self.surface)
        self.surface.set_opacity(0.0)
        self.move_camera(phi=65 * DEGREES, theta=-55 * DEGREES, zoom=0.8, run_time=2.0,
                         added_anims=[self.surface.animate.set_opacity(0.85)])
        self.begin_ambient_camera_rotation(rate=0.07)
        s0 = PLATEAU
        L0, g1, g2 = loss_grad(*s0)
        pts = descend(*s0, LR_SMALL)
        moved = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
        assert moved < 0.05, f"plateau start moved {moved}"
        nar.say("But in a saturated corner the surface is flat: slope almost zero.")
        flat = MathTex(rf"|\nabla L|={math.hypot(g1, g2):.4f}", font_size=44, color=GRAD).move_to([-3.2, 3.3, 0])
        counter = DecimalNumber(L0, num_decimal_places=4, font_size=44, color=YELLOW)
        lab = MathTex(r"L=", font_size=44, color=WHITE)
        grp = VGroup(lab, counter).arrange(RIGHT, buff=0.2).move_to([4.6, 3.3, 0])
        counter.next_to(lab, RIGHT, buff=0.2)
        self.fix(flat, grp)
        self.play(FadeIn(flat), FadeIn(grp))
        self.wait(1.5)
        ball, trail = self.roll(on_map(pts), ACTIVE, 5.0, counter=counter, keep_ball=True)
        nar.say("Twenty-five steps and the ball has hardly moved: the plateau traps it.")
        moved_t = MathTex(rf"\text{{moved}}\ {moved:.4f}", font_size=44, color=YELLOW).move_to([0, 2.5, 0])
        self.fix(moved_t)
        self.play(FadeIn(moved_t))
        self.wait(3.5)
        self.play(FadeOut(flat), FadeOut(grp), FadeOut(moved_t))

        # real networks: 41 gradients
        nar.say("Real networks have millions of weights: no surface to draw.")
        self.stop_ambient_camera_rotation()
        self.wipe([])
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, zoom=1, frame_center=[0, 0, 0])
        xs3 = [[2.0, 3.0, -1.0], [3.0, -1.0, 0.5], [0.5, 1.0, 1.0], [1.0, 1.0, -1.0]]
        net = MLP(3, [4, 4, 1], seed=1)
        loss = sum((net(x) - y) ** 2 for x, y in zip(xs3, YS))
        loss.backward()
        grads = [p.grad for p in net.parameters()]
        assert len(grads) == 41
        top = max(abs(g) for g in grads)
        chart = BarChart(grads, y_range=[-math.ceil(top), math.ceil(top), max(1, math.ceil(top) // 2)],
                         x_length=10.5, y_length=3.4, bar_colors=[GRAD],
                         y_axis_config={"font_size": 24}, x_axis_config={"include_ticks": False})
        chart.move_to([0, 0.7, 0])
        head = MathTex(r"\nabla L\in\mathbb{R}^{41}", font_size=48, color=GRAD).move_to([0, 3.2, 0])
        self.add(chart, head)
        self.play(Create(chart.axes), run_time=1.0)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in chart.bars], lag_ratio=0.05), run_time=3.0)
        note = callout("Same arrow, 41 numbers", "S11's network: one slope per weight", width=9.0)
        note.move_to([0, -1.7, 0])
        self.play(FadeIn(note))
        nar.say("Same idea: one slope per weight, at every single point.")
        self.wait(3.5)
        nar.say("The bowl is an analogy; the downhill rule is the real thing.")
        self.wait(3.0)
        nar.clear()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
