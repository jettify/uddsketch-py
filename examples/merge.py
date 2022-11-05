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
