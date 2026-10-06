## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Banners render as 'ExampleA:', 'ExampleB:', 'Expertcorner:' (missing spaces), small top-left, not the required 'Example A / Example B / Expert corner' (frames 2-12).
- Frame 7: axis label reads |x| but the curve is still g(x) (mid-morph mismatch); the label and curve disagree.
- Frame 11: central-difference curve is teal and the forward curve is blue, nearly the same colour; the caption says 'Blue forward... teal central' but hard to distinguish. Frame 10: the question 'Closer to 14 at h=10^-4?' is nearly invisible (dark grey on black), and the central formula is not yet shown. No reveal of the question answer (3.0e-4 vs 3.8e-11) is visible; no conclusion 'micrograd never uses tiny h' shown in any frame.
- Frame 11: log10|error| axis has an odd scale; the central curve starts around -13.7 and rises, and the forward error at h=1e-4 (k=4) is not annotated with 3.0e-4 / 3.8e-11; no numbers are substituted in the Expert corner.
- Frame 6: readout '= 0 ≠ 14' is orange and detached, the slope reads 0.0030 at x=2/3 while the caption talks about the floats warning, which mixes two ideas. The h=1e-16 example is not shown with a real number substituted.
- Frame 5: slope-at-x=-3 question shown but no reveal in any frame (the -21.9970 value never appears); the table has only x=3 row. The readout shows 3.1934 in green while the tangent is mid-slide.
- Frame 3: no caption present; frame 6 and 3 lack worked formulas with substituted numbers ((20.014-20)/0.001 never seen on screen). Frame 4 shows the formula only symbolically.
- Frame 8: the |x| label and Example A reminder overlap the formula column closely (the first fraction touches the grey 'Example A' line); the code panel text is tiny at 480p.
- Frame 9 shows the function f(x) while the description requires the h=1 step to be visible as a secant that misses; acceptable, but the table's 'x' axis label overlaps the table row '0.001' region at the bottom right.
- No 3D view is required for S01, but fewer than 10 of 12 frames carry captions (frames 3, 10 and 7-ish are missing or weak); frame 1 is a title-style card with a caption, OK.
- Description descriptions/S01.md is specific and matches the plan, but claims things not visible in the frames (camera zoom, x=-3 row of -21.997, x=2/3 row, central error numbers, the micrograd conclusion).

