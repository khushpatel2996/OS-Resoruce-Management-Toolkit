import matplotlib.pyplot as plt

with open("pages.txt","r") as f:
    lines=f.readlines()

frames=int(lines[0])
pages=list(map(int,lines[1].split()))

memory=[-1]*frames
index=0
faults=0

plt.ion()

for page in pages:

    found=False

    for i in range(frames):
        if memory[i]==page:
            found=True
            break

    if not found:
        memory[index]=page
        index=(index+1)%frames
        faults+=1

    plt.clf()

    y=list(range(frames))

    labels=[str(x) if x!=-1 else "-" for x in memory]

    plt.barh(y,[1]*frames,color="skyblue")

    for i,val in enumerate(labels):
        plt.text(0.5,i,val,ha="center",va="center",fontsize=16)

    plt.yticks(y,[f"Frame {i+1}" for i in range(frames)])
    plt.xticks([])

    plt.title(f"FIFO Frame Simulation | Page Faults: {faults}")

    plt.pause(1)
plt.ioff()
plt.show()