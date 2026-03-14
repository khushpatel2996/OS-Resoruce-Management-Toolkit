#ifndef RESOURCE_H
#define RESOURCE_H

#define MAX_RESOURCES 5
#define MAX_QUEUE 3

typedef struct {

    int resource[MAX_RESOURCES];
    char owner[MAX_RESOURCES][50];
    int owner_pid[MAX_RESOURCES];

    /* waiting queue for processes */
    int waiting_queue[MAX_QUEUE];
    int front;
    int rear;

    int manager_running;   // flag to check if manager is running

} SharedData;

#endif