import matplotlib.pyplot as plt

algorithms = []
values = []

# read comparison data
with open("comparison_data.txt") as f:
    for line in f:
        name, val = line.split()
        algorithms.append(name)
        values.append(float(val))

# find best algorithm
best_index = values.index(min(values))
best_algo = algorithms[best_index]

print("\nBest Algorithm for given input:", best_algo)
print("Reason: Lowest Average Waiting Time =", values[best_index])

# color list
colors = []
for i in range(len(values)):
    if i == best_index:
        colors.append("green")   # best algorithm
    else:
        colors.append("steelblue")

plt.figure(figsize=(8,5))

plt.barh(algorithms, values, color=colors)

plt.xlabel("Average Waiting Time")
plt.ylabel("Algorithms")
plt.title("CPU Scheduling Algorithms Comparison")

# show value on bars
for i, v in enumerate(values):
    plt.text(v + 0.05, i, f"{v:.2f}", va='center')

plt.show()