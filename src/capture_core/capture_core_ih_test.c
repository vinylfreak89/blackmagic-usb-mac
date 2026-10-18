/* capture_core's IOUSBHost glue (ih_main, ihc_*) against capture_iousbhost_mock.c, under TSan (make test-iousbhost).
 * The real backend's own behaviour is measured on hardware (README "USB stacks"); this decides the capture_core side:
 * unread-frame records land just before the transfer they precede, past-due packets are counted, a refused start
 * hands nothing over, a callback that calls cc_stop from the queue is refused, and the ring has one producer. */
#include "capture_core.h"
#include "capture_iousbhost_mock.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int fails;
#define CHECK(cond,...) do{ if(!(cond)){ fails++; fprintf(stderr,"FAIL: " __VA_ARGS__); fprintf(stderr,"\n"); } }while(0)

enum { EV_DATA, EV_LOSS };
typedef struct { int kind; uint8_t ep; uint32_t seq, pkt, packets; int loss_kind; int pay_ep; uint32_t pay_seq, pay_pkt; } ev;
#define MAXEV 40000
static ev evs[MAXEV]; static int nev;
static pthread_mutex_t m=PTHREAD_MUTEX_INITIALIZER; static pthread_cond_t c=PTHREAD_COND_INITIALIZER;
static int ended, data_n, balance_warned, stop_from_queue=99, exact_lines, approx_lines;
static cc_session *g_s;

static void on_packet(void *ctx, const cc_packet *p){ (void)ctx;
    if(nev<MAXEV){ ev e={EV_DATA,p->endpoint,p->submit_seq,p->pkt_index,0,0,-1,0,0};
        if(p->actual_len>=12){ memcpy(&e.pay_ep,p->data,4); memcpy(&e.pay_seq,p->data+4,4); memcpy(&e.pay_pkt,p->data+8,4); }
        evs[nev++]=e; }
    pthread_mutex_lock(&m); data_n++; pthread_cond_broadcast(&c); pthread_mutex_unlock(&m);
}
static void on_loss_ex(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){ (void)ctx; (void)by;
    if(nev<MAXEV) evs[nev++]=(ev){EV_LOSS,ep,seq,0,pk,kind,-1,0,0};
}
static void on_end(void *ctx, enum cc_end r){ (void)ctx; (void)r; pthread_mutex_lock(&m); ended++; pthread_cond_broadcast(&c); pthread_mutex_unlock(&m); }
static void diag(void *ctx, const char *line){ (void)ctx;
    if(strstr(line,"NOT balance")) balance_warned++;
    if(strstr(line,"HOST LOSS: ~")) approx_lines++; else if(strstr(line,"HOST LOSS:")) exact_lines++;
    if(strstr(line,"failed as too old")) stop_from_queue=cc_stop(g_s);   /* on the completion queue: must be refused */
}
static int wait_data(int n){
    struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts); ts.tv_sec+=20;
    pthread_mutex_lock(&m); int rc=0;
    while(data_n<n && rc==0) rc=pthread_cond_timedwait(&c,&m,&ts);
    int got=data_n; pthread_mutex_unlock(&m); return got>=n;
}
static cc_config cfg_(void){ cc_config cfg; memset(&cfg,0,sizeof cfg); cfg.usb_backend=CC_USB_IOUSBHOST; cfg.ring_mb=64; cfg.diag_log=diag; return cfg; }

int main(void){
    cc_callbacks cb; memset(&cb,0,sizeof cb); cb.on_packet=on_packet; cb.on_loss_ex=on_loss_ex; cb.on_end=on_end;
    const int T=40, NPK=128;

    /* 1. a normal session with two gaps and one past-due run */
    ih_mock=(ih_mock_config){.transfers=T,.gap_at_video=10,.gap_at_audio=20,.gap_frames=25,.too_old_at_video=30,.too_old=16};
    cc_config cfg=cfg_();
    CHECK(cc_open(&g_s,&cfg,&cb)==CC_OK,"open");
    CHECK(cc_start(g_s)==CC_OK,"start");
    CHECK(wait_data(2*T*NPK),"only %d of %d packets delivered",data_n,2*T*NPK);
    CHECK(cc_stop(g_s)==CC_OK,"stop");
    cc_stats st; cc_get_stats(g_s,&st);
    CHECK(ih_mock.went,"ih_go never called");
    CHECK(stop_from_queue==CC_ERR_STATE,"cc_stop from the completion queue returned %d, not refused",stop_from_queue);
    CHECK(st.unscheduled_packets[0]==25*8+16 && st.unscheduled_packets[1]==25*8,"unscheduled packets %llu / %llu",
          (unsigned long long)st.unscheduled_packets[0],(unsigned long long)st.unscheduled_packets[1]);
    CHECK(st.unscheduled_events==3 && st.unscheduled_late==0,"unscheduled events %llu late %llu",(unsigned long long)st.unscheduled_events,(unsigned long long)st.unscheduled_late);
    CHECK(st.iso_errors==16,"iso errors %ld",st.iso_errors);
    CHECK(st.transfers_allocated==st.transfers_freed && st.transfers_allocated==2*CC_XFERS_PER_ENDPOINT,"transfers %ld/%ld",st.transfers_allocated,st.transfers_freed);
    CHECK(!balance_warned,"unread-frame accounting warned");
    /* order and placement, per endpoint: data in (seq, pkt) order; each loss directly before its transfer's first packet */
    for(int ep=0;ep<2;ep++){
        uint8_t E=ep?CC_EP_AUDIO:CC_EP_VIDEO; uint32_t want_seq=0, want_pkt=0; int losses=0, pending=-1;
        for(int i=0;i<nev;i++){
            if(evs[i].ep!=E) continue;
            if(evs[i].kind==EV_LOSS){
                losses++; pending=(int)evs[i].seq;
                CHECK(evs[i].loss_kind==CC_LOSS_UNSCHEDULED && evs[i].packets==25*8,"ep %02x loss kind %d packets %u",E,evs[i].loss_kind,evs[i].packets);
                CHECK(evs[i].seq==(uint32_t)(ep?20:10),"ep %02x loss names seq %u",E,evs[i].seq);
                CHECK(want_pkt==0,"ep %02x loss inside transfer %u",E,want_seq);
                continue;
            }
            CHECK(evs[i].seq==want_seq && evs[i].pkt==want_pkt,"ep %02x packet (%u,%u), expected (%u,%u)",E,evs[i].seq,evs[i].pkt,want_seq,want_pkt);
            if(pending>=0){ CHECK((uint32_t)pending==evs[i].seq && evs[i].pkt==0,"ep %02x loss for seq %d not followed by its data",E,pending); pending=-1; }
            if(evs[i].pay_ep>=0) CHECK(evs[i].pay_ep==ep && evs[i].pay_seq==evs[i].seq && evs[i].pay_pkt==evs[i].pkt,"ep %02x payload names (%d,%u,%u)",E,evs[i].pay_ep,evs[i].pay_seq,evs[i].pay_pkt);
            if(++want_pkt==(uint32_t)NPK){ want_pkt=0; want_seq++; }
        }
        CHECK(losses==1 && want_seq==(uint32_t)T,"ep %02x: %d losses, %u transfers",E,losses,want_seq);
    }
    cc_close(g_s); g_s=NULL;
    CHECK(ended==1,"on_end fired %d times",ended);
    printf("  IOUSBHost glue: %d records in order, unread frames placed before their transfers, past-due packets counted, callback stop refused\n",nev);

    /* 2. a refused start: no data, no on_end, cc_start fails, ih_go never called */
    nev=0; data_n=0; ended=0;
    ih_mock=(ih_mock_config){.transfers=T,.gap_at_video=-1,.gap_at_audio=-1,.too_old_at_video=-1,.fail_start=(int)0xE00002C0};
    cfg=cfg_();
    CHECK(cc_open(&g_s,&cfg,&cb)==CC_OK,"open (refused start)");
    CHECK(cc_start(g_s)!=CC_OK,"a refused first enqueue still started");
    CHECK(!ih_mock.went,"ih_go called after a refused start");
    CHECK(data_n==0,"%d packets handed over from a failed start",data_n);
    cc_close(g_s); g_s=NULL;
    CHECK(ended==0,"on_end fired for a session that never started");
    printf("  refused start: nothing handed over, no on_end\n");

    /* 4. replay wording: a file's SESSION note says which USB stack made it, so HOST LOSS is worded exact or "~";
     *    the stack field is read where it stands, never from the recording's name (the user's text) */
    { struct { const char *note; int exact; } nc[]={
        {"shuttle-source tee v1 usb=iousbhost input=svideo setup=on mode=0x3c000000 part=1 recording=a.mov",1},
        {"shuttle-source tee v1 usb=libusb input=svideo setup=on mode=0x3c000000 part=1 recording=a.mov",0},
        {"shuttle-source tee v1 usb=libusb input=svideo setup=on mode=0x3c000000 part=1 recording=x usb=iousbhost y.mov",0},
        {"shuttle-capture v1 input=svideo mode_word=0x3c000000 ring_mb=256 fleet=32+32 control_loss=continue usb=iousbhost",1}};
      for(unsigned i=0;i<sizeof nc/sizeof nc[0];i++){
        char path[]="/tmp/cc_ih_note_XXXXXX"; int fd=mkstemp(path); CHECK(fd>=0,"temp file");
        struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } h={0x31504143u,3,0,0,0,0,0,(uint32_t)strlen(nc[i].note)};
        CHECK(write(fd,&h,sizeof h)==(ssize_t)sizeof h && write(fd,nc[i].note,h.al)==(ssize_t)h.al,"write note");
        struct { uint32_t magic; uint8_t type,ep; uint16_t pi; uint32_t seq,st,req,al; } l={0x31504143u,1,CC_EP_VIDEO,CC_PI_UNSCHEDULED,7,0,64,0};
        CHECK(write(fd,&l,sizeof l)==(ssize_t)sizeof l,"write loss"); close(fd);
        exact_lines=approx_lines=0; pthread_mutex_lock(&m); ended=0; pthread_mutex_unlock(&m);
        cc_config rc; memset(&rc,0,sizeof rc); rc.replay_path=path; rc.ring_mb=16; rc.diag_log=diag;
        cc_session *r=NULL; CHECK(cc_open(&r,&rc,&cb)==CC_OK && cc_start(r)==CC_OK,"replay start");
        for(int k=0;k<200;k++){ pthread_mutex_lock(&m); int e=ended; pthread_mutex_unlock(&m); if(e) break; usleep(10000); }
        cc_stop(r); cc_close(r); unlink(path);
        CHECK(nc[i].exact?(exact_lines==1&&approx_lines==0):(exact_lines==0&&approx_lines==1),"note %u: %d exact / %d approximate HOST LOSS lines",i,exact_lines,approx_lines);
      }
      printf("  replay wording: the USB stack is read from the note's own field, not the recording's name\n"); }

    /* 3. no device: cc_open fails without a session */
    ih_mock=(ih_mock_config){.fail_open=1};
    cfg=cfg_(); cc_session *x=NULL;
    CHECK(cc_open(&x,&cfg,&cb)==CC_ERR_NODEVICE && !x,"open without a device");

    if(fails){ printf("FAILURES: %d\n",fails); return 1; }
    printf("ALL TESTS PASSED\n"); return 0;
}
