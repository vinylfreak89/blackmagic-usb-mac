#include "audio_publisher.h"
#include <stdlib.h>
#include <string.h>

// Entries are read from other threads under a seqlock; the fields themselves are atomics
// (relaxed) so a concurrent read is never a C11 data race, only a possibly torn snapshot
// that the sequence check rejects.
typedef struct { _Atomic uint64_t epoch, counter, ordinal, pts; _Atomic int anchored; } ap_corr;

struct audio_publisher {
    ap_sink sink;
    uint8_t *buf; uint32_t cap, n;          // frames buffered
    uint64_t first_ordinal;                 // ordinal of buf[0]
    uint64_t epoch; int have_epoch;
    // run timing: pts(ord) = run_pts0 + (ord - run_ord0) * 5 once anchored
    int anchored; uint64_t run_ord0, run_pts0, anchor_counter;
    int have_last_resync; uint64_t last_resync_counter; int64_t last_residual;
    uint32_t pending_flags;                 // flags to stamp on the next emitted block
    // correlation history (single writer = delivery thread; readers anywhere)
    ap_corr corr[AP_LOOKUP_ENTRIES]; _Atomic uint32_t corr_seq; uint32_t corr_next;
    ap_stats st;
};

int ap_open(audio_publisher **out, uint32_t capacity_frames, const ap_sink *sink){
    if (!out || !sink || !sink->on_block || capacity_frames < 2) return -1;
    audio_publisher *p = calloc(1, sizeof *p); if (!p) return -1;
    p->buf = malloc((size_t)capacity_frames * AP_BYTES_PER_FRAME);
    if (!p->buf){ free(p); return -1; }
    p->cap = capacity_frames; p->sink = *sink;
    p->st.residual_min = INT64_MAX; p->st.residual_max = INT64_MIN;
    *out = p; return 0;
}

static uint64_t pts_of_(const audio_publisher *p, uint64_t ord){
    if (p->anchored) return p->run_pts0 + (ord - p->run_ord0) * AP_TICKS_PER_FRAME;
    return ord * AP_TICKS_PER_FRAME;                      // ordinal-only until anchored
}

static void emit_(audio_publisher *p, uint32_t extra_flags){
    if (!p->n){ p->pending_flags |= extra_flags; return; }
    ap_block b;
    b.pts_num = pts_of_(p, p->first_ordinal); b.pts_den = AP_PTS_DEN;
    b.epoch = p->epoch; b.sample_ordinal = p->first_ordinal;
    b.anchor_counter_ext = p->anchored ? p->anchor_counter : 0;
    b.last_resync_counter_ext = p->have_last_resync ? p->last_resync_counter : 0;
    b.correlation_residual = p->have_last_resync ? p->last_residual : 0;
    b.n_frames = p->n; b.s24le = p->buf;
    b.sample_rate = AP_SAMPLE_RATE; b.channels = AP_CHANNELS;
    b.flags = p->pending_flags | extra_flags | (p->anchored ? 0 : AP_FLAG_UNANCHORED);
    p->sink.on_block(p->sink.ctx, &b);
    p->st.blocks++; p->st.frames_published += p->n;
    if (b.flags & AP_FLAG_PARTIAL) p->st.blocks_partial++;
    if (b.flags & AP_FLAG_UNANCHORED) p->st.blocks_unanchored++;
    p->n = 0; p->pending_flags = 0;
}

static void discontinuity_(audio_publisher *p){
    emit_(p, 0);                             // what we had is contiguous up to here
    p->pending_flags |= AP_FLAG_DISCONTINUITY_BEFORE;
    p->anchored = 0; p->have_last_resync = 0; // physical time is unknown across missing bytes
    p->st.discontinuities++;
}

static void corr_record_(audio_publisher *p, uint64_t counter, uint64_t ordinal, uint64_t pts, int anchored){
    uint32_t i = p->corr_next++ % AP_LOOKUP_ENTRIES;
    // odd = writing. acq_rel: no entry mutation below may become visible before the odd value
    // (a reader that sees an even value with torn entries would accept them).
    atomic_fetch_add_explicit(&p->corr_seq, 1, memory_order_acq_rel);
    atomic_store_explicit(&p->corr[i].epoch, p->epoch, memory_order_relaxed);
    atomic_store_explicit(&p->corr[i].counter, counter, memory_order_relaxed);
    atomic_store_explicit(&p->corr[i].ordinal, ordinal, memory_order_relaxed);
    atomic_store_explicit(&p->corr[i].pts, pts, memory_order_relaxed);
    atomic_store_explicit(&p->corr[i].anchored, anchored, memory_order_relaxed);
    atomic_fetch_add_explicit(&p->corr_seq, 1, memory_order_release);   // even: stable
}

int ap_lookup(const audio_publisher *p, uint64_t epoch, uint64_t counter_ext, uint64_t *pts_num, uint64_t *ordinal){
    if (!p) return 0;
    for (int attempt = 0; attempt < 8; attempt++){
        uint32_t s0 = atomic_load_explicit(&p->corr_seq, memory_order_acquire);
        if (s0 & 1u) continue;
        uint64_t hpts = 0, hord = 0; int found = 0;
        for (unsigned i = 0; i < AP_LOOKUP_ENTRIES; i++)
            if (atomic_load_explicit(&p->corr[i].counter, memory_order_relaxed) == counter_ext &&
                atomic_load_explicit(&p->corr[i].epoch, memory_order_relaxed) == epoch &&
                atomic_load_explicit(&p->corr[i].anchored, memory_order_relaxed)){
                hpts = atomic_load_explicit(&p->corr[i].pts, memory_order_relaxed);
                hord = atomic_load_explicit(&p->corr[i].ordinal, memory_order_relaxed);
                found = 1; break;
            }
        atomic_thread_fence(memory_order_acquire);
        uint32_t s1 = atomic_load_explicit(&p->corr_seq, memory_order_relaxed);
        if (s0 != s1) continue;                            // torn: retry
        if (!found) return 0;
        if (pts_num) *pts_num = hpts; if (ordinal) *ordinal = hord;
        return 1;
    }
    return 0;
}

void ap_on_audio(audio_publisher *p, const unit_audio_observation *o){
    if (!p || !o) return;
    if (!p->have_epoch || o->epoch != p->epoch){
        if (p->have_epoch) discontinuity_(p);
        p->epoch = o->epoch; p->have_epoch = 1;
    }
    switch (o->kind){
    case UNIT_AUDIO_PCM:
        p->st.records_pcm++;
        if (p->n && p->first_ordinal + p->n != o->sample_ordinal) discontinuity_(p);   // ordinal must be contiguous
        if (!p->n) p->first_ordinal = o->sample_ordinal;
        memcpy(p->buf + (size_t)p->n * AP_BYTES_PER_FRAME, o->active_s24le, AP_BYTES_PER_FRAME);
        p->n++;
        if (p->n == p->cap) emit_(p, AP_FLAG_PARTIAL);
        break;
    case UNIT_AUDIO_RESYNC: {
        p->st.records_resync++;
        uint64_t video_pts = o->counter_extended * AP_TICKS_PER_UNIT;
        int gap = (o->transport_flags & UNIT_FLAG_COUNTER_DISCONTINUITY) != 0 ||
                  (p->have_last_resync && o->counter_extended != p->last_resync_counter + 1);
        emit_(p, 0);                                     // the unit before this resync is complete
        if (gap){ p->st.counter_gaps++; p->pending_flags |= AP_FLAG_COUNTER_GAP; }   // lands on the NEXT block
        if (!p->anchored){
            // first resync of a contiguous run: place the run on the video timebase, once
            p->anchored = 1; p->anchor_counter = o->counter_extended;
            p->run_ord0 = o->sample_ordinal; p->run_pts0 = video_pts;
            p->last_residual = 0;
        } else {
            p->last_residual = (int64_t)video_pts - (int64_t)pts_of_(p, o->sample_ordinal);
            if (p->last_residual < p->st.residual_min) p->st.residual_min = p->last_residual;
            if (p->last_residual > p->st.residual_max) p->st.residual_max = p->last_residual;
            p->st.resyncs_anchored++;
        }
        p->have_last_resync = 1; p->last_resync_counter = o->counter_extended;
        corr_record_(p, o->counter_extended, o->sample_ordinal, pts_of_(p, o->sample_ordinal), 1);
        break; }
    case UNIT_AUDIO_HOLE:
        p->st.records_hole++; discontinuity_(p); break;
    case UNIT_AUDIO_UNFRAMED:
        p->st.records_unframed++; discontinuity_(p); break;
    }
}

void ap_flush(audio_publisher *p){ if (p) emit_(p, 0); }
void ap_get_stats(const audio_publisher *p, ap_stats *out){ if (p && out) *out = p->st; }
void ap_close(audio_publisher *p){ if (!p) return; free(p->buf); free(p); }
