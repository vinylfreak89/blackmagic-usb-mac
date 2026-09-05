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

#ifndef RING_ITEMS
#define RING_ITEMS 128      // overridable for tests that must exhaust the item ring deterministically
#endif
_Static_assert(RING_ITEMS >= 2, "frameserver ring needs one data slot plus one terminal-loss slot");

// The publisher and the parser each name the fixed-raster unit size; they must be the same
// number or fp_publish would over-read into the neighbouring pool slot (silent, intermittent).
_Static_assert(FP_UNIT_BYTES == UNIT_PARSER_VIDEO_UNIT_BYTES, "publisher/parser unit size mismatch");

typedef enum { FS_DROP_NONE = 0, FS_DROP_POOL_FULL = 1 } fs_drop;
typedef enum { FS_LIFE_OPEN, FS_LIFE_STARTING, FS_LIFE_RUNNING,
               FS_LIFE_STOPPING, FS_LIFE_STOPPED } fs_life;

typedef struct {
    int slot;                              // pool slot holding the unit bytes, or -1
    fs_drop drop;                          // why an eligible unit carries no bytes (sidecar honesty)
    int eligible, gap_only;
    uint64_t preceding_ring_drops;
    unit_video_observation obs;            // metadata copy; bytes/payload re-pointed to the slot
} fs_item;

struct frameserver {
    fs_config cfg;
    cc_session *cap;
    unit_parser *parser;
    signal_state *sig;
    field_registration *eng;
    fp_publisher *pub;
    audio_publisher *aud;
    // audio queue: single producer (delivery thread, inside the publisher's sink) -> audio worker
    ap_block *aq; uint8_t *aq_pcm; unsigned aq_slots, aq_cap_frames; _Atomic unsigned aq_head, aq_tail;
    pthread_mutex_t aq_m; pthread_cond_t aq_c; int aq_m_init, aq_c_init;
    pthread_t audio_worker; int audio_worker_created; _Atomic int audio_done, audio_worker_done;
    uint64_t aq_drops_pending;           // producer-owned: flagged on the next enqueued block
    ap_sink user_audio_sink;
    _Atomic uint64_t aq_dropped_blocks, aq_dropped_frames;
    uint64_t aq_delivered_blocks, aq_delivered_frames;   // audio worker owned
    _Atomic uint64_t audio_master_frames;
    _Atomic int workers_terminal;        // video + audio workers that have drained; the second fires on_end
    FILE *log; pthread_mutex_t log_m; int log_m_init; uint64_t log_file_errors;   // write errors in the CURRENTLY attached file (reset at attach; fs_log_stop reports them)   // log_m: worker row writes vs control-thread attach/detach (fs_log_start/stop)
    // pool + ring (single producer = delivery thread, single consumer = worker)
    unsigned n_slots; uint8_t *pool; _Atomic int *slot_used;
    fs_item ring[RING_ITEMS]; _Atomic unsigned r_head, r_tail;
    pthread_mutex_t m; pthread_cond_t c;
    pthread_mutex_t life_m; pthread_cond_t life_c;
    int m_init,c_init,life_m_init,life_c_init;
    pthread_t worker; _Atomic int producer_done, worker_done;
    fs_life life; int worker_created, start_gate; _Atomic int notify_end;   // read by both workers, written by fs_start
    enum cc_end end_reason;
    fs_stats st; _Atomic uint64_t audio_records, audio_resync, dropped_pool_full, dropped_ring_full, video_obs, holes, unframed, shorts, other_fmt, ns0800;
    _Atomic unsigned pool_hw;              // written on the delivery thread, read by fs_get_stats
    _Atomic uint64_t eligible_ingress;     // fixed-raster-eligible observations seen at ingress (denominator)
    uint64_t ring_drops_pending;           // producer-owned: attached only to a later item
    uint64_t ring_drop_first_ordinal;
    int8_t last_comb_correction;
    uint64_t comb_correction_install_ordinal;
};

#ifdef FRAMESERVER_TEST_HOOKS
extern void fs_test_after_empty_snapshot(frameserver *f);
extern void fs_test_before_producer_done(frameserver *f);
extern void fs_test_after_log_row(frameserver *f, FILE *log);
#else
#define fs_test_after_empty_snapshot(f) ((void)(f))
#define fs_test_before_producer_done(f) ((void)(f))
#define fs_test_after_log_row(f,L) ((void)(f),(void)(L))
#endif

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
static int push(frameserver *f, const fs_item *it){
    unsigned h = atomic_load_explicit(&f->r_head, memory_order_relaxed);
    unsigned t = atomic_load_explicit(&f->r_tail, memory_order_acquire);
    // Ring full: the worker is behind. Distinct from pool exhaustion (slots held too long).
    // Missing observations are represented as an ordered range on the next retained row (or a
    // terminal range row); an individual dropped observation cannot carry its own row.
    // One slot is reserved for the terminal RingFullTail range.  The producer therefore never
    // has to wait for a slow publisher merely to make downstream loss self-describing.
    if (h - t >= RING_ITEMS-1){
        atomic_fetch_add(&f->dropped_ring_full, 1);
        if (!f->ring_drops_pending) f->ring_drop_first_ordinal = it->obs.ordinal;
        f->ring_drops_pending++;
        if (it->eligible) f->st.eligible_ring_drops++;
        if (it->slot >= 0) atomic_store(&f->slot_used[it->slot], 0); return 0;
    }
    fs_item q=*it;
    q.preceding_ring_drops=f->ring_drops_pending;
    f->ring_drops_pending=0;
    f->ring[h % RING_ITEMS] = q;
    atomic_store_explicit(&f->r_head, h + 1, memory_order_release);
    if (pthread_mutex_trylock(&f->m) == 0){ pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m); }
    return 1;
}
static void push_tail_gap(frameserver *f){
    if(!f->ring_drops_pending) return;
    fs_item q; memset(&q,0,sizeof q); q.slot=-1; q.gap_only=1;
    q.obs.ordinal=f->ring_drop_first_ordinal; q.preceding_ring_drops=f->ring_drops_pending;
    unsigned h=atomic_load_explicit(&f->r_head,memory_order_relaxed);
    // Normal items cannot occupy the reserved slot, so this is an invariant, not backpressure.
    f->ring[h%RING_ITEMS]=q; f->ring_drops_pending=0;
    atomic_store_explicit(&f->r_head,h+1,memory_order_release);
    if(pthread_mutex_trylock(&f->m)==0){ pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m); }
}
static void on_video(void *ctx, const unit_video_observation *u){
    frameserver *f = ctx;
    atomic_fetch_add(&f->video_obs, 1);
    fs_item it; memset(&it,0,sizeof it); it.slot = -1; it.drop = FS_DROP_NONE; it.obs = *u; it.obs.bytes = NULL; it.obs.payload = NULL;
    if (u->fixed_raster_eligible && u->byte_count == UNIT_PARSER_VIDEO_UNIT_BYTES){
        it.eligible=1;
        atomic_fetch_add(&f->eligible_ingress, 1);
        int s = take_slot(f);
        if (s < 0){
            // Bytes are shed (§8 property 7) but the OBSERVATION is not: the item still reaches the
            // worker so the sidecar carries an explicit PoolFull row instead of an unmarked hole.
            it.drop = FS_DROP_POOL_FULL;
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
    ap_on_audio(f->aud, a);                 // delivery thread: bounded, allocation-free
}
// publisher sink (delivery thread): copy the block into the bounded queue or drop it explicitly
static void aq_enqueue(void *ctx, const ap_block *b){
    frameserver *f = ctx;
    unsigned h = atomic_load_explicit(&f->aq_head, memory_order_relaxed);
    unsigned t = atomic_load_explicit(&f->aq_tail, memory_order_acquire);
    if (h - t >= f->aq_slots || b->n_frames > f->aq_cap_frames){
        atomic_fetch_add(&f->aq_dropped_blocks, 1); atomic_fetch_add(&f->aq_dropped_frames, b->n_frames);
        f->aq_drops_pending++; return;      // consumer too slow: shed HERE, never upstream
    }
    unsigned i = h % f->aq_slots;
    uint8_t *dst = f->aq_pcm + (size_t)i * f->aq_cap_frames * AP_BYTES_PER_FRAME;
    memcpy(dst, b->s24le, (size_t)b->n_frames * AP_BYTES_PER_FRAME);
    f->aq[i] = *b; f->aq[i].s24le = dst;
    if (f->aq_drops_pending){ f->aq[i].flags |= AP_FLAG_DISCONTINUITY_BEFORE; f->aq_drops_pending = 0; }
    atomic_store_explicit(&f->aq_head, h + 1, memory_order_release);
    if (pthread_mutex_trylock(&f->aq_m) == 0){ pthread_cond_signal(&f->aq_c); pthread_mutex_unlock(&f->aq_m); }
}
static void *audio_worker_main(void *arg){
    frameserver *f = arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED, 0);
    for (;;){
        unsigned t = atomic_load_explicit(&f->aq_tail, memory_order_relaxed);
        unsigned h = atomic_load_explicit(&f->aq_head, memory_order_acquire);
        if (h == t){
            if (atomic_load(&f->audio_done)){
                h = atomic_load_explicit(&f->aq_head, memory_order_acquire);   // same drain discipline as the video worker
                if (h == t) break;
                continue;
            }
            pthread_mutex_lock(&f->aq_m);
            h = atomic_load_explicit(&f->aq_head, memory_order_acquire);
            if (h == t && !atomic_load(&f->audio_done)){
                struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts); ts.tv_nsec += 100*1000000L;
                if (ts.tv_nsec >= 1000000000L){ ts.tv_sec++; ts.tv_nsec -= 1000000000L; }
                pthread_cond_timedwait(&f->aq_c, &f->aq_m, &ts);
            }
            pthread_mutex_unlock(&f->aq_m);
            continue;
        }
        const ap_block *b = &f->aq[t % f->aq_slots];
        if (f->user_audio_sink.on_block) f->user_audio_sink.on_block(f->user_audio_sink.ctx, b);
        f->aq_delivered_blocks++; f->aq_delivered_frames += b->n_frames;
        atomic_store_explicit(&f->aq_tail, t + 1, memory_order_release);
    }
    atomic_store(&f->audio_worker_done, 1);
    // on_end means BOTH media workers are terminal: whichever drains second fires it
    if (atomic_fetch_add(&f->workers_terminal, 1) == 1 && atomic_load_explicit(&f->notify_end, memory_order_acquire) && f->cfg.on_end)
        f->cfg.on_end(f->cfg.end_ctx, f->end_reason);
    return NULL;
}
static void cc_on_packet(void *ctx, const cc_packet *p){ frameserver *f = ctx; unit_parser_on_packet(f->parser, p); }
static void cc_on_loss(void *ctx, uint8_t ep, uint32_t n, uint64_t b){ frameserver *f = ctx; unit_parser_on_loss(f->parser, ep, n, b); }
static void cc_on_error(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){ frameserver *f = ctx; unit_parser_on_error(f->parser, ep, seq, st, kind); }
static void cc_on_end(void *ctx, enum cc_end r){
    frameserver *f = ctx; f->end_reason = r;
    unit_parser_finish(f->parser);
    ap_flush(f->aud);                       // the tail of the last unit, with its provenance
    atomic_store_explicit(&f->audio_done, 1, memory_order_release);   // producer is done: the audio worker drains and exits
    pthread_mutex_lock(&f->aq_m); pthread_cond_signal(&f->aq_c); pthread_mutex_unlock(&f->aq_m);
    fs_test_before_producer_done(f);
    push_tail_gap(f);
    atomic_store_explicit(&f->producer_done, 1, memory_order_release);
    pthread_mutex_lock(&f->m); pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m);
}

// ------------------------------------------------------------ worker side
static const char *transport_name(unit_transport_state t){
    switch (t){ case UNIT_TRANSPORT_COMPLETE: return "Complete"; case UNIT_TRANSPORT_HOLE: return "Hole";
                case UNIT_TRANSPORT_SHORT: return "Short"; default: return "Unframed"; }
}
static int log_header(FILE *L){
    return fprintf(L, "ordinal,counter_extended,transport,kind,appearance,appearance_confidence,source,source_confidence,"
               "interval_id,unsettled,provisional_d1,provisional_d2,applied_d1,applied_d2,baseline_d1,baseline_d2,"
               "settled_known,settled_d1,settled_d2,resolution,evidence_mode,confidence,"
               "f1_reason,f1_gauge,f1_insert_present,f1_insert_bytes,f1_insert_relation,f1_parity_candidates,f1_fallback_candidates,f1_gauge_line,f1_gauge_bytes,f1_gauge_amplitude,f1_geometry_d,f1_blank_mean,f1_body_witness_valid,f1_body_shift,f1_body_mad,f1_body_geometry_agrees,f1_body_reference_top,f1_body_implied_top,f1_body_differential,f1_body_common_mode,f1_picture_position_valid,f1_measured_picture_top,f1_picture_from_body,f1_raw_top,f1_raw_bottom,f1_raw_height,f1_geometry_measurable,f1_bottom_censored,f1_lock_state,f1_zero_source,f1_lock_id,f1_lock_top,f1_lock_height,f1_lock_height_known,f1_clip_state,f1_clip_ceiling,f1_expected_bottom,f1_lines_lost,f1_invariant_residual,f1_saved_good_valid,f1_saved_good_top,f1_saved_good_bottom,f1_saved_good_height,f1_saved_good_bottom_censored,f1_saved_good_applied_d,f1_saved_good_gauge,f1_saved_good_ordinal,f1_damage_hold_length,f1_damage_jump,"
               "f2_reason,f2_gauge,f2_insert_present,f2_insert_bytes,f2_insert_relation,f2_parity_candidates,f2_fallback_candidates,f2_gauge_line,f2_gauge_bytes,f2_gauge_amplitude,f2_geometry_d,f2_blank_mean,f2_body_witness_valid,f2_body_shift,f2_body_mad,f2_body_geometry_agrees,f2_body_reference_top,f2_body_implied_top,f2_body_differential,f2_body_common_mode,f2_picture_position_valid,f2_measured_picture_top,f2_picture_from_body,f2_raw_top,f2_raw_bottom,f2_raw_height,f2_geometry_measurable,f2_bottom_censored,f2_lock_state,f2_zero_source,f2_lock_id,f2_lock_top,f2_lock_height,f2_lock_height_known,f2_clip_state,f2_clip_ceiling,f2_expected_bottom,f2_lines_lost,f2_invariant_residual,f2_saved_good_valid,f2_saved_good_top,f2_saved_good_bottom,f2_saved_good_height,f2_saved_good_bottom_censored,f2_saved_good_applied_d,f2_saved_good_gauge,f2_saved_good_ordinal,f2_damage_hold_length,f2_damage_jump,"
               "parity_state,comb_check,comb_best_shift,parity_bias,comb_best_energy,comb_second_energy,comb_static_fraction,comb_correction,comb_correction_install_ordinal,comb_safe,published,drop_reason,schema_version,preceding_ring_drops\n") < 0 ? -1 : 0;
}

static int log_field(FILE *L, const fieldreg_field_decision *d)
{
    const char *reason = d ? fieldreg_mode_name(d->reason) : "None";
    const char *gauge = d ? fieldreg_gauge_name(d->gauge) : "None";
    const char *insert_relation = d ? fieldreg_insert_relation_name(d->insert_relation) : "None";
    const char *lock = d ? fieldreg_lock_state_name(d->lock_state) : "Unlocked";
    const char *zero = d ? fieldreg_zero_source_name(d->zero_source) : "None";
    const char *clip = d ? fieldreg_clip_state_name(d->clip_state) : "ClipUnknown";
    const char *saved_gauge = d ?
        fieldreg_gauge_name(d->saved_good_gauge) : "None";
    char insert_bytes[5] = "", gauge_bytes[5] = "";
    if (d && d->insert_present)
        snprintf(insert_bytes, sizeof insert_bytes, "%02x%02x", d->insert_byte1, d->insert_byte2);
    if (d && d->gauge_row >= 0 &&
        (d->gauge == FIELDREG_GAUGE_CEA608_PARITY ||
         d->gauge == FIELDREG_GAUGE_LINE22_DATA))
        snprintf(gauge_bytes, sizeof gauge_bytes, "%02x%02x", d->gauge_byte1, d->gauge_byte2);
    return fprintf(L,
                   ",%s,%s,%d,%s,%s,%u,%u,%d,%s,%.3f,%d,%.3f"
                   ",%d,%d,%.3f"
                   ",%d,%d,%d,%d,%d,%d,%d,%d"
                   ",%d,%d,%d,%d,%d"
                   ",%s,%s,%u,%d,%d,%d,%s,%d,%d,%d,%d"
                   ",%d,%d,%d,%d,%d,%d,%s,%llu,%u,%d",
                   reason, gauge, d && d->insert_present, insert_bytes, insert_relation,
                   d ? d->parity_candidate_count : 0,
                   d ? d->fallback_candidate_count : 0,
                   d && d->gauge_row >= 0 ? d->gauge_row + 4 : -1, gauge_bytes,
                   d ? d->gauge_amplitude : 0.0,
                   d ? d->geometry_d : FIELDREG_UNKNOWN,
                   d ? d->blank_mean : 0.0,
                   d && d->body_witness_valid,
                   d && d->body_witness_valid ? d->body_shift : FIELDREG_UNKNOWN,
                   d ? d->body_mad : 0.0,
                   d && d->body_geometry_agrees,
                   d && d->body_reference_top >= 0 ? d->body_reference_top + 4 : -1,
                   d && d->body_implied_top >= 0 ? d->body_implied_top + 4 : -1,
                   d && d->body_differential,
                   d && d->body_common_mode,
                   d && d->picture_position_valid,
                   d && d->measured_picture_top >= 0 ? d->measured_picture_top + 4 : -1,
                   d && d->picture_from_body,
                   d && d->raw_top >= 0 ? d->raw_top + 4 : -1,
                   d && d->raw_bottom >= 0 ? d->raw_bottom + 4 : -1,
                   d ? d->raw_height : -1, d && d->geometry_measurable,
                   d && d->bottom_censored, lock, zero, d ? d->lock_id : 0,
                   d && d->lock_top >= 0 ? d->lock_top + 4 : -1,
                   d ? d->lock_height : -1, d && d->lock_height_known, clip,
                   d && d->clip_ceiling >= 0 ? d->clip_ceiling + 4 : -1,
                   d && d->expected_bottom >= 0 ? d->expected_bottom + 4 : -1,
                   d ? d->lines_lost : 0, d ? d->invariant_residual : 0,
                   d && d->saved_good_valid,
                   d && d->saved_good_top >= 0 ? d->saved_good_top + 4 : -1,
                   d && d->saved_good_bottom >= 0 ? d->saved_good_bottom + 4 : -1,
                   d ? d->saved_good_height : -1,
                   d && d->saved_good_bottom_censored,
                   d ? d->saved_good_applied_d : 0, saved_gauge,
                   (unsigned long long)(d ? d->saved_good_ordinal : 0),
                   d ? d->damage_hold_length : 0,
                   d ? d->damage_jump : 0);
}
static void process_item(frameserver *f, const fs_item *it){
    if(it->gap_only){
        fieldreg_discontinuity(f->eng); f->st.discontinuity_calls++;
        f->st.ring_drops_logged+=it->preceding_ring_drops; f->st.ring_gap_rows++;
        pthread_mutex_lock(&f->log_m);
        if(f->log){
            int wr = fprintf(f->log,"%llu,0,Hole,-1,Unclassified,0.000,Unknown,0.000,0,0,,,,0,0,0,0,0,Immediate,None,0.000",
                             (unsigned long long)it->obs.ordinal);
            if (wr >= 0) wr = log_field(f->log, NULL);
            if (wr >= 0) wr = log_field(f->log, NULL);
            if (wr >= 0) wr = fprintf(f->log, ",Uncalibrated,n.a.,-128,0,0.000,0.000,0.000,%d,%lld,0,0,RingFullTail,%u,%llu\n",
                                      f->last_comb_correction,
                                      f->comb_correction_install_ordinal == UINT64_MAX ?
                                      -1LL : (long long)f->comb_correction_install_ordinal,
                                      FS_DECISION_LOG_SCHEMA,
                                      (unsigned long long)it->preceding_ring_drops);
            if(wr < 0){ f->st.log_write_errors++; f->log_file_errors++; }
            else f->st.log_rows++;
            fs_test_after_log_row(f, f->log);
        }
        pthread_mutex_unlock(&f->log_m);
        return;
    }
    unit_video_observation obs = it->obs;
    const uint8_t *unit = NULL;
    if (it->slot >= 0){ unit = f->pool + (size_t)it->slot * UNIT_PARSER_VIDEO_UNIT_BYTES; obs.bytes = unit; obs.payload = unit + UNIT_PARSER_VIDEO_HEADER_BYTES; }
    switch (obs.transport){ case UNIT_TRANSPORT_HOLE: atomic_fetch_add(&f->holes, 1); break;
        case UNIT_TRANSPORT_SHORT: atomic_fetch_add(&f->shorts, 1); break;
        case UNIT_TRANSPORT_UNFRAMED: atomic_fetch_add(&f->unframed, 1); break; default: break; }
    if (obs.kind == UNIT_VIDEO_DEVICE_NO_SIGNAL_0800) atomic_fetch_add(&f->ns0800, 1);
    else if (obs.kind == UNIT_VIDEO_OTHER_FORMAT) atomic_fetch_add(&f->other_fmt, 1);

    uint64_t rd = it->preceding_ring_drops;
    signal_context signal_ctx = {
        .host_raster_unobserved = it->drop == FS_DROP_POOL_FULL,
        .host_observations_missing_before = rd != 0,
    };
    signal_result sr; memset(&sr, 0, sizeof sr);
    // obs.bytes/payload are NULL for units without a pool slot (ineligible, or PoolFull); the
    // classifier's contract is metadata-only for those (signal_state.c: !fixed_raster_eligible || !bytes).
    bool classified = signal_state_classify(f->sig, &obs, &signal_ctx, &sr);
    fieldreg_decision d; memset(&d, 0, sizeof d); bool have_d = false; int published = 0;
    // Ring-full drops since the previous processed item: folded into this row (locatable in time)
    // and a byte discontinuity for the engine's temporal state.
    if (rd){ f->st.ring_drops_logged += rd; fieldreg_discontinuity(f->eng); f->st.discontinuity_calls++; }
    // Registration actions are dispatched for EVERY classified observation, not only those with
    // bytes: holes, short and unframed units carry the discontinuity the engine must see before
    // the next exact unit, and they never have a retained raster.
    if (classified){
        if (sr.actions & SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT){
            fieldreg_begin_segment(f->eng); f->st.begin_segment_calls++;
            f->last_comb_correction = 0;
            f->comb_correction_install_ordinal = UINT64_MAX;
        }
        else if (sr.actions & SIGNAL_ACTION_REGISTRATION_DISCONTINUITY){ fieldreg_discontinuity(f->eng); f->st.discontinuity_calls++; }
    }
    if (it->drop == FS_DROP_POOL_FULL){
        // eligible, bytes shed here: still an exact unit for accounting, and a byte discontinuity
        // for the engine's temporal state (the classifier only knows "no bytes", not why)
        atomic_fetch_add(&f->dropped_pool_full,1);
        f->st.exact_units++; fieldreg_discontinuity(f->eng); f->st.discontinuity_calls++;
    }
    if (unit){
        f->st.exact_units++;
        const fieldreg_process_context reg_ctx = {
            .ordinal = obs.ordinal,
            .program_like = classified &&
                sr.appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE,
        };
        have_d = fieldreg_process_ex(f->eng, unit, &reg_ctx, &d);
        if (have_d && d.comb_correction != f->last_comb_correction) {
            f->last_comb_correction = d.comb_correction;
            f->comb_correction_install_ordinal = d.comb_correction == 0 ?
                                                  UINT64_MAX : obs.ordinal;
        }
        if (have_d && classified)
            /* signal_state's observation API accepts a complete (d1,d2), not
             * a field-validity mask. Partial v9 support remains real and is
             * fully reflected by applied_known below; passing it as an
             * observation would fabricate FIELDREG_UNKNOWN for one field and
             * count that sentinel as phase chatter. */
            signal_state_note_registration(f->sig, &sr, d.frame_observation_support == 2,
                                           d.frame_observation_d1, d.frame_observation_d2,
                                           d.confidence, true,
                                           d.applied_d1, d.applied_d2);
        if (classified && sr.unsettled) f->st.unsettled_units++;
        uint64_t apts = 0; int aknown = ap_lookup(f->aud, obs.epoch, obs.counter_extended, &apts, NULL);   // audio-clock time of this unit
        if (aknown) atomic_fetch_add(&f->audio_master_frames, 1);
        int rc = fp_publish(f->pub, unit, FP_UNIT_BYTES, obs.counter_extended,
                            have_d ? d.applied_d1 : 0, have_d ? d.applied_d2 : 0,
                            obs.transport == UNIT_TRANSPORT_COMPLETE ? FP_TRANSPORT_COMPLETE : FP_TRANSPORT_SHORT,
                            aknown, apts);
        if (rc == 0){ f->st.published++; published = 1; } else if (rc == 1) f->st.publisher_dropped++;
        // The publisher copied the bytes: free the slot before the (slow) log write so slot
        // occupancy is the analysis time, not analysis + I/O.
        atomic_store(&f->slot_used[it->slot], 0);
    }
    // The attach/detach lock is held only for this one buffered fprintf; the control thread's
    // fopen/fclose happen outside it (fs_log_start/fs_log_stop), so the worker never waits on I/O it did not issue.
    pthread_mutex_lock(&f->log_m);
    if (f->log){
        int wr = fprintf(f->log, "%llu,%llu,%s,%d,%s,%.3f,%s,%.3f,%llu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%s,%.3f",
            (unsigned long long)obs.ordinal, (unsigned long long)obs.counter_extended, transport_name(obs.transport), (int)obs.kind,
            classified ? signal_appearance_name(sr.appearance) : "Unclassified", classified ? sr.appearance_confidence : 0.0,
            classified ? signal_source_state_name(sr.source) : "Unknown", classified ? sr.source_confidence : 0.0,
            (unsigned long long)(classified ? sr.unsettled_interval_id : 0), classified && sr.unsettled,
            have_d ? d.frame_observation_d1 : 0, have_d ? d.frame_observation_d2 : 0,
            have_d ? d.applied_d1 : 0, have_d ? d.applied_d2 : 0,
            have_d ? d.baseline_d1 : 0, have_d ? d.baseline_d2 : 0,
            classified && sr.settled_phase_known, classified ? sr.settled_d1 : 0, classified ? sr.settled_d2 : 0,
            "Immediate", have_d ? fieldreg_mode_name(d.mode) : "None", have_d ? d.confidence : 0.0);
        if (wr >= 0) wr = log_field(f->log, have_d ? &d.field[0] : NULL);
        if (wr >= 0) wr = log_field(f->log, have_d ? &d.field[1] : NULL);
        if (wr >= 0) wr = fprintf(f->log, ",%s,%s,%d,%d,%.3f,%.3f,%.6f,%d,%lld,%d,%d,%s,%u,%llu\n",
            have_d ? fieldreg_parity_state_name(d.parity_state) : "Uncalibrated",
            have_d ? fieldreg_comb_check_name(d.comb_check) : "n.a.",
            have_d ? d.comb_best_shift : FIELDREG_UNKNOWN,
            have_d ? d.parity_bias : 0,
            have_d ? d.comb_best_energy : 0.0,
            have_d ? d.comb_second_energy : 0.0,
            have_d ? d.comb_static_fraction : 0.0,
            have_d ? d.comb_correction : f->last_comb_correction,
            f->comb_correction_install_ordinal == UINT64_MAX ?
            -1LL : (long long)f->comb_correction_install_ordinal,
            have_d && d.comb_safe, published,
            it->drop == FS_DROP_POOL_FULL ? "PoolFull" : (!published && unit ? "PublisherFull" : "None"),
            FS_DECISION_LOG_SCHEMA, (unsigned long long)rd);
        if (wr < 0){ f->st.log_write_errors++; f->log_file_errors++; } else f->st.log_rows++;   // a failed row is never counted as written
        fs_test_after_log_row(f, f->log);
    }
    pthread_mutex_unlock(&f->log_m);
}
static void *worker_main(void *arg){
    frameserver *f = arg;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED, 0);
    pthread_mutex_lock(&f->life_m);
    while(!f->start_gate) pthread_cond_wait(&f->life_c,&f->life_m);
    pthread_mutex_unlock(&f->life_m);
    for (;;){
        unsigned t = atomic_load_explicit(&f->r_tail, memory_order_relaxed);
        unsigned h = atomic_load_explicit(&f->r_head, memory_order_acquire);
        if (h == t){
            fs_test_after_empty_snapshot(f);
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
    if (atomic_fetch_add(&f->workers_terminal, 1) == 1 && atomic_load_explicit(&f->notify_end, memory_order_acquire) && f->cfg.on_end)
        f->cfg.on_end(f->cfg.end_ctx, f->end_reason);
    return NULL;
}

// ------------------------------------------------------------ lifecycle
static void count_sink(void *ctx, const fp_frame *fr){ (void)ctx; (void)fr; }
int fs_open(frameserver **out, const fs_config *cfg){
    if (!out || !cfg) return -1;
    frameserver *f = calloc(1, sizeof *f); if (!f) return -1;
    f->comb_correction_install_ordinal = UINT64_MAX;
    f->cfg = *cfg;
    if(pthread_mutex_init(&f->m,NULL)) goto sync_fail;
    f->m_init=1;
    if(pthread_cond_init(&f->c,NULL)) goto sync_fail;
    f->c_init=1;
    if(pthread_mutex_init(&f->life_m,NULL)) goto sync_fail;
    f->life_m_init=1;
    if(pthread_cond_init(&f->life_c,NULL)) goto sync_fail;
    f->life_c_init=1;
    f->life=FS_LIFE_OPEN;
    f->n_slots = cfg->pool_units ? cfg->pool_units : 16;   // default kept at 16 (~0.5 s): whole-tape high-water was 2; change only on a measured stall (F5 stress matrix)
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
    f->user_audio_sink = cfg->audio_sink;
    f->aq_cap_frames = cfg->audio_block_frames ? cfg->audio_block_frames : 4096;
    f->aq_slots = cfg->audio_queue_blocks ? cfg->audio_queue_blocks : 32;
    f->aq = calloc(f->aq_slots, sizeof *f->aq);
    f->aq_pcm = malloc((size_t)f->aq_slots * f->aq_cap_frames * AP_BYTES_PER_FRAME);
    if (!f->aq || !f->aq_pcm){ fs_close(f); return -1; }
    if (pthread_mutex_init(&f->aq_m, NULL)){ fs_close(f); return -1; } f->aq_m_init = 1;
    if (pthread_cond_init(&f->aq_c, NULL)){ fs_close(f); return -1; } f->aq_c_init = 1;
    ap_sink asink = { aq_enqueue, f };
    if (ap_open(&f->aud, f->aq_cap_frames, &asink) != 0){ fs_close(f); return -1; }
    if (pthread_mutex_init(&f->log_m, NULL)){ fs_close(f); return -1; } f->log_m_init = 1;
    if (cfg->decision_log){ f->log = fopen(cfg->decision_log, "wx"); if (!f->log || log_header(f->log) != 0){ fs_close(f); return -1; } f->st.log_files++; }   // exclusive: a sidecar is evidence, never truncated
    cc_callbacks ccb = { cc_on_packet, cc_on_loss, cc_on_error, NULL, cc_on_end, f };
    if (cc_open(&f->cap, &cfg->capture, &ccb) != 0){ fs_close(f); return -1; }
    *out = f; return 0;
sync_fail:
    if(f->life_c_init) pthread_cond_destroy(&f->life_c);
    if(f->life_m_init) pthread_mutex_destroy(&f->life_m);
    if(f->c_init) pthread_cond_destroy(&f->c);
    if(f->m_init) pthread_mutex_destroy(&f->m);
    free(f); return -1;
}
int fs_start(frameserver *f){
    if(!f) return -1;
    pthread_mutex_lock(&f->life_m);
    if(f->life!=FS_LIFE_OPEN){ pthread_mutex_unlock(&f->life_m); return -1; }
    f->life=FS_LIFE_STARTING; pthread_mutex_unlock(&f->life_m);
    unit_parser_begin_epoch(f->parser, 1); signal_state_begin_epoch(f->sig, 1);
    if (pthread_create(&f->worker, NULL, worker_main, f)) goto fail_no_worker;
    f->worker_created=1;
    if (pthread_create(&f->audio_worker, NULL, audio_worker_main, f)){
        // roll back the video worker the same way a failed cc_start does
        atomic_store_explicit(&f->producer_done, 1, memory_order_release);
        pthread_mutex_lock(&f->life_m); f->start_gate=1; pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
        pthread_mutex_lock(&f->m); pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m);
        pthread_join(f->worker, NULL);
        goto fail_no_worker;
    }
    f->audio_worker_created=1;
    if (cc_start(f->cap) != 0){
        // Failed starts have no media callback; release the worker only to perform rollback.
        atomic_store_explicit(&f->producer_done, 1,memory_order_release);
        pthread_mutex_lock(&f->life_m); f->start_gate=1; pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
        pthread_mutex_lock(&f->m); pthread_cond_signal(&f->c); pthread_mutex_unlock(&f->m);
        pthread_join(f->worker, NULL);
        atomic_store_explicit(&f->audio_done, 1, memory_order_release);
        pthread_mutex_lock(&f->aq_m); pthread_cond_signal(&f->aq_c); pthread_mutex_unlock(&f->aq_m);
        pthread_join(f->audio_worker, NULL);
        pthread_mutex_lock(&f->life_m); f->life=FS_LIFE_STOPPED; pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
        return -1;
    }
    atomic_store_explicit(&f->notify_end, 1, memory_order_release);
    pthread_mutex_lock(&f->life_m); f->life=FS_LIFE_RUNNING; f->start_gate=1;
    pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
    return 0;
fail_no_worker:
    pthread_mutex_lock(&f->life_m); f->life=FS_LIFE_STOPPED; pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
    return -1;
}
int fs_stop(frameserver *f){
    if(!f) return -1;
    if((f->worker_created && pthread_equal(pthread_self(),f->worker)) ||
       (f->audio_worker_created && pthread_equal(pthread_self(),f->audio_worker))) return -1;   // no self-join from a callback
    pthread_mutex_lock(&f->life_m);
    while(f->life==FS_LIFE_STOPPING) pthread_cond_wait(&f->life_c,&f->life_m);
    if(f->life==FS_LIFE_STOPPED){ pthread_mutex_unlock(&f->life_m); return 0; }
    if(f->life!=FS_LIFE_RUNNING){ pthread_mutex_unlock(&f->life_m); return -1; }
    f->life=FS_LIFE_STOPPING; pthread_mutex_unlock(&f->life_m);
    cc_stop(f->cap);                        // fires on_end -> producer_done (audio flushed before it)
    pthread_join(f->worker, NULL);
    pthread_join(f->audio_worker, NULL);    // exits by itself once cc_on_end set audio_done and the queue drained
    pthread_mutex_lock(&f->log_m); FILE *L = f->log; f->log = NULL; uint64_t ferrs = f->log_file_errors; pthread_mutex_unlock(&f->log_m);   // detach under the lock (fs_log_stop may race), close outside it
    if (L){ if (fclose(L) != 0){ f->st.log_close_errors++; ferrs++; } f->st.log_last_file_errors = ferrs; }
    pthread_mutex_lock(&f->life_m); f->life=FS_LIFE_STOPPED; pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
    return 0;
}
// Runtime decision-log attachment (a recorder aligns the sidecar to ITS recording, not to the
// session). Refused from the worker threads (they hold the row lock while writing) and while a
// log is attached: one log at a time, and the caller decides when the previous one ends.
static int fs_log_from_worker(const frameserver *f){
    return (f->worker_created && pthread_equal(pthread_self(),f->worker)) ||
           (f->audio_worker_created && pthread_equal(pthread_self(),f->audio_worker));
}
int fs_log_start(frameserver *f, const char *path){
    if(!f || !path || !*path || fs_log_from_worker(f)) return -1;
    pthread_mutex_lock(&f->log_m); int attached = f->log != NULL; pthread_mutex_unlock(&f->log_m);
    if(attached) return -1;                            // one log at a time; the caller ends the previous one
    FILE *L = fopen(path, "wx");                       // never truncate an existing file: a sidecar is evidence
    if(!L) return -1;
    if(log_header(L) != 0){ fclose(L); remove(path); return -1; }   // we created it; a header-less file is not a log
    // Lifecycle check and install happen under life_m so fs_stop (which moves life to STOPPING
    // under the same lock before joining the workers) cannot slip between them.
    pthread_mutex_lock(&f->life_m);
    if(f->life==FS_LIFE_STOPPING || f->life==FS_LIFE_STOPPED){ pthread_mutex_unlock(&f->life_m); fclose(L); remove(path); return -1; }
    pthread_mutex_lock(&f->log_m);
    if(f->log){ pthread_mutex_unlock(&f->log_m); pthread_mutex_unlock(&f->life_m); fclose(L); remove(path); return -1; }   // lost a race with another control caller
    f->log = L; f->st.log_files++; f->log_file_errors = 0;
    pthread_mutex_unlock(&f->log_m);
    pthread_mutex_unlock(&f->life_m);
    return 0;
}
int fs_log_stop(frameserver *f){
    if(!f || fs_log_from_worker(f)) return -1;
    pthread_mutex_lock(&f->log_m);
    FILE *L = f->log; f->log = NULL; uint64_t errs = f->log_file_errors;   // detach under the lock ...
    pthread_mutex_unlock(&f->log_m);
    if(!L) return -1;
    if(fclose(L) != 0){ f->st.log_close_errors++; errs++; }   // ... flush and close outside it; a failed close is reported, never hidden
    f->st.log_last_file_errors = errs;
    return errs ? -1 : 0;                              // rows failed inside this file: the caller must not publish it as complete
}
void fs_get_stats(const frameserver *f, fs_stats *o){
    *o = f->st;
    o->video_observations = atomic_load(&f->video_obs); o->audio_records = atomic_load(&f->audio_records);
    o->audio_resync = atomic_load(&f->audio_resync); o->dropped_pool_full = atomic_load(&f->dropped_pool_full);
    if (f->aud){ ap_stats a; ap_get_stats(f->aud, &a); o->audio_pcm_records = a.records_pcm; o->audio_blocks = a.blocks;
        o->audio_frames_published = a.frames_published; o->audio_discontinuities = a.discontinuities; o->audio_blocks_unanchored = a.blocks_unanchored;
        o->audio_counter_gaps = a.counter_gaps; o->audio_residual_min = a.resyncs_anchored ? a.residual_min : 0; o->audio_residual_max = a.resyncs_anchored ? a.residual_max : 0; }
    o->audio_blocks_delivered = f->aq_delivered_blocks; o->audio_frames_delivered = f->aq_delivered_frames;
    o->audio_dropped_blocks = atomic_load(&f->aq_dropped_blocks); o->audio_dropped_frames = atomic_load(&f->aq_dropped_frames);
    o->audio_master_frames = atomic_load(&f->audio_master_frames);
    o->dropped_ring_full = atomic_load(&f->dropped_ring_full); o->pool_high_water = atomic_load(&f->pool_hw);
    o->eligible_observations = atomic_load(&f->eligible_ingress);
    o->holes = atomic_load(&f->holes); o->unframed = atomic_load(&f->unframed); o->short_units = atomic_load(&f->shorts);
    o->other_format = atomic_load(&f->other_fmt); o->no_signal_0800 = atomic_load(&f->ns0800);
}
void fs_close(frameserver *f){
    if (!f) return;
    if((f->worker_created && pthread_equal(pthread_self(),f->worker)) ||
       (f->audio_worker_created && pthread_equal(pthread_self(),f->audio_worker))){
        fprintf(stderr,"frameserver: close from a worker callback is forbidden; session retained\n"); return;
    }
    pthread_mutex_lock(&f->life_m); fs_life life=f->life; pthread_mutex_unlock(&f->life_m);
    if(life==FS_LIFE_RUNNING || life==FS_LIFE_STOPPING) fs_stop(f);
    if (f->cap) cc_close(f->cap);
    if (f->pub) fp_close(f->pub);
    if (f->aud) ap_close(f->aud);
    if (f->aq_c_init) pthread_cond_destroy(&f->aq_c);
    if (f->aq_m_init) pthread_mutex_destroy(&f->aq_m);
    free(f->aq); free(f->aq_pcm);
    if (f->log) fclose(f->log);
    if (f->log_m_init) pthread_mutex_destroy(&f->log_m);
    if(f->c_init) pthread_cond_destroy(&f->c);
    if(f->m_init) pthread_mutex_destroy(&f->m);
    if(f->life_c_init) pthread_cond_destroy(&f->life_c);
    if(f->life_m_init) pthread_mutex_destroy(&f->life_m);
    free(f->pool); free((void *)f->slot_used); free(f->parser); free(f->sig); free(f->eng); free(f);
}
