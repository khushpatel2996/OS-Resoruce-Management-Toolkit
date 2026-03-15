#include <stdio.h>
#include <float.h>
#include <stdbool.h>
#include <math.h>
#include <stdlib.h>

#define MAX 1000
#define EPS 0.00001

FILE *fp;

int main() {

    fp = fopen("gantt_data.txt","w");

    int n;
    int pid[MAX];
    float at[MAX], bt[MAX], rt[MAX], ct[MAX], tat[MAX], wt[MAX];

    FILE *fp2;

    fp2 = fopen("process_data.txt","r");

    if(fp2 == NULL){
        printf("Process data file not found! Run input first.\n");
        return 1;
    }

    fscanf(fp2,"%d",&n);

    for(int i = 0; i < n; i++) {

        int pr;  // priority read but not used

        pid[i] = i + 1;

        fscanf(fp2,"%f %f %d",&at[i],&bt[i],&pr);

        rt[i] = bt[i];
    }

    int tq; // time quantum read but not used
    fscanf(fp2,"%d",&tq);

    fclose(fp2);

    float time = 0;
    int completed = 0;
    int lastProcess = -1;
    int contextSwitch = 0;

    printf("\nExecution Timeline:\n");

    while(completed < n) {

        int current = -1;
        float minRT = FLT_MAX;

        for(int i = 0; i < n; i++) {

            if(at[i] <= time + EPS && rt[i] > EPS) {

                if(current == -1 ||
                   rt[i] < minRT - EPS ||
                   (fabs(rt[i] - minRT) < EPS && at[i] < at[current]) ||
                   (fabs(rt[i] - minRT) < EPS && fabs(at[i] - at[current]) < EPS && pid[i] < pid[current])) {

                    minRT = rt[i];
                    current = i;
                }
            }
        }

        if(current == -1) {

            float nextArrival = FLT_MAX;

            for(int i = 0; i < n; i++)
                if(rt[i] > EPS && at[i] > time && at[i] < nextArrival)
                    nextArrival = at[i];

            printf("Idle (%.2f -> %.2f)\n", time, nextArrival);

            fprintf(fp,"IDLE %.2f %.2f\n", time, nextArrival - time);

            time = nextArrival;
            continue;
        }

        if(lastProcess != -1 && lastProcess != current)
            contextSwitch++;

        float nextArrival = FLT_MAX;

        for(int i = 0; i < n; i++)
            if(at[i] > time && rt[i] > EPS && at[i] < nextArrival)
                nextArrival = at[i];

        float executeTime;

        if(nextArrival == FLT_MAX)
            executeTime = rt[current];
        else
            executeTime = fmin(rt[current], nextArrival - time);

        printf("P%d (%.2f -> %.2f)\n",
               pid[current], time, time + executeTime);

        fprintf(fp,"P%d %.2f %.2f\n", pid[current], time, executeTime);

        rt[current] -= executeTime;
        time += executeTime;

        if(rt[current] <= EPS) {

            ct[current] = time;
            tat[current] = ct[current] - at[current];
            wt[current] = tat[current] - bt[current];

            if(wt[current] < 0)
                wt[current] = 0;

            completed++;
        }

        lastProcess = current;
    }

    float totalWT = 0, totalTAT = 0;

    printf("\nPID\tAT\tBT\tCT\tTAT\tWT\n");

    for(int i = 0; i < n; i++) {

        totalWT += wt[i];
        totalTAT += tat[i];

        printf("P%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n",
               pid[i], at[i], bt[i], ct[i], tat[i], wt[i]);
    }

    printf("\nAverage Waiting Time: %.2f\n", totalWT/n);
    printf("Average Turnaround Time: %.2f\n", totalTAT/n);
    printf("Total Context Switches: %d\n", contextSwitch);

    FILE *cmp;
    cmp = fopen("comparison_data.txt","a");
    fprintf(cmp,"SRTF %.2f\n", totalWT/n);
    fclose(cmp);

    fclose(fp);

    system("python3 visualize.py SRTF");

    return 0;
}