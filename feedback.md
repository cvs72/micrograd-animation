## Reviewer feedback for S01 (row un-ticked; fix and re-render)
- Frame 09 (|x| secants): caption area at the bottom is empty/black, so no caption. Frame 11 (expert plot): caption area is empty too.
- Frame 12: bottom caption ('At k = 16 both slopes read 0...') is rendered almost black on black, unreadable. Captions are readable in only 9 of 12 frames, below the required 10.
- Frame 12: the yellow '3.0e-4 vs 3.8e-11' text sits directly under the 'central' label and almost touches it. It is also not labelled with which curve is which error, or with h = 1e-4.
- Expert corner: the required on-screen conclusion (micrograd never uses a tiny h but computes exact local derivatives) is not visible in any frame.
- Expert corner: the h = 1e-16 'both return exactly 0' point is only in the unreadable caption, with no visual marker on the plot. The log-plot x-axis is k, not h, and the y-axis has no unit for the 14 error. The 'rounding noise, k > 8' label floats over the curve with no pointer.
- Predict-then-reveal is incomplete: frame 02 asks 'above or below 20?' but no frame shows the answer. Frame 07 asks 'Where is the slope 0?' but the answer (flat at x = -1 and x = 1, hump and valley) is never shown. The x = -3 sign question is not visible.
- Frame 05: the table has only x = 3 and x = -3. The x = 2/3 flat-tangent row (about 0.0030) is missing, and the dot is parked at about 0.5 showing -1.4545 with no explanation.
- Act A lacks the step-by-step derivation with the rise-over-run triangle and h segment in the sampled frames. Only a single formula line appears (frame 04), and the triangle appears only in Act B frame 10.
- Frame 07: the function morph from f to g is not visible, and g's flat tangents are not shown. Frame 07 'Example A: f'(3)=14.0030' reminder next to slope 8.9940 is not explained. Frame 08 has no caption about the kink at this moment beyond the V, and the code panel is small.
- Expert corner shows only one visual (the log plot), not two. Act B changed-vs-original is partly shown (reminder line, 17 vs 14), but the two-visual requirement per act is weak.
- descriptions/S01.md is specific, but it does not match the frames in several places. It promises the camera zoom into the triangle, the 2/3 row, the h=1e-16 slope 0 in both methods, and the micrograd conclusion, none of which are visible.

