import matplotlib.pyplot as plt
import sys

processes = []
start_times = []
durations = []

# algorithm name command line se aayega
algo = sys.argv[1]

# Read gantt_data.txt
with open("gantt_data.txt", "r") as file:
    for line in file:
        parts = line.split()

        process = parts[0]
        start = float(parts[1])
        duration = float(parts[2])

        processes.append(process)
        start_times.append(start)
        durations.append(duration)

# Draw Gantt Chart
fig, ax = plt.subplots()

for i in range(len(processes)):
    ax.barh(processes[i], durations[i], left=start_times[i])

ax.set_xlabel("Time")

# yaha change hua hai
ax.set_title(algo + " Algorithm Gantt Chart")

plt.show()