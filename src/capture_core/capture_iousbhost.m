/* capture_iousbhost.m -- see capture_iousbhost.h. Built with -fobjc-arc. */
#import <Foundation/Foundation.h>
#import <IOUSBHost/IOUSBHost.h>
#include <stdatomic.h>
#include <stdio.h>
#include <time.h>
#include <mach/mach_time.h>
#include "capture_core.h"
#include "capture_iousbhost.h"
#ifdef IH_FAKE
#include "ih_fake_iokit.h"   /* the backend test's fake device (ih_fake_iousbhost.m); the framework is not linked */
#endif

#define IH_VID 0x1EDB
#define IH_PID 0xBD3B
#define IH_LEAD 8                      /* frames ahead of the bus a (re)scheduled read starts: 8 ms */
#define IH_MAXX 64
#define IH_PER_FRAME 8                 /* packets per 1 ms frame: bInterval 1 at high speed and above */
/* macOS fails as too old the frame after the one the bus is in as well (measured 2026-10-17: with the bus at a read's
 * first frame f, f and f+1 failed) */
#define IH_KERNEL_LEAD 1
#ifndef IH_BACKSTOP_S
#define IH_BACKSTOP_S 5.0                /* the fake-IOUSBHost test shortens it */
#endif

@interface IHCounter : NSObject {
@public
    _Atomic int n;
}
@end
@implementation IHCounter
@end

@interface IHXfer : NSObject
@property (nonatomic, strong) IHCounter *freed;   /* deallocations, shared with the device: a transfer can outlive it
                                                   * while IOUSBHost still holds its completion block */
@property (nonatomic) int ep;          /* 0 video, 1 audio */
@property (nonatomic) uint32_t seq;
@property (nonatomic) uint64_t gap;    /* frames left unread before this transfer, reported with its data */
@property (nonatomic) uint64_t fail_since_ms;   /* first refused enqueue of the current attempt (0: none) */
@property (nonatomic) uint64_t past_lo, past_hi; /* frames already passed when it was queued: the bus frame before and
                                                   * after the enqueue bracket the count failing as kIOReturnIsoTooOld */
@property (nonatomic, strong) NSMutableData *buf;
@property (nonatomic) IOUSBHostIsochronousTransaction *tl;
@end
@implementation IHXfer
- (void)dealloc { free(_tl); if(_freed) atomic_fetch_add(&_freed->n,1);
#ifdef IH_FAKE
    atomic_fetch_add(&ih_fake_xfer_deallocs,1);
#endif
}
@end

/* Everything below runs on q, except ih_open/ih_close, ih_start's caller around its dispatch_sync, and ih_stop.
 * stopping/detached/quiesced are atomics because ih_stop sets them from outside q when q does not answer. */
@interface IHDev : NSObject {
@public
    IOUSBHostDevice *dev; IOUSBHostInterface *ifc; IOUSBHostPipe *pipe[2];
    dispatch_queue_t q; dispatch_source_t tick; dispatch_group_t inflight;
    ih_callbacks cb; int npk[2], pkt[2]; int deadline_ms;
    uint64_t next[2]; uint32_t seqc[2];
    _Atomic int stopping, detached, quiesced;
    _Atomic int gone;                  /* a termination notice arrived (set on IOUSBHost's queue, read at ih_stop) */
    BOOL fatal_sent, gone_sent;
    BOOL running;                      /* ih_go has run: completions are handed over; refusals are retried */
    BOOL suspended;                    /* q is suspended (ih_start .. ih_go); touched by the caller's thread only */
    BOOL discard;                      /* stopped without ih_go: completions are dropped, never handed over */
    ih_stats st; int live[2];
    uint64_t last_ts[2]; double abs_ns;
    IHCounter *freed;
    NSMutableArray<IHXfer*> *all;
}
@end
@implementation IHDev
@end

static IHDev *D(ih_dev *d){ return (__bridge IHDev*)(void*)d; }
static uint64_t ih_ms_(void){ return clock_gettime_nsec_np(CLOCK_UPTIME_RAW)/1000000; }
static void ih_err(char *err, size_t n, const char *what, NSError *e){
    if(err && n) snprintf(err,n,"%s: %s",what,e?e.localizedDescription.UTF8String:"failed");
}
static BOOL ih_off_(IHDev *d){ return atomic_load(&d->detached) || atomic_load(&d->quiesced) || d->discard; }
/* dispatch_sync with a backstop: NO if q did not run b within s seconds (it still runs b later) */
static BOOL ih_sync_(dispatch_queue_t q, dispatch_block_t b, double s){
    dispatch_semaphore_t sem=dispatch_semaphore_create(0);
    dispatch_async(q,^{ b(); dispatch_semaphore_signal(sem); });
    return dispatch_semaphore_wait(sem,dispatch_time(DISPATCH_TIME_NOW,(int64_t)(s*NSEC_PER_SEC)))==0;
}
static void ih_fatal_(IHDev *d, int reason, int io, int ep, uint32_t seq){
    if(ih_off_(d)) return;
    if(reason==1){ if(d->gone_sent) return; d->gone_sent=YES; } else { if(d->fatal_sent) return; d->fatal_sent=YES; }
    atomic_store(&d->stopping,1);
    if(d->cb.on_fatal) d->cb.on_fatal(d->cb.ctx,reason,io,ep,seq);
}
static void ih_enqueue_(IHDev *d, IHXfer *x);
static void ih_complete_(IHDev *d, IHXfer *x, IOReturn status, IOUSBHostIsochronousTransaction *l){
    int ep=x.ep;
    d->live[ep]--;
    if(ih_off_(d)){ d->st.unread_at_stop[ep]+=x.gap; dispatch_group_leave(d->inflight); return; }
    d->st.completions[ep]++;
    if(status==kIOReturnAborted && atomic_load(&d->stopping)){
        d->st.aborted[ep]++; d->st.unread_at_stop[ep]+=x.gap; dispatch_group_leave(d->inflight); return; }
    IOUSBHostIsochronousTransaction *tl=l?l:x.tl;
    uint32_t old=0;
    for(int i=0;i<d->npk[ep];i++) if(tl[i].status==kIOReturnIsoTooOld) old++;
    d->st.too_old[ep]+=old; d->st.unread_delivered[ep]+=x.gap;
    /* observed past-due packets against the bracket from the bus frame before and after the enqueue: anything else
     * failing as too old shows as a mismatch */
    if(old<x.past_lo*IH_PER_FRAME || old>x.past_hi*IH_PER_FRAME){
        d->st.too_old_mismatch[ep]++;
        if(d->cb.on_diag){ char line[200];
            snprintf(line,sizeof line,"capture_iousbhost: %s transfer seq %u: %u packets failed as too old, outside the %llu..%llu its queueing frames allow",
                     ep?"audio":"video",x.seq,old,(unsigned long long)(x.past_lo*IH_PER_FRAME),(unsigned long long)(x.past_hi*IH_PER_FRAME));
            d->cb.on_diag(d->cb.ctx,line); }
        if(ih_off_(d)){ dispatch_group_leave(d->inflight); return; }   /* the log may have stalled past the stop */
    }
    if(d->cb.on_transfer) d->cb.on_transfer(d->cb.ctx,ep,x.seq,(int)status,x.gap,old);
    /* a callback can stall past ih_stop's backstop: once cut off, nothing more reaches the caller */
    if(ih_off_(d)){ dispatch_group_leave(d->inflight); return; }
    /* bus check (ih_stats.step_dev_ms): the last packet's completion time against the previous transfer's */
    uint64_t ts=tl[d->npk[ep]-1].timeStamp;
    if(ts && d->last_ts[ep] && status==kIOReturnSuccess && !old){
        double ms=(double)(ts-d->last_ts[ep])*d->abs_ns/1e6, frames=(double)(d->npk[ep]/IH_PER_FRAME);
        double dev=ms-frames-(double)x.gap, adev=dev<0?-dev:dev;
        if(x.gap){
            if(adev>d->st.gap_dev_ms[ep]) d->st.gap_dev_ms[ep]=adev;
            if(d->cb.on_diag){ char line[240];
                snprintf(line,sizeof line,"capture_iousbhost: %s: %llu frames unread before transfer seq %u; bus completion times put %.2f frames there",
                         ep?"audio":"video",(unsigned long long)x.gap,x.seq,ms-frames);
                d->cb.on_diag(d->cb.ctx,line); }
        } else { if(adev>d->st.step_dev_ms[ep]) d->st.step_dev_ms[ep]=adev; d->st.steps[ep]++; }
    }
    d->last_ts[ep]=status==kIOReturnSuccess && !old?ts:0;
    x.gap=0;
    const uint8_t *base=(const uint8_t*)x.buf.bytes;
    for(int i=0;i<d->npk[ep] && !ih_off_(d);i++){
        IOUSBHostIsochronousTransaction *t=&tl[i];
        int ok=t->status==kIOReturnSuccess || t->status==kIOReturnUnderrun;
        d->cb.on_packet(d->cb.ctx,ep,x.seq,i,ok,(uint32_t)t->status,t->requestCount,ok?t->completeCount:0,base+t->offset);
    }
    if(!atomic_load(&d->stopping) && !ih_off_(d)) ih_enqueue_(d,x);
    dispatch_group_leave(d->inflight);
}
/* Queue x at its endpoint's next frame. macOS refuses a transfer lying wholly in the past (measured: 16 frames late
 * refused, 15 accepted with those packets failed as kIOReturnIsoTooOld). Refused, it is queued IH_LEAD frames ahead
 * of the bus instead: the frames between are never read, and that exact count goes out with x's data. x takes its seq only once queued, so seqs follow frame order whatever was retried. Any other refusal is
 * retried every millisecond until the deadline (each one reported), then ends the session; during ih_start it
 * ends the start at once. */
static void ih_enqueue_(IHDev *d, IHXfer *x){
    int ep=x.ep, n=d->npk[ep];
    for(int i=0;i<n;i++) x.tl[i]=(IOUSBHostIsochronousTransaction){.status=kIOReturnInvalid,.requestCount=(uint32_t)d->pkt[ep],.offset=(uint32_t)(i*d->pkt[ep])};
    uint64_t f=d->next[ep], g=0, pre=[d->ifc frameNumberWithTime:nil]; NSError *e=nil;
    __weak IHDev *wd=d;
    void (^done)(IOReturn,IOUSBHostIsochronousTransaction*)=^(IOReturn st, IOUSBHostIsochronousTransaction *l){
        IHDev *sd=wd; if(sd) ih_complete_(sd,x,st,l); };
    dispatch_group_enter(d->inflight);
    BOOL ok=[d->pipe[ep] enqueueIORequestWithData:x.buf transactionList:x.tl transactionListCount:(NSUInteger)n
                                firstFrameNumber:f options:IOUSBHostIsochronousTransferOptionsNone error:&e completionHandler:done];
    if(!ok){
        uint64_t cur=[d->ifc frameNumberWithTime:nil];
        if(cur+1>=f){
            uint64_t start=cur+IH_LEAD; g=start-f; f=start; e=nil;
            ok=[d->pipe[ep] enqueueIORequestWithData:x.buf transactionList:x.tl transactionListCount:(NSUInteger)n
                                     firstFrameNumber:f options:IOUSBHostIsochronousTransferOptionsNone error:&e completionHandler:done];
        }
    }
    if(ok){
        uint64_t post=[d->ifc frameNumberWithTime:nil], nf=(uint64_t)(n/IH_PER_FRAME);
        if(g) pre=f;                          /* requeued ahead: its first frame was in the future when the bus read pre */
        x.past_lo=pre>f?(pre-f<nf?pre-f:nf):0;           /* frames certainly past (the one being read may go either way) */
        uint64_t edge=post+1+IH_KERNEL_LEAD;  /* frames before this one may have been failed */
        x.past_hi=edge>f?(edge-f<nf?edge-f:nf):0;
        if(g){ x.gap+=g; d->st.late_resubmits[ep]++; d->st.unread_frames[ep]+=g; }
        if(x.fail_since_ms){ d->st.resubmit_recovered[ep]++; x.fail_since_ms=0; }
        x.seq=d->seqc[ep]++;
        d->st.submits[ep]++; d->live[ep]++;
        d->next[ep]=f+(uint64_t)(n/IH_PER_FRAME);
        return;
    }
    dispatch_group_leave(d->inflight);
    int io=e?(int)e.code:0;
    if(!d->running){ ih_fatal_(d,2,io,ep,d->seqc[ep]); return; }
    uint64_t now=ih_ms_();
    d->st.submit_failures[ep]++;
    if(!x.fail_since_ms){                 /* the first refusal of this requeue is reported; the retries are counted */
        x.fail_since_ms=now?now:1;
        if(d->cb.on_submit_failed) d->cb.on_submit_failed(d->cb.ctx,ep,x.seq,io);
    }
    if(now-x.fail_since_ms>=(uint64_t)d->deadline_ms){ ih_fatal_(d,2,io,ep,x.seq); return; }
    dispatch_group_enter(d->inflight);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_MSEC),d->q,^{
        IHDev *sd=wd; if(!sd) return;
        if(!atomic_load(&sd->stopping) && !ih_off_(sd)) ih_enqueue_(sd,x);
        dispatch_group_leave(sd->inflight);
    });
}

static void ih_teardown_(IHDev *d, BOOL alt0){
    if(alt0) [d->ifc selectAlternateSetting:0 error:nil];
    atomic_store(&d->quiesced,1);
    [d->ifc destroy]; [d->dev destroy];
}
int ih_open(ih_dev **out, uint32_t mode_word, uint32_t r4, uint32_t latch, char *err, size_t errn){ @autoreleasepool {
    NSMutableDictionary *m=(__bridge_transfer NSMutableDictionary*)IOServiceMatching(kIOUSBHostDeviceClassName);
    m[@kUSBHostMatchingPropertyVendorID]=@(IH_VID); m[@kUSBHostMatchingPropertyProductID]=@(IH_PID);
    io_service_t ds=IOServiceGetMatchingService(kIOMainPortDefault,(__bridge_retained CFDictionaryRef)m);
    if(!ds){ if(err&&errn) snprintf(err,errn,"no Shuttle on the USB bus"); return CC_ERR_NODEVICE; }
    IHDev *d=[IHDev new];
    d->q=dispatch_queue_create("capture_core.iousbhost",dispatch_queue_attr_make_with_qos_class(DISPATCH_QUEUE_SERIAL,QOS_CLASS_USER_INTERACTIVE,0));
    d->inflight=dispatch_group_create(); d->all=[NSMutableArray new];
    d->freed=[IHCounter new];
    { mach_timebase_info_data_t tb; mach_timebase_info(&tb); d->abs_ns=tb.denom?(double)tb.numer/(double)tb.denom:1.0; }
    NSError *e=nil;
    __weak IHDev *wd=d;
    /* IOUSBHost delivers interest notices on its own internal queue, not q (IOUSBHostObject.h): move them onto q,
     * where the session state lives; once quiesced (ih_stop / ih_close) they do nothing */
    d->dev=[[IOUSBHostDevice alloc] initWithIOService:ds options:IOUSBHostObjectInitOptionsNone queue:d->q error:&e
                                      interestHandler:^(IOUSBHostObject *o, uint32_t type, void *arg){ (void)o; (void)arg;
        IHDev *sd=wd; if(!sd || type!=kIOMessageServiceIsTerminated) return;
        atomic_store(&sd->gone,1);
        dispatch_async(sd->q,^{ ih_fatal_(sd,1,0,0,0); }); }];
    IOObjectRelease(ds);
    if(!d->dev){ ih_err(err,errn,"open the Shuttle (IOUSBHostDevice)",e); return CC_ERR_USB; }
    if(!d->dev.configurationDescriptor && ![d->dev configureWithValue:1 matchInterfaces:NO error:&e]){
        ih_err(err,errn,"configure",e); atomic_store(&d->quiesced,1); [d->dev destroy]; return CC_ERR_USB; }
    io_service_t is=0, c; io_iterator_t it;   /* interface 0: the device's IOUSBHostInterface child */
    if(IORegistryEntryGetChildIterator(d->dev.ioService,kIOServicePlane,&it)==KERN_SUCCESS){
        while(!is && (c=IOIteratorNext(it))){
            if(IOObjectConformsTo(c,kIOUSBHostInterfaceClassName)){
                CFTypeRef nn=IORegistryEntryCreateCFProperty(c,CFSTR(kUSBHostMatchingPropertyInterfaceNumber),kCFAllocatorDefault,0);
                if(nn && [(__bridge NSNumber*)nn intValue]==0) is=c; else IOObjectRelease(c);
                if(nn) CFRelease(nn);
            } else IOObjectRelease(c);
        }
        IOObjectRelease(it);
    }
    if(!is){ if(err&&errn) snprintf(err,errn,"the Shuttle has no interface 0"); atomic_store(&d->quiesced,1); [d->dev destroy]; return CC_ERR_USB; }
    d->ifc=[[IOUSBHostInterface alloc] initWithIOService:is options:IOUSBHostObjectInitOptionsNone queue:d->q error:&e interestHandler:nil];
    IOObjectRelease(is);
    if(!d->ifc){ ih_err(err,errn,"open interface 0",e); atomic_store(&d->quiesced,1); [d->dev destroy]; return CC_ERR_USB; }
    IOUSBHostDevice *hd=d->dev;           /* the block is local and synchronous: a strong capture makes no cycle */
    BOOL (^vout)(uint16_t,uint32_t)=^BOOL(uint16_t idx,uint32_t be){
        IOUSBDeviceRequest r={.bmRequestType=0x40,.bRequest=215,.wValue=0,.wIndex=idx,.wLength=4};
        uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};
        NSMutableData *dd=[NSMutableData dataWithBytes:b length:4]; NSUInteger nn=0; NSError *ee=nil;
        return [hd sendDeviceRequest:r data:dd bytesTransferred:&nn completionTimeout:1.0 error:&ee] && nn==4;
    };
    /* the same start sequence as the libusb path (capture_core.c cc_open): commit twice at alt 0, reset, apply */
    BOOL ok=[d->ifc selectAlternateSetting:0 error:&e]
        && vout(0,mode_word) && vout(0,mode_word) && vout(4,r4) && vout(4,r4) && vout(24,latch) && vout(24,latch)
        && [d->ifc selectAlternateSetting:1 error:&e] && [d->ifc selectAlternateSetting:2 error:&e]
        && vout(0,mode_word) && vout(24,latch);
    if(!ok){ ih_err(err,errn,"start sequence (alt settings / mode word)",e); ih_teardown_(d,YES); return CC_ERR_USB; }
    d->pipe[0]=[d->ifc copyPipeWithAddress:CC_EP_VIDEO error:&e];
    d->pipe[1]=[d->ifc copyPipeWithAddress:CC_EP_AUDIO error:&e];
    if(!d->pipe[0] || !d->pipe[1]){ ih_err(err,errn,"isochronous pipes",e); ih_teardown_(d,YES); return CC_ERR_USB; }
    for(int ep=0;ep<2;ep++){
        const IOUSBHostIOSourceDescriptors *pd=d->pipe[ep].descriptors;
        if(!pd || pd->descriptor.bInterval!=1){
            if(err&&errn) snprintf(err,errn,"endpoint 0x%02x has bInterval %d, not 1: frame accounting would be wrong",
                                   ep?CC_EP_AUDIO:CC_EP_VIDEO,pd?pd->descriptor.bInterval:-1);
            ih_teardown_(d,YES); return CC_ERR_USB;
        }
    }
    *out=(ih_dev*)(__bridge_retained void*)d;
    return CC_OK;
}}

int ih_start(ih_dev *dv, const ih_callbacks *cb, int xfers, int v_npk, int v_pkt, int a_npk, int a_pkt,
             int deadline_ms, char *err, size_t errn){ @autoreleasepool {
    IHDev *d=D(dv);
    if(xfers<1 || xfers>IH_MAXX || v_npk%IH_PER_FRAME || a_npk%IH_PER_FRAME || !cb->on_packet){
        if(err&&errn) snprintf(err,errn,"bad transfer geometry"); return CC_ERR_ARGS; }
    __block int rc=CC_OK;
    dispatch_sync(d->q,^{
        d->cb=*cb; d->deadline_ms=deadline_ms>0?deadline_ms:2000;
        d->npk[0]=v_npk; d->npk[1]=a_npk; d->pkt[0]=v_pkt; d->pkt[1]=a_pkt;
        for(int ep=0;ep<2 && rc==CC_OK;ep++) for(int k=0;k<xfers && rc==CC_OK;k++){
            /* each endpoint starts IH_LEAD frames after its own first enqueue: one shared start was already
             * 6 frames past for audio after video's 32 enqueues (macOS took the transfer and failed those packets
             * with kIOReturnIsoTooOld, measured 2026-10-17) */
            if(!k) d->next[ep]=[d->ifc frameNumberWithTime:nil]+IH_LEAD;
            NSError *e=nil; IHXfer *x=[IHXfer new]; x.ep=ep; x.freed=d->freed;
            x.buf=[d->ifc ioDataWithCapacity:(NSUInteger)(d->npk[ep]*d->pkt[ep]) error:&e];
            x.tl=calloc((size_t)d->npk[ep],sizeof(IOUSBHostIsochronousTransaction));
            if(!x.buf || !x.tl){ ih_err(err,errn,"I/O buffers",e); rc=CC_ERR_NOMEM; [d->all addObject:x]; d->st.transfers++; break; }
            [d->all addObject:x]; d->st.transfers++;
            ih_enqueue_(d,x);
            if(d->fatal_sent){ if(err&&errn) snprintf(err,errn,"the first transfers could not be queued"); rc=CC_ERR_USB; }
        }
        d->tick=dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER,0,0,d->q);
        dispatch_source_set_timer(d->tick,dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC),NSEC_PER_SEC,10*NSEC_PER_MSEC);
        __weak IHDev *wd=d;
        dispatch_source_set_event_handler(d->tick,^{ IHDev *sd=wd;
            if(sd && !atomic_load(&sd->stopping) && !ih_off_(sd) && sd->cb.on_tick) sd->cb.on_tick(sd->cb.ctx); });
        dispatch_resume(d->tick);
        /* held until ih_go: completions queue up behind this, none is handed over before the caller says so */
        dispatch_suspend(d->q);
    });
    d->suspended=YES;
    return rc;
}}

void ih_go(ih_dev *dv){
    IHDev *d=D(dv);
    if(!d->suspended) return;
    d->running=YES;                       /* q runs nothing while suspended; the resume publishes this */
    d->suspended=NO; dispatch_resume(d->q);
}

void ih_stop(ih_dev *dv, ih_stats *st){ @autoreleasepool {
    IHDev *d=D(dv);
    atomic_store(&d->stopping,1);
    if(d->suspended){                     /* never went: q has run nothing since ih_start, so this thread may write */
        d->discard=YES; d->st.fleet[0]=d->live[0]; d->st.fleet[1]=d->live[1];
        if(d->tick) dispatch_source_cancel(d->tick);
        d->suspended=NO; dispatch_resume(d->q);
    } else if(!ih_sync_(d->q,^{ d->st.fleet[0]=d->live[0]; d->st.fleet[1]=d->live[1]; if(d->tick) dispatch_source_cancel(d->tick); },IH_BACKSTOP_S)){
        atomic_store(&d->detached,1); d->st.incomplete=1;
    }
    for(int ep=0;ep<2;ep++) if(d->pipe[ep]) [d->pipe[ep] abortWithOption:IOUSBHostAbortOptionAsynchronous error:nil];
    long left=d->st.incomplete?1:dispatch_group_wait(d->inflight,dispatch_time(DISPATCH_TIME_NOW,(int64_t)(IH_BACKSTOP_S*NSEC_PER_SEC)));
    /* after this nothing of ours runs on q, and nothing will call the caller again */
    if(left || !ih_sync_(d->q,^{ atomic_store(&d->quiesced,1); },IH_BACKSTOP_S)){
        atomic_store(&d->detached,1); atomic_store(&d->quiesced,1); d->st.incomplete=1;
    }
    if(d->st.incomplete){ char line[200];   /* the caller's log (OBS's, the CLI's stderr), callable from this thread */
        snprintf(line,sizeof line,"capture_iousbhost: the completion queue did not drain within %.1f s of the abort; its callbacks are cut off (session leaked, by design)",IH_BACKSTOP_S);
        if(d->cb.on_diag) d->cb.on_diag(d->cb.ctx,line); else fprintf(stderr,"%s\n",line); }
    [d->ifc selectAlternateSetting:0 error:nil];
    /* ours are dropped here; each is deallocated when IOUSBHost lets go of its completion block too (the fake-device
     * test waits for every one) */
    if(!d->st.incomplete){ d->st.transfers_freed=(int)d->all.count; [d->all removeAllObjects]; }
    d->st.device_gone=atomic_load(&d->gone);
    if(st) *st=d->st;
}}

void ih_close(ih_dev *dv){ @autoreleasepool {
    if(!dv) return;
    IHDev *d=(__bridge_transfer IHDev*)(void*)dv;
    if(d->suspended){ d->discard=YES; d->suspended=NO; dispatch_resume(d->q); }   /* opened and started, never stopped */
    ih_teardown_(d,YES);
    dispatch_sync(d->q,^{});               /* a termination notice moved onto q before the destroy has now run */
    /* every transfer should now be deallocated, once IOUSBHost lets go of its completion blocks: a bounded look,
     * reported (the real framework's retention is measured here; the fake-device test asserts it) */
    int want=d->st.transfers, got=0;
    for(int i=0;i<100 && (got=atomic_load(&d->freed->n))<want;i++) usleep(10000);
    if(got<want){ char line[160]; snprintf(line,sizeof line,"capture_iousbhost: %d of %d transfers still allocated 1 s after close (held by IOUSBHost?)",want-got,want);
        if(d->cb.on_diag) d->cb.on_diag(d->cb.ctx,line); else fprintf(stderr,"%s\n",line); }   /* the caller's session is still alive here */
    d=nil;
}}
