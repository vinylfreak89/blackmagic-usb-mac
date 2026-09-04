#include "publish_queue.h"
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

int (*pq_test_fail_init)(int which) = NULL;
#define FAIL_INIT(w) (pq_test_fail_init && pq_test_fail_init(w))

typedef struct pq_job { char *partial, *final; struct pq_job *next; } pq_job;
struct publish_queue {
    pthread_mutex_t m; pthread_cond_t c; pthread_t thread;
    pq_job *head, *tail; size_t queued, capacity; pq_job *current; int quit;
    pq_publish_fn publish; void *ctx;
};

static void job_free(pq_job *j){ free(j->partial); free(j->final); free(j); }

static void *pq_main(void *arg){
    publish_queue *q = arg;
    pthread_setname_np("sidecar-publish");
    for (;;){
        pthread_mutex_lock(&q->m);
        while (!q->head && !q->quit) pthread_cond_wait(&q->c, &q->m);
        pq_job *j = q->head;
        if (j){ q->head = j->next; if (!q->head) q->tail = NULL; q->queued--; q->current = j; }
        int quit = q->quit && !j;
        pthread_mutex_unlock(&q->m);
        if (quit) return NULL;
        q->publish(q->ctx, j->partial, j->final);
        pthread_mutex_lock(&q->m); q->current = NULL; pthread_cond_broadcast(&q->c); pthread_mutex_unlock(&q->m);
        job_free(j);
    }
}

int pq_open(publish_queue **out, size_t capacity, pq_publish_fn publish, void *ctx){
    *out = NULL;
    if (!publish || capacity == 0){ errno = EINVAL; return -1; }
    publish_queue *q = calloc(1, sizeof *q); if (!q){ errno = ENOMEM; return -1; }
    q->capacity = capacity; q->publish = publish; q->ctx = ctx;
    if (FAIL_INIT(0) || pthread_mutex_init(&q->m, NULL) != 0){ free(q); errno = EAGAIN; return -1; }
    if (FAIL_INIT(1) || pthread_cond_init(&q->c, NULL) != 0){ pthread_mutex_destroy(&q->m); free(q); errno = EAGAIN; return -1; }
    if (FAIL_INIT(2) || pthread_create(&q->thread, NULL, pq_main, q) != 0){ pthread_cond_destroy(&q->c); pthread_mutex_destroy(&q->m); free(q); errno = EAGAIN; return -1; }
    *out = q; return 0;
}

int pq_enqueue(publish_queue *q, const char *partial, const char *final){
    if (!q || !partial || !final){ errno = EINVAL; return -1; }
    pq_job *j = calloc(1, sizeof *j); if (!j){ errno = ENOMEM; return -1; }
    j->partial = strdup(partial); j->final = strdup(final);
    if (!j->partial || !j->final){ job_free(j); errno = ENOMEM; return -1; }
    pthread_mutex_lock(&q->m);
    if (q->queued >= q->capacity){ pthread_mutex_unlock(&q->m); job_free(j); errno = ENOSPC; return -1; }
    if (q->tail) q->tail->next = j; else q->head = j;
    q->tail = j; q->queued++;
    pthread_cond_broadcast(&q->c);
    pthread_mutex_unlock(&q->m);
    return 0;
}

int pq_reserved(publish_queue *q, const char *final){
    if (!q || !final) return 0;
    int r = 0;
    pthread_mutex_lock(&q->m);
    if (q->current && strcmp(q->current->final, final) == 0) r = 1;
    for (pq_job *j = q->head; j && !r; j = j->next) if (strcmp(j->final, final) == 0) r = 1;
    pthread_mutex_unlock(&q->m);
    return r;
}

size_t pq_pending(publish_queue *q){
    if (!q) return 0;
    pthread_mutex_lock(&q->m); size_t n = q->queued + (q->current ? 1 : 0); pthread_mutex_unlock(&q->m); return n;
}

void pq_close(publish_queue *q){
    if (!q) return;
    pthread_mutex_lock(&q->m); q->quit = 1; pthread_cond_broadcast(&q->c); pthread_mutex_unlock(&q->m);
    pthread_join(q->thread, NULL);              /* the thread exits only once the queue is empty: every job was published */
    pthread_cond_destroy(&q->c); pthread_mutex_destroy(&q->m); free(q);
}
