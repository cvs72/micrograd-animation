## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Only 12 frames sample the scene and they miss required content: no frame shows the MathTex step-by-step derivation with numbers substituted, no x=-3 sign question revealed with -21.9970, no x=2/3 0.0030 table row, no abs(x) secants (-1/+1), no h=1 secant with 17.0000, no h=1e-16 result of 0, and no final micrograd conclusion.
- Frame 1: the curve is half drawn, with dots fading out around x=3 to 5 and the plot is left-heavy. The right half of the screen is empty.
- Frame 3: the slope readout shows 15.4382 but the h/rise-run triangle is tiny and unlabelled (no h label). The tangent in frames 3 and 4 is hard to tell apart from the curve.
- Frame 4: caption is dim grey and low contrast, and is mid-fade. It says h=0.001 but there is no formula displayed.
- Frame 5: the readout shows -9.8627 at x=-1 (not the specified x=-3). The 'slope at x=-3: + or -?' question is nearly invisible (dark olive on black). The table has only the x=3 row. The old green tangent is still visible as a ghost.
- Frame 6: the readout is white 0.0030 at x=2/3, which is fine, but the right side is otherwise empty. The warning caption is generic and no floating-point demonstration is shown.
- Frame 7 (Example B, g): the slope readout (8.9940) overlaps closely with the 'Example A: f′(3)=14.0030' line and the question line. They are stacked with almost no spacing. The tangent at x=-2 is clipped against the curve edge. The hump and valley are never shown flat.
- Frame 8: the abs(x) frame has a code panel (a real visual) but no secants or slopes are shown, and the axis label |x| sits close to the axis tick '3'.
- Frame 9: the curve labelled f(x) is a V shape (mid-morph from |x| to f) with y up to 100. No secant, h=1 or 17.0000 is shown, and the caption claims a secant that is not on screen.
- Frame 10: labelled Example B, but the caption already says 'Expert corner'. The banner is mismatched. Only a plain curve is shown (nothing new).
- Frame 11: the faint olive text '3.0×10^-4 vs 3.8×10^-11' is low contrast. The 'k = 4' label is dim. The caption is cramped against the bottom of the x-axis label. The plot lacks a visible axis title for the y-values beyond 'log10|error|', and the curves do not show the h=1e-16 value of 0.
- Frame 12: the code panel overlaps nothing, but the conclusion that micrograd never uses a tiny h is not shown on any frame. The 'k=4' label touches the top of the vertical line.
- Act check: the Example A, Example B and Expert corner banners all appear. Example A, though, has only one real visual per frame (plot) and a thin table. Captions are present in all frames, but several are generic ('Back to f...', 'Expert corner: how good is this nudge...'). There is no 3D requirement for S01.
- The description descriptions/S01.md is specific, but it claims content that frames do not show (secants -1/+1, 17 for h=1, h=1e-16 giving 0, conclusion, 0.0030 table rows).

