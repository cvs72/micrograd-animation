# Animation plan (edit this BEFORE starting the loop; one row per scene)

Row format: `- [ ] ID | file | Class | min-max seconds | what the scene must show`
The builder ticks a row only after rendering it; the loop un-ticks it if the reviewer fails it.

- [x] S01 | scenes/scene01_derivative.py | Scene01Derivative | 20-70 | f(x)=3x^2-4x+5 plotted on Axes; a tangent line slides along the curve while its slope updates; nudge h shrinks toward 0
- [x] S02 | scenes/scene02_multi_input.py | Scene02MultiInput | 20-70 | d=a*b+c with a=2,b=-3,c=10; nudge each input by a small h and show how much d moves
- [ ] S03 | scenes/scene03_graph_forward.py | Scene03GraphForward | 20-70 | Value nodes (data, grad) and the computation graph for d=a*b+c; forward pass fills in numbers, numbers computed by running the Value class
- [ ] S04 | scenes/scene04_backward_manual.py | Scene04BackwardManual | 30-90 | backward pass node by node: + passes gradient through, * swaps children; chain rule with MathTex
- [ ] S05 | scenes/scene05_neuron_tanh.py | Scene05NeuronTanh | 30-90 | one neuron (two inputs, weights, bias, tanh); gradients flow back node by node
- [ ] S06 | scenes/scene06_toposort.py | Scene06TopoSort | 30-90 | topological order of the graph, then _backward called in reverse order, nodes lighting up in sequence
- [ ] S07 | scenes/scene07_accumulation_bug.py | Scene07AccumulationBug | 20-70 | b=a+a: gradient with = (wrong, 1) versus += (right, 2)
- [ ] S08 | scenes/scene08_training.py | Scene08Training | 30-90 | gradient descent on a tiny MLP: loss curve falling as weights update; real numbers from the Value class
- [ ] S09 | scenes/scene09_loss_surface.py | Scene09LossSurface | 20-70 | ThreeDScene loss surface over two weights with a point descending (state clearly this is an analogy)
