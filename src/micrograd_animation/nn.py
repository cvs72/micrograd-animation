"""Neuron, Layer and MLP built on the micrograd-style Value class (as in the lecture)."""
import random

from micrograd_animation.engine import Value


class Neuron:
    def __init__(self, nin, rng=None, const=None):
        """rng: a random.Random (seeded); const: fixed weight with bias 0 (symmetric start)."""
        rng = rng or random
        if const is None:
            self.w = [Value(rng.uniform(-1, 1)) for _ in range(nin)]
            self.b = Value(rng.uniform(-1, 1))
        else:
            self.w = [Value(const) for _ in range(nin)]
            self.b = Value(0.0)

    def __call__(self, x):
        act = sum((wi * xi for wi, xi in zip(self.w, x)), self.b)
        return act.tanh()

    def parameters(self):
        return self.w + [self.b]


class Layer:
    def __init__(self, nin, nout, rng=None, const=None):
        self.neurons = [Neuron(nin, rng, const) for _ in range(nout)]

    def __call__(self, x):
        outs = [n(x) for n in self.neurons]
        return outs[0] if len(outs) == 1 else outs

    def parameters(self):
        return [p for neuron in self.neurons for p in neuron.parameters()]


class MLP:
    def __init__(self, nin, nouts, seed=None, const=None):
        rng = random.Random(seed) if seed is not None else None
        sz = [nin] + nouts
        self.layers = [Layer(sz[i], sz[i + 1], rng, const) for i in range(len(nouts))]

    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]
