/* timing_report: events reach emit in order; a hung emit (a log write on a stalled disk) never
 * blocks tr_post; a full ring drops and counts instead of waiting; close emits what is queued. */
#include "timing_report.h"
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)
static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
static int hang, hung, released; static uint64_t seen[4096]; static unsigned nseen;
static void emit(void *ctx, const tr_event *e){
    (void)ctx; pthread_mutex_lock(&m);
    if (nseen < 4096) seen[nseen++] = e->counter;
    if (hang && !released){
        hung = 1; pthread_cond_broadcast(&cv);
        struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_sec += 60;
        while (!released) if (pthread_cond_timedwait(&cv, &m, &ts)){ fprintf(stderr, "FAIL: emit never released\n"); _exit(2); }
    }
    pthread_cond_broadcast(&cv); pthread_mutex_unlock(&m);
}
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

int main(void){
    /* 1. Order and completeness, 1000 events through a 16-slot ring with a fast emit: the producer
     * posts only when there is room (it would otherwise drop, which is case 2). */
    timing_report *r; CHECK(tr_open(&r, 16, emit, NULL) == 0, "open");
    for (uint64_t i = 0; i < 1000; i++){
        pthread_mutex_lock(&m); struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_sec += 60;
        while (i >= 16 && nseen + 16 <= i) if (pthread_cond_timedwait(&cv, &m, &ts)){ fprintf(stderr, "FAIL: reporter stalled\n"); _exit(2); }
        pthread_mutex_unlock(&m);
        tr_event e; memset(&e, 0, sizeof e); e.counter = i; tr_post(r, &e);
    }
    CHECK(tr_close(r) == 0, "no drops expected when the producer never outran the ring");
    int inorder = nseen == 1000; for (unsigned i = 0; inorder && i < 1000; i++) inorder = seen[i] == i;
    CHECK(inorder, "events not delivered complete and in order (%u seen)", nseen);

    /* 2. Hung emit: the first event hangs the reporter; 100 more posts return at once, the ring keeps
     * 8, the rest are counted as dropped; after release, close delivers the kept ones in order. */
    nseen = 0; hang = 1; hung = 0; released = 0;
    CHECK(tr_open(&r, 8, emit, NULL) == 0, "open (hung)");
    tr_event e; memset(&e, 0, sizeof e); e.counter = 0; tr_post(r, &e);
    pthread_mutex_lock(&m); struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_sec += 60;
    while (!hung) if (pthread_cond_timedwait(&cv, &m, &ts)){ fprintf(stderr, "FAIL: reporter never emitted\n"); _exit(2); }
    pthread_mutex_unlock(&m);
    double t0 = now();
    for (uint64_t i = 1; i <= 100; i++){ e.counter = i; tr_post(r, &e); }
    double took = now() - t0;
    CHECK(took < 0.1, "posts blocked behind a hung reporter (%.3f s)", took);
    pthread_mutex_lock(&m); released = 1; pthread_cond_broadcast(&cv); pthread_mutex_unlock(&m);
    uint64_t dropped = tr_close(r);
    CHECK(dropped == 92, "expected 92 dropped (100 posted, 8 slots), got %llu", (unsigned long long)dropped);
    inorder = nseen == 9; for (unsigned i = 0; inorder && i < 9; i++) inorder = seen[i] == i;
    CHECK(inorder, "after release: expected events 0..8 in order, saw %u", nseen);

    if (fails){ printf("timing_report tests: %d FAILURES\n", fails); return 1; }
    printf("timing_report tests: PASS\n"); return 0;
}
