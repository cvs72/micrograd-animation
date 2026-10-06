## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frames don't cover the spec: no frame shows x=-3 slope -21.997 reading, the x=2/3 table row, the abs(x) left/right secants (-1/+1), the h=1 slope 17.0000, the floating-point/h=1e-16 warning, or the micrograd conclusion; description claims these but frames don't show them.
- Frame 05: readout -21.7686 at x≈-3 is not the specified -21.9970 (h not 0.001); table beside it has only the x=3 row, so it is not filling row by row, and the f(x+h) value 20.014 is shown without the substituted-number formula.
- Frame 04: formula 'slope = (f(3+h)-f(3))/h' is dark grey on black, almost unreadable; no numbers substituted ((20.014-20)/0.001) in any frame.
- Frame 03: rise-over-run triangle is tiny and unlabelled (no h label, no rise label); readout 15.4905 is not explained.
- Frame 07: Example B g(x) shows slope 8.7733 at x≈-2 with a yellow dot, but the flat tangents at x=±1 are not shown; the Example A reminder text sits crammed under the slope readout and the question 'Where is the slope 0?' is never visibly revealed.
- Frame 08: abs(x) plot has no secants and no slope readout. The code panel's text is tiny (below legible at 480p) and its highlight box overlaps the first line 'def my_abs(x):'. The panel sits close to the x-axis label.
- Frame 09: Example B 'h far too big' shows only a bare curve with no secant, no h=1, no 17.0 readout; nothing demonstrates the point.
- Frame 10: nearly black transition frame, still labelled 'Example B'; wasted frame.
- Frames 11-12: the Expert corner log plot works, but the x-axis is k, not h as specified, and the 'log10|error|' label sits at the top-left corner, off the axis line. There is no marking of the rounding turnaround at h≈1e-8 or of the h=1e-16 zero result. The curves don't clearly say which colour is forward and which is central beyond the formula labels. The frame 11 text '3.0×10^-4 vs 3.8×10^-11' is fine.
- Act banners: Example A in frame 1 is a boxed title, but frames 2-9 use a small 'Example A:' / 'Example B:' with a trailing colon and no title text, so the banners look unfinished.
- Depth check: Act A has only a plot and a table; Act B has the plot, a code panel but no real tables or other changed-vs-original values side by side (only a faint text reminder); the formulas have no real numbers substituted before results; captions are present in all frames except possibly 10 but several are generic.
- Description descriptions/S01.md is specific, but it does not match the frames: the frames lack the camera zoom, the table rows for -3 and 2/3, abs secants, h=1 and the h=1e-16 warning.

