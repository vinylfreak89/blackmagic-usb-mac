/* End to end through capture_core: cc_open/cc_start with usb_backend IOUSBHOST, the unmodified capture_iousbhost.m,
 * and the fake IOUSBHost (ih_fake_iousbhost.m), under TSan (make test-iousbhost). The delivered cc_packet stream is
 * checked microframe by microframe against its HostLoss records, as a .tpc reader would see it: every bus microframe
 * from the first to the last is a packet in order or inside an unread-slot record. Also the end reason after an
 * unplug, and a stop while the completion queue is stalled past the backstop. */
#import <Foundation/Foundation.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "capture_core.h"
#include "ih_fake_iokit.h"

static int fails;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)

typedef struct { int started; uint64_t expect; long packets, bad_status, mismatch, unsched, unsched_pk; } ep_rec;
static ep_rec R[2]; static _Atomic int ended, end_reason, after_stop, late_calls; static int exact_lines, approx_lines;

static void on_packet(void *ctx, const cc_packet *p){ (void)ctx;
    if(atomic_load(&after_stop)) atomic_fetch_add(&late_calls,1);
    ep_rec *r=&R[p->endpoint==CC_EP_AUDIO];
    r->packets++;
    if(p->status==0 && p->actual_len>=8){ uint64_t uf; memcpy(&uf,p->data,8);
        if(!r->started){ r->started=1; r->expect=uf; }
        if(uf!=r->expect) r->mismatch++;
    } else r->bad_status++;
    if(r->started) r->expect++;
}
static void on_loss_ex(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){ (void)ctx; (void)by; (void)seq;
    ep_rec *r=&R[ep==CC_EP_AUDIO];
    if(kind==CC_LOSS_UNSCHEDULED){ r->unsched++; r->unsched_pk+=pk; if(r->started) r->expect+=pk; }
}
static void on_end(void *ctx, enum cc_end why){ (void)ctx; atomic_store(&end_reason,(int)why); atomic_store(&ended,1); }
static void diag(void *ctx, const char *line){ (void)ctx;
    if(strstr(line,"HOST LOSS: ~")) approx_lines++; else if(strstr(line,"HOST LOSS:")) exact_lines++;
    if(getenv("IH_TEST_VERBOSE")) fprintf(stderr,"  diag: %s\n",line); }

static cc_session *run_(cc_stats *st, int secs_ms, int stop){
    memset(R,0,sizeof R); atomic_store(&ended,0); atomic_store(&after_stop,0); atomic_store(&late_calls,0);
    exact_lines=approx_lines=0;
    cc_config cfg; memset(&cfg,0,sizeof cfg); cfg.usb_backend=CC_USB_IOUSBHOST; cfg.ring_mb=64; cfg.diag_log=diag;
    cc_callbacks cb; memset(&cb,0,sizeof cb); cb.on_packet=on_packet; cb.on_loss_ex=on_loss_ex; cb.on_end=on_end;
    cc_session *s=NULL;
    CHECK(cc_open(&s,&cfg,&cb)==CC_OK,"open");
    CHECK(cc_start(s)==CC_OK,"start");
    usleep((useconds_t)secs_ms*1000);
    if(stop){ CHECK(cc_stop(s)==CC_OK,"stop"); atomic_store(&after_stop,1); cc_get_stats(s,st); }   /* stats: after the stop */
    return s;
}
static void accounted_(const char *what){
    for(int e=0;e<2;e++){
        CHECK(R[e].mismatch==0,"%s ep%d: %ld packets off their microframe",what,e,R[e].mismatch);
        CHECK(R[e].started,"%s ep%d: no data",what,e);
    }
}

int main(void){ @autoreleasepool {
    cc_stats st; cc_session *s;

    /* 1. one endpoint's requeue lands k frames late (the other, sharing the completion queue, is held as long and
     *    lands about as late): video 8 frames (accepted, 64 packets failed as too old), then audio 20 (refused, one
     *    exact unread record of 28 frames). Every microframe accounted, and the unread-slot statistics are exactly
     *    the failed packets plus the unread records the stream carries. */
    struct { int ep, k; } lt[]={{0,8},{1,20}};
    for(int i=0;i<2;i++){
        int ep=lt[i].ep, k=lt[i].k;
        memset(&ih_fake,0,sizeof ih_fake);
        atomic_store(&ih_fake.late_at[ep],20); atomic_store(&ih_fake.late_k[ep],k);
        s=run_(&st,1500,1);
        accounted_("late");
        if(k<16) CHECK(R[ep].bad_status>=8*(k+2) && R[ep].bad_status<=8*(k+3) && R[ep].unsched==0,"late ep%d k%d: %ld failed packets, %ld unread records",ep,k,R[ep].bad_status,R[ep].unsched);
        else CHECK(R[ep].unsched==1 && R[ep].unsched_pk>=(k+8)*8 && R[ep].unsched_pk<=(k+9)*8 && R[ep].bad_status==0,
                   "late ep%d k%d: %ld records of %ld packets, %ld failed",ep,k,R[ep].unsched,R[ep].unsched_pk,R[ep].bad_status);
        for(int e=0;e<2;e++)
            CHECK(st.unscheduled_packets[e]==(uint64_t)(R[e].bad_status+R[e].unsched_pk),"late ep%d: stats %llu != %ld failed + %ld unread",e,
                  (unsigned long long)st.unscheduled_packets[e],R[e].bad_status,R[e].unsched_pk);
        CHECK(st.unscheduled_late==0 && exact_lines>=1 && approx_lines==0,"late: %llu late records, %d exact / %d approximate HOST LOSS lines",
              (unsigned long long)st.unscheduled_late,exact_lines,approx_lines);
        CHECK(atomic_load(&end_reason)==CC_END_STOPPED && !st.teardown_incomplete,"late: end %d, incomplete %d",atomic_load(&end_reason),st.teardown_incomplete);
        CHECK(st.transfers_allocated==st.transfers_freed && st.fleet[0]==32 && st.fleet[1]==32,"late: transfers %ld/%ld fleet %d+%d",st.transfers_allocated,st.transfers_freed,st.fleet[0],st.fleet[1]);
        usleep(50000); CHECK(atomic_load(&late_calls)==0,"late: %d packets after cc_stop",atomic_load(&late_calls));
        cc_close(s);
        printf("  %s requeue %d frames late through capture_core: %ld failed packets, %ld slots in %ld exact records; other endpoint %ld + %ld; every microframe accounted\n",
               ep?"audio":"video",k,R[ep].bad_status,R[ep].unsched_pk,R[ep].unsched,R[!ep].bad_status,R[!ep].unsched_pk);
    }

    /* 2. an unplug: requeues fail, the notice follows; the session ends DEVICE_GONE by itself */
    memset(&ih_fake,0,sizeof ih_fake);
    s=run_(&st,400,0);
    ih_fake_terminate();
    for(int i=0;i<200 && !atomic_load(&ended);i++) usleep(10000);
    CHECK(atomic_load(&ended) && atomic_load(&end_reason)==CC_END_DEVICE_GONE,"unplug: ended %d reason %d",atomic_load(&ended),atomic_load(&end_reason));
    CHECK(cc_stop(s)==CC_OK,"unplug: stop");
    accounted_("unplug");
    cc_close(s);
    printf("  unplug: the session ended DEVICE_GONE by itself\n");

    /* 3. the completion queue stalled 1.5 s (inside a completion) while the session stops: the stop returns, marked
     *    incomplete, nothing is delivered after it, and cc_close leaks the session rather than free it under the
     *    stalled callback */
    memset(&ih_fake,0,sizeof ih_fake);
    atomic_store(&ih_fake.late_at[0],15); atomic_store(&ih_fake.late_k[0],1500);
    s=run_(&st,600,1);
    cc_get_stats(s,&st);
    CHECK(st.teardown_incomplete==1,"stalled stop: not marked incomplete");
    usleep(2000000);
    CHECK(atomic_load(&late_calls)==0,"stalled stop: %d packets after cc_stop",atomic_load(&late_calls));
    cc_close(s);   /* leaks by design (teardown incomplete) */
    printf("  stalled stop: incomplete, nothing after cc_stop, session leaked by design\n");

    if(fails){ printf("FAILURES: %d\n",fails); return 1; }
    printf("ALL TESTS PASSED\n"); return 0;
}}
