#include <stdio.h>
#include <stdlib.h>

/* -------- FIFO PAGE REPLACEMENT -------- */

int FIFO(int pages[], int n, int frames)
{
    int memory[50];
    int index = 0;
    int faults = 0;

    for(int i=0;i<frames;i++)
        memory[i] = -1;

    printf("\n===== FIFO Page Replacement =====\n");
    printf("Page\tFrames\n");

    for(int i=0;i<n;i++)
    {
        int found = 0;

        for(int j=0;j<frames;j++)
        {
            if(memory[j] == pages[i])
            {
                found = 1;
                break;
            }
        }

        if(!found)
        {
            memory[index] = pages[i];
            index = (index + 1) % frames;
            faults++;
        }

        printf("%d\t", pages[i]);

        for(int j=0;j<frames;j++)
        {
            if(memory[j] == -1)
                printf("- ");
            else
                printf("%d ", memory[j]);
        }

        printf("\n");
    }

    printf("Total FIFO Page Faults = %d\n", faults);

    return faults;
}


/* -------- LRU PAGE REPLACEMENT -------- */

int LRU(int pages[], int n, int frames)
{
    int memory[50];
    int recent[50];
    int faults = 0;

    for(int i=0;i<frames;i++)
    {
        memory[i] = -1;
        recent[i] = -1;
    }

    printf("\n===== LRU Page Replacement =====\n");
    printf("Page\tFrames\n");

    for(int i=0;i<n;i++)
    {
        int found = -1;

        for(int j=0;j<frames;j++)
        {
            if(memory[j] == pages[i])
            {
                found = j;
                break;
            }
        }

        if(found != -1)
        {
            recent[found] = i;
        }
        else
        {
            int lru = 0;

            for(int j=1;j<frames;j++)
            {
                if(recent[j] < recent[lru])
                    lru = j;
            }

            memory[lru] = pages[i];
            recent[lru] = i;
            faults++;
        }

        printf("%d\t", pages[i]);

        for(int j=0;j<frames;j++)
        {
            if(memory[j] == -1)
                printf("- ");
            else
                printf("%d ", memory[j]);
        }

        printf("\n");
    }

    printf("Total LRU Page Faults = %d\n", faults);

    return faults;
}


/* -------- MAIN PROGRAM -------- */

int main()
{
    int n, frames;

    printf("===== Page Replacement Simulator =====\n");

    printf("\nEnter number of pages: ");
    scanf("%d", &n);

    int pages[n];

    printf("Enter page reference string:\n");

    for(int i=0;i<n;i++)
        scanf("%d", &pages[i]);

    printf("Enter number of frames: ");
    scanf("%d", &frames);


    /* Save page data for animation */

    FILE *fp_pages = fopen("pages.txt","w");

    fprintf(fp_pages,"%d\n",frames);

    for(int i=0;i<n;i++)
        fprintf(fp_pages,"%d ", pages[i]);

    fclose(fp_pages);


    /* Run algorithms */

    int fifoFaults = FIFO(pages, n, frames);
    int lruFaults  = LRU(pages, n, frames);


    /* Print summary */

    printf("\n===== Summary =====\n");
    printf("FIFO Page Faults : %d\n", fifoFaults);
    printf("LRU Page Faults  : %d\n", lruFaults);


    /* Save comparison data */

    FILE *fp = fopen("comparison.txt","w");

    fprintf(fp,"FIFO %d\n", fifoFaults);
    fprintf(fp,"LRU %d\n", lruFaults);

    fclose(fp);


    printf("\nOpening RAM Frame Visualization...\n");
    system("python3 frame_visualization.py");

    printf("\nGenerating FIFO vs LRU Comparison Graph...\n");
    system("python3 graph.py");


    return 0;
}