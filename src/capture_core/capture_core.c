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
#include <errno.h>
#include <fcntl.h>
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
#define CONTROL_TERMINAL_RESERVE (sizeof(rec_hdr))

typedef struct cc_session cc_session_fwd;
typedef struct {
    struct libusb_transfer *x;
    uint8_t ep;
    uint32_t seq;
    int idx;
    int pending;
    uint64_t pending_since_ms;
    uint64_t next_retry_ms;
    struct cc_session *s;
} xinfo;

enum cc_life { CC_LIFE_OPEN, CC_LIFE_STARTING, CC_LIFE_RUNNING,
               CC_LIFE_STOPPING, CC_LIFE_STOPPED };
enum { DELIVERY_BUFFER_BYTES = 1u << 20 };

struct cc_session {
    cc_config cfg;
    cc_callbacks cb;
    // ring
    uint8_t *ring; size_t ring_sz;
    uint8_t *delivery_buffer; /* allocated by start, owned by delivery after pthread_create */
    _Atomic size_t r_head, r_tail;
    size_t r_max;
    pthread_mutex_t sig_m; pthread_cond_t sig_c;
    pthread_mutex_t life_m; pthread_cond_t life_c;
    int sig_m_init, sig_c_init, life_m_init, life_c_init;
    // threads / state machine
    pthread_t backend_t, delivery_t;
    long corrupt_spans; uint64_t corrupt_bytes;   /* replay backend thread; read after stop */
    uint64_t align_bytes;                          /* replay: walked past before the first whole video transfer */
    _Atomic int replay_paused;                     /* cc_replay_pause: the pacer holds at a transfer boundary */
    pthread_mutex_t pause_m; pthread_cond_t pause_c; int pause_init;
    _Atomic int stop_req, backend_done, started_successfully;
    _Atomic int end_reason; _Atomic int end_fired;
    _Atomic uint64_t packets_delivered; /* delivery thread, not the libusb callback */
    enum cc_life life;
    int delivery_created, backend_created;
    int startup_done, startup_rc, start_gate;
    // producer-side stats (backend thread only)
    uint64_t bytes[2]; uint64_t lost_bytes[2], lost_pkts[2];
    long iso_err, xfer_err, resub_fail, resub_rec, zero_pkts, short_pkts;
    uint32_t seq_ctr[2];
    int fleet[2];
    long xfers_alloc, xfers_freed;   // every allocated transfer must be freed by stop (no leak, no double free)
    uint64_t lost_bytes_total[2], lost_pkts_total[2];   // cumulative (pending counters reset on every flush)
    long meta_dropped;               // control records that found no ring space even inside the reserve
    int control_loss_marked;
    int teardown_incomplete;
    // usb
    libusb_context *ctx; libusb_device_handle *h;
    xinfo xs[NXF];
    _Atomic long inflight;
};

static void destroy_sync_(cc_session *s){
    if(s->pause_init){ pthread_cond_destroy(&s->pause_c); pthread_mutex_destroy(&s->pause_m); }
    if(s->life_c_init) pthread_cond_destroy(&s->life_c);
    if(s->life_m_init) pthread_mutex_destroy(&s->life_m);
    if(s->sig_c_init) pthread_cond_destroy(&s->sig_c);
    if(s->sig_m_init) pthread_mutex_destroy(&s->sig_m);
}

/* Thread identity is valid only while executing this session's internal thread.
 * A joined pthread_t may be reused by an unrelated caller. */
static _Thread_local cc_session *internal_session;
#ifdef CAPTURE_CORE_TEST_HOOKS
void cc_test_reuse_worker_ids(cc_session *s){
    /* Test caller owns a stopped session; no joins or worker reads remain. */
    s->delivery_t=s->backend_t=pthread_self();
    s->delivery_created=s->backend_created=1;
}
extern void cc_test_destroyed(void);
extern void cc_test_data_resumed(void);
extern void cc_test_after_empty_snapshot(cc_session *s);
extern void cc_test_before_backend_done(cc_session *s);
extern int cc_test_fail_delivery_allocation(size_t bytes);
extern void cc_test_ring_loss(void);
extern void cc_test_recorded_error(void);
extern void cc_test_meta_exhausted(void);
extern void cc_test_input_done(void);
extern void cc_test_packet_progress(void);
extern ssize_t cc_test_replay_read(int fd, void *buf, size_t n);
extern void cc_test_replay_prefill_wait(void);
extern void cc_test_replay_paused(uint64_t video_bytes);
#else
#define cc_test_destroyed() ((void)0)
#define cc_test_after_empty_snapshot(s) ((void)(s))
#define cc_test_before_backend_done(s) ((void)(s))
#define cc_test_fail_delivery_allocation(n) 0
#define cc_test_ring_loss() ((void)0)
#define cc_test_recorded_error() ((void)0)
#define cc_test_meta_exhausted() ((void)0)
#define cc_test_input_done() ((void)0)
#define cc_test_packet_progress() ((void)0)
#define cc_test_replay_read(fd,buf,n) read((fd),(buf),(n))
#define cc_test_replay_prefill_wait() ((void)0)
#define cc_test_replay_paused(b) ((void)(b))
#endif

static uint64_t monotonic_ms_(void){
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint64_t)t.tv_sec * 1000u + (uint64_t)t.tv_nsec / 1000000u;
}

static void startup_report_(cc_session *s, int rc){
    pthread_mutex_lock(&s->life_m);
    if (!s->startup_done){ s->startup_done = 1; s->startup_rc = rc; pthread_cond_broadcast(&s->life_c); }
    pthread_mutex_unlock(&s->life_m);
}
static int await_start_gate_(cc_session *s){
    pthread_mutex_lock(&s->life_m);
    while (!s->start_gate) pthread_cond_wait(&s->life_c, &s->life_m);
    int run = s->startup_rc == CC_OK && !atomic_load(&s->stop_req);
    pthread_mutex_unlock(&s->life_m);
    return run;
}

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
static size_t loss_record_count_(const cc_session *s, int e){
    uint64_t bn=(s->lost_bytes[e]+UINT32_MAX-1)/UINT32_MAX;
    uint64_t pn=(s->lost_pkts[e]+UINT32_MAX-1)/UINT32_MAX;
    uint64_t n=bn>pn?bn:pn;
    return (size_t)(n?n:1);
}
static void flush_loss_(cc_session *s, uint8_t ep){
    int e=ep_i(ep);
    // The record carries 32-bit counts; a blocked interval can exceed that, so emit as many
    // records as it takes rather than truncating (each record confesses what it carries).
    while(s->lost_pkts[e] && ring_free_(s)>=sizeof(rec_hdr)+CONTROL_TERMINAL_RESERVE){
        size_t chunks=loss_record_count_(s,e);
        uint32_t lb=(uint32_t)((s->lost_bytes[e]+chunks-1)/chunks);
        uint32_t lp=(uint32_t)((s->lost_pkts[e]+chunks-1)/chunks);
        rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,0,s->seq_ctr[e],0,lp,lb};
        ring_put_record_(s,&h,NULL,0);
        s->lost_pkts[e]-=lp; s->lost_bytes[e]-=lb;
        s->lost_pkts_total[e]+=lp; s->lost_bytes_total[e]+=lb;
        if(s->lost_pkts[e]==0) s->lost_bytes[e]=0;
    }
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
                "(ring never drained); loss remains in cc_stats\n",(unsigned)s->lost_pkts[e],ep);
}

// Ring space reserved for control records (HostLoss, TransferError, TICK, SESSION): DATA
// records may not consume it, so a full data ring cannot suppress the report of its own
// overflow or of a transfer error (transport truth, §8 property 1/6).
#define META_RESERVE (64u*1024u)
static void put_pkt_(cc_session *s, uint8_t ep, uint16_t pi, uint32_t seq,
                     uint32_t st, uint32_t req, const uint8_t *d, uint32_t al){
    cc_test_packet_progress();
    int e=ep_i(ep);
#ifdef CAPTURE_CORE_TEST_HOOKS
    int resuming=s->lost_pkts[e]!=0;
#endif
    size_t data_need=sizeof(rec_hdr)+(size_t)al;
    // Keep one contiguous loss run in producer state.  Only publish its compact headers when
    // the resumed DATA record and the control reserve fit as one transaction.  Eagerly writing
    // one HostLoss header per dropped packet used to consume the reserve at packet rate.
    if(s->lost_pkts[e]){
        size_t loss_need=loss_record_count_(s,e)*sizeof(rec_hdr);
        if(ring_free_(s)>=META_RESERVE+loss_need+data_need) flush_loss_(s,ep);
    }
    if(s->lost_pkts[e] || ring_free_(s)<META_RESERVE+data_need){
        s->lost_pkts[e]++; s->lost_bytes[e]+=al;
        cc_test_ring_loss(); return;   // marked on flush
    }
    rec_hdr h={REC_MAGIC,REC_DATA,ep,pi,seq,st,req,al};
    ring_put_record_(s,&h,d,al);
    wake_(s);
#ifdef CAPTURE_CORE_TEST_HOOKS
    if(resuming) cc_test_data_resumed();
#endif
}
static void put_meta_(cc_session *s, uint8_t type, uint8_t ep, uint16_t pi,
                      uint32_t seq, uint32_t st, const void *p, uint32_t plen){
    if(ring_free_(s)<sizeof(rec_hdr)+plen+CONTROL_TERMINAL_RESERVE){
        s->meta_dropped++;
        // Consume the permanently reserved final header ONCE so the saved stream itself says
        // control truth was lost. Default policy continues but is permanently not-clean;
        // fail-stop is an explicit opt-in for operators who prefer termination.
        if(!s->control_loss_marked && ring_free_(s)>=sizeof(rec_hdr)){
            rec_hdr fatal={REC_MAGIC,REC_XFERERR,ep,0xFFFE,seq,UINT32_MAX,0,0};
            ring_put_record_(s,&fatal,NULL,0); wake_(s); s->control_loss_marked=1;
        }
        if(s->cfg.fail_stop_on_control_loss){
            atomic_store(&s->end_reason,CC_END_INTERNAL_ERROR); atomic_store(&s->stop_req,1);
        }
        cc_test_meta_exhausted();
        return;
    }
    rec_hdr h={REC_MAGIC,type,ep,pi,seq,st,0,plen};
    ring_put_record_(s,&h,p,plen);
    if(type==REC_XFERERR) cc_test_recorded_error();
    wake_(s);
}

// ---------------- delivery thread: parse ring records -> user callbacks
static void* delivery_main(void *arg){
    cc_session *s=arg;
    internal_session=s;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    size_t cap=DELIVERY_BUFFER_BYTES; uint8_t *buf=s->delivery_buffer;
    s->delivery_buffer=NULL; /* Ownership handed to this thread's local buffer. */
    for(;;){
        size_t t=atomic_load_explicit(&s->r_tail,memory_order_relaxed);
        size_t h=atomic_load_explicit(&s->r_head,memory_order_acquire);
        if(h==t){
            cc_test_after_empty_snapshot(s);
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
        if(plen>cap){ cap=plen; { uint8_t *nb=realloc(buf,cap); if(!nb){ fprintf(stderr,"capture_core: delivery buffer growth failed\n"); atomic_store(&s->stop_req,1); break; } buf=nb; } }
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
            atomic_fetch_add_explicit(&s->packets_delivered,1,memory_order_relaxed);
            break; }
        case REC_HOSTLOSS:
            if(s->cb.on_loss) s->cb.on_loss(s->cb.ctx,rh.endpoint,rh.req_len,rh.actual_len);
            break;
        case REC_XFERERR:
            if(s->cb.on_error) s->cb.on_error(s->cb.ctx,rh.endpoint,rh.submit_seq,
                                              (int)rh.status,rh.pkt_index==0xFFFE?CC_ERROR_CONTROL_LOSS:
                                              (rh.pkt_index==0xFFFF?CC_ERROR_SUBMIT:CC_ERROR_TRANSFER));
            break;
        case REC_TICK:
            if(s->cb.on_tick) s->cb.on_tick(s->cb.ctx,rh.status);
            break;
        default: break; // SESSION etc: internal
        }
    }
    free(buf);
    if(atomic_load(&s->started_successfully) && !atomic_exchange(&s->end_fired,1))
        s->cb.on_end(s->cb.ctx,(enum cc_end)atomic_load(&s->end_reason));
    internal_session=NULL;
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
        xi->pending_since_ms=monotonic_ms_(); xi->next_retry_ms=xi->pending_since_ms+10;
        if(rc==LIBUSB_ERROR_NO_DEVICE){
            atomic_store(&s->end_reason,CC_END_DEVICE_GONE); atomic_store(&s->stop_req,1);
        }
        return;
    }
    free(x->buffer); libusb_free_transfer(x); s->xs[xi->idx].x=NULL; s->xfers_freed++;
}
static int vout_(libusb_device_handle*h,uint8_t req,uint16_t idx,uint32_t be){
    uint8_t b[4]={(uint8_t)(be>>24),(uint8_t)(be>>16),(uint8_t)(be>>8),(uint8_t)be};
    return libusb_control_transfer(h,0x40,req,0,idx,b,4,1000);
}
int cc_debug_register(cc_session *s, int write, uint16_t index, uint32_t *value){
    if(!s || !value || !s->h || s->cfg.replay_path || index>56 || index%4) return CC_ERR_ARGS;
    if(write){
        if(index!=4 && index!=8 && index!=28 && index!=32) return CC_ERR_ARGS;
        return vout_(s->h,215,index,*value)==4?CC_OK:CC_ERR_USB;
    }
    uint8_t b[4];
    if(libusb_control_transfer(s->h,0xc0,214,0,index,b,4,1000)!=4) return CC_ERR_USB;
    *value=(uint32_t)b[0]<<24|(uint32_t)b[1]<<16|(uint32_t)b[2]<<8|b[3];
    return CC_OK;
}
int cc_debug_relatch(cc_session *s, int with_mode){
    if(!s || !s->h || s->cfg.replay_path) return CC_ERR_ARGS;
    uint32_t vsel = s->cfg.input==CC_INPUT_COMPONENT?0x02000000u
                  : s->cfg.input==CC_INPUT_COMPOSITE?0x04000000u:0x06000000u;
    if(with_mode && vout_(s->h,215,0,0x09000000u|vsel|0x10000000u|0x20000000u)!=4) return CC_ERR_USB;
    return vout_(s->h,215,24,0x73c60001u)==4?CC_OK:CC_ERR_USB;
}
static void* device_main(void *arg){
    cc_session *s=arg;
    internal_session=s;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    char note[192];
    snprintf(note,sizeof note,"capture_core v1 input=%d ring=%zuMB V_NPK=%d XFERS=%d",
             s->cfg.input,s->ring_sz>>20,V_NPK,XFERS);
    put_meta_(s,REC_SESSION,0,0,0,0,note,(uint32_t)strlen(note));
    int n=0, startup_rc=CC_OK;
    for(int w=0;w<2;w++){
        uint8_t ep=w?CC_EP_AUDIO:CC_EP_VIDEO; int npk=w?A_NPK:V_NPK, pkt=w?A_PKT:V_PKT;
        for(int i=0;i<XFERS;i++,n++){
            uint8_t *buf=malloc((size_t)npk*pkt);
            struct libusb_transfer *x=libusb_alloc_transfer(npk);
            if(!buf || !x){ free(buf); if(x) libusb_free_transfer(x); startup_rc=CC_ERR_NOMEM; goto startup_failed; }
            s->xfers_alloc++;
            s->xs[n]=(xinfo){.x=x,.ep=ep,.seq=s->seq_ctr[w]++,.idx=n,.s=s};
            libusb_fill_iso_transfer(x,s->h,ep,buf,npk*pkt,npk,usb_cb,&s->xs[n],0);
            libusb_set_iso_packet_lengths(x,pkt);
            int rc=libusb_submit_transfer(x);
            if(rc==0) atomic_fetch_add(&s->inflight,1);
            else { s->xfer_err++; s->resub_fail++;
                put_meta_(s,REC_XFERERR,ep,0xFFFF,s->xs[n].seq,(uint32_t)(-rc),NULL,0);
                s->xs[n].pending=1; // never submitted: teardown frees directly, never waits for a cancel callback
                startup_rc=(rc==LIBUSB_ERROR_NO_DEVICE)?CC_ERR_NODEVICE:CC_ERR_USB; goto startup_failed; }
        }
    }
    startup_report_(s,CC_OK);
    if(!await_start_gate_(s)) goto stopping;
    struct timespec t0; clock_gettime(CLOCK_MONOTONIC,&t0);
    uint32_t last_tick=0;
    struct timeval tv={0,100000};
    while(!atomic_load(&s->stop_req)){
        libusb_handle_events_timeout(s->ctx,&tv);
        int pending=0;
        for(int i=0;i<NXF;i++) if(s->xs[i].x && s->xs[i].pending){
            pending=1; uint64_t now=monotonic_ms_(); if(now<s->xs[i].next_retry_ms) continue;
            int rc=libusb_submit_transfer(s->xs[i].x);
            if(rc==0){ s->xs[i].pending=0; atomic_fetch_add(&s->inflight,1); s->resub_rec++; continue; }
            s->resub_fail++; s->xs[i].next_retry_ms=now+10;
            int deadline=s->cfg.resubmit_deadline_ms>0?s->cfg.resubmit_deadline_ms:2000;
            if(rc==LIBUSB_ERROR_NO_DEVICE || now-s->xs[i].pending_since_ms>=(uint64_t)deadline){
                put_meta_(s,REC_XFERERR,s->xs[i].ep,0xFFFF,s->xs[i].seq,(uint32_t)(-rc),NULL,0);
                atomic_store(&s->end_reason,rc==LIBUSB_ERROR_NO_DEVICE?CC_END_DEVICE_GONE:CC_END_TRANSFER_FAILED);
                atomic_store(&s->stop_req,1); break;
            }
        }
        if(pending) usleep(1000); // shim and pathological backends may return immediately
        struct timespec tn; clock_gettime(CLOCK_MONOTONIC,&tn);
        uint32_t ms=(uint32_t)((tn.tv_sec-t0.tv_sec)*1000+(tn.tv_nsec-t0.tv_nsec)/1000000);
        if(ms-last_tick>=1000){ last_tick=ms; put_meta_(s,REC_TICK,0,0,0,ms,NULL,0); }
    }
stopping:
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
    if(atomic_load(&s->inflight)>0){
        s->teardown_incomplete=1;
        fprintf(stderr,"capture_core: %ld transfers still in flight after cancellation drain\n",(long)atomic_load(&s->inflight));
    }
    cc_test_input_done();
    flush_loss_blocking_(s,CC_EP_VIDEO); flush_loss_blocking_(s,CC_EP_AUDIO);
    cc_test_before_backend_done(s);
    atomic_store_explicit(&s->backend_done,1,memory_order_release); wake_(s);
    pthread_mutex_lock(&s->sig_m); pthread_cond_signal(&s->sig_c); pthread_mutex_unlock(&s->sig_m);
    internal_session=NULL;
    return NULL;
startup_failed:
    atomic_store(&s->end_reason,startup_rc==CC_ERR_NODEVICE?CC_END_DEVICE_GONE:CC_END_INTERNAL_ERROR);
    atomic_store(&s->stop_req,1); startup_report_(s,startup_rc);
    pthread_mutex_lock(&s->life_m); while(!s->start_gate) pthread_cond_wait(&s->life_c,&s->life_m); pthread_mutex_unlock(&s->life_m);
    goto stopping;
}

// ---------------- replay backend
/* Read-ahead: a reader thread fills a byte ring from the .tpc; the pacer takes records from it.
 * Before this the pacer read with fread on its own thread, so every slow read on a network volume
 * delayed delivery directly (2026-09-28, 10 min off LucidLink: 3 handoff gaps over 83 ms, worst
 * 155.1 ms, all waiting on the file). Single producer (reader), single consumer (pacer). */
/* Stall diagnosis (cfg.replay_diag): the worst few events of each kind, by duration. */
#define RD_TOP 8
typedef struct { uint64_t us, at_ms, off; } rd_event;
typedef struct { rd_event ev[RD_TOP]; uint64_t n, total_us; } rd_list;
static void rd_note_(rd_list *l, uint64_t us, uint64_t at_ms, uint64_t off){
    l->n++; l->total_us+=us;
    int k=RD_TOP-1; if(us<=l->ev[k].us) return;
    while(k>0 && l->ev[k-1].us<us){ l->ev[k]=l->ev[k-1]; k--; }
    l->ev[k]=(rd_event){us,at_ms,off};
}
static uint64_t rd_now_us_(void){ return clock_gettime_nsec_np(CLOCK_UPTIME_RAW)/1000; }
typedef struct {
    int fd; uint8_t *ring; size_t cap, chunk, prefill;
    uint64_t base;                           /* file offset the reader started at; head/tail are file offsets */
    rd_list slow_reads;                      /* reader: reads over 50 ms (reader thread only) */
    _Atomic uint64_t t0_us;                  /* set by the pacer when pacing starts; 0 before */
    _Atomic uint64_t head, tail;            /* bytes read / bytes consumed, monotonic */
    _Atomic int eof, err, stop;             /* err: errno of a failed read */
    pthread_mutex_t m; pthread_cond_t cv;   /* sleep/wake only; both directions share it */
    pthread_t thr;
} replay_reader;
static void rr_wake_(replay_reader *r){ pthread_mutex_lock(&r->m); pthread_cond_broadcast(&r->cv); pthread_mutex_unlock(&r->m); }
static void rr_wait_(replay_reader *r, int (*ready)(replay_reader *)){
    pthread_mutex_lock(&r->m);
    if(!ready(r)){
        struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts); ts.tv_nsec+=100000000;
        if(ts.tv_nsec>=1000000000){ ts.tv_sec++; ts.tv_nsec-=1000000000; }
        pthread_cond_timedwait(&r->cv,&r->m,&ts);   /* liveness backstop only; the other side signals */
    }
    pthread_mutex_unlock(&r->m);
}
static int rr_has_space_(replay_reader *r){
    return atomic_load(&r->stop) || r->cap-(atomic_load(&r->head)-atomic_load(&r->tail))>=r->chunk;
}
static void *rr_main_(void *arg){
    replay_reader *r=arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    while(!atomic_load(&r->stop)){
        uint64_t head=atomic_load_explicit(&r->head,memory_order_relaxed);
        size_t space=r->cap-(size_t)(head-atomic_load_explicit(&r->tail,memory_order_acquire));
        if(space<r->chunk){ rr_wait_(r,rr_has_space_); continue; }
        size_t o=(size_t)(head%r->cap), n=r->chunk;
        if(n>r->cap-o) n=r->cap-o;
        uint64_t rs=rd_now_us_();
        ssize_t got=cc_test_replay_read(r->fd,r->ring+o,n);
        uint64_t rt=rd_now_us_()-rs;
        uint64_t t0=atomic_load(&r->t0_us);
        if(rt>50000) rd_note_(&r->slow_reads,rt,t0&&rs>t0?(rs-t0)/1000:0,head);
        if(got<0 && errno==EINTR) continue;
        if(got<0){ atomic_store(&r->err,errno?errno:EIO); rr_wake_(r); break; }
        if(got==0){ atomic_store(&r->eof,1); rr_wake_(r); break; }
        atomic_store_explicit(&r->head,head+(uint64_t)got,memory_order_release);
        rr_wake_(r);
    }
    return NULL;
}
static int rr_prefilled_(replay_reader *r){
    return atomic_load(&r->eof) || atomic_load(&r->err) || atomic_load(&r->head)-r->base>=r->prefill;
}
static int rr_has_data_(replay_reader *r){
    return atomic_load(&r->eof) || atomic_load(&r->err) || atomic_load(&r->head)!=atomic_load(&r->tail);
}
/* fread-like: n bytes, fewer only at end of file or on a read error; -1 when stop is requested.
 * Diagnosis (pacer thread only): each wait on an empty ring, and the lowest fill once pacing runs. */
static ssize_t rr_read_diag_(replay_reader *r, cc_session *s, void *dst, size_t n, rd_list *waits, uint64_t *min_fill){
    size_t done=0;
    while(done<n){
        uint64_t tail=atomic_load_explicit(&r->tail,memory_order_relaxed);
        size_t avail=(size_t)(atomic_load_explicit(&r->head,memory_order_acquire)-tail);
        uint64_t t0=atomic_load(&r->t0_us);
        if(min_fill && t0 && !atomic_load(&r->eof) && avail<*min_fill) *min_fill=avail;   /* the end of the file drains it by design */
        if(!avail){
            if(atomic_load(&r->eof)||atomic_load(&r->err)) break;
            if(atomic_load(&s->stop_req)) return -1;
            uint64_t ws=rd_now_us_();
            rr_wait_(r,rr_has_data_);
            if(waits && t0) rd_note_(waits,rd_now_us_()-ws,(ws-t0)/1000,tail);
            continue;
        }
        size_t k=n-done<avail?n-done:avail, o=(size_t)(tail%r->cap);
        if(k>r->cap-o) k=r->cap-o;
        memcpy((uint8_t*)dst+done,r->ring+o,k); done+=k;
        atomic_store_explicit(&r->tail,tail+(uint64_t)k,memory_order_release);
        rr_wake_(r);
    }
    return (ssize_t)done;
}
#define rr_read_(r,s,dst,n) rr_read_diag_((r),(s),(dst),(n),&empty_waits,&min_fill)
static void rd_emit_(const cc_session *s, const char *line){
    if(s->cfg.diag_log) s->cfg.diag_log(s->cfg.diag_ctx,line); else fprintf(stderr,"%s\n",line);
}
static void rd_print_(const cc_session *s, const char *what, const rd_list *l){
    char line[1024]; int n=snprintf(line,sizeof line,"capture_core replay diag: %s: %llu, total %.1f ms",what,(unsigned long long)l->n,l->total_us/1000.0);
    for(int k=0;k<RD_TOP && l->ev[k].us && n>0 && (size_t)n<sizeof line;k++)
        n+=snprintf(line+n,sizeof line-(size_t)n,"%s%.1f ms @%.2fs (offset %.2f GB)",k?", ":"; worst ",l->ev[k].us/1000.0,l->ev[k].at_ms/1000.0,l->ev[k].off/1e9);
    rd_emit_(s,line);
}
/* A header the capture writer could have produced. A garbage header can carry the magic by chance,
 * so the fields are checked too before any payload length is trusted. */
static int rec_plausible_(const rec_hdr *h){
    if(h->magic!=REC_MAGIC || h->type>REC_TICK) return 0;
    if(h->type==REC_DATA) return (h->endpoint==CC_EP_VIDEO||h->endpoint==CC_EP_AUDIO) && h->actual_len<=h->req_len && h->req_len<=65536;
    if(h->type==REC_SESSION) return h->actual_len<=(1u<<20);
    return 1;
}
#define REPLAY_MAX_SKIP ((uint64_t)256<<20)
/* Paused pacer's liveness backstop. Test builds wait 10 s, so a stop-while-paused test that returns
 * promptly proves cc_stop's own wake-up rather than the backstop. */
#ifdef CAPTURE_CORE_TEST_HOOKS
#define PAUSE_BACKSTOP_S 10
#define PAUSE_BACKSTOP_NS 0
#else
#define PAUSE_BACKSTOP_S 0
#define PAUSE_BACKSTOP_NS 100000000
#endif
static int rr_start_(replay_reader *r, const char *path, size_t cap, uint64_t offset){
    memset(r,0,sizeof *r);
    r->fd=open(path,O_RDONLY); if(r->fd<0) return CC_ERR_IO;
    if(offset && lseek(r->fd,(off_t)offset,SEEK_SET)!=(off_t)offset){ close(r->fd); return CC_ERR_IO; }
    r->base=offset; atomic_store(&r->head,offset); atomic_store(&r->tail,offset);   /* ring index = offset % cap on both sides */
    r->cap=cap; r->chunk=cap/4<(4u<<20)?cap/4:(4u<<20);   /* at most 4 MiB per read */
    r->prefill=cap/2;   /* delivery starts once half the ring is read (or the file ended) */
    r->ring=malloc(cap);
    if(!r->ring){ close(r->fd); return CC_ERR_NOMEM; }
    pthread_mutex_init(&r->m,NULL); pthread_cond_init(&r->cv,NULL);
    if(pthread_create(&r->thr,NULL,rr_main_,r)!=0){ pthread_mutex_destroy(&r->m); pthread_cond_destroy(&r->cv); free(r->ring); close(r->fd); return CC_ERR_NOMEM; }
    return CC_OK;
}
static int rr_finish_(replay_reader *r){   /* stops and joins the reader; returns its read errno, 0 if none */
    atomic_store(&r->stop,1); rr_wake_(r); pthread_join(r->thr,NULL);
    int e=atomic_load(&r->err);
    pthread_mutex_destroy(&r->m); pthread_cond_destroy(&r->cv); free(r->ring); close(r->fd);
    return e;
}
static void* replay_main(void *arg){
    cc_session *s=arg;
    internal_session=s;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    replay_reader rd, *f=&rd;
    rd_list empty_waits={0}, oversleeps={0}; uint64_t min_fill=UINT64_MAX;
    int rr=rr_start_(f,s->cfg.replay_path,(size_t)(s->cfg.replay_readahead_mb>0?s->cfg.replay_readahead_mb:CC_DEFAULT_READAHEAD_MB)<<20,s->cfg.replay_start_offset);
    if(rr!=CC_OK){ atomic_store(&s->end_reason,CC_END_INTERNAL_ERROR); startup_report_(s,rr); goto failed_start; }
    uint8_t *pay=malloc(1u<<20); size_t cap=1u<<20;
    if(!pay){ rr_finish_(f); atomic_store(&s->end_reason,CC_END_INTERNAL_ERROR); startup_report_(s,CC_ERR_NOMEM); goto failed_start; }
    startup_report_(s,CC_OK);
    if(!await_start_gate_(s)){ free(pay); rr_finish_(f); goto done; }
    /* Prefill before pacing: a cold start on a network volume read slower than real time for its first
     * seconds and the pacer, already running, delivered in bursts (2026-09-29, first read-ahead run:
     * gaps of 860/684/658/246 ms in the first 5 s, none over 75 ms after). The pace clock starts after. */
    while(!atomic_load(&s->stop_req) && !rr_prefilled_(f)){ cc_test_replay_prefill_wait(); rr_wait_(f,rr_prefilled_); }
    int fill[2]={0,0};   // packets since last transfer boundary, for pacing
    // Pacing is deadline-based: the n-th video transfer boundary is due at t0 + n*pace. Sleeping a
    // fixed interval per transfer ADDS the parser's own work to each period (measured: a "realtime"
    // replay ran 28% slow, starving a live audio mixer); sleeping until the deadline does not.
    struct timespec pace_t0; clock_gettime(CLOCK_MONOTONIC,&pace_t0); uint64_t paced_transfers=0;
    atomic_store(&f->t0_us,rd_now_us_());
    /* A start offset lands anywhere, usually inside a payload: slide to a valid record, then pass
     * over records until one begins a whole video transfer. A transfer is a group of consecutive
     * packets written together, so from there on both endpoints begin on whole transfers too. */
    /* The landing scan is bounded by one largest record (header + 64 KiB payload): a valid record must
     * begin within it. A longer implausible stretch is damage, and takes the loud corrupt-span path below
     * like any other, so a seek next to a damaged stretch never hides it as alignment. */
    int aligning=s->cfg.replay_start_offset>0, landing=aligning;
    while(!atomic_load(&s->stop_req)){
        rec_hdr h; uint64_t carried=0;   /* a failed landing scan's bytes belong to the corrupt span that follows */
        if(rr_read_(f,s,&h,sizeof h)!=(ssize_t)sizeof h) break;
        if(landing){
            landing=0; uint64_t n=0;
            for(; !rec_plausible_(&h) && n<(uint64_t)sizeof h+65536 && !atomic_load(&s->stop_req); n++){
                memmove(&h,(uint8_t*)&h+1,sizeof h-1);
                if(rr_read_(f,s,(uint8_t*)&h+sizeof h-1,1)!=1) break;
            }
            if(atomic_load(&s->stop_req)) break;
            if(rec_plausible_(&h)) s->align_bytes+=n; else carried=n;
        }
        if(!rec_plausible_(&h)){
            /* Corrupt stretch: slide byte by byte to the next valid record and say so. This used to end
             * the replay as a clean end of file (2026-09-29: a render lost its last 2:19 to 6.3 MB of
             * damage 3.4 GB before the end). Packets lost inside it surface downstream as holes. */
            uint64_t at=atomic_load(&f->tail)-sizeof h-carried, skipped=carried; int found=0;
            while(skipped<REPLAY_MAX_SKIP && !atomic_load(&s->stop_req)){
                memmove(&h,(uint8_t*)&h+1,sizeof h-1);
                if(rr_read_(f,s,(uint8_t*)&h+sizeof h-1,1)!=1) break;
                skipped++;
                if(rec_plausible_(&h)){ found=1; break; }
            }
            if(!found && atomic_load(&s->stop_req)) break;   /* stopped mid-scan: not an end of data */
            s->corrupt_spans++; s->corrupt_bytes+=skipped;
            char line[200];
            snprintf(line,sizeof line,"capture_core replay: skipped %llu unparseable bytes at file offset %llu%s",
                     (unsigned long long)skipped,(unsigned long long)at,found?"":" (no valid record after it: ending)");
            rd_emit_(s,line);
            if(!found) break;
        }
        size_t plen=(h.type==REC_DATA||h.type==REC_SESSION)?h.actual_len:0;
        if(plen>cap){ uint8_t *np=realloc(pay,plen); if(!np){ atomic_store(&s->end_reason,CC_END_INTERNAL_ERROR); break; } pay=np; cap=plen; }
        if(plen && rr_read_(f,s,pay,plen)!=(ssize_t)plen) break;
        if(aligning){
            if(h.type==REC_DATA && h.endpoint==CC_EP_VIDEO && h.pkt_index==0) aligning=0;
            else { s->align_bytes+=sizeof h+plen; continue; }
        }
        switch(h.type){
        case REC_DATA: {
            int e=ep_i(h.endpoint);
            // deliver with the ORIGINAL tags; backpressure via ring, honestly
            put_pkt_(s,h.endpoint,h.pkt_index,h.submit_seq,h.status,h.req_len,pay,h.actual_len);
            s->bytes[e]+=h.actual_len;
            if(h.actual_len==0) s->zero_pkts++; else if(h.actual_len<h.req_len) s->short_pkts++;
            int npk = e ? A_NPK : V_NPK;
            if(++fill[e]>=npk){ fill[e]=0;
                if(s->cfg.replay_pace_us>0 && e==0){
                    paced_transfers++;
                    struct timespec now; clock_gettime(CLOCK_MONOTONIC,&now);
                    int64_t elapsed_us=(int64_t)(now.tv_sec-pace_t0.tv_sec)*1000000+(now.tv_nsec-pace_t0.tv_nsec)/1000;
                    int64_t due_us=(int64_t)paced_transfers*s->cfg.replay_pace_us;
                    /* Preserve pacing, but allow stop to interrupt even a very long interval. */
                    int slept=0;
                    while(due_us>elapsed_us && !atomic_load(&s->stop_req)) {
                        int64_t left=due_us-elapsed_us;
                        usleep((useconds_t)(left>20000?20000:left)); slept=1;
                        clock_gettime(CLOCK_MONOTONIC,&now);
                        elapsed_us=(int64_t)(now.tv_sec-pace_t0.tv_sec)*1000000+(now.tv_nsec-pace_t0.tv_nsec)/1000;
                    }
                    /* a wake-up more than 20 ms past its deadline: the pacer was not scheduled in time */
                    if(slept && elapsed_us-due_us>20000) rd_note_(&oversleeps,(uint64_t)(elapsed_us-due_us),(uint64_t)due_us/1000,atomic_load(&f->tail));
                }
                if(e==0 && atomic_load(&s->replay_paused)){
                    /* Held after a whole video transfer. Pacing resumes from the resume time: the pause is
                     * added to the pace origin, so the next deadline is one period after resuming. */
                    struct timespec p0,p1; clock_gettime(CLOCK_MONOTONIC,&p0);
                    pthread_mutex_lock(&s->pause_m);
                    int told=0;
                    while(atomic_load(&s->replay_paused) && !atomic_load(&s->stop_req)){
                        /* test hook, under pause_m after the check: a stop signalled after it can only land once
                         * this thread waits, so a prompt stop proves the broadcast, not a lucky early check */
                        if(!told){ told=1; cc_test_replay_paused(s->bytes[0]); }
                        struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts); ts.tv_sec+=PAUSE_BACKSTOP_S; ts.tv_nsec+=PAUSE_BACKSTOP_NS;
                        if(ts.tv_nsec>=1000000000){ ts.tv_sec++; ts.tv_nsec-=1000000000; }
                        pthread_cond_timedwait(&s->pause_c,&s->pause_m,&ts);   /* liveness backstop: internal stop paths set stop_req without signalling */
                    }
                    pthread_mutex_unlock(&s->pause_m);
                    clock_gettime(CLOCK_MONOTONIC,&p1);
                    int64_t held_ns=(int64_t)(p1.tv_sec-p0.tv_sec)*1000000000+(p1.tv_nsec-p0.tv_nsec);
                    int64_t t0_ns=(int64_t)pace_t0.tv_nsec+held_ns;
                    pace_t0.tv_sec+=(time_t)(t0_ns/1000000000); pace_t0.tv_nsec=(long)(t0_ns%1000000000);
                } }
            break; }
        case REC_TICK: put_meta_(s,REC_TICK,0,0,0,h.status,NULL,0); break;
        case REC_XFERERR: put_meta_(s,REC_XFERERR,h.endpoint,h.pkt_index,h.submit_seq,h.status,NULL,0); break;
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
    free(pay);
    if(s->cfg.replay_diag){
        rd_print_(s,"pacer waited on an empty read-ahead ring (file too slow)",&empty_waits);
        rd_print_(s,"reads over 50 ms",&f->slow_reads);
        rd_print_(s,"pacer woke over 20 ms late",&oversleeps);
        char line[160]; snprintf(line,sizeof line,"capture_core replay diag: lowest read-ahead fill while pacing: %.1f MiB of %.0f",min_fill==UINT64_MAX?-1.0:min_fill/1048576.0,f->cap/1048576.0);
        rd_emit_(s,line);
    }
    int read_err=rr_finish_(f);
    if(read_err && !atomic_load(&s->stop_req)){
        fprintf(stderr,"capture_core: replay read failed: %s\n",strerror(read_err));
        atomic_store(&s->end_reason,CC_END_INTERNAL_ERROR);   /* named: a failed read is not the end of the file */
    }
    if(atomic_load(&s->end_reason)==CC_END_STOPPED && !atomic_load(&s->stop_req))
        atomic_store(&s->end_reason,CC_END_REPLAY_EOF);
done:
    cc_test_input_done();
    flush_loss_blocking_(s,CC_EP_VIDEO); flush_loss_blocking_(s,CC_EP_AUDIO);
    cc_test_before_backend_done(s);
    atomic_store_explicit(&s->backend_done,1,memory_order_release);
    pthread_mutex_lock(&s->sig_m); pthread_cond_signal(&s->sig_c); pthread_mutex_unlock(&s->sig_m);
    internal_session=NULL;
    return NULL;
failed_start:
    pthread_mutex_lock(&s->life_m); while(!s->start_gate) pthread_cond_wait(&s->life_c,&s->life_m); pthread_mutex_unlock(&s->life_m);
    goto done;
}

// ---------------- lifecycle
int cc_open(cc_session **out, const cc_config *cfg, const cc_callbacks *cb){
    if(!out||!cfg||!cb||!cb->on_packet||!cb->on_end) return CC_ERR_ARGS;
    if(!cfg->replay_path && cfg->input!=CC_INPUT_SVIDEO && cfg->input!=CC_INPUT_COMPONENT &&
       cfg->input!=CC_INPUT_COMPOSITE) return CC_ERR_ARGS;   // never silently map junk to S-video
    cc_session *s=calloc(1,sizeof *s);
    if(!s) return CC_ERR_NOMEM;
    s->cfg=*cfg; s->cb=*cb;
    if(pthread_mutex_init(&s->sig_m,NULL)) goto sync_fail;
    s->sig_m_init=1;
    if(pthread_cond_init(&s->sig_c,NULL)) goto sync_fail;
    s->sig_c_init=1;
    if(pthread_mutex_init(&s->life_m,NULL)) goto sync_fail;
    s->life_m_init=1;
    if(pthread_cond_init(&s->life_c,NULL)) goto sync_fail;
    s->life_c_init=1;
    if(pthread_mutex_init(&s->pause_m,NULL)) goto sync_fail;
    if(pthread_cond_init(&s->pause_c,NULL)){ pthread_mutex_destroy(&s->pause_m); goto sync_fail; }
    s->pause_init=1;
    s->life=CC_LIFE_OPEN;
    s->ring_sz=(size_t)(cfg->ring_mb>0?cfg->ring_mb:CC_DEFAULT_RING_MB)<<20;
    s->ring=malloc(s->ring_sz);
    if(!s->ring) goto nomem;
    atomic_store(&s->end_reason,CC_END_STOPPED);
    if(!cfg->replay_path){
        if(libusb_init(&s->ctx)) goto usb_fail;
        s->h=libusb_open_device_with_vid_pid(s->ctx,VID,PID);
        if(!s->h) goto nodevice;
        if(libusb_claim_interface(s->h,0)) goto usb_fail;
        // alt1 -> alt2 is the reset + input select (§5); an unchecked failure here streams nothing
        // or streams the previous state, so every lifecycle transition must be confirmed.
        if(libusb_set_interface_alt_setting(s->h,0,1) || libusb_set_interface_alt_setting(s->h,0,2)){
            goto usb_fail;
        }
        uint32_t vsel = s->cfg.input==CC_INPUT_COMPONENT?0x02000000u
                      : s->cfg.input==CC_INPUT_COMPOSITE?0x04000000u:0x06000000u;
        if(vout_(s->h,215,0,0x09000000u|vsel|0x10000000u|0x20000000u)!=4 ||
           vout_(s->h,215,24,0x73c60001u)!=4){
            // A failed/short control transfer leaves the analog mux wherever it was and every
            // downstream layer would report a healthy capture of the WRONG input.
            goto usb_fail;
        }
    }
    *out=s; return CC_OK;
nodevice:
    if(s->ctx) libusb_exit(s->ctx); s->ctx=NULL;
    destroy_sync_(s); free(s->ring); free(s);
    return CC_ERR_NODEVICE;
usb_fail:
    if(s->h){ libusb_release_interface(s->h,0); libusb_close(s->h); }
    if(s->ctx) libusb_exit(s->ctx);
    destroy_sync_(s); free(s->ring); free(s);
    return CC_ERR_USB;
nomem:
    destroy_sync_(s); free(s); return CC_ERR_NOMEM;
sync_fail:
    destroy_sync_(s); free(s); return CC_ERR_STATE;
}
int cc_start(cc_session *s){
    if(!s) return CC_ERR_STATE;
    pthread_mutex_lock(&s->life_m);
    if(s->life!=CC_LIFE_OPEN){ pthread_mutex_unlock(&s->life_m); return CC_ERR_STATE; }
    s->life=CC_LIFE_STARTING; pthread_mutex_unlock(&s->life_m);
    /* Establish the consumer before the backend can report success. Only the backend
     * now reports startup: allocation failure cannot lose a first-report-wins race. */
    int failure=CC_ERR_STATE;
    s->delivery_buffer=cc_test_fail_delivery_allocation(DELIVERY_BUFFER_BYTES)?NULL:malloc(DELIVERY_BUFFER_BYTES);
    if(!s->delivery_buffer){
        fprintf(stderr,"capture_core: delivery buffer allocation failed\n");
        failure=CC_ERR_NOMEM; goto thread_fail;
    }
    if(pthread_create(&s->delivery_t,NULL,delivery_main,s)) {
        free(s->delivery_buffer); s->delivery_buffer=NULL; goto thread_fail;
    }
    s->delivery_created=1;
    void*(*bm)(void*)=s->cfg.replay_path?replay_main:device_main;
    if(pthread_create(&s->backend_t,NULL,bm,s)){
        atomic_store(&s->backend_done,1); wake_(s); pthread_join(s->delivery_t,NULL);
        goto thread_fail;
    }
    s->backend_created=1;
    pthread_mutex_lock(&s->life_m);
    while(!s->startup_done) pthread_cond_wait(&s->life_c,&s->life_m);
    int rc=s->startup_rc;
    if(rc==CC_OK){ atomic_store(&s->started_successfully,1); s->life=CC_LIFE_RUNNING; }
    else { atomic_store(&s->stop_req,1); s->life=CC_LIFE_STOPPING; }
    s->start_gate=1; pthread_cond_broadcast(&s->life_c); pthread_mutex_unlock(&s->life_m);
    if(rc==CC_OK) return CC_OK;
    pthread_join(s->backend_t,NULL); pthread_join(s->delivery_t,NULL);
    pthread_mutex_lock(&s->life_m); s->life=CC_LIFE_STOPPED; pthread_cond_broadcast(&s->life_c); pthread_mutex_unlock(&s->life_m);
    return rc;
thread_fail:
    pthread_mutex_lock(&s->life_m); s->life=CC_LIFE_STOPPED; pthread_cond_broadcast(&s->life_c); pthread_mutex_unlock(&s->life_m);
    return failure;
}
int cc_stop(cc_session *s){
    if(!s) return CC_ERR_STATE;
    if(internal_session==s) return CC_ERR_STATE;
    pthread_mutex_lock(&s->life_m);
    while(s->life==CC_LIFE_STOPPING) pthread_cond_wait(&s->life_c,&s->life_m);
    if(s->life==CC_LIFE_STOPPED){ pthread_mutex_unlock(&s->life_m); return CC_OK; }
    if(s->life!=CC_LIFE_RUNNING){ pthread_mutex_unlock(&s->life_m); return CC_ERR_STATE; }
    s->life=CC_LIFE_STOPPING; pthread_mutex_unlock(&s->life_m);
    atomic_store(&s->stop_req,1);
    pthread_mutex_lock(&s->pause_m); pthread_cond_broadcast(&s->pause_c); pthread_mutex_unlock(&s->pause_m);   /* a paused pacer wakes now */
    pthread_join(s->backend_t,NULL);
    pthread_join(s->delivery_t,NULL);
    pthread_mutex_lock(&s->life_m); s->life=CC_LIFE_STOPPED; pthread_cond_broadcast(&s->life_c); pthread_mutex_unlock(&s->life_m);
    return CC_OK;
}
void cc_close(cc_session *s){
    if(!s) return;
    if(internal_session==s){
        fprintf(stderr,"capture_core: close from internal callback is forbidden; session retained\n"); return;
    }
    pthread_mutex_lock(&s->life_m); enum cc_life life=s->life; pthread_mutex_unlock(&s->life_m);
    if(life==CC_LIFE_RUNNING || life==CC_LIFE_STOPPING) cc_stop(s);
    if(s->teardown_incomplete){
        // libusb never proved quiescence: a late callback would touch freed state. Leak the
        // session deliberately and say so; a silent use-after-free is the worse outcome.
        fprintf(stderr,"capture_core: teardown incomplete (transfers still in flight); session leaked deliberately\n");
        return;
    }
    if(s->h){ libusb_release_interface(s->h,0); libusb_close(s->h); }
    if(s->ctx) libusb_exit(s->ctx);
    destroy_sync_(s);
    cc_test_destroyed();
    free(s->ring); free(s);
}
void cc_get_stats(const cc_session *s, cc_stats *o){
    memset(o,0,sizeof *o);
    o->bytes[0]=s->bytes[0]; o->bytes[1]=s->bytes[1];
    // cumulative confessed loss plus anything still pending (unflushed) at the time of the call
    o->lost_bytes[0]=s->lost_bytes_total[0]+s->lost_bytes[0]; o->lost_bytes[1]=s->lost_bytes_total[1]+s->lost_bytes[1];
    o->lost_packets[0]=s->lost_pkts_total[0]+s->lost_pkts[0]; o->lost_packets[1]=s->lost_pkts_total[1]+s->lost_pkts[1];
    o->control_records_dropped=s->meta_dropped;
    o->control_loss_markers=s->control_loss_marked;
    o->teardown_incomplete=s->teardown_incomplete;
    o->iso_errors=s->iso_err; o->transfer_errors=s->xfer_err;
    o->resubmit_failures=s->resub_fail; o->resubmit_recovered=s->resub_rec;
    o->zero_len_packets=s->zero_pkts; o->short_packets=s->short_pkts;
    o->ring_high_water=s->r_max; o->ring_size=s->ring_sz;
    o->fleet[0]=s->fleet[0]; o->fleet[1]=s->fleet[1]; o->fleet_size=XFERS;
    o->transfers_allocated=s->xfers_alloc; o->transfers_freed=s->xfers_freed;
    o->replay_corrupt_spans=s->corrupt_spans; o->replay_corrupt_bytes=s->corrupt_bytes;
    o->replay_align_bytes=s->align_bytes;
}
int cc_replay_pause(cc_session *s, int paused){
    if(!s || !s->cfg.replay_path) return CC_ERR_STATE;
    pthread_mutex_lock(&s->pause_m);
    atomic_store(&s->replay_paused,paused?1:0);
    pthread_cond_broadcast(&s->pause_c);
    pthread_mutex_unlock(&s->pause_m);
    return CC_OK;
}
uint64_t cc_packets_delivered(const cc_session *s){
    return atomic_load_explicit(&s->packets_delivered,memory_order_relaxed);
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
static void snk_error(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){
    struct cc_tagged_sink *k=sink_of(ctx);
    uint16_t pi=kind==CC_ERROR_CONTROL_LOSS?0xFFFE:(kind==CC_ERROR_SUBMIT?0xFFFF:0);
    rec_hdr h={REC_MAGIC,REC_XFERERR,ep,pi,seq,(uint32_t)st,0,0};
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
    if(k->f){ int ferr=fclose(k->f)!=0; if(k->io_err || ferr) rc=CC_ERR_IO; }   // always close; keep the earlier error
    free(k); return rc;
}

// ---------------- buffered tpc sink (tee)
ssize_t (*cc_async_sink_test_write)(int fd, const void *buf, size_t n) = NULL;
struct cc_async_sink {
    int fd; uint8_t *ring; size_t cap, chunk;
    _Atomic size_t head, tail;           // monotonic byte counts: producer publishes head, writer tail
    pthread_t thr; pthread_mutex_t m; pthread_cond_t cv; _Atomic int stop;
    uint64_t pend_pk[2], pend_by[2];     // producer-only: dropped DATA not yet confessed
    _Atomic uint64_t records, written, lost_pk[2], lost_by[2], control_dropped, discarded;
    _Atomic size_t high_water, max_write; int io_errno;
};
static size_t as_free_(struct cc_async_sink *k){
    return k->cap-(atomic_load_explicit(&k->head,memory_order_relaxed)-atomic_load_explicit(&k->tail,memory_order_acquire));
}
static void as_copy_(struct cc_async_sink *k, size_t at, const void *p, size_t n){
    size_t o=at%k->cap, first=n<k->cap-o?n:k->cap-o;
    memcpy(k->ring+o,p,first); if(n>first) memcpy(k->ring,(const uint8_t*)p+first,n-first);
}
static void as_wake_(struct cc_async_sink *k){
    pthread_mutex_lock(&k->m); pthread_cond_signal(&k->cv); pthread_mutex_unlock(&k->m);
}
/* one record: header + payload, published together; caller checked space */
static void as_put_(struct cc_async_sink *k, const rec_hdr *h, const void *pay, size_t plen){
    size_t at=atomic_load_explicit(&k->head,memory_order_relaxed);
    as_copy_(k,at,h,sizeof *h); if(plen) as_copy_(k,at+sizeof *h,pay,plen);
    atomic_store_explicit(&k->head,at+sizeof *h+plen,memory_order_release);
    size_t used=at+sizeof *h+plen-atomic_load_explicit(&k->tail,memory_order_relaxed);
    if(used>atomic_load_explicit(&k->high_water,memory_order_relaxed)) atomic_store_explicit(&k->high_water,used,memory_order_relaxed);
    atomic_fetch_add_explicit(&k->records,1,memory_order_relaxed);
}
static size_t as_loss_records_(uint64_t by){ return by<=0xffffffffu?1:(size_t)((by+0xfffffffeu)/0xffffffffu); }
/* confess this endpoint's pending loss as HostLoss records (byte field split at 32 bits) */
static void as_flush_loss_(struct cc_async_sink *k, int e){
    uint64_t pk=k->pend_pk[e], by=k->pend_by[e]; uint8_t ep=e?CC_EP_AUDIO:CC_EP_VIDEO;
    do {
        uint32_t b=(uint32_t)(by>0xffffffffu?0xffffffffu:by); by-=b;
        uint32_t p=(uint32_t)(pk>0xffffffffu?0xffffffffu:pk); pk-=p;
        rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,0,0,0,p,b}; as_put_(k,&h,NULL,0);
    } while(by || pk);
    k->pend_pk[e]=k->pend_by[e]=0;
}
static void as_packet_(void *ctx, const cc_packet *p){
    struct cc_async_sink *k=ctx; int e=p->endpoint==CC_EP_AUDIO;
    size_t need=sizeof(rec_hdr)+p->actual_len;
    if(k->pend_pk[e]){
        size_t loss=as_loss_records_(k->pend_by[e])*sizeof(rec_hdr);
        if(as_free_(k)>=loss+need) as_flush_loss_(k,e);
    }
    if(k->pend_pk[e] || as_free_(k)<need){
        k->pend_pk[e]++; k->pend_by[e]+=p->actual_len;
        atomic_fetch_add_explicit(&k->lost_pk[e],1,memory_order_relaxed);
        atomic_fetch_add_explicit(&k->lost_by[e],p->actual_len,memory_order_relaxed);
        return;
    }
    rec_hdr h={REC_MAGIC,REC_DATA,p->endpoint,p->pkt_index,p->submit_seq,p->status,p->req_len,p->actual_len};
    as_put_(k,&h,p->data,p->actual_len); as_wake_(k);
}
static void as_meta_(struct cc_async_sink *k, const rec_hdr *h){
    if(as_free_(k)<sizeof *h){ atomic_fetch_add_explicit(&k->control_dropped,1,memory_order_relaxed); return; }
    as_put_(k,h,NULL,0); as_wake_(k);
}
static void as_loss_(void *ctx, uint8_t ep, uint32_t pk, uint64_t by){
    struct cc_async_sink *k=ctx; int e=ep==CC_EP_AUDIO;
    if(k->pend_pk[e]){ k->pend_pk[e]+=pk; k->pend_by[e]+=by; return; }   /* one run: confessed together */
    if(as_free_(k)<as_loss_records_(by)*sizeof(rec_hdr)){ k->pend_pk[e]+=pk; k->pend_by[e]+=by; return; }
    k->pend_pk[e]=pk; k->pend_by[e]=by; as_flush_loss_(k,e); as_wake_(k);
}
static void as_error_(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){
    uint16_t pi=kind==CC_ERROR_CONTROL_LOSS?0xFFFE:(kind==CC_ERROR_SUBMIT?0xFFFF:0);
    rec_hdr h={REC_MAGIC,REC_XFERERR,ep,pi,seq,(uint32_t)st,0,0}; as_meta_(ctx,&h);
}
static void as_tick_(void *ctx, uint32_t ms){ rec_hdr h={REC_MAGIC,REC_TICK,0,0,0,ms,0,0}; as_meta_(ctx,&h); }
static void as_end_(void *ctx, enum cc_end r){ (void)ctx; (void)r; }
static void *as_writer_(void *arg){
    struct cc_async_sink *k=arg;
    pthread_set_qos_class_self_np(QOS_CLASS_UTILITY,0);
    for(;;){
        size_t tail=atomic_load_explicit(&k->tail,memory_order_relaxed);
        size_t avail=atomic_load_explicit(&k->head,memory_order_acquire)-tail;
        if(!avail){
            if(atomic_load(&k->stop)) break;
            pthread_mutex_lock(&k->m);
            if(atomic_load_explicit(&k->head,memory_order_acquire)==tail && !atomic_load(&k->stop)){
                struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts); ts.tv_nsec+=100000000;
                if(ts.tv_nsec>=1000000000){ ts.tv_sec++; ts.tv_nsec-=1000000000; }
                pthread_cond_timedwait(&k->cv,&k->m,&ts);   /* liveness backstop only */
            }
            pthread_mutex_unlock(&k->m); continue;
        }
        size_t o=tail%k->cap, n=avail;
        if(n>k->cap-o) n=k->cap-o;
        if(n>k->chunk) n=k->chunk;
        if(k->io_errno){ atomic_fetch_add_explicit(&k->discarded,n,memory_order_relaxed); }
        else {
            size_t done=0;
            while(done<n){
                ssize_t w=cc_async_sink_test_write?cc_async_sink_test_write(k->fd,k->ring+o+done,n-done):write(k->fd,k->ring+o+done,n-done);
                if(w<0 && errno==EINTR) continue;
                if(w<=0){ k->io_errno=w<0?errno:EIO; break; }
                if((size_t)w>atomic_load_explicit(&k->max_write,memory_order_relaxed)) atomic_store_explicit(&k->max_write,(size_t)w,memory_order_relaxed);
                done+=(size_t)w;
            }
            atomic_fetch_add_explicit(&k->written,done,memory_order_relaxed);
            if(done<n) atomic_fetch_add_explicit(&k->discarded,n-done,memory_order_relaxed);
        }
        atomic_store_explicit(&k->tail,tail+n,memory_order_release);
    }
    return NULL;
}
int cc_async_sink_open(cc_async_sink **out, const char *path, const char *note, size_t ring_bytes, size_t chunk){
    if(!out || !path || ring_bytes<(1u<<20) || !chunk) return CC_ERR_ARGS;
    cc_async_sink *k=calloc(1,sizeof *k); if(!k) return CC_ERR_NOMEM;
    k->cap=ring_bytes; k->chunk=chunk; k->ring=malloc(ring_bytes);
    if(!k->ring){ free(k); return CC_ERR_NOMEM; }
    k->fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0644);
    if(k->fd<0){ free(k->ring); free(k); return CC_ERR_IO; }
    pthread_mutex_init(&k->m,NULL); pthread_cond_init(&k->cv,NULL);
    if(note && *note){
        size_t len=strlen(note); rec_hdr h={REC_MAGIC,REC_SESSION,0,0,0,0,0,(uint32_t)len}; as_put_(k,&h,note,len);
    }
    if(pthread_create(&k->thr,NULL,as_writer_,k)!=0){
        close(k->fd); unlink(path); pthread_mutex_destroy(&k->m); pthread_cond_destroy(&k->cv); free(k->ring); free(k); return CC_ERR_NOMEM;
    }
    *out=k; return CC_OK;
}
void cc_async_sink_callbacks(cc_async_sink *k, cc_callbacks *o){
    memset(o,0,sizeof *o);
    o->on_packet=as_packet_; o->on_loss=as_loss_; o->on_error=as_error_;
    o->on_tick=as_tick_; o->on_end=as_end_; o->ctx=k;
}
int cc_async_sink_close(cc_async_sink *k, cc_async_sink_stats *st){
    if(!k) return CC_ERR_ARGS;
    /* a loss run still pending at the end is confessed if it fits, else counted as control loss */
    for(int e=0;e<2;e++) if(k->pend_pk[e]){
        if(as_free_(k)>=as_loss_records_(k->pend_by[e])*sizeof(rec_hdr)) as_flush_loss_(k,e);
        else atomic_fetch_add(&k->control_dropped,1);
    }
    atomic_store(&k->stop,1); as_wake_(k); pthread_join(k->thr,NULL);
    if(!k->io_errno && fsync(k->fd)!=0) k->io_errno=errno;
    if(close(k->fd)!=0 && !k->io_errno) k->io_errno=errno;
    if(st){
        memset(st,0,sizeof *st);
        st->records=atomic_load(&k->records); st->bytes_written=atomic_load(&k->written);
        for(int e=0;e<2;e++){ st->lost_packets[e]=atomic_load(&k->lost_pk[e]); st->lost_bytes[e]=atomic_load(&k->lost_by[e]); }
        st->control_dropped=atomic_load(&k->control_dropped); st->discarded_after_error=atomic_load(&k->discarded);
        st->high_water=atomic_load(&k->high_water); st->max_write=atomic_load(&k->max_write); st->io_error=k->io_errno;
    }
    int rc=k->io_errno?CC_ERR_IO:CC_OK;
    pthread_mutex_destroy(&k->m); pthread_cond_destroy(&k->cv); free(k->ring); free(k);
    return rc;
}
