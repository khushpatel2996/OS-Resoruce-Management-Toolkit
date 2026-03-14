
import matplotlib.pyplot as plt
import time

plt.style.use("ggplot")
plt.ion()

fig, (ax1, ax2) = plt.subplots(1, 2)

colors = ["red", "blue", "green", "orange", "purple"]

while True:

    counts = [0,0,0,0,0]
    queue_counts = [0,0,0,0,0]

    # dictionary to track waiting processes
    waiting = {0:[],1:[],2:[],3:[],4:[]}

    try:
        with open("resource_log.txt","r") as f:
            lines = f.readlines()

        for line in lines:

            parts = line.split()

            if len(parts) < 6:
                continue

            pid = parts[6]
            r = int(parts[7])

            # process enters waiting queue
            if "WAITING" in line:
                if pid not in waiting[r]:
                    waiting[r].append(pid)

            # process allocated resource
            if "ALLOCATED" in line:

                counts[r] += 1

                # remove from waiting queue
                if pid in waiting[r]:
                    waiting[r].remove(pid)

        # calculate queue size per resource
        for i in range(5):
            queue_counts[i] = len(waiting[i])

    except:
        pass

    ax1.clear()
    ax2.clear()

    # -------- Resource Usage Graph --------
    ax1.bar(range(5), counts, color=colors)

    ax1.set_title("Resource Usage")
    ax1.set_xlabel("Resource ID")
    ax1.set_ylabel("Allocations")

    ax1.set_xticks(range(5))
    ax1.set_xticklabels(["R0","R1","R2","R3","R4"])

    ax1.set_ylim(0,8)
    ax1.set_yticks(range(0,9))

    for i,v in enumerate(counts):
        ax1.text(i, v+0.05, str(v), ha='center')

    ax1.grid(axis='y')

    # -------- Waiting Queue Graph --------
    ax2.bar(range(5), queue_counts, color="purple")

    ax2.set_title("Waiting Queue per Resource")
    ax2.set_xlabel("Resource ID")
    ax2.set_ylabel("Processes Waiting")

    ax2.set_xticks(range(5))
    ax2.set_xticklabels(["R0","R1","R2","R3","R4"])

    max_wait = max(queue_counts) if max(queue_counts) > 0 else 1
    ax2.set_ylim(0, max_wait + 1)
    ax2.set_yticks(range(0, max_wait + 2))

    for i,v in enumerate(queue_counts):
        ax2.text(i, v+0.05, str(v), ha='center')

    ax2.grid(axis='y')

    plt.tight_layout()

    plt.draw()
    plt.pause(0.5)

    time.sleep(1)

