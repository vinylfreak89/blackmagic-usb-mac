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
//   7 unread USB slots — the shim schedules like libusb's Darwin backend (REPLAY_REALTIME) and records every gap it
//                     creates; for a clean run and stalls of 300-1000 ms the reported packets must match the truth
//                     (within one frame), and every report must come immediately before its transfer's first packet
//   5 start-up sequence — the exact alt-setting and control-transfer sequence cc_open sends, for setup on and off,
//                     and the mode word cc_start_info reports (written out here from the vendor driver's commit, not
//                     taken from the code under test)
#include "capture_core.h"
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include "../test_supervisor.h"

static int fails=0;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)

typedef struct { uint64_t pkts; _Atomic int ended; int end_reason; } tally;
static void t_packet(void *ctx, const cc_packet *p){ tally *t=ctx; (void)p; t->pkts++; }
static void t_end(void *ctx, enum cc_end r){ tally *t=ctx; t->end_reason=r; atomic_store(&t->ended,1); }
static void wait_device_end(tally *t, double seconds){
    double until=test_clock()+seconds;
    while (!atomic_load(&t->ended)) {
        if (test_clock() >= until) {
            fprintf(stderr,"FAIL: TIMEOUT: shim run_device on_end (%.3g s); exiting before cc_stop\n",seconds);
            _exit(2);
        }
        usleep(20000);
    }
}

const char *replay_shim_trace(void);   // libusb_replay_shim.c: this session's alt-setting and control-transfer calls

// cc_open alone (no streaming): the start-up trace and the reported mode word
static int open_trace_in(int input, int setup_off, char *trace, size_t n, uint32_t *mode, int *info_rc){
    tally t={0}; cc_config cfg={0}; cfg.input=input; cfg.ring_mb=16; cfg.setup_off=setup_off;
    cc_callbacks cb={0}; cb.on_packet=t_packet; cb.on_end=t_end; cb.ctx=&t;
    cc_session *s=NULL; int rc=cc_open(&s,&cfg,&cb);
    snprintf(trace,n,"%s",replay_shim_trace());
    *mode=0; *info_rc=rc==CC_OK?cc_start_info(s,mode):-99;
    if(rc==CC_OK) cc_close(s);
    return rc;
}
static int open_trace(int setup_off, char *trace, size_t n, uint32_t *mode, int *info_rc){
    return open_trace_in(CC_INPUT_SVIDEO,setup_off,trace,n,mode,info_rc);
}

void replay_shim_gaps(int ep_index, long long *frames, long *events, long *first_transfer);
/* placement check: an unread-slot report must be followed, on its endpoint, by packet 0 of the transfer it names */
static struct { int n, misplaced, late; int pending[2]; uint32_t seq[2]; } lt;
static void lt_packet(void *ctx, const cc_packet *p){
    t_packet(ctx,p); int e=p->endpoint==CC_EP_AUDIO;
    if(lt.pending[e]){ if(p->submit_seq!=lt.seq[e] || p->pkt_index!=0) lt.misplaced++; lt.pending[e]=0; }
}
static void lt_loss_ex(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){
    (void)ctx; (void)pk; (void)by;
    if(kind==CC_LOSS_UNSCHEDULED_LATE){ lt.late++; return; }   /* located by seq, not position */
    if(kind!=CC_LOSS_UNSCHEDULED) return;
    int e=ep==CC_EP_AUDIO; if(lt.pending[e]) lt.misplaced++;
    lt.pending[e]=1; lt.seq[e]=seq; lt.n++;
}
static int run_device_lt(cc_stats *st, tally *t){
    memset(t,0,sizeof *t);
    cc_config cfg={0}; cfg.input=CC_INPUT_SVIDEO; cfg.ring_mb=16;
    cc_callbacks cb={0}; cb.on_packet=lt_packet; cb.on_end=t_end; cb.ctx=t; cb.on_loss_ex=lt_loss_ex;
    cc_session *s=NULL; int rc=cc_open(&s,&cfg,&cb); if(rc!=CC_OK) return rc;
    rc=cc_start(s); if(rc!=CC_OK){ cc_get_stats(s,st); cc_close(s); return rc; }
    wait_device_end(t,20);
    CHECK(cc_stop(s)==CC_OK,"stop"); cc_get_stats(s,st); cc_close(s); return CC_OK;
}
static int run_device(cc_stats *st, tally *t, int wait_for_end, int deadline_ms){
    memset(t,0,sizeof *t);
    cc_config cfg={0}; cfg.input=CC_INPUT_SVIDEO; cfg.ring_mb=16; cfg.resubmit_deadline_ms=deadline_ms;
    cc_callbacks cb={0}; cb.on_packet=t_packet; cb.on_end=t_end; cb.ctx=t;
    cc_session *s=NULL;
    int rc=cc_open(&s,&cfg,&cb);
    if(rc!=CC_OK) return rc;
    rc=cc_start(s);
    if(rc!=CC_OK){ cc_get_stats(s,st); cc_close(s); return rc; }
    if(wait_for_end) wait_device_end(t,10);
    else usleep(200000);
    CHECK(cc_stop(s)==CC_OK,"stop");
    cc_get_stats(s,st);
    cc_close(s);
    return CC_OK;
}

int main(int argc, char **argv){
    test_supervise(argv, "SHIM_TEST_TOTAL_S", "capture_core_shim_test");
    if (argc == 3 && !strcmp(argv[1], "--deadline-probe")) {
        if (!strcmp(argv[2], "total")) { alarm(0); for (;;) pause(); }
        tally t={0}; wait_device_end(&t,0);
        fprintf(stderr,"FAIL: continued after shim timeout\n"); return 99;
    }
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

    for(int i=1;i<=3;i++){                 // alt0, alt1, alt2
        char n[8]; snprintf(n,sizeof n,"%d",i); setenv("REPLAY_FAIL_ALT_AT",n,1);
        CHECK(run_device(&st,&t,0,0)==CC_ERR_USB,"cc_open ignored alt-setting failure %d",i);
        unsetenv("REPLAY_FAIL_ALT_AT");
    }
    for(int i=1;i<=8;i++){                 // six writes before the reset, the mode word and the latch after it
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

    // 5: the start-up sequence, exactly, for both settings of the 7.5 IRE setup bit
    {
        static const char *want[2]={
            "alt0 W215/0:3c000000 W215/0:3c000000 W215/4:80808000 W215/4:80808000 W215/24:73c60001 W215/24:73c60001 "
            "alt1 alt2 W215/0:3c000000 W215/24:73c60001",
            "alt0 W215/0:34000000 W215/0:34000000 W215/4:80808000 W215/4:80808000 W215/24:73c60001 W215/24:73c60001 "
            "alt1 alt2 W215/0:34000000 W215/24:73c60001" };
        static const uint32_t want_mode[2]={0x3c000000u,0x34000000u};
        for(int off=0;off<=1;off++){
            char tr[4096]; uint32_t mode; int irc;
            CHECK(open_trace(off,tr,sizeof tr,&mode,&irc)==CC_OK,"setup %s: cc_open",off?"off":"on");
            CHECK(!strcmp(tr,want[off]),"setup %s: start-up sequence\n  got  %s\n  want %s",off?"off":"on",tr,want[off]);
            CHECK(irc==0 && mode==want_mode[off],"setup %s: cc_start_info rc %d mode 0x%08x, want 0x%08x",off?"off":"on",irc,mode,want_mode[off]);
        }
    }

    // 6: the input select reaches the mode word, before and after the reset, as the vendor driver selects inputs:
    //    composite bit 1 (0x02), component none (0x00); S-video bit 2 (0x04) above; never the HDMI bit 0
    {
        static const struct { int in; const char *name; const char *w; uint32_t mode; } cases[]={
            {CC_INPUT_COMPOSITE,"composite","3a000000",0x3a000000u},{CC_INPUT_COMPONENT,"component","38000000",0x38000000u}};
        for(int i=0;i<2;i++){
            char tr[4096], want[512]; uint32_t mode; int irc;
            snprintf(want,sizeof want,"alt0 W215/0:%s W215/0:%s W215/4:80808000 W215/4:80808000 W215/24:73c60001 W215/24:73c60001 "
                     "alt1 alt2 W215/0:%s W215/24:73c60001",cases[i].w,cases[i].w,cases[i].w);
            CHECK(open_trace_in(cases[i].in,0,tr,sizeof tr,&mode,&irc)==CC_OK,"%s: cc_open",cases[i].name);
            CHECK(!strcmp(tr,want),"%s: start-up sequence\n  got  %s\n  want %s",cases[i].name,tr,want);
            CHECK(irc==0 && mode==cases[i].mode,"%s: mode 0x%08x, want 0x%08x",cases[i].name,mode,cases[i].mode);
        }
    }

    // 7: unread USB slots, against the shim's ground truth (REPLAY_REALTIME = libusb's Darwin scheduling rule)
    if(argc>=3){
        setenv("REPLAY_CAPTURE",argv[2],1); unsetenv("REPLAY_MAX_DATA"); setenv("REPLAY_REALTIME","1",1);
        static const struct { int ms, at; } sc[]={{0,0},{300,100},{450,97},{450,100},{450,105},{500,100},{600,100},{800,100},{1000,103}};
        for(unsigned i=0;i<sizeof sc/sizeof sc[0];i++){
            char ms[16], at[16]; snprintf(ms,sizeof ms,"%d",sc[i].ms); snprintf(at,sizeof at,"%d",sc[i].at);
            if(sc[i].ms){ setenv("REPLAY_STALL_MS",ms,1); setenv("REPLAY_STALL_VIDEO_AT",at,1); }
            else { unsetenv("REPLAY_STALL_MS"); unsetenv("REPLAY_STALL_VIDEO_AT"); }
            lt.n=0; lt.misplaced=0; lt.pending[0]=lt.pending[1]=0;
            CHECK(run_device_lt(&st,&t)==CC_OK,"stall %d@%d: open",sc[i].ms,sc[i].at);
            for(int e=0;e<2;e++){
                long long tf; long tev, tfirst; replay_shim_gaps(e,&tf,&tev,&tfirst);
                long long got=(long long)st.unscheduled_packets[e], want=tf*8;
                CHECK(got>=want-8 && got<=want+8,"stall %d@%d %s: reported %lld unread packets, truth %lld",
                      sc[i].ms,sc[i].at,e?"audio":"video",got,want);
                CHECK((tev>0)==(got>0),"stall %d@%d %s: truth %ld gap events, reported %lld packets",sc[i].ms,sc[i].at,e?"audio":"video",tev,got);
            }
            CHECK(lt.misplaced==0,"stall %d@%d: %d unread-slot reports not immediately before their transfer's first packet",
                  sc[i].ms,sc[i].at,lt.misplaced);
            long long vf,af; long ve,ae,vk,ak; replay_shim_gaps(0,&vf,&ve,&vk); replay_shim_gaps(1,&af,&ae,&ak);
            printf("  stall %4d ms @%3d: truth video %lld / audio %lld packets; reported %llu / %llu in %llu events; misplaced %d\n",
                   sc[i].ms,sc[i].at,vf*8,af*8,(unsigned long long)st.unscheduled_packets[0],(unsigned long long)st.unscheduled_packets[1],
                   (unsigned long long)st.unscheduled_events,lt.misplaced);
        }
        unsetenv("REPLAY_STALL_MS"); unsetenv("REPLAY_STALL_VIDEO_AT");
        // 7b: bus-to-callback delay the model cannot see: under-reporting by at most the delay, never over, never misplaced
        static const struct { int lat_us, ms; } lc[]={{1500,520},{1500,600},{3000,520},{3000,600},{3000,800}};
        for(unsigned i=0;i<sizeof lc/sizeof lc[0];i++){
            char lat[16], ms[16]; snprintf(lat,sizeof lat,"%d",lc[i].lat_us); snprintf(ms,sizeof ms,"%d",lc[i].ms);
            setenv("REPLAY_LAT_US",lat,1); setenv("REPLAY_STALL_MS",ms,1); setenv("REPLAY_STALL_VIDEO_AT","100",1);
            lt.n=0; lt.misplaced=0; lt.pending[0]=lt.pending[1]=0;
            CHECK(run_device_lt(&st,&t)==CC_OK,"latency %d us stall %d: open",lc[i].lat_us,lc[i].ms);
            long long slack=((lc[i].lat_us+999)/1000+1)*8;
            for(int e=0;e<2;e++){
                long long tf; long tev, tk; replay_shim_gaps(e,&tf,&tev,&tk); long long got=(long long)st.unscheduled_packets[e], want=tf*8;
                CHECK(got<=want+8 && got>=want-slack,"latency %d us stall %d %s: reported %lld, truth %lld (allowed down to %lld)",
                      lc[i].lat_us,lc[i].ms,e?"audio":"video",got,want,want-slack);
            }
            CHECK(lt.misplaced==0,"latency %d us stall %d: %d misplaced reports",lc[i].lat_us,lc[i].ms,lt.misplaced);
            long long vf,af; long ve,ae,vk,ak; replay_shim_gaps(0,&vf,&ve,&vk); replay_shim_gaps(1,&af,&ae,&ak);
            printf("  latency %4d us, stall %d ms: truth %lld / %lld; reported %llu / %llu; backstop shifts %llu; misplaced %d\n",
                   lc[i].lat_us,lc[i].ms,vf*8,af*8,(unsigned long long)st.unscheduled_packets[0],(unsigned long long)st.unscheduled_packets[1],
                   (unsigned long long)st.schedule_shifts,lt.misplaced);
        }
        unsetenv("REPLAY_LAT_US"); unsetenv("REPLAY_STALL_MS"); unsetenv("REPLAY_STALL_VIDEO_AT");
        // 7c: a failed submit: no loss if libusb did not advance its queue end; one phantom transfer if it did
        for(int adv=0;adv<2;adv++){
            setenv("REPLAY_FAIL_SUBMIT_VIDEO_AT","100",1); if(adv) setenv("REPLAY_FAIL_ADVANCES","1",1); else unsetenv("REPLAY_FAIL_ADVANCES");
            lt.n=0; lt.late=0; lt.misplaced=0; lt.pending[0]=lt.pending[1]=0;
            CHECK(run_device_lt(&st,&t)==CC_OK,"failed submit (advances %d): open",adv);
            long long tf; long tev, tk; replay_shim_gaps(0,&tf,&tev,&tk);
            long long got=(long long)st.unscheduled_packets[0], want=tf*8;
            CHECK(got>=want-8 && got<=want+8,"failed submit (advances %d): reported %lld video packets, truth %lld",adv,got,want);
            CHECK(lt.n==0 && lt.late==adv && (int)st.unscheduled_late==adv && !st.schedule_shifts,"failed submit (advances %d): %d on-time records, %d late (want %d), %llu shifts",
                  adv,lt.n,lt.late,adv,(unsigned long long)st.schedule_shifts);
            CHECK(lt.misplaced==0,"failed submit (advances %d): %d misplaced",adv,lt.misplaced);
            printf("  failed submit, libusb %s its queue end: truth %lld, reported %lld (late records %d), misplaced %d\n",adv?"advances":"does not advance",want,got,lt.late,lt.misplaced);
        }
        // 7d: a failed submit with the event thread held around the transfer that settles it. The held callback is
        // late without any phantom transfer; it must not be read as one (review D6: 2,160-2,416 packets reported, truth 0
        // or 128). A phantom is still found, placed at once or, when the hold leaves it in doubt, as a counted shift.
        struct { int ms, at, aphase; } hc[]={{300,99,0},{300,100,0},{300,101,0},{20,100,0},{450,100,0},
            {10,100,15},{10,99,15},{12,100,14},{14,100,15},{10,100,7}};   /* review: audio 15 ms off video, a 10 ms hold placed 80 */
        for(size_t i=0;i<sizeof hc/sizeof hc[0];i++) for(int adv=0;adv<2;adv++){
            char ms[16],at[16]; snprintf(ms,sizeof ms,"%d",hc[i].ms); snprintf(at,sizeof at,"%d",hc[i].at);
            setenv("REPLAY_FAIL_SUBMIT_VIDEO_AT","100",1); if(adv) setenv("REPLAY_FAIL_ADVANCES","1",1); else unsetenv("REPLAY_FAIL_ADVANCES");
            setenv("REPLAY_STALL_MS",ms,1); setenv("REPLAY_STALL_VIDEO_AT",at,1);
            { char ph[8]; snprintf(ph,sizeof ph,"%d",hc[i].aphase); setenv("REPLAY_APHASE_MS",ph,1); }
            lt.n=0; lt.late=0; lt.misplaced=0; lt.pending[0]=lt.pending[1]=0;
            CHECK(run_device_lt(&st,&t)==CC_OK,"failed submit + hold %d@%d (advances %d): open",hc[i].ms,hc[i].at,adv);
            long long tf; long tev, tk; replay_shim_gaps(0,&tf,&tev,&tk);
            long long placed=(long long)st.unscheduled_packets[0], shifted=(long long)st.schedule_shift_frames*8, want=tf*8;
            CHECK(placed>=want-8 && placed<=want+8 && !shifted,"failed submit + hold %d@%d (advances %d): reported %lld + %lld shifted, truth %lld",
                  hc[i].ms,hc[i].at,adv,placed,shifted,want);
            CHECK(lt.n==0 && lt.late==adv,"failed submit + hold %d@%d (advances %d): %d records at the data, %d late (want %d)",hc[i].ms,hc[i].at,adv,lt.n,lt.late,adv);
            CHECK(lt.misplaced==0,"failed submit + hold %d@%d (advances %d): %d misplaced",hc[i].ms,hc[i].at,adv,lt.misplaced);
            printf("  failed submit + hold %3d ms @%d, audio phase %2d ms, libusb %s: truth %lld; reported %lld (late records %d), shifts %lld; misplaced %d\n",
                   hc[i].ms,hc[i].at,hc[i].aphase,adv?"advances":"does not advance",want,placed,lt.late,shifted,lt.misplaced);
        }
        unsetenv("REPLAY_STALL_MS"); unsetenv("REPLAY_STALL_VIDEO_AT"); unsetenv("REPLAY_APHASE_MS");
        unsetenv("REPLAY_FAIL_SUBMIT_VIDEO_AT"); unsetenv("REPLAY_FAIL_ADVANCES");
        // 7e: the model's packets-per-frame comes from bInterval 1: read from the device, it stays on at 1 and turns
        // off (nothing reported) at any other interval, here with a stall that leaves unread slots
        for(int iv=1;iv<=4;iv+=3){
            char b[4]; snprintf(b,sizeof b,"%d",iv); setenv("REPLAY_BINTERVAL",b,1);
            setenv("REPLAY_STALL_MS","800",1); setenv("REPLAY_STALL_VIDEO_AT","100",1);
            lt.n=0; lt.misplaced=0; lt.pending[0]=lt.pending[1]=0;
            CHECK(run_device_lt(&st,&t)==CC_OK,"bInterval %d: open",iv);
            long long tf; long tev, tk; replay_shim_gaps(0,&tf,&tev,&tk);
            if(iv==1) CHECK((long long)st.unscheduled_packets[0]==tf*8 && tf>0,"bInterval 1: reported %llu, truth %lld",(unsigned long long)st.unscheduled_packets[0],tf*8);
            else CHECK(st.unscheduled_events==0 && st.schedule_shifts==0,"bInterval %d: model still reporting (%llu events)",iv,(unsigned long long)st.unscheduled_events);
            printf("  bInterval %d read from the device: unread-slot model %s (reported %llu, truth %lld)\n",iv,iv==1?"on":"off",(unsigned long long)st.unscheduled_packets[0],tf*8);
        }
        unsetenv("REPLAY_BINTERVAL"); unsetenv("REPLAY_STALL_MS"); unsetenv("REPLAY_STALL_VIDEO_AT"); unsetenv("REPLAY_REALTIME");
    } else { fails++; fprintf(stderr,"FAIL: no realtime fixture given (case 7 not run)\n"); }

    printf(fails? "FAILURES: %d\n" : "SHIM TESTS PASSED\n", fails);
    return fails?1:0;
}
