/* Test-only progress deadline. All predicates and progress share this mutex.
 * A wakeup is not progress. Call note only for completed work/state transitions.
 * The independent process supervisor remains the total runtime bound. */
#ifndef BM_TEST_LIVENESS_H
#define BM_TEST_LIVENESS_H
#include "test_condition.h"
typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    double last;
    const char *setting;
} test_liveness;
#define TEST_LIVENESS_INIT(setting) {PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER, 0, setting}
static void test_live_note_locked(test_liveness *p){
    p->last=test_now();
    pthread_cond_broadcast(&p->cond);
}
static void test_live_note(test_liveness *p){
    pthread_mutex_lock(&p->mutex);
    test_live_note_locked(p);
    pthread_mutex_unlock(&p->mutex);
}
/* Called in a predicate loop, locked; begun is fixed at wait entry. Recompute
 * after every wake, including ETIMEDOUT, before declaring a stall. */
static void test_live_wait(test_liveness *p,double begun,const char *name){
    const char *s=getenv(p->setting); char *end=NULL;
    double seconds=s?strtod(s,&end):60;
    if(!isfinite(seconds)||seconds<0||(s&&(!*s||*end))){
        fprintf(stderr,"FAIL: invalid %s\n",p->setting); _exit(2);
    }
    double until=(p->last>begun?p->last:begun)+seconds;
    test_condition(&p->cond,&p->mutex,until,name);
}
#endif
