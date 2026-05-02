from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


BASE_DIR = Path(__file__).resolve().parent
GANTT_FILE = BASE_DIR / "gantt_data.txt"
COLORS = [
    "#2f6bff",
    "#cf5264",
    "#2aa785",
    "#4ca6ff",
    "#8a72ff",
    "#d5a24d",
    "#ff7f50",
]


def read_gantt_segments():
    if not GANTT_FILE.exists():
        raise FileNotFoundError(f"{GANTT_FILE.name} was not found.")

    segments = []
    with GANTT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            parts = line.split()
            if len(parts) < 3:
                continue
            pid = parts[0]
            start = float(parts[1])
            duration = float(parts[2])
            segments.append(
                {
                    "pid": pid,
                    "start": start,
                    "duration": duration,
                    "end": start + duration,
                }
            )
    if not segments:
        raise ValueError("No Gantt chart data found in gantt_data.txt.")
    return segments


def build_color_map(segments):
    color_map = {}
    color_index = 0
    for segment in segments:
        pid = segment["pid"]
        if pid == "IDLE":
            color_map[pid] = "#374151"
            continue
        if pid not in color_map:
            color_map[pid] = COLORS[color_index % len(COLORS)]
            color_index += 1
    return color_map


def draw_gantt(segments, algorithm_name):
    start_time = segments[0]["start"]
    end_time = segments[-1]["end"]
    total_time = max(end_time - start_time, 1)
    figure_width = max(10, min(22, total_time * 0.35))

    fig, ax = plt.subplots(figsize=(figure_width, 3.8))
    fig.patch.set_facecolor("#0c1222")
    ax.set_facecolor("#12192b")

    color_map = build_color_map(segments)
    y_bottom, height = 3, 4

    for segment in segments:
        pid = segment["pid"]
        start = segment["start"]
        duration = segment["duration"]
        color = color_map[pid]

        ax.broken_barh([(start, duration)], (y_bottom, height), facecolors=color, edgecolors=color, linewidth=0)

        if pid != "IDLE" and duration >= max(1.4, total_time * 0.08):
            ax.text(
                start + duration / 2,
                y_bottom + height / 2,
                pid,
                ha="center",
                va="center",
                color="white",
                fontsize=10,
                fontweight="bold",
            )

        ax.plot([start, start], [y_bottom - 0.4, y_bottom], color="#92a2c8", linewidth=1)
        ax.text(start, y_bottom - 0.9, f"{start:.0f}", ha="center", va="top", color="#edf2ff", fontsize=9)

    ax.plot([end_time, end_time], [y_bottom - 0.4, y_bottom], color="#92a2c8", linewidth=1)
    ax.text(end_time, y_bottom - 0.9, f"{end_time:.0f}", ha="center", va="top", color="#edf2ff", fontsize=9)

    legend_items = [
        Patch(facecolor=color_map[pid], edgecolor=color_map[pid], label=pid)
        for pid in color_map
        if pid != "IDLE"
    ]
    if legend_items:
        legend = ax.legend(
            handles=legend_items,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.2),
            ncol=min(6, len(legend_items)),
            frameon=False,
            fontsize=9,
        )
        for text in legend.get_texts():
            text.set_color("#edf2ff")

    ax.set_xlim(start_time, end_time)
    ax.set_ylim(1.5, 8.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlabel("Time", color="#edf2ff", fontsize=10)
    ax.set_title(f"{algorithm_name} Algorithm Gantt Chart", color="#edf2ff", fontsize=13, fontweight="bold", pad=18)

    for spine in ax.spines.values():
        spine.set_color("#25314c")

    plt.tight_layout()
    plt.show()


def main():
    algorithm_name = sys.argv[1] if len(sys.argv) > 1 else "CPU Scheduling"
    segments = read_gantt_segments()
    draw_gantt(segments, algorithm_name)


if __name__ == "__main__":
    main()
