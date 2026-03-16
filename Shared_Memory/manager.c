import matplotlib.pyplot as plt
import time

plt.style.use("ggplot")
plt.ion()

colors = ["red","blue","green","orange","purple"]

while True:

    counts = [0,0,0,0,0]
    queue_size = 0

    try:
        with open("resource_log.txt") as f:
            for line in f:

                parts = line.split()

                if len(parts) < 6:
                    continue

                # count resource allocation
                if "ALLOCATED" in line:
                    r = int(parts[-2])
                    counts[r] += 1

                # count waiting queue
                if "WAITING" in line:
                    queue_size += 1

    except:
        pass

    plt.clf()

    # -------- Resource Usage Graph --------
    plt.subplot(1,2,1)

    bars = plt.bar(range(5), counts, color=colors)

    plt.title("Resource Usage")
    plt.xlabel("Resource ID")
    plt.ylabel("Allocations")

    plt.xticks(range(5), ["R0","R1","R2","R3","R4"])

    # keep graph scale clean
    plt.ylim(0, max(counts)+2 if max(counts)>0 else 2)

    # show numbers above bars
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x()+bar.get_width()/2,
                 h+0.05,
                 str(int(h)),
                 ha='center')

    # -------- Waiting Queue Graph --------
    plt.subplot(1,2,2)

    plt.bar(["Queue"], [queue_size], color="purple")

    plt.title("Waiting Queue Size")
    plt.ylabel("Processes Waiting")

    plt.ylim(0,4)   # queue max is 3 so keep scale nice

    plt.pause(1)
    time.sleep(1)