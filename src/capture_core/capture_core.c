// capture_core implementation. Internal shape (all §8-mandated):
//   backend thread (USB event loop OR .tpc reader) --> SPSC byte ring of
//   tagged records --> delivery thread --> user callbacks.
// The ring carries records in the .tpc wire format, so the tpc sink is a
// trivial re-serialization and capture/replay share one delivery path.
#include "capture_core.h"
#include <libusb.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/qos.h>
#include <pthread/qos.h>

#define VID 0x1EDB
#define PID 0xBD3B
#define V_PKT 15360
#define V_NPK 128
#define A_PKT 0xc0
#define A_NPK 80
#define XFERS 8
#define NXF (XFERS*2)

#define REC_MAGIC 0x31504143u
enum { REC_DATA=0, REC_HOSTLOSS=1, REC_XFERERR=2, REC_SESSION=3, REC_TICK=4 };
typedef struct {
    uint32_t magic; uint8_t type, endpoint; uint16_t pkt_index;
    uint32_t submit_seq, status, req_len, actual_len;
} rec_hdr;
_Static_assert(sizeof(rec_hdr)==24, "rec_hdr must be 24 bytes");

typedef struct cc_session cc_session_fwd;
typedef struct { struct libusb_transfer *x; uint8_t ep; uint32_t seq; int idx; int pending; struct cc_session *s; } xinfo;

struct cc_session {
    cc_config cfg;
    cc_callbacks cb;
    // ring
    uint8_t *ring; size_t ring_sz;
    _Atomic size_t r_head, r_tail;
    size_t r_max;
    pthread_mutex_t sig_m; pthread_cond_t sig_c;
    // threads / state machine
    pthread_t backend_t, delivery_t;
    _Atomic int stop_req, backend_done, started;
    _Atomic int end_reason; _Atomic int end_fired;
    // producer-side stats (backend thread only)
    uint64_t bytes[2]; uint64_t lost_bytes[2]; uint32_t lost_pkts[2];
    long iso_err, xfer_err, resub_fail, resub_rec, zero_pkts, short_pkts;
    uint32_t seq_ctr[2];
    int fleet[2];
    long xfers_alloc, xfers_freed;   // every allocated transfer must be freed by stop (no leak, no double free)
    // usb
    libusb_context *ctx; libusb_device_handle *h;
    xinfo xs[NXF];
    _Atomic long inflight;
};

static int ep_i(uint8_t ep){ return ep==CC_EP_AUDIO ? 1 : 0; }

// ---------------- ring (single producer = backend, single consumer = delivery)
static size_t ring_free_(cc_session *s){
    size_t h=atomic_load_explicit(&s->r_head,memory_order_relaxed);
    size_t t=atomic_load_explicit(&s->r_tail,memory_order_acquire);
    return s->ring_sz-(h-t);
}
// raw copy into the ring at an absolute position -- does NOT publish
static void ring_copy_at_(cc_session *s, size_t pos, const void*d, size_t n){
    size_t off=pos%s->ring_sz, first=s->ring_sz-off; if(first>n) first=n;
    memcpy(s->ring+off,d,first);
    if(n>first) memcpy(s->ring,(const uint8_t*)d+first,n-first);
}
// publish ONE record atomically: header+payload land, THEN head moves once.
// The delivery thread parses records, so partial publication is corruption --
// capture_tagged_bench got away with two-stage writes only because its consumer never parsed.
static void ring_put_record_(cc_session *s, const rec_hdr *h, const void *pay, size_t plen){
    size_t head=atomic_load_explicit(&s->r_head,memory_order_relaxed);
    ring_copy_at_(s,head,h,sizeof *h);
    if(plen) ring_copy_at_(s,head+sizeof *h,pay,plen);
    atomic_store_explicit(&s->r_head,head+sizeof *h+plen,memory_order_release);
    size_t used=head+sizeof *h+plen-atomic_load_explicit(&s->r_tail,memory_order_relaxed);
    if(used>s->r_max) s->r_max=used;
}
static void wake_(cc_session *s){
    if(pthread_mutex_trylock(&s->sig_m)==0){ pthread_cond_signal(&s->sig_c); pthread_mutex_unlock(&s->sig_m); }
}
static void flush_loss_(cc_session *s, uint8_t ep){
    int e=ep_i(ep);
    if(!s->lost_pkts[e] || ring_free_(s)<sizeof(rec_hdr)) return;
    uint32_t lb = s->lost_bytes[e]>0xffffffffu?0xffffffffu:(uint32_t)s->lost_bytes[e];
    rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,0,s->seq_ctr[e],0,s->lost_pkts[e],lb};
    ring_put_record_(s,&h,NULL,0);
    s->lost_pkts[e]=0; s->lost_bytes[e]=0;
}
// Termination-path flush: loss accounting MUST reach the consumer before the
// backend declares itself done, or bytes vanish unconfessed (caught by the
// balance test: delivered + lost must equal input to the byte). Waits for the
// consumer to drain ring space; bounded so a wedged user callback cannot hang
// cc_stop forever -- on timeout the loss stays visible in cc_stats and we say
// so loudly. (Polling here is a termination-only liveness backstop; the data
// path proper never polls.)
static void flush_loss_blocking_(cc_session *s, uint8_t ep){
    int e=ep_i(ep);
    for(int i=0; s->lost_pkts[e] && i<10000; i++){
        flush_loss_(s,ep);
        if(!s->lost_pkts[e]){ wake_(s); return; }
        usleep(1000);
    }
    if(s->lost_pkts[e])
        fprintf(stderr,"capture_core: %u lost packets on ep 0x%02x UNREPORTED to consumer "
                "(ring never drained); loss remains in cc_stats\n",s->lost_pkts[e],ep);
}

static void put_pkt_(cc_session *s, uint8_t ep, uint16_t pi, uint32_t seq,
                     uint32_t st, uint32_t req, const uint8_t *d, uint32_t al){
    int e=ep_i(ep);
    flush_loss_(s,ep);
    if(s->lost_pkts[e] || ring_free_(s)<sizeof(rec_hdr)+al){
        s->lost_pkts[e]++; s->lost_bytes[e]+=al; return;   // marked on flush
    }
    rec_hdr h={REC_MAGIC,REC_DATA,ep,pi,seq,st,req,al};
    ring_put_record_(s,&h,d,al);
    wake_(s);
}
static void put_meta_(cc_session *s, uint8_t type, uint8_t ep, uint16_t pi,
                      uint32_t seq, uint32_t st, const void *p, uint32_t plen){
    if(ring_free_(s)<sizeof(rec_hdr)+plen) return;
    rec_hdr h={REC_MAGIC,type,ep,pi,seq,st,0,plen};
    ring_put_record_(s,&h,p,plen);
    wake_(s);
}

// ---------------- delivery thread: parse ring records -> user callbacks
static void* delivery_main(void *arg){
    cc_session *s=arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    size_t cap=1u<<20; uint8_t *buf=malloc(cap);
    for(;;){
        size_t t=atomic_load_explicit(&s->r_tail,memory_order_relaxed);
        size_t h=atomic_load_explicit(&s->r_head,memory_order_acquire);
        if(h==t){
            if(atomic_load(&s->backend_done)){
                // backend_done is stored after the backend's final ring publications (including
                // the termination HostLoss records), so an acquire re-load of r_head sees them.
                // Breaking on the stale h would drop exactly the loss accounting the design
                // leans on (delivered + lost == input).
                h=atomic_load_explicit(&s->r_head,memory_order_acquire);
                if(h==t) break;
                continue;
            }
            pthread_mutex_lock(&s->sig_m);
            h=atomic_load_explicit(&s->r_head,memory_order_acquire);
            if(h==t && !atomic_load(&s->backend_done)){
                struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts);
                ts.tv_nsec+=100*1000000L;
                if(ts.tv_nsec>=1000000000L){ ts.tv_sec++; ts.tv_nsec-=1000000000L; }
                pthread_cond_timedwait(&s->sig_c,&s->sig_m,&ts);
            }
            pthread_mutex_unlock(&s->sig_m);
            continue;
        }
        // copy out one record (header, then payload)
        rec_hdr rh;
        size_t off=t%s->ring_sz, first=s->ring_sz-off;
        if(first>=sizeof rh) memcpy(&rh,s->ring+off,sizeof rh);
        else { memcpy(&rh,s->ring+off,first); memcpy((uint8_t*)&rh+first,s->ring,sizeof rh-first); }
        size_t plen=(rh.type==REC_DATA||rh.type==REC_SESSION)?rh.actual_len:0;
        if(plen>cap){ cap=plen; buf=realloc(buf,cap); }
        size_t p0=(t+sizeof rh)%s->ring_sz;
        size_t f2=s->ring_sz-p0; if(f2>plen) f2=plen;
        memcpy(buf,s->ring+p0,f2);
        if(plen>f2) memcpy(buf+f2,s->ring,plen-f2);
        atomic_store_explicit(&s->r_tail,t+sizeof rh+plen,memory_order_release);
        switch(rh.type){
        case REC_DATA: {
            cc_packet p={rh.endpoint,rh.pkt_index,rh.submit_seq,rh.status,
                         rh.req_len,rh.actual_len,buf};
            s->cb.on_packet(s->cb.ctx,&p);
            break; }
        case REC_HOSTLOSS:
            if(s->cb.on_loss) s->cb.on_loss(s->cb.ctx,rh.endpoint,rh.req_len,rh.actual_len);
            break;
        case REC_XFERERR:
            if(s->cb.on_error) s->cb.on_error(s->cb.ctx,rh.endpoint,rh.submit_seq,
                                              (int)rh.status,rh.pkt_index==0xFFFF);
            break;
        case REC_TICK:
            if(s->cb.on_tick) s->cb.on_tick(s->cb.ctx,rh.status);
            break;
        default: break; // SESSION etc: internal
        }
    }
    free(buf);
    if(!atomic_exchange(&s->end_fired,1))
        s->cb.on_end(s->cb.ctx,(enum cc_end)atomic_load(&s->end_reason));
    return NULL;
}

// ---------------- device backend
static void usb_cb(struct libusb_transfer *x){
    xinfo *xi=x->user_data;
    cc_session *s=xi->s;
    atomic_fetch_sub(&s->inflight,1);
    int e=ep_i(xi->ep);
    if(x->status==LIBUSB_TRANSFER_COMPLETED){
        for(int i=0;i<x->num_iso_packets;i++){
            struct libusb_iso_packet_descriptor *p=&x->iso_packet_desc[i];
            uint32_t al=(p->status==LIBUSB_TRANSFER_COMPLETED)?p->actual_length:0;
            if(p->status!=LIBUSB_TRANSFER_COMPLETED) s->iso_err++;
            if(al==0) s->zero_pkts++; else if(al<p->length) s->short_pkts++;
            put_pkt_(s,xi->ep,(uint16_t)i,xi->seq,(uint32_t)p->status,p->length,
                     libusb_get_iso_packet_buffer_simple(x,i),al);
            s->bytes[e]+=al;
        }
    } else if(x->status==LIBUSB_TRANSFER_CANCELLED && atomic_load(&s->stop_req)){
        /* deliberate */
    } else {
        s->xfer_err++;
        put_meta_(s,REC_XFERERR,xi->ep,0,xi->seq,(uint32_t)x->status,NULL,0);
        if(x->status==LIBUSB_TRANSFER_NO_DEVICE){
            atomic_store(&s->end_reason,CC_END_DEVICE_GONE);
            atomic_store(&s->stop_req,1);
        }
    }
    if(!atomic_load(&s->stop_req) && x->status!=LIBUSB_TRANSFER_NO_DEVICE){
        xi->seq=s->seq_ctr[e]++;
        int rc=libusb_submit_transfer(x);
        if(rc==0){ atomic_fetch_add(&s->inflight,1); return; }
        s->xfer_err++; s->resub_fail++;
        put_meta_(s,REC_XFERERR,xi->ep,0xFFFF,xi->seq,(uint32_t)(-rc),NULL,0);
        xi->pending=1;                          // retried from the event loop; never freed
        return;
    }
    free(x->buffer); libusb_free_transfer(x); s->xs[xi->idx].x=NULL; s->xfers_freed++;
}
static int vout_(libusb_device_handle*h,uint8_t req,uint16_t idx,uint32_t be){
    uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};
    return libusb_control_transfer(h,0x40,req,0,idx,b,4,1000);
}
static void* device_main(void *arg){
    cc_session *s=arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    char note[192];
    snprintf(note,sizeof note,"capture_core v1 input=%d ring=%zuMB V_NPK=%d XFERS=%d",
             s->cfg.input,s->ring_sz>>20,V_NPK,XFERS);
    put_meta_(s,REC_SESSION,0,0,0,0,note,(uint32_t)strlen(note));
    int n=0;
    for(int w=0;w<2;w++){
        uint8_t ep=w?CC_EP_AUDIO:CC_EP_VIDEO; int npk=w?A_NPK:V_NPK, pkt=w?A_PKT:V_PKT;
        for(int i=0;i<XFERS;i++,n++){
            uint8_t *buf=malloc((size_t)npk*pkt);
            struct libusb_transfer *x=libusb_alloc_transfer(npk);
            s->xfers_alloc++;
            s->xs[n]=(xinfo){x,ep,s->seq_ctr[w]++,n,0,s};
            libusb_fill_iso_transfer(x,s->h,ep,buf,npk*pkt,npk,usb_cb,&s->xs[n],0);
            libusb_set_iso_packet_lengths(x,pkt);
            if(libusb_submit_transfer(x)==0) atomic_fetch_add(&s->inflight,1);
            else { free(buf); libusb_free_transfer(x); s->xs[n].x=NULL; s->xfers_freed++; }
        }
    }
    struct timespec t0; clock_gettime(CLOCK_MONOTONIC,&t0);
    uint32_t last_tick=0;
    struct timeval tv={0,100000};
    while(!atomic_load(&s->stop_req)){
        libusb_handle_events_timeout(s->ctx,&tv);
        for(int i=0;i<NXF;i++)
            if(s->xs[i].x && s->xs[i].pending && libusb_submit_transfer(s->xs[i].x)==0){
                s->xs[i].pending=0; atomic_fetch_add(&s->inflight,1); s->resub_rec++;
            }
        struct timespec tn; clock_gettime(CLOCK_MONOTONIC,&tn);
        uint32_t ms=(uint32_t)((tn.tv_sec-t0.tv_sec)*1000+(tn.tv_nsec-t0.tv_nsec)/1000000);
        if(ms-last_tick>=1000){ last_tick=ms; put_meta_(s,REC_TICK,0,0,0,ms,NULL,0); }
    }
    // capture fleet before cancelling
    for(int i=0;i<NXF;i++) if(s->xs[i].x && !s->xs[i].pending)
        s->fleet[ep_i(s->xs[i].ep)]++;
    for(int i=0;i<NXF;i++){
        if(!s->xs[i].x) continue;
        if(s->xs[i].pending){
            // never (re)submitted: cancel would return NOT_FOUND and the callback that frees a
            // transfer would never run, leaking buffer+transfer per session
            free(s->xs[i].x->buffer); libusb_free_transfer(s->xs[i].x); s->xs[i].x=NULL; s->xfers_freed++;
        } else libusb_cancel_transfer(s->xs[i].x);
    }
    int guard=0;
    while(atomic_load(&s->inflight)>0 && guard++<300)
        libusb_handle_events_timeout(s->ctx,&tv);
    flush_loss_blocking_(s,CC_EP_VIDEO); flush_loss_blocking_(s,CC_EP_AUDIO);
    atomic_store(&s->backend_done,1); wake_(s);
    pthread_mutex_lock(&s->sig_m); pthread_cond_signal(&s->sig_c); pthread_mutex_unlock(&s->sig_m);
    return NULL;
}

// ---------------- replay backend
static void* replay_main(void *arg){
    cc_session *s=arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    FILE *f=fopen(s->cfg.replay_path,"rb");
    if(!f){ atomic_store(&s->end_reason,CC_END_REPLAY_EOF); goto done; }
    uint8_t *pay=malloc(1u<<20); size_t cap=1u<<20;
    int fill[2]={0,0};   // packets since last transfer boundary, for pacing
    while(!atomic_load(&s->stop_req)){
        rec_hdr h;
        if(fread(&h,1,sizeof h,f)!=sizeof h || h.magic!=REC_MAGIC) break;
        size_t plen=(h.type==REC_DATA||h.type==REC_SESSION)?h.actual_len:0;
        if(plen>cap){ cap=plen; pay=realloc(pay,cap); }
        if(plen && fread(pay,1,plen,f)!=plen) break;
        switch(h.type){
        case REC_DATA: {
            int e=ep_i(h.endpoint);
            // deliver with the ORIGINAL tags; backpressure via ring, honestly
            put_pkt_(s,h.endpoint,h.pkt_index,h.submit_seq,h.status,h.req_len,pay,h.actual_len);
            s->bytes[e]+=h.actual_len;
            if(h.actual_len==0) s->zero_pkts++; else if(h.actual_len<h.req_len) s->short_pkts++;
            int npk = e ? A_NPK : V_NPK;
            if(++fill[e]>=npk){ fill[e]=0;
                if(s->cfg.replay_pace_us>0 && e==0) usleep((useconds_t)s->cfg.replay_pace_us); }
            break; }
        case REC_TICK: put_meta_(s,REC_TICK,0,0,0,h.status,NULL,0); break;
        case REC_HOSTLOSS: {
            // fold the ORIGINAL capture's loss into our accounting so counts
            // survive replay (forwarding with zeroed fields lost them)
            int le=ep_i(h.endpoint);
            s->lost_pkts[le]+=h.req_len; s->lost_bytes[le]+=h.actual_len;
            flush_loss_(s,h.endpoint);
            break; }
        default: break;
        }
    }
    free(pay); fclose(f);
    if(atomic_load(&s->end_reason)==CC_END_STOPPED && !atomic_load(&s->stop_req))
        atomic_store(&s->end_reason,CC_END_REPLAY_EOF);
done:
    flush_loss_blocking_(s,CC_EP_VIDEO); flush_loss_blocking_(s,CC_EP_AUDIO);
    atomic_store(&s->backend_done,1);
    pthread_mutex_lock(&s->sig_m); pthread_cond_signal(&s->sig_c); pthread_mutex_unlock(&s->sig_m);
    return NULL;
}

// ---------------- lifecycle
int cc_open(cc_session **out, const cc_config *cfg, const cc_callbacks *cb){
    if(!out||!cfg||!cb||!cb->on_packet||!cb->on_end) return CC_ERR_ARGS;
    cc_session *s=calloc(1,sizeof *s);
    if(!s) return CC_ERR_NOMEM;
    s->cfg=*cfg; s->cb=*cb;
    s->ring_sz=(size_t)(cfg->ring_mb>0?cfg->ring_mb:256)<<20;
    s->ring=malloc(s->ring_sz);
    if(!s->ring){ free(s); return CC_ERR_NOMEM; }
    pthread_mutex_init(&s->sig_m,NULL); pthread_cond_init(&s->sig_c,NULL);
    atomic_store(&s->end_reason,CC_END_STOPPED);
    if(!cfg->replay_path){
        if(libusb_init(&s->ctx)){ free(s->ring); free(s); return CC_ERR_USB; }
        s->h=libusb_open_device_with_vid_pid(s->ctx,VID,PID);
        if(!s->h){ libusb_exit(s->ctx); free(s->ring); free(s); return CC_ERR_NODEVICE; }
        if(libusb_claim_interface(s->h,0)){ libusb_close(s->h); libusb_exit(s->ctx);
            free(s->ring); free(s); return CC_ERR_USB; }
        libusb_set_interface_alt_setting(s->h,0,1);
        libusb_set_interface_alt_setting(s->h,0,2);
        uint32_t vsel = s->cfg.input==CC_INPUT_COMPONENT?0x02000000u
                      : s->cfg.input==CC_INPUT_COMPOSITE?0x04000000u:0x06000000u;
        if(vout_(s->h,215,0,0x09000000u|vsel|0x10000000u|0x20000000u)!=4 ||
           vout_(s->h,215,24,0x73c60001u)!=4){
            // A failed/short control transfer leaves the analog mux wherever it was and every
            // downstream layer would report a healthy capture of the WRONG input.
            libusb_release_interface(s->h,0); libusb_close(s->h); libusb_exit(s->ctx);
            free(s->ring); free(s); return CC_ERR_USB;
        }
    }
    *out=s; return CC_OK;
}
int cc_start(cc_session *s){
    if(!s||atomic_load(&s->started)) return CC_ERR_STATE;
    atomic_store(&s->started,1);
    if(pthread_create(&s->delivery_t,NULL,delivery_main,s)) return CC_ERR_STATE;
    void*(*bm)(void*)=s->cfg.replay_path?replay_main:device_main;
    if(pthread_create(&s->backend_t,NULL,bm,s)) return CC_ERR_STATE;
    return CC_OK;
}
int cc_stop(cc_session *s){
    if(!s||!atomic_load(&s->started)) return CC_ERR_STATE;
    atomic_store(&s->stop_req,1);
    pthread_join(s->backend_t,NULL);
    pthread_join(s->delivery_t,NULL);
    return CC_OK;
}
void cc_close(cc_session *s){
    if(!s) return;
    if(s->h){ libusb_release_interface(s->h,0); libusb_close(s->h); }
    if(s->ctx) libusb_exit(s->ctx);
    free(s->ring); free(s);
}
void cc_get_stats(const cc_session *s, cc_stats *o){
    memset(o,0,sizeof *o);
    o->bytes[0]=s->bytes[0]; o->bytes[1]=s->bytes[1];
    o->lost_bytes[0]=s->lost_bytes[0]; o->lost_bytes[1]=s->lost_bytes[1];
    o->lost_packets[0]=s->lost_pkts[0]; o->lost_packets[1]=s->lost_pkts[1];
    o->iso_errors=s->iso_err; o->transfer_errors=s->xfer_err;
    o->resubmit_failures=s->resub_fail; o->resubmit_recovered=s->resub_rec;
    o->zero_len_packets=s->zero_pkts; o->short_packets=s->short_pkts;
    o->ring_high_water=s->r_max; o->ring_size=s->ring_sz;
    o->fleet[0]=s->fleet[0]; o->fleet[1]=s->fleet[1]; o->fleet_size=XFERS;
    o->transfers_allocated=s->xfers_alloc; o->transfers_freed=s->xfers_freed;
}
const char* cc_strerror(int e){
    switch(e){ case CC_OK:return "ok"; case CC_ERR_ARGS:return "bad arguments";
    case CC_ERR_NODEVICE:return "device not found"; case CC_ERR_USB:return "usb error";
    case CC_ERR_NOMEM:return "out of memory"; case CC_ERR_STATE:return "bad state";
    case CC_ERR_IO:return "i/o error"; default:return "unknown"; }
}

// ---------------- tpc sink
struct cc_tagged_sink { FILE *f; int io_err; };
static struct cc_tagged_sink *sink_of(void *ctx){ return ctx; }
static void snk_wr(struct cc_tagged_sink *k, const void *p, size_t n){
    if(!k->io_err && fwrite(p,1,n,k->f)!=n) k->io_err=1;
}
static void snk_packet(void *ctx, const cc_packet *p){
    struct cc_tagged_sink *k=sink_of(ctx);
    rec_hdr h={REC_MAGIC,REC_DATA,p->endpoint,p->pkt_index,p->submit_seq,
               p->status,p->req_len,p->actual_len};
    snk_wr(k,&h,sizeof h);
    if(p->actual_len) snk_wr(k,p->data,p->actual_len);
}
static void snk_loss(void *ctx, uint8_t ep, uint32_t pk, uint64_t by){
    struct cc_tagged_sink *k=sink_of(ctx);
    rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,0,0,0,pk,(uint32_t)(by>0xffffffffu?0xffffffffu:by)};
    snk_wr(k,&h,sizeof h);
}
static void snk_error(void *ctx, uint8_t ep, uint32_t seq, int st, int isf){
    struct cc_tagged_sink *k=sink_of(ctx);
    rec_hdr h={REC_MAGIC,REC_XFERERR,ep,(uint16_t)(isf?0xFFFF:0),seq,(uint32_t)st,0,0};
    snk_wr(k,&h,sizeof h);
}
static void snk_tick(void *ctx, uint32_t ms){
    struct cc_tagged_sink *k=sink_of(ctx);
    rec_hdr h={REC_MAGIC,REC_TICK,0,0,0,ms,0,0};
    snk_wr(k,&h,sizeof h);
}
static void snk_end(void *ctx, enum cc_end r){ (void)ctx; (void)r; }
int cc_tagged_sink_open(cc_tagged_sink **out, const char *path, const char *note){
    cc_tagged_sink *k=calloc(1,sizeof *k);
    if(!k) return CC_ERR_NOMEM;
    k->f=fopen(path,"wb");
    if(!k->f){ free(k); return CC_ERR_IO; }
    if(note && *note){
        rec_hdr h={REC_MAGIC,REC_SESSION,0,0,0,0,0,(uint32_t)strlen(note)};
        snk_wr(k,&h,sizeof h); snk_wr(k,note,strlen(note));
    }
    *out=k; return CC_OK;
}
void cc_tagged_sink_callbacks(cc_tagged_sink *k, cc_callbacks *o){
    memset(o,0,sizeof *o);
    o->on_packet=snk_packet; o->on_loss=snk_loss; o->on_error=snk_error;
    o->on_tick=snk_tick; o->on_end=snk_end; o->ctx=k;
}
int cc_tagged_sink_close(cc_tagged_sink *k){
    int rc = CC_OK;
    if(k->f && (k->io_err || fclose(k->f)!=0)) rc=CC_ERR_IO;
    free(k); return rc;
}
