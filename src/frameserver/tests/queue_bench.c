/* Time the real analysis worker, including its bounded output copies/enqueues,
 * excluding the now-independent sinks. Scalar output only. */
#define FRAMESERVER_QUEUE_TEST_HOOKS
#include "../frameserver.c"
#include <assert.h>
#include <unistd.h>
enum { SAMPLES=4096 }; /* profiling capacity; not an engine signal constant */
static double all[SAMPLES],registered[SAMPLES];
static unsigned nall,nregistered;static uint64_t started,prior_calls;
static _Atomic int finished;
static uint64_t nanos(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000+t.tv_nsec;}
void fs_test_before_analysis_wait(frameserver *f){(void)f;}
void fs_test_after_analysis_wait(frameserver *f,int r){(void)f;(void)r;}
void fs_test_before_analysis_item(frameserver *f,const unit_video_observation *o){
    (void)o;prior_calls=f->st.registration_calls;started=nanos();
}
void fs_test_after_analysis_item(frameserver *f,const unit_video_observation *o){
    double ms=(nanos()-started)/1e6;
    if(o->fixed_raster_eligible){assert(nall<SAMPLES);all[nall++]=ms;}
    if(f->st.registration_calls!=prior_calls){assert(nregistered<SAMPLES);registered[nregistered++]=ms;}
}
static void ended(void *ctx,enum cc_end e){(void)ctx;assert(e==CC_END_REPLAY_EOF);atomic_store(&finished,1);}
static int cmp(const void *a,const void *b){double x=*(const double*)a,y=*(const double*)b;return(x>y)-(x<y);}
static void report(const char *name,double *a,unsigned n){
    assert(n);qsort(a,n,sizeof *a,cmp);
    printf("%s: n=%u median_ms=%.6f p95_ms=%.6f\n",name,n,n%2?a[n/2]:(a[n/2-1]+a[n/2])/2,a[(unsigned)(.95*(n-1))]);
}
int main(int argc,char **argv){
    assert(argc==3);alarm(180);
    fs_config c={0};c.capture.replay_path=argv[1];c.capture.replay_pace_us=16000;c.capture.ring_mb=512;
    c.pool_units=32;c.decision_log=argv[2];c.on_end=ended;
    frameserver *f=NULL;assert(!fs_open(&f,&c));assert(!fs_start(f));
    while(!atomic_load(&finished))usleep(1000);
    assert(!fs_stop(f));fs_stats s;fs_get_stats(f,&s);
    report("analysis_all_exact",all,nall);if(nregistered)report("analysis_registration",registered,nregistered);
    printf("exact=%llu published=%llu input_pool_drops=%llu input_ring_drops=%llu publisher_drops=%llu log_queue_drops=%llu log_errors=%llu input_high=%u output_high=%u log_high=%u\n",
        (unsigned long long)s.exact_units,(unsigned long long)s.published,(unsigned long long)s.dropped_pool_full,
        (unsigned long long)s.dropped_ring_full,(unsigned long long)s.publisher_dropped,(unsigned long long)s.log_queue_drops,
        (unsigned long long)s.log_last_file_errors,s.pool_high_water,s.publication_queue_high_water,s.log_queue_high_water);
    printf("output_slot_bytes=%zu log_slot_bytes=%zu output_capacity=%u log_capacity=%u\n",(size_t)FP_UNIT_BYTES+sizeof(fs_output_item),sizeof(fs_log_item),f->output_capacity,f->log_capacity);
    int bad=s.dropped_pool_full || s.dropped_ring_full || s.publisher_dropped || s.log_queue_drops || s.log_last_file_errors;
    fs_close(f);return bad?1:0;
}
