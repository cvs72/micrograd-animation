## Reviewer feedback for S00 (row un-ticked; fix and re-render)
- frames/index.txt gives an empty description for S00, so I judged against the PLAN.md row. This is a process problem.
- Frame 02: a stray teal dash sits at about x=500-530 next to the code panel. It is a truncated arrow that points at nothing. 'g = ?' is thin, teal on black and small, so it is weak at 480p.
- Frame 04: the check line 'a: -4 -> -3.999, h = 0.001' is small and low-contrast teal. The result '= 139.0388' is shown without a left-hand side or any working, so it reads as a bare number. The orange arrows beside ∂g/∂a and ∂g/∂b point at the whole code panel, not at a and b (lines 1-2).
- Frames 05 and 06 to 08: the callout body text, the network title 'A tiny network: 16 knobs (weights)' and the 'inputs / hidden / output' labels are grey and roughly 20 px tall at 540p. That is below the 24 pt minimum and low-contrast.
- Frames 06 to 08: the slider handles are thick grey bars lying on top of the connection lines. In frame 06 the two crossing sliders at the top left overlap each other and the lines, and the result looks cluttered. The right half of frame 06 is empty.
- Frames 07 and 08: the plan asks for a question mark when a knob is turned blindly and the loss gets worse. No frame shows a question mark or a loss increase. Frame 07 shows loss 1.2513 with no sign that it got worse, and frame 08 shows 'lucky, the loss falls'. There is no predict-then-reveal visible.
- Frames 09 and 10: the roadmap should light up one chapter at a time, but only chapter 9 is lit in frame 10 and nothing is lit in frame 09. The caption in frame 10 ('adding up gradients, more operations, PyTorch') does not match the single highlighted chapter 9 'PyTorch'.
- Frame 12: no caption is visible, although captions are required at all times except on the title card and recap line. The scene is not a title or recap frame.
- The 12 sampled frames show no title card, no recap line and no closing question 'what is a derivative, really?'. The plan requires all three.
- Frames 11 and 12: the three-act preview is thin. The icons are tiny and the first two are identical parabolas in frame 11. The Example A and Example B banners only show the plain wording, not a real example.
- Frame 01: I could not confirm that the code panel matches test_readme_example in tests/test_oracle.py. The panel's lines 4 to 8 read like an odd mix and should be checked against the test.

