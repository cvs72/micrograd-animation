# Notes on Karpathy's micrograd lecture (own words; checked against the lecture transcript)

How to use this file: read the section for your chapter first, then grep reference/lecture_transcript.md for the keywords given (the transcript has numbered chunks like [T042]), then read the notebook for the exact code and values. The NOTEBOOKS WIN for code and numbers: this is live speech with slips, and some values (marked "not stated") are never said aloud. Never copy sentences from the transcript into captions or on-screen text; explain in your own words.

Teaching devices he uses all the time (reuse them): he pauses and asks the viewer to predict a sign or a value before revealing it; he verifies almost every claim with a quick numerical nudge; he separates the "local derivative" (what one little node knows) from the "global derivative" (the effect on the final output); he builds first, then abstracts; he is relaxed about his own mistakes and leaves them in.

## L0 Opening and the README example
- Goal stated up front: start from a blank notebook and end by defining and training a neural net, seeing everything under the hood.
- micrograd = a small autograd engine (automatic gradient); it implements backpropagation, the algorithm that gives the gradient of a loss with respect to the weights, which is then used to tune the weights and lower the loss. Modern libraries (PyTorch, JAX) have it at their core.
- README example: a = -4.0, b = 2.0 wrapped in Value objects, then a made-up expression using add, multiply, power by a constant, offset by one, negate, relu, square, divide; output g. Forward value g about 24.7 (exactly 24.7041); after g.backward(): a.grad about 138 (138.8338) and b.grad about 645 (645.5773). Meaning: nudge a up a little and g grows with slope about 138.8; same for b with slope about 645.6.
- He stresses the expression is meaningless, "flexing" what the engine supports. Neural nets are just a (less crazy) kind of mathematical expression: data and weights go in, predictions or a loss come out. Backprop does not care about neural nets at all; it works for any expression.
- keywords: README, flexing, expression graph, meaningless

## L1 Why scalars, and how small micrograd is
- micrograd is scalar-valued on purpose: everything broken into individual numbers and tiny plus and times operations; "excessive" and never done in production; chosen for teaching so there are no n-dimensional tensors in the way.
- Real libraries pack scalars into tensors (arrays) so operations run in parallel; none of the maths changes, it is purely efficiency.
- His claim: micrograd is all you need to train networks, everything else is efficiency. The repo has two files: the engine (about 100 lines) and nn.py (neuron, layer, MLP; "a joke"), about 150 lines in total.
- keywords: scalar valued, tensors, efficiency, two files, 100 lines

## L2 What a derivative is (one input)
- Function f(x) = 3x^2 - 4x + 5, made up at random. f(3.0) = 20. He plots it over x from -5 up to (not including) 5 in steps of 0.25 with numpy arange and matplotlib: a parabola.
- He refuses the symbolic route (nobody writes the derivative of a network by hand: thousands to tens of thousands of terms) and goes to the definition: the limit as h goes to zero of (f(x+h) - f(x)) / h. Reading: bump x by a small h, how does the function respond and how strongly.
- Numeric approach with h = 0.001. At x = 3: rise over run gives about 14, confirmed by differentiating in his head (6x - 4 = 14). He asks the viewer: will f(x+h) be above or below 20? (above, because the slope is positive).
- Warning: too many zeros in h eventually gives wrong answers because floating-point numbers are finite.
- At x = -3 he asks for the SIGN first: the function goes down when x goes up there, so negative; about -22. The slope is exactly zero near x = 2/3 (he says he looked it up): nudging does almost nothing.
- Not stated: the exact values he prints beyond 14, -22 and 0; read the notebook.
- keywords: rise over run, floating point, differentiable, slope, two over three, bump

## L3 Several inputs
- d = a*b + c with a = 2.0, b = -3.0, c = 10.0, so d = 4. Method: tiny h, fix the inputs, compute d1, bump ONE input by h, compute d2, slope = (d2 - d1) / h.
- Bump a: he reasons first that b is negative so a larger a adds less to d, so d goes DOWN; the notebook shows d falling from 4.0 to about 3.9997 (he reads it aloud as 3.9996); slope = -3 = the value of b (matches calculus: derivative of a*b + c with respect to a is b).
- Bump b: because a is positive, d goes up; slope = 2 = the value of a.
- Bump c: a*b is untouched, d rises by exactly what c rose by; slope = 1.
- Not stated: the exact h used in this part (the notebook has it).
- keywords: three scalar inputs, bump a, negative three, slope is one

## L4 The Value class and the graph
- A Value wraps a single scalar. He pastes a skeleton, then adds a readable print form (__repr__; the transcript garbles it as "wrapper"). Python cannot add two Values until __add__ is defined; the dunder methods make a + b call a.__add__(b) and return a NEW Value wrapping the sum. Same for __mul__.
- The connective tissue: a constructor argument for the children (a tuple), stored in the class as a set called _prev (he thinks the set was for efficiency), and _op, a string such as "+" or "*" saying which operation produced the value (empty for leaves). Now d._prev shows the two Values it came from and d._op the operation.
- Visualisation: draw_dot, using the Graphviz library; a trace helper walks all nodes and edges. IMPORTANT detail: the round operation nodes are fake nodes created only inside draw_dot for readability; the only real Value objects are the rectangles.
- Labels are added by hand (a, b, c, e, d, f, L). The graph is extended: e = a*b, d = e + c, f = -2.0, L = d*f, so L = -8. This is the forward pass.
- keywords: wrapper (repr), children, prev, op, draw_dot, Graphviz, fake nodes, labels, forward pass, negative eight

## L5 Manual backpropagation on L = (a*b + c) * f
- Goal: for every node, the derivative of L with respect to it. Every Value gets a grad attribute starting at 0.0, meaning "no effect on the output" (changing it would not change the loss). In a network the leaves a, b, c, f stand for weights and data; the weights get updated with the gradient, the data is fixed so its gradient is not useful.
- Base case: L.grad = 1 (change L by h and L changes by h). He wraps a numerical check in a throwaway function (called lol) so the notebook's global variables stay clean; this is an "inline gradient check".
- dL/dd = f = -2 and dL/df = d = 4; he derives it from the definition of the derivative (d*f product, the d*f terms cancel, h*f/h leaves f), then checks numerically.
- The crux ("if you understand this node you understand all of backprop"): dL/dc. We know how L depends on d, and how d depends on c; the plus node knows only its own inputs (it does not know the rest of the graph): its LOCAL derivative with respect to c is 1 and with respect to e is 1 (derived from the definition: c cancels).
- Chain rule, his version: if z depends on y and y depends on x, dz/dx = dz/dy times dy/dx. Intuition he likes: a car is twice as fast as a bicycle and the bicycle is four times as fast as a walking man, so the car is eight times as fast as the man: you multiply the rates.
- So dL/dc = dL/dd times dd/dc = -2 times 1 = -2; the plus node simply ROUTES the gradient to both children, so c.grad = -2 and e.grad = -2 (he describes the signal flowing backward through the graph). Checked numerically.
- Times node: the local derivative with respect to one input is the OTHER input's value. a.grad = e.grad times b = -2 times -3 = 6; b.grad = e.grad times a = -2 times 2 = -4. Checked numerically (up to float oddness).
- Summary in his words: backprop is just a recursive application of the chain rule backward through the graph, multiplying the local derivatives as you go.
- keywords: crux, local derivative, chain rule, car, bicycle, man, routes, gradient check, lol, plus node, times node

## L6 A first optimisation step (preview)
- To make L go UP, move each leaf (a, b, c, f) a small step in the direction of its gradient, then redo the forward pass. L becomes less negative: he reads it as about -7 (with a step of 0.01 it is about -7.29). He calls this one step of an optimisation that will later be run in a loop.
- keywords: nudge our inputs, direction of the gradient, step size, negative seven

## L7 A neuron
- Biological metaphor, deliberately simple: inputs x arrive through synapses with weights w (they multiply: w times x), the cell body sums all w times x and adds a bias (the neuron's innate "trigger happiness", it can make it more or less eager regardless of input), then an activation function squashes the result: sigmoid or tanh. He uses tanh.
- np.tanh plotted: 0 maps to 0, large positive inputs flatten smoothly toward 1, large negative toward -1.
- Example neuron: x1, x2 (inputs), w1, w2 (weights), bias b; built in small steps with labels x1w1, x2w2, their sum, n (the raw cell-body value), then o = n.tanh().
- tanh cannot be built from plus and times alone (needs exponentiation). He chooses NOT to add exp yet and implements tanh as ONE operation, to make a point: operations can sit at any level of abstraction; only the local derivative matters.
- With bias 8, n = 2 and tanh gives about 0.96 (in the flat tail). Then he changes the bias to 6.8813735870195432 on purpose so the numbers come out nice: n about 0.88, o about 0.7071.
- keywords: synapses, cell body, trigger happy, squashing, activation function, 6.88, nice numbers

## L8 Manual backprop through the neuron
- o.grad = 1. Local derivative of tanh: 1 - tanh(n)^2 = 1 - o^2; here that is exactly 0.5, "conveniently". So n.grad = 0.5.
- Plus nodes route 0.5 to both children, twice (to the sum and the bias, then to x1w1 and x2w2). "Pluses are my favourite to backpropagate through."
- Times nodes: x2.grad = w2 times 0.5 = 0.5; w2.grad = x2 times 0.5 = 0 because x2 is 0; x1.grad = w1 times 0.5 = -1.5; w1.grad = x1 times 0.5 = 1.0.
- Interpretation: a gradient is the influence on the final output. w2.grad = 0 is the right answer: x2 is 0 so wiggling w2 changes nothing. To make this neuron's output increase, w1 should go up.
- Reminder: this is one small neuron inside a bigger puzzle; eventually a loss measures the accuracy and we backpropagate from that.
- keywords: 0.5, one minus tanh squared, distributor, x2 times zero, w1 should go up

## L9 Automating the backward pass
- Each Value gets a function _backward (default: does nothing, right for leaves). Created inside add, mul and tanh as a closure: add: self.grad += 1.0 times out.grad and the same for other; mul: self.grad += other.data times out.grad and other.grad += self.data times out.grad; tanh: self.grad += (1 - t^2) times out.grad. (He first writes = and fixes it to += later, L10.)
- He leaves a funny bug in: storing the function versus CALLING it ("NoneType is not callable"). Then calls each node's _backward by hand in the right order to show it works.
- Why order matters: never call a node's backward before every node after it has pushed its gradient into it. Needed: a topological sort = a layout of a directed acyclic graph where all edges go one way, left to right; the same graph has several valid orders.
- Implementation: a visited set; build_topo(node): if not visited, mark it, recurse into all children, then append the node (so a node appears only after all its children). Start at the output; the list ends with the output. Then: set output.grad = 1 (base case), walk the list in REVERSED order calling _backward. Finally wrapped as the method Value.backward().
- keywords: closure, underscore backward, empty function, topological sort, left to right, DAG, visited, reversed

## L10 The bug: a node used more than once
- Simplest case: a = 3, b = a + a. Forward gives 6 but a.grad comes out as 1, while it should be 2 (derivative of a + a is 2). Reason: in __add__ self and other are the same object, so the second "= 1.0" overwrites the first.
- A bigger case: a and b feed both d = a*b and e = a + b, then f = d*e; the gradients are wrong because the later backward of d overwrites the deposit that e already made on a and b. Rule: any variable used more than once triggers it.
- Fix: accumulate with += (multivariable chain rule: contributions from different paths ADD). Works because every grad starts at 0.
- Not stated: the values of a and b in the second example (the notebook has them).
- keywords: a plus a, overwrite, used more than once, accumulate, plus equals, multivariate

## L11 More operations, and the level of abstraction
- Plain numbers: a + 1 fails ("int has no attribute data"); fix: in add and mul, if other is not a Value, wrap it in Value(other).
- 2 * a fails even after that: Python first tries int.__mul__, fails, and then falls back to a.__rmul__(2); defining __rmul__ as "swap the operands and call a * 2" fixes it.
- exp: out = Value(math.exp(x)); local derivative of e^x is e^x, which is already stored in out.data, so self.grad += out.data times out.grad.
- Division: a / b = a * b**(-1). So he implements power with a constant exponent k (only int or float, asserted; a Value exponent would need a different derivative): local derivative k times x^(k-1) (the power rule), times out.grad. Subtraction: a - b = a + (-b), and negation is multiplication by -1.
- tanh rebuilt from exp: e = (2n).exp(); o = (e - 1) / (e + 1). The graph is much longer but forward value and gradients are the SAME (x2 0.5, w2 0, x1 -1.5, w1 1).
- Lesson he repeats: it is entirely up to you at what level you write operations (tiny plus or a composite tanh); if you can write the forward pass and the local gradient, you can chain it and continue backprop.
- keywords: has no attribute data, rmul, fallback, exponentiation, power rule, division, negation, abstraction, composite

## L12 The same thing in PyTorch
- PyTorch is built on tensors: n-dimensional arrays of scalars (he shows a 2 by 3 example and its shape). He uses single-element tensors for the neuron.
- .double() because PyTorch defaults to float32 while Python floats are float64. requires_grad = True must be set explicitly on leaf tensors (default False "for efficiency", since inputs usually do not need gradients).
- Then the same arithmetic, torch.tanh, o.backward(); .item() pulls a Python number out of a one-element tensor. Forward 0.7071; grads x2 0.5, w2 0, x1 -1.5, w1 1: PyTorch agrees. API is very close; PyTorch's real advantage is doing many operations in parallel.
- keywords: tensors, double, float32, requires_grad, item, shape, parallel

## L13 The neural network library
- Neuron(nin): one random weight per input drawn between -1 and 1, one random bias; calling it computes sum(w_i * x_i) + b, then tanh, using zip over weights and inputs and sum with the bias as its start value.
- Layer(nin, nout): a list of nout independent neurons, all fully connected to the same inputs; calling it evaluates them independently.
- MLP(nin, nouts): takes a LIST of layer sizes, builds layers from consecutive pairs, calls them in sequence. Example: 3 inputs, two layers of 4, one output. A layer with one neuron returns that single value instead of a list. draw_dot of the output is a large graph.
- The API deliberately matches PyTorch's modules.
- keywords: neuron, layer, multilayer perceptron, zip, nouts, random between negative one and one, sequentially

## L14 Dataset, loss, gradient descent
- Four examples with targets 1.0, -1.0, -1.0, 1.0: a tiny binary classifier. First predictions (random weights, his run): about 0.91, 0.88, 0.8, 0.8: the first should go up, the others down...
- Loss: ONE number measuring performance; low is good. For every example (prediction - target)^2 (squaring removes the sign; zero exactly when equal); summed over the four (he calls it "mean squared error" but adds them up). Initial loss around 7 (7.12 in one run).
- loss.backward() fills every parameter's grad; a negative gradient means increasing that weight lowers the loss. Gradients also appear on the input data but are not useful (data is fixed).
- parameters(): neuron returns its weights plus the bias; layer and MLP gather them with nested list comprehensions (PyTorch also has parameters()). Total for this MLP: 41 parameters.
- Update: p.data += -step * p.grad. Sign logic: the gradient points toward INCREASING loss, so go the opposite way. Run by run (his numbers, step 0.01): loss 4.84, 4.36, 3.9, 3.66, 3.47 ... The loop is forward, backward, update, repeat = gradient descent.
- Larger step: loss 0.31, then 0.04, then a too-big step: it overshoots, briefly "explodes", and by luck lands in a very good spot (around 1e-9). The learning rate is a "subtle art": too low is slow, too high is unstable and can even blow up the loss; we only know the local slope, so a big step may land somewhere very different.
- Proper training loop over about 20 steps with a rate between 0.01 (too small) and 0.1 (dangerously high). Not stated: the exact chosen rate and the example inputs (the notebook has them).
- The BUG he leaves in on camera: forgetting to zero the grads before backward. Because backward uses +=, gradients pile up from step to step, which acted like a massive step size; it only "worked" because the problem is tiny. Fix: set p.grad = 0.0 for every parameter before backward. Descent is then slower but correct. He calls it the third most common neural-net mistake from his tweet.
- keywords: loss, squared, mean squared error, 41, gradient descent, step size, overstep, explode, subtle art, zero grad, forgot, massive step size

## L15 Summary and scale
- A neural net is a fairly simple mathematical expression taking data and weights; a loss function measures how well predictions match targets; backprop gives the gradient; gradient descent iterates many times to lower the loss. "A blob of neural tissue" that you can make do arbitrary things by choosing the loss.
- 41 parameters here, billions to almost trillions in practice. GPT is trained on internet text to predict the next word, with hundreds of billions of parameters, but it is the same principles. Real training differs in details: more sophisticated stochastic updates, and cross-entropy loss for predicting the next token.
- keywords: blob, neural tissue, trillions, GPT, next word, cross entropy, stochastic

## L16 Walkthrough of the micrograd repo
- engine.py: Value with data, grad, backward, _prev, _op; add, multiply, power by a scalar, relu (tanh was not in the repo at the time). relu vs tanh vs sigmoid: roughly equivalent in MLPs; he used tanh because it is smoother and stresses local gradients a bit more.
- nn.py: a Module base class (matches PyTorch's nn.Module, includes zero_grad), then Neuron, Layer, MLP. test file: builds the same expressions in micrograd and in PyTorch and checks forward and backward agree.
- demo.ipynb: a bigger binary classification (red and blue 2D points) with a bigger MLP; batching (random subset of the data per step instead of the whole set); a max-margin loss (others: binary cross-entropy); L2 regularisation (controls overfitting); learning-rate decay (high at first, shrinking as training settles); the decision surface separating red and blue.
- keywords: engine, relu, module, zero_grad, test, demo, batch, max margin, regularization, learning rate decay, decision surface

## L17 Real PyTorch internals
- He could not find tanh's backward in PyTorch after about 15 minutes (thousands of hits, hundreds of files). Found the CPU and CUDA kernels: heavy because of complex numbers and special dtypes like bfloat16, but at the core a line that multiplies the incoming grad by one minus the output squared: the same formula as micrograd's.
- Adding a custom operation: subclass torch.autograd.Function, write forward and backward (example: a Legendre polynomial of degree 3); then it is a "lego block" PyTorch can backpropagate through.
- keywords: kernel, cpu, cuda, bfloat16, Function, Legendre, lego

## L18 Sign-off
- He thanks the viewers and mentions links, a discussion group and a possible follow-up. Anything after "see you later" in the raw transcript is outtakes: ignore it.

## Ideas the lecture itself gives for "what if" and "expert corner" material
- sign prediction before computing (L2, L3, L8); a leaf whose neighbour is zero has zero gradient (L8); different graph shapes for the same maths (L11: tanh in one node vs many); learning-rate too low, right, too high (L14); gradient accumulation bug as an experiment (L10, L14); relu vs tanh vs sigmoid (L16); batching, L2 regularisation, learning-rate decay, cross-entropy (L15, L16); real frameworks store one hand-written backward per operation (L17).

## Things this transcript never states (read the notebooks)
The exact h values, the four example input rows, the example input of the MLP forward pass, the exact learning rate and number of steps of the training loop, any random seed, and the values of a and b in the second accumulation-bug example.
