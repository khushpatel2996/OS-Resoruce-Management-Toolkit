#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

int firstCount=0,bestCount=0,worstCount=0;

/* ---------- UNIT CONVERSION ---------- */

long long convertToBytes(double value, char unit[])
{
    if(value < 0)
    {
        printf("Error: Memory size cannot be negative.\n");
        exit(1);
    }

    if(strcasecmp(unit,"bit")==0)
        return value / 8;

    if(strcasecmp(unit,"byte")==0 || strcasecmp(unit,"b")==0)
        return value;

    if(strcasecmp(unit,"kb")==0)
        return value * 1024;

    if(strcasecmp(unit,"mb")==0)
        return value * 1024 * 1024;

    if(strcasecmp(unit,"gb")==0)
        return value * 1024LL * 1024LL * 1024LL;

    if(strcasecmp(unit,"tb")==0)
        return value * 1024LL * 1024LL * 1024LL * 1024LL;

    printf("Warning: Invalid unit '%s'. Assuming Byte.\n", unit);
    return value;
}

/* ---------- PARSE INPUT (MULTIPLE UNITS) ---------- */

long long parseMemoryInput()
{
    char line[200];
    long long totalBytes = 0;

    fgets(line,sizeof(line),stdin);

    char *token = strtok(line," \n");

    while(token != NULL)
    {
        double value = atof(token);

        char *unit = strtok(NULL," \n");

        if(unit == NULL)
        {
            /* Default unit = Byte */
            totalBytes += convertToBytes(value,"Byte");
            break;
        }

        totalBytes += convertToBytes(value,unit);

        token = strtok(NULL," \n");
    }

    return totalBytes;
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
    scanf("%d",&m);
    getchar();

    long long block[m];

    printf("\nEnter block sizes (Allowed units: Bit, Byte, KB, MB, GB, TB)\n");
    printf("Default unit is Byte\n");

    for(int i=0;i<m;i++)
    {
        printf("Block %d: ",i+1);
        block[i]=parseMemoryInput();
    }

    printf("\nEnter number of processes: ");
    scanf("%d",&n);
    getchar();

    long long process[n];

    printf("\nEnter process sizes (Allowed units: Bit, Byte, KB, MB, GB, TB)\n");
    printf("Default unit is Byte\n");

    for(int i=0;i<n;i++)
    {
        printf("Process %d: ",i+1);
        process[i]=parseMemoryInput();
    }

    FILE *fp=fopen("output.txt","w");

    if(fp==NULL)
    {
        printf("Error opening output file\n");
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