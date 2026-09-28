#include "timing_report.h"
#include <dispatch/dispatch.h>
#include <errno.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>

struct timing_report {
    tr_event *ev; unsigned cap;
    _Atomic uint64_t head, tail, dropped;   /* monotonic: the producer publishes head, the reporter tail */
    dispatch_semaphore_t sem;               /* signal never blocks or allocates: safe on the worker */
    _Atomic int stop; pthread_t thr;
    void (*emit)(void *, const tr_event *); void *ctx;
};

static void *tr_main(void *arg){
    timing_report *r = arg;
    for (;;){
        dispatch_semaphore_wait(r->sem, DISPATCH_TIME_FOREVER);   /* one signal per post, one at close */
        uint64_t t = atomic_load_explicit(&r->tail, memory_order_relaxed);
        while (t != atomic_load_explicit(&r->head, memory_order_acquire)){
            tr_event e = r->ev[t % r->cap];
            atomic_store_explicit(&r->tail, t + 1, memory_order_release);   /* slot free before the (slow) emit */
            r->emit(r->ctx, &e); t++;
        }
        if (atomic_load(&r->stop)) return NULL;
    }
}

int tr_open(timing_report **out, unsigned capacity, void (*emit)(void *, const tr_event *), void *ctx){
    if (!out || !capacity || !emit){ errno = EINVAL; return -1; }
    timing_report *r = calloc(1, sizeof *r); if (!r) return -1;
    r->ev = calloc(capacity, sizeof *r->ev); if (!r->ev){ free(r); return -1; }
    r->cap = capacity; r->emit = emit; r->ctx = ctx;
    r->sem = dispatch_semaphore_create(0); if (!r->sem){ free(r->ev); free(r); errno = ENOMEM; return -1; }
    if (pthread_create(&r->thr, NULL, tr_main, r) != 0){ dispatch_release(r->sem); free(r->ev); free(r); errno = EAGAIN; return -1; }
    *out = r; return 0;
}

void tr_post(timing_report *r, const tr_event *e){
    if (!r) return;
    uint64_t h = atomic_load_explicit(&r->head, memory_order_relaxed);
    if (h - atomic_load_explicit(&r->tail, memory_order_acquire) >= r->cap){ atomic_fetch_add(&r->dropped, 1); return; }
    r->ev[h % r->cap] = *e;
    atomic_store_explicit(&r->head, h + 1, memory_order_release);
    dispatch_semaphore_signal(r->sem);
}

uint64_t tr_close(timing_report *r){
    if (!r) return 0;
    atomic_store(&r->stop, 1); dispatch_semaphore_signal(r->sem);
    pthread_join(r->thr, NULL);
    uint64_t d = atomic_load(&r->dropped);
    dispatch_release(r->sem); free(r->ev); free(r);
    return d;
}
