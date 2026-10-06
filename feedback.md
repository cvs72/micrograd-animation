## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 10: the frame is almost black, with only a caption and no visual. It looks like a transition caught mid-way, or an empty card.
- Frame 11: the Expert corner plot has no caption, and the frame is identical to frame 12 except for the caption. The captions that are present are all generic.
- Frame 12: the Expert corner never shows the required conclusion that micrograd never uses a tiny h and computes exact local derivatives. It also never shows the floating-point failure, either the h=1e-16 result of exactly 0 or the 'both degrade below ~1e-8' annotation. The plot ends at k=16 with no marker for these.
- Across all 12 frames the lecture's floating-point warning (too many zeros in h gives wrong answers) is never shown on screen. The description file says it is, so the description does not match the frames.
- The Example A table in frame 5 has only the x=3 and x=-3 rows. The x=2/3 row never appears in the table. Frame 6 shows the 0.0030 readout but the table is gone.
- Example B (1): the morph from f to g is not visible, only the finished g plot in frame 7. In that frame the 'g'(-1) = 3·(-1)²-3 = 0' line is dim grey on black and barely readable at 480p. The orange/teal readout shows '-0.0030' without the original-vs-changed comparison that the 'Example A: f'(3)=14.0030' line gives.
- Example B (2): in frame 8 there is no slope readout of -1 and +1 for the two secants. The slope is only asked about in the question text, and the reveal is not shown in any frame, so predict-then-reveal is incomplete.
- Frame 9: the caption is dim grey and low contrast against the black background, hard to read at 480p. In frame 3 the secant dot and the tangent overlap at the point, so the h segment is not legible.
- The step-by-step MathTex derivation with substituted numbers is shown in only one frame (frame 4). Frame 1 shows 40 dots, but the right-most dots fade out and look cut off.
- Only frames 1 and 10 look like title or intro frames, so captions are present in 10 of 12 frames at best. Frames 10 and 11 lack visuals or captions, and the required reveal of the sign question at x=-3 is not clearly shown as a question first.

