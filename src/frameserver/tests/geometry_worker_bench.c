/* Real replay worker, not a reimplementation of its processing path.
 * Measure thread CPU from classifier entry through process_item completion.
 * Queue waits/input I/O are excluded; optional sidecar formatting is included.
 * Timings are buffered until worker join, never written by the worker. */
#include "../frameserver.h"
#include "../../signal_state/signal_state.h"
#include "../../field_registration/geometry_engine.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

enum { BENCH_CAPACITY=100000 };
typedef struct {
    uint64_t counter,total,classifier,engine,publisher;
    unsigned searches;
} geometry_sample;
static geometry_sample samples[BENCH_CAPACITY],current;
static size_t sample_count;
static int sample_active,overflow;
static uint64_t sample_start;
extern unsigned geometry_bench_searches(const geometry_engine *);
static uint64_t cpu_ns(void) {
    struct timespec t;assert(!clock_gettime(CLOCK_THREAD_CPUTIME_ID,&t));
    return (uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;
}
static bool timed_classify(signal_state *s,const unit_video_observation *o,
                           const signal_context *ctx,signal_result *out) {
    current=(geometry_sample){0};sample_active=0;sample_start=cpu_ns();
    bool result=signal_state_classify(s,o,ctx,out);
    current.classifier=cpu_ns()-sample_start;return result;
}
static unsigned timed_push(geometry_engine *g,const uint8_t *y,uint64_t c,int reset,ge_decision out[2]) {
    uint64_t begin=cpu_ns();unsigned n=ge_push(g,y,c,reset,out);
    current.engine+=cpu_ns()-begin;current.counter=c;
    current.searches=geometry_bench_searches(g);sample_active=1;return n;
}
static int timed_publish(fp_publisher *p,const uint8_t *u,size_t n,uint64_t c,
                         int d1,int d2,uint32_t transport,int known,uint64_t pts) {
    uint64_t begin=cpu_ns();int rc=fp_publish_placed(p,u,n,c,d1,d2,transport,known,pts);
    current.publisher+=cpu_ns()-begin;return rc;
}
#define FRAMESERVER_TEST_HOOKS
#define signal_state_classify timed_classify
#define ge_push timed_push
#define fp_publish_placed timed_publish
#include "../frameserver.c"
#undef signal_state_classify
#undef ge_push
#undef fp_publish_placed

void fs_test_destroyed(void) {}
void fs_test_after_empty_snapshot(frameserver *f) {(void)f;}
void fs_test_before_producer_done(frameserver *f) {(void)f;}
void fs_test_after_log_row(frameserver *f,FILE *l) {(void)f;(void)l;}
void fs_test_pool_drop(void) {}
void fs_test_ring_drop(void) {}
void fs_test_audio_drop(void) {}
void fs_test_before_video(frameserver *f) {(void)f;}
void fs_test_after_item(frameserver *f) {
    (void)f;
    if(!sample_active)return;
    current.total=cpu_ns()-sample_start;
    if(sample_count<BENCH_CAPACITY)samples[sample_count++]=current;else overflow=1;
    sample_active=0;
}
#define main geometry_replay_main
#include "../frameserver_replay.c"
#undef main

static int ns_compare(const void *a,const void *b) {
    uint64_t x=*(const uint64_t*)a,y=*(const uint64_t*)b;return (x>y)-(x<y);
}
static void report_group(int searches) {
    uint64_t *v=malloc(sample_count*sizeof *v);assert(v);
    const char *names[]={"worker","classifier","engine","publisher","other"};
    for(unsigned stage=0;stage<5;stage++) {
        size_t n=0;
        for(size_t i=0;i<sample_count;i++) {
            geometry_sample *s=samples+i;
            if(searches>=0 && s->searches!=(unsigned)searches)continue;
            uint64_t times[]={s->total,s->classifier,s->engine,s->publisher,
                s->total-s->classifier-s->engine-s->publisher};
            assert(s->total>=s->classifier+s->engine+s->publisher);
            v[n++]=times[stage];
        }
        if(!n)continue;
        qsort(v,n,sizeof *v,ns_compare);
        printf("GE-WORKER-BENCH searches=%d stage=%s units=%zu median_ms=%.6f p95_ms=%.6f max_ms=%.6f\n",
            searches,names[stage],n,v[n/2]/1e6,v[n*95/100]/1e6,v[n-1]/1e6);
    }
    free(v);
}
int main(int argc,char **argv) {
    const char *path=getenv("GE_BENCH_TIMINGS");
    if(!path){fputs("GE_BENCH_TIMINGS is required\n",stderr);return 2;}
    FILE *f=fopen(path,"wx");if(!f){perror("GE_BENCH_TIMINGS");return 2;}
    int rc=geometry_replay_main(argc,argv);
    if(rc || overflow || !sample_count){fclose(f);return rc?rc:2;}
    fprintf(f,"counter,worker_ms,classifier_ms,engine_ms,publisher_ms,other_ms,rigid_fields\n");
    size_t searched=0;
    for(size_t i=0;i<sample_count;i++) {
        geometry_sample *s=samples+i;searched+=s->searches!=0;
        fprintf(f,"%llu,%.6f,%.6f,%.6f,%.6f,%.6f,%u\n",(unsigned long long)s->counter,
            s->total/1e6,s->classifier/1e6,s->engine/1e6,s->publisher/1e6,
            (s->total-s->classifier-s->engine-s->publisher)/1e6,s->searches);
    }
    int failed=ferror(f);if(fclose(f) || failed)return 2;
    printf("GE-WORKER-BENCH units=%zu rigid_units=%zu rigid_pct=%.6f\n",sample_count,searched,100.0*searched/sample_count);
    for(int n=-1;n<=2;n++)report_group(n);
    return 0;
}
