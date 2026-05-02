#include <stdlib.h>
#include <stdio.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <time.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include "resource.h"

SharedData *global_data;

/* Signal handler */
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
            printf("3. Logout\n");
            printf("Choice: ");
            fflush(stdout);
            break;
        }
    }
}

/* Semaphore Lock */
void lock(int semid)
{
    struct sembuf sb = {0,-1,0};
    semop(semid,&sb,1);
}

/* Semaphore Unlock */
void unlock(int semid)
{
    struct sembuf sb = {0,1,0};
    semop(semid,&sb,1);
}

/* Logging */
void log_event(int id,char action[],char client_name[])
{
    FILE *fp=fopen("resource_log.txt","a");

    if(fp==NULL)
    {
        printf("Error opening log file\n");
        return;
    }

    time_t now=time(NULL);
    char *t=ctime(&now);
    t[strlen(t)-1]='\0';

    fprintf(fp,"%-24s %-8s %-6d %-10d %-10s\n",
            t,client_name,getpid(),id,action);

    fclose(fp);
}

int main()
{
    key_t shmkey=5678;
    key_t semkey=9999;

    int shmid=shmget(shmkey,sizeof(SharedData),0666);
    int semid=semget(semkey,1,0666);

    if(shmid<0 || semid<0)
    {
        printf("Manager not running. Start manager first.\n");
        return 1;
    }

    SharedData *data=(SharedData*)shmat(shmid,NULL,0);
    global_data=data;

    if(data==(void*)-1)
    {
        printf("Shared memory attach failed\n");
        return 1;
    }

    if(data->manager_running!=1)
    {
        printf("Manager is not running. Client exiting.\n");
        shmdt(data);
        return 1;
    }

    signal(SIGUSR1,warning_handler);

    int session_choice;

    while(1)
    {
        printf("\n===== CLIENT SESSION MANAGER =====\n");
        printf("1. Login Client\n");
        printf("2. Exit\n");

        printf("Choice: ");
        scanf("%d",&session_choice);

        if(session_choice==2)
        {
            printf("Exiting client program...\n");
            break;
        }

        if(session_choice!=1)
        {
            printf("Invalid choice\n");
            continue;
        }

        char client_name[50];

        printf("\nEnter Client Name: ");
        scanf("%s",client_name);

        /* CHECK IF CLIENT ALREADY EXISTS */

        int existing=-1;

        for(int i=0;i<data->client_count;i++)
        {
            if(strcmp(data->client_names[i],client_name)==0)
            {
                existing=i;
                break;
            }
        }

        if(existing!=-1)
{
    printf("Client already active.\n");
    printf("Using previous PID: %d\n",data->client_pids[existing]);

    int choice,id;

    while(1)
    {
        printf("\nCurrent Resource Status:\n");

        for(int i=0;i<MAX_RESOURCES;i++)
        {
            if(data->resource[i]==0)
                printf("Resource %d : FREE\n",i);
            else
                printf("Resource %d : BUSY (Owner: %s)\n",i,data->owner[i]);
        }

        printf("\n1. Request Resource\n");
        printf("2. Release Resource\n");
        printf("3. Logout\n");

        printf("Choice: ");
        scanf("%d",&choice);

        if(choice==3)
        {
            printf("Logging out...\n");
            break;
        }

        printf("Enter Resource ID (0-4): ");
        scanf("%d",&id);

        if(id<0 || id>=MAX_RESOURCES)
        {
            printf("Invalid Resource ID\n");
            continue;
        }

        lock(semid);

        if(choice==1)
        {
            if(data->resource[id]==0)
            {
                data->resource[id]=1;
                strcpy(data->owner[id],client_name);
                data->owner_pid[id]=data->client_pids[existing];

                printf("Resource %d Allocated to %s\n",id,client_name);

                log_event(id,"ALLOCATED",client_name);
            }
            else
            {
                printf("Resource Busy! Owned by %s\n",data->owner[id]);
            }
        }

        else if(choice==2)
        {
            if(data->owner_pid[id]==data->client_pids[existing])
            {
                data->resource[id]=0;
                data->owner[id][0]='\0';
                data->owner_pid[id]=0;

                printf("Resource %d Released\n",id);

                log_event(id,"RELEASED",client_name);
            }
            else
            {
                printf("You cannot release this resource.\n");
            }
        }

        unlock(semid);
    }

    continue;
}

        /* CREATE NEW PROCESS */

        pid_t pid=fork();

        if(pid<0)
        {
            printf("Process creation failed\n");
            continue;
        }

        if(pid==0)
        {
            /* CHILD PROCESS */

            printf("Client PID: %d\n",getpid());

            strcpy(data->client_names[data->client_count],client_name);
            data->client_pids[data->client_count]=getpid();
            data->client_count++;

            int choice,id;

            while(1)
            {
                printf("\nCurrent Resource Status:\n");

                for(int i=0;i<MAX_RESOURCES;i++)
                {
                    if(data->resource[i]==0)
                        printf("Resource %d : FREE\n",i);
                    else
                        printf("Resource %d : BUSY (Owner: %s)\n",i,data->owner[i]);
                }

                printf("\n1. Request Resource\n");
                printf("2. Release Resource\n");
                printf("3. Logout\n");

                printf("Choice: ");
                scanf("%d",&choice);

                if(choice==3)
                {
                    printf("Logging out...\n");
                    exit(0);
                }

                printf("Enter Resource ID (0-4): ");
                scanf("%d",&id);

                if(id<0 || id>=MAX_RESOURCES)
                {
                    printf("Invalid Resource ID\n");
                    continue;
                }

                lock(semid);

                if(data->manager_running==0)
                {
                    printf("Manager stopped. Client exiting...\n");
                    unlock(semid);
                    exit(0);
                }

                /* REQUEST RESOURCE */

                if(choice==1)
                {
                    if(data->resource[id]==0)
                    {
                        data->resource[id]=1;
                        strcpy(data->owner[id],client_name);
                        data->owner_pid[id]=getpid();

                        printf("Resource %d Allocated to %s\n",id,client_name);

                        log_event(id,"ALLOCATED",client_name);
                    }
                    else
                    {
                        printf("Resource Busy! Owned by %s\n",data->owner[id]);

                        if((data->rear+1)%MAX_QUEUE==data->front)
                        {
                            printf("Waiting Queue FULL!\n");
                            kill(data->owner_pid[id],SIGUSR1);
                        }
                        else
                        {
                            if(data->front==-1)
                                data->front=0;

                            data->rear=(data->rear+1)%MAX_QUEUE;
                            data->waiting_queue[data->rear]=getpid();

                            printf("Added to waiting queue.\n");

                            log_event(id,"WAITING",client_name);
                        }
                    }
                }

                /* RELEASE RESOURCE */

                else if(choice==2)
                {
                    if(data->resource[id]==0)
                    {
                        printf("Resource %d is already FREE.\n",id);
                    }
                    else if(data->owner_pid[id]==getpid())
                    {
                        printf("Resource %d Released\n",id);

                        log_event(id,"RELEASED",client_name);

                        data->resource[id]=0;
                        data->owner[id][0]='\0';
                        data->owner_pid[id]=0;
                    }
                    else
                    {
                        printf("You cannot release this resource.\n");
                    }
                }

                else
                {
                    printf("Invalid Choice\n");
                }

                unlock(semid);
            }
        }
        else
        {
            /* PARENT PROCESS */
            wait(NULL);
        }
    }

    shmdt(data);

    return 0;
}