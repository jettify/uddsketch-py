uddsketch
=============
.. image:: https://github.com/jettify/uddsketch-py/workflows/CI/badge.svg
   :target: https://github.com/jettify/uddsketch-py/actions?query=workflow%3ACI
   :alt: GitHub Actions status for master branch
.. image:: https://codecov.io/gh/jettify/uddsketch-py/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jettify/uddsketch-py
.. image:: https://img.shields.io/pypi/pyversions/uddsketch.svg
    :target: https://pypi.org/project/uddsketch
.. image:: https://img.shields.io/pypi/v/uddsketch.svg
    :target: https://pypi.python.org/pypi/uddsketch
..
.. image:: https://readthedocs.org/projects/uddsketch/badge/?version=latest
    :target: https://uddsketch.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


**uddsketch** data structure.


Simple example
--------------

.. code:: python

    from uddsketch import UDDSketch

    hist = UDDSketch(initial_error=0.01)

    for i in range(0, 100):
        hist.add(0.1 * i)
    q = hist.quantile(0.5)
    print('quantile: {}'.format(q))


Installation
------------
Installation process is simple, just::

    $ pip install uddsketch
