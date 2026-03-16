#include <stdio.h>
#include <stdlib.h>

int main() {

    int choice;

    while(1) {

        printf("\nCPU Scheduling Simulator\n");
        printf("------------------------\n");
        printf("1. Enter Process Data\n");
        printf("2. FCFS\n");
        printf("3. SJF\n");
        printf("4. SRTF\n");
        printf("5. Round Robin\n");
        printf("6. Priority (Preemptive)\n");
        printf("7. Priority (Non-Preemptive)\n");
        printf("8. Compare Algorithms\n");
        printf("9. Exit\n");

        printf("\nSelect Option: ");
        scanf("%d", &choice);

        switch(choice) {

            case 1:
                system("./input ");
                break;

            case 2:
                system("./fcfs ");
                break;

            case 3:
                system("./sjf ");
                break;

            case 4:
                system("./srtf ");
                break;

            case 5:
                system("./rr ");
                break;

            case 6:
                system("./priority ");
                break;

            case 7:
                system("./priority_np ");
                break;

            case 8: {

                FILE *fp = fopen("comparison_data.txt","w");
                if(fp != NULL)
                    fclose(fp);

                system("./fcfs ");
                system("./sjf ");
                system("./srtf ");
                system("./rr ");
                system("./priority ");
                system("./priority_np ");
                

                system("python3 compare.py  ");

                break;
            }

            case 9:
                exit(0);

            default:
                printf("Invalid choice\n");
        }
    }

    return 0;
}