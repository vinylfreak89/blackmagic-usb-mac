// capture_tagged_bench — tagged capture core bench. Every iso packet lands in the output file with a
// 24-byte provenance record, so scheduled-slot accounting is complete: a missing USB frame
// is PROVABLE from the tag stream, never inferred from content. Ring overflow becomes an
// explicit in-stream HostLoss record instead of silent loss (design doc §8 requirement 7).
//
// Threads: single libusb event thread (main; the only producer) -> SPSC byte ring
// (atomic head/tail, no lock on the data path) -> writer thread (the only consumer).
// The condvar is used solely for sleep/wake; a 100 ms timedwait is a liveness backstop.
//
// Usage: ./capture_tagged_bench <component|svideo|composite> <seconds> <outfile> [ringMB=256]
//
// Output format: sequence of records, each 24-byte header + payload:
//   { u32 magic 'CAP1'; u8 type; u8 endpoint; u16 pkt_index;
//     u32 submit_seq; u32 status; u32 req_len; u32 actual_len; }
//   type 0 DATA     — one iso packet; payload = actual_len bytes (0-length packets ARE
//                     logged: header only — that is the scheduled-slot proof)
//   type 1 HostLoss — ring overflow; req_len = lost packet count, actual_len = lost bytes
//   type 2 TransferError  — transfer-level failure/cancellation; status = libusb status
//   type 3 SESSION  — file-start parameter record; payload = text
#include <libusb.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>
#include <inttypes.h>

#define VID 0x1EDB
#define PID 0xBD3B
#define VIDEO_EP 0x83
#define AUDIO_EP 0x84
#define V_PKT 15360
#define V_NPK 128            // ~128 ms of video schedule queued per transfer (cf28b89 fix)
#define A_PKT 0xc0
#define A_NPK 80
#define XFERS 8
#define NXF (XFERS*2)

#define REC_MAGIC 0x31504143u   // "CAP1" little-endian
enum { REC_DATA=0, REC_HOSTLOSS=1, REC_XFERERR=2, REC_SESSION=3 };
typedef struct {
    uint32_t magic; uint8_t type, endpoint; uint16_t pkt_index;
    uint32_t submit_seq, status, req_len, actual_len;
} rec_hdr;
_Static_assert(sizeof(rec_hdr)==24, "rec_hdr must be 24 bytes");

static uint8_t *ring; static size_t RING;
static _Atomic size_t r_head=0, r_tail=0;   // monotonic byte counters; index = ctr % RING
static size_t r_max=0;                       // producer-side high-water stat
static pthread_mutex_t sig_m=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  sig_c=PTHREAD_COND_INITIALIZER;
static FILE *g_out;
static _Atomic int g_stop=0, g_done=0;
static _Atomic long inflight=0;

// Producer-thread-only state (all callbacks run on the single libusb event thread).
static long v_bytes=0, a_bytes=0, iso_err=0, xfer_err=0, zero_pkts=0, short_pkts=0, hostloss_recs=0;
static uint32_t seq_ctr[2]={0,0};                    // per-endpoint submit sequence
static uint64_t lost_bytes[2]={0,0}, total_lost[2]={0,0};
static uint32_t lost_pkts[2]={0,0};

static int ep_idx(uint8_t ep){ return ep==AUDIO_EP ? 1 : 0; }

static size_t ring_free(void){
    size_t h=atomic_load_explicit(&r_head,memory_order_relaxed);
    size_t t=atomic_load_explicit(&r_tail,memory_order_acquire);
    return RING-(h-t);
}
static void ring_write(const void*d, size_t n){   // caller has verified room
    size_t h=atomic_load_explicit(&r_head,memory_order_relaxed);
    size_t off=h%RING, first=RING-off; if(first>n) first=n;
    memcpy(ring+off,d,first);
    if(n>first) memcpy(ring,(const uint8_t*)d+first,n-first);
    atomic_store_explicit(&r_head,h+n,memory_order_release);
    size_t used=h+n-atomic_load_explicit(&r_tail,memory_order_relaxed);
    if(used>r_max) r_max=used;
}
static void wake_writer(void){
    // trylock: if the writer holds sig_m it is either draining or about to re-check
    // r_head under the lock, so the missed signal costs at most one 100 ms backstop.
    if(pthread_mutex_trylock(&sig_m)==0){ pthread_cond_signal(&sig_c); pthread_mutex_unlock(&sig_m); }
}

static void flush_loss(uint8_t ep){
    int e=ep_idx(ep);
    if(!lost_pkts[e]) return;
    if(ring_free() < sizeof(rec_hdr)) return;        // still no room; keep accumulating
    uint32_t lb = lost_bytes[e] > 0xffffffffu ? 0xffffffffu : (uint32_t)lost_bytes[e];
    rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,0,seq_ctr[e],0,lost_pkts[e],lb};
    ring_write(&h,sizeof h);
    hostloss_recs++; lost_pkts[e]=0; lost_bytes[e]=0;
}
static void put_pkt(uint8_t ep, uint16_t pi, uint32_t seq, uint32_t st,
                    uint32_t req, const uint8_t*d, uint32_t al){
    int e=ep_idx(ep);
    flush_loss(ep);
    if(lost_pkts[e] || ring_free() < sizeof(rec_hdr)+al){
        lost_pkts[e]++; lost_bytes[e]+=al; total_lost[e]+=al;   // explicit, counted, and
        return;                                                  // marked in-stream on flush
    }
    rec_hdr h={REC_MAGIC,REC_DATA,ep,pi,seq,st,req,al};
    ring_write(&h,sizeof h);
    if(al) ring_write(d,al);
    wake_writer();
}
static void put_meta(uint8_t type, uint8_t ep, uint32_t seq, uint32_t st,
                     const void*payload, uint32_t plen){
    if(ring_free() < sizeof(rec_hdr)+plen) return;   // meta records are best-effort
    rec_hdr h={REC_MAGIC,type,ep,0,seq,st,0,plen};
    ring_write(&h,sizeof h);
    if(plen) ring_write(payload,plen);
    wake_writer();
}

static void* writer(void*_){
    (void)_;
    uint8_t *local=malloc(8u<<20);
    for(;;){
        size_t t=atomic_load_explicit(&r_tail,memory_order_relaxed);
        size_t h=atomic_load_explicit(&r_head,memory_order_acquire);
        if(h==t){
            if(atomic_load(&g_done)) break;
            pthread_mutex_lock(&sig_m);
            h=atomic_load_explicit(&r_head,memory_order_acquire);   // re-check: no missed wakeup
            if(h==t && !atomic_load(&g_done)){
                struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts);
                ts.tv_nsec+=100*1000000L;
                if(ts.tv_nsec>=1000000000L){ ts.tv_sec++; ts.tv_nsec-=1000000000L; }
                pthread_cond_timedwait(&sig_c,&sig_m,&ts);
            }
            pthread_mutex_unlock(&sig_m);
            continue;
        }
        size_t n=h-t; if(n>(8u<<20)) n=8u<<20;
        size_t off=t%RING, first=RING-off; if(first>n) first=n;
        memcpy(local,ring+off,first);
        if(n>first) memcpy(local+first,ring,n-first);
        atomic_store_explicit(&r_tail,t+n,memory_order_release);
        if(fwrite(local,1,n,g_out)!=n){ fprintf(stderr,"!! SHORT WRITE — stopping\n"); atomic_store(&g_stop,1); }
    }
    free(local); return NULL;
}

typedef struct { struct libusb_transfer *x; uint8_t ep; uint32_t seq; int idx; } xinfo;
static xinfo XS[NXF];

static void cb(struct libusb_transfer *x){
    xinfo *xi=x->user_data;
    atomic_fetch_sub(&inflight,1);
    int e=ep_idx(xi->ep);
    if(x->status==LIBUSB_TRANSFER_COMPLETED){
        for(int i=0;i<x->num_iso_packets;i++){
            struct libusb_iso_packet_descriptor *p=&x->iso_packet_desc[i];
            uint32_t al = (p->status==LIBUSB_TRANSFER_COMPLETED) ? p->actual_length : 0;
            if(p->status!=LIBUSB_TRANSFER_COMPLETED) iso_err++;
            if(al==0) zero_pkts++; else if(al<p->length) short_pkts++;
            put_pkt(xi->ep,(uint16_t)i,xi->seq,(uint32_t)p->status,p->length,
                    libusb_get_iso_packet_buffer_simple(x,i),al);
            if(xi->ep==VIDEO_EP) v_bytes+=al; else a_bytes+=al;
        }
    } else {
        xfer_err++;
        put_meta(REC_XFERERR,xi->ep,xi->seq,(uint32_t)x->status,NULL,0);
        if(x->status==LIBUSB_TRANSFER_NO_DEVICE) atomic_store(&g_stop,1);
    }
    if(!atomic_load(&g_stop) && x->status!=LIBUSB_TRANSFER_NO_DEVICE){
        xi->seq=seq_ctr[e]++;
        if(libusb_submit_transfer(x)==0){ atomic_fetch_add(&inflight,1); return; }
        xfer_err++;
    }
    free(x->buffer); libusb_free_transfer(x); XS[xi->idx].x=NULL;
}

static int vout(libusb_device_handle*h,uint8_t req,uint16_t idx,uint32_t be){
    uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};
    return libusb_control_transfer(h,0x40,req,0,idx,b,4,1000);
}

int main(int argc,char**argv){
    if(argc<4){ printf("usage: %s <component|svideo|composite> <seconds> <outfile> [ringMB=256]\n",argv[0]); return 9; }
    const char*in=argv[1]; int secs=atoi(argv[2]); const char*outf=argv[3];
    size_t ringmb = argc>4 ? (size_t)atoi(argv[4]) : 256;
    if(ringmb<64) ringmb=64;
    RING = ringmb<<20;
    uint32_t vsel;
    if(!strcmp(in,"component"))vsel=0x02000000; else if(!strcmp(in,"composite"))vsel=0x04000000;
    else if(!strcmp(in,"svideo"))vsel=0x06000000; else { printf("bad input\n"); return 9; }
    uint32_t mode=0x09000000|vsel|0x10000000|0x20000000;

    ring=malloc(RING); if(!ring){ printf("ring alloc fail\n"); return 1; }
    g_out=fopen(outf,"wb"); if(!g_out){ printf("open %s fail\n",outf); return 1; }

    libusb_context*ctx=NULL; if(libusb_init(&ctx)) return 1;
    libusb_device_handle*h=libusb_open_device_with_vid_pid(ctx,VID,PID);
    if(!h){ printf("OPEN FAIL\n"); return 2; }
    if(libusb_claim_interface(h,0)){ printf("claim fail\n"); return 3; }
    libusb_set_interface_alt_setting(h,0,1); libusb_set_interface_alt_setting(h,0,2);
    vout(h,215,0,mode); vout(h,215,24,0x73c60001);
    printf("input=%s mode=0x%08x -> %ds to %s (tagged, SPSC ring=%zuMB)\n",in,mode,secs,outf,ringmb);

    char sess[256];
    int sl=snprintf(sess,sizeof sess,
        "capture_tagged_bench v1 mode=0x%08x V_PKT=%d V_NPK=%d A_PKT=%d A_NPK=%d XFERS=%d ring=%zuMB",
        mode,V_PKT,V_NPK,A_PKT,A_NPK,XFERS,ringmb);
    put_meta(REC_SESSION,0,0,0,sess,(uint32_t)sl);

    pthread_t wt; pthread_create(&wt,NULL,writer,NULL);
    int n=0;
    for(int w=0;w<2;w++){
        uint8_t ep=w?AUDIO_EP:VIDEO_EP; int npk=w?A_NPK:V_NPK, pkt=w?A_PKT:V_PKT;
        for(int i=0;i<XFERS;i++,n++){
            uint8_t*buf=malloc((size_t)npk*pkt);
            struct libusb_transfer*x=libusb_alloc_transfer(npk);
            XS[n]=(xinfo){x,ep,seq_ctr[w]++,n};
            libusb_fill_iso_transfer(x,h,ep,buf,npk*pkt,npk,cb,&XS[n],0);
            libusb_set_iso_packet_lengths(x,pkt);
            if(libusb_submit_transfer(x)==0) atomic_fetch_add(&inflight,1);
            else { free(buf); libusb_free_transfer(x); XS[n].x=NULL; }
        }
    }

    time_t start=time(NULL); struct timeval tv={0,100000};
    while(time(NULL)-start<secs && !atomic_load(&g_stop)) libusb_handle_events_timeout(ctx,&tv);
    atomic_store(&g_stop,1);
    for(int i=0;i<NXF;i++) if(XS[i].x) libusb_cancel_transfer(XS[i].x);
    int guard=0;
    while(atomic_load(&inflight)>0 && guard<300){ libusb_handle_events_timeout(ctx,&tv); guard++; }
    flush_loss(VIDEO_EP); flush_loss(AUDIO_EP);       // any still-pending loss becomes a record

    pthread_mutex_lock(&sig_m);
    atomic_store(&g_done,1); pthread_cond_signal(&sig_c);
    pthread_mutex_unlock(&sig_m);
    pthread_join(wt,NULL);
    if(fclose(g_out)!=0) fprintf(stderr,"!! fclose failed\n");

    printf("\n=== RESULTS ===\n");
    printf("video %.1f MB (%.0f Mbit/s) | audio %.1f MB\n",
           v_bytes/1e6,(v_bytes*8.0/1e6)/secs,a_bytes/1e6);
    printf("iso-pkt errors=%ld  xfer errors=%ld  zero-len pkts=%ld  short pkts=%ld\n",
           iso_err,xfer_err,zero_pkts,short_pkts);
    printf("HostLoss records=%ld  lost video=%" PRIu64 " B  lost audio=%" PRIu64 " B\n",
           hostloss_recs,total_lost[0],total_lost[1]);
    printf("ring high-water=%.0f MB / %zu MB\n",r_max/1e6,ringmb);
    libusb_release_interface(h,0); libusb_close(h); libusb_exit(ctx);
    return 0;
}
