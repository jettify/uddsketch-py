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
        [1.0 * v for v in range(0, 1000)],
        [-v for v in range(0, 1000)],
        [1.0 * v for v in range(-100, 100)],
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
    expected = "<UDDSketch initial_error=0.1 max_buckets=128 num_values=3>"
    assert repr(hist) == expected


def test_weighted_sample(arr_w, alpha):
    weights = [v[1] for v in arr_w]

    hist = UDDSketch(initial_error=alpha)
    [hist.add(v, c) for v, c in arr_w]

    assert hist.num_values == np.sum(weights)


def test_quantile_with_merge(arr, alpha, quantile, num_compactions):
    hist1 = UDDSketch(initial_error=alpha)
    hist2 = UDDSketch(initial_error=alpha)
    mid = len(arr) // 2

    [hist1.add(v) for v in arr[mid:]]
    [hist2.add(v) for v in arr[:mid]]

    for _ in range(num_compactions):
        hist1.compact()

    hist1.merge(hist2)

    expected = np.quantile(arr, quantile, method="lower")
    q = hist1.quantile(quantile)
    eps = np.finfo(float).eps
    a = (expected, q)
    assert abs(expected - q) <= (hist1.max_error * abs(expected) + eps), a


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
    assert abs(expected - q) <= (hist.max_error * abs(expected) + eps)


@pytest.mark.parametrize("value", [0.0001, 1.1, 20.0, 300.0, 4000.0, 50000.0])
def test_value_to_bucket_bucket_to_value(alpha, value):
    gamma: float = (1.0 + alpha) / (1.0 - alpha)

    b = _value_to_bucket(value, gamma)
    val = _bucket_to_value(alpha, gamma, b)
    assert val == pytest.approx(value, rel=alpha)


def test_empty():
    hist = UDDSketch(initial_error=0.1)
    assert hist.num_values == 0
    assert hist.num_values == 0
    assert math.isnan(hist.median())
    assert math.isnan(hist.quantile(0.1))

    hist.add(42.0, 0)
    assert hist.num_values == 0


def test_errors():
    hist = UDDSketch(initial_error=0.1)
    hist.add(-1.0)
    hist.add(0.0)
    hist.add(1.0)

    with pytest.raises(ValueError):
        hist.quantile(-1)

    with pytest.raises(ValueError):
        hist.quantile(2)

    assert hist.median() == pytest.approx(0.0)


def test_buckets():
    hist = UDDSketch(initial_error=0.1)
    hist.add(-1.0)
    assert hist.buckets() == [(-0.9, 1)]
    assert hist.num_buckets == 1

    hist.add(0.0)
    assert hist.buckets() == [(-0.9, 1), (0.0, 1)]
    assert hist.num_buckets == 2
    hist.add(1.0)
    assert hist.buckets() == [(-0.9, 1), (0.0, 1), (0.9, 1)]
    assert hist.num_buckets == 3


def test_auto_compaction(rng):
    arr = ((rng.pareto(3.0, 1000) + 1) * 2.0).tolist()
    max_buckets = 10
    hist = UDDSketch(max_buckets=10, initial_error=0.01)
    for v in arr:
        hist.add(v)
        assert hist.num_buckets <= max_buckets
    assert hist.num_compactions == 4


def test_merge_error():
    hist1 = UDDSketch(initial_error=0.1)
    hist2 = UDDSketch(initial_error=0.2)
    with pytest.raises(ValueError):
        hist1.merge(hist2)

    hist1 = UDDSketch(initial_error=0.1, max_buckets=128)
    hist2 = UDDSketch(initial_error=0.1, max_buckets=256)
    with pytest.raises(ValueError):
        hist1.merge(hist2)


def test_merge_same_compaction_level():
    hist1 = UDDSketch(initial_error=0.1)
    hist1.add(-1.0)
    hist1.add(0.0)
    hist1.add(1.0)

    hist2 = UDDSketch(initial_error=0.1)
    hist2.add(-2.0)
    hist2.add(0.0)
    hist2.add(2.0)
    hist2.compact()
    expected_count = hist1.num_values + hist2.num_values

    result = hist1.merge(hist2)
    assert hist1.num_values == expected_count
    assert result is hist1


def test_one_empty():
    hist1 = UDDSketch(initial_error=0.1)
    hist2 = UDDSketch(initial_error=0.1)

    hist1.add(1.0)
    assert hist1.num_values == 1
    hist1.merge(hist2)
    assert hist1.num_values == 1

    hist1 = UDDSketch(initial_error=0.1)
    hist2 = UDDSketch(initial_error=0.1)

    hist2.add(1.0)

    hist1.merge(hist2)

    assert hist1.num_values == 1
