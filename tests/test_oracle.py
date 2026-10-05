"""Fixed oracle. The agent must make its Value class pass this; it may not edit this file."""
import importlib
import math
import pathlib
import random

root = pathlib.Path(__file__).resolve().parents[1]
pkgs = sorted(p.parent.name for p in (root / "src").glob("*/__init__.py"))
assert pkgs, "expected a package under src/"
Value = importlib.import_module(f"{pkgs[0]}.engine").Value


def test_readme_example():
    # The example from the micrograd README, with its documented results.
    a = Value(-4.0)
    b = Value(2.0)
    c = a + b
    d = a * b + b**3
    c += c + 1
    c += 1 + c + (-a)
    d += d * 2 + (b + a).relu()
    d += 3 * d + (b - a).relu()
    e = c - d
    f = e**2
    g = f / 2.0
    g += 10.0 / f
    g.backward()
    assert round(g.data, 4) == 24.7041
    assert round(a.grad, 4) == 138.8338
    assert round(b.grad, 4) == 645.5773


def test_gradients_accumulate_when_a_node_is_reused():
    a = Value(3.0)
    b = a + a
    b.backward()
    assert a.grad == 2.0
    x = Value(2.0)
    y = x * x
    y.backward()
    assert x.grad == 4.0


def _expr(v):
    x, w, b = v
    n = x * w + b
    return (n.tanh() * 2 + (n * n).relu() - (x / (w * w + 1.5)) + (b * 0.5).exp()) ** 2


def test_gradients_match_numerical_derivative():
    rng = random.Random(0)
    for _ in range(25):
        vals = [rng.uniform(-1.5, 1.5) for _ in range(3)]
        leaves = [Value(v) for v in vals]
        out = _expr(leaves)
        out.backward()
        for i, leaf in enumerate(leaves):
            h = 1e-6
            hi = [Value(v + (h if j == i else 0)) for j, v in enumerate(vals)]
            lo = [Value(v - (h if j == i else 0)) for j, v in enumerate(vals)]
            num = (_expr(hi).data - _expr(lo).data) / (2 * h)
            assert math.isclose(leaf.grad, num, rel_tol=1e-4, abs_tol=1e-5)
