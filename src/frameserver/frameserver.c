#include "frameserver.h"
#include "../unit_parser/unit_parser.h"
#include "../signal_state/signal_state.h"
#include "../field_registration/field_registration.h"
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/qos.h>
#include <pthread/qos.h>

#define RING_ITEMS 128

// The publisher and the parser each name the fixed-raster unit size; they must be the same
// number or fp_publish would over-read into the neighbouring pool slot (silent, intermittent).
_Static_assert(FP_UNIT_BYTES == UNIT_PARSER_VIDEO_UNIT_BYTES, "publisher/parser unit size mismatch");

typedef enum { FS_DROP_NONE = 0, FS_DROP_POOL_FULL = 1 } fs_drop;

typedef struct {
    int slot;                              // pool slot holding the unit bytes, or -1
    fs_drop drop;                          // why an eligible unit carries no bytes (sidecar honesty)
    unit_video_observation obs;            // metadata copy; bytes/payload re-pointed to the slot
} fs_item;

struct frameserver {
    fs_config cfg;
    cc_session *cap;
    unit_parser *parser;
    signal_state *sig;
    field_registration *eng;
    fp_publisher *pub;
    FILE *log;
    // pool + ring (single producer = delivery thread, single consumer = worker)
    unsigned n_slots; uint8_t *pool; _Atomic int *slot_used;
    fs_item ring[RING_ITEMS]; _Atomic unsigned r_head, r_tail;
    pthread_mutex_t m; pthread_cond_t c;
    pthread_t worker; _Atomic int started, producer_done, worker_done;
    enum cc_end end_reason;
    fs_stats st; _Atomic uint64_t audio_records, audio_resync, dropped_pool_full, dropped_ring_full, video_obs, holes, unframed, shorts, other_fmt, ns0800;
    _Atomic unsigned pool_hw;              // written on the delivery thread, read by fs_get_stats
    _Atomic int stopped;
};

// ------------------------------------------------------------ producer side (delivery thread)
static int take_slot(frameserver *f){
    unsigned used = 0; int free_i = -1;
    for (unsigned i = 0; i < f->n_slots; i++){
        if (atomic_load(&f->slot_used[i])) used++; else if (free_i < 0) free_i = (int)i;
    }
    if (free_i >= 0) atomic_store(&f->slot_used[free_i], 1);
    unsigned occupancy = free_i >= 0 ? used + 1 : used;   // occupancy after this claim, never > n_slots
    if (occupancy > atomic_load_explicit(&f->pool_hw, memory_order_relaxed)) atomic_store_explicit(&f->pool_hw, occupancy, memory_order_relaxed);
    return free_i;
}
static void push(frameserver *f, const fs_item *it){
    unsigned h = atomic_load_explicit(&f->r_head, memory_order_relaxed);
    unsigned t = atomic_load_explicit(&f->r_tail, memory_order_acquire);
    // Ring full: the worker is behind. Distinct from pool exhaustion (slots held too long). No
    // worker ever sees this item, so it cannot get a sidecar row; it is counted, never silent.
    if (h - t >= RING_ITEMS){ atomic_fetch_add(&f->dropped_ring_full, 1); if (it->slot >= 0) atomic_store(&f->slot_used[it->slot], 0); return; }
    f->ring[h % RING_ITEMS] = *it;
    atomic_store_explicit(&f->r_head, h + 1, memory_order_release);
    if (pthread_mutex_trylock(&f->m) == 0){ pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m); }
}
static void on_video(void *ctx, const unit_video_observation *u){
    frameserver *f = ctx;
    atomic_fetch_add(&f->video_obs, 1);
    fs_item it; it.slot = -1; it.drop = FS_DROP_NONE; it.obs = *u; it.obs.bytes = NULL; it.obs.payload = NULL;
    if (u->fixed_raster_eligible && u->byte_count == UNIT_PARSER_VIDEO_UNIT_BYTES){
        int s = take_slot(f);
        if (s < 0){
            // Bytes are shed (§8 property 7) but the OBSERVATION is not: the item still reaches the
            // worker so the sidecar carries an explicit PoolFull row instead of an unmarked hole.
            atomic_fetch_add(&f->dropped_pool_full, 1); it.drop = FS_DROP_POOL_FULL;
        } else {
            memcpy(f->pool + (size_t)s * UNIT_PARSER_VIDEO_UNIT_BYTES, u->bytes, UNIT_PARSER_VIDEO_UNIT_BYTES);
            it.slot = s;
        }
    }
    push(f, &it);
}
static void on_audio(void *ctx, const unit_audio_observation *a){
    frameserver *f = ctx;
    atomic_fetch_add(&f->audio_records, 1);
    if (a->kind == UNIT_AUDIO_RESYNC) atomic_fetch_add(&f->audio_resync, 1);
}
static void cc_on_packet(void *ctx, const cc_packet *p){ frameserver *f = ctx; unit_parser_on_packet(f->parser, p); }
static void cc_on_loss(void *ctx, uint8_t ep, uint32_t n, uint64_t b){ frameserver *f = ctx; unit_parser_on_loss(f->parser, ep, n, b); }
static void cc_on_error(void *ctx, uint8_t ep, uint32_t seq, int st, int isf){ frameserver *f = ctx; unit_parser_on_error(f->parser, ep, seq, st, isf); }
static void cc_on_end(void *ctx, enum cc_end r){
    frameserver *f = ctx; f->end_reason = r;
    unit_parser_finish(f->parser);
    atomic_store(&f->producer_done, 1);
    pthread_mutex_lock(&f->m); pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m);
}

// ------------------------------------------------------------ worker side
static const char *transport_name(unit_transport_state t){
    switch (t){ case UNIT_TRANSPORT_COMPLETE: return "Complete"; case UNIT_TRANSPORT_HOLE: return "Hole";
                case UNIT_TRANSPORT_SHORT: return "Short"; default: return "Unframed"; }
}
static void log_header(FILE *L){
    fprintf(L, "ordinal,counter_extended,transport,kind,appearance,appearance_confidence,source,source_confidence,"
               "interval_id,unsettled,provisional_d1,provisional_d2,applied_d1,applied_d2,baseline_d1,baseline_d2,"
               "settled_known,settled_d1,settled_d2,resolution,evidence_mode,confidence,published,drop_reason\n");
}
static void process_item(frameserver *f, const fs_item *it){
    unit_video_observation obs = it->obs;
    const uint8_t *unit = NULL;
    if (it->slot >= 0){ unit = f->pool + (size_t)it->slot * UNIT_PARSER_VIDEO_UNIT_BYTES; obs.bytes = unit; obs.payload = unit + UNIT_PARSER_VIDEO_HEADER_BYTES; }
    switch (obs.transport){ case UNIT_TRANSPORT_HOLE: atomic_fetch_add(&f->holes, 1); break;
        case UNIT_TRANSPORT_SHORT: atomic_fetch_add(&f->shorts, 1); break;
        case UNIT_TRANSPORT_UNFRAMED: atomic_fetch_add(&f->unframed, 1); break; default: break; }
    if (obs.kind == UNIT_VIDEO_DEVICE_NO_SIGNAL_0800) atomic_fetch_add(&f->ns0800, 1);
    else if (obs.kind == UNIT_VIDEO_OTHER_FORMAT) atomic_fetch_add(&f->other_fmt, 1);

    signal_result sr; memset(&sr, 0, sizeof sr);
    // obs.bytes/payload are NULL for units without a pool slot (ineligible, or PoolFull); the
    // classifier's contract is metadata-only for those (signal_state.c: !fixed_raster_eligible || !bytes).
    bool classified = signal_state_classify(f->sig, &obs, NULL, &sr);
    fieldreg_decision d; memset(&d, 0, sizeof d); bool have_d = false; int published = 0;
    if (it->drop == FS_DROP_POOL_FULL) f->st.exact_units++;   // eligible, bytes shed: still an exact unit
    if (unit){
        f->st.exact_units++;
        if (classified){
            if (sr.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT){ fieldreg_begin_segment(f->eng); f->st.begin_segment_calls++; }
            else if (sr.actions & SIGNAL_ACTION_REGISTRATION_DISCONTINUITY){ fieldreg_discontinuity(f->eng); f->st.discontinuity_calls++; }
        }
        have_d = fieldreg_process(f->eng, unit, &d);
        if (have_d && classified)
            signal_state_note_registration(f->sig, &sr, d.frame_observation_support > 0,
                                           d.frame_observation_d1, d.frame_observation_d2, d.confidence);
        if (classified && sr.unsettled) f->st.unsettled_units++;
        int rc = fp_publish(f->pub, unit, FP_UNIT_BYTES, (uint32_t)obs.counter_extended,
                            have_d ? d.applied_d1 : 0, have_d ? d.applied_d2 : 0,
                            obs.transport == UNIT_TRANSPORT_COMPLETE ? FP_TRANSPORT_COMPLETE : FP_TRANSPORT_SHORT);
        if (rc == 0){ f->st.published++; published = 1; } else if (rc == 1) f->st.publisher_dropped++;
        // The publisher copied the bytes: free the slot before the (slow) log write so slot
        // occupancy is the analysis time, not analysis + I/O.
        atomic_store(&f->slot_used[it->slot], 0);
    }
    if (f->log){
        fprintf(f->log, "%llu,%llu,%s,%d,%s,%.3f,%s,%.3f,%llu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%s,%.3f,%d,%s\n",
            (unsigned long long)obs.ordinal, (unsigned long long)obs.counter_extended, transport_name(obs.transport), (int)obs.kind,
            classified ? signal_appearance_name(sr.appearance) : "Unclassified", classified ? sr.appearance_confidence : 0.0,
            classified ? signal_source_state_name(sr.source) : "Unknown", classified ? sr.source_confidence : 0.0,
            (unsigned long long)(classified ? sr.unsettled_interval_id : 0), classified && sr.unsettled,
            have_d ? d.frame_observation_d1 : 0, have_d ? d.frame_observation_d2 : 0,
            have_d ? d.applied_d1 : 0, have_d ? d.applied_d2 : 0,
            have_d ? d.baseline_d1 : 0, have_d ? d.baseline_d2 : 0,
            classified && sr.settled_phase_known, classified ? sr.settled_d1 : 0, classified ? sr.settled_d2 : 0,
            "Immediate", have_d ? fieldreg_mode_name(d.mode) : "None", have_d ? d.confidence : 0.0, published,
            it->drop == FS_DROP_POOL_FULL ? "PoolFull" : "None");
        f->st.log_rows++;
    }
}
static void *worker_main(void *arg){
    frameserver *f = arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED, 0);
    for (;;){
        unsigned t = atomic_load_explicit(&f->r_tail, memory_order_relaxed);
        unsigned h = atomic_load_explicit(&f->r_head, memory_order_acquire);
        if (h == t){
            if (atomic_load(&f->producer_done)){
                // producer_done is stored after the producer's last release-store of r_head, so
                // an acquire re-load here sees every item published before it. Exiting on the
                // stale h would strand the tail units (and their sidecar rows).
                h = atomic_load_explicit(&f->r_head, memory_order_acquire);
                if (h == t) break;
                continue;
            }
            pthread_mutex_lock(&f->m);
            h = atomic_load_explicit(&f->r_head, memory_order_acquire);
            if (h == t && !atomic_load(&f->producer_done)){
                struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_nsec += 100*1000000L;
                if (ts.tv_nsec >= 1000000000L){ ts.tv_sec++; ts.tv_nsec -= 1000000000L; }
                pthread_cond_timedwait(&f->c, &f->m, &ts);
            }
            pthread_mutex_unlock(&f->m);
            continue;
        }
        fs_item it = f->ring[t % RING_ITEMS];
        atomic_store_explicit(&f->r_tail, t + 1, memory_order_release);
        process_item(f, &it);
    }
    atomic_store(&f->worker_done, 1);
    if (f->cfg.on_end) f->cfg.on_end(f->cfg.end_ctx, f->end_reason);
    return NULL;
}

// ------------------------------------------------------------ lifecycle
static void count_sink(void *ctx, const fp_frame *fr){ (void)ctx; (void)fr; }
int fs_open(frameserver **out, const fs_config *cfg){
    if (!out || !cfg) return -1;
    frameserver *f = calloc(1, sizeof *f); if (!f) return -1;
    f->cfg = *cfg;
    f->n_slots = cfg->pool_units ? cfg->pool_units : 64;   // sized to a worst-case worker stall (~2 s), not steady state
    f->pool = malloc((size_t)f->n_slots * UNIT_PARSER_VIDEO_UNIT_BYTES);
    f->slot_used = calloc(f->n_slots, sizeof(_Atomic int));
    f->parser = aligned_alloc(unit_parser_alignment(), unit_parser_size());
    f->sig = aligned_alloc(signal_state_alignment(), signal_state_size());
    f->eng = aligned_alloc(64, ((fieldreg_state_size() + 63) / 64) * 64);
    if (!f->pool || !f->slot_used || !f->parser || !f->sig || !f->eng){ fs_close(f); return -1; }
    unit_parser_callbacks pcb = { on_video, on_audio, f };
    unit_parser_init(f->parser, NULL, &pcb);
    signal_state_config sc = signal_state_default_config(); signal_state_init(f->sig, &sc);
    fieldreg_config ec = fieldreg_default_config(); fieldreg_init(f->eng, &ec);
    fp_sink sink = cfg->sink.on_frame ? cfg->sink : (fp_sink){ count_sink, NULL };
    if (fp_open(&f->pub, cfg->surface_pool ? cfg->surface_pool : 6, &sink) != 0){ fs_close(f); return -1; }
    if (cfg->decision_log){ f->log = fopen(cfg->decision_log, "w"); if (!f->log){ fs_close(f); return -1; } log_header(f->log); }
    pthread_mutex_init(&f->m, NULL); pthread_cond_init(&f->c, NULL);
    cc_callbacks ccb = { cc_on_packet, cc_on_loss, cc_on_error, NULL, cc_on_end, f };
    if (cc_open(&f->cap, &cfg->capture, &ccb) != 0){ fs_close(f); return -1; }
    *out = f; return 0;
}
int fs_start(frameserver *f){
    if (!f || atomic_load(&f->started)) return -1;
    atomic_store(&f->started, 1);
    unit_parser_begin_epoch(f->parser, 1); signal_state_begin_epoch(f->sig, 1);
    if (pthread_create(&f->worker, NULL, worker_main, f)) return -1;
    return cc_start(f->cap);
}
int fs_stop(frameserver *f){
    if (!f || !atomic_load(&f->started)) return -1;
    if (atomic_exchange(&f->stopped, 1)) return 0;   // idempotent: a second stop is a no-op
    cc_stop(f->cap);                        // fires on_end -> producer_done
    pthread_join(f->worker, NULL);
    if (f->log){ fclose(f->log); f->log = NULL; }
    return 0;
}
void fs_get_stats(const frameserver *f, fs_stats *o){
    *o = f->st;
    o->video_observations = atomic_load(&f->video_obs); o->audio_records = atomic_load(&f->audio_records);
    o->audio_resync = atomic_load(&f->audio_resync); o->dropped_pool_full = atomic_load(&f->dropped_pool_full);
    o->dropped_ring_full = atomic_load(&f->dropped_ring_full); o->pool_high_water = atomic_load(&f->pool_hw);
    o->holes = atomic_load(&f->holes); o->unframed = atomic_load(&f->unframed); o->short_units = atomic_load(&f->shorts);
    o->other_format = atomic_load(&f->other_fmt); o->no_signal_0800 = atomic_load(&f->ns0800);
}
void fs_close(frameserver *f){
    if (!f) return;
    if (atomic_load(&f->started)) fs_stop(f);   // close-after-start must not free state under live threads
    if (f->cap) cc_close(f->cap);
    if (f->pub) fp_close(f->pub);
    if (f->log) fclose(f->log);
    free(f->pool); free((void *)f->slot_used); free(f->parser); free(f->sig); free(f->eng); free(f);
}
