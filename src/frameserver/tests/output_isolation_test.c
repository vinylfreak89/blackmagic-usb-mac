/* Exercise real frameserver queues with deterministic classifier/registration
 * and publication boundary doubles; no picture-content thresholds involved. */
#include "../frameserver.h"
#include "../../signal_state/signal_state.h"
#include "../../field_registration/field_registration.h"
static bool classify_test(signal_state *,const unit_video_observation *,const signal_context *,signal_result *);
static bool register_test(field_registration *,const uint8_t *,fieldreg_decision *);
static int publish_test(fp_publisher *,const uint8_t *,size_t,uint64_t,int,int,uint8_t,int,uint64_t);
#define signal_state_classify classify_test
#define fieldreg_process register_test
#define fp_publish publish_test
#define FRAMESERVER_TEST_HOOKS
#define FRAMESERVER_QUEUE_TEST_HOOKS
#include "../frameserver.c"
#include <assert.h>
#include <unistd.h>
#include <signal.h>
static _Atomic unsigned analyzed, publications;
static _Atomic int blocked, released, done, gate_crop;
static unsigned classifications, decisions;
static int mode;
static uint64_t checksum(const uint8_t *p,size_t n){
    uint64_t h=14695981039346656037ull;for(size_t i=0;i<n;++i)h=(h^p[i])*1099511628211ull;return h;
}
static bool classify_test(signal_state *s,const unit_video_observation *u,const signal_context *c,signal_result *r){
    (void)s;(void)c;memset(r,0,sizeof *r);
    r->source=SIGNAL_SOURCE_PRESENT;r->appearance=SIGNAL_APPEARANCE_PROGRAM_LIKE;
    if(u->fixed_raster_eligible && u->bytes){
        ++classifications;r->normal_picture=mode!=2 || classifications<=2;
    }
    return true;
}
static bool register_test(field_registration *e,const uint8_t *u,fieldreg_decision *d){
    (void)e;(void)u;memset(d,0,sizeof *d);++decisions;
    d->applied_d1=mode==2?(int8_t)decisions:0;return true;
}
static int publish_test(fp_publisher *p,const uint8_t *u,size_t n,uint64_t ctr,int d1,int d2,uint8_t tr,int ak,uint64_t pts){
    (void)p;(void)u;(void)n;(void)ctr;(void)d2;(void)tr;(void)ak;(void)pts;
    unsigned k=atomic_fetch_add(&publications,1)+1;
    if(mode==0 && k==1){
        uint64_t before=checksum(u,n);
        atomic_store(&blocked,1);while(!atomic_load(&released))usleep(100);
        assert(checksum(u,n)==before); /* consumer's slab survives reuse of every input slot */
    }
    if(mode==2 && k==2)return 1;
    if(mode==2 && k==3)atomic_store(&gate_crop,d1);
    return 0;
}
void fs_test_after_empty_snapshot(frameserver *f){(void)f;}
void fs_test_before_analysis_wait(frameserver *f){(void)f;}
void fs_test_after_analysis_wait(frameserver *f,int r){(void)f;(void)r;}
void fs_test_before_analysis_item(frameserver *f,const unit_video_observation *o){(void)f;(void)o;}
void fs_test_before_producer_done(frameserver *f){(void)f;}
void fs_test_after_analysis_item(frameserver *f,const unit_video_observation *o){
    (void)f;if(o->fixed_raster_eligible)atomic_fetch_add(&analyzed,1);
}
void fs_test_after_log_row(frameserver *f,FILE *l){
    (void)f;(void)l;
    if((mode==1 || mode==3) && !atomic_exchange(&blocked,1))while(!atomic_load(&released))usleep(100);
}
static void ended(void *p,enum cc_end e){(void)p;(void)e;atomic_store(&done,1);}
int main(int argc,char **argv){
    assert(argc==3);alarm(180);mode=atoi(argv[2]);
    char path[]="/tmp/fs_output_isolation_XXXXXX";int fd=mkstemp(path);assert(fd>=0);close(fd);unlink(path);
    fs_config cfg={0};cfg.capture.replay_path=argv[1];cfg.capture.replay_pace_us=1000;
    cfg.pool_units=16;cfg.decision_log=path;cfg.on_end=ended;
    if(mode==3)cfg.log_queue_items=2; /* deliberately exhaust this boundary */
    frameserver *f=NULL;assert(!fs_open(&f,&cfg));assert(!fs_start(f));
    int pass=1;
    if(mode!=2){
        for(int i=0;i<5000 && !atomic_load(&blocked);++i)usleep(1000);
        assert(atomic_load(&blocked));
        /* TSan instruments the 90-MB CAP1/parser input too; this is a test
         * watchdog, not a pipeline polling interval or performance assertion. */
        for(int i=0;i<60000 && !atomic_load(&f->producer_done);++i)usleep(1000);
        unsigned target=(unsigned)atomic_load(&f->eligible_ingress);
        assert(atomic_load(&f->producer_done) && target>0);
        for(int i=0;i<5000 && atomic_load(&analyzed)<target;++i)usleep(1000);
        pass=atomic_load(&analyzed)==target;
        fprintf(stderr,"%s_does_not_block_analysis: %s (%u/%u analyzed while blocked)\n",
                mode==0?"publisher":"logger",pass?"PASS":"FAIL",atomic_load(&analyzed),target);
        atomic_store(&released,1);
    }
    while(!atomic_load(&done))usleep(1000);
    if(mode==3)assert(fs_log_stop(f)==-1);
    assert(!fs_stop(f));
    if(mode==2){pass=atomic_load(&gate_crop)==2;fprintf(stderr,"gate_holds_analysis_decision_after_delivery_failure: %s (crop %d, expected 2)\n",pass?"PASS":"FAIL",atomic_load(&gate_crop));}
    fs_stats st;fs_get_stats(f,&st);
    assert(st.published+st.publisher_dropped+st.dropped_pool_full==st.exact_units);
    if(mode==0){assert(st.publication_queue_drops>0 && st.dropped_pool_full==0 && st.dropped_ring_full==0);
        assert(st.published==f->output_capacity);
        fprintf(stderr,"output_slab_retained_and_overflow_counted: PASS (%llu published, %llu dropped)\n",(unsigned long long)st.published,(unsigned long long)st.publication_queue_drops);}
    if(mode==1)assert(st.log_queue_drops==0 && st.publisher_dropped==0 && st.log_last_file_errors==0);
    if(mode==3){assert(st.log_queue_drops>0 && st.publisher_dropped==0 && st.log_last_file_errors>0);
        fprintf(stderr,"log_queue_overflow_is_incomplete: PASS (%llu dropped records)\n",(unsigned long long)st.log_queue_drops);}
    fs_close(f);unlink(path);return pass?0:1;
}
