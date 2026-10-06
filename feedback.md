## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frames 2-6: Example A banner disappears after frame 1; frames 7-12 never show an 'Example B' or 'Expert corner' banner, so only 1 of 3 act banners is visible.
- Frame 7: stale 'slope = 8.9940' readout and 'Example A' leftover text remain during g(x) act, cluttering the panel; slope readout is meaningless there.
- Frame 8: curve labeled |x| (axis label) is still the g(x) cubic morph midway, with y-axis 0..3 mismatched to the curve (curve shape wrong for label); stale 'Example A' text lingers.
- Frame 10: 'Closer to 14 at h = 10^-4?' question is dark grey/near-black on black and almost unreadable, and overlaps the region under the forward formula; the x-axis label 'k (h=10^-k)' sits very close to caption.
- Frame 10: caption says 'teal central' but forward curve and its label are blue; frame 11 central curve is green-teal while forward label colour is similar blue — colours hard to distinguish. The reveal in frame 11 shows the curve dipping below the forward line at k=1-3 (error -13), contradicting expected error behaviour of central at large h and the claimed ~1e-11 at k=4 (marker at about -10.4).
- Frame 6: orange text '= 0 ≠ 14' is detached from the slope readout and floats with no clear referent; slope 0.0030 at x=2/3 mixed with a warning about h=1e-16 is confusing.
- Frame 5: table shows only one row (x=3) and slope readout 3.1934 while sliding; x=-3 and 2/3 rows are not visible; the sign-question text is dim olive and low contrast.
- Frame 9: table at right bottom runs close to x-axis label 'x' of the plot (0.001 row near axis at x=5); layout crowded.
- Frame 3: no caption in this frame; frames 1,2,... captions are present in most frames but frame 3 lacks one, and no typeset step-by-step substitution of numbers (e.g. (20.014-20)/0.001) is visible in any frame.
- Not enough visuals/requirements across the 12 frames: no Example B changed-vs-original side by side for the kink beyond text, no live h=1 floating-point 1e-16 demonstration, no visible 'micrograd never uses tiny h' conclusion, no 3D view (not required for S01).
- descriptions/S01.md is specific and mostly matches the plan, but claims (camera zoom, row-by-row table with x=-3 and 2/3 rows, 1e-16 warning with 0 result, conclusion) are not visible in the frames.

