# coding: utf-8

import math
from dataclasses import dataclass
from typing import Dict, Optional, Union

from ._version import version as _version

__all__ = ("UDDSketch",)
__version__ = _version


@dataclass
class _Entry:
    count: int
    next_bucket: Optional[int]


class _Store:
    def __init__(self) -> None:
        self._store: Dict[int, _Entry] = {}
        self._head: Optional[int] = None
        self._tail: Optional[int] = None
        self._count: int = 0

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
        self, count: Union[int, float], lower: bool = True
    ) -> int:
        assert self._tail is not None  # nosec for mypy
        next_ = self._head
        running_count = 0

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

    def compact(self):
        return


def _value_to_bucket(value: float, gamma: float) -> int:
    value = math.fabs(value)
    return math.ceil(math.log(value, gamma))


def _bucket_to_value(alpha: float, gamma: float, bucket: int) -> float:
    return (1.0 + alpha) * gamma ** (bucket - 1)


def _compact_bucket(bucket):
    return (bucket + 1 if bucket > 0 else bucket) // 2


class UDDSketch:
    def __init__(
        self, max_buckets: int = 256, initial_error: float = 0.01
    ) -> None:
        self._max_buckets: int = max_buckets
        self._initial_error: float = initial_error
        self._alpha: float = initial_error
        self._gamma: float = (1.0 + initial_error) / (1.0 - initial_error)
        self._compactions = 0

        self._values_sum: float = 0
        self._min = float("inf")
        self._max = float("-inf")
        # storage
        self._neg_storage = _Store()
        self._zero_counts = 0
        self._pos_storage = _Store()

    def min(self):
        return self._min

    def max(self):
        return self._max

    @property
    def num_values(self):
        return (
            self._neg_storage.num_values
            + self._pos_storage.num_values
            + self._zero_counts
        )

    def add(self, value: float, count: int = 1) -> None:
        self._values_sum += value * count
        self._min = min(self._min, value)
        self._max = max(self._max, value)

        if value > 0.0:
            bucket = _value_to_bucket(value, self._gamma)
            self._pos_storage.add_to_bucket(bucket, count=count)
        elif value < 0.0:
            bucket = _value_to_bucket(value, self._gamma)
            self._neg_storage.add_to_bucket(bucket, count=count)
        else:
            self._zero_counts += count

    @property
    def num_compactions(self) -> int:
        return self._compactions

    def max_error(self) -> float:
        return self._initial_error

    def quantile(self, q: float) -> float:
        if not (q >= 0 and q <= 1):
            raise ValueError("Quantile should be value from 0 to 1.")
        rank = q * (self.num_values)
        val: float

        if self._neg_storage.num_values > rank:
            reversed_rank = self._neg_storage.num_values - rank
            bucket = self._neg_storage.bucket_at_count(
                reversed_rank, lower=False
            )
            val = -_bucket_to_value(self._alpha, self._gamma, bucket)
        elif self._neg_storage.num_values + self._zero_counts > rank:
            val = 0.0
        else:
            pos_count = rank - (
                self._neg_storage.num_values + self._zero_counts
            )
            bucket = self._pos_storage.bucket_at_count(pos_count, lower=True)
            val = _bucket_to_value(self._alpha, self._gamma, bucket)
        return val

    def median(self) -> float:
        return self.quantile(0.5)

    def mean(self) -> float:
        return self._values_sum / self.num_values

    def std(self) -> float:
        return self._values_sum / self.num_values

    def merge(self, other: "UDDSketch") -> "UDDSketch":
        return self
