// libusb_replay_shim — replay a capture_tagged_bench .tpc capture through the REAL capture code by
// impersonating libusb. Link the capture source against this file INSTEAD of
// -lusb-1.0 and the unmodified code sees the recorded traffic exactly as the
// device delivered it: same endpoints, same packet lengths, same interleave,
// same callback cadence (§8 property 9, deterministic replay, made concrete).
//
//   clang -O2 -Wall -o capture_tagged_bench_replay capture_tagged_bench.c libusb_replay_shim.c -lpthread \
//         $(pkg-config --cflags libusb-1.0)          # cflags ONLY — no -lusb!
//   REPLAY_CAPTURE=capture.tpc ./capture_tagged_bench_replay svideo 600 out.tpc
//
// The replay is as-fast-as-possible; input EOF surfaces as NO_DEVICE, which the
// capture code already handles as a clean stop.
//
// Fault injection (the paths healthy hardware never exercises):
//   REPLAY_MAX_DATA=N            stop after N DATA records (bounded runs)
//   REPLAY_DROP_VIDEO_XFER=N     swallow the Nth completed video transfer —
//                              its callback never fires; the output MUST show
//                              a submit-seq GAP or the accounting is broken
//   REPLAY_FAIL_SUBMIT_VIDEO_AT=N  Nth video submit returns LIBUSB_ERROR_BUSY
//   REPLAY_FAIL_SUBMIT_CODE=N      libusb error returned by submit faults (default BUSY)
//   REPLAY_FAIL_SUBMIT_VIDEO_FROM=N  every video submit from the Nth on fails (parks the
//                                fleet in the pending state until stop — leak/teardown test)
//   REPLAY_FAIL_ALT_AT=N         Nth alternate-setting call fails
//   REPLAY_FAIL_CONTROL_AT=N     Nth control transfer fails; REPLAY_SHORT_CONTROL_AT=N returns 3
//   REPLAY_FAIL_ALLOC_AT=N       Nth libusb transfer allocation fails
//   REPLAY_WITHHOLD_CANCEL=1     retain cancel callbacks (teardown containment test)
//                              once — exercises the no-fleet-shrink retry path
//   REPLAY_PACE_US=N             sleep N µs per completed transfer (16000 ≈ the
//                              real device's video cadence -> realtime replay
//                              for clock/A-V-sync/live-path development);
//                              default 0 = as fast as the disk goes
//
// Bench scope: single context/device, iso IN only, no hotplug, no threads of
// its own (everything happens inside libusb_handle_events_timeout, mirroring
// the single-event-thread model the real backend presents to this code).
#include <libusb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

#define REC_MAGIC 0x31504143u
enum { REC_DATA=0, REC_HOSTLOSS=1, REC_XFERERR=2, REC_SESSION=3, REC_TICK=4 };
typedef struct { uint32_t magic; uint8_t type, endpoint; uint16_t pkt_index;
    uint32_t submit_seq, status, req_len, actual_len; } rec_hdr;

struct libusb_context { int unused; };
struct libusb_device_handle { int unused; };
static struct libusb_context g_ctx;
static struct libusb_device_handle g_h;

#define QMAX 64
typedef struct {
    struct libusb_transfer *q[QMAX];   // submitted, awaiting data (FIFO)
    int head, count;
    int fill;                          // packets filled into q[head] so far
    struct libusb_transfer *cancelled[QMAX];
    int ncancel;
    int eof_sent;
} epstate;
static epstate EP83, EP84;
static FILE *g_in;
static long g_data_seen=0, g_max_data=-1;
static long g_v_completed=0, g_drop_video=-1;
static long g_v_submits=0, g_fail_submit_at=-1, g_fail_submit_from=-1;
static int g_fail_submit_code=LIBUSB_ERROR_BUSY;
static long g_alt_calls=0, g_fail_alt_at=-1, g_control_calls=0, g_fail_control_at=-1,
            g_short_control_at=-1, g_alloc_calls=0, g_fail_alloc_at=-1;
static int g_withhold_cancel=0, g_burst=4, g_pace=0;
static int g_eof=0;

static epstate* eps(uint8_t ep){ return ep==0x84 ? &EP84 : &EP83; }

int libusb_init(libusb_context **ctx){
    const char *p=getenv("REPLAY_CAPTURE");
    if(!p){ fprintf(stderr,"libusb_replay_shim: set REPLAY_CAPTURE=<capture.tpc>\n"); return LIBUSB_ERROR_OTHER; }
    if(g_in) fclose(g_in);
    g_in=fopen(p,"rb");
    if(!g_in){ fprintf(stderr,"libusb_replay_shim: cannot open %s\n",p); return LIBUSB_ERROR_OTHER; }
    // per-session state: a process may open several sessions (test harnesses do), and the
    // fault-injection counters must count THIS session's submits, not the process's
    memset(&EP83,0,sizeof EP83); memset(&EP84,0,sizeof EP84);
    g_data_seen=0; g_v_completed=0; g_v_submits=0; g_eof=0;
    g_alt_calls=0; g_control_calls=0; g_alloc_calls=0;
    g_max_data=-1; g_drop_video=-1; g_fail_submit_at=-1; g_fail_submit_from=-1;
    g_fail_alt_at=-1; g_fail_control_at=-1; g_short_control_at=-1; g_fail_alloc_at=-1;
    if(getenv("REPLAY_MAX_DATA")) g_max_data=atol(getenv("REPLAY_MAX_DATA"));
    if(getenv("REPLAY_DROP_VIDEO_XFER")) g_drop_video=atol(getenv("REPLAY_DROP_VIDEO_XFER"));
    if(getenv("REPLAY_FAIL_SUBMIT_VIDEO_AT")) g_fail_submit_at=atol(getenv("REPLAY_FAIL_SUBMIT_VIDEO_AT"));
    if(getenv("REPLAY_FAIL_SUBMIT_VIDEO_FROM")) g_fail_submit_from=atol(getenv("REPLAY_FAIL_SUBMIT_VIDEO_FROM"));
    if(getenv("REPLAY_FAIL_SUBMIT_CODE")) g_fail_submit_code=atoi(getenv("REPLAY_FAIL_SUBMIT_CODE")); else g_fail_submit_code=LIBUSB_ERROR_BUSY;
    if(getenv("REPLAY_FAIL_ALT_AT")) g_fail_alt_at=atol(getenv("REPLAY_FAIL_ALT_AT"));
    if(getenv("REPLAY_FAIL_CONTROL_AT")) g_fail_control_at=atol(getenv("REPLAY_FAIL_CONTROL_AT"));
    if(getenv("REPLAY_SHORT_CONTROL_AT")) g_short_control_at=atol(getenv("REPLAY_SHORT_CONTROL_AT"));
    if(getenv("REPLAY_FAIL_CONTROL")) g_fail_control_at=1;
    if(getenv("REPLAY_FAIL_ALLOC_AT")) g_fail_alloc_at=atol(getenv("REPLAY_FAIL_ALLOC_AT"));
    g_withhold_cancel=getenv("REPLAY_WITHHOLD_CANCEL")!=NULL;
    { const char *b=getenv("REPLAY_BURST"); g_burst=b?atoi(b):4; if(g_burst<1) g_burst=1; }
    { const char *p=getenv("REPLAY_PACE_US"); g_pace=p?atoi(p):0; }
    if(ctx) *ctx=&g_ctx;
    return 0;
}
void libusb_exit(libusb_context *ctx){ (void)ctx; if(g_in){ fclose(g_in); g_in=NULL; } }
libusb_device_handle* libusb_open_device_with_vid_pid(libusb_context*c,uint16_t v,uint16_t p){
    (void)c;(void)v;(void)p; return &g_h; }
void libusb_close(libusb_device_handle*h){ (void)h; }
int libusb_claim_interface(libusb_device_handle*h,int i){ (void)h;(void)i; return 0; }
int libusb_release_interface(libusb_device_handle*h,int i){ (void)h;(void)i; return 0; }
int libusb_set_interface_alt_setting(libusb_device_handle*h,int i,int a){
    (void)h;(void)i;(void)a; return (++g_alt_calls==g_fail_alt_at)?LIBUSB_ERROR_PIPE:0; }
int libusb_control_transfer(libusb_device_handle*h,uint8_t t,uint8_t r,uint16_t v,
                            uint16_t i,unsigned char*d,uint16_t len,unsigned int to){
    (void)h;(void)t;(void)r;(void)v;(void)i;(void)d;(void)to;
    g_control_calls++; if(g_control_calls==g_fail_control_at) return LIBUSB_ERROR_PIPE;
    if(g_control_calls==g_short_control_at) return len?len-1:0; return len; }
const char* libusb_error_name(int code){
    static char b[32]; snprintf(b,sizeof b,"REPLAY_ERR_%d",code); return b; }

struct libusb_transfer* libusb_alloc_transfer(int iso){
    if(++g_alloc_calls==g_fail_alloc_at) return NULL;
    return calloc(1, sizeof(struct libusb_transfer)
                     + (size_t)(iso>0?iso:0)*sizeof(struct libusb_iso_packet_descriptor));
}
void libusb_free_transfer(struct libusb_transfer*x){ free(x); }

int libusb_submit_transfer(struct libusb_transfer *x){
    epstate *s=eps(x->endpoint);
    if(x->endpoint==0x83){
        g_v_submits++;
        if(g_fail_submit_at>0 && g_v_submits==g_fail_submit_at){
            g_fail_submit_at=-1;             // fail exactly once
            return g_fail_submit_code;
        }
        if(g_fail_submit_from>0 && g_v_submits>=g_fail_submit_from) return g_fail_submit_code;
    }
    if(s->count>=QMAX) return LIBUSB_ERROR_BUSY;
    s->q[(s->head+s->count)%QMAX]=x; s->count++;
    return 0;
}
int libusb_cancel_transfer(struct libusb_transfer *x){
    epstate *s=eps(x->endpoint);
    for(int i=0;i<s->count;i++){
        int idx=(s->head+i)%QMAX;
        if(s->q[idx]==x){
            for(int j=i;j<s->count-1;j++)
                s->q[(s->head+j)%QMAX]=s->q[(s->head+j+1)%QMAX];
            s->count--; if(i==0) s->fill=0;
            s->cancelled[s->ncancel++]=x;
            return 0;
        }
    }
    return LIBUSB_ERROR_NOT_FOUND;
}

static void complete(struct libusb_transfer *x, enum libusb_transfer_status st){
    x->status=st;
    if(x->callback) x->callback(x);
}
static void pop_and_complete(epstate *s, enum libusb_transfer_status st){
    struct libusb_transfer *x=s->q[s->head];
    s->head=(s->head+1)%QMAX; s->count--; s->fill=0;
    if(st==LIBUSB_TRANSFER_COMPLETED && x->endpoint==0x83){
        g_v_completed++;
        if(g_v_completed==g_drop_video) return;   // swallowed: no callback, ever
    }
    complete(x,st);
}
static void flush_cancels(epstate *s){
    if(g_withhold_cancel) return;
    while(s->ncancel>0) complete(s->cancelled[--s->ncancel], LIBUSB_TRANSFER_CANCELLED);
}
static void send_eof(epstate *s){
    if(!s->eof_sent && s->count>0){ s->eof_sent=1; pop_and_complete(s,LIBUSB_TRANSFER_NO_DEVICE); }
}

int libusb_handle_events_timeout(libusb_context *ctx, struct timeval *tv){
    (void)ctx;(void)tv;
    flush_cancels(&EP83); flush_cancels(&EP84);
    int delivered=0;
    while(delivered<g_burst){
        if(g_eof || (g_max_data>=0 && g_data_seen>=g_max_data)){
            send_eof(&EP83); send_eof(&EP84); return 0;
        }
        rec_hdr h;
        if(fread(&h,1,sizeof h,g_in)!=sizeof h || h.magic!=REC_MAGIC){ g_eof=1; continue; }
        uint32_t plen=(h.type==REC_DATA||h.type==REC_SESSION)?h.actual_len:0;
        if(h.type!=REC_DATA){ if(plen) fseek(g_in,plen,SEEK_CUR); continue; }
        g_data_seen++;
        epstate *s=eps(h.endpoint);
        if(s->count==0){                       // no transfer waiting: replay can't
            if(plen) fseek(g_in,plen,SEEK_CUR); // backpressure a file; drop like a
            continue;                           // device would on a starved host
        }
        struct libusb_transfer *x=s->q[s->head];
        int i=s->fill;
        struct libusb_iso_packet_descriptor *p=&x->iso_packet_desc[i];
        unsigned char *dst=x->buffer + (size_t)i * x->iso_packet_desc[0].length;
        uint32_t n=h.actual_len;
        if(n>p->length) n=p->length;
        if(n && fread(dst,1,n,g_in)!=n){ g_eof=1; continue; }
        if(h.actual_len>n) fseek(g_in,h.actual_len-n,SEEK_CUR);
        p->actual_length=n; p->status=LIBUSB_TRANSFER_COMPLETED;
        s->fill++;
        if(g_pace>0 && s->fill>=x->num_iso_packets) usleep(g_pace);
        if(s->fill>=x->num_iso_packets){ pop_and_complete(s,LIBUSB_TRANSFER_COMPLETED); delivered++; }
    }
    return 0;
}
