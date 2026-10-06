## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 5: the table shows only the x=3 row (14.003) while the slope readout shows -21.7686 at x=-3, so table and readout disagree. Also the readout is -21.7686, not the -21.9970 the description requires.
- Frame 4: the formula 'slope = (f(3+h)-f(3))/h' is dim grey and nearly unreadable. No substituted numbers such as (20.014-20)/0.001 appear in any frame, so the 'real numbers substituted before results' requirement is not met.
- Frame 3: the secant, white step h and orange rise triangle are tiny and cramped around the dot. The slope reads 15.4905, which is a mid-animation value, and the dot/tangent overlap is hard to read.
- Frame 2: the predict question appears, but no reveal is visible afterwards in the sampled frames. The act banner is cut to 'Example A:' with a trailing colon and no title.
- Frame 7: the Example B g(x) frame has the slope readout at 8.7733 and the tangent at x≈-2, not at the flat points. The caption says x=-1 and x=1, but no flat tangent is shown. The curve morph from f to g is not visible.
- Frames 8-9: the |x| frame has no secants (left -1, right +1) and no 'no derivative' conclusion. In frame 9 (h=1 case) the curve is shown with no secant, no 17.0000 readout and no changed-vs-original values side by side.
- Frame 10 is almost entirely black, with only a faint ghost of the curve, while the banner still says 'Example B'. This is a mid-transition frame that should not be published.
- Frame 11: the title-card style banner is OK, but the log axis label reads 'log10 |error|' with k on x. The 3.0e-4 vs 3.8e-11 text is shown, but the plot has no marked region for rounding degradation below h=1e-8. The error curve for forward difference stops at k=8, so the h=1e-16 result of exactly 0 is never shown.
- Frame 12: the plot is the same as frame 11, so it adds no new visual. No conclusion 'this is why micrograd never uses a tiny h' appears in any frame, and the floating-point warning from the lecture (too many zeros in h) is not visible.
- Act structure: Example A, Example B and Expert corner banners are present, but Example B has fewer than two real visuals with the required content. Captions are missing on frame 10's visual content, and there is no 3D view (not required for S01).
- descriptions/S01.md is specific, but it describes content the frames do not show: the zoom into the triangle, the row-by-row table with three rows, the left/right secants on |x|, the h=1 slope reading 17, and the final conclusion.

