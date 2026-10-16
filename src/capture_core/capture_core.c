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
#include <sys/mman.h>
#include <sys/qos.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread/qos.h>
#include <mach/mach.h>
#include <mach/thread_policy.h>
#include <mach/mach_time.h>
#include <limits.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <dirent.h>
#include <signal.h>

#define VID 0x1EDB
#define PID 0xBD3B
#define V_PKT 15360
#define V_NPK 128
#define A_PKT 0xc0
/* Audio transfers: 128 packets = 16 ms, like video, so both endpoints keep the same ~512 ms queued. With 80 (10 ms) the
 * audio queue was 320 ms and a 450 ms hold-off lost audio while video survived (shim ground truth, 2026-10-16). */
#define A_NPK 128
/* Transfers queued per endpoint. Each video transfer is 128 microframes (16 ms), so 32 keep ~512 ms of USB slots
 * requested ahead. With 8 (128 ms), a held-off event thread let macOS reschedule late resubmissions past the
 * frames in between, which are then never read and leave no record (2026-10-15: 1,352 video packets in one second). */
#define XFERS CC_XFERS_PER_ENDPOINT
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
    int64_t end_frame;          /* unscheduled-slot model: the USB frame this transfer's slots end at */
    uint32_t gap_frames;        /* frames left unread before this transfer (reported just before its data) */
    int uncertain;              /* failed submits just before this one: libusb may have advanced its queue end */
    struct cc_session *s;
} xinfo;

enum cc_life { CC_LIFE_OPEN, CC_LIFE_STARTING, CC_LIFE_RUNNING,
               CC_LIFE_STOPPING, CC_LIFE_STOPPED };
enum { DELIVERY_BUFFER_BYTES = 1u << 20 };

struct cc_session {
    uint32_t start_mode_word;                  // provenance: the mode word sent at start (0 until the device start-up sent it)
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
    _Atomic int space_waiting;                     /* replay_block_when_full: the replay waits for ring space */
    pthread_mutex_t space_m; pthread_cond_t space_c;   /* statically initialised in cc_open; signalled by the delivery thread */
    _Atomic uint64_t replay_space_waits;
    /* unscheduled-slot detector (device backend, event thread only): per endpoint, completions are expected every
     * transfer = npk x 125 us. A window's minimum lateness that steps up and stays up means slots were skipped. */
    struct { int anchored; uint64_t origin_ns; int64_t corr_ns, wmin_ns; int wn, high_windows;
             int64_t lib_qend, data_end; int64_t tf; int uncertain;
             int doubt, defer; int64_t defer_min;
             uint64_t last_cb_ns; int64_t last_late; } sch[2];   /* the endpoint's previous normal completion: when, how late */
    double abs_to_ns;
    _Atomic uint64_t unsched_events, unsched_pkts[2];
    int sched_off; char sched_note[160];   /* the unread-slot model is off when the endpoints are not bInterval 1 */
    int rt_event, rt_lib, rt_still, rt_pri_stop, rt_pri_min;   /* rt_pri_min: lowest scheduled priority, sampled each tick and at stop */
    _Atomic uint64_t sched_shifts, sched_shift_frames;   /* backstop: unexplained completion shifts (model missed a gap) */
    long dbg_hold_at; int dbg_hold_ms; long dbg_video_done;   /* CC_DEBUG_HOLD_AT/MS: hold the event thread once (builds with -DCC_DEBUG_HOLD only) */
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
/* replay_block_when_full: wait until the next DATA record fits (as put_pkt_ requires) or the session stops. The
 * delivery thread broadcasts after every consumed record while a waiter exists; the timeout is a liveness backstop. */
static void replay_wait_space_(cc_session *s, size_t data_need){
    if(ring_free_(s)>=META_RESERVE+data_need) return;
    atomic_fetch_add(&s->space_waiting,1); atomic_fetch_add(&s->replay_space_waits,1);
    pthread_mutex_lock(&s->space_m);
    while(ring_free_(s)<META_RESERVE+data_need && !atomic_load(&s->stop_req)){
        struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts); ts.tv_nsec+=100000000;
        if(ts.tv_nsec>=1000000000){ ts.tv_sec++; ts.tv_nsec-=1000000000; }
        pthread_cond_timedwait(&s->space_c,&s->space_m,&ts);
    }
    pthread_mutex_unlock(&s->space_m);
    atomic_fetch_sub(&s->space_waiting,1);
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
        if(atomic_load(&s->space_waiting)){ pthread_mutex_lock(&s->space_m); pthread_cond_broadcast(&s->space_c); pthread_mutex_unlock(&s->space_m); }
        switch(rh.type){
        case REC_DATA: {
            cc_packet p={rh.endpoint,rh.pkt_index,rh.submit_seq,rh.status,
                         rh.req_len,rh.actual_len,buf};
            s->cb.on_packet(s->cb.ctx,&p);
            atomic_fetch_add_explicit(&s->packets_delivered,1,memory_order_relaxed);
            break; }
        case REC_HOSTLOSS:
            if(rh.pkt_index==CC_PI_UNSCHEDULED){   /* loud: this loss leaves no other trace anywhere */
                char line[200];
                snprintf(line,sizeof line,"capture_core: HOST LOSS: ~%u USB %s slots never read (macOS skipped past them after a late resubmission), from transfer seq %u",
                         rh.req_len,rh.endpoint==CC_EP_VIDEO?"video":"audio",rh.submit_seq);
                if(s->cfg.diag_log) s->cfg.diag_log(s->cfg.diag_ctx,line); else fprintf(stderr,"%s\n",line);
            }
            if(s->cb.on_loss_ex) s->cb.on_loss_ex(s->cb.ctx,rh.endpoint,rh.req_len,rh.actual_len,
                                                  rh.pkt_index==CC_PI_UNSCHEDULED?CC_LOSS_UNSCHEDULED:CC_LOSS_RING,rh.submit_seq);
            else if(s->cb.on_loss) s->cb.on_loss(s->cb.ctx,rh.endpoint,rh.req_len,rh.actual_len);
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
/* Real-time scheduling (THREAD_TIME_CONSTRAINT_POLICY, the mechanism Core Audio uses; no root, no entitlement) for the
 * threads that only move USB packets into the ring: our event thread and libusb's internal Darwin completion thread.
 * Ordinary system load (another app's I/O, the window server, a network volume's client) must not hold them off.
 * Aperiodic; computation is a budget per wake-up, preemptible so a burst of callbacks cannot monopolise a core. */
static int rt_policy_(thread_t th){
    mach_timebase_info_data_t tb; if(mach_timebase_info(&tb)!=KERN_SUCCESS || !tb.numer) return -1;
    double us=1000.0*(double)tb.denom/(double)tb.numer;          /* absolute-time units per microsecond */
    thread_time_constraint_policy_data_t p={ .period=0, .computation=(uint32_t)(5000*us), .constraint=(uint32_t)(10000*us), .preemptible=1 };
    return thread_policy_set(th,THREAD_TIME_CONSTRAINT_POLICY,(thread_policy_t)&p,THREAD_TIME_CONSTRAINT_POLICY_COUNT)==KERN_SUCCESS?0:-1;
}
/* libusb's Darwin backend delivers completions on its own CFRunLoop thread before our event thread sees them. It is
 * created inside libusb_init and named by libusb; find it by name. Returns how many threads were promoted. */
static int rt_promote_libusb_threads_(char *names, size_t names_sz){
    thread_act_array_t th; mach_msg_type_number_t n=0; int promoted=0; size_t used=0;
    if(names_sz) names[0]=0;
    if(task_threads(mach_task_self(),&th,&n)!=KERN_SUCCESS) return -1;
    for(mach_msg_type_number_t i=0;i<n;i++){
        pthread_t pt=pthread_from_mach_thread_np(th[i]); char nm[64]="";
        if(pt) pthread_getname_np(pt,nm,sizeof nm);
        if(!strncmp(nm,"org.libusb",10) && rt_policy_(th[i])==0){
            promoted++;
            if(used<names_sz){ int w=snprintf(names+used,names_sz-used,"%s%s",used?",":"",nm); if(w>0) used+=(size_t)w; }
        }
        mach_port_deallocate(mach_task_self(),th[i]);
    }
    vm_deallocate(mach_task_self(),(vm_address_t)th,n*sizeof *th);
    return promoted;
}
/* Unscheduled-slot detector: libusb's Darwin backend (1.0.30 darwin_usb.c) schedules an isochronous transfer at
 *     start = max(current 1 ms bus frame + 4, the end of what the endpoint already has queued)
 * and sets that end to start + the transfer's length after the IOKit call (even when the call fails; earlier failures,
 * such as BUSY or NO_DEVICE in libusb core, return before it). A start past the end of the data already queued leaves
 * frames that are never read and that nothing records. The event thread mirrors the rule (arithmetic only): each
 * transfer's start and end frame is known at submit, so a gap is known with the transfer it precedes; it is counted
 * at once and its HostLoss goes into the stream immediately before that transfer's data. A stall that does not drain
 * the queue creates no gap, so it cannot be reported.
 * The bus frame comes from the host clock: frame 0 is where the initial fleet starts, anchored by the first NORMAL
 * completion; corr_ns is the latency floor (minimum of completion minus scheduled end) over normal completions, so
 * the 3 ppm USB/host drift never accumulates. Known limit: the floor absorbs the bus-to-callback delay, so every
 * gap is under-predicted by that delay (a gap no larger than it is missed at the gap). Measure it on hardware
 * (CC_DEBUG_HOLD_*); exact frame numbers need IOKit's own completion timestamps.
 * A failed submit is uncertain (libusb may or may not have advanced its queue end): it is settled when the next
 * transferred one completes, by whether that completion lands a whole transfer later than the model said. A late
 * callback can also be a held event thread; then the next SCHED_DEFER completions decide (a phantom transfer keeps
 * them all late) and a phantom found that way is a counted schedule shift: its data has gone by, so nothing is placed.
 * Backstop: completions that stay > 2 ms later than the model for 3 windows are counted as a schedule shift and the
 * model re-anchored; no record is placed (it could only land on an intact unit). */
#define SCHED_FRAME_NS 1000000ll
#define SCHED_LEAD 4                          /* libusb: frame += 4 */
#define SCHED_PKTS_PER_FRAME 8                /* bInterval 1 at high speed (both endpoints, 8,000 packets/s measured) */
#define SCHED_DEFER 40                        /* completions a doubtful settlement watches: 640 ms, past the 512 ms queue */
static uint64_t sched_now_ns_(const cc_session *s){ return (uint64_t)((double)mach_absolute_time()*s->abs_to_ns); }
static void sched_count_(cc_session *s, int e, uint64_t frames){
    atomic_fetch_add(&s->unsched_events,1); atomic_fetch_add(&s->unsched_pkts[e],frames*SCHED_PKTS_PER_FRAME);
}
static void sched_place_(cc_session *s, uint8_t ep, uint32_t seq, uint64_t frames){
    uint32_t pk=(uint32_t)(frames*SCHED_PKTS_PER_FRAME);
    int e=ep_i(ep);
    if(s->lost_pkts[e]) flush_loss_(s,ep);            /* ring loss already pending on this endpoint comes first */
    if(ring_free_(s)>=sizeof(rec_hdr)+CONTROL_TERMINAL_RESERVE){
        rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,(uint16_t)CC_PI_UNSCHEDULED,seq,0,pk,0};
        ring_put_record_(s,&h,NULL,0); wake_(s);
    } else put_meta_(s,REC_HOSTLOSS,ep,(uint16_t)CC_PI_UNSCHEDULED,seq,0,NULL,0);   /* reserve policy: marks control loss */
}
/* The model counts SCHED_PKTS_PER_FRAME packets per 1 ms frame, which holds for bInterval 1 on both iso endpoints of
 * IF0 alt 2. Read it from the device: anything else turns the model off (named), an unreadable descriptor leaves
 * it on and says so. The note goes out with the real-time status line when the event thread starts. */
static void sched_check_interval_(cc_session *s){
    struct libusb_config_descriptor *cd=NULL; int found=0, bad=0, iv=0;
    if(libusb_get_active_config_descriptor(libusb_get_device(s->h),&cd)==0 && cd){
        for(int i=0;i<cd->bNumInterfaces;i++) for(int a=0;a<cd->interface[i].num_altsetting;a++){
            const struct libusb_interface_descriptor *d=&cd->interface[i].altsetting[a];
            if(d->bInterfaceNumber!=0 || d->bAlternateSetting!=2) continue;
            for(int k=0;k<d->bNumEndpoints;k++){
                uint8_t ep=d->endpoint[k].bEndpointAddress;
                if(ep!=CC_EP_VIDEO && ep!=CC_EP_AUDIO) continue;
                found++; if(d->endpoint[k].bInterval!=1){ bad=1; iv=d->endpoint[k].bInterval; }
            }
        }
        libusb_free_config_descriptor(cd);
    }
    s->sched_off=bad;
    if(bad) snprintf(s->sched_note,sizeof s->sched_note,"capture_core: an iso endpoint has bInterval %d, not 1: unread-USB-slot detection is OFF for this session",iv);
    else if(found!=2) snprintf(s->sched_note,sizeof s->sched_note,"capture_core: iso endpoint intervals could not be read (%d of 2): unread-USB-slot detection assumes bInterval 1",found);
}
/* every submit attempt goes through here: initial fleet (pre-anchor: back to back), resubmit, retry */
static int sched_submit_(cc_session *s, xinfo *xi, int initial_index){
    if(s->sched_off) return libusb_submit_transfer(xi->x);
    int e=ep_i(xi->ep); __typeof__(s->sch[0]) *q=&s->sch[e];
    if(!q->tf) q->tf=(int64_t)xi->x->num_iso_packets/SCHED_PKTS_PER_FRAME;
    int64_t start; uint32_t gap=0;
    if(initial_index>=0 || !q->anchored) start=q->lib_qend;   /* frames fixed at the anchor: initial i ends at (i+1)tf */
    else {
        int64_t cur=((int64_t)(sched_now_ns_(s)-q->origin_ns)-q->corr_ns)/SCHED_FRAME_NS;
        start=cur+SCHED_LEAD; if(start<q->lib_qend) start=q->lib_qend;
        gap=start>q->data_end?(uint32_t)(start-q->data_end):0;
    }
    int rc=libusb_submit_transfer(xi->x);
    if(rc==0){
        q->lib_qend=start+q->tf; xi->end_frame=q->lib_qend; q->data_end=xi->end_frame;
        xi->gap_frames=gap; xi->uncertain=q->uncertain; q->uncertain=0;
        if(gap) sched_count_(s,e,gap);                /* counted when known, even if this transfer never completes */
    } else { q->uncertain++; xi->gap_frames=0; xi->uncertain=0; }
    return rc;
}
/* Move the model's queue on this endpoint `shift` frames later: libusb's queue end, and every transfer in flight
 * queued after `after` (by queue position, not seq: a retried transfer keeps the seq of its failed attempt). */
static void sched_shift_(cc_session *s, const xinfo *xi, int64_t after, int64_t shift){
    __typeof__(s->sch[0]) *q=&s->sch[ep_i(xi->ep)];
    for(int i=0;i<NXF;i++) if(s->xs[i].x && s->xs[i].ep==xi->ep && &s->xs[i]!=xi && s->xs[i].end_frame>after)
        s->xs[i].end_frame+=shift;
    q->lib_qend+=shift; q->data_end+=shift;
}
/* before the transfer's data, on the event thread */
static void sched_complete_(cc_session *s, xinfo *xi, int normal){
    if(s->sched_off) return;
    int e=ep_i(xi->ep); __typeof__(s->sch[0]) *q=&s->sch[e];
    uint64_t now=sched_now_ns_(s);
    if(!normal){ if(xi->uncertain){ q->doubt=1; xi->uncertain=0; } return; }   /* no timing here: the next normal completion settles it */
    if(!q->anchored){ q->anchored=1; q->origin_ns=now-(uint64_t)(xi->end_frame*SCHED_FRAME_NS); q->corr_ns=0; q->wn=0; q->high_windows=0; }
    int64_t r=(int64_t)(now-q->origin_ns)-xi->end_frame*SCHED_FRAME_NS;
    int64_t half=q->tf*SCHED_FRAME_NS/2;
    if(xi->uncertain || q->doubt){                    /* settle failed submits before this one */
        int64_t late=r-q->corr_ns; xi->uncertain=0; q->doubt=0;
        if(late>half){
            /* A transfer late: a phantom one before it (libusb did advance), or this callback was held up. A held event
             * thread holds the other endpoint too, so it is a phantom for certain only if the other endpoint kept
             * completing on time: its last completion on time, no earlier than this one's due moment and within one of
             * its transfers of now (both endpoints complete on the same frames). Otherwise the next completions decide:
             * a phantom keeps them all late, a hold catches up. Known limit: a hold that begins between the two
             * endpoints' callbacks of one frame and lasts under one transfer passes this test. */
            __typeof__(s->sch[0]) *o=&s->sch[e^1];
            uint64_t due=now-(uint64_t)late, recent=now-(uint64_t)(o->tf*SCHED_FRAME_NS);   /* due: this callback without its lateness */
            uint64_t need=(due>recent?due:recent)-(uint64_t)SCHED_FRAME_NS;
            int held=!o->anchored || o->last_cb_ns<need || o->last_late>2*SCHED_FRAME_NS;
            if(!held){
                int64_t shift=(late+SCHED_FRAME_NS/2)/SCHED_FRAME_NS;
                xi->gap_frames+=(uint32_t)shift; sched_count_(s,e,(uint64_t)shift);
                sched_shift_(s,xi,xi->end_frame,shift); xi->end_frame+=shift; r-=shift*SCHED_FRAME_NS;
            } else { q->defer=SCHED_DEFER; q->defer_min=late; }
        }
    } else if(q->defer){
        int64_t late=r-q->corr_ns; if(late<q->defer_min) q->defer_min=late;
        if(--q->defer==0){
            if(q->defer_min>half){                    /* it stayed late: a phantom transfer, found after its data went by */
                int64_t shift=(q->defer_min+SCHED_FRAME_NS/2)/SCHED_FRAME_NS;
                atomic_fetch_add(&s->sched_shifts,1); atomic_fetch_add(&s->sched_shift_frames,(uint64_t)shift);
                sched_shift_(s,xi,INT64_MIN,shift); xi->end_frame+=shift; r-=shift*SCHED_FRAME_NS;
            }
            q->wn=0; q->high_windows=0;
        }
    }
    if(xi->gap_frames){ sched_place_(s,xi->ep,xi->seq,xi->gap_frames); xi->gap_frames=0; }
    q->last_cb_ns=now; q->last_late=r-q->corr_ns;
    if(r<q->corr_ns) q->corr_ns=r;                    /* latency floor: any decrease at once */
    if(q->defer) return;                              /* the deferred decision owns this stretch, not the backstop */
    if(!q->wn || r<q->wmin_ns) q->wmin_ns=r;
    if(++q->wn<16) return;
    q->wn=0;
    int64_t step=q->wmin_ns-q->corr_ns;
    if(step>2*SCHED_FRAME_NS){
        if(++q->high_windows>=3){                     /* the model missed something: count it, re-anchor, place nothing */
            atomic_fetch_add(&s->sched_shifts,1); atomic_fetch_add(&s->sched_shift_frames,(uint64_t)(step/SCHED_FRAME_NS));
            q->corr_ns=q->wmin_ns; q->high_windows=0;
        }
    } else { q->high_windows=0; q->corr_ns+=step<50000?step:50000; }   /* drift: slow increase only */
}
static void usb_cb(struct libusb_transfer *x){
    xinfo *xi=x->user_data;
    cc_session *s=xi->s;
    atomic_fetch_sub(&s->inflight,1);
    int e=ep_i(xi->ep);
    int stopping_cancel=x->status==LIBUSB_TRANSFER_CANCELLED && atomic_load(&s->stop_req);
    if(!stopping_cancel && x->status!=LIBUSB_TRANSFER_NO_DEVICE)
        sched_complete_(s,xi,x->status==LIBUSB_TRANSFER_COMPLETED);   /* places a known gap before this data */
#ifdef CC_DEBUG_HOLD
    if(e==0 && s->dbg_hold_at>0 && ++s->dbg_video_done==s->dbg_hold_at)
        usleep((useconds_t)s->dbg_hold_ms*1000);      /* CC_DEBUG_HOLD_*: a held-off event thread, on purpose */
#endif
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
        int rc=sched_submit_(s,xi,-1);
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
/* Input select, wire byte 0 of register 0x00, as the vendor driver writes it: one of bits 7 (SDI), 0 (HDMI),
 * 2 (S-Video), 1 (composite), or none (component). Measured 2026-10-13 against bars with each cable alone and
 * both: 0x04 decodes S-Video, 0x02 decodes the composite jack (3.58 MHz residue in luma 5.3x, S-Video 0.8x).
 * The words this code sent before, 0x09|0x06 for S-Video and 0x09|0x04 for "composite", set the HDMI bit and
 * put composite on the S-Video bit, so "composite" decoded S-Video. Component (0x00) is the driver's and has
 * not been exercised on hardware. Bits 4 (analog audio) and 5 (8-bit) as before; bit 3 is the 7.5 IRE setup bit. */
uint32_t cc_mode_word(const cc_config *cfg){
    uint32_t vsel = cfg->input==CC_INPUT_COMPONENT?0x00000000u
                  : cfg->input==CC_INPUT_COMPOSITE?0x02000000u:0x04000000u;
    uint32_t w=0x08000000u|vsel|0x10000000u|0x20000000u;
    if(cfg->setup_off) w&=~0x08000000u;
    return w;
}
int cc_start_info(const cc_session *s, uint32_t *mode_word){
    if(!s || s->cfg.replay_path || !s->start_mode_word) return -1;
    *mode_word=s->start_mode_word;
    return 0;
}
/* The event thread's scheduled priority now (-1 unknown), folded into the session minimum. A fail-safe demotion
 * drops it below the real-time queues (97 and up) whatever the policy reads back; sampled once a second. */
static void rt_sample_(cc_session *s){
    struct thread_extended_info ei; mach_msg_type_number_t c=THREAD_EXTENDED_INFO_COUNT;
    int p=thread_info(pthread_mach_thread_np(pthread_self()),THREAD_EXTENDED_INFO,(thread_info_t)&ei,&c)==KERN_SUCCESS?ei.pth_curpri:-1;
    if(p<s->rt_pri_min) s->rt_pri_min=p;
}
static void* device_main(void *arg){
    cc_session *s=arg;
    internal_session=s; s->rt_pri_min=INT_MAX;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    { mach_timebase_info_data_t tb; mach_timebase_info(&tb); s->abs_to_ns=tb.numer?(double)tb.numer/(double)tb.denom:1.0; }
#ifdef CC_DEBUG_HOLD   /* a measurement build: the hold is never compiled into a normal one */
    { const char *a=getenv("CC_DEBUG_HOLD_AT"), *m=getenv("CC_DEBUG_HOLD_MS");
      s->dbg_hold_at=a?atol(a):0; s->dbg_hold_ms=m?atoi(m):0; s->dbg_video_done=0;
      if(s->dbg_hold_at>0) fprintf(stderr,"capture_core: DEBUG HOLD ARMED: the USB event thread will stop for %d ms at video completion %ld\n",s->dbg_hold_ms,s->dbg_hold_at); }
#endif
    if(s->sched_note[0]){ if(s->cfg.diag_log) s->cfg.diag_log(s->cfg.diag_ctx,s->sched_note); else fprintf(stderr,"%s\n",s->sched_note); }
    char note[480], lnames[96];
    int rt_self=rt_policy_(pthread_mach_thread_np(pthread_self()))==0, rt_lib=rt_promote_libusb_threads_(lnames,sizeof lnames);
    s->rt_event=rt_self; s->rt_lib=rt_lib;
    { char line[240];
      if(!rt_self || rt_lib<1)
          snprintf(line,sizeof line,"capture_core: real-time scheduling NOT fully applied (event thread %s, libusb threads promoted %d): USB reads can be held off by system load",
                   rt_self?"ok":"FAILED",rt_lib);
      else snprintf(line,sizeof line,"capture_core: real-time scheduling on: event thread and %d libusb thread%s (%s); %d transfers queued per endpoint",
                    rt_lib,rt_lib==1?"":"s",lnames,XFERS);
      if(s->cfg.diag_log) s->cfg.diag_log(s->cfg.diag_ctx,line); else fprintf(stderr,"%s\n",line); }
    snprintf(note,sizeof note,"capture_core v1 input=%d ring=%zuMB V_NPK=%d XFERS=%d mode=0x%08x setup=%s rt=event:%s,libusb:%d[%s]",
             s->cfg.input,s->ring_sz>>20,V_NPK,XFERS,s->start_mode_word,s->cfg.setup_off?"off":"on",
             rt_self?"yes":"NO",rt_lib,lnames);
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
            int rc=sched_submit_(s,&s->xs[n],i);
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
            int rc=sched_submit_(s,&s->xs[i],-1);
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
        if(ms-last_tick>=1000){ last_tick=ms; put_meta_(s,REC_TICK,0,0,0,ms,NULL,0); rt_sample_(s); }
    }
stopping:
    { thread_time_constraint_policy_data_t p; mach_msg_type_number_t n=THREAD_TIME_CONSTRAINT_POLICY_COUNT; boolean_t dflt=0;
      s->rt_still=thread_policy_get(pthread_mach_thread_np(pthread_self()),THREAD_TIME_CONSTRAINT_POLICY,(thread_policy_t)&p,&n,&dflt)==KERN_SUCCESS && !dflt;
      /* the policy read back can survive a fail-safe demotion; the scheduled priority cannot (real-time queues >= 97) */
      struct thread_extended_info ei; mach_msg_type_number_t c=THREAD_EXTENDED_INFO_COUNT;
      s->rt_pri_stop=thread_info(pthread_mach_thread_np(pthread_self()),THREAD_EXTENDED_INFO,(thread_info_t)&ei,&c)==KERN_SUCCESS?ei.pth_curpri:-1;
      if(s->rt_pri_stop<s->rt_pri_min) s->rt_pri_min=s->rt_pri_stop; }
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
            // deliver with the ORIGINAL tags; backpressure via ring, honestly (offline: wait for room instead)
            if(s->cfg.replay_block_when_full) replay_wait_space_(s,sizeof(rec_hdr)+(size_t)h.actual_len);
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
            int le=ep_i(h.endpoint);
            if(h.pkt_index==CC_PI_UNSCHEDULED){   /* the capture's own unread-slot record: forward it as captured */
                if(s->cfg.replay_block_when_full) replay_wait_space_(s,0);
                if(s->lost_pkts[le]) flush_loss_(s,h.endpoint);   /* earlier ring loss first */
                atomic_fetch_add(&s->unsched_events,1); atomic_fetch_add(&s->unsched_pkts[le],h.req_len);
                if(ring_free_(s)>=sizeof(rec_hdr)+CONTROL_TERMINAL_RESERVE){ ring_put_record_(s,&h,NULL,0); wake_(s); }
                else put_meta_(s,REC_HOSTLOSS,h.endpoint,(uint16_t)CC_PI_UNSCHEDULED,h.submit_seq,0,NULL,0);
                break;
            }
            // fold the ORIGINAL capture's loss into our accounting so counts
            // survive replay (forwarding with zeroed fields lost them)
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
    if(cfg->replay_block_when_full && !cfg->replay_path) return CC_ERR_ARGS;   // a device cannot wait for its consumer
    cc_session *s=calloc(1,sizeof *s);
    if(!s) return CC_ERR_NOMEM;
    s->cfg=*cfg; s->cb=*cb;
    s->space_m=(pthread_mutex_t)PTHREAD_MUTEX_INITIALIZER; s->space_c=(pthread_cond_t)PTHREAD_COND_INITIALIZER;
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
        uint32_t mode_word=cc_mode_word(&s->cfg);
        /* Register 4 has no user meaning (the Shuttle has no input gain controls, owner 2026-10-07); the driver's
         * settings commit writes it as 80 80 80 00, so it is written so here, never anything else. */
        const uint32_t r4=0x80808000u;
        /* The device latches the mode register only at the alt-setting reset, and from the value written BEFORE the
         * most recent write (a one-write lag). Measured 2026-10-06: with the mode word sent only after the reset, each
         * start showed the previous start's setup bit. So before the reset, with the stream idle (alt 0), the driver's
         * commit goes out twice in a row, in address order (0x00, 0x04, 0x18), so the staged and the committed value
         * are both this start's; the reset then applies them. The words after the reset stay as they always were. */
        if(libusb_set_interface_alt_setting(s->h,0,0)) goto usb_fail;
        if(vout_(s->h,215,0,mode_word)!=4 || vout_(s->h,215,0,mode_word)!=4 ||
           vout_(s->h,215,4,r4)!=4 || vout_(s->h,215,4,r4)!=4 ||
           vout_(s->h,215,24,0x73c60001u)!=4 || vout_(s->h,215,24,0x73c60001u)!=4) goto usb_fail;
        if(libusb_set_interface_alt_setting(s->h,0,1) || libusb_set_interface_alt_setting(s->h,0,2)){
            goto usb_fail;
        }
        sched_check_interval_(s);
        if(vout_(s->h,215,0,mode_word)!=4) goto usb_fail;
        s->start_mode_word=mode_word;
        if(vout_(s->h,215,24,0x73c60001u)!=4){
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
    pthread_mutex_lock(&s->space_m); pthread_cond_broadcast(&s->space_c); pthread_mutex_unlock(&s->space_m);   /* so does a replay waiting for ring space */
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
    o->replay_align_bytes=s->align_bytes; o->replay_space_waits=atomic_load(&s->replay_space_waits);
    o->unscheduled_events=atomic_load(&s->unsched_events);
    o->rt_event_thread=s->rt_event; o->rt_libusb_threads=s->rt_lib; o->rt_event_at_stop=s->rt_still; o->rt_priority_at_stop=s->rt_pri_stop; o->rt_priority_min=s->rt_pri_min;
    o->schedule_shifts=atomic_load(&s->sched_shifts); o->schedule_shift_frames=atomic_load(&s->sched_shift_frames);
    o->unscheduled_packets[0]=atomic_load(&s->unsched_pkts[0]); o->unscheduled_packets[1]=atomic_load(&s->unsched_pkts[1]);
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
static void snk_loss_ex(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){
    if(kind!=CC_LOSS_UNSCHEDULED){ snk_loss(ctx,ep,pk,by); return; }
    rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,(uint16_t)CC_PI_UNSCHEDULED,seq,0,pk,0};
    snk_wr(sink_of(ctx),&h,sizeof h);
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
    o->on_tick=snk_tick; o->on_end=snk_end; o->ctx=k; o->on_loss_ex=snk_loss_ex;
}
int cc_tagged_sink_close(cc_tagged_sink *k){
    int rc = CC_OK;
    if(k->f){ int ferr=fclose(k->f)!=0; if(k->io_err || ferr) rc=CC_ERR_IO; }   // always close; keep the earlier error
    free(k); return rc;
}

// ---------------- buffered tpc sink (tee)
ssize_t (*cc_async_sink_test_write)(int fd, const void *buf, size_t n) = NULL;
int (*cc_async_sink_test_fsync)(int fd) = NULL;
ssize_t (*cc_async_sink_test_spill_write)(int fd, const void *buf, size_t n, off_t off) = NULL;
uint64_t (*cc_async_sink_test_free)(const char *dir) = NULL;
int cc_async_sink_test_spill_any_volume = 0;
/* Flush to the volume this often. A network volume (LucidLink's SMB share) refuses writes at the flush, not at
 * write(): a full filespace once let gigabytes of acknowledged writes pile up as failing write-backs that the
 * system retried until it hung (2026-10-03). A refused flush is a write error like any other: the file stops. */
size_t cc_async_sink_sync_every = (size_t)256 << 20;
int cc_async_sink_writer_qos = QOS_CLASS_UTILITY;
static uint64_t as_now_(void){ return clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW); }
struct cc_async_sink {
    int fd; uint8_t *ring; size_t cap, chunk;
    _Atomic size_t head, tail;           // monotonic byte counts: producer publishes head, writer tail
    size_t granule;                      // tail is published in whole granules so drained pages can be handed back; 0 = exact
    _Atomic size_t drained;              // exact position up to which memory has been taken (the published tail lags it by under a granule)
    _Atomic uint64_t max_wake_backlog, released_bytes, release_failures;
    pthread_t thr; pthread_mutex_t m; pthread_cond_t cv; _Atomic int stop;
    uint64_t pend_pk[2], pend_by[2];     // producer-only: dropped DATA not yet confessed
    _Atomic uint64_t records, written, lost_pk[2], lost_by[2], control_dropped, discarded;
    _Atomic size_t high_water, max_write; _Atomic int io_errno; int qos;
    _Atomic uint64_t write_started;      // writer: nonzero while inside a write call (its start time)
    _Atomic uint64_t writes, write_ns, max_write_ns, slow_writes, max_ready_gap_ns;
    _Atomic uint64_t loss_episodes, loss_in_write, max_in_write_at_loss_ns;
    /* Two consumers take memory from the front, one take at a time, under m: the writer (copies a chunk out, then
     * writes it to the destination) and, with a spill, the spiller (moves the oldest backlog to local segment files).
     * Bytes leave memory in stream order and the writer always empties the spill before it takes memory again, so the
     * destination receives the stream in order. Spill offsets [sp_r, sp_w) are the bytes on disk, segment = off/sseg. */
    size_t mpos;                         // under m: stream position up to which memory is taken (or being taken)
    int take_busy, stuck;                // under m: a take is in progress; a release failed (the tail stays put)
    uint8_t *bbuf;                       // writer: the chunk being written
    int spill_on, spill_thread, spill_state; _Atomic int spill_error;
    pthread_t sthr; pthread_cond_t acv; _Atomic size_t a_wake_at;   // the producer wakes the spiller when head reaches a_wake_at
    char *sdir, *sbase; uint32_t stag; uint64_t sfloor; size_t safter, sseg;
    uint64_t sp_w, sp_r, floor_retry_ns; // under m
    int64_t spill_room; uint64_t stale_files, stale_bytes; int finished;   /* at open: free bytes above the floor; segments of dead writers */
    int swfd, srfd; uint64_t swseg, srseg;   // spiller's open segment; writer's
    _Atomic uint64_t spill_bytes, spill_peak, spill_segments, spill_floor_refusals, spill_max_write_ns;
};
static size_t as_free_(struct cc_async_sink *k){
    return k->cap-(atomic_load_explicit(&k->head,memory_order_relaxed)-atomic_load_explicit(&k->tail,memory_order_acquire));
}
static void as_copy_(struct cc_async_sink *k, size_t at, const void *p, size_t n){
    size_t o=at%k->cap, first=n<k->cap-o?n:k->cap-o;
    memcpy(k->ring+o,p,first); if(n>first) memcpy(k->ring,(const uint8_t*)p+first,n-first);
}
/* The producer never waits for the writers' lock (they hold it across a page hand-back): a busy lock skips the
 * signal, and the waiter's 100 ms liveness backstop picks the data up instead. */
static void as_wake_(struct cc_async_sink *k){
    if(pthread_mutex_trylock(&k->m)!=0) return;
    pthread_cond_signal(&k->cv);
    if(atomic_load_explicit(&k->head,memory_order_relaxed)>=atomic_load_explicit(&k->a_wake_at,memory_order_relaxed)) pthread_cond_signal(&k->acv);
    pthread_mutex_unlock(&k->m);
}
/* one record: header + payload, published together; caller checked space */
static void as_put_(struct cc_async_sink *k, const rec_hdr *h, const void *pay, size_t plen){
    size_t at=atomic_load_explicit(&k->head,memory_order_relaxed);
    as_copy_(k,at,h,sizeof *h); if(plen) as_copy_(k,at+sizeof *h,pay,plen);
    atomic_store_explicit(&k->head,at+sizeof *h+plen,memory_order_release);
    size_t used=at+sizeof *h+plen-atomic_load_explicit(&k->drained,memory_order_relaxed);
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
/* The first drop of a run of dropped packets (nothing pending on either endpoint): one loss episode, and what the
 * writer was doing at that moment. */
static void as_episode_(struct cc_async_sink *k){
    if(k->pend_pk[0] || k->pend_pk[1]) return;
    uint64_t ws=atomic_load_explicit(&k->write_started,memory_order_relaxed);
    atomic_fetch_add_explicit(&k->loss_episodes,1,memory_order_relaxed);
    if(ws){
        uint64_t age=as_now_()-ws;
        atomic_fetch_add_explicit(&k->loss_in_write,1,memory_order_relaxed);
        if(age>atomic_load_explicit(&k->max_in_write_at_loss_ns,memory_order_relaxed)) atomic_store_explicit(&k->max_in_write_at_loss_ns,age,memory_order_relaxed);
    }
}
static void as_packet_(void *ctx, const cc_packet *p){
    struct cc_async_sink *k=ctx; int e=p->endpoint==CC_EP_AUDIO;
    size_t need=sizeof(rec_hdr)+p->actual_len;
    if(k->pend_pk[e]){
        size_t loss=as_loss_records_(k->pend_by[e])*sizeof(rec_hdr);
        if(as_free_(k)>=loss+need) as_flush_loss_(k,e);
    }
    if(k->pend_pk[e] || as_free_(k)<need){
        as_episode_(k);
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
    if(as_free_(k)<as_loss_records_(by)*sizeof(rec_hdr)){ as_episode_(k); k->pend_pk[e]+=pk; k->pend_by[e]+=by; return; }
    k->pend_pk[e]=pk; k->pend_by[e]=by; as_flush_loss_(k,e); as_wake_(k);
}
static void as_loss_ex_(void *ctx, uint8_t ep, uint32_t pk, uint64_t by, int kind, uint32_t seq){
    if(kind!=CC_LOSS_UNSCHEDULED){ as_loss_(ctx,ep,pk,by); return; }   /* never merged into a ring-loss run */
    struct cc_async_sink *k=ctx; int e=ep==CC_EP_AUDIO;
    rec_hdr h={REC_MAGIC,REC_HOSTLOSS,ep,(uint16_t)CC_PI_UNSCHEDULED,seq,0,pk,0};
    if(k->pend_pk[e]){                                /* loss confessed before this record stays before it */
        /* Pending loss means the ring had no room for a packet: both records must fit, or this one is counted as a
         * dropped control record (the pending HostLoss still marks the stretch) and the run stays pending. */
        if(as_free_(k)<as_loss_records_(k->pend_by[e])*sizeof(rec_hdr)+sizeof h){ atomic_fetch_add_explicit(&k->control_dropped,1,memory_order_relaxed); return; }
        as_flush_loss_(k,e);
    }
    as_meta_(k,&h);
}
static void as_error_(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){
    uint16_t pi=kind==CC_ERROR_CONTROL_LOSS?0xFFFE:(kind==CC_ERROR_SUBMIT?0xFFFF:0);
    rec_hdr h={REC_MAGIC,REC_XFERERR,ep,pi,seq,(uint32_t)st,0,0}; as_meta_(ctx,&h);
}
static void as_tick_(void *ctx, uint32_t ms){ rec_hdr h={REC_MAGIC,REC_TICK,0,0,0,ms,0,0}; as_meta_(ctx,&h); }
static void as_end_(void *ctx, enum cc_end r){ (void)ctx; (void)r; }
/* Hand the memory of drained ring bytes [a,b) back to the system. Laid out end to end, the stream passes through
 * every page of the ring once per ring length whether or not the writer keeps up, so without this a ring sized
 * for a long stall would stay resident in full a few minutes into every recording. Called before the tail that
 * frees [a,b) is published: until then the producer cannot write there. a and b are granule (page) multiples.
 * The cost falls on the producer: its first copy into each handed-back page takes a zero-fill fault (about one
 * per packet at device rate, +0.3-0.4 us measured 2026-10-02; not measured under memory pressure).
 * Returns 0 if the kernel refused: the range may then be unmapped, so the caller must never publish a tail past a. */
static int as_release_(struct cc_async_sink *k, size_t a, size_t b){
    while(a<b){
        size_t o=a%k->cap, n=b-a; if(n>k->cap-o) n=k->cap-o;
        if(mmap(k->ring+o,n,PROT_READ|PROT_WRITE,MAP_FIXED|MAP_PRIVATE|MAP_ANON,-1,0)==MAP_FAILED){   /* fresh zero pages in place */
            atomic_fetch_add_explicit(&k->release_failures,1,memory_order_relaxed); return 0;
        }
        atomic_fetch_add_explicit(&k->released_bytes,n,memory_order_relaxed);
        a+=n;
    }
    return 1;
}
static void as_wait_(pthread_cond_t *c, pthread_mutex_t *m, uint64_t ns){   /* liveness backstop around an event wait */
    struct timespec ts; clock_gettime(CLOCK_REALTIME,&ts);
    ts.tv_nsec+=(long)(ns%1000000000ull); ts.tv_sec+=(time_t)(ns/1000000000ull);
    if(ts.tv_nsec>=1000000000){ ts.tv_sec++; ts.tv_nsec-=1000000000; }
    pthread_cond_timedwait(c,m,&ts);
}
/* Memory up to pos has been taken: hand it back to the producer. Under m; takes complete in stream order. */
static void as_consumed_(struct cc_async_sink *k, size_t pos){
    atomic_store_explicit(&k->drained,pos,memory_order_relaxed);
    size_t pub=k->granule?pos-pos%k->granule:pos, was=atomic_load_explicit(&k->tail,memory_order_relaxed);
    /* A refused release may have left a hole in the ring. The tail is then never published past it: the producer
     * cannot reach the hole, sees the ring fill, and drops with exact counts; close reports the failure. */
    if(pub>was && !k->stuck){
        if(k->granule && !as_release_(k,was,pub)) k->stuck=1;
        else atomic_store_explicit(&k->tail,pub,memory_order_release);
    }
}
static void as_seg_name_(const struct cc_async_sink *k, uint64_t seg, char *out, size_t cap){
    snprintf(out,cap,"%s/%.96s.p%d.%08x.spill%06llu",k->sdir,k->sbase,(int)getpid(),(unsigned)k->stag,(unsigned long long)seg);
}
/* Write buf[0,n) to the destination. Short only after a failure, which sets io_errno; the rest is counted discarded. */
static void as_dest_write_(struct cc_async_sink *k, const uint8_t *buf, size_t n, uint64_t *last_done, uint64_t *since_sync){
    size_t done=0;
    while(done<n){
        uint64_t t0=as_now_();
        if(*last_done && t0-*last_done>atomic_load_explicit(&k->max_ready_gap_ns,memory_order_relaxed)) atomic_store_explicit(&k->max_ready_gap_ns,t0-*last_done,memory_order_relaxed);
        atomic_store_explicit(&k->write_started,t0,memory_order_relaxed);
        ssize_t w=cc_async_sink_test_write?cc_async_sink_test_write(k->fd,buf+done,n-done):write(k->fd,buf+done,n-done);
        uint64_t t1=as_now_(), dt=t1-t0;
        atomic_store_explicit(&k->write_started,0,memory_order_relaxed); *last_done=t1;
        atomic_fetch_add_explicit(&k->writes,1,memory_order_relaxed); atomic_fetch_add_explicit(&k->write_ns,dt,memory_order_relaxed);
        if(dt>atomic_load_explicit(&k->max_write_ns,memory_order_relaxed)) atomic_store_explicit(&k->max_write_ns,dt,memory_order_relaxed);
        if(dt>100000000ull) atomic_fetch_add_explicit(&k->slow_writes,1,memory_order_relaxed);
        if(w<0 && errno==EINTR) continue;
        if(w<=0){ k->io_errno=w<0?errno:EIO; break; }
        if((size_t)w>atomic_load_explicit(&k->max_write,memory_order_relaxed)) atomic_store_explicit(&k->max_write,(size_t)w,memory_order_relaxed);
        done+=(size_t)w;
    }
    atomic_fetch_add_explicit(&k->written,done,memory_order_relaxed);
    if(done<n) atomic_fetch_add_explicit(&k->discarded,n-done,memory_order_relaxed);
    *since_sync+=done;
    if(!k->io_errno && cc_async_sink_sync_every && *since_sync>=cc_async_sink_sync_every){
        *since_sync=0;
        int r=cc_async_sink_test_fsync?cc_async_sink_test_fsync(k->fd):fsync(k->fd);
        if(r!=0) k->io_errno=errno?errno:EIO;   /* from here on everything drains into the discarded count */
    }
}
/* Read spill bytes [off, off+n) (within one segment) into the writer's buffer. 0 on failure (errno set). */
static int as_spill_read_(struct cc_async_sink *k, uint64_t off, size_t n){
    uint64_t seg=off/k->sseg;
    if(k->srfd<0 || k->srseg!=seg){
        if(k->srfd>=0) close(k->srfd);
        char nm[PATH_MAX]; as_seg_name_(k,seg,nm,sizeof nm);
        k->srfd=open(nm,O_RDONLY); k->srseg=seg;
        if(k->srfd<0) return 0;
    }
    size_t done=0;
    while(done<n){
        ssize_t r=pread(k->srfd,k->bbuf+done,n-done,(off_t)(off%k->sseg+done));
        if(r<0 && errno==EINTR) continue;
        if(r<=0){ if(!r) errno=EIO; return 0; }
        done+=(size_t)r;
    }
    return 1;
}
/* The writer: the only thread that touches the destination. It takes the oldest bytes, from the spill while the
 * spill holds any, otherwise from memory, and writes them in stream order. A destination call that blocks for
 * seconds holds only this thread and its private chunk; memory keeps draining into the spill meanwhile. */
static void *as_writer_(void *arg){
    struct cc_async_sink *k=arg;
    pthread_set_qos_class_self_np((qos_class_t)k->qos,0);
    uint64_t last_done=0;                /* end of the previous write if data was still waiting then, else 0 */
    uint64_t since_sync=0;               /* bytes written since the last flush */
    int idle=0;                          /* the last pass found nothing to write (not thread start-up) */
    pthread_mutex_lock(&k->m);
    for(;;){
        size_t n; uint64_t sp=0; int from_spill=0;
        if(k->sp_r<k->sp_w){             /* the oldest bytes are on disk */
            sp=k->sp_r; n=k->sp_w-sp<k->chunk?(size_t)(k->sp_w-sp):k->chunk;
            size_t left=(size_t)(k->sseg-sp%k->sseg); if(n>left) n=left;
            from_spill=1;
        } else if(k->take_busy){         /* the spiller is moving the next bytes to disk; it signals when done */
            as_wait_(&k->cv,&k->m,100000000ull); continue;
        } else {
            size_t avail=atomic_load_explicit(&k->head,memory_order_acquire)-k->mpos;
            if(!avail){
                last_done=0; idle=1;
                if(atomic_load(&k->stop)) break;
                as_wait_(&k->cv,&k->m,100000000ull); continue;
            }
            /* What had built up while this thread was away in its idle wait: at device rate, how long it was not running.
             * (max_ready_gap_ns cannot see that: it measures between writes, and an idle writer has no previous write.) */
            if(idle){ idle=0; if(avail>atomic_load_explicit(&k->max_wake_backlog,memory_order_relaxed)) atomic_store_explicit(&k->max_wake_backlog,avail,memory_order_relaxed); }
            size_t lo=k->mpos, o=lo%k->cap; n=avail;
            if(n>k->cap-o) n=k->cap-o;
            if(n>k->chunk) n=k->chunk;
            k->mpos=lo+n; k->take_busy=1;
            pthread_mutex_unlock(&k->m);
            memcpy(k->bbuf,k->ring+o,n);
            pthread_mutex_lock(&k->m);
            as_consumed_(k,lo+n); k->take_busy=0; pthread_cond_signal(&k->acv);
        }
        pthread_mutex_unlock(&k->m);
        if(from_spill && !k->io_errno && !as_spill_read_(k,sp,n)) k->io_errno=errno?errno:EIO;   /* bytes lost on the local disk: the file is incomplete */
        if(k->io_errno) atomic_fetch_add_explicit(&k->discarded,n,memory_order_relaxed);
        else as_dest_write_(k,k->bbuf,n,&last_done,&since_sync);
        uint64_t done_seg=UINT64_MAX;
        if(from_spill && (sp+n)%k->sseg==0){   /* that segment is fully delivered: its disk space goes back now */
            done_seg=sp/k->sseg;
            if(k->srfd>=0 && k->srseg==done_seg){ close(k->srfd); k->srfd=-1; }
            char nm[PATH_MAX]; as_seg_name_(k,done_seg,nm,sizeof nm); unlink(nm);
        }
        pthread_mutex_lock(&k->m);
        if(from_spill){ k->sp_r=sp+n; if(done_seg!=UINT64_MAX){ k->floor_retry_ns=0; pthread_cond_signal(&k->acv); } }
    }
    pthread_mutex_unlock(&k->m);
    return NULL;
}
static uint64_t as_free_bytes_(struct cc_async_sink *k){
    if(cc_async_sink_test_free) return cc_async_sink_test_free(k->sdir);
    struct statfs s; if(statfs(k->sdir,&s)!=0) return 0;   /* unknown free space is no free space */
    return (uint64_t)s.f_bavail*(uint64_t)s.f_bsize;
}
/* The spiller: when the memory backlog reaches safter bytes, it moves the oldest memory bytes to segment files on
 * the local disk, so a destination that stalls for minutes costs local disk space instead of the capture. It
 * leaves sfloor bytes free on that volume; past that, memory is the only buffer again and overflow is HostLoss.
 * A spill write that fails returns its bytes to memory and turns the spill off: nothing is lost by that. */
static void *as_spiller_(void *arg){
    struct cc_async_sink *k=arg;
    pthread_set_qos_class_self_np((qos_class_t)k->qos,0);
    pthread_mutex_lock(&k->m);
    for(;;){
        if(atomic_load(&k->stop) || k->io_errno) break;
        size_t backlog=atomic_load_explicit(&k->head,memory_order_acquire)-k->mpos;
        if(k->take_busy || backlog<k->safter){
            atomic_store_explicit(&k->a_wake_at,k->mpos+k->safter,memory_order_relaxed);
            as_wait_(&k->acv,&k->m,100000000ull); continue;
        }
        uint64_t seg=k->sp_w/k->sseg;
        if(k->swfd<0 || k->swseg!=seg){  /* a new segment: only with the floor still clear after it */
            uint64_t now=as_now_();
            if(now<k->floor_retry_ns){ atomic_store_explicit(&k->a_wake_at,SIZE_MAX,memory_order_relaxed); as_wait_(&k->acv,&k->m,k->floor_retry_ns-now); continue; }
            pthread_mutex_unlock(&k->m);
            int fd=-1, err=0; uint64_t fr=as_free_bytes_(k);
            if(k->swfd>=0){ close(k->swfd); k->swfd=-1; }
            if(fr>=k->sfloor+k->sseg){
                char nm[PATH_MAX]; as_seg_name_(k,seg,nm,sizeof nm);
                fd=open(nm,O_WRONLY|O_CREAT|O_EXCL,0600); if(fd<0) err=errno;
            }
            pthread_mutex_lock(&k->m);
            if(fd<0 && !err){                /* the floor: retry when a segment is freed, or the volume gains space */
                atomic_fetch_add_explicit(&k->spill_floor_refusals,1,memory_order_relaxed);
                k->floor_retry_ns=as_now_()+100000000ull; continue;
            }
            if(fd<0){ k->spill_error=err; break; }
            k->swfd=fd; k->swseg=seg; atomic_fetch_add_explicit(&k->spill_segments,1,memory_order_relaxed);
            continue;                        /* state may have moved while unlocked */
        }
        size_t lo=k->mpos, o=lo%k->cap, n=backlog;
        if(n>k->cap-o) n=k->cap-o;
        if(n>k->chunk) n=k->chunk;
        size_t left=(size_t)(k->sseg-k->sp_w%k->sseg); if(n>left) n=left;
        uint64_t at=k->sp_w; k->mpos=lo+n; k->take_busy=1;
        pthread_mutex_unlock(&k->m);
        size_t done=0; int err=0; uint64_t t0=as_now_();
        while(done<n){
            ssize_t w=cc_async_sink_test_spill_write?cc_async_sink_test_spill_write(k->swfd,k->ring+o+done,n-done,(off_t)(at%k->sseg+done))
                                                    :pwrite(k->swfd,k->ring+o+done,n-done,(off_t)(at%k->sseg+done));
            if(w<0 && errno==EINTR) continue;
            if(w<=0){ err=w<0?errno:EIO; break; }
            done+=(size_t)w;
        }
        uint64_t dt=as_now_()-t0;
        if(dt>atomic_load_explicit(&k->spill_max_write_ns,memory_order_relaxed)) atomic_store_explicit(&k->spill_max_write_ns,dt,memory_order_relaxed);
        if(!err && (at+n)%k->sseg==0){ close(k->swfd); k->swfd=-1; }   /* full: the writer frees it once delivered */
        pthread_mutex_lock(&k->m);
        k->take_busy=0;
        if(err){ k->mpos=lo; k->spill_error=err; pthread_cond_signal(&k->cv); break; }   /* the bytes are still in memory */
        k->sp_w=at+n; as_consumed_(k,lo+n);
        atomic_fetch_add_explicit(&k->spill_bytes,n,memory_order_relaxed);
        if(k->sp_w-k->sp_r>atomic_load_explicit(&k->spill_peak,memory_order_relaxed)) atomic_store_explicit(&k->spill_peak,k->sp_w-k->sp_r,memory_order_relaxed);
        pthread_cond_signal(&k->cv);
    }
    k->spill_on=0; atomic_store_explicit(&k->a_wake_at,SIZE_MAX,memory_order_relaxed);
    pthread_mutex_unlock(&k->m);
    return NULL;
}
/* Segments left by a process that is gone hold capture bytes that never reached their destination: they are
 * counted and named, never deleted here (the scratch volume clears them at restart). */
static void as_stale_scan_(struct cc_async_sink *k){
    DIR *d=opendir(k->sdir); if(!d) return; struct dirent *e;
    while((e=readdir(d))){
        /* <base>.p<pid>.<8 hex>.spill<n>: the pid is the last ".p" field before the tag */
        const char *sp=strstr(e->d_name,".spill"); if(!sp || sp-e->d_name<12 || sp[-9]!='.') continue;
        const char *p=NULL; for(const char *q=e->d_name; q<sp-9; q++) if(q[0]=='.' && q[1]=='p') p=q;
        if(!p) continue;
        int pid=atoi(p+2); if(pid<=0 || pid==getpid()) continue;
        if(kill(pid,0)==0 || errno!=ESRCH) continue;   /* its writer is alive (or not ours to judge) */
        char nm[PATH_MAX]; struct stat st; snprintf(nm,sizeof nm,"%s/%s",k->sdir,e->d_name);
        if(lstat(nm,&st)==0 && S_ISREG(st.st_mode)){ k->stale_files++; k->stale_bytes+=(uint64_t)st.st_blocks*512u; }
    }
    closedir(d);
}
int cc_async_sink_open_spill(cc_async_sink **out, const char *path, const char *note, size_t ring_bytes, size_t chunk,
                             const cc_async_sink_spill *sp){
    if(!out || !path || ring_bytes<(1u<<20) || !chunk) return CC_ERR_ARGS;
    cc_async_sink *k=calloc(1,sizeof *k); if(!k) return CC_ERR_NOMEM;
    k->cap=ring_bytes; k->chunk=chunk; k->qos=cc_async_sink_writer_qos; k->swfd=k->srfd=-1;
    atomic_store(&k->a_wake_at,SIZE_MAX);
    size_t page=(size_t)getpagesize(), g=ring_bytes/64<(1u<<20)?ring_bytes/64:(1u<<20);
    k->granule=ring_bytes%page?0:g-g%page;                /* a ring that is not whole pages publishes exactly and keeps its memory */
    k->bbuf=malloc(chunk);
    k->ring=k->bbuf?mmap(NULL,ring_bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0):MAP_FAILED;
    if(k->ring==MAP_FAILED){ free(k->bbuf); free(k); return CC_ERR_NOMEM; }
    k->fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0644);
    struct stat cs;   /* a character device (/dev/null) exists by nature: it is opened, never created */
    if(k->fd<0 && errno==EEXIST && stat(path,&cs)==0 && S_ISCHR(cs.st_mode)) k->fd=open(path,O_WRONLY);
    if(k->fd<0){ munmap(k->ring,k->cap); free(k->bbuf); free(k); return CC_ERR_IO; }
    if(sp && sp->dir && *sp->dir){
        struct stat ds, fs;
        if(mkdir(sp->dir,0700)!=0 && errno!=EEXIST) k->spill_state=-errno;
        else if(lstat(sp->dir,&ds)!=0) k->spill_state=-errno;
        else if(!S_ISDIR(ds.st_mode)) k->spill_state=-ENOTDIR;   /* a symlink too: the spill is never redirected */
        else if(ds.st_uid!=getuid() || (ds.st_mode&077)) k->spill_state=-EPERM;   /* private: nobody else may swap segments */
        else if(fstat(k->fd,&fs)!=0) k->spill_state=-errno;
        else if(fs.st_dev==ds.st_dev && !cc_async_sink_test_spill_any_volume) k->spill_state=0;   /* the destination is that disk already: a spill would only add a copy */
        else {
            const char *b=strrchr(path,'/');
            k->sdir=strdup(sp->dir); k->sbase=strdup(b?b+1:path); k->stag=arc4random();
            k->sfloor=sp->floor?sp->floor:32000000000ull;   /* 32 GB (owner's staging floor, decimal) */
            k->sseg=sp->segment?sp->segment:(size_t)128<<20;
            size_t def=ring_bytes/16; if(def<((size_t)8<<20)) def=(size_t)8<<20; if(def>((size_t)256<<20)) def=(size_t)256<<20;
            k->safter=sp->after?sp->after:def;
            k->spill_state=k->sdir && k->sbase?1:-ENOMEM; k->spill_on=k->spill_state==1;
            if(k->spill_on){ uint64_t fr=as_free_bytes_(k); k->spill_room=(int64_t)fr-(int64_t)k->sfloor; as_stale_scan_(k); }
        }
    }
    pthread_mutex_init(&k->m,NULL); pthread_cond_init(&k->cv,NULL); pthread_cond_init(&k->acv,NULL);
    if(note && *note){
        size_t len=strlen(note); rec_hdr h={REC_MAGIC,REC_SESSION,0,0,0,0,0,(uint32_t)len}; as_put_(k,&h,note,len);
    }
    int started=pthread_create(&k->thr,NULL,as_writer_,k)==0;
    if(started && k->spill_on){
        if(pthread_create(&k->sthr,NULL,as_spiller_,k)==0) k->spill_thread=1;
        else { k->spill_on=0; k->spill_state=-EAGAIN; }
    }
    if(!started){
        close(k->fd); unlink(path); pthread_mutex_destroy(&k->m); pthread_cond_destroy(&k->cv); pthread_cond_destroy(&k->acv);
        munmap(k->ring,k->cap); free(k->bbuf); free(k->sdir); free(k->sbase); free(k); return CC_ERR_NOMEM;
    }
    *out=k; return CC_OK;
}
int cc_async_sink_open(cc_async_sink **out, const char *path, const char *note, size_t ring_bytes, size_t chunk){
    return cc_async_sink_open_spill(out,path,note,ring_bytes,chunk,NULL);
}
int cc_async_sink_spill_state(const cc_async_sink *k){ return k?k->spill_state:-EINVAL; }
int64_t cc_async_sink_spill_room(const cc_async_sink *k){ return k?k->spill_room:0; }
void cc_async_sink_spill_stale(const cc_async_sink *k, uint64_t *files, uint64_t *bytes){ *files=k?k->stale_files:0; *bytes=k?k->stale_bytes:0; }
uint64_t cc_async_sink_progress(cc_async_sink *k){ return atomic_load(&k->written)+atomic_load(&k->discarded); }
void cc_async_sink_callbacks(cc_async_sink *k, cc_callbacks *o){
    memset(o,0,sizeof *o);
    o->on_packet=as_packet_; o->on_loss=as_loss_; o->on_error=as_error_;
    o->on_tick=as_tick_; o->on_end=as_end_; o->ctx=k; o->on_loss_ex=as_loss_ex_;
}
int cc_async_sink_finish(cc_async_sink *k){
    if(!k) return CC_ERR_ARGS;
    if(k->finished) return CC_OK;
    pthread_mutex_lock(&k->m); atomic_store(&k->stop,1); pthread_cond_broadcast(&k->cv); pthread_cond_broadcast(&k->acv); pthread_mutex_unlock(&k->m);
    if(k->spill_thread) pthread_join(k->sthr,NULL);
    pthread_join(k->thr,NULL);             /* the writer has delivered memory and spill, or counted them discarded */
    k->finished=1;
    return CC_OK;
}
int cc_async_sink_close(cc_async_sink *k, cc_async_sink_stats *st){
    if(!k) return CC_ERR_ARGS;
    cc_async_sink_finish(k);
    if(k->swfd>=0) close(k->swfd);
    if(k->srfd>=0) close(k->srfd);
    if(k->sdir) for(uint64_t g=k->sp_r/k->sseg; g<=k->sp_w/k->sseg; g++){ char nm[PATH_MAX]; as_seg_name_(k,g,nm,sizeof nm); unlink(nm); }
    /* A loss run still pending at the end: the writer has drained and gone, so its confession goes straight to the
     * file (the ring may have been full to the last packet). Only a file that already failed leaves it uncounted
     * in the stream, and then it is counted as a dropped control record. */
    for(int e=0;e<2;e++) if(k->pend_pk[e]){
        if(k->io_errno){ atomic_fetch_add(&k->control_dropped,1); continue; }
        uint64_t pk=k->pend_pk[e], by=k->pend_by[e];
        do {
            uint32_t b=(uint32_t)(by>0xffffffffu?0xffffffffu:by); by-=b;
            uint32_t q=(uint32_t)(pk>0xffffffffu?0xffffffffu:pk); pk-=q;
            rec_hdr h={REC_MAGIC,REC_HOSTLOSS,e?CC_EP_AUDIO:CC_EP_VIDEO,0,0,0,q,b}; size_t done=0;
            while(done<sizeof h){
                ssize_t w=cc_async_sink_test_write?cc_async_sink_test_write(k->fd,(const uint8_t*)&h+done,sizeof h-done):write(k->fd,(const uint8_t*)&h+done,sizeof h-done);
                if(w<0 && errno==EINTR) continue;
                if(w<=0){ k->io_errno=w<0?errno:EIO; break; }
                done+=(size_t)w;
            }
            atomic_fetch_add(&k->written,done);
            if(done==sizeof h) atomic_fetch_add(&k->records,1); else { atomic_fetch_add(&k->control_dropped,1); break; }
        } while(by || pk);
        k->pend_pk[e]=k->pend_by[e]=0;
    }
    if(atomic_load(&k->release_failures) && !k->io_errno) k->io_errno=ENOMEM;   /* the ring lost part of its memory: the capture is incomplete */
    if(!k->io_errno && fsync(k->fd)!=0) k->io_errno=errno;
    if(close(k->fd)!=0 && !k->io_errno) k->io_errno=errno;
    if(st){
        memset(st,0,sizeof *st);
        st->records=atomic_load(&k->records); st->bytes_written=atomic_load(&k->written);
        for(int e=0;e<2;e++){ st->lost_packets[e]=atomic_load(&k->lost_pk[e]); st->lost_bytes[e]=atomic_load(&k->lost_by[e]); }
        st->control_dropped=atomic_load(&k->control_dropped); st->discarded_after_error=atomic_load(&k->discarded);
        st->high_water=atomic_load(&k->high_water); st->max_write=atomic_load(&k->max_write); st->io_error=k->io_errno;
        st->writes=atomic_load(&k->writes); st->write_ns=atomic_load(&k->write_ns); st->max_write_ns=atomic_load(&k->max_write_ns);
        st->slow_writes=atomic_load(&k->slow_writes); st->max_ready_gap_ns=atomic_load(&k->max_ready_gap_ns);
        st->loss_episodes=atomic_load(&k->loss_episodes); st->loss_in_write=atomic_load(&k->loss_in_write);
        st->max_in_write_at_loss_ns=atomic_load(&k->max_in_write_at_loss_ns);
        st->max_wake_backlog=atomic_load(&k->max_wake_backlog); st->released_bytes=atomic_load(&k->released_bytes); st->release_failures=atomic_load(&k->release_failures);
        st->spill_state=k->spill_state; st->spill_error=k->spill_error; st->spill_bytes=atomic_load(&k->spill_bytes);
        st->spill_peak=atomic_load(&k->spill_peak); st->spill_segments=atomic_load(&k->spill_segments);
        st->spill_floor_refusals=atomic_load(&k->spill_floor_refusals); st->spill_max_write_ns=atomic_load(&k->spill_max_write_ns);
    }
    int rc=k->io_errno?CC_ERR_IO:CC_OK;
    pthread_mutex_destroy(&k->m); pthread_cond_destroy(&k->cv); pthread_cond_destroy(&k->acv);
    free(k->bbuf); free(k->sdir); free(k->sbase);
    /* After a refused hand-back part of the ring's range may be unmapped and something else may have been mapped
     * there since; unmapping the whole range would take that with it. The address space is left to the process. */
    if(!atomic_load(&k->release_failures)) munmap(k->ring,k->cap);
    free(k);
    return rc;
}
