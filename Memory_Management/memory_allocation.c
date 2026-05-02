#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#define MAX_LABEL 32
#define MAX_PROC_LIST 512

typedef enum {
    MODE_FIXED = 0,
    MODE_VARIABLE = 1
} AllocationMode;

typedef struct {
    char id[MAX_LABEL];
    long long size_bytes;
} MemoryBlock;

typedef struct {
    char id[MAX_LABEL];
    long long size_bytes;
} ProcessInfo;

typedef struct {
    int allocated;
    int block_index;
    long long block_size_bytes;
    long long process_size_bytes;
    long long internal_fragmentation;
} ProcessResult;

typedef struct {
    char id[MAX_LABEL];
    long long size_bytes;
    long long remaining_bytes;
    int allocated;
    char process_list[MAX_PROC_LIST];
} BlockState;

typedef struct {
    char code[16];
    char title[32];
    ProcessResult *rows;
    BlockState *blocks;
    int allocated_count;
    int failed_count;
    long long internal_fragmentation;
    long long external_fragmentation;
    double utilization;
    int external_warning;
} AlgorithmResult;

long long convertToBytes(double value, const char unit[])
{
    if(value < 0)
    {
        printf("Error: Memory size cannot be negative.\n");
        exit(1);
    }

    if(strcasecmp(unit, "bit") == 0)
        return (long long)(value / 8.0);
    if(strcasecmp(unit, "byte") == 0 || strcasecmp(unit, "bytes") == 0 || strcasecmp(unit, "b") == 0)
        return (long long)value;
    if(strcasecmp(unit, "kb") == 0)
        return (long long)(value * 1024.0);
    if(strcasecmp(unit, "mb") == 0)
        return (long long)(value * 1024.0 * 1024.0);
    if(strcasecmp(unit, "gb") == 0)
        return (long long)(value * 1024.0 * 1024.0 * 1024.0);
    if(strcasecmp(unit, "tb") == 0)
        return (long long)(value * 1024.0 * 1024.0 * 1024.0 * 1024.0);

    printf("Warning: Invalid unit '%s'. Assuming Byte.\n", unit);
    return (long long)value;
}

long long parseMemoryInput()
{
    char line[200];
    double value = 0.0;
    char unit[32] = "Byte";

    if(fgets(line, sizeof(line), stdin) == NULL)
        return 0;

    if(sscanf(line, "%lf %31s", &value, unit) < 1)
        return 0;

    return convertToBytes(value, unit);
}

void append_process(char target[], const char process_id[])
{
    if(target[0] != '\0')
        strncat(target, ",", MAX_PROC_LIST - strlen(target) - 1);
    strncat(target, process_id, MAX_PROC_LIST - strlen(target) - 1);
}

int pick_block(BlockState blocks[], int m, long long process_size, const char algorithm[])
{
    int chosen = -1;
    for(int i = 0; i < m; i++)
    {
        if(blocks[i].remaining_bytes < process_size)
            continue;

        if(chosen == -1)
        {
            chosen = i;
            if(strcmp(algorithm, "FIRST") == 0)
                break;
            continue;
        }

        if(strcmp(algorithm, "BEST") == 0)
        {
            if(blocks[i].remaining_bytes < blocks[chosen].remaining_bytes)
                chosen = i;
        }
        else if(strcmp(algorithm, "WORST") == 0)
        {
            if(blocks[i].remaining_bytes > blocks[chosen].remaining_bytes)
                chosen = i;
        }
    }
    return chosen;
}

long long compute_external_fragmentation(BlockState blocks[], int m, ProcessResult rows[], int n)
{
    long long total_free = 0;
    long long largest_free = 0;

    for(int i = 0; i < m; i++)
    {
        if(blocks[i].remaining_bytes <= 0)
            continue;
        total_free += blocks[i].remaining_bytes;
        if(blocks[i].remaining_bytes > largest_free)
            largest_free = blocks[i].remaining_bytes;
    }

    if(total_free == 0 || largest_free == 0)
        return 0;

    for(int i = 0; i < n; i++)
    {
        long long size = rows[i].process_size_bytes;
        if(rows[i].allocated)
            continue;
        if(size <= total_free && size > largest_free)
            return total_free - largest_free;
    }

    return 0;
}

int compute_external_warning(BlockState blocks[], int m, ProcessResult rows[], int n)
{
    long long total_free = 0;
    long long largest_free = 0;

    for(int i = 0; i < m; i++)
    {
        if(blocks[i].remaining_bytes <= 0)
            continue;
        total_free += blocks[i].remaining_bytes;
        if(blocks[i].remaining_bytes > largest_free)
            largest_free = blocks[i].remaining_bytes;
    }

    for(int i = 0; i < n; i++)
    {
        long long size = rows[i].process_size_bytes;
        if(rows[i].allocated)
            continue;
        if(size <= total_free && size > largest_free)
            return 1;
    }

    return 0;
}

AlgorithmResult run_algorithm(
    MemoryBlock blocks[],
    int m,
    ProcessInfo processes[],
    int n,
    AllocationMode mode,
    const char algorithm_code[],
    const char algorithm_title[]
)
{
    AlgorithmResult result;
    long long total_memory = 0;
    long long used_process_bytes = 0;

    strcpy(result.code, algorithm_code);
    strcpy(result.title, algorithm_title);
    result.rows = (ProcessResult *)calloc((size_t)n, sizeof(ProcessResult));
    result.blocks = (BlockState *)calloc((size_t)m, sizeof(BlockState));
    result.allocated_count = 0;
    result.failed_count = 0;
    result.internal_fragmentation = 0;
    result.external_fragmentation = 0;
    result.utilization = 0.0;
    result.external_warning = 0;

    for(int i = 0; i < m; i++)
    {
        strcpy(result.blocks[i].id, blocks[i].id);
        result.blocks[i].size_bytes = blocks[i].size_bytes;
        result.blocks[i].remaining_bytes = blocks[i].size_bytes;
        result.blocks[i].allocated = 0;
        result.blocks[i].process_list[0] = '\0';
        total_memory += blocks[i].size_bytes;
    }

    for(int i = 0; i < n; i++)
    {
        int chosen = pick_block(result.blocks, m, processes[i].size_bytes, algorithm_code);

        result.rows[i].process_size_bytes = processes[i].size_bytes;
        result.rows[i].allocated = 0;
        result.rows[i].block_index = -1;
        result.rows[i].block_size_bytes = 0;
        result.rows[i].internal_fragmentation = 0;

        if(chosen == -1)
        {
            result.failed_count++;
            continue;
        }

        result.rows[i].allocated = 1;
        result.rows[i].block_index = chosen;
        result.rows[i].block_size_bytes = result.blocks[chosen].size_bytes;
        if(mode == MODE_FIXED)
        {
            result.rows[i].internal_fragmentation = result.blocks[chosen].size_bytes - processes[i].size_bytes;
            result.blocks[chosen].remaining_bytes = 0;
        }
        else
        {
            result.rows[i].internal_fragmentation = 0;
            result.blocks[chosen].remaining_bytes -= processes[i].size_bytes;
        }

        result.blocks[chosen].allocated = 1;
        append_process(result.blocks[chosen].process_list, processes[i].id);
        result.internal_fragmentation += result.rows[i].internal_fragmentation;
        result.allocated_count++;
        used_process_bytes += processes[i].size_bytes;
    }

    result.external_fragmentation = compute_external_fragmentation(result.blocks, m, result.rows, n);
    result.external_warning = compute_external_warning(result.blocks, m, result.rows, n);
    result.utilization = total_memory > 0 ? ((double)used_process_bytes / (double)total_memory) * 100.0 : 0.0;
    return result;
}

int is_better_result(const AlgorithmResult *candidate, const AlgorithmResult *best, AllocationMode mode)
{
    if(best == NULL)
        return 1;

    if(candidate->external_warning != best->external_warning)
        return candidate->external_warning < best->external_warning;

    if(candidate->allocated_count != best->allocated_count)
        return candidate->allocated_count > best->allocated_count;

    if(candidate->external_fragmentation != best->external_fragmentation)
        return candidate->external_fragmentation < best->external_fragmentation;

    if(mode == MODE_FIXED && candidate->internal_fragmentation != best->internal_fragmentation)
        return candidate->internal_fragmentation < best->internal_fragmentation;

    if(candidate->utilization != best->utilization)
        return candidate->utilization > best->utilization;

    return 0;
}

void write_results_file(
    const char *mode_text,
    MemoryBlock blocks[],
    int m,
    ProcessInfo processes[],
    int n,
    AlgorithmResult results[],
    int best_index
)
{
    FILE *fp = fopen("memory_results.txt", "w");
    if(fp == NULL)
    {
        printf("Error opening memory_results.txt\n");
        exit(1);
    }

    fprintf(fp, "MODE %s\n", mode_text);
    fprintf(fp, "BLOCK_COUNT %d\n", m);
    fprintf(fp, "PROCESS_COUNT %d\n", n);
    for(int i = 0; i < m; i++)
        fprintf(fp, "BLOCK %s %lld\n", blocks[i].id, blocks[i].size_bytes);
    for(int i = 0; i < n; i++)
        fprintf(fp, "PROCESS %s %lld\n", processes[i].id, processes[i].size_bytes);

    for(int r = 0; r < 3; r++)
    {
        fprintf(fp, "ALGO %s\n", results[r].code);
        fprintf(
            fp,
            "SUMMARY %d %d %lld %lld %.6f %d\n",
            results[r].allocated_count,
            results[r].failed_count,
            results[r].internal_fragmentation,
            results[r].external_fragmentation,
            results[r].utilization,
            results[r].external_warning
        );

        for(int i = 0; i < n; i++)
        {
            fprintf(
                fp,
                "ROW %s %d %d %lld %lld %lld\n",
                processes[i].id,
                results[r].rows[i].allocated,
                results[r].rows[i].block_index + 1,
                results[r].rows[i].block_size_bytes,
                results[r].rows[i].process_size_bytes,
                results[r].rows[i].internal_fragmentation
            );
        }

        for(int i = 0; i < m; i++)
        {
            fprintf(
                fp,
                "BLOCKSTATE %s %lld %lld %d %s\n",
                results[r].blocks[i].id,
                results[r].blocks[i].size_bytes,
                results[r].blocks[i].remaining_bytes,
                results[r].blocks[i].allocated,
                results[r].blocks[i].process_list[0] ? results[r].blocks[i].process_list : "NONE"
            );
        }
        fprintf(fp, "ENDALGO\n");
    }

    fprintf(fp, "BEST_ALGO %s\n", results[best_index].code);
    fclose(fp);
}

void print_console_summary(AlgorithmResult results[], int best_index)
{
    for(int i = 0; i < 3; i++)
    {
        printf("\n%s Allocation\n", results[i].title);
        printf("Allocated Processes : %d\n", results[i].allocated_count);
        printf("Internal Fragmentation : %lld Bytes\n", results[i].internal_fragmentation);
        printf("External Fragmentation : %lld Bytes\n", results[i].external_fragmentation);
        printf("Memory Utilization : %.2f%%\n", results[i].utilization);
    }
    printf("\nBest Algorithm: %s\n", results[best_index].title);
}

int main(int argc, char *argv[])
{
    int m, n;
    int visualize = 1;
    char mode_text[32];
    AllocationMode mode;
    MemoryBlock *blocks;
    ProcessInfo *processes;
    AlgorithmResult results[3];
    int best_index = 0;

    if(argc > 1 && strcmp(argv[1], "--no-visualize") == 0)
        visualize = 0;

    printf("===== Memory Allocation Simulator =====\n");
    printf("Enter allocation type (FIXED or VARIABLE): ");
    scanf("%31s", mode_text);
    getchar();

    mode = strcasecmp(mode_text, "VARIABLE") == 0 ? MODE_VARIABLE : MODE_FIXED;
    strcpy(mode_text, mode == MODE_VARIABLE ? "VARIABLE" : "FIXED");

    printf("Enter number of memory blocks: ");
    scanf("%d", &m);
    getchar();
    blocks = (MemoryBlock *)calloc((size_t)m, sizeof(MemoryBlock));

    for(int i = 0; i < m; i++)
    {
        sprintf(blocks[i].id, "B%d", i + 1);
        printf("Block %d: ", i + 1);
        blocks[i].size_bytes = parseMemoryInput();
    }

    printf("Enter number of processes: ");
    scanf("%d", &n);
    getchar();
    processes = (ProcessInfo *)calloc((size_t)n, sizeof(ProcessInfo));

    for(int i = 0; i < n; i++)
    {
        sprintf(processes[i].id, "P%d", i + 1);
        printf("Process %d: ", i + 1);
        processes[i].size_bytes = parseMemoryInput();
    }

    results[0] = run_algorithm(blocks, m, processes, n, mode, "FIRST", "First Fit");
    results[1] = run_algorithm(blocks, m, processes, n, mode, "BEST", "Best Fit");
    results[2] = run_algorithm(blocks, m, processes, n, mode, "WORST", "Worst Fit");

    for(int i = 1; i < 3; i++)
    {
        if(is_better_result(&results[i], &results[best_index], mode))
            best_index = i;
    }

    write_results_file(mode_text, blocks, m, processes, n, results, best_index);
    print_console_summary(results, best_index);

    if(visualize)
        system("python3 visualization.py");

    for(int i = 0; i < 3; i++)
    {
        free(results[i].rows);
        free(results[i].blocks);
    }
    free(blocks);
    free(processes);
    return 0;
}
