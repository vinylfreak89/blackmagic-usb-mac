// capture_untagged_ring — fixed capture: NO disk I/O in the iso callback (ring buffer + writer
// thread), error counting, fwrite-return checks, submission-seq inversion detection,
// clean drain. Usage: ./capture_untagged_ring <component|svideo|composite> <seconds> <outfile>
#include <libusb.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

#define VID 0x1EDB
#define PID 0xBD3B
#define VIDEO_EP 0x83
#define AUDIO_EP 0x84
#define V_PKT 15360
#define V_NPK 8
#define A_PKT 0xc0
#define A_NPK 80
#define XFERS 6
#define RINGSIZE (256u*1024u*1024u)   // 256 MB ring (~11s of buffering)

static uint8_t *ring;
static size_t r_head=0, r_tail=0, r_count=0, r_max=0;
static long overflow_bytes=0;
static pthread_mutex_t r_mtx=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  r_cv=PTHREAD_COND_INITIALIZER;
static FILE *g_out;
static volatile int g_stop=0, g_done=0;

static int inflight=0;
static long v_bytes=0,a_bytes=0,iso_err=0,xfer_err=0;
static long v_submit=0;           // next video submission seq
static long last_v_submit=-1, v_inversions=0;   // reorder detection (video)

// producer (runs on the libusb event/main thread) — memcpy only, NO disk I/O
static void ring_put(const uint8_t*d, size_t n){
    pthread_mutex_lock(&r_mtx);
    if(r_count+n > RINGSIZE){ overflow_bytes += n; pthread_mutex_unlock(&r_mtx); return; }
    size_t first = RINGSIZE - r_head; if(first>n) first=n;
    memcpy(ring+r_head, d, first);
    if(n>first) memcpy(ring, d+first, n-first);
    r_head=(r_head+n)%RINGSIZE; r_count+=n; if(r_count>r_max) r_max=r_count;
    pthread_cond_signal(&r_cv);
    pthread_mutex_unlock(&r_mtx);
}
// consumer (writer thread) — copies out under lock, fwrites UNLOCKED (never blocks producer)
static void* writer(void*_){
    uint8_t*local=malloc(8u*1024u*1024u);
    for(;;){
        pthread_mutex_lock(&r_mtx);
        while(r_count==0 && !g_done) pthread_cond_wait(&r_cv,&r_mtx);
        if(r_count==0 && g_done){ pthread_mutex_unlock(&r_mtx); break; }
        size_t chunk=r_count; if(chunk>8u*1024u*1024u) chunk=8u*1024u*1024u;
        size_t first=RINGSIZE-r_tail; if(first>chunk) first=chunk;
        memcpy(local, ring+r_tail, first);
        if(chunk>first) memcpy(local+first, ring, chunk-first);
        r_tail=(r_tail+chunk)%RINGSIZE; r_count-=chunk;
        pthread_mutex_unlock(&r_mtx);
        size_t w=fwrite(local,1,chunk,g_out);
        if(w!=chunk){ fprintf(stderr,"!! SHORT WRITE %zu/%zu\n",w,chunk); }
    }
    free(local); return NULL;
}

static void cb(struct libusb_transfer *x){
    inflight--;
    int isvideo=(x->endpoint==VIDEO_EP);
    if(isvideo){
        long s=(long)(intptr_t)x->user_data;
        if(last_v_submit>=0 && s<last_v_submit) v_inversions++;   // out-of-order completion
        last_v_submit=s;
    }
    if(x->status==LIBUSB_TRANSFER_COMPLETED){
        for(int i=0;i<x->num_iso_packets;i++){
            struct libusb_iso_packet_descriptor *p=&x->iso_packet_desc[i];
            if(p->status!=LIBUSB_TRANSFER_COMPLETED){ iso_err++; continue; }
            int n=p->actual_length; if(n<=0) continue;
            ring_put(libusb_get_iso_packet_buffer_simple(x,i), n);
            if(isvideo) v_bytes+=n; else a_bytes+=n;
        }
    } else if(x->status==LIBUSB_TRANSFER_NO_DEVICE){ g_stop=1; xfer_err++; }
    else { xfer_err++; }
    if(!g_stop && x->status!=LIBUSB_TRANSFER_NO_DEVICE){
        if(isvideo) x->user_data=(void*)(intptr_t)(v_submit++);
        if(libusb_submit_transfer(x)==0){ inflight++; return; }
        xfer_err++;
    }
    free(x->buffer); libusb_free_transfer(x);
}
static int vout(libusb_device_handle*h,uint8_t req,uint16_t idx,uint32_t be){
    uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};
    return libusb_control_transfer(h,0x40,req,0,idx,b,4,1000);
}

int main(int argc,char**argv){
    if(argc<4){ printf("usage: %s <component|svideo|composite> <seconds> <outfile>\n",argv[0]); return 9; }
    const char*in=argv[1]; int secs=atoi(argv[2]); const char*outf=argv[3];
    uint32_t vsel; if(!strcmp(in,"component"))vsel=0x02000000;else if(!strcmp(in,"composite"))vsel=0x04000000;else if(!strcmp(in,"svideo"))vsel=0x06000000;else{printf("bad input\n");return 9;}
    uint32_t mode=0x09000000|vsel|0x10000000|0x20000000;
    ring=malloc(RINGSIZE); if(!ring){ printf("ring alloc fail\n"); return 1; }
    g_out=fopen(outf,"wb"); if(!g_out){ printf("open %s fail\n",outf); return 1; }

    libusb_context*ctx=NULL; if(libusb_init(&ctx)) return 1;
    libusb_device_handle*h=libusb_open_device_with_vid_pid(ctx,VID,PID); if(!h){ printf("OPEN FAIL\n"); return 2; }
    if(libusb_claim_interface(h,0)){ printf("claim fail\n"); return 3; }
    libusb_set_interface_alt_setting(h,0,1); libusb_set_interface_alt_setting(h,0,2);
    vout(h,215,0,mode); vout(h,215,24,0x73c60001);
    printf("input=%s mode=0x%08x -> %ds to %s (ring=%uMB, writer thread)\n",in,mode,secs,outf,RINGSIZE>>20);

    pthread_t wt; pthread_create(&wt,NULL,writer,NULL);
    for(int w=0;w<2;w++){
        int ep=w?AUDIO_EP:VIDEO_EP,npk=w?A_NPK:V_NPK,pkt=w?A_PKT:V_PKT,bufsz=npk*pkt;
        for(int i=0;i<XFERS;i++){
            uint8_t*buf=malloc(bufsz); struct libusb_transfer*x=libusb_alloc_transfer(npk);
            libusb_fill_iso_transfer(x,h,ep,buf,bufsz,npk,cb, (w?NULL:(void*)(intptr_t)(v_submit++)), 0);
            libusb_set_iso_packet_lengths(x,pkt);
            if(libusb_submit_transfer(x)==0) inflight++; else { free(buf); libusb_free_transfer(x); }
        }
    }
    time_t start=time(NULL); struct timeval tv={0,100000};
    while(time(NULL)-start<secs && !g_stop) libusb_handle_events_timeout(ctx,&tv);
    g_stop=1; int guard=0; while(inflight>0 && guard<300){ libusb_handle_events_timeout(ctx,&tv); guard++; }
    pthread_mutex_lock(&r_mtx); g_done=1; pthread_cond_signal(&r_cv); pthread_mutex_unlock(&r_mtx);
    pthread_join(wt,NULL); fclose(g_out);

    double sec=secs;
    printf("\n=== RESULTS ===\n");
    printf("video %.1f MB (%.0f Mbit/s) | audio %.1f MB\n", v_bytes/1e6, (v_bytes*8.0/1e6)/sec, a_bytes/1e6);
    printf("iso-packet errors=%ld  transfer errors=%ld  ring overflow=%ld B\n", iso_err, xfer_err, overflow_bytes);
    printf("ring high-water=%.0f MB / %u MB\n", r_max/1e6, RINGSIZE>>20);
    printf("video submission-order INVERSIONS (out-of-order completions)=%ld\n", v_inversions);
    libusb_release_interface(h,0); libusb_close(h); libusb_exit(ctx);
    return 0;
}
