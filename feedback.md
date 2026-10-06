## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 1: the dot plot is only half drawn. Points for x>0 fade to near-invisible, so the 'forty x values' caption is not matched.
- Frame 3: no caption. The secant triangle (h segment and orange rise) is tiny and unlabeled, so the f(3+h)>20 prediction from frame 2 is never visibly answered.
- No frame shows the formula with real numbers substituted, e.g. (20.014-20)/0.001 = 14.003. Frame 4 shows only the symbolic f(3+h)-f(3) over h.
- Frame 5: the table has only the x=3 row. The x=-3 sign question is asked but never revealed, and no frame shows -21.997 or the x=2/3 row. The orange/white/teal readout is only partly demonstrated. The dot at x≈1.2 and the question text are low-contrast olive.
- Frame 6: the readout 'slope = 0.0030' next to '= 0 ≠ 14' is confusing. It mixes the flat tangent at x=2/3 with the h=1e-16 floating-point warning, and no h=1e-16 value is shown.
- Frame 7: g(x) is shown but the flat tangents at x=-1 and x=1 are not revealed. The predict question is never answered. The slope readout 8.9940 sits at x=-2 with no tangent visible.
- Frame 8: this is a mid-morph frame. The axis label says |x| but the curve is still the cubic, so label and curve do not match. The y-axis range is also inconsistent.
- Frame 9: the '|0|-|-1|' fraction nearly touches the 'Example A: f′(3)=14.0030' line above it. The code panel text is tiny and crowds its border and highlight box, so it is hard to read at 480p. No y-axis label.
- Frame 11: the question 'Closer to 14 at h=10^-4?' is nearly invisible (dark grey on black). The 'forward' label touches the fraction bar. The caption mentions blue and teal curves but only one curve exists yet.
- Frame 12: the olive '3.0e-4 vs 3.8e-11' line is low contrast and sits close to the 'central' label. There is no legend for the curve colours. The required on-screen conclusion (micrograd never uses a tiny h but computes exact local derivatives) is never shown, and the question from frame 11 is never revealed.
- Act C has essentially one visual, the error plot. At least two real visuals per act are required.
- Act B frames do not clearly show the changed values next to the originals. Only a small grey 'Example A: f′(3)=14.0030' line is carried over.
- descriptions/S01.md is specific and well written, but it claims content the frames do not show: the worked numeric substitution, the table rows for -3 and 2/3, and the micrograd conclusion.

