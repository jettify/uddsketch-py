import pytest

from uddsketch import UDDSketch


def test_ctor():
    hist = UDDSketch()
    assert hist
