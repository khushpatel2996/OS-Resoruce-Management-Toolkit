import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Patch

with open("output.txt","r") as file:
    lines=file.readlines()

y_labels=[]
values=[]
colors=[]
block_labels=[]
best_algo=""

for line in lines:

    data=line.strip().split()

    if not data:
        continue

    if data[0]=="BEST_ALGO":
        best_algo=data[1]
        continue

    algo=data[0]
    allocations=[int(x) for x in data[1:]]

    for i,val in enumerate(allocations):

        y_labels.append(f"P{i+1} ({algo})")
        values.append(i+1)

        if algo=="FIRST":
            base_color="#3498db"
        elif algo=="BEST":
            base_color="#2ecc71"
        else:
            base_color="#f39c12"

        if val==0:
            colors.append("#e74c3c")
            block_labels.append("Not Alloc")
        else:
            colors.append(base_color)
            block_labels.append(f"B{val}")

# Dynamic height for many inputs
fig_height=max(8,len(y_labels)*0.35)

fig,ax=plt.subplots(figsize=(14,fig_height))

bars=ax.barh(y_labels,values,color=colors)

ax.xaxis.set_major_locator(MaxNLocator(integer=True))

for i,bar in enumerate(bars):

    ax.text(
        bar.get_width()+0.1,
        bar.get_y()+bar.get_height()/2,
        block_labels[i],
        va='center',
        fontsize=10,
        fontweight='bold'
    )

ax.set_xlabel("Process Order",fontsize=13,fontweight='bold')
ax.set_ylabel("Process & Algorithm",fontsize=13,fontweight='bold')

ax.grid(axis='x',linestyle='--',alpha=0.6)

# Main title
ax.set_title(
    "Memory Allocation Visualization",
    fontsize=22,
    fontweight="bold",
    pad=40
)

# ⭐ Colored Best Algorithm text (safe position)
if best_algo!="":
    ax.text(
        0.5,
        1.02,
        f"Best Algorithm : {best_algo}",
        transform=ax.transAxes,
        ha="center",
        fontsize=18,
        fontweight="bold",
        color="#8e44ad"
    )

legend_elements=[
    Patch(facecolor="#3498db",label="First Fit"),
    Patch(facecolor="#2ecc71",label="Best Fit"),
    Patch(facecolor="#f39c12",label="Worst Fit"),
    Patch(facecolor="#e74c3c",label="Allocation Failed")
]

ax.legend(handles=legend_elements,loc="lower right")

plt.tight_layout()

plt.show()