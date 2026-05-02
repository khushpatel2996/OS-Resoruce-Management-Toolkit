#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int *faults;
    int **states;
    int fault_count;
} PagingResult;

/* ================= FIFO ================= */
PagingResult FIFO(int pages[], int n, int frames) {
    PagingResult result;
    int *memory = (int *)malloc(frames * sizeof(int));
    int index = 0;

    result.faults = (int *)calloc(n, sizeof(int));
    result.states = (int **)malloc(n * sizeof(int *));
    result.fault_count = 0;

    for(int i = 0; i < frames; i++) memory[i] = -1;

    for(int i = 0; i < n; i++) {
        int found = 0;
        result.states[i] = (int *)malloc(frames * sizeof(int));

        for(int j = 0; j < frames; j++) {
            if(memory[j] == pages[i]) {
                found = 1;
                break;
            }
        }

        if(!found) {
            memory[index] = pages[i];
            index = (index + 1) % frames;
            result.faults[i] = 1;
            result.fault_count++;
        }

        for(int j = 0; j < frames; j++)
            result.states[i][j] = memory[j];
    }

    free(memory);
    return result;
}

/* ================= LRU ================= */
PagingResult LRU(int pages[], int n, int frames) {
    PagingResult result;
    int *memory = (int *)malloc(frames * sizeof(int));
    int *recent = (int *)malloc(frames * sizeof(int));

    result.faults = (int *)calloc(n, sizeof(int));
    result.states = (int **)malloc(n * sizeof(int *));
    result.fault_count = 0;

    for(int i = 0; i < frames; i++) {
        memory[i] = -1;
        recent[i] = -1;
    }

    for(int i = 0; i < n; i++) {
        int found = -1;
        result.states[i] = (int *)malloc(frames * sizeof(int));

        for(int j = 0; j < frames; j++) {
            if(memory[j] == pages[i]) {
                found = j;
                break;
            }
        }

        if(found != -1) {
            recent[found] = i;
        } else {
            int lru = 0;
            for(int j = 1; j < frames; j++)
                if(recent[j] < recent[lru]) lru = j;

            memory[lru] = pages[i];
            recent[lru] = i;
            result.faults[i] = 1;
            result.fault_count++;
        }

        for(int j = 0; j < frames; j++)
            result.states[i][j] = memory[j];
    }

    free(memory);
    free(recent);
    return result;
}

/* ================= OPTIMAL ================= */
int findOptimal(int pages[], int framesArr[], int n, int index, int frames) {
    int farthest = index, pos = -1;

    for(int i = 0; i < frames; i++) {
        int j;
        for(j = index; j < n; j++) {
            if(framesArr[i] == pages[j]) {
                if(j > farthest) {
                    farthest = j;
                    pos = i;
                }
                break;
            }
        }
        if(j == n) return i;
    }
    return (pos == -1) ? 0 : pos;
}

PagingResult OPT(int pages[], int n, int frames) {
    PagingResult result;
    int *memory = (int *)malloc(frames * sizeof(int));

    result.faults = (int *)calloc(n, sizeof(int));
    result.states = (int **)malloc(n * sizeof(int *));
    result.fault_count = 0;

    for(int i = 0; i < frames; i++) memory[i] = -1;

    for(int i = 0; i < n; i++) {
        int found = 0;
        result.states[i] = (int *)malloc(frames * sizeof(int));

        for(int j = 0; j < frames; j++) {
            if(memory[j] == pages[i]) {
                found = 1;
                break;
            }
        }

        if(!found) {
            int pos = -1;

            for(int j = 0; j < frames; j++) {
                if(memory[j] == -1) {
                    pos = j;
                    break;
                }
            }

            if(pos == -1)
                pos = findOptimal(pages, memory, n, i + 1, frames);

            memory[pos] = pages[i];
            result.faults[i] = 1;
            result.fault_count++;
        }

        for(int j = 0; j < frames; j++)
            result.states[i][j] = memory[j];
    }

    free(memory);
    return result;
}

/* ================= AI (Frequency-Based) ================= */
PagingResult AI(int pages[], int n, int frames) {
    PagingResult result;
    int *memory = (int *)malloc(frames * sizeof(int));
    int freq[100] = {0};

    result.faults = (int *)calloc(n, sizeof(int));
    result.states = (int **)malloc(n * sizeof(int *));
    result.fault_count = 0;

    for(int i = 0; i < frames; i++) memory[i] = -1;

    for(int i = 0; i < n; i++) {
        freq[pages[i]]++;
        int found = 0;
        result.states[i] = (int *)malloc(frames * sizeof(int));

        for(int j = 0; j < frames; j++) {
            if(memory[j] == pages[i]) {
                found = 1;
                break;
            }
        }

        if(!found) {
            int pos = -1;

            for(int j = 0; j < frames; j++) {
                if(memory[j] == -1) {
                    pos = j;
                    break;
                }
            }

            if(pos == -1) {
                int min = 9999;
                for(int j = 0; j < frames; j++) {
                    if(freq[memory[j]] < min) {
                        min = freq[memory[j]];
                        pos = j;
                    }
                }
            }

            memory[pos] = pages[i];
            result.faults[i] = 1;
            result.fault_count++;
        }

        for(int j = 0; j < frames; j++)
            result.states[i][j] = memory[j];
    }

    free(memory);
    return result;
}

/* ================= WRITE RESULTS ================= */
void write_results(int pages[], int n, int frames,
                   PagingResult fifo, PagingResult lru,
                   PagingResult opt, PagingResult ai) {

    FILE *fp = fopen("paging_results.txt", "w");

    fprintf(fp, "REFS");
    for(int i = 0; i < n; i++) fprintf(fp, " %d", pages[i]);
    fprintf(fp, "\n");

    fprintf(fp, "FRAMES %d\n", frames);

    PagingResult arr[4] = {fifo, lru, opt, ai};
    char *names[4] = {"FIFO", "LRU", "OPT", "AI"};

    int best = arr[0].fault_count;
    char bestAlgo[10];
    strcpy(bestAlgo, names[0]);

    for(int a = 0; a < 4; a++) {
        fprintf(fp, "ALGO %s\n", names[a]);
        fprintf(fp, "SUMMARY %d\n", arr[a].fault_count);

        for(int i = 0; i < n; i++) {
            fprintf(fp, "STEP %d %d", pages[i], arr[a].faults[i]);
            for(int j = 0; j < frames; j++)
                fprintf(fp, " %d", arr[a].states[i][j]);
            fprintf(fp, "\n");
        }

        if(arr[a].fault_count < best) {
            best = arr[a].fault_count;
            strcpy(bestAlgo, names[a]);
        }
    }

    fprintf(fp, "BETTER %s\n", bestAlgo);
    fclose(fp);
}

/* ================= FREE ================= */
void free_result(PagingResult r, int n) {
    for(int i = 0; i < n; i++)
        free(r.states[i]);
    free(r.states);
    free(r.faults);
}

/* ================= MAIN ================= */
int main(int argc, char *argv[]) {
    int n, frames;
    int visualize = 1;

    if(argc > 1 && strcmp(argv[1], "--no-visualize") == 0)
        visualize = 0;

    printf("Enter number of pages: ");
    scanf("%d", &n);

    int *pages = (int *)malloc(n * sizeof(int));

    printf("Enter reference string:\n");
    for(int i = 0; i < n; i++)
        scanf("%d", &pages[i]);

    printf("Enter frames: ");
    scanf("%d", &frames);

    PagingResult fifo = FIFO(pages, n, frames);
    PagingResult lru  = LRU(pages, n, frames);
    PagingResult opt  = OPT(pages, n, frames);
    PagingResult ai   = AI(pages, n, frames);

    write_results(pages, n, frames, fifo, lru, opt, ai);

    printf("\nFIFO: %d\nLRU: %d\nOPT: %d\nAI: %d\n",
           fifo.fault_count, lru.fault_count,
           opt.fault_count, ai.fault_count);

    free_result(fifo, n);
    free_result(lru, n);
    free_result(opt, n);
    free_result(ai, n);
    free(pages);

    return 0;
}