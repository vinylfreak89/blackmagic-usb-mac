/* usb_close_notice_probe: on a real USB device, exercise the two kernel behaviours the OBS plugin's reconnect waits on.
 * (1) the error IOUSBHost returns when another process holds the device open exclusively, and (2) whether a
 * general-interest watcher on the device receives kIOMessageServiceWasClosed when that process lets go.
 *
 *   usb_close_notice_probe <vid> <pid>        e.g. 0x2109 0x0101 (a USB-C hub's Billboard device: no driver, no data)
 *
 * It spawns itself as the holder (opens the device, holds it 500 ms, destroys the handle, then lives 1 s more so a
 * close notice is not confused with process exit), then as the waiter: watch, try to open while held (must fail),
 * wait for the close notice, open (must succeed). Use only a device nothing else uses: the open is exclusive.
 * Build: clang -fobjc-arc -framework Foundation -framework IOKit -framework IOUSBHost usb_close_notice_probe.m */
#import <Foundation/Foundation.h>
#import <IOUSBHost/IOUSBHost.h>
#include <IOKit/IOMessage.h>
#include <spawn.h>
#include <stdatomic.h>
#include <stdio.h>
#include <unistd.h>

extern char **environ;
static uint64_t ms_(void){ return clock_gettime_nsec_np(CLOCK_UPTIME_RAW)/1000000; }
static io_service_t find_(int vid, int pid){
    NSMutableDictionary *m=(__bridge_transfer NSMutableDictionary*)IOServiceMatching(kIOUSBHostDeviceClassName);
    m[@kUSBHostMatchingPropertyVendorID]=@(vid); m[@kUSBHostMatchingPropertyProductID]=@(pid);
    return IOServiceGetMatchingService(kIOMainPortDefault,(__bridge_retained CFDictionaryRef)m);
}
static IOUSBHostDevice *open_(io_service_t s, NSError **e){
    return [[IOUSBHostDevice alloc] initWithIOService:s options:IOUSBHostObjectInitOptionsNone
                                                queue:dispatch_queue_create("probe",DISPATCH_QUEUE_SERIAL) error:e interestHandler:nil];
}
static dispatch_semaphore_t closed_sem; static _Atomic uint64_t closed_ms;
static void interest_(void *ref, io_service_t s, natural_t type, void *arg){ (void)ref; (void)s; (void)arg;
    printf("waiter: %llu ms: message 0x%08x%s\n",(unsigned long long)ms_(),type,
           type==kIOMessageServiceWasClosed?" (kIOMessageServiceWasClosed)":type==kIOMessageServiceIsTerminated?" (terminated)":"");
    fflush(stdout);
    if(type==kIOMessageServiceWasClosed){ uint64_t z=0; atomic_compare_exchange_strong(&closed_ms,&z,ms_()); dispatch_semaphore_signal(closed_sem); }
}
int main(int argc, char **argv){ @autoreleasepool {
    if(argc>=4 && !strcmp(argv[1],"hold")){
        int vid=(int)strtol(argv[2],NULL,0), pid=(int)strtol(argv[3],NULL,0);
        io_service_t s=find_(vid,pid); NSError *e=nil;
        IOUSBHostDevice *d=s?open_(s,&e):nil;
        if(!d){ fprintf(stderr,"holder: open failed: %s\n",e.localizedDescription.UTF8String); printf("FAILED\n"); return 1; }
        printf("HELD\n"); fflush(stdout);
        usleep(500000);
        uint64_t t=ms_(); [d destroy]; d=nil;
        fprintf(stderr,"holder: %llu ms: destroyed its handle\n",(unsigned long long)t);
        usleep(1000000);
        fprintf(stderr,"holder: %llu ms: exiting\n",(unsigned long long)ms_());
        return 0;
    }
    if(argc<3){ fprintf(stderr,"usage: %s <vid> <pid>\n",argv[0]); return 2; }
    int vid=(int)strtol(argv[1],NULL,0), pid=(int)strtol(argv[2],NULL,0);
    io_service_t s=find_(vid,pid);
    if(!s){ fprintf(stderr,"no device %04x:%04x\n",vid,pid); return 2; }
    closed_sem=dispatch_semaphore_create(0);
    IONotificationPortRef port=IONotificationPortCreate(kIOMainPortDefault);
    IONotificationPortSetDispatchQueue(port,dispatch_queue_create("probe.interest",DISPATCH_QUEUE_SERIAL));
    io_object_t note=0;
    kern_return_t kr=IOServiceAddInterestNotification(port,s,kIOGeneralInterest,interest_,NULL,&note);
    if(kr){ fprintf(stderr,"IOServiceAddInterestNotification: 0x%x\n",kr); return 1; }
    int fd[2]; pipe(fd);
    posix_spawn_file_actions_t fa; posix_spawn_file_actions_init(&fa); posix_spawn_file_actions_adddup2(&fa,fd[1],1);
    char *hargv[]={argv[0],"hold",argv[1],argv[2],NULL}; pid_t hp;
    if(posix_spawn(&hp,argv[0],&fa,NULL,hargv,environ)){ perror("posix_spawn"); return 1; }
    close(fd[1]);
    char line[32]={0}; ssize_t n=read(fd[0],line,sizeof line-1);
    if(n<=0 || strncmp(line,"HELD",4)){ fprintf(stderr,"holder did not hold the device: %s\n",line); return 1; }
    NSError *e=nil; IOUSBHostDevice *d=open_(s,&e);
    int fails=0;
    if(d){ printf("FAIL: opened while another process held it\n"); fails++; [d destroy]; d=nil; }
    else printf("waiter: %llu ms: open while held refused: domain %s code 0x%08lx (%s); reason: %s\n",(unsigned long long)ms_(),
                e.domain.UTF8String,(long)e.code,e.code==kIOReturnExclusiveAccess?"kIOReturnExclusiveAccess":"not kIOReturnExclusiveAccess",
                e.localizedFailureReason?e.localizedFailureReason.UTF8String:"(none)");
    BOOL got=dispatch_semaphore_wait(closed_sem,dispatch_time(DISPATCH_TIME_NOW,5*NSEC_PER_SEC))==0;
    if(!got){ printf("FAIL: no kIOMessageServiceWasClosed within 5 s of the holder's release\n"); fails++; }
    e=nil; d=open_(s,&e);
    if(!d){ printf("FAIL: open after the close notice: %s\n",e.localizedDescription.UTF8String); fails++; }
    else { printf("waiter: %llu ms: opened after the close notice\n",(unsigned long long)ms_()); [d destroy]; d=nil; }
    int st=0; waitpid(hp,&st,0);
    usleep(200000);   /* our own close's notice, if one comes, prints above */
    IOObjectRelease(note); IONotificationPortDestroy(port); IOObjectRelease(s);
    printf("%s\n",fails?"PROBE FAILED":"PROBE OK");
    return fails?1:0;
}}
