## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 5: slope readout shows -21.7686 at x≈-3, while the spec and the table below say -21.997; the table still shows only the x=3 row, so it is not filling row by row.
- Frame 3: slope 15.4905 with h≈0.5 is shown with a tangent-looking line; the h segment and rise triangle are tiny and hard to read at 480p.
- Frame 4: the formula 'slope = (f(3+h)-f(3))/h' is dimmed and very low contrast. Real numbers are not substituted (20.014-20)/0.001, so the step-by-step derivation with numbers is not visible.
- Frame 7: Act B g(x) shows slope 8.7733 on the steep branch with the dot at the left edge; the flat points at x=±1 are not shown. The morph from f to g is not visible. The Example A 'f'(3)=14.0030' comparison sits cramped under the readout with the question 'Where is the slope 0?' almost touching it.
- Frame 8: the |x| plot has no secants, no left −1 / right +1 slopes and no 'no derivative' conclusion. The code panel is tiny and its text is hard to read at 480p, with the highlight box overlapping the first line.
- Frame 9: Act B 'h=1 gives 17.0000' is not shown. The frame has just the bare f curve with no secant, no readout and no changed value next to the original.
- Frame 10: nearly black frame (mid-transition) showing the Example B banner with faint ghosts of the previous curve. Unusable as a published frame.
- Frames 11-12: Expert corner has the log error plot but the axis x-label and caption are crowded against the bottom, and the plot spans k=1..16 so the h=1e-16 exact-0 case is not shown. The conclusion 'micrograd never uses tiny h' is not visible. Frame 11 formula/result text 'forward/central' labels sit tight against the fractions. Frame 12 is fine but the results line is gone.
- Act banners: Example A banner is shown large only in frame 1; later it reads 'Example A:' with a trailing colon and no title. Act B and Expert corner are shown, but the check 'at least two real visuals in each act' is not met in Act B (only plot and a small code panel) and the table is only a single row.
- Predict-then-reveal: frame 2 poses the question, but the reveal is the unlabeled secant; the sign-of-slope question at x=-3 is not visible as a question. The floating-point warning (h too many zeros) is not visible in any frame.
- Required typeset-formulas-with-numbers and a real 3D view for S02/S12 are not applicable here, but the check for formulas with substituted numbers fails.
- descriptions/S01.md is specific and well written, but it describes content that the frames do not show (numeric substitution (20.014-20)/0.001, rows for x=-3 and 2/3, secants on |x|, h=1 slope 17, h=1e-16 giving 0, micrograd conclusion), so it does not match the frames.

