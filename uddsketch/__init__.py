# coding: utf-8

from ._version import version as _version

__all__ = ("UDDSketch",)
__version__ = _version


class UDDSketch:
    def __init__(self, alpha=0.1):
        self.alpha = alpha

    def quantile(self, q: float):
        return 0.0
