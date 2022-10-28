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
