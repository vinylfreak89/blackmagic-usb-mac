#include "frameserver.h"
#include "async_file.h"

/* Sidecar rows go through a writer thread so storage stalls never stall the video worker (async_file.h).
 * Rows with H-retiming measured 8.1 KB (948 rows, 7.7 MB), ~243 KB/s: 64 MiB rides out ~4.5 minutes of
 * stalled disk. An overflow makes the file incomplete, never silently thinner. */
#define FS_LOG_RING_BYTES (64u<<20)
#define FS_LOG_WRITE_CHUNK (1u<<20)
#include "../unit_parser/unit_parser.h"
#include "../signal_state/signal_state.h"
#include "../field_registration/geometry_engine.h"
#include "pairing_schedule.h"
#include "hretime.h"
#include <math.h>
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
    unsigned partial_lines;                // show_partial: whole lines of picture in a unit that is not whole, held in the slot
    uint64_t preceding_ring_drops;
    unit_video_observation obs;            // metadata copy; bytes/payload re-pointed to the slot
    /* Decision-log evidence has an input-order cutoff: the parser's video-unit
     * callback. Its single delivery thread also owns correlation writes, so
     * this immutable snapshot cannot lose a retry race or expire in the queue.
     * Genuinely later/missing resyncs stay unknown in this unit's log. */
    int audio_evidence_known;
    ap_correlation audio_evidence;
    uint64_t t_enqueue;                    // parser handoff (CLOCK_UPTIME_RAW ns), for handoff timing
} fs_item;

struct frameserver {
    fs_config cfg;
    cc_session *cap;
    unit_parser *parser;
    signal_state *sig;
    geometry_engine *geometry;
    uint8_t *geometry_y, *geometry_unit;
    uint8_t *retime_unit, *retime_previous; /* repaired copies, never geometry inputs */
    hrt_workspace *retime_work;
    hrt_result retime_result;
    fs_item geometry_item;
    fs_handoff_timing ht; uint64_t ht_since, idle_since;   // worker-only handoff accounting
    int geometry_pending, geometry_reset;
    uint64_t geometry_epoch;
    int geometry_have_epoch;
    fs_pairing_schedule pairing;
    const fs_pairing_row *pairing_active;
    int geometry_reversed;
    fp_publisher *pub;
    audio_publisher *aud;
    // Video-worker owned, independent of geometry resets and sidecar attachment.
    int audio_residual_known;
    uint64_t audio_residual_epoch, audio_residual_run;
    int64_t audio_residual_previous;
    // audio queue: single producer (delivery thread, inside the publisher's sink) -> audio worker
    ap_block *aq; uint8_t *aq_pcm; unsigned aq_slots, aq_cap_frames; _Atomic unsigned aq_head, aq_tail;
    pthread_mutex_t aq_m; pthread_cond_t aq_c; int aq_m_init, aq_c_init;
    pthread_t audio_worker; int audio_worker_created; _Atomic int audio_done, audio_worker_done;
    uint64_t aq_drops_pending;           // producer-owned: flagged on the next enqueued block
    uint32_t aq_drop_flags;              // preserve a real run break even if its first block was dropped
    ap_sink user_audio_sink;
    _Atomic uint64_t aq_dropped_blocks, aq_dropped_frames;
    uint64_t aq_delivered_blocks, aq_delivered_frames;   // audio worker owned
    _Atomic uint64_t audio_master_frames;
    _Atomic int workers_terminal;        // video + audio workers that have drained; the second fires on_end
    cc_async_sink *tee; cc_callbacks tee_cb; pthread_mutex_t tee_m; int tee_m_init;   // raw .tpc tee: delivery thread forwards under tee_m
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
};

static _Thread_local frameserver *callback_session;
#ifdef FRAMESERVER_TEST_HOOKS
const signal_state_config *fs_test_signal_config(const frameserver *f){
    return signal_state_get_config(f->sig);
}
void fs_test_reuse_worker_ids(frameserver *f){
    /* Caller owns an open (log checks) or stopped (lifecycle checks) session. */
    f->worker=f->audio_worker=pthread_self();
    f->worker_created=f->audio_worker_created=1;
}
extern void fs_test_destroyed(void);
extern void fs_test_after_empty_snapshot(frameserver *f);
extern void fs_test_before_producer_done(frameserver *f);
extern void fs_test_after_log_row(frameserver *f, FILE *log);
extern void fs_test_pool_drop(void);
extern void fs_test_ring_drop(void);
extern void fs_test_audio_drop(void);
extern void fs_test_before_video(frameserver *f);
extern void fs_test_after_item(frameserver *f);
#else
#define fs_test_destroyed() ((void)0)
#define fs_test_after_empty_snapshot(f) ((void)(f))
#define fs_test_before_producer_done(f) ((void)(f))
#define fs_test_after_log_row(f,L) ((void)(f),(void)(L))
#define fs_test_pool_drop() ((void)0)
#define fs_test_ring_drop() ((void)0)
#define fs_test_audio_drop() ((void)0)
#define fs_test_before_video(f) ((void)(f))
#define fs_test_after_item(f) ((void)(f))
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
        fs_test_ring_drop();
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
    fs_test_before_video(f);
    atomic_fetch_add(&f->video_obs, 1);
    fs_item it; memset(&it,0,sizeof it); it.slot = -1; it.drop = FS_DROP_NONE; it.obs = *u; it.obs.bytes = NULL; it.obs.payload = NULL;
    if(u->fixed_raster_eligible)
        it.audio_evidence_known=ap_lookup_correlation(f->aud,u->epoch,u->counter_extended,&it.audio_evidence);
    if (u->fixed_raster_eligible && u->byte_count == UNIT_PARSER_VIDEO_UNIT_BYTES){
        it.eligible=1;
        atomic_fetch_add(&f->eligible_ingress, 1);
        int s = take_slot(f);
        if (s < 0){
            // Bytes are shed (§8 property 7) but the OBSERVATION is not: the item still reaches the
            // worker so the sidecar carries an explicit PoolFull row instead of an unmarked hole.
            it.drop = FS_DROP_POOL_FULL;
            fs_test_pool_drop();
        } else {
            memcpy(f->pool + (size_t)s * UNIT_PARSER_VIDEO_UNIT_BYTES, u->bytes, UNIT_PARSER_VIDEO_UNIT_BYTES);
            it.slot = s;
        }
    }
    /* A picture unit that is not whole (one short field per unit from a deck in search, or the PAL-family units of
     * an unlocked decoder) is kept for showing if asked. No-signal pseudo-frames, units with bytes missing and
     * stubs of a few lines are not picture. No slot free: it is simply not shown. */
    else if (f->cfg.show_partial && u->bytes && u->transport != UNIT_TRANSPORT_HOLE && (u->format & 0xff00u) == 0xe800u &&
             u->byte_count <= UNIT_PARSER_VIDEO_UNIT_BYTES && u->byte_count >= UNIT_PARSER_VIDEO_HEADER_BYTES + 32u * FP_LINE_BYTES){
        int s = take_slot(f);
        if (s >= 0){
            memcpy(f->pool + (size_t)s * UNIT_PARSER_VIDEO_UNIT_BYTES, u->bytes, u->byte_count);
            it.slot = s; it.partial_lines = (unsigned)((u->byte_count - UNIT_PARSER_VIDEO_HEADER_BYTES) / FP_LINE_BYTES);
            it.audio_evidence_known=ap_lookup_correlation(f->aud,u->epoch,u->counter_extended,&it.audio_evidence);   /* its time on the audio clock, for the consumer's timestamp */
        }
    }
    it.t_enqueue = clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
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
        fs_test_audio_drop();
        f->aq_drop_flags |= b->flags & AP_FLAG_DISCONTINUITY_BEFORE;
        f->aq_drops_pending++; return;      // consumer too slow: shed HERE, never upstream
    }
    unsigned i = h % f->aq_slots;
    uint8_t *dst = f->aq_pcm + (size_t)i * f->aq_cap_frames * AP_BYTES_PER_FRAME;
    memcpy(dst, b->s24le, (size_t)b->n_frames * AP_BYTES_PER_FRAME);
    f->aq[i] = *b; f->aq[i].s24le = dst;
    if (f->aq_drops_pending){
        f->aq[i].flags |= AP_FLAG_DROPPED_BEFORE | f->aq_drop_flags;
        f->aq_drops_pending = 0; f->aq_drop_flags = 0;
    }
    atomic_store_explicit(&f->aq_head, h + 1, memory_order_release);
    if (pthread_mutex_trylock(&f->aq_m) == 0){ pthread_cond_signal(&f->aq_c); pthread_mutex_unlock(&f->aq_m); }
}
static void *audio_worker_main(void *arg){
    frameserver *f = arg;
    callback_session=f;
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
    callback_session=NULL;
    return NULL;
}
/* The tee sees exactly what the parser sees, in the same order; its callbacks only copy. */
#define TEE(call) do{ pthread_mutex_lock(&f->tee_m); if(f->tee) f->tee_cb.call; pthread_mutex_unlock(&f->tee_m); }while(0)
static void cc_on_packet(void *ctx, const cc_packet *p){ frameserver *f = ctx; TEE(on_packet(f->tee_cb.ctx, p)); unit_parser_on_packet(f->parser, p); }
static void cc_on_tick(void *ctx, uint32_t ms){ frameserver *f = ctx; TEE(on_tick(f->tee_cb.ctx, ms)); }
static void cc_on_loss(void *ctx, uint8_t ep, uint32_t n, uint64_t b){ frameserver *f = ctx; TEE(on_loss(f->tee_cb.ctx, ep, n, b)); unit_parser_on_loss(f->parser, ep, n, b); }
static void cc_on_error(void *ctx, uint8_t ep, uint32_t seq, int st, int kind){ frameserver *f = ctx; TEE(on_error(f->tee_cb.ctx, ep, seq, st, kind)); unit_parser_on_error(f->parser, ep, seq, st, kind); }
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
static int log_header(FILE *L,int retime){
    if(fprintf(L,"ordinal,epoch,observed_counter,counter_extended,applied_d1,applied_d2,f1_unused,f2_unused,reset_before,comb_ran,comb_d,comb_margin,comb_decided,confidence,frame_top_unit,triggers,frame_d1,frame_d2,f1_first,f2_first,f1_last,f2_last,bl1,bl2,hblank_level_f1,hblank_cols_f1,hblank_level_f2,hblank_cols_f2,class_f1,class_f2,published,drop_reason,preceding_ring_drops,schema_version,pairing,pairing_note,audio_residual_ticks,audio_step_samples,comb_energies,ge_wave_bar,ge_wave_clamp,wave_top_f1,wave_step_f1,wave_max_step_f1,wave_status_f1,wave_top_f2,wave_step_f2,wave_max_step_f2,wave_status_f2,relative_source,anchor_source,held_correction,ge_comb_reject,comb_reject_ratio,comb_rejected,comb_refused_d,comb_substituted_d,comb_discarded,comb_floor_lo,comb_floor_hi,comb_rise_left,comb_rise_right,comb_basin,ge_anchor_vote,ge_level_fill,ge_level_flat,vote_confident,vote_anchor,vote_engine_anchor,vote_count,vote_winner_count,vote_top_f1,vote_top_f2,level_top_f1,level_ref_f1,level_mean_f1,level_sd_f1,level_corr_f1,level_accepted_f1,level_top_f2,level_ref_f2,level_mean_f2,level_sd_f2,level_corr_f2,level_accepted_f2,ge_vote_pair,ge_vote_pair_min,vote_rB,vote_pair_pass,ge_bottom_flat,ge_bottom_flat_margin,bottom_rule_f1,bottom_F_p5_f1,bottom_F_p50_f1,bottom_F_p95_f1,bottom_rule_f2,bottom_F_p5_f2,bottom_F_p50_f2,bottom_F_p95_f2,ge_vote_blankspot,ge_comb_still,vote_blankspot_pass,vote_blankspot_line,motion_shift_f1,motion_error_f1,motion_error2_f1,motion_shift_f2,motion_error_f2,motion_error2_f2,picture_motion,still_trigger,comb_suppressed,ge_comb_motion_min,ge_comb_rigid,ge_comb_rigid_clarity,rigid_dx_f1,rigid_dy_f1,rigid_sad_f1,rigid_sad_far_f1,rigid_clarity_f1,rigid_dx_f2,rigid_dy_f2,rigid_sad_f2,rigid_sad_far_f2,rigid_clarity_f2")<0)return -1;
    if(retime) {
        if(fputs(",fs_hretime",L)==EOF)return -1;
        for(int k=1;k<=2;k++)
            if(fprintf(L,",hretime_bands_f%d,hretime_retimed_f%d,hretime_interpolated_f%d,hretime_unavailable_f%d,hretime_first_f%d,hretime_last_f%d,hretime_lines_f%d",k,k,k,k,k,k,k)<0)return -1;
        if(fputs(",hretime_edges_f1,hretime_edges_f2,hretime_content_f1,hretime_content_f2",L)==EOF)return -1;
        if(fputs(",hretime_evidence_f1,hretime_evidence_f2,hretime_normal_f1,hretime_normal_f2,hretime_typical_band",L)==EOF)return -1;
    }
    return fputc('\n',L)==EOF?-1:0;
}
/* v11 rows are unit-keyed. Frame diagnostics belong to that unit's bottom field;
 * frame_d1 therefore need not equal applied_d1 when pairing is reversed. Ineligible
 * observations keep provenance but have no placement/key for the renderer. */
static void geometry_log(frameserver *f,const fs_item *it,const ge_decision *d,int published,const char *drop,const ap_correlation *audio,const hrt_result *repair) {
    int64_t step=0;
    if(audio) {
        if(f->audio_residual_known && f->audio_residual_epoch==it->obs.epoch && f->audio_residual_run==audio->run) {
            int64_t delta=audio->residual_ticks-f->audio_residual_previous;
            // Each measurement is quantized within +/-3 ticks. A difference must
            // exceed both envelopes. Round signed ticks to the nearest sample.
            if(delta>6 || delta<-6)step=delta/5+(delta%5>=3)-(delta%5<=-3);
        }
        f->audio_residual_known=1;f->audio_residual_epoch=it->obs.epoch;
        f->audio_residual_run=audio->run;f->audio_residual_previous=audio->residual_ticks;
    }
    pthread_mutex_lock(&f->log_m);
    if(f->log) {
        char cell[30][64]={{0}};
#define CELL(i,fmt,v) snprintf(cell[i],sizeof cell[i],fmt,v)
        CELL(0,"%llu",(unsigned long long)it->obs.ordinal);
        CELL(1,"%llu",(unsigned long long)it->obs.epoch);
        CELL(2,"%llu",(unsigned long long)it->obs.counter_extended);
        if(d) {
            CELL(3,"%llu",(unsigned long long)d->counter);
            CELL(4,"%d",d->d1);CELL(5,"%d",d->d2);
            CELL(6,"%d",d->unused1);CELL(7,"%d",d->unused2);CELL(8,"%d",d->reset_before);
            if(d->has_frame) {
                CELL(9,"%d",d->comb_ran);
                if(!isnan(d->comb.margin)) {
                    CELL(10,"%d",d->comb.shift);CELL(11,"%.12g",d->comb.margin);CELL(12,"%d",d->comb.decided);
                }
                CELL(13,"%s",d->comb_ran?"LOW":"HIGH");CELL(14,"%llu",(unsigned long long)d->top_unit);
                CELL(15,"%u",d->triggers);CELL(16,"%d",d->frame_d1);CELL(17,"%d",d->frame_d2);
                for(int k=0;k<2;k++) {
                    if(d->first[k])CELL(18+k,"%d",d->first[k]);
                    if(d->last[k])CELL(20+k,"%d",d->last[k]);
                    if(d->bottom[k])CELL(22+k,"%d",d->bottom[k]);
                    CELL(24+k,"%s",ge_class_name(d->motion[k]));
                }
            }
        }
        CELL(26,"%d",published);CELL(27,"%s",drop);
        CELL(28,"%llu",(unsigned long long)it->preceding_ring_drops);CELL(29,"%d",f->cfg.hretime?FS_HRETIME_LOG_SCHEMA:FS_GEOMETRY_LOG_SCHEMA);
#undef CELL
        int bad=0;
        for(int i=0;i<30;i++) {
            if(fprintf(f->log,"%s,",cell[i])<0)bad=1;
            if(i==23) {
                if(d) {
                    if(fprintf(f->log,"%.12g,%d,%.12g,%d,",d->hblank_level[0],d->hblank_cols[0],
                               d->hblank_level[1],d->hblank_cols[1])<0)bad=1;
                } else if(fputs(",,,,",f->log)==EOF)bad=1;
            }
        }
        /* Pending reversed rows must retain THEIR note, not the next unit's note.
         * Counterless hole/tail rows use the active setting, not a fictitious 0. */
        const fs_pairing_row *pair=(d || (!it->gap_only && it->obs.format))?
            fs_pairing_find(&f->pairing,d?d->counter:it->obs.counter_extended):f->pairing_active;
        if(fprintf(f->log,"%s,",(pair?pair->reversed:f->geometry_reversed)?"reversed":"aligned")<0)bad=1;
        if(fs_pairing_write_note(f->log,pair?pair->note:"")<0)bad=1;
        if(audio) {
            if(fprintf(f->log,",%lld,%lld",(long long)audio->residual_ticks,(long long)step)<0)bad=1;
        } else if(fputs(",,",f->log)==EOF)bad=1;
        if(fputc(',',f->log)==EOF)bad=1;
        if(d && d->has_frame && !isnan(d->comb.margin))
            for(int i=0;i<11;i++)
                if(fprintf(f->log,"%s%.9g",i?" ":"",d->comb.energies[i])<0)bad=1;
        if(fprintf(f->log,",%.17g,%d",f->cfg.geometry_config->wave_bar,f->cfg.geometry_config->wave_clamp)<0)bad=1;
        for(int k=0;k<2;k++) {
            if(fputc(',',f->log)==EOF)bad=1;
            if(d) {
                if(d->wave[k].first && fprintf(f->log,"%d",d->wave[k].first)<0)bad=1;
                if(fprintf(f->log,",%.12g,%.12g,%s",d->wave[k].step,d->wave[k].max_step,
                           ge_wave_status_name(d->wave_status[k]))<0)bad=1;
            } else if(fputs(",,,",f->log)==EOF)bad=1;
        }
        if(d && d->has_frame) {
            if(fprintf(f->log,",%s,%s,%d",ge_source_name(d->relative_source),
                       ge_source_name(d->anchor_source),d->held)<0)bad=1;
        } else if(fputs(",,,",f->log)==EOF)bad=1;
        if(fprintf(f->log,",%.17g,",f->cfg.geometry_config->comb_reject)<0)bad=1;
        if(d && d->has_frame) {
            if(!isnan(d->rejection.ratio) && fprintf(f->log,"%.12g",d->rejection.ratio)<0)bad=1;
            if(fprintf(f->log,",%d,",d->rejected)<0)bad=1;
            if(d->rejected && fprintf(f->log,"%d",d->refused_d)<0)bad=1;
            if(fputc(',',f->log)==EOF)bad=1;
            if(d->rejected && !d->discarded && fprintf(f->log,"%d",d->substituted_d)<0)bad=1;
            if(fprintf(f->log,",%d,",d->discarded)<0)bad=1;
            if(!isnan(d->comb.margin)) {
                if(fprintf(f->log,"%d,%d,",d->rejection.floor_lo,d->rejection.floor_hi)<0)bad=1;
                if(!isnan(d->rejection.rise_left) && fprintf(f->log,"%.12g",d->rejection.rise_left)<0)bad=1;
                if(fputc(',',f->log)==EOF)bad=1;
                if(!isnan(d->rejection.rise_right) && fprintf(f->log,"%.12g",d->rejection.rise_right)<0)bad=1;
                if(fprintf(f->log,",%d",d->rejection.basin)<0)bad=1;
            } else if(fputs(",,,,",f->log)==EOF)bad=1;
        } else if(fputs(",,,,,,,,,",f->log)==EOF)bad=1;
        if(fprintf(f->log,",1,1,0")<0)bad=1; /* frozen schema-28 configuration */
        if(d && d->has_frame) {
            if(fprintf(f->log,",%d,%d,%d,%d,%d,%d,%d",d->vote_confident,d->vote_anchor,
                       d->vote_engine_anchor,d->vote_count,d->vote_winner_count,
                       d->vote_top[0],d->vote_top[1])<0)bad=1;
            for(int k=0;k<2;k++) {
                const ge_level_result *v=d->level+k;
                if(v->measured) {
                    if(fprintf(f->log,",%d,%.17g,%.17g,%.17g,%.17g,%d",v->first,v->reference,
                               v->mean,v->sd,v->corr_below,v->accepted)<0)bad=1;
                } else if(fputs(",,,,,,",f->log)==EOF)bad=1;
            }
        } else for(int k=0;k<19;k++)if(fputc(',',f->log)==EOF)bad=1;
        if(fprintf(f->log,",1,%.17g,",f->cfg.geometry_config->vote_pair_min)<0)bad=1;
        if(d && d->has_frame && !isnan(d->vote_rB)) {
            if(fprintf(f->log,"%.17g,%d",d->vote_rB,d->vote_pair_pass)<0)bad=1;
        } else if(fputc(',',f->log)==EOF)bad=1;
        if(fprintf(f->log,",1,%.17g",f->cfg.geometry_config->bottom_flat_margin)<0)bad=1;
        for(int k=0;k<2;k++) {
            if(d && d->has_frame) {
                const ge_bottom_evidence *e=d->bottom_evidence+k;
                if(fprintf(f->log,",%s",ge_bottom_rule_name(e->rule))<0)bad=1;
                if(e->measured) {
                    if(fprintf(f->log,",%.17g,%.17g,%.17g",e->p5,e->p50,e->p95)<0)bad=1;
                } else if(fputs(",,,",f->log)==EOF)bad=1;
            } else if(fputs(",,,,",f->log)==EOF)bad=1;
        }
        if(fprintf(f->log,",1,1")<0)bad=1;
        if(d && d->has_frame) {
            if(d->vote_blankspot_measured) {
                if(fprintf(f->log,",%d,%d",d->vote_blankspot_pass,d->vote_blankspot_line)<0)bad=1;
            } else if(fputs(",,",f->log)==EOF)bad=1;
            for(int k=0;k<2;k++) {
                const ge_vertical_motion *v=d->vertical+k;
                if(v->known) {
                    if(fprintf(f->log,",%d,%.17g,%.17g",v->shift,v->error,v->second_error)<0)bad=1;
                } else if(fputs(",,,",f->log)==EOF)bad=1;
            }
            if(fprintf(f->log,",%s,%d,%d",ge_picture_motion_name(d->picture_motion),d->still_trigger,d->comb_suppressed)<0)bad=1;
        } else for(int k=0;k<11;k++)if(fputc(',',f->log)==EOF)bad=1;
        if(fprintf(f->log,",1,1,%.17g",f->cfg.geometry_config->rigid_clarity)<0)bad=1;
        for(int k=0;k<2;k++) {
            if(d && d->has_frame && d->rigid[k].known) {
                const ge_rigid_motion *r=d->rigid+k;
                if(fprintf(f->log,",%d,%d,%.17g,%.17g,%.17g",r->dx,r->dy,r->error,r->far_error,r->clarity)<0)bad=1;
            } else if(fputs(",,,,,",f->log)==EOF)bad=1;
        }
        if(f->cfg.hretime) {
            if(fputs(",1",f->log)==EOF)bad=1;
            for(int k=0;k<2;k++) {
                if(repair) {
                    const hrt_field_result *r=repair->field+k;
                    if(fprintf(f->log,",%d,%d,%d,%d,%d,%d,",r->bands,r->retimed,r->interpolated,r->unavailable,r->first,r->last)<0)bad=1;
                    int sep=0;
                    for(int j=k;j<HRT_ROWS;j+=2)if(repair->action[j]) {
                        int line=(k?286+d->frame_d2:23+d->frame_d1)+j/2;
                        if(fprintf(f->log,"%s%d:%c",sep?" ":"",line,"NRIUC"[repair->action[j]])<0)bad=1;
                        sep=1;
                    }
                } else if(fputs(",,,,,,,",f->log)==EOF)bad=1;
            }
            for(int k=0;k<2;k++) {
                if(fputc(',',f->log)==EOF)bad=1;
                int sep=0;
                if(repair)for(int j=k;j<HRT_ROWS;j+=2)if(repair->action[j]) {
                    unsigned e=repair->edge_moved[j];
                    int line=(k?286+d->frame_d2:23+d->frame_d1)+j/2;
                    if(fprintf(f->log,"%s%d:%s%s%s%s%s",sep?" ":"",line,
                       e&HRT_LEFT_EARLIER?"L-":"",e&HRT_LEFT_LATER?"L+":"",
                       e&HRT_RIGHT_EARLIER?"R-":"",e&HRT_RIGHT_LATER?"R+":"",
                       !(e&HRT_EDGES_KNOWN)?"?":(e&15)?"":"=")<0)bad=1;
                    sep=1;
                }
            }
            for(int k=0;k<2;k++) {
                if(fputc(',',f->log)==EOF)bad=1;
                if(repair && fprintf(f->log,"%d",repair->field[k].content)<0)bad=1;
            }
            for(int k=0;k<2;k++) {
                if(fputc(',',f->log)==EOF)bad=1;
                if(repair)for(int j=k;j<HRT_ROWS;j+=2) {
                    int line=(k?286+d->frame_d2:23+d->frame_d1)+j/2;
                    if(fprintf(f->log,"%s%d:%u/%.9g/%.9g/%d",j==k?"":" ",line,
                       repair->reason[j],repair->r_line[j],repair->r_neighbours[j],repair->shift[j])<0)bad=1;
                }
            }
            for(int k=0;k<2;k++) {
                if(fputc(',',f->log)==EOF)bad=1;
                if(repair && fprintf(f->log,"%.9g/%.9g/%.9g/%.9g/%.9g",
                   repair->correlation_limit[k],repair->edge_median[k][0],repair->edge_median[k][1],
                   repair->edge_spread[k][0],repair->edge_spread[k][1])<0)bad=1;
            }
            if(fputc(',',f->log)==EOF)bad=1;
            if(repair && fprintf(f->log,"%.9g",repair->typical_band_length)<0)bad=1;
        }
        if(fputc('\n',f->log)==EOF)bad=1;
        if(bad){f->st.log_write_errors++;f->log_file_errors++;}else f->st.log_rows++;
        fs_test_after_log_row(f,f->log);
    }
    pthread_mutex_unlock(&f->log_m);
}
static void geometry_publish(frameserver *f,const fs_item *it,const uint8_t *unit,const ge_decision *d,const hrt_result *repair) {
    ap_correlation audio={0};int known=ap_lookup_correlation(f->aud,it->obs.epoch,d->counter,&audio);
#ifdef AP_LOOKUP_DIAGNOSTICS
    if(known!=it->audio_evidence_known || (known && memcmp(&audio,&it->audio_evidence,sizeof audio)))
        fprintf(stderr,"AUDIO-INGRESS-DIFF counter=%llu ingress_known=%d publication_known=%d ingress_residual=%lld publication_residual=%lld\n",
            (unsigned long long)d->counter,it->audio_evidence_known,known,
            (long long)it->audio_evidence.residual_ticks,(long long)audio.residual_ticks);
#endif
    if(known)atomic_fetch_add(&f->audio_master_frames,1);
    int rc=fp_publish_placed(f->pub,unit,FP_UNIT_BYTES,d->counter,d->d1,d->d2,FP_TRANSPORT_COMPLETE,known,audio.pts_num);
    if(rc==0)f->st.published++;else f->st.publisher_dropped++;
    if(rc==0){ memset(&f->ht,0,sizeof f->ht); f->ht_since=clock_gettime_nsec_np(CLOCK_UPTIME_RAW); }   /* accounting restarts at each handoff */
    uint64_t tl=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
    geometry_log(f,it,d,rc==0,rc==0?"None":"PublisherFull",
                 it->audio_evidence_known?&it->audio_evidence:NULL,repair);
    f->ht.log_ns+=clock_gettime_nsec_np(CLOCK_UPTIME_RAW)-tl;
}
/* Registration off: publish the nominal aperture. The engine's own evaluation
 * (comb, votes, census) stays in its decision fields for the sidecar. */
static void placement_override(const frameserver *f,ge_decision *out,unsigned n) {
    if(!f->cfg.registration_off)return;
    for(unsigned i=0;i<n;i++)out[i].d1=out[i].d2=out[i].frame_d1=out[i].frame_d2=0;
}
static void geometry_flush(frameserver *f) {
    if(f->retime_work)hrt_reset(f->retime_work);
    ge_decision out[2];unsigned n=ge_break(f->geometry,out);placement_override(f,out,n);
    if(n && f->geometry_pending)geometry_publish(f,&f->geometry_item,f->geometry_unit,out,NULL);
    f->geometry_pending=0;f->geometry_reset=1;
}
static void process_geometry(frameserver *f,const fs_item *it,const uint8_t *unit,const signal_result *sr,int classified) {
    if(it->obs.format) {
        const fs_pairing_row *pair=fs_pairing_find(&f->pairing,it->obs.counter_extended);
        if(pair && pair->reversed!=f->geometry_reversed) {
            geometry_flush(f); /* complete the old pairing's unused boundary first */
            f->geometry_reversed=pair->reversed;
            ge_set_pairing(f->geometry,f->geometry_reversed);
            f->st.discontinuity_calls++;
        }
        if(pair)f->pairing_active=pair; /* note-only changes never reset */
    }
    uint32_t actions=classified?sr->actions:0;
    if(actions&SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT)f->st.begin_segment_calls++;
    else if(actions&SIGNAL_ACTION_REGISTRATION_DISCONTINUITY)f->st.discontinuity_calls++;
    if(actions&(SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT|SIGNAL_ACTION_REGISTRATION_DISCONTINUITY))f->geometry_reset=1;
    if(it->preceding_ring_drops) {
        f->st.ring_drops_logged+=it->preceding_ring_drops;f->st.discontinuity_calls++;
        geometry_flush(f);
    }
    if(f->geometry_have_epoch && f->geometry_epoch!=it->obs.epoch)geometry_flush(f);
    /* A backward/repeated raw counter can extend by +1. It is still a broken
     * adjacency, even though the extended numbers alone look consecutive. */
    if(it->obs.transport_flags&UNIT_FLAG_COUNTER_DISCONTINUITY)geometry_flush(f);
    f->geometry_epoch=it->obs.epoch;f->geometry_have_epoch=1;
    if(!unit) {
        geometry_flush(f);
        if(it->drop==FS_DROP_POOL_FULL){atomic_fetch_add(&f->dropped_pool_full,1);f->st.exact_units++;f->st.discontinuity_calls++;}
        /* after the flush above, so an earlier whole unit still waiting for its pair is published first */
        const char *why=it->drop==FS_DROP_POOL_FULL?"PoolFull":transport_name(it->obs.transport);
        if(it->partial_lines && it->slot>=0) {
            const uint8_t *rows=f->pool+(size_t)it->slot*UNIT_PARSER_VIDEO_UNIT_BYTES+UNIT_PARSER_VIDEO_HEADER_BYTES;
            if(fp_publish_partial(f->pub,rows,it->partial_lines,it->obs.counter_extended,it->audio_evidence_known,it->audio_evidence.pts_num)==0) {
                f->st.partial_shown++;
                why=it->obs.transport==UNIT_TRANSPORT_SHORT?"ShortShown":"OtherShown";
            }
            atomic_store(&f->slot_used[it->slot],0);
        }
        geometry_log(f,it,NULL,0,why,NULL,NULL);
        return;
    }
    f->st.exact_units++;
    if(classified && sr->unsettled)f->st.unsettled_units++;
    const uint8_t *p=unit+48;
    for(unsigned i=0;i<GE_PIXELS;i++)f->geometry_y[i]=p[2*i+1];
    uint64_t tg=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
    ge_decision out[2];unsigned n=ge_push(f->geometry,f->geometry_y,it->obs.counter_extended,f->geometry_reset,out);
    f->ht.geometry_ns+=clock_gettime_nsec_np(CLOCK_UPTIME_RAW)-tg;
    placement_override(f,out,n);
    f->geometry_reset=0;
    if(f->cfg.hretime)memcpy(f->retime_unit,unit,FP_UNIT_BYTES);
    if(f->geometry_reversed) {
        /* Outputs precede replacement of the single pending raster. ge_push flushes
         * a broken counter adjacency, and never attaches the new field to it. */
        for(unsigned i=0;i<n;i++) {
            const uint8_t *published=f->geometry_unit;
            hrt_result *repair=NULL;
            if(f->cfg.hretime && out[i].has_frame) {
                memcpy(f->retime_previous,f->geometry_unit,FP_UNIT_BYTES);
                repair=&f->retime_result;
                hrt_begin(f->retime_work,out[i].top_unit,out[i].counter,it->obs.epoch,out[i].reset_before);
                uint64_t th=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
                hrt_apply(f->retime_work,unit,f->geometry_unit,out[i].frame_d1,out[i].frame_d2,
                          f->retime_unit,f->retime_previous,repair);
                f->ht.hretime_ns+=clock_gettime_nsec_np(CLOCK_UPTIME_RAW)-th;
                published=f->retime_previous;
            }
            geometry_publish(f,&f->geometry_item,published,out+i,repair);
        }
        /* Current f1 belongs to the completed frame; pending f2 is still raw.
         * Geometry already retained the untouched current raster in ge_push. */
        memcpy(f->geometry_unit,f->cfg.hretime?f->retime_unit:unit,FP_UNIT_BYTES);f->geometry_item=*it;
        f->geometry_pending=1;f->geometry_epoch=it->obs.epoch;
    } else {
        for(unsigned i=0;i<n;i++) {
            hrt_result *repair=NULL;
            if(f->cfg.hretime && out[i].has_frame) {
                repair=&f->retime_result;
                hrt_begin(f->retime_work,out[i].top_unit,out[i].counter,it->obs.epoch,out[i].reset_before);
                uint64_t th=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
                hrt_apply(f->retime_work,unit,unit,out[i].frame_d1,out[i].frame_d2,
                          f->retime_unit,f->retime_unit,repair);
                f->ht.hretime_ns+=clock_gettime_nsec_np(CLOCK_UPTIME_RAW)-th;
            }
            geometry_publish(f,it,f->cfg.hretime?f->retime_unit:unit,out+i,repair);
        }
        f->geometry_epoch=it->obs.epoch;
    }
    atomic_store(&f->slot_used[it->slot],0);
}
static void process_item(frameserver *f, const fs_item *it){
    if(it->gap_only){
        geometry_flush(f);f->st.discontinuity_calls++;f->st.ring_drops_logged+=it->preceding_ring_drops;f->st.ring_gap_rows++;
        geometry_log(f,it,NULL,0,"RingFullTail",NULL,NULL);return;
    }
    unit_video_observation obs = it->obs;
    const uint8_t *unit = NULL;
    if (it->slot >= 0 && !it->partial_lines){ unit = f->pool + (size_t)it->slot * UNIT_PARSER_VIDEO_UNIT_BYTES; obs.bytes = unit; obs.payload = unit + UNIT_PARSER_VIDEO_HEADER_BYTES; }
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
    uint64_t tc=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
    bool classified = signal_state_classify(f->sig, &obs, &signal_ctx, &sr);
    f->ht.classify_ns+=clock_gettime_nsec_np(CLOCK_UPTIME_RAW)-tc;
    process_geometry(f,it,unit,&sr,classified);
}
static void *worker_main(void *arg){
    frameserver *f = arg;
    callback_session=f;
    pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED, 0);
    pthread_mutex_lock(&f->life_m);
    while(!f->start_gate) pthread_cond_wait(&f->life_c,&f->life_m);
    pthread_mutex_unlock(&f->life_m);
    for (;;){
        unsigned t = atomic_load_explicit(&f->r_tail, memory_order_relaxed);
        unsigned h = atomic_load_explicit(&f->r_head, memory_order_acquire);
        if (h == t){
            if(!f->idle_since) f->idle_since=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
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
        { uint64_t now=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
          if(f->idle_since){ f->ht.idle_ns+=now-f->idle_since; f->idle_since=0; }
          f->ht.queue_wait_ns=it.t_enqueue&&now>it.t_enqueue?now-it.t_enqueue:0; f->ht.items++; }
        process_item(f, &it);
        fs_test_after_item(f);
    }
    if(f->geometry)geometry_flush(f);
    atomic_store(&f->worker_done, 1);
    if (atomic_fetch_add(&f->workers_terminal, 1) == 1 && atomic_load_explicit(&f->notify_end, memory_order_acquire) && f->cfg.on_end)
        f->cfg.on_end(f->cfg.end_ctx, f->end_reason);
    callback_session=NULL;
    return NULL;
}

// ------------------------------------------------------------ lifecycle
static void count_sink(void *ctx, const fp_frame *fr){ (void)ctx; (void)fr; }
int fs_open(frameserver **out, const fs_config *cfg){
    if (!out || !cfg || (cfg->geometry_config && !ge_config_valid(cfg->geometry_config))) return -1;
    if(cfg->pairing_schedule && cfg->geometry_pair_next) {
        fprintf(stderr,"pairing schedule: excludes --pair-next\n");return -1;
    }
    frameserver *f = calloc(1, sizeof *f); if (!f) return -1;
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
    f->geometry_reversed=!!cfg->geometry_pair_next;
    if(cfg->pairing_schedule) {
        if(fs_pairing_load(&f->pairing,cfg->pairing_schedule)){fs_close(f);return -1;}
        f->pairing_active=fs_pairing_find(&f->pairing,0);
        f->geometry_reversed=f->pairing_active->reversed;
    }
    // Default: as many unit slots as the capture ring holds bytes, so a slow video worker can fall
    // behind for as long as acquisition itself can buffer (~11.8 s at the 256 MB default) before
    // units are shed. Measured stall that motivated it: a live OBS capture on 2026-09-27 lost 64
    // units (2.1 s) when the worker stalled past the old 64-slot pool while the ring stayed nearly
    // empty. The delivery thread drains the ring immediately (it also carries audio), so the pool,
    // not the ring, is the buffer a worker stall consumes; a zero-copy single buffer is the follow-up.
    if (cfg->pool_units) f->n_slots = cfg->pool_units;
    else {
        size_t ring = (size_t)(cfg->capture.ring_mb > 0 ? cfg->capture.ring_mb : CC_DEFAULT_RING_MB) << 20;
        f->n_slots = (unsigned)(ring / UNIT_PARSER_VIDEO_UNIT_BYTES);
        if (!f->n_slots) f->n_slots = 1;
    }
    f->pool = malloc((size_t)f->n_slots * UNIT_PARSER_VIDEO_UNIT_BYTES);
    f->slot_used = calloc(f->n_slots, sizeof(_Atomic int));
    f->parser = aligned_alloc(unit_parser_alignment(), unit_parser_size());
    f->sig = aligned_alloc(signal_state_alignment(), signal_state_size());
    if (!f->pool || !f->slot_used || !f->parser || !f->sig){ fs_close(f); return -1; }
    unit_parser_callbacks pcb = { on_video, on_audio, f };
    unit_parser_init(f->parser, NULL, &pcb);
    signal_state_init(f->sig, cfg->signal_config);
    f->cfg.signal_config = signal_state_get_config(f->sig);
    {
        f->geometry=malloc(ge_size());f->geometry_y=malloc(GE_PIXELS);
        f->geometry_unit=malloc(FP_UNIT_BYTES);
        if(cfg->hretime) {
            f->retime_unit=malloc(FP_UNIT_BYTES);f->retime_previous=malloc(FP_UNIT_BYTES);
            f->retime_work=calloc(1,hrt_size());
            if(!f->retime_unit || !f->retime_previous || !f->retime_work){fs_close(f);return -1;}
        }
        if(!f->geometry||!f->geometry_y||!f->geometry_unit){fs_close(f);return -1;}
        ge_init(f->geometry,f->geometry_reversed,cfg->geometry_config);
        f->cfg.geometry_config=ge_get_config(f->geometry);
    }
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
    if (pthread_mutex_init(&f->tee_m, NULL)){ fs_close(f); return -1; } f->tee_m_init = 1;
    if (cfg->decision_log){ f->log = fs_async_fopen_excl(cfg->decision_log, FS_LOG_RING_BYTES, FS_LOG_WRITE_CHUNK); if (!f->log || log_header(f->log,cfg->hretime) != 0){ fs_close(f); return -1; } f->st.log_files++; }   // exclusive: a sidecar is evidence, never truncated
    cc_callbacks ccb = { cc_on_packet, cc_on_loss, cc_on_error, cc_on_tick, cc_on_end, f };
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
    if(callback_session==f) return -1;   // no self-join from a callback
    pthread_mutex_lock(&f->life_m);
    while(f->life==FS_LIFE_STOPPING) pthread_cond_wait(&f->life_c,&f->life_m);
    if(f->life==FS_LIFE_STOPPED){ pthread_mutex_unlock(&f->life_m); return 0; }
    if(f->life!=FS_LIFE_RUNNING){ pthread_mutex_unlock(&f->life_m); return -1; }
    f->life=FS_LIFE_STOPPING; pthread_mutex_unlock(&f->life_m);
    cc_stop(f->cap);                        // fires on_end -> producer_done (audio flushed before it)
    pthread_join(f->worker, NULL);
    pthread_join(f->audio_worker, NULL);    // exits by itself once cc_on_end set audio_done and the queue drained
    cc_async_sink *T = fs_tee_detach(f); if (T) cc_async_sink_close(T, NULL);   // the capture is stopped: nothing more can arrive
    pthread_mutex_lock(&f->log_m); FILE *L = f->log; f->log = NULL; uint64_t ferrs = f->log_file_errors; pthread_mutex_unlock(&f->log_m);   // detach under the lock (fs_log_stop may race), close outside it
    if (L){ if (fclose(L) != 0){ f->st.log_close_errors++; ferrs++; } f->st.log_last_file_errors = ferrs; }
    pthread_mutex_lock(&f->life_m); f->life=FS_LIFE_STOPPED; pthread_cond_broadcast(&f->life_c); pthread_mutex_unlock(&f->life_m);
    return 0;
}
// Runtime decision-log attachment (a recorder aligns the sidecar to ITS recording, not to the
// session). Refused from the worker threads (they hold the row lock while writing) and while a
// log is attached: one log at a time, and the caller decides when the previous one ends.
static int fs_log_from_worker(const frameserver *f){
    return callback_session==f;
}
int fs_log_start(frameserver *f, const char *path){
    if(!f || !path || !*path || fs_log_from_worker(f)) return -1;
    pthread_mutex_lock(&f->log_m); int attached = f->log != NULL; pthread_mutex_unlock(&f->log_m);
    if(attached) return -1;                            // one log at a time; the caller ends the previous one
    FILE *L = fs_async_fopen_excl(path, FS_LOG_RING_BYTES, FS_LOG_WRITE_CHUNK);   // never truncate an existing file: a sidecar is evidence
    if(!L) return -1;
    if(log_header(L,f->cfg.hretime) != 0){ fclose(L); remove(path); return -1; }   // we created it; a header-less file is not a log
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
FILE *fs_log_detach(frameserver *f, uint64_t *row_errors){
    if(!f || fs_log_from_worker(f)) return NULL;
    pthread_mutex_lock(&f->log_m);
    FILE *L = f->log; f->log = NULL; uint64_t errs = f->log_file_errors;
    pthread_mutex_unlock(&f->log_m);
    if(L && row_errors) *row_errors = errs;
    return L;
}
int fs_tee_start(frameserver *f, const char *path, const char *note, size_t ring_bytes){
    if(!f || !path || !*path || fs_log_from_worker(f) || !f->tee_m_init) return -1;
    pthread_mutex_lock(&f->tee_m); int attached = f->tee != NULL; pthread_mutex_unlock(&f->tee_m);
    if(attached) return -1;
    cc_async_sink *k; if(cc_async_sink_open(&k, path, note, ring_bytes, 1u<<20) != CC_OK) return -1;
    pthread_mutex_lock(&f->life_m);
    if(f->life!=FS_LIFE_RUNNING){ pthread_mutex_unlock(&f->life_m); cc_async_sink_close(k,NULL); remove(path); return -1; }
    pthread_mutex_lock(&f->tee_m);
    if(f->tee){ pthread_mutex_unlock(&f->tee_m); pthread_mutex_unlock(&f->life_m); cc_async_sink_close(k,NULL); remove(path); return -1; }
    cc_async_sink_callbacks(k, &f->tee_cb); f->tee = k;
    pthread_mutex_unlock(&f->tee_m); pthread_mutex_unlock(&f->life_m);
    return 0;
}
cc_async_sink *fs_tee_detach(frameserver *f){
    if(!f || !f->tee_m_init) return NULL;
    pthread_mutex_lock(&f->tee_m); cc_async_sink *k = f->tee; f->tee = NULL; pthread_mutex_unlock(&f->tee_m);
    return k;
}
void fs_handoff_timing_get(const frameserver *f, fs_handoff_timing *o){
    *o=f->ht;
    uint64_t now=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
    o->since_prev_ns=f->ht_since&&now>f->ht_since?now-f->ht_since:0;
    uint64_t known=o->idle_ns+o->classify_ns+o->geometry_ns+o->hretime_ns+o->log_ns;
    o->other_ns=o->since_prev_ns>known?o->since_prev_ns-known:0;
}
int fs_device_start_info(const frameserver *f, uint32_t *mode_word, uint32_t *reg4, const char **reg4_action){
    return f && f->cap ? cc_start_info(f->cap, mode_word, reg4, reg4_action) : -1;
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
    o->dropped_ring_full = atomic_load(&f->dropped_ring_full); o->pool_high_water = atomic_load(&f->pool_hw); o->pool_units = f->n_slots;
    o->eligible_observations = atomic_load(&f->eligible_ingress);
    o->holes = atomic_load(&f->holes); o->unframed = atomic_load(&f->unframed); o->short_units = atomic_load(&f->shorts);
    o->other_format = atomic_load(&f->other_fmt); o->no_signal_0800 = atomic_load(&f->ns0800);
}
uint64_t fs_packets_delivered(const frameserver *f){ return cc_packets_delivered(f->cap); }
int fs_replay_pause(frameserver *f, int paused){ return f && f->cap && cc_replay_pause(f->cap, paused) == CC_OK ? 0 : -1; }
void fs_close(frameserver *f){
    if (!f) return;
    if(callback_session==f){
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
    if (f->tee_m_init) pthread_mutex_destroy(&f->tee_m);
    if(f->c_init) pthread_cond_destroy(&f->c);
    if(f->m_init) pthread_mutex_destroy(&f->m);
    if(f->life_c_init) pthread_cond_destroy(&f->life_c);
    if(f->life_m_init) pthread_mutex_destroy(&f->life_m);
    fs_test_destroyed();
    free(f->geometry);free(f->geometry_y);free(f->geometry_unit);
    free(f->retime_unit);free(f->retime_previous);free(f->retime_work);
    fs_pairing_free(&f->pairing);
    free(f->pool); free((void *)f->slot_used); free(f->parser); free(f->sig); free(f);
}
