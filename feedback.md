## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 11: the faint question 'Closer to 14 at h=10^-4?' is almost invisible (dark grey on black) and sits right under the 'forward' label. Poor contrast.
- Frame 11: the caption says 'Blue forward... teal central', but only the forward curve is drawn. The forward curve is cyan and the formula label is also cyan.
- Frame 12: the error curves are drawn from k=1 to 16. The central curve starts at about -13.7 at k=1 and rises with k. That does not match the described plot (central error 3.8e-11 at h=1e-4, i.e. k=4). The marker at k=4 reads about -10.4. The conclusion that micrograd never uses a tiny h is not shown on screen in any frame.
- Frame 12: the question from frame 11 is never revealed. No answer about which method is closer to 14 appears, so the predict-then-reveal is incomplete.
- Frame 8: the y-axis label reads |x| while the curve still shows the g(x) cubic morph in progress. The label and curve mismatch for that frame. The cubic also doesn't match the x=0 axis crossing.
- Frame 9: the secant formulas '|0|-|-1|/1' crowd the 'Example A' line above them. The code panel's yellow box tightly overlaps its text. The small code text is hard to read at 480p.
- Frame 7: g(x) is labelled with slope 8.9940 at x=-2, but the flat tangents at x=±1 are never shown in any frame (no reveal of the predict question). The Example A reference text and the 'Where is the slope 0?' question are crammed together.
- Frame 6: the 'slope = 0.0030' readout is white and shows '= 0 ≠ 14'. This mixes the flat-tangent case at x=2/3 with the h=1e-16 float warning, which is confusing. The x=-3 negative slope (-21.997, orange) is never shown, and the table in frame 5 only has the x=3 row.
- Frame 5: the readout shows 3.1934 at about x=1.2 while the table and the question 'slope at x=-3: + or -?' compete for space. The question is never revealed in later frames (no -21.9970, no orange readout).
- Frame 1: the title banner is Example A, but frame 1 is the only frame with a banner box. Frames 2-6 show only a small 'Example A:' with nothing after it, and the banner text is cut to a bare label.
- Frame 10 (Expert corner banner, frame 11): the three-act check needs two real visuals per act. Act C has one plot only. Act A has no typeset step-by-step derivation with substituted numbers in the frames. Frame 4 shows only the general formula f(3+h)-f(3) over h, with no numbers substituted, although the description file says the numbers are worked.
- Captions are missing in frames 2 to 12 only partially. Frame 3 has no caption at the bottom and frame 11 has no caption in the title area, so the 10-of-12 caption requirement is marginal.
- descriptions/S01.md is specific, but it claims content that the frames do not show: the camera zoom, the table rows for x=-3 and 2/3, g flat at x=±1, the h=1e-16 slope 0 numbers, the conclusion card, and the central error 3.8e-11 at h=1e-4.

