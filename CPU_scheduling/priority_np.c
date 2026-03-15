#include <stdio.h>
#include <float.h>
#include <limits.h>
#include <stdlib.h>

#define MAX 1000

FILE *fp;

int main(){

    fp = fopen("gantt_data.txt","w");

    int n;
    int pid[MAX], priority[MAX], completed[MAX]={0};
    float at[MAX], bt[MAX], ct[MAX], tat[MAX], wt[MAX];

    FILE *fp2;

    fp2 = fopen("process_data.txt","r");

    if(fp2 == NULL){
        printf("Process data file not found! Run input first.\n");
        return 1;
    }

    fscanf(fp2,"%d",&n);

    for(int i=0;i<n;i++){

        pid[i] = i+1;

        fscanf(fp2,"%f %f %d",&at[i],&bt[i],&priority[i]);
    }

    float tq;
    fscanf(fp2,"%f",&tq);

    fclose(fp2);

    float time = 0;
    int done = 0;
    int contextSwitch = 0;
    int lastProcess = -1;

    printf("\nExecution Timeline:\n");

    while(done < n){

        int current = -1;
        int bestPriority = INT_MAX;

        for(int i=0;i<n;i++){

            if(!completed[i] && at[i] <= time){

                if(current == -1 ||
                   priority[i] < bestPriority ||
                   (priority[i]==bestPriority && at[i] < at[current])){

                    bestPriority = priority[i];
                    current = i;
                }
            }
        }

        if(current == -1){

            float nextArrival = FLT_MAX;

            for(int i=0;i<n;i++)
                if(!completed[i] && at[i] < nextArrival)
                    nextArrival = at[i];

            printf("Idle (%.2f -> %.2f)\n",time,nextArrival);

            fprintf(fp,"IDLE %.2f %.2f\n",time,nextArrival-time);

            time = nextArrival;
            continue;
        }

        if(lastProcess != -1 && lastProcess != current)
            contextSwitch++;

        printf("P%d (%.2f -> %.2f)\n",
               pid[current], time, time + bt[current]);

        fprintf(fp,"P%d %.2f %.2f\n",
                pid[current], time, bt[current]);

        time += bt[current];

        ct[current] = time;
        tat[current] = ct[current] - at[current];
        wt[current] = tat[current] - bt[current];

        completed[current] = 1;
        done++;

        lastProcess = current;
    }

    float totalWT=0,totalTAT=0;

    printf("\nPID\tAT\tBT\tPR\tCT\tTAT\tWT\n");

    for(int i=0;i<n;i++){

        totalWT += wt[i];
        totalTAT += tat[i];

        printf("P%d\t%.2f\t%.2f\t%d\t%.2f\t%.2f\t%.2f\n",
        pid[i],at[i],bt[i],priority[i],
        ct[i],tat[i],wt[i]);
    }

    printf("\nAverage Waiting Time: %.2f\n",totalWT/n);
    printf("Average Turnaround Time: %.2f\n",totalTAT/n);
    printf("Total Context Switches: %d\n",contextSwitch);

    FILE *cmp;
    cmp = fopen("comparison_data.txt","a");
    fprintf(cmp,"PRIORITY_NP %.2f\n", totalWT/n);
    fclose(cmp);

    fclose(fp);

    system("python3 visualize.py PRIORITY_NP");

    return 0;
}