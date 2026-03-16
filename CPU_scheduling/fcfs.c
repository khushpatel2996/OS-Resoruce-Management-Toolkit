#include <stdio.h>
#include <stdlib.h>
#define MAX 1000

FILE *fp;

int main() {

    fp = fopen("gantt_data.txt","w");

    int n;
    int pid[MAX];
    float at[MAX], bt[MAX], ct[MAX], tat[MAX], wt[MAX];

    FILE *fp2;

    fp2 = fopen("process_data.txt","r");

    if(fp2 == NULL){
        printf("Process data file not found! Run input first.\n");
        return 1;
    }

    fscanf(fp2,"%d",&n);

    for(int i = 0; i < n; i++) {

        int pr;  // priority read (not used in FCFS)

        pid[i] = i + 1;

        fscanf(fp2,"%f %f %d",&at[i],&bt[i],&pr);
    }

    int tq;   // time quantum read (not used in FCFS)
    fscanf(fp2,"%d",&tq);

    fclose(fp2);

    // Sort by Arrival Time
    for(int i = 0; i < n - 1; i++) {
        for(int j = i + 1; j < n; j++) {

            if(at[i] > at[j]) {

                float temp;

                temp = at[i]; at[i] = at[j]; at[j] = temp;
                temp = bt[i]; bt[i] = bt[j]; bt[j] = temp;

                int t = pid[i]; pid[i] = pid[j]; pid[j] = t;
            }
        }
    }

    float currentTime = 0;
    float totalWT = 0, totalTAT = 0;

    printf("\n===== FCFS Execution Log =====\n");

    for(int i = 0; i < n; i++) {

        if(currentTime < at[i]) {

            printf("CPU Idle from %.2f to %.2f\n", currentTime, at[i]);
            fprintf(fp,"IDLE %.2f %.2f\n", currentTime, at[i] - currentTime);

            currentTime = at[i];
        }

        float startTime = currentTime;

        ct[i] = currentTime + bt[i];
        tat[i] = ct[i] - at[i];
        wt[i] = tat[i] - bt[i];

        currentTime = ct[i];

        printf("Process P%d executed from %.2f to %.2f\n",
               pid[i], startTime, ct[i]);

        fprintf(fp,"P%d %.2f %.2f\n", pid[i], startTime, bt[i]);

        totalWT += wt[i];
        totalTAT += tat[i];
    }

    printf("\n-------------------------------------------\n");
    printf("PID\tAT\tBT\tCT\tTAT\tWT\n");
    printf("-------------------------------------------\n");

    for(int i = 0; i < n; i++) {
        printf("%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n",
               pid[i], at[i], bt[i], ct[i], tat[i], wt[i]);
    }

    printf("-------------------------------------------\n");
    printf("Average Waiting Time = %.2f\n", totalWT/n);
    printf("Average Turnaround Time = %.2f\n", totalTAT/n);

    // Save comparison data
    FILE *cmp;
    cmp = fopen("comparison_data.txt","a");
    fprintf(cmp,"FCFS %.2f\n", totalWT/n);
    fclose(cmp);

    fclose(fp);

    system("python3 visualize.py FCFS");

    return 0;
}