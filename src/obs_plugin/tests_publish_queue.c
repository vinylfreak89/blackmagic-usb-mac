// Deciding test for publish_queue: FIFO order; the caller's strings are copied (mutated and freed
// right after enqueue); a gated job A blocks B without blocking the enqueuing thread; reservation
// sees queued and in-progress finals; a full queue refuses with ENOSPC and drops nothing; close
// drains everything already queued (including while A is still gated) and joins; each primitive
// initialisation failure is clean. Run under ASan/UBSan and TSan.
#include "publish_queue.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <pthread.h>
#include <stdatomic.h>
static int fails;
#define CHECK(c,...) do{ if(!(c)){ fails++; printf("FAIL: " __VA_ARGS__); printf("\n"); } }while(0)
static pthread_mutex_t gm = PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t gc = PTHREAD_COND_INITIALIZER; static int gate_open = 1;
static char log_[16][256]; static _Atomic int nlog;
static _Atomic int entered_gated;   /* handshake: the publisher has ENTERED the gated job (it is in progress, not queued) */
static void publish(void *ctx, const char *partial, const char *final){
    (void)ctx;
    if (strstr(final, "GATED")){ pthread_mutex_lock(&gm); atomic_store(&entered_gated, 1); pthread_cond_broadcast(&gc); while (!gate_open) pthread_cond_wait(&gc, &gm); pthread_mutex_unlock(&gm); }
    int i = atomic_fetch_add(&nlog, 1); if (i < 16) snprintf(log_[i], sizeof log_[i], "%s->%s", partial, final);
}
static void open_gate(void){ pthread_mutex_lock(&gm); gate_open = 1; pthread_cond_broadcast(&gc); pthread_mutex_unlock(&gm); }
static void close_gate(void){ pthread_mutex_lock(&gm); gate_open = 0; pthread_mutex_unlock(&gm); }
static int wait_log(int n){ for (int i = 0; i < 500; i++){ if (atomic_load(&nlog) >= n) return 1; usleep(10000); } return 0; }
static void *closer_main(void *a){ pq_close(a); return NULL; }
static publish_queue *race_q; static _Atomic int accepted, refused_cancel, refused_other;
static void *producer_main(void *a){ (void)a; for (int i = 0; i < 400; i++){ if (pq_enqueue(race_q, "/s/x.partial", "/d/x.csv") == 0) atomic_fetch_add(&accepted, 1); else if (errno == ECANCELED){ atomic_fetch_add(&refused_cancel, 1); break; } else if (errno != ENOSPC) atomic_fetch_add(&refused_other, 1); usleep(100); } return NULL; }
static int fail_which = -1; static int fail_init(int w){ return w == fail_which; }
int main(void){
    publish_queue *q = NULL;
    // init failures: each one clean (-1, no queue), then a normal open
    pq_test_fail_init = fail_init;
    for (fail_which = 0; fail_which <= 2; fail_which++){ CHECK(pq_open(&q, 4, publish, NULL) == -1 && q == NULL, "init failure %d must fail cleanly", fail_which); }
    fail_which = -1; pq_test_fail_init = NULL;
    CHECK(pq_open(&q, 3, publish, NULL) == 0 && q, "open");
    { publish_queue *z = NULL; CHECK(pq_open(&z, 0, publish, NULL) == -1 && z == NULL, "capacity 0 refused"); }
    // ownership: strings mutated and freed right after enqueue
    char *p1 = strdup("/scratch/a.partial"), *f1 = strdup("/dst/GATED-a.csv");
    close_gate();
    CHECK(pq_enqueue(q, p1, f1) == 0, "enqueue A");
    memset(p1, 'X', strlen(p1)); free(p1); memset(f1, 'X', strlen(f1)); free(f1);
    { pthread_mutex_lock(&gm); while (!atomic_load(&entered_gated)) pthread_cond_wait(&gc, &gm); pthread_mutex_unlock(&gm); }   /* A is in progress (observed, not assumed) */
    CHECK(pq_pending(q) == 1, "A in progress counts as pending");
    CHECK(pq_reserved(q, "/dst/GATED-a.csv"), "in-progress final is reserved");
    // B and C queue behind the gated A without blocking this thread
    CHECK(pq_enqueue(q, "/scratch/b.partial", "/dst/b.csv") == 0, "enqueue B");
    CHECK(pq_enqueue(q, "/scratch/c.partial", "/dst/c.csv") == 0, "enqueue C");
    CHECK(pq_reserved(q, "/dst/b.csv") && pq_reserved(q, "/dst/c.csv") && !pq_reserved(q, "/dst/z.csv"), "queued finals are reserved, others not");
    CHECK(pq_enqueue(q, "/scratch/d.partial", "/dst/d.csv") == 0, "enqueue D (queue now full: 3 queued + 1 in progress)");
    CHECK(pq_enqueue(q, "/scratch/e.partial", "/dst/e.csv") == -1 && errno == ENOSPC, "full queue refuses with ENOSPC");
    CHECK(atomic_load(&nlog) == 0, "nothing published while A is gated");
    // close while A is gated: close must drain B, C, D after the gate opens, and return only then
    pthread_t closer; pthread_create(&closer, NULL, closer_main, q);
    usleep(100000); CHECK(atomic_load(&nlog) == 0, "close must not skip or drop while A is gated");
    open_gate();
    pthread_join(closer, NULL);
    CHECK(atomic_load(&nlog) == 4, "close drained all four jobs (%d)", atomic_load(&nlog));
    CHECK(strcmp(log_[0], "/scratch/a.partial->/dst/GATED-a.csv") == 0, "A published with its own copied strings: %s", log_[0]);
    CHECK(strcmp(log_[1], "/scratch/b.partial->/dst/b.csv") == 0 && strcmp(log_[2], "/scratch/c.partial->/dst/c.csv") == 0 && strcmp(log_[3], "/scratch/d.partial->/dst/d.csv") == 0, "FIFO order kept");
    CHECK(pq_enqueue(q, "/s/late.partial", "/d/late.csv") == -1 && errno == ECANCELED, "enqueue after close is refused with ECANCELED (object still valid)");
    pq_destroy(q); pq_close(NULL); pq_destroy(NULL);
    // enqueue racing close: producers spam enqueue while close runs; every ACCEPTED job is published,
    // every refusal after close began is ECANCELED, nothing crashes (run under TSan too)
    atomic_store(&nlog, 0); atomic_store(&entered_gated, 0); open_gate();
    publish_queue *r = NULL; CHECK(pq_open(&r, 64, publish, NULL) == 0, "open (race)");
    pthread_t prod[4]; race_q = r;
    for (int i = 0; i < 4; i++) pthread_create(&prod[i], NULL, producer_main, NULL);
    usleep(20000); pq_close(r);
    int published_at_close = atomic_load(&nlog);
    for (int i = 0; i < 4; i++) pthread_join(prod[i], NULL);
    CHECK(atomic_load(&accepted) == published_at_close, "accepted %d != published-before-close-returned %d", atomic_load(&accepted), published_at_close);
    CHECK(atomic_load(&nlog) == published_at_close, "nothing published after close returned");
    CHECK(atomic_load(&refused_other) == 0, "refusals after close must all be ECANCELED (other errno seen %d times)", atomic_load(&refused_other));
    CHECK(atomic_load(&refused_cancel) > 0, "at least one enqueue landed after close began (%d)", atomic_load(&refused_cancel));
    pq_destroy(r);   /* only now: every producer has been joined */
    printf(fails ? "publish_queue tests: FAILURES %d\n" : "publish_queue tests: PASS\n", fails); return fails ? 1 : 0;
}
