// capture_core test harness — hardware-free, replay-driven, adversarial.
//   capture_core_test <slice.tpc> <video_bytes> <video_pkts> <audio_bytes> <audio_pkts>
// Cases:
//   1 fidelity     — replay totals must equal the independently computed truth
//   2 honesty      — 1 MB ring + AFAP replay forces overflow; delivered+lost
//                    must balance to the byte and on_loss must have fired
//   3 truncation   — prefixes cut mid-header and mid-payload replay to a clean
//                    REPLAY_EOF with no crash and no over-delivery
//   4 lifecycle    — bad args and bad state transitions are refused
//   5 discipline   — on_end fires exactly once; callbacks never run on main
#include "capture_core.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int fails=0;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)

typedef struct {
    uint64_t bytes[2]; uint64_t pkts[2];
    uint64_t loss_bytes[2]; uint32_t loss_events;
    int end_count; int end_reason;
    pthread_t main_thread; int cb_on_main;
    int throttle;              // sleep every 256th packet: consumer provably slower
    _Atomic int ended;
} tally;

static void t_packet(void *ctx, const cc_packet *p){
    tally *t=ctx;
    int e = p->endpoint==CC_EP_AUDIO;
    t->bytes[e]+=p->actual_len; t->pkts[e]++;
    if(pthread_equal(pthread_self(),t->main_thread)) t->cb_on_main=1;
    // overflow tests must not race: cap consumer throughput well below the
    // producer's disk speed so a small ring is GUARANTEED to overflow
    if(t->throttle && ((t->pkts[0]+t->pkts[1]) & 255)==0) usleep(2000);
}
static void t_loss(void *ctx, uint8_t ep, uint32_t pk, uint64_t by){
    tally *t=ctx; (void)pk;
    t->loss_bytes[ep==CC_EP_AUDIO]+=by; t->loss_events++;
}
static void t_end(void *ctx, enum cc_end r){
    tally *t=ctx;
    t->end_count++; t->end_reason=r;
    atomic_store(&t->ended,1);
}
static void run_replay_opt(const char *path, int ring_mb, tally *t, int throttle){
    memset(t,0,sizeof *t);
    t->main_thread=pthread_self();
    t->throttle=throttle;
    cc_config cfg={0}; cfg.replay_path=path; cfg.ring_mb=ring_mb;
    cc_callbacks cb={0};
    cb.on_packet=t_packet; cb.on_loss=t_loss; cb.on_end=t_end; cb.ctx=t;
    cc_session *s=NULL;
    CHECK(cc_open(&s,&cfg,&cb)==CC_OK,"open %s",path);
    if(!s) return;
    CHECK(cc_start(s)==CC_OK,"start");
    while(!atomic_load(&t->ended)) usleep(20000);
    CHECK(cc_stop(s)==CC_OK,"stop");
    cc_close(s);
}
static void run_replay(const char *path, int ring_mb, tally *t){
    run_replay_opt(path,ring_mb,t,0);
}

int main(int argc, char **argv){
    if(argc<6){ fprintf(stderr,"usage: %s <slice.tpc> vB vP aB aP\n",argv[0]); return 9; }
    const char *slice=argv[1];
    uint64_t vB=strtoull(argv[2],0,10), vP=strtoull(argv[3],0,10);
    uint64_t aB=strtoull(argv[4],0,10), aP=strtoull(argv[5],0,10);
    tally t;

    // 1: fidelity
    run_replay(slice,0,&t);
    CHECK(t.bytes[0]==vB && t.pkts[0]==vP,"video fidelity: got %llu B/%llu pkts want %llu/%llu",
          (unsigned long long)t.bytes[0],(unsigned long long)t.pkts[0],
          (unsigned long long)vB,(unsigned long long)vP);
    CHECK(t.bytes[1]==aB && t.pkts[1]==aP,"audio fidelity");
    CHECK(t.loss_events==0,"unexpected loss in fidelity run");
    CHECK(t.end_reason==CC_END_REPLAY_EOF,"end reason %d",t.end_reason);
    CHECK(t.end_count==1,"on_end fired %d times",t.end_count);
    CHECK(!t.cb_on_main,"callbacks ran on the caller's thread");

    // 2: honesty under forced overflow (1 MB ring, throttled consumer)
    run_replay_opt(slice,1,&t,1);
    CHECK(t.loss_events>0,"1MB ring produced no overflow — test not exercising loss");
    CHECK(t.bytes[0]+t.loss_bytes[0]==vB,
          "video accounting UNBALANCED: %llu delivered + %llu lost != %llu",
          (unsigned long long)t.bytes[0],(unsigned long long)t.loss_bytes[0],
          (unsigned long long)vB);
    CHECK(t.bytes[1]+t.loss_bytes[1]==aB,"audio accounting unbalanced");
    CHECK(t.end_count==1,"on_end fired %d times (overflow run)",t.end_count);

    // 3: truncation robustness — cut mid-header and mid-payload
    long cuts[]={ 10, 24+5, 3000, 500000, 7777777 };
    FILE *in=fopen(slice,"rb");
    for(unsigned i=0;i<sizeof cuts/sizeof cuts[0];i++){
        char tmp[]="/tmp/cc_trunc_XXXXXX";
        int fd=mkstemp(tmp);
        FILE *o=fdopen(fd,"wb");
        fseek(in,0,SEEK_SET);
        for(long left=cuts[i]; left>0; ){
            char b[65536];
            size_t n=fread(b,1,left>(long)sizeof b?sizeof b:(size_t)left,in);
            if(!n) break;
            fwrite(b,1,n,o); left-=n;
        }
        fclose(o);
        run_replay(tmp,0,&t);
        CHECK(t.end_count==1 && t.end_reason==CC_END_REPLAY_EOF,
              "truncation @%ld: end_count=%d reason=%d",cuts[i],t.end_count,t.end_reason);
        CHECK(t.bytes[0]<=vB && t.bytes[1]<=aB,"truncation @%ld over-delivered",cuts[i]);
        unlink(tmp);
    }
    fclose(in);

    // 4: lifecycle / argument discipline
    cc_session *s=NULL;
    cc_config cfg={0}; cfg.replay_path=slice;
    cc_callbacks bad={0};
    CHECK(cc_open(&s,&cfg,&bad)==CC_ERR_ARGS,"open accepted NULL callbacks");
    CHECK(cc_open(NULL,&cfg,&bad)==CC_ERR_ARGS,"open accepted NULL out");
    cc_callbacks cb={0}; tally lt; memset(&lt,0,sizeof lt); lt.main_thread=pthread_self();
    cb.on_packet=t_packet; cb.on_end=t_end; cb.ctx=&lt;
    CHECK(cc_open(&s,&cfg,&cb)==CC_OK,"open (lifecycle)");
    CHECK(cc_stop(s)==CC_ERR_STATE,"stop before start accepted");
    CHECK(cc_start(s)==CC_OK,"start (lifecycle)");
    CHECK(cc_start(s)==CC_ERR_STATE,"double start accepted");
    while(!atomic_load(&lt.ended)) usleep(20000);
    CHECK(cc_stop(s)==CC_OK,"stop (lifecycle)");
    cc_close(s);
    CHECK(lt.end_count==1,"lifecycle on_end count %d",lt.end_count);

    printf(fails? "FAILURES: %d\n" : "ALL TESTS PASSED\n", fails);
    return fails?1:0;
}
