# Title

Backpropagation from zero: how a neural network learns, explained three times over

# Description

Never studied calculus? This video builds backpropagation from nothing, one small number at a time. You start with a plain slope, move to several inputs, then draw the computation graph and push gradients backward with the chain rule. Next come a single tanh neuron, the topological order, the surprising reason gradients are added up, and a tiny network with 41 knobs trained by gradient descent. Every chapter has three acts: Example A uses the numbers of the original lecture, Example B changes them live so you see why results move, and the Expert corner adds what an expert would warn you about: saturation, dead ReLU, overflow, a learning rate that is too large and forgetting to zero the gradients. All numbers on screen are computed by a small micrograd-style engine, never typed in by hand. About 49 minutes in 14 chapters, with captions and written notes.

# Who this video is for

Developers who can read Python but have no calculus background, and anyone who wants to explain backpropagation to someone else using their own numbers.

# Glossary

- Scalar: a single number.
- Value: an object holding a number (data) and its gradient (grad).
- Derivative: the slope of a function, how fast the output moves when the input moves.
- Slope, secant, tangent: steepness, a line through two points of a curve, a line that just touches it.
- Partial derivative: the slope with respect to one input while the others stay fixed.
- Gradient: the vector of all partial derivatives; it points uphill.
- Computation graph: the picture of every operation and its inputs (children).
- Child: an input of a node in the graph.
- Local derivative: the slope of one operation with respect to its own inputs.
- Chain rule: multiply local derivatives along a path to get the overall slope.
- Topological order: an order where every node comes after all of its children.
- Closure: a small function that remembers the variables around it, used for each backward step.
- Gradient accumulation: adding up the contributions when a node is used more than once.
- Activation function: the squashing step after a neuron's sum.
- tanh, ReLU, sigmoid: three common activation functions.
- Saturation: a flat part of tanh where the gradient is almost zero.
- Operator overloading: making + and * work on custom objects.
- Overflow: a number too big to represent, which raises an error.
- Tensor: a block of numbers handled by one operation, used for speed.
- requires_grad, autograd: PyTorch's switch for tracking gradients and its backpropagation engine.
- Neuron, layer, MLP: weights and a bias with tanh, a row of neurons, layers called in sequence.
- Parameter: a weight or a bias, one knob that training can turn.
- Loss: one number measuring how wrong the network is.
- Learning rate: the size of one step of gradient descent.
- Gradient descent: repeatedly moving every parameter a little against its gradient.
- Overfitting: memorising the training examples instead of learning something general.

# Credit

Based on Andrej Karpathy's micrograd lecture (Neural Networks: Zero to Hero).

# Tags

backpropagation, micrograd, neural networks, gradient descent, chain rule, derivative, computation graph, tanh, autograd, PyTorch, machine learning for beginners, Manim, Andrej Karpathy, deep learning, Python
