#include "mockcuda.h"
#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>

static pthread_mutex_t internal_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_t bg;
static volatile int running = 0;

static void* bg_thread(void* arg) {
    (void)arg;
    while (running) {
        // Simulate the driver occasionally taking a global lock
        pthread_mutex_lock(&internal_lock);
        usleep(1000);   // hold it briefly
        pthread_mutex_unlock(&internal_lock);
        usleep(1000);
    }
    return NULL;
}

void mockcuda_init(void) {
    if (!running) {
        running = 1;
        pthread_create(&bg, NULL, bg_thread, NULL);
    }
}

void mockcuda_shutdown(void) {
    if (running) {
        running = 0;
        pthread_join(bg, NULL);
    }
}

void mockcuda_free(void* p) {
    // Simulate the driver taking an internal lock before freeing
    pthread_mutex_lock(&internal_lock);
    usleep(1000);       // small latency
    free(p);            // <- second free on same pointer is UB/abort
    pthread_mutex_unlock(&internal_lock);
}
