#include <stdlib.h>
#include <stdio.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <time.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include "resource.h"

/* global pointer to shared memory */
SharedData *global_data;

/* Signal handler for owner warning */
void warning_handler(int sig)
{
    for (int i = 0; i < MAX_RESOURCES; i++)
    {
        if (global_data->owner_pid[i] == getpid() && global_data->front != -1)
        {
            printf("\n⚠ WARNING: Resource %d is needed by other clients.\n", i);
            printf("Please consider releasing it.\n");

            printf("\n1. Request Resource\n");
            printf("2. Release Resource\n");
            printf("3. Exit\n");
            printf("Choice: ");
            fflush(stdout);

            break;   // prevent multiple warnings
        }
    }
}

/* Lock function */
void lock(int semid)
{
    struct sembuf sb = {0, -1, 0};
    semop(semid, &sb, 1);
}

/* Unlock function */
void unlock(int semid)
{
    struct sembuf sb = {0, 1, 0};
    semop(semid, &sb, 1);
}

/* Logging function */
void log_event(int id, char action[], char client_name[])
{
    FILE *fp = fopen("resource_log.txt", "a");

    if (fp == NULL)
    {
        printf("Error opening log file\n");
        return;
    }

    time_t now = time(NULL);
    char *t = ctime(&now);
    t[strlen(t) - 1] = '\0';

    fprintf(fp, "%-24s %-8s %-6d %-10d %-10s\n",
            t, client_name, getpid(), id, action);

    fclose(fp);
}

int main()
{

    key_t shmkey = 5678;
    key_t semkey = 9999;

    int shmid = shmget(shmkey, sizeof(SharedData), 0666);
    int semid = semget(semkey, 1, 0666);

    if (shmid < 0 || semid < 0)
    {
        printf("Manager not running. Start manager first.\n");
        return 1;
    }

    SharedData *data = (SharedData *)shmat(shmid, NULL, 0);
    global_data = data;

    if (data == (void *)-1)
    {
        printf("Shared memory attach failed\n");
        return 1;
    }

    if (data->manager_running != 1)
    {
        printf("Manager is not running. Client exiting.\n");
        shmdt(data);
        return 1;
    }

    char client_name[50];

    printf("Enter Client Name: ");
    scanf("%s", client_name);

    printf("Client PID: %d\n", getpid());

    signal(SIGUSR1, warning_handler);

    int choice, id;

    while (1)
    {

        printf("\nCurrent Resource Status:\n");

        for (int i = 0; i < MAX_RESOURCES; i++)
        {
            if (data->resource[i] == 0)
                printf("Resource %d : FREE\n", i);
            else
                printf("Resource %d : BUSY (Owner: %s)\n", i, data->owner[i]);
        }

        printf("\n1. Request Resource\n");
        printf("2. Release Resource\n");
        printf("3. Exit\n");

        printf("Choice: ");
        scanf("%d", &choice);

        if (choice == 3)
        {
            printf("Exiting client...\n");
            break;
        }

        printf("Enter Resource ID (0-4): ");
        scanf("%d", &id);

        if (id < 0 || id >= MAX_RESOURCES)
        {
            printf("Invalid Resource ID\n");
            continue;
        }

        lock(semid);

        if (data->manager_running == 0)
        {
            printf("Manager stopped. Client exiting...\n");
            unlock(semid);
            break;
        }

        /* REQUEST RESOURCE */
        if (choice == 1)
        {

            if (data->resource[id] == 0)
            {

                data->resource[id] = 1;
                strcpy(data->owner[id], client_name);
                data->owner_pid[id] = getpid();

                printf("Resource %d Allocated to %s\n", id, client_name);

                log_event(id, "ALLOCATED", client_name);
            }

            else
            {

                printf("Resource Busy! Owned by %s\n", data->owner[id]);

                if ((data->rear + 1) % MAX_QUEUE == data->front)
                {

                    printf("Waiting Queue FULL!\n");
                    kill(data->owner_pid[id], SIGUSR1);
                }

                else
                {

                    if (data->front == -1)
                        data->front = 0;

                    data->rear = (data->rear + 1) % MAX_QUEUE;
                    data->waiting_queue[data->rear] = getpid();

                    printf("Added to waiting queue.\n");

                    log_event(id, "WAITING", client_name);

                    int count;

                    if (data->rear >= data->front)
                        count = data->rear - data->front + 1;
                    else
                        count = MAX_QUEUE - data->front + data->rear + 1;

                    if (count == MAX_QUEUE)
                    {
                        kill(data->owner_pid[id], SIGUSR1);
                    }
                }
            }
        }

        /* RELEASE RESOURCE */
        else if (choice == 2)
        {

            if (data->resource[id] == 0)
            {
                printf("Resource %d is already FREE.\n", id);
            }

            else if (data->owner_pid[id] == getpid())
            {

                printf("Resource %d Released\n", id);

                log_event(id, "RELEASED", client_name);

                if (data->front == -1)
                {

                    data->resource[id] = 0;
                    data->owner[id][0] = '\0';
                    data->owner_pid[id] = 0;
                }

                else
                {

                    int next_pid = data->waiting_queue[data->front];

                    printf("Resource %d automatically allocated to PID %d\n",
                           id, next_pid);

                    data->owner_pid[id] = next_pid;

                    log_event(id, "ALLOCATED", "AUTO");

                    if (data->front == data->rear)
                    {
                        data->front = -1;
                        data->rear = -1;
                    }
                    else
                    {
                        data->front = (data->front + 1) % MAX_QUEUE;
                    }
                }
            }

            else
            {

                printf("You cannot release this resource.\n");
                printf("Resource Busy! Owned by %s (PID %d)\n",
                       data->owner[id], data->owner_pid[id]);
            }
        }

        else
        {
            printf("Invalid Choice\n");
        }

        unlock(semid);
    }

    shmdt(data);

    return 0;
}