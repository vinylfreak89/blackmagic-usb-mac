/* capture_iousbhost.m -- see capture_iousbhost.h. Built with -fobjc-arc. */
#import <Foundation/Foundation.h>
#import <IOUSBHost/IOUSBHost.h>
#include <stdio.h>
#include <mach/mach_time.h>
#include "capture_core.h"
#include "capture_iousbhost.h"

#define IH_VID 0x1EDB
#define IH_PID 0xBD3B
#define IH_LEAD 8                      /* frames ahead of the bus a (re)scheduled read starts: 8 ms */
#define IH_MAXX 64
#define IH_PER_FRAME 8                 /* packets per 1 ms frame: bInterval 1 at high speed and above */

@interface IHXfer : NSObject
@property (nonatomic) int ep;          /* 0 video, 1 audio */
@property (nonatomic) uint32_t seq;
@property (nonatomic) uint64_t gap;    /* frames left unread before this transfer, reported with its data */
@property (nonatomic, strong) NSMutableData *buf;
@property (nonatomic) IOUSBHostIsochronousTransaction *tl;
@end
@implementation IHXfer
- (void)dealloc { free(_tl); }
@end

/* Everything below runs on q except ih_open/ih_close and the parts of ih_start/ih_stop outside dispatch_sync. */
@interface IHDev : NSObject {
@public
    IOUSBHostDevice *dev; IOUSBHostInterface *ifc; IOUSBHostPipe *pipe[2];
    dispatch_queue_t q; dispatch_source_t tick; dispatch_group_t inflight;
    ih_callbacks cb; int npk[2], pkt[2];
    uint64_t next[2]; uint32_t seqc[2];
    BOOL stopping, fatal_sent, detached;
    ih_stats st; int live[2];
    uint64_t last_ts[2]; double abs_ns;
    NSMutableArray<IHXfer*> *all;
}
@end
@implementation IHDev
@end

static IHDev *D(ih_dev *d){ return (__bridge IHDev*)(void*)d; }
static void ih_err(char *err, size_t n, const char *what, NSError *e){
    if(err && n) snprintf(err,n,"%s: %s",what,e?e.localizedDescription.UTF8String:"failed");
}
static void ih_fatal_(IHDev *d, int reason, int io, int ep, uint32_t seq){
    if(d->fatal_sent) return;
    d->fatal_sent=YES; d->stopping=YES;
    if(d->cb.on_fatal && !d->detached) d->cb.on_fatal(d->cb.ctx,reason,io,ep,seq);
}
static void ih_enqueue_(IHDev *d, IHXfer *x);
static void ih_complete_(IHDev *d, IHXfer *x, IOReturn status){
    int ep=x.ep;
    d->live[ep]--;
    if(d->detached){ dispatch_group_leave(d->inflight); return; }
    d->st.completions[ep]++;
    if(status==kIOReturnAborted && d->stopping){ d->st.aborted[ep]++; dispatch_group_leave(d->inflight); return; }
    if(d->cb.on_transfer) d->cb.on_transfer(d->cb.ctx,ep,x.seq,(int)status,x.gap);
    /* bus check (ih_stats.step_dev_ms): the last packet's completion time against the previous transfer's */
    uint64_t ts=x.tl[d->npk[ep]-1].timeStamp;
    if(ts && d->last_ts[ep] && status==kIOReturnSuccess){
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
    d->last_ts[ep]=status==kIOReturnSuccess?ts:0;
    x.gap=0;
    const uint8_t *base=(const uint8_t*)x.buf.bytes;
    for(int i=0;i<d->npk[ep];i++){
        IOUSBHostIsochronousTransaction *t=&x.tl[i];
        int ok=t->status==kIOReturnSuccess || t->status==kIOReturnUnderrun;
        d->cb.on_packet(d->cb.ctx,ep,x.seq,i,ok,(uint32_t)t->status,t->requestCount,ok?t->completeCount:0,base+t->offset);
    }
    if(!d->stopping){ x.seq=d->seqc[ep]++; ih_enqueue_(d,x); }
    dispatch_group_leave(d->inflight);
}
/* Queue x at its endpoint's next frame. If macOS refuses because that frame has passed (or is being read now), queue
 * it IH_LEAD frames ahead of the bus instead: the frames between are never read, and that exact count goes out with
 * x's data. Any other refusal ends the session. */
static void ih_enqueue_(IHDev *d, IHXfer *x){
    int ep=x.ep, n=d->npk[ep];
    for(int i=0;i<n;i++) x.tl[i]=(IOUSBHostIsochronousTransaction){.status=kIOReturnInvalid,.requestCount=(uint32_t)d->pkt[ep],.offset=(uint32_t)(i*d->pkt[ep])};
    uint64_t f=d->next[ep]; NSError *e=nil;
    __weak IHDev *wd=d;
    void (^done)(IOReturn,IOUSBHostIsochronousTransaction*)=^(IOReturn st, IOUSBHostIsochronousTransaction *l){ (void)l;
        IHDev *sd=wd; if(sd) ih_complete_(sd,x,st); };
    dispatch_group_enter(d->inflight);
    BOOL ok=[d->pipe[ep] enqueueIORequestWithData:x.buf transactionList:x.tl transactionListCount:(NSUInteger)n
                                firstFrameNumber:f options:IOUSBHostIsochronousTransferOptionsNone error:&e completionHandler:done];
    if(!ok){
        uint64_t cur=[d->ifc frameNumberWithTime:nil];
        if(cur+1>=f){
            uint64_t start=cur+IH_LEAD;
            x.gap+=start-f; d->st.late_resubmits[ep]++; d->st.unread_frames[ep]+=start-f;
            f=start; e=nil;
            ok=[d->pipe[ep] enqueueIORequestWithData:x.buf transactionList:x.tl transactionListCount:(NSUInteger)n
                                     firstFrameNumber:f options:IOUSBHostIsochronousTransferOptionsNone error:&e completionHandler:done];
        }
    }
    if(!ok){ dispatch_group_leave(d->inflight); ih_fatal_(d,2,e?(int)e.code:0,ep,x.seq); return; }
    d->st.submits[ep]++; d->live[ep]++;
    d->next[ep]=f+(uint64_t)(n/IH_PER_FRAME);
}

int ih_open(ih_dev **out, uint32_t mode_word, uint32_t r4, uint32_t latch, char *err, size_t errn){ @autoreleasepool {
    NSMutableDictionary *m=(__bridge_transfer NSMutableDictionary*)IOServiceMatching(kIOUSBHostDeviceClassName);
    m[@kUSBHostMatchingPropertyVendorID]=@(IH_VID); m[@kUSBHostMatchingPropertyProductID]=@(IH_PID);
    io_service_t ds=IOServiceGetMatchingService(kIOMainPortDefault,(__bridge_retained CFDictionaryRef)m);
    if(!ds){ if(err&&errn) snprintf(err,errn,"no Shuttle on the USB bus"); return CC_ERR_NODEVICE; }
    IHDev *d=[IHDev new];
    d->q=dispatch_queue_create("capture_core.iousbhost",dispatch_queue_attr_make_with_qos_class(DISPATCH_QUEUE_SERIAL,QOS_CLASS_USER_INTERACTIVE,0));
    d->inflight=dispatch_group_create(); d->all=[NSMutableArray new];
    { mach_timebase_info_data_t tb; mach_timebase_info(&tb); d->abs_ns=tb.denom?(double)tb.numer/(double)tb.denom:1.0; }
    NSError *e=nil;
    __weak IHDev *wd=d;
    d->dev=[[IOUSBHostDevice alloc] initWithIOService:ds options:IOUSBHostObjectInitOptionsNone queue:d->q error:&e
                                      interestHandler:^(IOUSBHostObject *o, uint32_t type, void *arg){ (void)o; (void)arg;
        IHDev *sd=wd; if(sd && type==kIOMessageServiceIsTerminated) ih_fatal_(sd,1,0,0,0); }];
    IOObjectRelease(ds);
    if(!d->dev){ ih_err(err,errn,"open the Shuttle (IOUSBHostDevice)",e); return CC_ERR_USB; }
    if(!d->dev.configurationDescriptor && ![d->dev configureWithValue:1 matchInterfaces:NO error:&e]){
        ih_err(err,errn,"configure",e); [d->dev destroy]; return CC_ERR_USB; }
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
    if(!is){ if(err&&errn) snprintf(err,errn,"the Shuttle has no interface 0"); [d->dev destroy]; return CC_ERR_USB; }
    d->ifc=[[IOUSBHostInterface alloc] initWithIOService:is options:IOUSBHostObjectInitOptionsNone queue:d->q error:&e interestHandler:nil];
    IOObjectRelease(is);
    if(!d->ifc){ ih_err(err,errn,"open interface 0",e); [d->dev destroy]; return CC_ERR_USB; }
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
    if(!ok){ ih_err(err,errn,"start sequence (alt settings / mode word)",e); [d->ifc destroy]; [d->dev destroy]; return CC_ERR_USB; }
    d->pipe[0]=[d->ifc copyPipeWithAddress:CC_EP_VIDEO error:&e];
    d->pipe[1]=[d->ifc copyPipeWithAddress:CC_EP_AUDIO error:&e];
    if(!d->pipe[0] || !d->pipe[1]){ ih_err(err,errn,"isochronous pipes",e); [d->ifc destroy]; [d->dev destroy]; return CC_ERR_USB; }
    for(int ep=0;ep<2;ep++){
        const IOUSBHostIOSourceDescriptors *pd=d->pipe[ep].descriptors;
        if(!pd || pd->descriptor.bInterval!=1){
            if(err&&errn) snprintf(err,errn,"endpoint 0x%02x has bInterval %d, not 1: frame accounting would be wrong",
                                   ep?CC_EP_AUDIO:CC_EP_VIDEO,pd?pd->descriptor.bInterval:-1);
            [d->ifc selectAlternateSetting:0 error:nil]; [d->ifc destroy]; [d->dev destroy]; return CC_ERR_USB;
        }
    }
    *out=(ih_dev*)(__bridge_retained void*)d;
    return CC_OK;
}}

int ih_start(ih_dev *dv, const ih_callbacks *cb, int xfers, int v_npk, int v_pkt, int a_npk, int a_pkt, char *err, size_t errn){ @autoreleasepool {
    IHDev *d=D(dv);
    if(xfers<1 || xfers>IH_MAXX || v_npk%IH_PER_FRAME || a_npk%IH_PER_FRAME || !cb->on_packet){
        if(err&&errn) snprintf(err,errn,"bad transfer geometry"); return CC_ERR_ARGS; }
    __block int rc=CC_OK;
    dispatch_sync(d->q,^{
        d->cb=*cb; d->npk[0]=v_npk; d->npk[1]=a_npk; d->pkt[0]=v_pkt; d->pkt[1]=a_pkt;
        for(int ep=0;ep<2 && rc==CC_OK;ep++) for(int k=0;k<xfers && rc==CC_OK;k++){
            /* each endpoint starts IH_LEAD frames after its own first enqueue: one shared start was already
             * 6 frames past for audio after video's 32 enqueues (macOS took the transfer and failed those packets
             * with kIOReturnIsoTooOld, measured 2026-10-17) */
            if(!k) d->next[ep]=[d->ifc frameNumberWithTime:nil]+IH_LEAD;
            NSError *e=nil; IHXfer *x=[IHXfer new]; x.ep=ep; x.seq=d->seqc[ep]++;
            x.buf=[d->ifc ioDataWithCapacity:(NSUInteger)(d->npk[ep]*d->pkt[ep]) error:&e];
            x.tl=calloc((size_t)d->npk[ep],sizeof(IOUSBHostIsochronousTransaction));
            if(!x.buf || !x.tl){ ih_err(err,errn,"I/O buffers",e); rc=CC_ERR_NOMEM; break; }
            [d->all addObject:x]; d->st.transfers++;
            ih_enqueue_(d,x);
            if(d->fatal_sent){ if(err&&errn) snprintf(err,errn,"the first transfers could not be queued"); rc=CC_ERR_USB; }
        }
        if(rc==CC_OK){
            d->tick=dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER,0,0,d->q);
            dispatch_source_set_timer(d->tick,dispatch_time(DISPATCH_TIME_NOW,NSEC_PER_SEC),NSEC_PER_SEC,10*NSEC_PER_MSEC);
            __weak IHDev *wd=d;
            dispatch_source_set_event_handler(d->tick,^{ IHDev *sd=wd;
                if(sd && !sd->stopping && !sd->detached && sd->cb.on_tick) sd->cb.on_tick(sd->cb.ctx); });
            dispatch_resume(d->tick);
        }
    });
    return rc;
}}

void ih_stop(ih_dev *dv, ih_stats *st){ @autoreleasepool {
    IHDev *d=D(dv);
    dispatch_sync(d->q,^{ d->stopping=YES; d->st.fleet[0]=d->live[0]; d->st.fleet[1]=d->live[1]; if(d->tick) dispatch_source_cancel(d->tick); });
    for(int ep=0;ep<2;ep++) if(d->pipe[ep]) [d->pipe[ep] abortWithOption:IOUSBHostAbortOptionAsynchronous error:nil];
    long left=dispatch_group_wait(d->inflight,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC));
    /* after this, no callback of ours is running, and none will call the caller again */
    dispatch_sync(d->q,^{ if(left){ d->detached=YES; d->st.incomplete=1; } });
    if(left) fprintf(stderr,"capture_iousbhost: transfers still in flight 5 s after the abort; their callbacks are cut off\n");
    [d->ifc selectAlternateSetting:0 error:nil];
    if(st) *st=d->st;
}}

void ih_close(ih_dev *dv){ @autoreleasepool {
    if(!dv) return;
    IHDev *d=(__bridge_transfer IHDev*)(void*)dv;
    [d->ifc destroy]; [d->dev destroy];
    d=nil;
}}
