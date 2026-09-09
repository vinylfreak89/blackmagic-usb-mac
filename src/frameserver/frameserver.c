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
#include "wakeup.h"

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

enum { OUT_PENDING, OUT_PUBLISHED, OUT_SURFACE_FULL, OUT_QUEUE_FULL, OUT_REJECTED, OUT_NO_FRAME };
typedef struct {
    fs_item input;
    signal_result signal;
    fieldreg_decision decision;
    int classified, have_decision, has_unit;
    int8_t chosen_d1,chosen_d2,comb_correction;
    uint64_t correction_ordinal;
    FILE *file;                         /* protected by detach's drain barrier */
    _Atomic int outcome;               /* publication completion, never engine input */
} fs_log_item;
typedef struct {
    uint64_t epoch,ordinal,counter,audio_pts,log_sequence;
    int8_t d1,d2;
    uint8_t transport,audio_known;
} fs_output_item;

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
    int analysis_event,audio_event,publication_event,log_event,log_control_event;
    pthread_t audio_worker; int audio_worker_created; _Atomic int audio_done, audio_worker_done;
    uint64_t aq_drops_pending;           // producer-owned: flagged on the next enqueued block
    ap_sink user_audio_sink;
    _Atomic uint64_t aq_dropped_blocks, aq_dropped_frames;
    uint64_t aq_delivered_blocks, aq_delivered_frames;   // audio worker owned
    _Atomic uint64_t audio_master_frames;
    _Atomic int workers_terminal;        // analysis, publication, logger and audio all drain before on_end
    FILE *log; pthread_mutex_t log_m; int log_m_init; uint64_t log_file_errors;
    _Atomic(FILE *) active_log;
    _Atomic unsigned log_producers;
    fs_log_item *log_queue; unsigned log_capacity;
    _Atomic uint64_t log_head,log_tail,log_overflows,log_current_overflows;
    fs_output_item *output_queue; uint8_t *output_pool; unsigned output_capacity;
    _Atomic uint64_t output_head,output_tail,output_drops;
    _Atomic unsigned output_high,log_high;
    pthread_t publication_worker,log_worker;
    int publication_created,log_created;
    _Atomic int publication_done,log_done;
    // pool + ring (single producer = delivery thread, single consumer = worker)
    unsigned n_slots; uint8_t *pool; _Atomic int *slot_used;
    fs_item ring[RING_ITEMS]; _Atomic unsigned r_head, r_tail;
    pthread_mutex_t life_m; pthread_cond_t life_c;
    int life_m_init,life_c_init;
    pthread_t worker; _Atomic int producer_done, worker_done;
    fs_life life; int worker_created, start_gate; _Atomic int notify_end;   // read by both workers, written by fs_start
    enum cc_end end_reason;
    fs_stats st; _Atomic uint64_t audio_records, audio_resync, dropped_pool_full, dropped_ring_full, video_obs, holes, unframed, shorts, other_fmt, ns0800;
    _Atomic unsigned pool_hw;              // written on the delivery thread, read by fs_get_stats
    _Atomic uint64_t eligible_ingress;     // fixed-raster-eligible observations seen at ingress (denominator)
    uint64_t ring_drops_pending;           // producer-owned: attached only to a later item
    uint64_t ring_drop_first_ordinal;
    uint64_t ring_drop_epoch;
    int8_t last_comb_correction;
    int8_t last_decided_d1, last_decided_d2;
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

#ifdef FRAMESERVER_QUEUE_TEST_HOOKS
extern void fs_test_before_analysis_wait(frameserver *f);
extern void fs_test_after_analysis_wait(frameserver *f, int result);
extern void fs_test_after_analysis_item(frameserver *f, const unit_video_observation *obs);
extern void fs_test_before_analysis_item(frameserver *f, const unit_video_observation *obs);
#define before_analysis_wait(f) fs_test_before_analysis_wait(f)
#define after_analysis_wait(f,r) fs_test_after_analysis_wait(f,r)
#define after_analysis_item(f,o) fs_test_after_analysis_item(f,o)
#define before_analysis_item(f,o) fs_test_before_analysis_item(f,o)
#else
#define before_analysis_wait(f) ((void)(f))
#define after_analysis_wait(f,r) ((void)(f),(void)(r))
#define after_analysis_item(f,o) ((void)(f),(void)(o))
#define before_analysis_item(f,o) ((void)(f),(void)(o))
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
        if (!f->ring_drops_pending){f->ring_drop_first_ordinal = it->obs.ordinal;f->ring_drop_epoch=it->obs.epoch;}
        f->ring_drops_pending++;
        if (it->eligible) f->st.eligible_ring_drops++;
        if (it->slot >= 0) atomic_store(&f->slot_used[it->slot], 0); return 0;
    }
    fs_item q=*it;
    q.preceding_ring_drops=f->ring_drops_pending;
    f->ring_drops_pending=0;
    f->ring[h % RING_ITEMS] = q;
    atomic_store_explicit(&f->r_head, h + 1, memory_order_release);
    fs_event_signal(f->analysis_event);
    return 1;
}
static void push_tail_gap(frameserver *f){
    if(!f->ring_drops_pending) return;
    fs_item q; memset(&q,0,sizeof q); q.slot=-1; q.gap_only=1;
    q.obs.ordinal=f->ring_drop_first_ordinal; q.preceding_ring_drops=f->ring_drops_pending;
    q.obs.epoch=f->ring_drop_epoch;
    unsigned h=atomic_load_explicit(&f->r_head,memory_order_relaxed);
    // Normal items cannot occupy the reserved slot, so this is an invariant, not backpressure.
    f->ring[h%RING_ITEMS]=q; f->ring_drops_pending=0;
    atomic_store_explicit(&f->r_head,h+1,memory_order_release);
    fs_event_signal(f->analysis_event);
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
    fs_event_signal(f->audio_event);
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
            fs_event_wait(f->audio_event);
            continue;
        }
        const ap_block *b = &f->aq[t % f->aq_slots];
        if (f->user_audio_sink.on_block) f->user_audio_sink.on_block(f->user_audio_sink.ctx, b);
        f->aq_delivered_blocks++; f->aq_delivered_frames += b->n_frames;
        atomic_store_explicit(&f->aq_tail, t + 1, memory_order_release);
    }
    atomic_store(&f->audio_worker_done, 1);
    // on_end means BOTH media workers are terminal: whichever drains second fires it
    if (atomic_fetch_add(&f->workers_terminal, 1) == 3 && atomic_load_explicit(&f->notify_end, memory_order_acquire) && f->cfg.on_end)
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
    fs_event_signal(f->audio_event);
    fs_test_before_producer_done(f);
    push_tail_gap(f);
    atomic_store_explicit(&f->producer_done, 1, memory_order_release);
    fs_event_signal(f->analysis_event);
}

// ------------------------------------------------------------ worker side
static const char *transport_name(unit_transport_state t){
    switch (t){ case UNIT_TRANSPORT_COMPLETE: return "Complete"; case UNIT_TRANSPORT_HOLE: return "Hole";
                case UNIT_TRANSPORT_SHORT: return "Short"; default: return "Unframed"; }
}
static int log_header(FILE *L){
    return fprintf(L, "ordinal,counter_extended,transport,kind,appearance,appearance_confidence,source,source_confidence,"
               "interval_id,unsettled,provisional_d1,provisional_d2,applied_d1,applied_d2,baseline_d1,baseline_d2,"
               "geometry_lock_known,engine_applied_d1,engine_applied_d2,resolution,evidence_mode,confidence,"
               "f1_reason,f1_gauge,f1_insert_present,f1_insert_bytes,f1_insert_relation,f1_caption_confirmation,f1_parity_candidates,f1_fallback_candidates,f1_gauge_line,f1_gauge_bytes,f1_gauge_amplitude,f1_geometry_d,f1_blank_mean,f1_blank_chroma_noise,f1_body_witness_valid,f1_body_shift,f1_body_mad,f1_body_geometry_agrees,f1_body_reference_top,f1_body_implied_top,f1_body_differential,f1_body_common_mode,f1_picture_position_valid,f1_measured_picture_top,f1_picture_from_body,f1_recorded_first,f1_recorded_last,f1_raw_top,f1_raw_bottom,f1_switch_line,f1_first_full_other_head_line,f1_rf_peak_line,f1_rf_peak_position,f1_raw_span,f1_picture_rows,f1_band_extent,f1_observed_switch_line_count,f1_switch_count_agrees,f1_switch_count_conflict,f1_switch_signature,f1_switch_measurable,f1_geometry_measurable,f1_lock_state,f1_zero_source,f1_lock_id,f1_lock_top,f1_lock_switch_line_count,f1_lock_switch_line_count_known,f1_clip_state,f1_clip_ceiling,f1_expected_bottom,f1_lines_lost,f1_invariant_residual,"
               "f2_reason,f2_gauge,f2_insert_present,f2_insert_bytes,f2_insert_relation,f2_caption_confirmation,f2_parity_candidates,f2_fallback_candidates,f2_gauge_line,f2_gauge_bytes,f2_gauge_amplitude,f2_geometry_d,f2_blank_mean,f2_blank_chroma_noise,f2_body_witness_valid,f2_body_shift,f2_body_mad,f2_body_geometry_agrees,f2_body_reference_top,f2_body_implied_top,f2_body_differential,f2_body_common_mode,f2_picture_position_valid,f2_measured_picture_top,f2_picture_from_body,f2_recorded_first,f2_recorded_last,f2_raw_top,f2_raw_bottom,f2_switch_line,f2_first_full_other_head_line,f2_rf_peak_line,f2_rf_peak_position,f2_raw_span,f2_picture_rows,f2_band_extent,f2_observed_switch_line_count,f2_switch_count_agrees,f2_switch_count_conflict,f2_switch_signature,f2_switch_measurable,f2_geometry_measurable,f2_lock_state,f2_zero_source,f2_lock_id,f2_lock_top,f2_lock_switch_line_count,f2_lock_switch_line_count_known,f2_clip_state,f2_clip_ceiling,f2_expected_bottom,f2_lines_lost,f2_invariant_residual,"
               "parity_state,comb_check,comb_best_shift,parity_bias,comb_best_energy,comb_second_energy,comb_static_fraction,comb_correction,comb_correction_install_ordinal,comb_safe,published,drop_reason,schema_version,preceding_ring_drops,f1_geometry_observation_changed,f2_geometry_observation_changed,registration_measured,signal_gate_cause,lock_like_loss,signal_actions,observed_appearance,f1_row_coherence,f1_temporal_coherence,f2_row_coherence,f2_temporal_coherence,comb_candidate_shift,comb_unresolved_alternatives,epoch\n") < 0 ? -1 : 0;
}

static int log_field(FILE *L, const fieldreg_field_decision *d)
{
    const char *reason = d ? fieldreg_mode_name(d->reason) : "None";
    const char *gauge = d ? fieldreg_gauge_name(d->gauge) : "None";
    const char *insert_relation = d ? fieldreg_insert_relation_name(d->insert_relation) : "None";
    const char *caption_confirmation = d ? fieldreg_confirmation_name(d->caption_confirmation) : "n.a.";
    const char *switch_signature = d ? fieldreg_switch_signature_name(d->switch_signature) : "None";
    const char *lock = d ? fieldreg_lock_state_name(d->lock_state) : "NotMeasured";
    const char *zero = d ? fieldreg_zero_source_name(d->zero_source) : "None";
    const char *clip = d ? fieldreg_clip_state_name(d->clip_state) : "ClipUnknown";
    char insert_bytes[5] = "", gauge_bytes[5] = "";
    if (d && d->insert_present)
        snprintf(insert_bytes, sizeof insert_bytes, "%02x%02x", d->insert_byte1, d->insert_byte2);
    if (d && d->gauge_row >= 0 &&
        (d->gauge == FIELDREG_GAUGE_CEA608_PARITY ||
         d->gauge == FIELDREG_GAUGE_LINE22_DATA))
        snprintf(gauge_bytes, sizeof gauge_bytes, "%02x%02x", d->gauge_byte1, d->gauge_byte2);
    return fprintf(L,
                   ",%s,%s,%d,%s,%s,%s,%u,%u,%d,%s,%.3f,%d,%.3f,%.3f"
                   ",%d,%d,%.3f"
                   ",%d,%d,%d,%d,%d,%d,%d,%d"
                   ",%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%d,%d"
                   ",%s,%s,%u,%d,%d,%d,%s,%d,%d,%d,%d",
                   reason, gauge, d && d->insert_present, insert_bytes,
                   insert_relation, caption_confirmation,
                   d ? d->parity_candidate_count : 0,
                   d ? d->fallback_candidate_count : 0,
                   d && d->gauge_row >= 0 ? d->gauge_row + 4 : -1, gauge_bytes,
                   d ? d->gauge_amplitude : 0.0,
                   d ? d->geometry_d : FIELDREG_UNKNOWN,
                   d ? d->blank_mean : 0.0,
                   d ? d->blank_chroma_noise : 0.0,
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
                   d && d->recorded_first >= 0 ? d->recorded_first + 4 : -1,
                   d && d->recorded_last >= 0 ? d->recorded_last + 4 : -1,
                   d && d->raw_top >= 0 ? d->raw_top + 4 : -1,
                   d && d->raw_bottom >= 0 ? d->raw_bottom + 4 : -1,
                   d && d->switch_line >= 0 ? d->switch_line + 4 : -1,
                   d && d->first_full_other_head_line >= 0 ?
                       d->first_full_other_head_line + 4 : -1,
                   d && d->rf_peak_line >= 0 ? d->rf_peak_line + 4 : -1,
                   d ? d->rf_peak_position : -1,
                   d ? d->raw_span : -1,
                   d ? d->picture_rows : -1,
                   d ? d->band_extent : -1,
                   d ? d->observed_switch_line_count : -1,
                   d && d->switch_count_agrees,
                   d && d->switch_count_conflict,
                   switch_signature,
                   d && d->switch_measurable,
                   d && d->geometry_measurable,
                   lock, zero, d ? d->lock_id : 0,
                   d && d->lock_top >= 0 ? d->lock_top + 4 : -1,
                   d ? d->lock_switch_line_count : -1,
                   d && d->lock_switch_line_count_known, clip,
                   d && d->clip_ceiling >= 0 ? d->clip_ceiling + 4 : -1,
                   d && d->expected_bottom >= 0 ? d->expected_bottom + 4 : -1,
                   d ? d->lines_lost : 0, d ? d->invariant_residual : 0);
}
/* Analysis is the sole producer. The logger retains a slot until the publisher
 * has completed it, so a queued log index cannot alias a newer decision. */
static uint64_t enqueue_log(frameserver *f,const fs_log_item *value,int outcome){
    atomic_fetch_add_explicit(&f->log_producers,1,memory_order_seq_cst);
    FILE *file=atomic_load_explicit(&f->active_log,memory_order_seq_cst);
    uint64_t seq=UINT64_MAX;
    if(file){
        uint64_t h=atomic_load_explicit(&f->log_head,memory_order_relaxed);
        uint64_t t=atomic_load_explicit(&f->log_tail,memory_order_acquire);
        if(h-t>=f->log_capacity){
            atomic_fetch_add(&f->log_overflows,1);atomic_fetch_add(&f->log_current_overflows,1);
        }else{
            fs_log_item *j=&f->log_queue[h%f->log_capacity];
            /* No other thread owns this free slot. */
            memcpy(j,value,offsetof(fs_log_item,outcome));j->file=file;
            atomic_store_explicit(&j->outcome,outcome,memory_order_relaxed);
            atomic_store_explicit(&f->log_head,h+1,memory_order_release);
            unsigned used=(unsigned)(h-t+1);
            if(used>atomic_load(&f->log_high))atomic_store(&f->log_high,used);
            seq=h;fs_event_signal(f->log_event);
        }
    }
    atomic_fetch_sub_explicit(&f->log_producers,1,memory_order_seq_cst);
    fs_event_signal(f->log_control_event);
    return seq;
}
static void complete_log(frameserver *f,uint64_t seq,uint64_t epoch,uint64_t ordinal,int outcome){
    if(seq==UINT64_MAX)return;
    fs_log_item *j=&f->log_queue[seq%f->log_capacity];
    if(j->input.obs.epoch!=epoch || j->input.obs.ordinal!=ordinal)abort();
    atomic_store_explicit(&j->outcome,outcome,memory_order_release);
    fs_event_signal(f->log_event);
}
static void enqueue_output(frameserver *f,const uint8_t *unit,const fs_output_item *value){
    uint64_t h=atomic_load_explicit(&f->output_head,memory_order_relaxed);
    uint64_t t=atomic_load_explicit(&f->output_tail,memory_order_acquire);
    if(h-t>=f->output_capacity){
        atomic_fetch_add(&f->output_drops,1);
        complete_log(f,value->log_sequence,value->epoch,value->ordinal,OUT_QUEUE_FULL);return;
    }
    unsigned i=(unsigned)(h%f->output_capacity);
    memcpy(f->output_pool+(size_t)i*FP_UNIT_BYTES,unit,FP_UNIT_BYTES);
    f->output_queue[i]=*value;
    atomic_store_explicit(&f->output_head,h+1,memory_order_release);
    unsigned used=(unsigned)(h-t+1);
    if(used>atomic_load(&f->output_high))atomic_store(&f->output_high,used);
    fs_event_signal(f->publication_event);
}
static void *publication_main(void *arg){
    frameserver *f=arg;pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    for(;;){
        uint64_t t=atomic_load_explicit(&f->output_tail,memory_order_relaxed);
        uint64_t h=atomic_load_explicit(&f->output_head,memory_order_acquire);
        if(t==h){
            if(atomic_load_explicit(&f->worker_done,memory_order_acquire)){
                if(t==atomic_load_explicit(&f->output_head,memory_order_acquire))break;
                continue;
            }
            fs_event_wait(f->publication_event);continue;
        }
        unsigned i=(unsigned)(t%f->output_capacity);
        const fs_output_item *p=&f->output_queue[i];
        int rc=fp_publish(f->pub,f->output_pool+(size_t)i*FP_UNIT_BYTES,FP_UNIT_BYTES,
                         p->counter,p->d1,p->d2,p->transport,p->audio_known,p->audio_pts);
        if(!rc){f->st.published++;if(p->audio_known)atomic_fetch_add(&f->audio_master_frames,1);}
        else f->st.publisher_dropped++;
        complete_log(f,p->log_sequence,p->epoch,p->ordinal,
                     !rc?OUT_PUBLISHED:rc==1?OUT_SURFACE_FULL:OUT_REJECTED);
        atomic_store_explicit(&f->output_tail,t+1,memory_order_release);
    }
    atomic_store_explicit(&f->publication_done,1,memory_order_release);fs_event_signal(f->log_event);
    if(atomic_fetch_add(&f->workers_terminal,1)==3 && atomic_load(&f->notify_end) && f->cfg.on_end)
        f->cfg.on_end(f->cfg.end_ctx,f->end_reason);
    return NULL;
}
static void write_log_item(frameserver *f,const fs_log_item *j,int outcome){
    const fs_item *it=&j->input;
    unit_video_observation obs=it->obs;
    signal_result sr=j->signal;fieldreg_decision d=j->decision;
    int classified=j->classified,have_d=j->have_decision,unit=j->has_unit;
    int published=outcome==OUT_PUBLISHED;uint64_t rd=it->preceding_ring_drops;
    if (j->file){
        int wr = fprintf(j->file, "%llu,%llu,%s,%d,%s,%.3f,%s,%.3f,%llu,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%s,%.3f",
            (unsigned long long)obs.ordinal, (unsigned long long)obs.counter_extended, transport_name(obs.transport), (int)obs.kind,
            classified ? signal_appearance_name(sr.appearance) : "Unclassified", classified ? sr.appearance_confidence : 0.0,
            classified ? signal_source_state_name(sr.source) : "Unknown", classified ? sr.source_confidence : 0.0,
            (unsigned long long)(classified ? sr.unsettled_interval_id : 0), classified && sr.unsettled,
            have_d ? d.frame_observation_d1 : 0, have_d ? d.frame_observation_d2 : 0,
            j->chosen_d1,
            j->chosen_d2,
            have_d ? d.baseline_d1 : 0, have_d ? d.baseline_d2 : 0,
            have_d && d.geometry_lock_known, have_d ? d.applied_d1 : 0, have_d ? d.applied_d2 : 0,
            "Immediate", have_d ? fieldreg_mode_name(d.mode) :
                unit ? "SignalGateHold" : "None", have_d ? d.confidence : 0.0);
        if (wr >= 0) wr = log_field(j->file, have_d ? &d.field[0] : NULL);
        if (wr >= 0) wr = log_field(j->file, have_d ? &d.field[1] : NULL);
        if (wr >= 0) wr = fprintf(j->file, ",%s,%s,%d,%d,%.3f,%.3f,%.6f,%d,%lld,%d,%d,%s,%u,%llu,%d,%d,%d,%s,%d,%u,%s,%.6f,%.6f,%.6f,%.6f,%d,%u,%llu\n",
            have_d ? fieldreg_parity_state_name(d.parity_state) : "Uncalibrated",
            have_d ? fieldreg_comb_check_name(d.comb_check) : "n.a.",
            have_d ? d.comb_best_shift : FIELDREG_COMB_UNKNOWN,
            have_d ? d.parity_bias : 0,
            have_d ? d.comb_best_energy : 0.0,
            have_d ? d.comb_second_energy : 0.0,
            have_d ? d.comb_static_fraction : 0.0,
            have_d ? d.comb_correction : j->comb_correction,
            j->correction_ordinal == UINT64_MAX ?
            -1LL : (long long)j->correction_ordinal,
            have_d && d.comb_safe, published,
            it->gap_only ? "RingFullTail" : it->drop == FS_DROP_POOL_FULL ? "PoolFull" : outcome == OUT_QUEUE_FULL ? "PublicationQueueFull" : outcome == OUT_SURFACE_FULL ? "PublisherFull" : outcome == OUT_REJECTED ? "PublisherError" : "None",
            FS_DECISION_LOG_SCHEMA, (unsigned long long)rd,
            have_d && d.geometry_observation_changed[0],
            have_d && d.geometry_observation_changed[1],
            unit && classified && sr.normal_picture,
            !unit ? "NoRaster" : !classified ? "Unclassified" :
            sr.normal_picture ? "None" :
            sr.observed_appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE ?
                "SourceAcquiring" : signal_appearance_name(sr.observed_appearance),
            classified && sr.lock_like_loss, classified ? sr.actions : 0,
            classified ? signal_appearance_name(sr.observed_appearance) : "Unknown",
            sr.measurements.row_coherence[0], sr.measurements.temporal_coherence[0],
            sr.measurements.row_coherence[1], sr.measurements.temporal_coherence[1],
            have_d ? d.comb_candidate_shift : FIELDREG_COMB_UNKNOWN,
            have_d ? d.comb_unresolved_alternatives : 0, (unsigned long long)obs.epoch);
        if (wr < 0){ f->st.log_write_errors++; f->log_file_errors++; } else f->st.log_rows++;   // a failed row is never counted as written
        fs_test_after_log_row(f, j->file);
    }

}
static void *log_main(void *arg){
    frameserver *f=arg;pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
    for(;;){
        uint64_t t=atomic_load_explicit(&f->log_tail,memory_order_relaxed);
        uint64_t h=atomic_load_explicit(&f->log_head,memory_order_acquire);
        if(t==h){
            if(atomic_load_explicit(&f->publication_done,memory_order_acquire) &&
               atomic_load_explicit(&f->worker_done,memory_order_acquire)){
                if(t==atomic_load_explicit(&f->log_head,memory_order_acquire))break;
                continue;
            }
            fs_event_wait(f->log_event);continue;
        }
        fs_log_item *j=&f->log_queue[t%f->log_capacity];
        int outcome=atomic_load_explicit(&j->outcome,memory_order_acquire);
        if(outcome==OUT_PENDING){fs_event_wait(f->log_event);continue;}
        write_log_item(f,j,outcome);
        atomic_store_explicit(&f->log_tail,t+1,memory_order_release);
        fs_event_signal(f->log_control_event);
    }
    atomic_store(&f->log_done,1);fs_event_signal(f->log_control_event);
    if(atomic_fetch_add(&f->workers_terminal,1)==3 && atomic_load(&f->notify_end) && f->cfg.on_end)
        f->cfg.on_end(f->cfg.end_ctx,f->end_reason);
    return NULL;
}
static void process_item(frameserver *f,const fs_item *it){
    if(it->gap_only){
        fieldreg_discontinuity(f->eng);f->st.discontinuity_calls++;
        f->st.ring_drops_logged+=it->preceding_ring_drops;f->st.ring_gap_rows++;
        fs_log_item j={0};j.input=*it;j.input.obs.transport=UNIT_TRANSPORT_HOLE;
        j.chosen_d1=f->last_decided_d1;j.chosen_d2=f->last_decided_d2;
        j.comb_correction=f->last_comb_correction;j.correction_ordinal=f->comb_correction_install_ordinal;
        enqueue_log(f,&j,OUT_NO_FRAME);return;
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
    fieldreg_decision d; memset(&d, 0, sizeof d); bool have_d = false;
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
    uint64_t apts = 0; int aknown = 0;
    if (unit){
        f->st.exact_units++;
        if (classified && sr.normal_picture) {
            f->st.registration_calls++;
            have_d = fieldreg_process(f->eng, unit, &d);
        } else {
            f->st.signal_gate_units++;
            /* A gated raster is not a previous-picture witness either. */
            fieldreg_discontinuity(f->eng);
        }
        if (have_d && d.comb_correction != f->last_comb_correction) {
            f->last_comb_correction = d.comb_correction;
            f->comb_correction_install_ordinal = d.comb_correction == 0 ?
                                                  UINT64_MAX : obs.ordinal;
        }
        if (classified && sr.unsettled) f->st.unsettled_units++;
        aknown = ap_lookup(f->aud, obs.epoch, obs.counter_extended, &apts, NULL);   // audio-clock time of this unit
        if(have_d){f->last_decided_d1=d.applied_d1;f->last_decided_d2=d.applied_d2;}
    }
    fs_log_item j={0};j.input=*it;j.input.obs.bytes=NULL;j.input.obs.payload=NULL;
    j.signal=sr;j.decision=d;j.classified=classified;j.have_decision=have_d;j.has_unit=unit!=NULL;
    j.chosen_d1=f->last_decided_d1;j.chosen_d2=f->last_decided_d2;
    j.comb_correction=f->last_comb_correction;j.correction_ordinal=f->comb_correction_install_ordinal;
    uint64_t seq=enqueue_log(f,&j,unit?OUT_PENDING:OUT_NO_FRAME);
    if(unit){
        fs_output_item p={.epoch=obs.epoch,.ordinal=obs.ordinal,.counter=obs.counter_extended,
            .audio_pts=apts,.audio_known=aknown,.log_sequence=seq,
            .d1=j.chosen_d1,.d2=j.chosen_d2,
            .transport=obs.transport==UNIT_TRANSPORT_COMPLETE?FP_TRANSPORT_COMPLETE:FP_TRANSPORT_SHORT};
        enqueue_output(f,unit,&p);
        /* Publication owns a different slab. Neither sink can retain input. */
        atomic_store_explicit(&f->slot_used[it->slot],0,memory_order_release);
    }
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
            before_analysis_wait(f);
            fs_event_wait(f->analysis_event);
            after_analysis_wait(f,0);
            continue;
        }
        fs_item it = f->ring[t % RING_ITEMS];
        atomic_store_explicit(&f->r_tail, t + 1, memory_order_release);
        before_analysis_item(f,&it.obs);
        process_item(f, &it);
        after_analysis_item(f,&it.obs);
    }
    atomic_store(&f->worker_done, 1);
    fs_event_signal(f->publication_event);fs_event_signal(f->log_event);
    if (atomic_fetch_add(&f->workers_terminal, 1) == 3 && atomic_load_explicit(&f->notify_end, memory_order_acquire) && f->cfg.on_end)
        f->cfg.on_end(f->cfg.end_ctx, f->end_reason);
    return NULL;
}

// ------------------------------------------------------------ lifecycle
static void count_sink(void *ctx, const fp_frame *fr){ (void)ctx; (void)fr; }
int fs_open(frameserver **out, const fs_config *cfg){
    if (!out || !cfg) return -1;
    frameserver *f = calloc(1, sizeof *f); if (!f) return -1;
    f->analysis_event=f->audio_event=f->publication_event=f->log_event=f->log_control_event=-1;
    f->comb_correction_install_ordinal = UINT64_MAX;
    f->cfg = *cfg;
    if(pthread_mutex_init(&f->life_m,NULL)) goto sync_fail;
    f->life_m_init=1;
    if(pthread_cond_init(&f->life_c,NULL)) goto sync_fail;
    f->life_c_init=1;
    f->life=FS_LIFE_OPEN;
    f->analysis_event=fs_event_open();f->audio_event=fs_event_open();
    f->publication_event=fs_event_open();f->log_event=fs_event_open();f->log_control_event=fs_event_open();
    if(f->analysis_event<0 || f->audio_event<0 || f->publication_event<0 || f->log_event<0 || f->log_control_event<0){fs_close(f);return -1;}
    /* Memory capacities, not signal thresholds. Keep input/output slabs separate. */
    f->output_capacity=cfg->publication_queue_units?cfg->publication_queue_units:16;
    f->log_capacity=cfg->log_queue_items?cfg->log_queue_items:128;
    f->output_queue=calloc(f->output_capacity,sizeof *f->output_queue);
    f->output_pool=malloc((size_t)f->output_capacity*FP_UNIT_BYTES);
    f->log_queue=calloc(f->log_capacity,sizeof *f->log_queue);
    if(!f->output_queue || !f->output_pool || !f->log_queue){fs_close(f);return -1;}
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
    ap_sink asink = { aq_enqueue, f };
    if (ap_open(&f->aud, f->aq_cap_frames, &asink) != 0){ fs_close(f); return -1; }
    if (pthread_mutex_init(&f->log_m, NULL)){ fs_close(f); return -1; } f->log_m_init = 1;
    if (cfg->decision_log){ f->log = fopen(cfg->decision_log, "wx"); if (!f->log || log_header(f->log) != 0){ fs_close(f); return -1; } f->st.log_files++; }   // exclusive: a sidecar is evidence, never truncated
    atomic_store(&f->active_log,f->log);
    cc_callbacks ccb = { cc_on_packet, cc_on_loss, cc_on_error, NULL, cc_on_end, f };
    if (cc_open(&f->cap, &cfg->capture, &ccb) != 0){ fs_close(f); return -1; }
    *out = f; return 0;
sync_fail:
    if(f->life_c_init) pthread_cond_destroy(&f->life_c);
    if(f->life_m_init) pthread_mutex_destroy(&f->life_m);
    free(f); return -1;
}
static int fs_log_from_worker(const frameserver *f){
    return (f->worker_created && pthread_equal(pthread_self(),f->worker)) ||
        (f->audio_worker_created && pthread_equal(pthread_self(),f->audio_worker)) ||
        (f->publication_created && pthread_equal(pthread_self(),f->publication_worker)) ||
        (f->log_created && pthread_equal(pthread_self(),f->log_worker));
}
int fs_start(frameserver *f){
    if(!f)return -1;
    pthread_mutex_lock(&f->life_m);
    if(f->life!=FS_LIFE_OPEN){pthread_mutex_unlock(&f->life_m);return -1;}
    f->life=FS_LIFE_STARTING;pthread_mutex_unlock(&f->life_m);
    unit_parser_begin_epoch(f->parser,1);signal_state_begin_epoch(f->sig,1);
    if(pthread_create(&f->worker,NULL,worker_main,f))goto fail;
    f->worker_created=1;
    if(pthread_create(&f->publication_worker,NULL,publication_main,f))goto fail;
    f->publication_created=1;
    if(pthread_create(&f->log_worker,NULL,log_main,f))goto fail;
    f->log_created=1;
    if(pthread_create(&f->audio_worker,NULL,audio_worker_main,f))goto fail;
    f->audio_worker_created=1;
    if(cc_start(f->cap))goto fail;
    atomic_store_explicit(&f->notify_end,1,memory_order_release);
    pthread_mutex_lock(&f->life_m);f->life=FS_LIFE_RUNNING;f->start_gate=1;
    pthread_cond_broadcast(&f->life_c);pthread_mutex_unlock(&f->life_m);
    return 0;
fail:
    atomic_store(&f->producer_done,1);atomic_store(&f->audio_done,1);
    if(!f->worker_created)atomic_store(&f->worker_done,1);
    if(!f->publication_created)atomic_store(&f->publication_done,1);
    pthread_mutex_lock(&f->life_m);f->start_gate=1;pthread_cond_broadcast(&f->life_c);pthread_mutex_unlock(&f->life_m);
    fs_event_signal(f->analysis_event);fs_event_signal(f->audio_event);
    fs_event_signal(f->publication_event);fs_event_signal(f->log_event);
    if(f->worker_created)pthread_join(f->worker,NULL);
    if(f->publication_created)pthread_join(f->publication_worker,NULL);
    if(f->log_created)pthread_join(f->log_worker,NULL);
    if(f->audio_worker_created)pthread_join(f->audio_worker,NULL);
    pthread_mutex_lock(&f->life_m);f->life=FS_LIFE_STOPPED;pthread_cond_broadcast(&f->life_c);pthread_mutex_unlock(&f->life_m);
    return -1;
}
/* Control callers may block for their requested log boundary. Analysis and
 * publication never acquire log_m, nor wait for this drain or for file I/O. */
static int detach_log(frameserver *f){
    pthread_mutex_lock(&f->log_m);
    FILE *file=atomic_exchange_explicit(&f->active_log,NULL,memory_order_seq_cst);
    if(!file){pthread_mutex_unlock(&f->log_m);return -1;}
    while(atomic_load_explicit(&f->log_producers,memory_order_seq_cst))fs_event_wait(f->log_control_event);
    uint64_t end=atomic_load_explicit(&f->log_head,memory_order_acquire);
    while(atomic_load_explicit(&f->log_tail,memory_order_acquire)<end)fs_event_wait(f->log_control_event);
    uint64_t errors=f->log_file_errors+atomic_load(&f->log_current_overflows);
    f->log=NULL;
    if(fclose(file)){f->st.log_close_errors++;errors++;}
    f->st.log_last_file_errors=errors;
    pthread_mutex_unlock(&f->log_m);return errors?-1:0;
}
int fs_stop(frameserver *f){
    if(!f || fs_log_from_worker(f))return -1;
    pthread_mutex_lock(&f->life_m);
    while(f->life==FS_LIFE_STOPPING)pthread_cond_wait(&f->life_c,&f->life_m);
    if(f->life==FS_LIFE_STOPPED){pthread_mutex_unlock(&f->life_m);return 0;}
    if(f->life!=FS_LIFE_RUNNING){pthread_mutex_unlock(&f->life_m);return -1;}
    f->life=FS_LIFE_STOPPING;pthread_mutex_unlock(&f->life_m);
    cc_stop(f->cap);
    pthread_join(f->worker,NULL);
    pthread_join(f->publication_worker,NULL);
    pthread_join(f->log_worker,NULL);
    pthread_join(f->audio_worker,NULL);
    if(atomic_load(&f->active_log))detach_log(f);
    pthread_mutex_lock(&f->life_m);f->life=FS_LIFE_STOPPED;pthread_cond_broadcast(&f->life_c);pthread_mutex_unlock(&f->life_m);
    return 0;
}
int fs_log_start(frameserver *f,const char *path){
    if(!f || !path || !*path || fs_log_from_worker(f))return -1;
    pthread_mutex_lock(&f->life_m);
    if(f->life==FS_LIFE_STOPPING || f->life==FS_LIFE_STOPPED){pthread_mutex_unlock(&f->life_m);return -1;}
    pthread_mutex_lock(&f->log_m);
    if(f->log){pthread_mutex_unlock(&f->log_m);pthread_mutex_unlock(&f->life_m);return -1;}
    FILE *file=fopen(path,"wx");
    if(!file){pthread_mutex_unlock(&f->log_m);pthread_mutex_unlock(&f->life_m);return -1;}
    if(log_header(file)){fclose(file);remove(path);pthread_mutex_unlock(&f->log_m);pthread_mutex_unlock(&f->life_m);return -1;}
    f->log=file;f->log_file_errors=0;atomic_store(&f->log_current_overflows,0);f->st.log_files++;
    atomic_store_explicit(&f->active_log,file,memory_order_seq_cst);
    pthread_mutex_unlock(&f->log_m);pthread_mutex_unlock(&f->life_m);return 0;
}
int fs_log_stop(frameserver *f){
    if(!f || fs_log_from_worker(f))return -1;
    return detach_log(f);
}
void fs_get_stats(const frameserver *f, fs_stats *o){
    *o = f->st;
    o->publication_queue_drops=atomic_load(&f->output_drops);
    o->publisher_dropped+=o->publication_queue_drops;
    o->log_queue_drops=atomic_load(&f->log_overflows);
    o->publication_queue_high_water=atomic_load(&f->output_high);
    o->log_queue_high_water=atomic_load(&f->log_high);
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
    if(fs_log_from_worker(f)){
        fprintf(stderr,"frameserver: close from a worker callback is forbidden; session retained\n"); return;
    }
    pthread_mutex_lock(&f->life_m); fs_life life=f->life; pthread_mutex_unlock(&f->life_m);
    if(life==FS_LIFE_RUNNING || life==FS_LIFE_STOPPING) fs_stop(f);
    if (f->cap) cc_close(f->cap);
    if (f->pub) fp_close(f->pub);
    if (f->aud) ap_close(f->aud);
    free(f->aq); free(f->aq_pcm);
    if (f->log) fclose(f->log);
    if (f->log_m_init) pthread_mutex_destroy(&f->log_m);
    if(f->analysis_event>=0)close(f->analysis_event);
    if(f->audio_event>=0)close(f->audio_event);
    if(f->publication_event>=0)close(f->publication_event);
    if(f->log_event>=0)close(f->log_event);
    if(f->log_control_event>=0)close(f->log_control_event);
    free(f->output_queue);free(f->output_pool);free(f->log_queue);
    if(f->life_c_init) pthread_cond_destroy(&f->life_c);
    if(f->life_m_init) pthread_mutex_destroy(&f->life_m);
    free(f->pool); free((void *)f->slot_used); free(f->parser); free(f->sig); free(f->eng); free(f);
}
