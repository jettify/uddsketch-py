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


**uddsketch** data structure for fast and accurate tracking of quantiles in
data streams. Implantation is based on ideas described in  DDSketch_ and
UDDSketch_ papers.


Simple example
--------------

.. code:: python

    from uddsketch import UDDSketch

    hist = UDDSketch(initial_error=0.01)

    # Populate structure with dummy data
    for i in range(0, 100):
        hist.add(0.1 * i)

    # Estimate p95 percentile
    q = hist.quantile(0.95)
    print(f"quantie: {q}")
    # quantie: 9.487973051696695

    # Estimate median
    m = hist.median()
    print(f"median: {m}")
    # median: 4.903763642930295


Merging Two Sketches
--------------------

.. code:: python

    import numpy as np

    from uddsketch import UDDSketch


    def main():
        # fix seed for reproducible results
        rs = np.random.RandomState(seed=42)
        # generate dummy data
        data = ((rs.pareto(3.0, 5000) + 1) * 2.0).tolist()

        # add first half to first sketch
        hist1 = UDDSketch(initial_error=0.01, max_buckets=128)
        for v in data[:500]:
            hist1.add(v)

        # add second half to other sketch
        hist2 = UDDSketch(initial_error=0.01, max_buckets=128)
        for v in data[500:]:
            hist2.add(v)

        hist1.merge(hist2)
        combined_count = hist1.num_values
        print(f"Num values added to combined sketch: {combined_count}")
        # Num values added to combined sketch: 5000

        # Estimate combined p95 percentile
        q = hist1.quantile(0.95)
        print(f"quantie: {q}")
        # quantie: 5.419515033387234

        # Estimate combined median
        m = hist1.median()
        print(f"median: {m}")
        # median: 2.5344610207788048


    if __name__ == "__main__":
        main()


Installation
------------
Installation process is simple, just::

    $ pip install uddsketch


References
----------

1. Charles Masson, Jee E. Rim and Homin K. Lee. *DDSketch: a fast and fully-mergeable quantile sketch
with relative-error guarantees.* [https://www.vldb.org/pvldb/vol12/p2195-masson.pdf]

2. I. Epicoco, C. Melle, M. Cafaro, M. Pulimeno and G. Morleo. *UDDSketch: Accurate Tracking of
Quantiles in Data Streams.* [https://arxiv.org/abs/2004.08604]


.. _DDSketch: https://www.vldb.org/pvldb/vol12/p2195-masson.pdf
.. _UDDSketch: https://arxiv.org/abs/2004.08604
