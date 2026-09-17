// capture_core test harness — hardware-free, replay-driven, adversarial.
//   capture_core_test <slice.tpc> <video_bytes> <video_pkts> <audio_bytes> <audio_pkts>
// Cases:
//   1 fidelity     — replay totals must equal the independently computed truth
//   2 honesty      — 1 MB ring + condition-held consumer forces overflow; delivered+lost
//                    must balance to the byte and on_loss must have fired
//   3 truncation   — prefixes cut mid-header and mid-payload replay to a clean
//                    REPLAY_EOF with no crash and no over-delivery
//   4 lifecycle    — bad args and bad state transitions are refused
//   5 discipline   — on_end fires exactly once; callbacks never run on main
//   6 control loss — metadata exhaustion marks-and-continues by default and
//                    terminates only under the explicit fail-stop policy
#include "capture_core.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <signal.h>
#include "../test_supervisor.h"
#include "../test_liveness.h"

static int fails=0;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
extern void cc_test_reuse_worker_ids(cc_session *s);
static _Atomic int destroyed;
void cc_test_destroyed(void){ atomic_fetch_add(&destroyed,1); }
static cc_session *callback_target;
static _Atomic int callback_probe, callback_stop_rc, end_probe, end_stop_rc;

typedef struct {
    uint64_t bytes[2]; uint64_t pkts[2];
    uint64_t loss_bytes[2]; uint32_t loss_events; uint32_t error_events;
    uint32_t control_loss_markers;
    int end_count; int end_reason;
    pthread_t main_thread; int cb_on_main;
    int throttle;              // 1=two loss/resume rounds, 2=loss+error, 3=metadata exhaustion
    _Atomic int ended;
} tally;

static _Atomic int hook_arm, hook_empty, hook_release, hook_fail_alloc;
static _Atomic int alloc_hold, alloc_entered, alloc_release, alloc_on_starter;
static pthread_t starter_thread;
/* Every wait here has a stall deadline: CC_TEST_WAIT_S seconds without progress, default 60. On expiry the test fails loudly,
 * names the wait and exits at once (exit 2), rather than hanging or passing silently. */
enum { PRESSURE_LOSS=1, PRESSURE_ERROR=2, PRESSURE_META=4 };
static test_liveness live=TEST_LIVENESS_INIT("CC_TEST_WAIT_S");
static int pressure_mode, pressure_events, pressure_round, loss_round, pressure_ready, input_done, resumed;
/* Caller holds live.mutex. Time only limits liveness, never establishes loss. */
static void pressure_wait(int *value,int target,const char *what){
    double begun=test_now();
    while(*value<target){
        if(input_done){
            fprintf(stderr,"FAIL: pressure hold (%s): producer ended before required event\n",what);
            _exit(2);
        }
        test_live_wait(&live,begun,what);
    }
}
static void pressure_event(int event){
    if(!pressure_mode) return;
    pthread_mutex_lock(&live.mutex);
    pressure_events|=event;
    if(event==PRESSURE_LOSS && (pressure_round==1 || resumed)) loss_round=pressure_round;
    int required=PRESSURE_LOSS|(pressure_mode==2?PRESSURE_ERROR:PRESSURE_META);
    pressure_ready=(pressure_events&required)==required;
    test_live_note_locked(&live);
    pthread_mutex_unlock(&live.mutex);
}
void cc_test_data_resumed(void){
    if(pressure_mode!=1) return;
    pthread_mutex_lock(&live.mutex);
    if(!resumed){
        resumed=1;
        test_live_note_locked(&live);
        /* A pending loss has been flushed AND a DATA record accepted. Wait
         * until the consumer holds again before filling the ring a second time. */
        pressure_wait(&pressure_round,2,"post-resume consumer hold");
    }
    pthread_mutex_unlock(&live.mutex);
}
void cc_test_ring_loss(void){ pressure_event(PRESSURE_LOSS); }
void cc_test_recorded_error(void){ pressure_event(PRESSURE_ERROR); }
void cc_test_meta_exhausted(void){ pressure_event(PRESSURE_META); }
void cc_test_packet_progress(void){ test_live_note(&live); }
void cc_test_input_done(void){
    pthread_mutex_lock(&live.mutex); input_done=1; test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex);
}
static void wait_ended(_Atomic int *ended, const char *what){
    char name[128]; snprintf(name,sizeof name,"waiting for on_end (%s)",what);
    double begun=test_now(); pthread_mutex_lock(&live.mutex);
    while(!atomic_load(ended)) test_live_wait(&live,begun,name);
    pthread_mutex_unlock(&live.mutex);
}
void cc_test_after_empty_snapshot(cc_session *s){
    (void)s;
    pthread_mutex_lock(&live.mutex);
    if(atomic_load(&hook_arm) && !atomic_exchange(&hook_empty,1)){
        double begun=test_now();
        while(!atomic_load(&hook_release))
            test_live_wait(&live,begun,"cc_test_after_empty_snapshot: cc_test_before_backend_done never released the backend");
    }
    pthread_mutex_unlock(&live.mutex);
}
void cc_test_before_backend_done(cc_session *s){
    (void)s; pthread_mutex_lock(&live.mutex);
    if(atomic_load(&hook_arm)) atomic_store(&hook_release,1);
    test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex);
}
int cc_test_fail_delivery_allocation(size_t bytes){
    (void)bytes;
    if(atomic_load(&alloc_hold)) {
        double begun=test_now(); pthread_mutex_lock(&live.mutex);
        atomic_store(&alloc_on_starter,pthread_equal(pthread_self(),starter_thread));
        atomic_store(&alloc_entered,1);
        test_live_note_locked(&live);
        while(!atomic_load(&alloc_release)) test_live_wait(&live,begun,"allocation release");
        pthread_mutex_unlock(&live.mutex);
    }
    return atomic_exchange(&hook_fail_alloc,0);
}

static void t_packet(void *ctx, const cc_packet *p){
    test_live_note(&live);
    tally *t=ctx;
    if(atomic_exchange(&callback_probe,0)){
        callback_stop_rc=cc_stop(callback_target);
        cc_close(callback_target); /* must refuse; normal owner still closes it */
    }
    int e = p->endpoint==CC_EP_AUDIO;
    t->bytes[e]+=p->actual_len; t->pkts[e]++;
    if(pthread_equal(pthread_self(),t->main_thread)) t->cb_on_main=1;
    uint64_t total=t->pkts[0]+t->pkts[1];
    if(t->throttle==1 || (t->throttle>=2 && total==1)){
        pthread_mutex_lock(&live.mutex);
        if(t->throttle==1){
            if(total==1) pressure_wait(&loss_round,1,"first ring loss");
            else if(t->loss_events && pressure_round==1){
                /* This callback follows the first HostLoss record, so the
                 * producer can publish resumed DATA without more draining.
                 * Wait even if its post-publication hook has not run yet. */
                pressure_wait(&resumed,1,"accepted DATA after first loss");
                pressure_round=2; test_live_note_locked(&live);
                pressure_wait(&loss_round,2,"post-resume ring loss");
            }
        }else pressure_wait(&pressure_ready,1,t->throttle==2?"ring loss and recorded TransferError":"metadata exhaustion");
        pthread_mutex_unlock(&live.mutex);
    }
}
static void t_loss(void *ctx, uint8_t ep, uint32_t pk, uint64_t by){
    test_live_note(&live);
    tally *t=ctx; (void)pk;
    t->loss_bytes[ep==CC_EP_AUDIO]+=by; t->loss_events++;
}
static void t_error(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){
    test_live_note(&live);
    tally *t=ctx; (void)ep;(void)seq;(void)st;
    t->error_events++;
    if(kind==CC_ERROR_CONTROL_LOSS) t->control_loss_markers++;
}
static void t_end(void *ctx, enum cc_end r){
    tally *t=ctx;
    if(atomic_exchange(&end_probe,0)){ end_stop_rc=cc_stop(callback_target); cc_close(callback_target); }
    t->end_count++; t->end_reason=r;
    pthread_mutex_lock(&live.mutex);
    atomic_store(&t->ended,1); test_live_note_locked(&live);
    pthread_mutex_unlock(&live.mutex);
}
typedef struct { cc_session *s; int rc; } stop_arg;
static void *stop_thread(void *p){ stop_arg *a=p; a->rc=cc_stop(a->s); return NULL; }
typedef struct { cc_session *s; int rc; _Atomic int returned; } start_arg;
static void *start_thread(void *p){
    start_arg *a=p; starter_thread=pthread_self();
    a->rc=cc_start(a->s); atomic_store(&a->returned,1); return NULL;
}
static void run_replay_opt(const char *path, int ring_mb, tally *t, int throttle,
                           long expected_meta_drops, int fail_stop_on_control_loss){
    memset(t,0,sizeof *t);
    t->main_thread=pthread_self();
    t->throttle=throttle;
    pressure_mode=throttle; pressure_events=0; pressure_round=1; loss_round=0; pressure_ready=0; input_done=0; resumed=0;
    cc_config cfg={0}; cfg.replay_path=path; cfg.ring_mb=ring_mb;
    cfg.fail_stop_on_control_loss=fail_stop_on_control_loss;
    cc_callbacks cb={0};
    cb.on_packet=t_packet; cb.on_loss=t_loss; cb.on_error=t_error; cb.on_end=t_end; cb.ctx=t;
    cc_session *s=NULL;
    CHECK(cc_open(&s,&cfg,&cb)==CC_OK,"open %s",path);
    if(!s) return;
    CHECK(cc_start(s)==CC_OK,"start");
    wait_ended(&t->ended, "replay run");
    CHECK(cc_stop(s)==CC_OK,"stop");
    CHECK(cc_packets_delivered(s)==t->pkts[0]+t->pkts[1],"packet progress disagrees with completed callbacks");
    cc_stats st; cc_get_stats(s,&st);
    // stats must tell the same story as the callbacks: cumulative loss, not "pending since last flush"
    CHECK(st.lost_bytes[0]==t->loss_bytes[0] && st.lost_bytes[1]==t->loss_bytes[1],
          "cc_stats loss (%llu/%llu) != callback loss (%llu/%llu)",
          (unsigned long long)st.lost_bytes[0],(unsigned long long)st.lost_bytes[1],
          (unsigned long long)t->loss_bytes[0],(unsigned long long)t->loss_bytes[1]);
    if(expected_meta_drops>=0)
        CHECK(st.control_records_dropped==expected_meta_drops,"control records dropped: %ld (expected %ld)",st.control_records_dropped,expected_meta_drops);
    else
        CHECK(st.control_records_dropped>0,"metadata-exhaustion fixture dropped no control records");
    CHECK(st.control_loss_markers==(long)t->control_loss_markers,
          "control-loss marker stats/callback mismatch: %ld/%u",
          st.control_loss_markers,t->control_loss_markers);
    CHECK(!st.teardown_incomplete,"teardown incomplete");
    cc_close(s);
    if(throttle==1){
        CHECK(resumed && loss_round==2,"periodic pressure did not exercise loss/resume/loss");
        CHECK(t->loss_events>=2,"periodic pressure requires two delivered loss records");
    }
    pressure_mode=0;
}
static void run_replay(const char *path, int ring_mb, tally *t){
    run_replay_opt(path,ring_mb,t,0,0,0);
}

int main(int argc, char **argv){
    test_supervise(argv, "CC_TEST_TOTAL_S", "capture_core_test");
    if (argc == 3 && !strcmp(argv[1], "--deadline-probe")) {
        if (!strcmp(argv[2], "total")) { alarm(0); for (;;) pause(); }
        setenv("CC_TEST_WAIT_S", "0", 1);
        if (!strcmp(argv[2], "hook")) { hook_arm=1; cc_test_after_empty_snapshot(NULL); }
        else { _Atomic int ended=0; wait_ended(&ended,"forced wait probe"); }
        return 99;
    }
    if(argc<6){ fprintf(stderr,"usage: %s <slice.tpc> vB vP aB aP [late.tpc [exhaust.tpc vB vP aB aP]]\n",argv[0]); return 9; }
    const char *slice=argv[1];
    uint64_t vB=strtoull(argv[2],0,10), vP=strtoull(argv[3],0,10);
    uint64_t aB=strtoull(argv[4],0,10), aP=strtoull(argv[5],0,10);
    tally t;
    /* A continued loss cannot masquerade as a second round. No worker needed
     * for this adversarial state transition; the real replay below proves resume. */
    pressure_mode=1; pressure_round=2; loss_round=1; resumed=0;
    pressure_event(PRESSURE_LOSS);
    CHECK(loss_round==1,"continued loss counted as round two without resume");
    pressure_mode=0;

    // 1: fidelity
    run_replay(slice,0,&t);
    CHECK(t.bytes[0]==vB && t.pkts[0]==vP,"video fidelity: got %llu B/%llu pkts want %llu/%llu",
          (unsigned long long)t.bytes[0],(unsigned long long)t.pkts[0],
          (unsigned long long)vB,(unsigned long long)vP);
    CHECK(t.bytes[1]==aB && t.pkts[1]==aP,"audio fidelity");
    CHECK(t.loss_events==0,"unexpected loss in fidelity run");
    CHECK(t.error_events==1,"recorded TransferError not replayed to on_error (got %u, fixture carries 1)",t.error_events);
    CHECK(t.end_reason==CC_END_REPLAY_EOF,"end reason %d",t.end_reason);
    CHECK(t.end_count==1,"on_end fired %d times",t.end_count);
    CHECK(!t.cb_on_main,"callbacks ran on the caller's thread");

    // 2: honesty under forced overflow (1 MB ring, condition-held consumer)
    run_replay_opt(slice,1,&t,1,0,0);
    CHECK(t.loss_events>0,"1MB ring produced no overflow — test not exercising loss");
    CHECK(t.bytes[0]+t.loss_bytes[0]==vB,
          "video accounting UNBALANCED: %llu delivered + %llu lost != %llu",
          (unsigned long long)t.bytes[0],(unsigned long long)t.loss_bytes[0],
          (unsigned long long)vB);
    CHECK(t.bytes[1]+t.loss_bytes[1]==aB,"audio accounting unbalanced");
    CHECK(t.end_count==1,"on_end fired %d times (overflow run)",t.end_count);

    // Hold through ring loss AND the recorded late TransferError. Coalescing must
    // preserve both without assuming a disk speed or a callback duration.
    if(argc>=7){
        run_replay_opt(argv[6],1,&t,2,0,0);
        CHECK(t.loss_events>0,"blocked consumer did not exercise loss coalescing");
        CHECK(t.error_events==1,"late TransferError lost behind DATA pressure (got %u)",t.error_events);
    }
    if(argc>=12){
        uint64_t ex_vB=strtoull(argv[8],0,10), ex_aB=strtoull(argv[10],0,10);

        // Default policy preserves the archive's data path while marking it permanently
        // not-clean exactly once.  Every DATA byte is still either delivered or confessed.
        run_replay_opt(argv[7],1,&t,3,-1,0);
        CHECK(t.end_reason==CC_END_REPLAY_EOF,"continuation policy ended %d, expected replay EOF",t.end_reason);
        CHECK(t.control_loss_markers==1,"continuation policy emitted %u control-loss markers",t.control_loss_markers);
        CHECK(t.bytes[0]+t.loss_bytes[0]==ex_vB,"metadata continuation video accounting unbalanced");
        CHECK(t.bytes[1]+t.loss_bytes[1]==ex_aB,"metadata continuation audio accounting unbalanced");

        // Operators may explicitly choose the old fail-stop policy.
        run_replay_opt(argv[7],1,&t,3,-1,1);
        CHECK(t.end_reason==CC_END_INTERNAL_ERROR,"fail-stop metadata exhaustion ended %d",t.end_reason);
        CHECK(t.control_loss_markers==1,"fail-stop policy emitted %u control-loss markers",t.control_loss_markers);
    }

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
    callback_target=s; callback_stop_rc=end_stop_rc=99; callback_probe=end_probe=1;
    CHECK(cc_stop(s)==CC_ERR_STATE,"stop before start accepted");
    CHECK(cc_start(s)==CC_OK,"start (lifecycle)");
    CHECK(cc_start(s)==CC_ERR_STATE,"double start accepted");
    wait_ended(&lt.ended, "lifecycle run");
    CHECK(callback_probe==0 && callback_stop_rc==CC_ERR_STATE,"callback stop must be refused");
    CHECK(end_probe==0 && end_stop_rc==CC_ERR_STATE,"on_end stop must be refused");
    CHECK(cc_stop(s)==CC_OK,"stop (lifecycle)");
    CHECK(cc_stop(s)==CC_OK,"second stop must be an idempotent no-op");
    int closed_before=destroyed;
    cc_test_reuse_worker_ids(s);
    CHECK(cc_stop(s)==CC_OK,"external stop with reused worker IDs must succeed");
    cc_close(s);
    CHECK(destroyed==closed_before+1,"external close with reused worker IDs must destroy session");
    CHECK(lt.end_count==1,"lifecycle on_end count %d",lt.end_count);
    // close-after-start without stop must stop first (ASan/TSan builds prove no use-after-free)
    cc_session *s2=NULL; tally lt2; memset(&lt2,0,sizeof lt2); lt2.main_thread=pthread_self(); cb.ctx=&lt2;
    CHECK(cc_open(&s2,&cfg,&cb)==CC_OK,"open (close-without-stop)");
    CHECK(cc_start(s2)==CC_OK,"start (close-without-stop)");
    wait_ended(&lt2.ended, "close-without-stop run");
    cc_close(s2);
    CHECK(lt2.end_count==1,"close-without-stop on_end count %d",lt2.end_count);
    cc_config badin={0}; badin.input=(enum cc_input)77;
    CHECK(cc_open(&s2,&badin,&cb)==CC_ERR_ARGS,"invalid input enum was accepted (would silently select S-video)");

    // Force the consumer to hold a stale empty snapshot while the producer publishes the
    // complete fixture and backend_done.  The acquire reload must still drain every record.
    atomic_store(&hook_arm,1); atomic_store(&hook_empty,0); atomic_store(&hook_release,0);
    run_replay(slice,0,&t);
    CHECK(atomic_load(&hook_empty),"empty-snapshot hook was not exercised");
    CHECK(t.bytes[0]==vB && t.bytes[1]==aB,"stale-empty race stranded published records");
    atomic_store(&hook_arm,0);

    // A delivery allocation failure is a failed start, not a silently wedged session.  No
    // on_end callback belongs to a start call that returned failure.
    tally af; memset(&af,0,sizeof af); af.main_thread=pthread_self(); cb.ctx=&af;
    cfg.replay_path=slice; atomic_store(&hook_fail_alloc,1); s=NULL;
    CHECK(cc_open(&s,&cfg,&cb)==CC_OK,"open (delivery allocation fault)");
    if(s){
        CHECK(cc_start(s)==CC_ERR_NOMEM,"delivery allocation fault did not fail start as NOMEM");
        cc_close(s); /* Join even on a regression returning OK before reading callback-owned tally. */
        CHECK(af.end_count==0,"on_end fired for failed start");
    }

    // Force the former losing ordering: allocation stays unresolved while the backend
    // would otherwise be free to report success. The preflight must run on the starter,
    // before worker creation (thread identity makes this assertion scheduler-independent).
    memset(&af,0,sizeof af); af.main_thread=pthread_self(); cb.ctx=&af; s=NULL;
    CHECK(cc_open(&s,&cfg,&cb)==CC_OK,"open (held allocation)");
    if(s){
        alloc_entered=0; alloc_release=0; alloc_hold=1; hook_fail_alloc=1;
        start_arg a={.s=s,.rc=-99}; pthread_t thread;
        int created=pthread_create(&thread,NULL,start_thread,&a);
        CHECK(created==0,"create held-allocation starter");
        if(!created){
            double begun=test_now(); pthread_mutex_lock(&live.mutex);
            while(!atomic_load(&alloc_entered)) test_live_wait(&live,begun,"held allocation hook not entered");
            CHECK(atomic_load(&alloc_on_starter),"allocation did not precede worker launch on the starting thread");
            CHECK(!atomic_load(&a.returned),"cc_start returned while allocation was unresolved");
            alloc_release=1; test_live_note_locked(&live); pthread_mutex_unlock(&live.mutex);
            pthread_join(thread,NULL);
            CHECK(a.rc==CC_ERR_NOMEM,"held allocation returned %d, expected NOMEM",a.rc);
            CHECK(cc_stop(s)==CC_OK,"stop after failed preflight");
            CHECK(af.end_count==0,"on_end fired after failed allocation preflight");
        }
        alloc_hold=0; cc_close(s);
    }

    // Concurrent stop callers elect exactly one joiner; the waiter returns only after STOPPED.
    tally ct; memset(&ct,0,sizeof ct); ct.main_thread=pthread_self(); cb.ctx=&ct;
    cc_config pcfg={0}; pcfg.replay_path=slice; pcfg.replay_pace_us=100000; s=NULL;
    CHECK(cc_open(&s,&pcfg,&cb)==CC_OK,"open (concurrent stop)");
    if(s){
        CHECK(cc_start(s)==CC_OK,"start (concurrent stop)"); usleep(20000);
        stop_arg a={s,-99}, b={s,-99}; pthread_t ta,tb;
        pthread_create(&ta,NULL,stop_thread,&a); pthread_create(&tb,NULL,stop_thread,&b);
        pthread_join(ta,NULL); pthread_join(tb,NULL);
        CHECK(a.rc==CC_OK && b.rc==CC_OK,"concurrent stop results %d/%d",a.rc,b.rc);
        CHECK(ct.end_count==1,"concurrent stop on_end count %d",ct.end_count); cc_close(s);
    }

    printf(fails? "FAILURES: %d\n" : "ALL TESTS PASSED\n", fails);
    return fails?1:0;
}
