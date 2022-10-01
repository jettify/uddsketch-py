# coding: utf-8

import math
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Union

from ._version import version as _version

__all__ = ("UDDSketch",)
__version__ = _version


def _compact_bucket(bucket: int) -> int:
    return (bucket + 1 if bucket > 0 else bucket) // 2


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

    def size(self) -> int:
        return len(self._store)

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

    def compact(
        self, compact_fn: Callable[[int], int] = _compact_bucket
    ) -> None:
        if self._head is None:
            return

        old_store = self._store
        self._store = {}
        self._head = None
        self._tail = None
        self._count = 0
        for old_bucket, entry in old_store.items():
            self.add_to_bucket(compact_fn(old_bucket), count=entry.count)


def _value_to_bucket(value: float, gamma: float) -> int:
    value = math.fabs(value)
    return math.ceil(math.log(value, gamma))


def _bucket_to_value(alpha: float, gamma: float, bucket: int) -> float:
    return (1.0 + alpha) * gamma ** (bucket - 1)


class UDDSketch:
    def __init__(
        self, max_buckets: int = 256, initial_error: float = 0.01
    ) -> None:
        self._max_buckets: int = max_buckets
        self._initial_error: float = initial_error
        self._alpha: float = initial_error
        self._gamma: float = (1.0 + initial_error) / (1.0 - initial_error)
        self._compactions: int = 0

        self._m: float = 0
        self._var: float = float("nan")
        self._min = float("inf")
        self._max = float("-inf")
        # storage
        self._neg_storage: _Store = _Store()
        self._zero_counts: int = 0
        self._pos_storage: _Store = _Store()

    def min(self) -> float:
        return self._min if self.num_values > 0 else float("-inf")

    def max(self) -> float:
        return self._max if self.num_values > 0 else float("inf")

    @property
    def num_values(self) -> int:
        return (
            self._neg_storage.num_values
            + self._pos_storage.num_values
            + self._zero_counts
        )

    def add(self, value: float, count: int = 1) -> None:
        # https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Online
        if count <= 0:
            return

        prev_count = self.num_values
        prev_mean = self._m
        prev_var = self._var

        new_count = prev_count + count
        self._m = (prev_mean * prev_count) / new_count + (
            value * count
        ) / new_count

        if prev_count == 0:
            self._var = 0
        else:
            self._var = prev_var + count * (value - prev_mean) * (
                value - self._m
            )

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
        return self._alpha

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

    def mean(self) -> float:
        return self._m if self.num_values else float("nan")

    def var(self) -> float:
        return self._var / self.num_values if self.num_values else float("nan")

    def merge(self, other: "UDDSketch") -> "UDDSketch":
        return self

    def compact(self) -> None:
        self._neg_storage.compact()
        self._pos_storage.compact()
        self._gamma *= self._gamma
        self._alpha = 2.0 * self._alpha / (1.0 + self._alpha**2)
        self._compactions += 1
