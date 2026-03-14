#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int firstCount=0,bestCount=0,worstCount=0;

/* ---------- UNIT CONVERSION ---------- */

long long convertToBytes(double value, char unit[])
{
    if(value < 0)
    {
        printf("Error: Memory size cannot be negative.\n");
        exit(1);
    }

    if(strcmp(unit,"Bit")==0 || strcmp(unit,"bit")==0)
        return value / 8;

    if(strcmp(unit,"Byte")==0 || strcmp(unit,"B")==0)
        return value;

    if(strcmp(unit,"KB")==0)
        return value * 1024;

    if(strcmp(unit,"MB")==0)
        return value * 1024 * 1024;

    if(strcmp(unit,"GB")==0)
        return value * 1024LL * 1024LL * 1024LL;

    if(strcmp(unit,"TB")==0)
        return value * 1024LL * 1024LL * 1024LL * 1024LL;

    /* ⭐ If unit is invalid */
    printf("Warning: Invalid unit '%s'. Assuming Byte.\n", unit);

    return value;   // treat as Byte
}

/* ---------- FIRST FIT ---------- */

void firstFit(long long block[], int m, long long process[], int n, FILE *fp)
{
    long long temp[m];

    for(int i=0;i<m;i++)
        temp[i]=block[i];

    int success=0;

    printf("\nFirst Fit Allocation\n");
    fprintf(fp,"FIRST ");

    for(int i=0;i<n;i++)
    {
        int done=0;

        for(int j=0;j<m;j++)
        {
            if(temp[j] >= process[i])
            {
                printf("P%d -> B%d\n",i+1,j+1);
                fprintf(fp,"%d ",j+1);

                temp[j]-=process[i];
                success++;
                done=1;
                break;
            }
        }

        if(!done)
        {
            printf("P%d -> Not Allocated\n",i+1);
            fprintf(fp,"0 ");
        }
    }

    firstCount=success;
    fprintf(fp,"\n");
}

/* ---------- BEST FIT ---------- */

void bestFit(long long block[], int m, long long process[], int n, FILE *fp)
{
    long long temp[m];

    for(int i=0;i<m;i++)
        temp[i]=block[i];

    int success=0;

    printf("\nBest Fit Allocation\n");
    fprintf(fp,"BEST ");

    for(int i=0;i<n;i++)
    {
        int best=-1;

        for(int j=0;j<m;j++)
        {
            if(temp[j] >= process[i])
            {
                if(best==-1 || temp[j] < temp[best])
                    best=j;
            }
        }

        if(best!=-1)
        {
            printf("P%d -> B%d\n",i+1,best+1);
            fprintf(fp,"%d ",best+1);

            temp[best]-=process[i];
            success++;
        }
        else
        {
            printf("P%d -> Not Allocated\n",i+1);
            fprintf(fp,"0 ");
        }
    }

    bestCount=success;
    fprintf(fp,"\n");
}

/* ---------- WORST FIT ---------- */

void worstFit(long long block[], int m, long long process[], int n, FILE *fp)
{
    long long temp[m];

    for(int i=0;i<m;i++)
        temp[i]=block[i];

    int success=0;

    printf("\nWorst Fit Allocation\n");
    fprintf(fp,"WORST ");

    for(int i=0;i<n;i++)
    {
        int worst=-1;

        for(int j=0;j<m;j++)
        {
            if(temp[j] >= process[i])
            {
                if(worst==-1 || temp[j] > temp[worst])
                    worst=j;
            }
        }

        if(worst!=-1)
        {
            printf("P%d -> B%d\n",i+1,worst+1);
            fprintf(fp,"%d ",worst+1);

            temp[worst]-=process[i];
            success++;
        }
        else
        {
            printf("P%d -> Not Allocated\n",i+1);
            fprintf(fp,"0 ");
        }
    }

    worstCount=success;
    fprintf(fp,"\n");
}

/* ---------- BEST ALGORITHM ---------- */

void bestAlgorithm(FILE *fp)
{
    printf("\n");

    if(firstCount>=bestCount && firstCount>=worstCount)
    {
        printf("Best Algorithm: FIRST FIT\n");
        fprintf(fp,"BEST_ALGO FIRST\n");
    }
    else if(bestCount>=firstCount && bestCount>=worstCount)
    {
        printf("Best Algorithm: BEST FIT\n");
        fprintf(fp,"BEST_ALGO BEST\n");
    }
    else
    {
        printf("Best Algorithm: WORST FIT\n");
        fprintf(fp,"BEST_ALGO WORST\n");
    }
}

/* ---------- MAIN PROGRAM ---------- */

int main()
{
    int m,n;

    printf("===== Memory Allocation Simulator =====\n");

    printf("\nEnter number of memory blocks: ");
    if(scanf("%d",&m)!=1 || m<=0)
    {
        printf("Error: Invalid number of blocks.\n");
        return 1;
    }

    long long block[m];

    printf("\nEnter block sizes (Allowed units: Bit Byte KB MB GB TB)\n");

    for(int i=0;i<m;i++)
    {
        double value;
        char unit[10]="Byte";
        char line[50];

        printf("Block %d: ",i+1);

        getchar();  // clear buffer
        fgets(line,sizeof(line),stdin);

        sscanf(line,"%lf %s",&value,unit);

        block[i]=convertToBytes(value,unit);
    }

    printf("\nEnter number of processes: ");
    if(scanf("%d",&n)!=1 || n<=0)
    {
        printf("Error: Invalid number of processes.\n");
        return 1;
    }

    long long process[n];

    printf("\nEnter process sizes (Allowed units: Bit Byte KB MB GB TB)\n");

    for(int i=0;i<n;i++)
    {
    double value;
    char unit[10]="Byte";
    char line[50];

    printf("Process %d: ",i+1);

    getchar();   // clear input buffer
    fgets(line,sizeof(line),stdin);

    sscanf(line,"%lf %s",&value,unit);

    process[i]=convertToBytes(value,unit);
    }

    FILE *fp=fopen("output.txt","w");

    if(fp==NULL)
    {
        printf("Error: Could not open output file.\n");
        return 1;
    }

    firstFit(block,m,process,n,fp);
    bestFit(block,m,process,n,fp);
    worstFit(block,m,process,n,fp);

    bestAlgorithm(fp);

    fclose(fp);

    printf("\nOpening Visualization...\n");

    system("python3 visualization.py");

    return 0;
}