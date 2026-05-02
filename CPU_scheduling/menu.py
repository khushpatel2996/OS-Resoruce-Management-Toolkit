import os

def run_program(source, exe):
    
    os.system(f"gcc {source} -o {exe} -lm")

    os.system(f"./{exe}")


while True:

    print("\n===================================")
    print("      CPU Scheduling Simulator")
    print("===================================")
    print("1. Input Processes")
    print("2. FCFS Scheduling")
    print("3. SJF Scheduling")
    print("4. SRTF Scheduling")
    print("5. Round Robin Scheduling")
    print("6. Priority Scheduling (Preemptive)")
    print("7. Priority Scheduling (Non-Preemptive)")
    print("8. Compare All Algorithms")
    print("0. Exit")
    print("===================================")

    choice = input("Enter your choice: ")

    if choice == "1":
        run_program("input.c", "input")

    elif choice == "2":
        run_program("fcfs.c", "fcfs")

    elif choice == "3":
        run_program("sjf.c", "sjf")

    elif choice == "4":
        run_program("srtf.c", "srtf")

    elif choice == "5":
        run_program("rr.c", "rr")

    elif choice == "6":
        run_program("priority.c", "priority")

    elif choice == "7":
        run_program("priority_np.c", "priority_np")

    elif choice == "8":
        print("\nRunning All Algorithms for Comparison...\n")

        run_program("fcfs.c", "fcfs")
        run_program("sjf.c", "sjf")
        run_program("srtf.c", "srtf")
        run_program("rr.c", "rr")
        run_program("priority.c", "priority")
        run_program("priority_np.c", "priority_np")

    elif choice == "0":
        print("Exiting Program...")
        break

    else:
        print("Invalid choice! Try again.")