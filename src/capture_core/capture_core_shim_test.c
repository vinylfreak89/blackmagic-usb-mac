// capture_core DEVICE-path test: the real libusb backend linked against the replay shim
// (experiments/libusb_replay_shim.c) instead of libusb, so init, the fleet, resubmission,
// cancellation and teardown run exactly as on hardware — with faults hardware never produces.
//   capture_core_shim_test <slice.tpc>
// Cases:
//   1 teardown      — device-mode run to a bounded record count; every allocated transfer is
//                     freed by cc_stop (transfers_allocated == transfers_freed > 0)
//   2 retry deadline — permanent BUSY terminates loudly and frees the fleet
//   3 startup honesty — every init stage and initial submit/allocation fail synchronously
//   4 teardown containment — a missing cancel callback poisons/leaks instead of UAF
#include "capture_core.h"
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int fails=0;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)

typedef struct { uint64_t pkts; _Atomic int ended; int end_reason; } tally;
static void t_packet(void *ctx, const cc_packet *p){ tally *t=ctx; (void)p; t->pkts++; }
static void t_end(void *ctx, enum cc_end r){ tally *t=ctx; t->end_reason=r; atomic_store(&t->ended,1); }

static int run_device(cc_stats *st, tally *t, int wait_for_end, int deadline_ms){
    memset(t,0,sizeof *t);
    cc_config cfg={0}; cfg.input=CC_INPUT_SVIDEO; cfg.ring_mb=16; cfg.resubmit_deadline_ms=deadline_ms;
    cc_callbacks cb={0}; cb.on_packet=t_packet; cb.on_end=t_end; cb.ctx=t;
    cc_session *s=NULL;
    int rc=cc_open(&s,&cfg,&cb);
    if(rc!=CC_OK) return rc;
    rc=cc_start(s);
    if(rc!=CC_OK){ cc_get_stats(s,st); cc_close(s); return rc; }
    if(wait_for_end){ int guard=0; while(!atomic_load(&t->ended) && guard++<500) usleep(20000); }
    else usleep(200000);
    CHECK(cc_stop(s)==CC_OK,"stop");
    cc_get_stats(s,st);
    cc_close(s);
    return CC_OK;
}

int main(int argc, char **argv){
    if(argc<2){ fprintf(stderr,"usage: %s <slice.tpc>\n",argv[0]); return 9; }
    setenv("REPLAY_CAPTURE",argv[1],1);
    setenv("REPLAY_MAX_DATA","2000",1);
    cc_stats st; tally t;

    // 1: teardown frees the whole fleet
    CHECK(run_device(&st,&t,1,0)==CC_OK,"device open (teardown case)");
    CHECK(t.pkts>0,"device path delivered packets (%llu)",(unsigned long long)t.pkts);
    CHECK(st.transfers_allocated>0 && st.transfers_allocated==st.transfers_freed,
          "transfer leak: allocated %ld freed %ld",st.transfers_allocated,st.transfers_freed);

    // A second session in the same process must not inherit EOF/queues/static pacing.
    CHECK(run_device(&st,&t,1,0)==CC_OK,"second session after EOF");
    CHECK(t.pkts>0,"second session inherited stale shim EOF/queues");

    // 2: permanent resubmit BUSY is bounded and visible, never a hot infinite retry or shrink.
    char from[16]; snprintf(from,sizeof from,"%d",st.fleet_size+1);
    setenv("REPLAY_FAIL_SUBMIT_VIDEO_FROM",from,1); setenv("REPLAY_PACE_US","10000",1);
    CHECK(run_device(&st,&t,1,30)==CC_OK,"device open (pending case)");
    unsetenv("REPLAY_FAIL_SUBMIT_VIDEO_FROM"); unsetenv("REPLAY_PACE_US");
    CHECK(st.resubmit_failures>0,"pending case did not exercise submit failure");
    CHECK(t.end_reason==CC_END_TRANSFER_FAILED,"permanent resubmit ended as %d",t.end_reason);
    CHECK(st.transfers_allocated==st.transfers_freed,
          "pending transfers leaked: allocated %ld freed %ld (failures %ld)",
          st.transfers_allocated,st.transfers_freed,st.resubmit_failures);

    // 3: an initial submission failure is a synchronous failed start, never CC_OK with 15/16.
    setenv("REPLAY_FAIL_SUBMIT_VIDEO_AT","1",1);
    CHECK(run_device(&st,&t,1,0)==CC_ERR_USB,"initial-submit BUSY did not fail start");
    unsetenv("REPLAY_FAIL_SUBMIT_VIDEO_AT");
    CHECK(st.transfers_allocated==st.transfers_freed,"initial-submit case leaked: %ld vs %ld",st.transfers_allocated,st.transfers_freed);

    setenv("REPLAY_FAIL_SUBMIT_VIDEO_AT","1",1); setenv("REPLAY_FAIL_SUBMIT_CODE","-4",1);
    CHECK(run_device(&st,&t,1,0)==CC_ERR_NODEVICE,"initial NO_DEVICE did not fail as NODEVICE");
    unsetenv("REPLAY_FAIL_SUBMIT_VIDEO_AT"); unsetenv("REPLAY_FAIL_SUBMIT_CODE");

    setenv("REPLAY_FAIL_ALLOC_AT","1",1);
    CHECK(run_device(&st,&t,1,0)==CC_ERR_NOMEM,"transfer allocation failure did not fail start");
    unsetenv("REPLAY_FAIL_ALLOC_AT");

    for(int i=1;i<=2;i++){
        char n[8]; snprintf(n,sizeof n,"%d",i); setenv("REPLAY_FAIL_ALT_AT",n,1);
        CHECK(run_device(&st,&t,0,0)==CC_ERR_USB,"cc_open ignored alt-setting failure %d",i);
        unsetenv("REPLAY_FAIL_ALT_AT");
    }
    for(int i=1;i<=2;i++){
        char n[8]; snprintf(n,sizeof n,"%d",i); setenv("REPLAY_FAIL_CONTROL_AT",n,1);
        CHECK(run_device(&st,&t,0,0)==CC_ERR_USB,"cc_open ignored control failure %d",i);
        unsetenv("REPLAY_FAIL_CONTROL_AT"); setenv("REPLAY_SHORT_CONTROL_AT",n,1);
        CHECK(run_device(&st,&t,0,0)==CC_ERR_USB,"cc_open ignored short control %d",i);
        unsetenv("REPLAY_SHORT_CONTROL_AT");
    }

    // 4: an absent cancellation callback is a poisoned teardown and deliberate containment leak.
    setenv("REPLAY_WITHHOLD_CANCEL","1",1);
    CHECK(run_device(&st,&t,0,0)==CC_OK,"device open (withheld cancel)");
    unsetenv("REPLAY_WITHHOLD_CANCEL");
    CHECK(st.teardown_incomplete==1,"withheld cancel did not mark teardown incomplete");

    printf(fails? "FAILURES: %d\n" : "SHIM TESTS PASSED\n", fails);
    return fails?1:0;
}
