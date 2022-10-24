import math

import numpy as np
import pytest

from uddsketch import UDDSketch, _bucket_to_value, _value_to_bucket

rs = np.random.RandomState(seed=42)


@pytest.fixture(
    params=[
        [1.0, 2.0, 3.0, 4.0, 5.0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [-1, -2, -3, -4, -5],
        [0.01 * v for v in range(0, 1000)],
        [v for v in range(0, 1000)],
        [-v for v in range(0, 1000)],
        [v for v in range(-100, 100)],
        [0.01 * v for v in range(-100, 100)],
        [0.01 * v for v in range(100, 1000)],
        rs.normal(1.0, 0.1, 1000).tolist(),
        rs.normal(10000, 10000, 1000).tolist(),
        ((rs.pareto(3.0, 1000) + 1) * 2.0).tolist(),
    ],
    ids=lambda v: str(v[:3]),
)
def arr(request):
    return request.param


@pytest.fixture(
    params=[
        [(1.0, 1), (2.0, 1), (3.0, 1), (4.0, 1), (5.0, 1)],
        [(1.0, 2), (2.0, 2), (3.0, 2), (4.0, 2), (5.0, 2)],
        [(v, 1) for v in range(0, 1000)],
        [(-v, i + 1) for i, v in enumerate(range(0, 1000))],
    ],
    ids=lambda v: str(v[:3]),
)
def arr_w(request):
    return request.param


@pytest.fixture(params=[0.1, 0.01, 0.001, 0.0001], ids=lambda v: f"alpha={v}")
def alpha(request):
    return request.param


@pytest.fixture(
    params=[0.005, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99],
    ids=lambda v: f"q={v}",
)
def quantile(request):
    return request.param


@pytest.fixture(params=[0, 3], ids=lambda v: f"n={v}")
def num_compactions(request):
    return request.param


@pytest.fixture(params=[6, 42], ids=lambda v: f"seed={v}")
def rng(request):
    return np.random.RandomState(seed=request.param)


def test_ctor():
    hist = UDDSketch(initial_error=0.1, max_buckets=128)
    hist.add(0.1)
    hist.add(0.2)
    hist.add(0.3)
    expected = "<UDDSketch min=0.1000 max=0.3000 mean=0.2000 var=0.0067>"
    assert repr(hist) == expected


def test_mean_var(arr_w, alpha):
    arr = [v[0] for v in arr_w]
    weights = [v[1] for v in arr_w]

    hist = UDDSketch(initial_error=alpha)
    [hist.add(v, c) for v, c in arr_w]

    assert hist.min() == min(arr)
    assert hist.max() == max(arr)
    assert hist.num_values == np.sum(weights)
    assert hist.mean() == pytest.approx(np.average(arr, weights=weights))
    assert hist.var() == pytest.approx(
        np.cov(arr, aweights=weights, bias=True)
    )


def test_quantile(arr, alpha, quantile, num_compactions):
    hist = UDDSketch(initial_error=alpha)
    [hist.add(v) for v in arr]
    for _ in range(num_compactions):
        hist.compact()
    assert hist.num_compactions == num_compactions

    expected = np.quantile(arr, quantile, method="lower")
    q = hist.quantile(quantile)
    eps = np.finfo(float).eps
    a = (expected, q)
    assert abs(expected - q) <= (hist.max_error() * abs(expected) + eps), a
    assert hist.mean() == pytest.approx(np.mean(arr))
    assert hist.var() == pytest.approx(np.var(arr))


def test_median(alpha, num_compactions, rng):
    arr = ((rng.pareto(3.0, 1000) + 1) * 2.0).tolist()
    hist = UDDSketch(initial_error=alpha)
    [hist.add(v) for v in arr]
    for _ in range(num_compactions):
        hist.compact()
    expected = np.quantile(arr, 0.5, method="lower")
    q = hist.quantile(0.5)
    median = hist.median()
    assert q == pytest.approx(median)
    eps = np.finfo(float).eps
    assert abs(expected - q) <= (hist.max_error() * abs(expected) + eps)


@pytest.mark.parametrize("value", [0.0001, 1.1, 20.0, 300.0, 4000.0, 50000.0])
def test_value_to_bucket_bucket_to_value(alpha, value):
    gamma: float = (1.0 + alpha) / (1.0 - alpha)

    b = _value_to_bucket(value, gamma)
    val = _bucket_to_value(alpha, gamma, b)
    assert val == pytest.approx(value, rel=alpha)


def test_empty():
    hist = UDDSketch(initial_error=0.1)
    assert hist.num_values == 0
    assert math.isinf(hist.min())
    assert math.isinf(hist.max())
    assert hist.num_values == 0
    assert math.isnan(hist.mean())
    assert math.isnan(hist.var())
    assert math.isnan(hist.median())
    assert math.isnan(hist.quantile(0.1))

    hist.add(42.0, 0)
    assert hist.num_values == 0


def test_buckets():
    hist = UDDSketch(initial_error=0.1)
    hist.add(-1.0)
    assert hist.buckets() == [(-0.9, 1)]

    hist.add(0.0)
    assert hist.buckets() == [(-0.9, 1), (0.0, 1)]
    hist.add(1.0)
    assert hist.buckets() == [(-0.9, 1), (0.0, 1), (0.9, 1)]


def test_auto_compaction(rng):
    arr = ((rng.pareto(3.0, 1000) + 1) * 2.0).tolist()
    max_buckets = 10
    hist = UDDSketch(max_buckets=10, initial_error=0.01)
    for v in arr:
        hist.add(v)
        assert hist.num_buckets() <= max_buckets
    assert hist.num_compactions == 4
