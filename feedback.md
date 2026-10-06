## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frames 1-12 show no act banners for 'Example A' or 'Example B'; only the 'Expert corner' banner is visible (frame 10), so the three-act requirement is not met.
- Frame 1: caption 'Forty x values...' is nearly invisible (faded in), and the plot is empty.
- Frame 6: the 'Derivative' definition box is half faded and hard to read.
- Frame 9: the |x| to f morph is caught mid-transition, so the axis labels are garbled and overlapping ('|x|', '3', '1 1'). The caption says 'Back to f' but the frame shows a half-morphed curve, not f, and no h=1 secant or slope 17.0 appears.
- Frame 8: the |x| kink is shown without the left and right secants (-1 / +1). The description requires both to be animated.
- Frame 7: g(x) is shown, but no flat-tangent reveal at x=±1 is visible. The question 'Where is the slope 0?' is never visibly answered in the frames.
- Frame 11: the caption is fading and is barely readable, and the k=4 cursor line carries no readout of the forward (3.0e-4) or central (3.8e-11) errors.
- Frame 11 and the plot: the y-axis is labelled as log10|error| but the ticks run oddly (2, -2, -4 ... with no 0), the plot is cramped, and the x-axis label sits far from the axis.
- Act C is missing the floating-point warning (h=1e-16 gives exactly 0) and the on-screen conclusion that micrograd never uses a tiny h. Frame 10 is a near-empty title card with a banner and caption only.
- Frame 4 is the only visible formula with real numbers substituted; the step-by-step derivation is thin. Frame 4 also shows the secant line in a dark green on black that is hard to see.
- Example B shows no original values next to the changed ones. Captions are visible in about 11/12 frames, but several are generic ('Predict: ...').
- Each act has fewer than two distinct visuals visible in the sampled frames; Act B shows only bare curves. The code panel and bar chart are absent.
- The description file descriptions/S01.md is specific and matches the script, but it describes content that the frames do not show (e.g. the h=1 slope of 17, the secants for |x|, and the 1e-16 warning).

