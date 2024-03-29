import math
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from ._version import version as _version

__all__ = ("UDDSketch",)
__version__ = _version


def _compact_bucket(bucket: int) -> int:
    return math.ceil(bucket / 2.0)


@dataclass
class _Entry:
    count: int
    next_bucket: Optional[int]


Centroid = Tuple[float, int]


class _Store:
    def __init__(self) -> None:
        self._store: Dict[int, _Entry] = {}
        self._head: Optional[int] = None
        self._tail: Optional[int] = None
        self._count: int = 0

    def __repr__(self) -> str:
        klass = self.__class__.__name__
        return f"<{klass} {self.buckets()}>"

    def size(self) -> int:
        return len(self._store)

    def buckets(self) -> List[Tuple[int, int]]:
        bucket_counts = sorted(self._store.items(), key=lambda v: v[0])
        return [(k, v.count) for k, v in bucket_counts]

    @property
    def num_values(self) -> int:
        return self._count

    def add_to_bucket(self, bucket: int, count: int = 1) -> None:
        self._count += count
        next_ = self._head
        if not self._store:
            self._store[bucket] = _Entry(count, None)
            self._head = bucket
            self._tail = bucket

        elif bucket in self._store:
            self._store[bucket].count += count
        else:
            if self._head is not None and bucket < self._head:
                self._store[bucket] = _Entry(count, self._head)
                self._head = bucket
            elif self._tail is not None and bucket > self._tail:
                self._store[self._tail].next_bucket = bucket
                self._store[bucket] = _Entry(count, None)
                self._tail = bucket
            else:
                prev = next_
                while next_ is not None and bucket > next_:
                    prev = next_
                    next_ = self._store[next_].next_bucket

                assert prev is not None  # nosec for mypy
                self._store[prev].next_bucket = bucket
                self._store[bucket] = _Entry(count, next_)
                if next_ is None:
                    self._tail = bucket

    def bucket_at_count(
        self, count: Union[int, float], *, lower: bool = True
    ) -> int:
        if not self._store:
            raise RuntimeError("Bucket store is empty")

        assert self._tail is not None  # nosec for mypy
        assert self._head is not None  # nosec for mypy

        next_: Optional[int] = self._head
        running_count: int = 0

        if count >= self.num_values:
            return self._tail

        while next_ is not None:
            entry = self._store[next_]
            running_count += entry.count
            if lower and running_count >= count:
                return next_
            elif not lower and running_count > count:
                return next_

            next_ = entry.next_bucket

        return self._tail

    def compact(self) -> None:
        if self._head is None:
            return

        old_store = self._store
        self._store = {}
        self._head = None
        self._tail = None
        self._count = 0
        for old_bucket, entry in old_store.items():
            self.add_to_bucket(_compact_bucket(old_bucket), count=entry.count)


def _value_to_bucket(value: float, gamma: float) -> int:
    value = math.fabs(value)
    return math.ceil(math.log(value, gamma))


def _bucket_to_value(alpha: float, gamma: float, bucket: int) -> float:
    return (1.0 + alpha) * gamma ** (bucket - 1)


class UDDSketch:
    def __init__(
        self, max_buckets: Optional[int] = None, initial_error: float = 0.01
    ) -> None:
        self._max_buckets: Optional[int] = max_buckets
        self._initial_error: float = initial_error
        self._alpha: float = initial_error
        self._gamma: float = (1.0 + initial_error) / (1.0 - initial_error)
        self._compactions: int = 0

        # storage
        self._neg_storage: _Store = _Store()
        self._zero_counts: int = 0
        self._pos_storage: _Store = _Store()

    @property
    def initial_error(self) -> float:
        return self._initial_error

    @property
    def max_buckets(self) -> Optional[int]:
        return self._max_buckets

    @property
    def num_values(self) -> int:
        return (
            self._neg_storage.num_values
            + self._pos_storage.num_values
            + self._zero_counts
        )

    @property
    def num_compactions(self) -> int:
        return self._compactions

    @property
    def max_error(self) -> float:
        return self._alpha

    @property
    def num_buckets(self) -> int:
        num_buckets = self._neg_storage.size() + self._pos_storage.size()
        if self._zero_counts != 0:
            num_buckets += 1
        return num_buckets

    def __repr__(self) -> str:
        klass = self.__class__.__name__
        t = (
            f"<{klass} initial_error={self.initial_error} "
            f"max_buckets={self.max_buckets} "
            f"num_values={self.num_values}>"
        )
        return t

    def buckets(self) -> List[Centroid]:
        neg = [
            (-_bucket_to_value(self._alpha, self._gamma, b), c)
            for b, c in self._neg_storage.buckets()
        ]
        zero = [(0.0, self._zero_counts)] if self._zero_counts else []
        pos = [
            (_bucket_to_value(self._alpha, self._gamma, b), c)
            for b, c in self._pos_storage.buckets()
        ]
        return neg + zero + pos

    def add(self, value: float, count: int = 1) -> None:
        if count <= 0:
            return

        if value > 0.0:
            bucket = _value_to_bucket(value, self._gamma)
            self._pos_storage.add_to_bucket(bucket, count=count)
        elif value < 0.0:
            bucket = _value_to_bucket(value, self._gamma)
            self._neg_storage.add_to_bucket(bucket, count=count)
        else:
            self._zero_counts += count

        if self._max_buckets is None:
            return

        while self.num_buckets > self._max_buckets:
            self.compact()

    def quantile(self, q: float) -> float:
        if not (q >= 0 and q <= 1):
            raise ValueError("Quantile should be value from 0 to 1.")

        if not self.num_values:
            return float("nan")

        rank = q * (self.num_values - 1)
        val: float

        if self._neg_storage.num_values > rank:
            reversed_rank = self._neg_storage.num_values - rank
            bucket = self._neg_storage.bucket_at_count(
                reversed_rank, lower=True
            )
            val = -_bucket_to_value(self._alpha, self._gamma, bucket)
        elif self._neg_storage.num_values + self._zero_counts > rank:
            val = 0.0
        else:
            pos_count = rank - (
                self._neg_storage.num_values + self._zero_counts
            )
            bucket = self._pos_storage.bucket_at_count(pos_count, lower=False)
            val = _bucket_to_value(self._alpha, self._gamma, bucket)
        return val

    def median(self) -> float:
        return self.quantile(0.5)

    def merge(self, other: "UDDSketch") -> "UDDSketch":
        if self._initial_error != other.initial_error:
            msg = (
                f"Expected initial_error is {self._initial_error} "
                f"got {other.initial_error}"
            )
            raise ValueError(msg)

        if self._max_buckets != other.max_buckets:
            msg = (
                f"Expected max_buckets is {self._max_buckets} "
                f"got {other.max_buckets}"
            )
            raise ValueError(msg)

        if other.num_values == 0:
            return self

        if self.num_values == 0:
            self._neg_storage = deepcopy(other._neg_storage)
            self._zero_counts = other._zero_counts
            self._pos_storage = deepcopy(other._pos_storage)
            return self

        if self.num_compactions < other.num_compactions:
            for _ in range(self.num_compactions, other.num_compactions):
                self.compact()

        if other.num_compactions < self.num_compactions:
            other = deepcopy(other)
            for _ in range(other.num_compactions, self.num_compactions):
                other.compact()

        for b, c in other._neg_storage.buckets():
            self._neg_storage.add_to_bucket(b, count=c)

        self._zero_counts += other._zero_counts

        for b, c in other._pos_storage.buckets():
            self._pos_storage.add_to_bucket(b, count=c)
        return self

    def compact(self) -> None:
        self._neg_storage.compact()
        self._pos_storage.compact()
        self._gamma *= self._gamma
        self._alpha = 2.0 * self._alpha / (1.0 + self._alpha**2)
        self._compactions += 1
