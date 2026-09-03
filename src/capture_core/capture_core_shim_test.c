// capture_core DEVICE-path test: the real libusb backend linked against the replay shim
// (experiments/libusb_replay_shim.c) instead of libusb, so init, the fleet, resubmission,
// cancellation and teardown run exactly as on hardware — with faults hardware never produces.
//   capture_core_shim_test <slice.tpc>
// Cases:
//   1 teardown      — device-mode run to a bounded record count; every allocated transfer is
//                     freed by cc_stop (transfers_allocated == transfers_freed > 0)
//   2 pending park  — every video RE-submit fails (the initial fleet submits succeed, then
//                     every later submit returns BUSY): the fleet parks in the pending state
//                     (never silently shrunk) and cc_stop must still free every transfer
//   2b initial fail — the first video submit at start fails: parked, confessed, recovered, freed
//   3 init honesty  — a failing control transfer (mode word / latch) makes cc_open FAIL with
//                     CC_ERR_USB instead of returning a clean capture of the wrong input
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

static int run_device(cc_stats *st, tally *t, int wait_for_end){
    memset(t,0,sizeof *t);
    cc_config cfg={0}; cfg.input=CC_INPUT_SVIDEO; cfg.ring_mb=16;      // no replay_path => device backend
    cc_callbacks cb={0}; cb.on_packet=t_packet; cb.on_end=t_end; cb.ctx=t;
    cc_session *s=NULL;
    int rc=cc_open(&s,&cfg,&cb);
    if(rc!=CC_OK) return rc;
    CHECK(cc_start(s)==CC_OK,"start");
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
    CHECK(run_device(&st,&t,1)==CC_OK,"device open (teardown case)");
    CHECK(t.pkts>0,"device path delivered packets (%llu)",(unsigned long long)t.pkts);
    CHECK(st.transfers_allocated>0 && st.transfers_allocated==st.transfers_freed,
          "transfer leak: allocated %ld freed %ld",st.transfers_allocated,st.transfers_freed);

    // 2: every video submit after the initial fleet fails -> transfers park pending; stop must
    //    free them. (Initial-submit failures take a different path: freed at start.)
    char from[16]; snprintf(from,sizeof from,"%d",st.fleet_size+1);
    setenv("REPLAY_FAIL_SUBMIT_VIDEO_FROM",from,1);
    CHECK(run_device(&st,&t,0)==CC_OK,"device open (pending case)");
    unsetenv("REPLAY_FAIL_SUBMIT_VIDEO_FROM");
    CHECK(st.resubmit_failures>0,"pending case did not exercise submit failure");
    CHECK(st.transfers_allocated==st.transfers_freed,
          "pending transfers leaked: allocated %ld freed %ld (failures %ld)",
          st.transfers_allocated,st.transfers_freed,st.resubmit_failures);

    // 2b: the FIRST video submit fails at start: the fleet must not silently shrink -- the
    //     transfer parks, is retried from the event loop, recovers, and is freed at stop
    setenv("REPLAY_FAIL_SUBMIT_VIDEO_AT","1",1);
    CHECK(run_device(&st,&t,1)==CC_OK,"device open (initial-submit case)");
    unsetenv("REPLAY_FAIL_SUBMIT_VIDEO_AT");
    CHECK(st.resubmit_failures>=1 && st.resubmit_recovered>=1,
          "initial submit failure not confessed+recovered (failures %ld recovered %ld)",st.resubmit_failures,st.resubmit_recovered);
    CHECK(st.fleet[0]==st.fleet_size,"fleet silently shrank at start: %d of %d video transfers live",st.fleet[0],st.fleet_size);
    CHECK(st.transfers_allocated==st.transfers_freed,"initial-submit case leaked: %ld vs %ld",st.transfers_allocated,st.transfers_freed);

    // 3: control transfer failure must fail open, never a clean capture of the wrong input
    setenv("REPLAY_FAIL_CONTROL","1",1);
    CHECK(run_device(&st,&t,0)==CC_ERR_USB,"cc_open ignored a failed mode-word/latch control transfer");
    unsetenv("REPLAY_FAIL_CONTROL");

    printf(fails? "FAILURES: %d\n" : "SHIM TESTS PASSED\n", fails);
    return fails?1:0;
}
