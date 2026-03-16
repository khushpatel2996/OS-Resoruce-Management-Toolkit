#include <unistd.h>
#include <sys/types.h>
#include <stdio.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include "resource.h"

union semun
{
    int val;
};
int main()
{
    FILE *fp = fopen("resource_log.txt", "w");
    if (fp != NULL)
    {
        fclose(fp);
    }

    key_t shmkey = 5678;
    key_t semkey = 9999;

    int shmid = shmget(shmkey, sizeof(SharedData), 0666 | IPC_CREAT);

    if (shmid < 0)
    {
        printf("Shared memory creation failed\n");
        return 1;
    }

    SharedData *data = (SharedData *)shmat(shmid, NULL, 0);

    if (data == (void *)-1)
    {
        printf("Shared memory attach failed\n");
        return 1;
    }

    int semid = semget(semkey, 1, 0666 | IPC_CREAT);

    union semun setval;
    setval.val = 1;
    semctl(semid, 0, SETVAL, setval);

    /* initialize shared memory */
    memset(data, 0, sizeof(SharedData));
    data->front = -1;
    data->rear = -1;

    data->manager_running = 1;

    printf("=== OS Resource Manager Running ===\n");

    while (1)
    {

        printf("\nResource Status:\n");

        printf("\n---------------------------------\n");
        printf("ID\tSTATUS\t\tOWNER\n");
        printf("---------------------------------\n");

        for (int i = 0; i < MAX_RESOURCES; i++)
        {

            if (data->resource[i] == 0)
                printf("%d\tFREE\t\t-\n", i);
            else
                printf("%d\tALLOCATED\t%s\n", i, data->owner[i]);
        }

        printf("---------------------------------\n");

        sleep(3);
    }

    return 0;
}