/* ih_fake_iousbhost.m -- see ih_fake_iokit.h. Fakes of the IOUSBHost calls capture_iousbhost.m makes, keeping the
 * behaviour measured on the Shuttle (README "USB stacks"): a transfer lying wholly in the past is refused with
 * kIOReturnIsoTooOld; one partly in the past is accepted with its past packets failed that way; a transfer completes
 * once its last frame has gone by; an abort completes what is pending with kIOReturnAborted; termination notices come
 * on a queue of their own. Payload: each packet starts with its microframe number (uint64). */
#import <Foundation/Foundation.h>
#import <IOUSBHost/IOUSBHost.h>
#include <mach/mach_time.h>
#include "ih_fake_iokit.h"

#pragma clang diagnostic ignored "-Wincomplete-implementation"
#pragma clang diagnostic ignored "-Wobjc-designated-initializers"
#pragma clang diagnostic ignored "-Wprotocol"

ih_fake_controls ih_fake;
_Atomic long ih_fake_xfer_deallocs;
static uint64_t t0_abs; static double abs_ns;
static void clock_init_(void){ static dispatch_once_t o; dispatch_once(&o,^{ mach_timebase_info_data_t tb; mach_timebase_info(&tb);
    abs_ns=(double)tb.numer/tb.denom; t0_abs=mach_absolute_time(); }); }
uint64_t ih_fake_frame_now(void){ clock_init_(); return 1000+(uint64_t)((mach_absolute_time()-t0_abs)*abs_ns/1e6); }
static uint64_t abs_at_frame_(uint64_t f){ clock_init_(); return t0_abs+(uint64_t)((double)(f-1000)*1e6/abs_ns); }

static IOUSBHostInterestHandler g_interest; static IOUSBHostObject *g_dev_obj;
static dispatch_queue_t interest_q_(void){ static dispatch_queue_t q; static dispatch_once_t o;
    dispatch_once(&o,^{ q=dispatch_queue_create("ih_fake.interest",DISPATCH_QUEUE_SERIAL); }); return q; }
void ih_fake_terminate(void){
    atomic_store(&ih_fake.gone,1);                  /* as an unplug: requeues now fail, the notice follows */
    IOUSBHostInterestHandler h=g_interest; IOUSBHostObject *o=g_dev_obj;
    if(h) dispatch_async(interest_q_(),^{ h(o,kIOMessageServiceIsTerminated,NULL); });
}

io_service_t ih_fake_get_matching(mach_port_t port, CFDictionaryRef m){ (void)port; if(m) CFRelease(m); return atomic_load(&ih_fake.absent)?0:101; }
kern_return_t ih_fake_release(io_object_t o){ (void)o; return KERN_SUCCESS; }
static _Atomic int iter_left;
kern_return_t ih_fake_children(io_registry_entry_t e, const io_name_t plane, io_iterator_t *it){ (void)e; (void)plane; atomic_store(&iter_left,1); *it=102; return KERN_SUCCESS; }
io_object_t ih_fake_next(io_iterator_t it){ (void)it; return atomic_exchange(&iter_left,0)?103:0; }
boolean_t ih_fake_conforms(io_object_t o, const io_name_t cls){ (void)cls; return o==103; }
CFTypeRef ih_fake_property(io_registry_entry_t e, CFStringRef key, CFAllocatorRef a, IOOptionBits op){ (void)e; (void)key; (void)a; (void)op;
    int z=0; return CFNumberCreate(NULL,kCFNumberIntType,&z); }

@implementation IOUSBHostObject {
@public
    dispatch_queue_t _q; io_service_t _svc;
}
- (instancetype)initWithIOService:(io_service_t)ioService options:(IOUSBHostObjectInitOptions)options queue:(dispatch_queue_t)queue
                            error:(NSError**)error interestHandler:(IOUSBHostInterestHandler)interestHandler {
    (void)options; (void)error;
    if((self=[super init])){ _q=queue; _svc=ioService;
        if(interestHandler){ g_interest=interestHandler; g_dev_obj=self; } }
    return self;
}
- (io_service_t)ioService { return _svc; }
- (dispatch_queue_t)queue { return _q; }
- (void)destroy { if(g_dev_obj==self){ g_interest=nil; g_dev_obj=nil; } }
- (BOOL)sendDeviceRequest:(IOUSBDeviceRequest)r data:(NSMutableData*)data bytesTransferred:(NSUInteger*)n
        completionTimeout:(NSTimeInterval)t error:(NSError**)error { (void)r; (void)t; (void)error; if(n) *n=data.length; return YES; }
- (uint64_t)frameNumberWithTime:(IOUSBHostTime*)time { if(time) *time=mach_absolute_time(); return ih_fake_frame_now(); }
- (NSMutableData*)ioDataWithCapacity:(NSUInteger)capacity error:(NSError**)error { (void)error; return [NSMutableData dataWithLength:capacity]; }
@end

static const IOUSBConfigurationDescriptor fake_config={.bLength=9,.bDescriptorType=2,.bConfigurationValue=1};
@implementation IOUSBHostDevice
- (const IOUSBConfigurationDescriptor*)configurationDescriptor { return &fake_config; }
- (BOOL)configureWithValue:(NSUInteger)value matchInterfaces:(BOOL)m error:(NSError**)error { (void)value; (void)m; (void)error; return YES; }
@end

@interface IOUSBHostIOSource (Fake)
- (instancetype)initFakeBase;
@end
@implementation IOUSBHostIOSource
- (instancetype)initFakeBase { return [super init]; }
@end

@interface IHFakePending : NSObject {
@public
    _Atomic int done;
}
@property (nonatomic, copy) IOUSBHostIsochronousTransactionCompletionHandler h;
@property (nonatomic) IOUSBHostIsochronousTransaction *tl;
@end
@implementation IHFakePending
@end

@implementation IOUSBHostPipe {
    IOUSBHostIOSourceDescriptors _d; int _ep; dispatch_queue_t _q; NSMutableArray<IHFakePending*> *_pending; NSLock *_lock;
}
- (instancetype)initFake:(int)ep queue:(dispatch_queue_t)q {
    if((self=[super initFakeBase])){ _ep=ep; _q=q; _pending=[NSMutableArray new]; _lock=[NSLock new];
        _d.descriptor.bInterval=1; _d.descriptor.bEndpointAddress=ep?0x84:0x83; }
    return self;
}
- (const IOUSBHostIOSourceDescriptors*)descriptors { return &_d; }
static NSError *io_err_(IOReturn r){ return [NSError errorWithDomain:@"IOKit" code:r userInfo:nil]; }
- (BOOL)enqueueIORequestWithData:(NSMutableData*)data transactionList:(IOUSBHostIsochronousTransaction*)tl
            transactionListCount:(NSUInteger)n firstFrameNumber:(uint64_t)f options:(IOUSBHostIsochronousTransferOptions)o
                           error:(NSError**)error completionHandler:(IOUSBHostIsochronousTransactionCompletionHandler)h {
    (void)o;
    atomic_fetch_add(&ih_fake.enqueues[_ep],1);
    [_lock lock];
    for(IHFakePending *q in _pending) if(q.tl==tl){ fprintf(stderr,"ih_fake: a transaction list queued twice\n"); abort(); }
    [_lock unlock];
    if(atomic_load(&ih_fake.gone)){ if(error) *error=io_err_(kIOReturnNoDevice); return NO; }
    if(atomic_load(&ih_fake.refuse_all[_ep]) || (atomic_load(&ih_fake.refuse[_ep])>0 && atomic_fetch_sub(&ih_fake.refuse[_ep],1)>0)){
        atomic_fetch_add(&ih_fake.refusals[_ep],1); if(error) *error=io_err_(kIOReturnNoResources); return NO; }
    uint64_t cur=ih_fake_frame_now(), frames=n/8;
    if(f+frames<=cur){ if(error) *error=io_err_(kIOReturnIsoTooOld); return NO; }   /* wholly in the past */
    uint8_t *b=data.mutableBytes;
    for(NSUInteger i=0;i<n;i++){
        uint64_t uf=(f+i/8)*8+i%8;
        if(f+i/8<=cur+1){ tl[i].status=kIOReturnIsoTooOld;   /* as measured: the current frame and the next */ tl[i].completeCount=0; atomic_fetch_add(&ih_fake.too_old_packets[_ep],1); }
        else { tl[i].status=kIOReturnSuccess; tl[i].completeCount=tl[i].requestCount<32?tl[i].requestCount:32;
               memcpy(b+tl[i].offset,&uf,8); }
        tl[i].timeStamp=abs_at_frame_(f+i/8+1);
    }
    IHFakePending *p=[IHFakePending new]; p.h=h; p.tl=tl;
    atomic_store(&ih_fake.queue_end[_ep],f+frames);
    [_lock lock]; [_pending addObject:p]; [_lock unlock];
    uint64_t due=abs_at_frame_(f+frames)+100000/abs_ns, now=mach_absolute_time();
    int64_t wait_ns=due>now?(int64_t)((due-now)*abs_ns):0;
    __weak IOUSBHostPipe *wp=self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,wait_ns),_q,^{
        if(atomic_exchange(&p->done,1)) return;
        IOUSBHostPipe *sp=wp; if(sp){ [sp->_lock lock]; [sp->_pending removeObject:p]; [sp->_lock unlock]; }
        int ep=sp?sp->_ep:0;
        if(atomic_fetch_add(&ih_fake.completions[ep],1)+1==atomic_load(&ih_fake.late_at[ep])){
            uint64_t target=atomic_load(&ih_fake.queue_end[ep])+(uint64_t)atomic_load(&ih_fake.late_k[ep]);
            while(ih_fake_frame_now()<target) usleep(100);
        }
        p.h(kIOReturnSuccess,p.tl);
    });
    return YES;
}
- (BOOL)abortWithOption:(IOUSBHostAbortOption)option error:(NSError**)error { (void)option; (void)error;
    [_lock lock]; NSArray *all=[_pending copy]; [_pending removeAllObjects]; [_lock unlock];
    int64_t delay=(int64_t)atomic_load(&ih_fake.abort_delay_ms)*NSEC_PER_MSEC;
    for(IHFakePending *p in all) dispatch_after(dispatch_time(DISPATCH_TIME_NOW,delay),_q,^{
        if(atomic_exchange(&p->done,1)) return;
        p.h(kIOReturnAborted,p.tl); });
    return YES;
}
@end

@implementation IOUSBHostInterface {
    IOUSBHostPipe *_pipes[2];
}
- (BOOL)selectAlternateSetting:(NSUInteger)a error:(NSError**)error { (void)a; (void)error; return YES; }
- (IOUSBHostPipe*)copyPipeWithAddress:(NSUInteger)address error:(NSError**)error { (void)error;
    int ep=address==0x84?1:0;
    if(!_pipes[ep]) _pipes[ep]=[[IOUSBHostPipe alloc] initFake:ep queue:((IOUSBHostObject*)self)->_q];
    return _pipes[ep];
}
@end
