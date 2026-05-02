#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main()
{
    int choice;

    while (1)
    {
        printf("\n===== OS RESOURCE MANAGEMENT TOOLKIT =====\n");
        printf("1. CPU Scheduling\n");
        printf("2. Memory Management\n");
        printf("3. Shared Memory Simulation\n");
        printf("4. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        switch (choice)
        {
        case 1:
            system("cd CPU_scheduling && python3 menu.py");
            break;

        case 2:
            system("cd Memory_Management && python3 menu.py");
            break;
        case 3:

            printf("\n===== SHARED MEMORY SIMULATION =====\n");

            /* compile programs */
            system("cd Shared_Memory && gcc manager.c -o manager");
            system("cd Shared_Memory && gcc client.c -o client");

            /* start manager in background */
            system("cd Shared_Memory && ./manager > /dev/null 2>&1 &");

            sleep(1); // wait for shared memory creation

            /* start client */
            system("cd Shared_Memory && ./client");

            break;

        case 4:
            exit(0);

        default:
            printf("Invalid choice\n");
        }
    }
}