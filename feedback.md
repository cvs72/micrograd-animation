## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 12 (final frame): the required on-screen conclusion (micrograd never uses a tiny h, it computes exact local derivatives) is not visible. The description and the Act C spec both promise it.
- Frame 12: the caption sits almost on the x-axis label 'k (h = 10^-k)', so the two lines of text are nearly touching. The 'rounding noise, k > 8' label also sits very close to the green curve.
- Frame 11: there is no caption, even though it is not a title or recap card.
- Frame 7: the 'g'(-1) = 3·(-1)^2 - 3 = 0' formula is rendered very dark grey on black, so contrast is too low to read at 480p. The 'Example A: f'(3) = 14.0030' comparison line is also dim.
- Frame 9: the caption 'With h = 1 the slope reads 17, not 14...' is dark grey on black, so contrast is too low. The secant, tangent and triangle all crowd into one small area near x=3..4 with overlapping coloured lines, and there is no h label on the white segment.
- Frame 8: the kink is shown with orange and green secants, but there are no -1 / +1 slope labels. The question 'Slope at x = 0?' is never answered in these frames (no 'no derivative' reveal). The code panel at right is small and tight against the frame edge.
- Frame 3: the secant dots and tangent line crowd around the point (3, 20), where a small white/yellow dot is clipped by the line, so there is no clear h segment or rise-over-run triangle. The slope readout (14.5076) does not match the 14.0030 expected at this stage.
- Frame 5: there are two redundant slope readouts ('slope = -21.9970' and 'slope = -21.997 < 0') stacked on the right. The table has no x = 2/3 row, and the sign-first question for x = -3 is not visible as a question before its reveal.
- Act A: the floating-point warning (too many zeros in h gives wrong answers) is not shown in any Act A frame, only the end of Act C. The zoomed rise-over-run triangle with the h segment is also not visible in Act A frames.
- Act B: no frame shows the morph from f to g, and the changed values are next to the originals only as the small dim 'Example A: f'(3)' line. The x = 1 valley is not shown.
- Act C: frame 10 is an empty axes with no plot content, and the central-vs-forward curves in frame 11 are not labelled with h = 1e-4 on the plot itself.
- descriptions/S01.md is detailed and mostly matches the planned content. However, it describes things the frames do not show: the camera zoom into the triangle, the table row for x = 2/3, the morph to |x| with -1/+1 secants, and the micrograd conclusion.

