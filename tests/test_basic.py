import numpy as np
import pytest

from uddsketch import UDDSketch, _bucket_to_value, _value_to_bucket


@pytest.fixture(
    params=[
        [1, 2, 3, 4, 5],
        [0, 0, 0, 0, 0],
        [-1, -2, -3, -4, -5],
        [0.01 * v for v in range(0, 1000)],
        [v for v in range(0, 1000)],
        [-v for v in range(0, 1000)],
        [v for v in range(-100, 100)],
        [0.01 * v for v in range(-100, 100)],
    ],
    ids=lambda v: str(v[:5]),
)
def arr(request):
    return request.param


@pytest.fixture(params=[0.1, 0.01, 0.001])
def alpha(request):
    return request.param


@pytest.fixture(params=[0.99, 0.01])
def quantile(request):
    return request.param


def test_quantile(arr, alpha, quantile):
    hist = UDDSketch(initial_error=alpha)
    [hist.add(v) for v in arr]

    expected = np.quantile(arr, quantile, method="closest_observation")
    q = hist.quantile(quantile)
    eps = np.finfo(float).eps
    assert abs(q - expected) <= (alpha * abs(expected) + eps), (expected, q)

    assert hist.mean() == pytest.approx(np.mean(arr))
    assert hist.min() == min(arr)
    assert hist.max() == max(arr)
    assert hist.num_values == len(arr)


@pytest.mark.parametrize("value", [0.0001, 1.1, 20.0, 300.0, 4000.0, 50000.0])
def test_value_to_bucket_bucket_to_value(alpha, value):
    gamma: float = (1.0 + alpha) / (1.0 - alpha)

    b = _value_to_bucket(value, gamma)
    val = _bucket_to_value(alpha, gamma, b)
    assert val == pytest.approx(value, rel=alpha)
