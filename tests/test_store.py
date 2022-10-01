import pytest

from uddsketch import _Store


def test_basic():
    s = _Store()
    s.add_to_bucket(2)
    assert s._head == 2
    assert s._tail == 2

    s.add_to_bucket(3)
    assert s._head == 2
    assert s._tail == 3

    s.add_to_bucket(4)
    assert s._head == 2
    assert s._tail == 4

    s.add_to_bucket(1)
    assert s._head == 1
    assert s._tail == 4


def test_bucket_at_count():
    s = _Store()
    s.add_to_bucket(1)
    s.add_to_bucket(2)
    s.add_to_bucket(3)
    s.add_to_bucket(4)
    s.add_to_bucket(5)

    b = s.bucket_at_count(3)
    assert b == 3

    b = s.bucket_at_count(1)
    assert b == 1

    b = s.bucket_at_count(5)
    assert b == 5

    b = s.bucket_at_count(15)
    assert b == 5

    b = s.bucket_at_count(0)
    assert b == 1


def test_compaction():
    s = _Store()
    s.add_to_bucket(1)
    s.add_to_bucket(2)
    s.add_to_bucket(3)
    s.add_to_bucket(4)
    s.add_to_bucket(5)
    s.add_to_bucket(6)
    s.add_to_bucket(9)
    s.add_to_bucket(11)
    assert s.size() == 8
    orig_num_values = s.num_values

    b = s.bucket_at_count(1)
    assert b == 1
    b = s.bucket_at_count(15)
    assert b == 11
    s.compact()
    assert s.num_values == orig_num_values
    assert s.size() == 5

    b = s.bucket_at_count(15)
    assert b == 6


def test_exceptions():
    s = _Store()
    with pytest.raises(RuntimeError):
        s.bucket_at_count(10)
