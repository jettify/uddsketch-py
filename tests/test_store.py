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
