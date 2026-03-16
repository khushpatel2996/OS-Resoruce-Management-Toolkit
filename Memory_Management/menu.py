import subprocess


def memory_allocation():
    print("\nRunning Contiguous Memory Allocation...\n")

    # compile and run C program
    subprocess.run(["gcc", "memory_allocation.c", "-o", "memory_allocation"])
    subprocess.run(["./memory_allocation"])

    print("\nOpening Memory Visualization...\n")
    


def page_replacement():
    print("\nRunning Non-Contiguous Memory Allocation...\n")

    # compile and run C program
    subprocess.run(["gcc", "page_replacement.c", "-o", "page_replacement"])
    subprocess.run(["./page_replacement"])

    print("\nOpening Frame Visualization...\n")

    print("\nOpening Graph...\n")
    


while True:

    print("\n==============================")
    print(" MEMORY MANAGEMENT SIMULATOR ")
    print("==============================")
    print("1. Contiguous Memory Allocation")
    print("2. Non-Contiguous Memory")
    print("3. Exit")

    choice = input("\nEnter your choice: ")

    if choice == "1":
        memory_allocation()

    elif choice == "2":
        page_replacement()

    elif choice == "3":
        print("\nExiting...")
        break

    else:
        print("\nInvalid choice. Try again.")