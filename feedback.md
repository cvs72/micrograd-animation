## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Act banners: only 'Example A: the lecture's own function' is visible (frame 1). No 'Example B' banner and no 'Expert corner' banner appear in any of the 12 frames.
- Frame 3 has no caption, so captions are present in 11 of 12 frames. That meets the 10-of-12 threshold, but frame 3 is a main Act A frame and should have one.
- Frame 11: faint, almost invisible dark text ('Closer to 14 at h=10^-4?') sits at right-middle. It is unreadable, and it is the on-screen question for the Expert act. The caption below also mentions the teal central step, which is not drawn yet.
- Frame 9: the curve is caught mid-morph. The y-axis label reads |x|, but the curve drawn is the cubic g(x), so the label and curve contradict each other. The tangent and the x=-1 / x=1 reveal are not shown.
- Frame 8: the predict-then-reveal for g never visibly resolves. The frames show no flat tangents at x=-1 and x=1 and no g'(x)=3x^2-3 formula.
- Frame 7: the right-hand text '= 0 ≠ 14' is orange with no visible lead-in. It sits next to 'slope = 0.0030', so it reads as a contradiction. The h=1e-16 float warning has no formula or number shown, and the x=2/3 flat tangent is not labelled.
- Frame 6: the table has only one row (x=3). The x=-3 row, with its -21.997 result and the predicted sign, never appears in the frames. The 'slope at x=-3: + or -?' question is in dim olive text with low contrast.
- Frame 3 and frame 4: substituted-number MathTex is thin. Frame 4 shows only the symbolic f(3+h)-f(3) over h, with no (20.014-20)/0.001 substitution. Frame 3's rise-over-run triangle is tiny and unreadable.
- Frame 10: the 'Example A: f'(3)=14.0030' reference line is crammed directly above the first fraction, almost touching it. The code panel at lower right is small. The 'changed values next to originals' idea for |x| is not shown beyond this reference line.
- Frame 12: the central-difference curve is drawn but the forward and central curves look merged and unlabelled apart from the formulas. No error values (3.0e-4, 3.8e-11) and no concluding micrograd statement are visible. The caption claims both are exactly 0 at k=16, but the plotted points are about 1, not 0 or -inf, so the plot contradicts it.
- Frames 11-12: the log-plot y-axis label 'log10|error|' is clipped close to the top-left edge. The plotted point at k=16 sits at the edge of the axis range.
- Frames 2-12 do not show a rotating tangent with a colour-coded readout going through orange for negative slopes. No negative-slope readout is visible in any frame, so the orange-white-teal behaviour cannot be verified.
- descriptions/S01.md is detailed and mostly matches the planned scene. It does not match the frames: it claims a zoom into the triangle, a table with x=-3 and x=2/3 rows, a morph with flat tangents, both secants animated, the error numbers and the micrograd conclusion, and none of these are visible in the 12 frames.

