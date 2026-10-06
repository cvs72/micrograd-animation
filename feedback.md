## Reviewer feedback for S11 (row un-ticked; fix ONLY the blocking items, rejection 1 of 4)
- BLOCKING: Frame 5 (Act A loss curve): the layout is broken. The 'loss' axis label is clipped at the top edge, and the '∂L' formula is cut off at the bottom edge. The caption overlaps the x-axis tick labels (15, 20, 25), so the key caption and the formula are not readable.
- BLOCKING: Frames 1-5 (Act A) never show the update rule p.data += -lr*p.grad, or the loss sum, as typeset MathTex with real numbers substituted. The only formula-like item in the whole scene is the partial '2 · 1.5' in frame 12. Act A therefore lacks the required formula with substituted numbers. The sole fragment is the clipped '∂L' in frame 5.
(optional, ignore unless you have time:)
- optional polish: Frame 10 (zero_grad): both axes are empty, with no curves. The colour legend 'zeroed each step / never zeroed' has no line swatches. Check that a neighbouring frame shows the accumulating gradient, since the 'loss still falls' point is not visible in any frame.
- optional polish: Frame 4 asks 'knob up or down?' (gradient -2.3854), but no sampled frame shows the reveal. The predict-then-reveal beat is only half visible. In frame 8 the loss reads 7.8034 while the plan and frame 7 say about 8.0, so label it as a particular step.
- optional polish: Frames 3-4 leave the right half empty beside the bar chart. In frame 12 the right side holds only the lone '2 · 1.5' with no result, so the comparison looks unfinished.

