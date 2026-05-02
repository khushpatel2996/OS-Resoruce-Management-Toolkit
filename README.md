# OS Resource Management Toolkit

A desktop OS simulator dashboard built with Python `tkinter` and C modules for core operating-system concepts.

## Modules

- `CPU Scheduling`
  Compare FCFS, SJF, SRTF, Round Robin, and Priority scheduling with Gantt-chart style output.
- `Memory Management`
  Explore contiguous allocation with First Fit, Best Fit, and Worst Fit, plus paging with FIFO and LRU.
- `Resource Manager`
  Simulate client login, resource request/release flow, waiting queues, warnings, and event logs.
- `System Monitor`
  View lightweight live charts for simulated CPU and memory activity.
- `AI Study Tutor`
  Ask project-specific OS questions, analyze current simulator output, generate debugging checklists, and prepare viva questions.

## Tech Stack

- Python
- Tkinter
- C
- GCC

## Project Structure

```text
CPU_scheduling/      C programs and helpers for CPU scheduling
Memory_Management/   C programs and helpers for memory allocation and paging
Shared_Memory/       Resource manager backend files
ai_tutor.py          Local context-aware AI study tutor engine
dashboard.py         Main integrated GUI
main.c               Basic console entry file
```

## Requirements

- Python 3
- GCC available in `PATH`
- Windows environment recommended for the current local setup

## Run

From the project folder:

```powershell
python dashboard.py
```

## Notes

- The dashboard compiles and runs the memory-management C files from `Memory_Management/`.
- Generated binaries, logs, and temporary output files are ignored through `.gitignore`.
- Some simulator behaviors are intentionally educational rather than production-grade OS implementations.

## Author

made with ❤️
# OS-Resoruce-Management-Toolkit
