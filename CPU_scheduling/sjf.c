#include <stdio.h>
#include <stdlib.h>
#define MAX 1000
#define INF 999999

FILE *fp;

int main() {

    fp = fopen("gantt_data.txt","w");

    int n;
    int pid[MAX], isCompleted[MAX];
    float at[MAX], bt[MAX], ct[MAX], tat[MAX], wt[MAX];

    FILE *fp2;

    fp2 = fopen("process_data.txt","r");

    if(fp2 == NULL){
        printf("Process data file not found! Run input first.\n");
        return 1;
    }

    fscanf(fp2,"%d",&n);

    for(int i = 0; i < n; i++) {

        int pr;   // priority read (not used in SJF)

        pid[i] = i + 1;
        isCompleted[i] = 0;

        fscanf(fp2,"%f %f %d",&at[i],&bt[i],&pr);
    }

    int tq;   // time quantum read (not used in SJF)
    fscanf(fp2,"%d",&tq);

    fclose(fp2);

    float currentTime = 0;
    int completed = 0;
    float totalWT = 0, totalTAT = 0;

    printf("\n========== SJF Execution Log ==========\n");

    while(completed < n) {

        int index = -1;
        float minBT = INF;

        for(int i = 0; i < n; i++) {

            if(at[i] <= currentTime && isCompleted[i] == 0) {

                if(bt[i] < minBT) {
                    minBT = bt[i];
                    index = i;
                }

                else if(bt[i] == minBT) {
                    if(at[i] < at[index])
                        index = i;
                }
            }
        }

        if(index != -1) {

            float startTime = currentTime;

            ct[index] = currentTime + bt[index];
            tat[index] = ct[index] - at[index];
            wt[index] = tat[index] - bt[index];

            currentTime = ct[index];
            isCompleted[index] = 1;
            completed++;

            printf("Process P%d executed from %.2f to %.2f\n",
                   pid[index], startTime, ct[index]);

            fprintf(fp,"P%d %.2f %.2f\n", pid[index], startTime, bt[index]);

            totalWT += wt[index];
            totalTAT += tat[index];
        }
        else {

            float nextArrival = INF;

            for(int i = 0; i < n; i++) {
                if(isCompleted[i] == 0 && at[i] > currentTime) {
                    if(at[i] < nextArrival)
                        nextArrival = at[i];
                }
            }

            printf("CPU Idle from %.2f to %.2f\n",
                   currentTime, nextArrival);

            fprintf(fp,"IDLE %.2f %.2f\n", currentTime, nextArrival-currentTime);

            currentTime = nextArrival;
        }
    }

    printf("\n--------------------------------------------------------------\n");
    printf("PID\tAT\tBT\tCT\tTAT\tWT\n");
    printf("--------------------------------------------------------------\n");

    for(int i = 0; i < n; i++) {

        printf("%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n",
               pid[i], at[i], bt[i], ct[i], tat[i], wt[i]);
    }

    printf("--------------------------------------------------------------\n");
    printf("Average Waiting Time = %.2f\n", totalWT/n);
    printf("Average Turnaround Time = %.2f\n", totalTAT/n);

    FILE *cmp;
    cmp = fopen("comparison_data.txt","a");
    fprintf(cmp,"SJF %.2f\n", totalWT/n);
    fclose(cmp);

    fclose(fp);

    system("python3 visualize.py SJF");

    return 0;
}