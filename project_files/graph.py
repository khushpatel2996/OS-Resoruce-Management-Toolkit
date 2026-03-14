import matplotlib.pyplot as plt

algorithms = []
faults = []

# Read data from file
with open("comparison.txt", "r") as file:
    for line in file:
        name, value = line.split()
        algorithms.append(name)
        faults.append(int(value))

# Find best algorithm (minimum faults)
min_fault = min(faults)

best_algorithms = []
for i in range(len(faults)):
    if faults[i] == min_fault:
        best_algorithms.append(algorithms[i])

# Set colors
colors = []
for i in range(len(algorithms)):
    if faults[i] == min_fault:
        colors.append("green")
    else:
        colors.append("orange")

plt.figure(figsize=(8,5))

bars = plt.bar(algorithms, faults, color=colors)

# Add values on top of bars
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        height + 0.05,
        int(height),
        ha='center',
        fontsize=11,
        fontweight='bold'
    )

# Title and labels
plt.title("FIFO vs LRU Page Replacement Comparison", fontsize=15)
plt.xlabel("Page Replacement Algorithm", fontsize=12)
plt.ylabel("Number of Page Faults", fontsize=12)

# Show best algorithm text
best_text = " / ".join(best_algorithms)

plt.figtext(
    0.5,
    0.93,
    f"BEST ALGORITHM : {best_text}",
    ha="center",
    fontsize=14,
    fontweight="bold",
    color="darkgreen"
)

plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout(rect=[0,0,1,0.9])

plt.show()