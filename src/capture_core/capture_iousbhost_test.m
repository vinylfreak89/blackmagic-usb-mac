/* The IOUSBHost backend itself (capture_iousbhost.m, unmodified) against the fake IOUSBHost (ih_fake_iousbhost.m),
 * under TSan (make test-iousbhost). The fake's packets carry their bus microframe number, so every scenario checks
 * the one property that matters: from the first microframe to the last, each is accounted exactly once, as a packet
 * in order or inside a reported unread gap or past-due run. Stalls, refusals, removal notices, the start gate and the
 * stop backstop are driven here; the measured behaviour of the real stack is in README "USB stacks". */
#import <Foundation/Foundation.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "capture_core.h"
#include "capture_iousbhost.h"
#include "ih_fake_iokit.h"

static int fails;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
#define NPK 128

typedef struct {
    int started; uint64_t expect; uint32_t last_seq;
    long xfers, packets, ok, too_old, dead, other_bad, mismatch, seq_bad, gap_frames, gaps;
} ep_rec;
static struct {
    ep_rec r[2];
    _Atomic int after_stop, late_calls, calls;
    int stall_at, stall_ms, refuse_at, refuse_n, refuse_all_at, terminate_at, late_at, late_k;
    dispatch_semaphore_t stalled, unstalled;
    long submit_failed[2], fatal[4]; int fatal_reason_last; _Atomic uint64_t fatal_ms; _Atomic long ok_video, enq_at_fatal; int stall_dead_ms, stall_dead_done;
} T;

static void on_transfer(void *ctx, int ep, uint32_t seq, int io, uint64_t unread, uint32_t too_old){ (void)ctx; (void)io; (void)too_old;
    atomic_fetch_add(&T.calls,1); if(atomic_load(&T.after_stop)) atomic_fetch_add(&T.late_calls,1);
    ep_rec *r=&T.r[ep];
    if(r->started && seq!=r->last_seq+1) r->seq_bad++;
    r->last_seq=seq; r->xfers++;
    if(unread){ r->gaps++; r->gap_frames+=(long)unread; if(r->started) r->expect+=unread*8; }
    if(ep==0 && r->xfers==T.refuse_at) atomic_store(&ih_fake.refuse[0],T.refuse_n);
    if(ep==0 && r->xfers==T.refuse_all_at) atomic_store(&ih_fake.refuse_all[0],1);
    if(ep==0 && r->xfers==T.terminate_at) ih_fake_terminate();
    /* hold until the bus is exactly late_k frames past the end of what is queued: this transfer's requeue (right
     * after this callback) then lands that late, and the backlog behind it catches up in a burst, as on hardware */
    if(ep==0 && r->xfers==T.late_at){ uint64_t target=atomic_load(&ih_fake.queue_end[0])+(uint64_t)T.late_k;
        while(ih_fake_frame_now()<target) usleep(100); }
    if(ep==0 && r->xfers==T.stall_at){ if(T.stalled) dispatch_semaphore_signal(T.stalled); usleep((useconds_t)T.stall_ms*1000); if(T.unstalled) dispatch_semaphore_signal(T.unstalled); }
}
static void on_packet(void *ctx, int ep, uint32_t seq, int pi, int ok, uint32_t st, uint32_t req, uint32_t actual, const uint8_t *d){
    (void)ctx; (void)seq; (void)pi; (void)req;
    atomic_fetch_add(&T.calls,1); if(atomic_load(&T.after_stop)) atomic_fetch_add(&T.late_calls,1);
    ep_rec *r=&T.r[ep]; r->packets++;
    if(ok && actual>=8){
        uint64_t uf; memcpy(&uf,d,8);
        if(!r->started){ r->started=1; r->expect=uf; }
        if(uf!=r->expect) r->mismatch++;
        r->ok++; if(!ep) atomic_fetch_add(&T.ok_video,1);
    } else if(st==(uint32_t)kIOReturnIsoTooOld) r->too_old++;
    else if(st==(uint32_t)kIOReturnNoResources) r->dead++;   /* the fake's dead link */
    else r->other_bad++;
    if(r->started) r->expect++;
    /* the first failed video transfer's last packet (after the backend has timed it): one more failed video transfer
     * to come, then the queue stands still */
    if(ep==0 && st==(uint32_t)kIOReturnNoResources && pi==NPK-1 && T.stall_dead_ms && !T.stall_dead_done){
        T.stall_dead_done=1; atomic_store(&ih_fake.link_dead,0); atomic_store(&ih_fake.dead_left[0],1); atomic_store(&ih_fake.dead_left[1],0);
        usleep((useconds_t)T.stall_dead_ms*1000); }
}
static void on_tick(void *ctx){ (void)ctx; }
static void on_submit_failed(void *ctx, int ep, uint32_t seq, int io){ (void)ctx; (void)seq; (void)io; T.submit_failed[ep]++; }
static void on_fatal(void *ctx, int reason, int io, int ep, uint32_t seq){ (void)ctx; (void)io; (void)ep; (void)seq;
    if(reason>=1 && reason<=3) T.fatal[reason]++; T.fatal_reason_last=reason; uint64_t z=0; if(atomic_compare_exchange_strong(&T.fatal_ms,&z,clock_gettime_nsec_np(CLOCK_UPTIME_RAW)/1000000))
        atomic_store(&T.enq_at_fatal,atomic_load(&ih_fake.enqueues[0])+atomic_load(&ih_fake.enqueues[1]));
    if(atomic_load(&T.after_stop)) atomic_fetch_add(&T.late_calls,1); }
static void on_diag(void *ctx, const char *line){ (void)ctx; if(getenv("IH_TEST_VERBOSE")) fprintf(stderr,"  diag: %s\n",line); }
static const ih_callbacks CB={ .on_transfer=on_transfer, .on_packet=on_packet, .on_tick=on_tick,
                               .on_submit_failed=on_submit_failed, .on_fatal=on_fatal, .on_diag=on_diag };

static void reset_(void){
    memset(&T.r,0,sizeof T.r); atomic_store(&T.after_stop,0); atomic_store(&T.late_calls,0); atomic_store(&T.calls,0);
    T.stall_at=T.refuse_at=T.refuse_all_at=T.terminate_at=T.late_at=-1; T.late_k=0; T.stall_ms=0; T.refuse_n=0; T.stalled=nil; T.unstalled=nil;
    memset(T.submit_failed,0,sizeof T.submit_failed); memset(T.fatal,0,sizeof T.fatal); T.fatal_reason_last=0; atomic_store(&T.fatal_ms,0); atomic_store(&T.ok_video,0); atomic_store(&T.enq_at_fatal,0); T.stall_dead_ms=0; T.stall_dead_done=0;
    memset(&ih_fake,0,sizeof ih_fake);
}
static ih_dev *open_start_(int deadline_ms, int *rc){
    ih_dev *d=NULL; char err[200];
    CHECK(ih_open(&d,0x3C000000u,0x80808000u,0x73c60001u,err,sizeof err)==CC_OK,"open: %s",err);
    *rc=ih_start(d,&CB,32,NPK,15360,NPK,192,deadline_ms,err,sizeof err);
    return d;
}
/* every microframe from the first to the last once; returns microframes covered */
static uint64_t check_accounting_(const char *what, const ih_stats *st){
    uint64_t covered=0;
    for(int ep=0;ep<2;ep++){
        ep_rec *r=&T.r[ep];
        CHECK(r->mismatch==0,"%s ep%d: %ld packets off their microframe",what,ep,r->mismatch);
        CHECK(r->seq_bad==0,"%s ep%d: %ld seq steps not +1",what,ep,r->seq_bad);
        CHECK(r->other_bad==0,"%s ep%d: %ld packets failed other than too old",what,ep,r->other_bad);
        CHECK(r->packets==r->xfers*NPK,"%s ep%d: %ld packets in %ld transfers",what,ep,r->packets,r->xfers);
        CHECK(st->unread_frames[ep]==st->unread_delivered[ep]+st->unread_at_stop[ep],"%s ep%d: unread %llu != %llu + %llu",what,ep,
              (unsigned long long)st->unread_frames[ep],(unsigned long long)st->unread_delivered[ep],(unsigned long long)st->unread_at_stop[ep]);
        CHECK(st->too_old[ep]==(uint64_t)r->too_old,"%s ep%d: too-old stat %llu, seen %ld",what,ep,(unsigned long long)st->too_old[ep],r->too_old);
        CHECK(st->too_old_mismatch[ep]==0,"%s ep%d: %llu too-old counts off the prediction",what,ep,(unsigned long long)st->too_old_mismatch[ep]);
        covered+=r->expect;
    }
    return covered;
}
static long closed_transfers, last_transfers;
static void finish_(ih_dev *d, ih_stats *st){ ih_stop(d,st); atomic_store(&T.after_stop,1); last_transfers=st->transfers; }
static void close_(ih_dev *d){ ih_close(d); closed_transfers+=last_transfers; }

int main(void){ @autoreleasepool {
    int rc; ih_stats st; ih_dev *d;

    /* 1. clean, with the callbacks held for 200 ms after the start (the gate): nothing before ih_go, nothing lost */
    reset_(); d=open_start_(2000,&rc); CHECK(rc==CC_OK,"start");
    usleep(200000); CHECK(atomic_load(&T.calls)==0,"%d callbacks before ih_go",atomic_load(&T.calls));
    ih_go(d); usleep(1200000); finish_(d,&st); usleep(100000);
    check_accounting_("clean",&st);
    CHECK(T.r[0].gaps==0 && T.r[1].gaps==0 && T.r[0].too_old==0 && T.r[1].too_old==0,"clean: loss (gaps %ld/%ld, too old %ld/%ld)",T.r[0].gaps,T.r[1].gaps,T.r[0].too_old,T.r[1].too_old);
    CHECK(st.fleet[0]==32 && st.fleet[1]==32,"clean: fleet %d+%d",st.fleet[0],st.fleet[1]);
    CHECK(st.transfers==64 && st.transfers_freed==64 && !st.incomplete,"clean: transfers %d freed %d incomplete %d",st.transfers,st.transfers_freed,st.incomplete);
    CHECK(atomic_load(&T.late_calls)==0,"clean: %d callbacks after ih_stop",atomic_load(&T.late_calls));
    close_(d);
    printf("  clean: %ld+%ld transfers, every microframe once; nothing before ih_go or after ih_stop\n",T.r[0].xfers,T.r[1].xfers);

    /* 2. the queue held inside a callback: under the 512 ms queued (no loss), near it (past-due packets or a gap),
     *    well past it (a gap) -- every microframe still accounted once */
    int holds[]={300,505,800};
    for(int i=0;i<3;i++){
        reset_(); T.stall_at=20; T.stall_ms=holds[i];
        d=open_start_(2000,&rc); ih_go(d); usleep((useconds_t)(1200+holds[i])*1000); finish_(d,&st);
        check_accounting_("hold",&st);
        long lost=T.r[0].gap_frames*8+T.r[0].too_old;
        if(holds[i]==300) CHECK(lost==0 && T.r[1].gap_frames==0,"hold 300: %ld video packets lost",lost);
        if(holds[i]==800) CHECK(T.r[0].gaps==1 && T.r[0].gap_frames>200,"hold 800: %ld gaps of %ld frames",T.r[0].gaps,T.r[0].gap_frames);
        printf("  hold %d ms: video %ld unread frames in %ld gaps + %ld past-due packets, audio %ld + %ld; accounted exactly\n",
               holds[i],T.r[0].gap_frames,T.r[0].gaps,T.r[0].too_old,T.r[1].gap_frames,T.r[1].too_old);
        close_(d);
    }

    /* 2b. a requeue landing exactly k frames late: under a whole transfer (16 frames) it is accepted with those
     *     packets failed as too old (the frame being crossed may go either way); past it, refused and requeued
     *     ahead with an exact gap */
    int lates[]={1,8,13,20};   /* 13: the callbacks after the hold can take a frame or two, and 16 failed is refused */
    for(int i=0;i<4;i++){
        int k=lates[i]; reset_(); T.late_at=20; T.late_k=k;
        d=open_start_(2000,&rc); ih_go(d); usleep(1500000); finish_(d,&st);
        check_accounting_("late",&st);
        /* the bus is at f+k when it is queued: frames f..f+k+1 fail (the kernel's lead, as measured) */
        if(k<16) CHECK(T.r[0].gaps==0 && T.r[0].too_old>=8*(k+2) && T.r[0].too_old<=8*(k+4),"late %d: gaps %ld, too old %ld (want %d..%d)",k,T.r[0].gaps,T.r[0].too_old,8*(k+2),8*(k+4));
        else CHECK(T.r[0].gaps==1 && T.r[0].too_old==0 && T.r[0].gap_frames>=k+8 && T.r[0].gap_frames<=k+10,"late %d: %ld gaps of %ld frames, too old %ld",k,T.r[0].gaps,T.r[0].gap_frames,T.r[0].too_old);
        printf("  requeue %d frames late: %ld past-due packets, %ld unread frames in %ld gaps; prediction held\n",k,T.r[0].too_old,T.r[0].gap_frames,T.r[0].gaps);
        close_(d);
    }

    /* 3. a requeue refused 5 times (not late), then accepted: reported once, recovered, nothing lost */
    reset_(); T.refuse_at=10; T.refuse_n=5;
    d=open_start_(2000,&rc); ih_go(d); usleep(800000); finish_(d,&st);
    check_accounting_("refused 5x",&st);
    CHECK(T.submit_failed[0]==1 && st.resubmit_recovered[0]==1 && st.submit_failures[0]==5,"refused 5x: reported %ld, recovered %llu, attempts %llu",
          T.submit_failed[0],(unsigned long long)st.resubmit_recovered[0],(unsigned long long)st.submit_failures[0]);
    CHECK(T.fatal[1]+T.fatal[2]==0,"refused 5x: fatal");
    CHECK(T.r[0].gaps==0,"refused 5x: %ld gaps",T.r[0].gaps);
    close_(d);
    printf("  refused 5 times: one report, recovered, nothing lost\n");

    /* 4. refusals past the deadline: one report per transfer (not per retry), then one fatal */
    reset_(); T.refuse_all_at=10;
    d=open_start_(60,&rc); ih_go(d); usleep(500000); finish_(d,&st);
    check_accounting_("refused for good",&st);
    CHECK(T.fatal[2]==1 && T.fatal[1]==0,"refused for good: fatal %ld/%ld",T.fatal[1],T.fatal[2]);
    CHECK(T.submit_failed[0]>=1 && T.submit_failed[0]<=32 && st.submit_failures[0]>(uint64_t)T.submit_failed[0],
          "refused for good: %ld reports for %llu attempts",T.submit_failed[0],(unsigned long long)st.submit_failures[0]);
    close_(d);
    printf("  refused past the deadline: %ld reports for %llu attempts, one fatal\n",T.submit_failed[0],(unsigned long long)st.submit_failures[0]);

    /* 5. removal while streaming: one reason-1 fatal, device_gone at stop; a notice after the stop calls nothing */
    reset_(); T.terminate_at=15;
    d=open_start_(2000,&rc); ih_go(d); usleep(600000); finish_(d,&st);
    CHECK(T.fatal[1]==1 && T.fatal[2]<=1 && st.device_gone,"removal: fatal %ld/%ld, device_gone %d",T.fatal[1],T.fatal[2],st.device_gone);
    check_accounting_("removal",&st);
    close_(d);
    reset_(); d=open_start_(2000,&rc); ih_go(d); usleep(300000); finish_(d,&st);
    ih_fake_terminate(); usleep(100000);
    CHECK(atomic_load(&T.late_calls)==0 && T.fatal[1]==0,"notice after stop: %d late calls, fatal %ld",atomic_load(&T.late_calls),T.fatal[1]);
    close_(d);
    printf("  removal: one fatal while streaming, nothing after the stop\n");

    /* 6. a refused start: an error, one fatal inside ih_start, and nothing handed over afterwards */
    reset_(); atomic_store(&ih_fake.refuse_all[1],1);
    d=open_start_(2000,&rc); CHECK(rc!=CC_OK,"refused start returned OK");
    int during=atomic_load(&T.calls); usleep(100000); finish_(d,&st); usleep(100000);
    CHECK(atomic_load(&T.calls)==during && during==0,"refused start: %d callbacks",atomic_load(&T.calls));
    CHECK(T.fatal[2]==1,"refused start: fatal %ld",T.fatal[2]);
    close_(d);
    printf("  refused start: nothing handed over\n");

    /* 7. the stop while a callback is stalled longer than the backstop: ih_stop returns incomplete, and nothing more
     *    reaches the caller afterwards (the stalled callback stops at its next check) */
    reset_(); T.stall_at=12; T.stall_ms=1500; T.stalled=dispatch_semaphore_create(0); T.unstalled=dispatch_semaphore_create(0);
    d=open_start_(2000,&rc); ih_go(d);
    dispatch_semaphore_wait(T.stalled,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC));
    finish_(d,&st);
    CHECK(st.incomplete,"stalled stop: not marked incomplete");
    CHECK(!dispatch_semaphore_wait(T.unstalled,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC)),"stalled callback never returned");
    usleep(500000);
    CHECK(atomic_load(&T.late_calls)==0,"stalled stop: %d callbacks after ih_stop returned",atomic_load(&T.late_calls));
    printf("  stop during a stalled callback: incomplete, nothing after ih_stop (session leaked by design)\n");

    /* every transfer of the closed sessions is eventually deallocated (7's session is leaked by design) */
    for(int i=0;i<40 && atomic_load(&ih_fake_xfer_deallocs)<closed_transfers;i++) usleep(50000);
    CHECK(atomic_load(&ih_fake_xfer_deallocs)==closed_transfers,"%ld of %ld transfers deallocated after their sessions closed",atomic_load(&ih_fake_xfer_deallocs),closed_transfers);
    printf("  all %ld transfers of the closed sessions deallocated\n",closed_transfers);

    /* 8. a link that dies with the device still attached (2026-11-10): the reads complete about every 100 ms here
     *    (2 s on hardware), each failed, nothing delivered, and the requeues are accepted. Once one endpoint's streak
     *    reaches the deadline (300 ms): one reason-3 fatal, and requeuing stops */
    reset_(); atomic_store(&ih_fake.dead_spacing_ms,100);
    d=open_start_(300,&rc); ih_go(d); usleep(300000);
    uint64_t died_ms=clock_gettime_nsec_np(CLOCK_UPTIME_RAW)/1000000;
    atomic_store(&ih_fake.link_dead,1);
    for(int i=0;i<60 && !atomic_load(&T.fatal_ms);i++) usleep(50000);
    long enq_at_fatal=atomic_load(&T.enq_at_fatal);   /* sampled inside on_fatal: the fatal transfer's own requeue counts */
    usleep(400000);
    long enq_after=atomic_load(&ih_fake.enqueues[0])+atomic_load(&ih_fake.enqueues[1]);
    long dead_seen=atomic_load(&ih_fake.dead_completions[0])+atomic_load(&ih_fake.dead_completions[1]);
    finish_(d,&st);
    CHECK(T.fatal[3]==1 && T.fatal[1]==0 && T.fatal[2]==0,"dead link: fatal %ld/%ld/%ld (want 0/0/1)",T.fatal[1],T.fatal[2],T.fatal[3]);
    uint64_t fms=atomic_load(&T.fatal_ms), took=fms?fms-died_ms:0;
    CHECK(fms && took>=300 && took<=900,"dead link: ended %llu ms after the link died (want 300..900)",(unsigned long long)took);
    CHECK(enq_after==enq_at_fatal,"dead link: %ld reads queued after the session ended",enq_after-enq_at_fatal);
    CHECK(st.dead_transfers[0]+st.dead_transfers[1]>=2 && T.r[0].dead+T.r[1].dead>=2*NPK,"dead link: %llu+%llu dead transfers, %ld+%ld dead packets",
          (unsigned long long)st.dead_transfers[0],(unsigned long long)st.dead_transfers[1],T.r[0].dead,T.r[1].dead);
    check_accounting_("dead link",&st);
    close_(d);
    printf("  dead link (device attached): ended %llu ms after it died, %ld failed completions, no read queued after\n",(unsigned long long)took,dead_seen);

    /* 9. a dead stretch shorter than the deadline (here 150 ms of failed reads against 600): no fatal, and the
     *    stream goes on delivering */
    reset_(); d=open_start_(600,&rc); ih_go(d); usleep(200000);
    atomic_store(&ih_fake.link_dead,1); usleep(150000); atomic_store(&ih_fake.link_dead,0);
    long ok_before=atomic_load(&T.ok_video); usleep(500000);
    long ok_after=atomic_load(&T.ok_video);
    finish_(d,&st);
    CHECK(T.fatal[1]+T.fatal[2]+T.fatal[3]==0,"brief dead stretch: fatal %ld/%ld/%ld",T.fatal[1],T.fatal[2],T.fatal[3]);
    CHECK(st.dead_transfers[0]>0 && ok_after>ok_before+100,"brief dead stretch: %llu dead video transfers, %ld packets delivered after",
          (unsigned long long)st.dead_transfers[0],ok_after-ok_before);
    check_accounting_("brief dead stretch",&st);
    close_(d);
    printf("  dead stretch shorter than the deadline: %llu+%llu failed transfers, no fatal, delivery resumed\n",
           (unsigned long long)st.dead_transfers[0],(unsigned long long)st.dead_transfers[1]);

    /* 9b. the transfer fails while its packets say Success with no data: still counted as failed, one reason-3 fatal */
    reset_(); atomic_store(&ih_fake.dead_spacing_ms,100); atomic_store(&ih_fake.dead_pkt_ok,1);
    d=open_start_(300,&rc); ih_go(d); usleep(200000); atomic_store(&ih_fake.link_dead,1);
    for(int i=0;i<60 && !atomic_load(&T.fatal_ms);i++) usleep(50000);
    finish_(d,&st);
    CHECK(T.fatal[3]==1 && T.fatal[1]+T.fatal[2]==0,"transfer-level failure: fatal %ld/%ld/%ld (want 0/0/1)",T.fatal[1],T.fatal[2],T.fatal[3]);
    close_(d);
    printf("  transfer failed, packets Success with no data: one reason-3 fatal\n");

    /* 9c. two failed stretches of 400 ms, delivery between them, against a 600 ms deadline: a delivery ends the
     *     streak, so no fatal (without the reset the second stretch would reach the deadline) */
    reset_(); d=open_start_(600,&rc); ih_go(d); usleep(200000);
    atomic_store(&ih_fake.link_dead,1); usleep(400000); atomic_store(&ih_fake.link_dead,0); usleep(150000);
    atomic_store(&ih_fake.link_dead,1); usleep(400000); atomic_store(&ih_fake.link_dead,0); usleep(200000);
    finish_(d,&st);
    CHECK(T.fatal[1]+T.fatal[2]+T.fatal[3]==0,"two stretches: fatal %ld/%ld/%ld",T.fatal[1],T.fatal[2],T.fatal[3]);
    CHECK(st.dead_transfers[0]>=20,"two stretches: only %llu failed video transfers",(unsigned long long)st.dead_transfers[0]);
    check_accounting_("two stretches",&st);
    close_(d);
    printf("  two failed stretches split by delivery: %llu failed video transfers, no fatal\n",(unsigned long long)st.dead_transfers[0]);

    /* 9d. two failed video transfers with an 800 ms queue stall between their processing (deadline 500): the streak
     *     looks long only because the queue stood still; the transfers that completed during the stall are already
     *     waiting, and their data cancels the end */
    reset_(); T.stall_dead_ms=800; d=open_start_(500,&rc); ih_go(d); usleep(200000);
    atomic_store(&ih_fake.link_dead,1);
    usleep(1800000);
    finish_(d,&st);
    CHECK(T.stall_dead_done,"stall between failures: the hook never ran");
    CHECK(T.fatal[1]+T.fatal[2]+T.fatal[3]==0,"stall between failures: fatal %ld/%ld/%ld",T.fatal[1],T.fatal[2],T.fatal[3]);
    CHECK(st.dead_transfers[0]==2,"stall between failures: %llu failed video transfers (want 2)",(unsigned long long)st.dead_transfers[0]);
    close_(d);
    printf("  queue stall between two failures: the waiting deliveries cancelled the end\n");

    /* 10. no device */
    reset_(); atomic_store(&ih_fake.absent,1); ih_dev *x=NULL; char err[100];
    CHECK(ih_open(&x,0,0,0,err,sizeof err)==CC_ERR_NODEVICE && !x,"absent device opened");

    if(fails){ printf("FAILURES: %d\n",fails); return 1; }
    printf("ALL TESTS PASSED\n"); return 0;
}}
