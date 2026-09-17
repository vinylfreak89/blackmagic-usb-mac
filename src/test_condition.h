/* Test-only condition deadline. Call in a predicate loop with the mutex held.
 * The deadline bounds a missing event; it never supplies the expected event. */
#ifndef BM_TEST_CONDITION_H
#define BM_TEST_CONDITION_H
#include <pthread.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <math.h>
static double test_now(void){
    struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec+t.tv_nsec/1e9;
}
static inline double test_until(const char *setting){
    const char *s=getenv(setting); char *end=NULL;
    double seconds=s?strtod(s,&end):60;
    if(!isfinite(seconds)||seconds<=0||(s&&(!*s||*end))){
        fprintf(stderr,"FAIL: invalid %s\n",setting); _exit(2);
    }
    return test_now()+seconds;
}
static void test_condition(pthread_cond_t *c,pthread_mutex_t *m,double until,const char *name){
    double left=until-test_now();
    if(left<=0){ fprintf(stderr,"FAIL: TIMEOUT: %s\n",name); _exit(2); }
    struct timespec t={(time_t)left,(long)((left-(time_t)left)*1e9)};
    int rc=pthread_cond_timedwait_relative_np(c,m,&t);
    if(rc&&rc!=ETIMEDOUT){ fprintf(stderr,"FAIL: %s: condition error %d\n",name,rc); _exit(2); }
}
#endif
