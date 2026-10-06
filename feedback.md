## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 01: the 40-point plot matches the description, but its lower-left area is empty and it looks unbalanced. This is minor.
- Frame 07 (Example B, g(x)): the g'(-1) = 3·(-1)^2 - 3 = 0 formula is nearly black on black and unreadable. This is a contrast and fade problem.
- Frame 11 (Expert corner): the caption 'Errors shrink until k = 8, then rounding wins: at k = 16 both are 14.' is dark grey on black and almost invisible. Its text also says both errors are 14 at k = 16, which does not match the description (both slopes exactly 0).
- Frame 10 (Expert corner title card): the screen is empty apart from the banner and caption, and the caption sits very low. This is acceptable for a title card.
- Act C: the plot is the error-vs-k chart. The forward-difference curve ends at k=8 and does not continue to k=16, so the claim that both curves degrade does not match what is drawn. The forward error is about 3e-4 at k=4 (reads about -3.5, which is fine). The central error at k=4 reads about -10.4, which matches 3.8e-11.
- Act C has no on-screen conclusion that micrograd never uses a tiny h, and no frame shows the h=1e-16 result of 0. Act A frames do not show the floating-point warning either.
- Act B frame 08 (|x|): the left and right secants (-1 and +1) are drawn, but the slope values are not labelled on screen. The only text is the question 'Slope at x = 0?'. The y-axis tick '1' is overlapped by the white and orange segments. No reveal of the answer appears in the 12 frames, so the predict-then-reveal for the kink is incomplete.
- Act A frame 03: the secant dot and the tangent dot overlap near x=3, and the small white dot is cluttered. The slope readout is 14.5076, which is fine.
- Act A frame 06: the flat tangent at x = 2/3 is drawn along the bottom and nearly merges with the x-axis. The 'Derivative' definition box is fine.
- Three-act check: the Example A, Example B and Expert corner banners are present. Visuals per act: A has a plot, table and tangent. B has the g plot, the |x| plot with a code panel, and the h=1 plot. C has only one real visual (the log-error plot), not two.
- Captions: frame 10 is a title card, but frame 11's caption is unreadable, so the 10 of 12 requirement is at risk. Frame 12 is the only readable Act C caption.
- Act B frame 09 (h=1): the 'Example A: f'(3) = 14.0030' comparison is shown next to the new value 17.0000, which is good. Frame 07 shows it too, but faintly.
- descriptions/S01.md is specific and matches the intended content. However, it describes Act C as ending with 'both slopes exactly 0 at h=1e-16' and the micrograd conclusion, and the frames contradict or do not show these (frame 11 says 14, and no conclusion appears). It also describes a camera zoom and a morph that are not visible in the frames I saw.

