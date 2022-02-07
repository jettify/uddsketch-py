from uddsketch import UDDSketch

hist = UDDSketch(initial_error=0.01)

for i in range(0, 100):
    hist.add(0.1 * i)
q = hist.quantile(0.5)
print("quantie: {}".format(q))
