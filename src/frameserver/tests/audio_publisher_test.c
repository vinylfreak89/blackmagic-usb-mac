// audio_publisher invariants on synthetic observation sequences, modelled on the real parser:
//   sample conservation; sample-contiguous pts across 1601/1602-frame units (no ±0.6-sample
//   gaps at block boundaries) with the residual REPORTED, not applied; empty resync intervals;
//   a hole exactly as the parser emits it (ordinal does not advance) -> flagged, unanchored until
//   the next resync; counter gaps (extended jump and parser-flagged) -> COUNTER_GAP; partial
//   blocks; epoch change; ap_lookup correlation for video counters; timebase arithmetic.
#include "../audio_publisher.h"
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; fprintf(stderr, "FAIL: " __VA_ARGS__); fprintf(stderr, "\n"); } } while (0)

typedef struct { ap_block blocks[64]; uint8_t first[64]; int n; uint64_t frames; uint8_t bytes[8192*6]; size_t nbytes; } sinkstate;
static void on_block(void *ctx, const ap_block *b){
    sinkstate *s = ctx; if (s->n < 64){ s->blocks[s->n] = *b; s->first[s->n] = b->s24le[0]; s->blocks[s->n].s24le = NULL; s->n++; }
    size_t nb = (size_t)b->n_frames * 6; if (s->nbytes + nb <= sizeof s->bytes){ memcpy(s->bytes + s->nbytes, b->s24le, nb); s->nbytes += nb; }
    s->frames += b->n_frames;
}
static unit_audio_observation pcm(uint64_t epoch, uint64_t ord, uint8_t tag){
    unit_audio_observation o; memset(&o, 0, sizeof o); o.epoch = epoch; o.kind = UNIT_AUDIO_PCM; o.transport = UNIT_TRANSPORT_COMPLETE;
    o.sample_ordinal = ord; memset(o.active_s24le, tag, 6); return o;
}
static unit_audio_observation resync(uint64_t epoch, uint64_t ord, uint64_t ctr, uint32_t flags){
    unit_audio_observation o; memset(&o, 0, sizeof o); o.epoch = epoch; o.kind = UNIT_AUDIO_RESYNC; o.transport = UNIT_TRANSPORT_COMPLETE;
    o.sample_ordinal = ord; o.counter_extended = ctr; o.counter16 = (uint16_t)ctr; o.transport_flags = flags; return o;
}
static unit_audio_observation hole(uint64_t epoch, uint64_t ord){
    unit_audio_observation o; memset(&o, 0, sizeof o); o.epoch = epoch; o.kind = UNIT_AUDIO_HOLE; o.transport = UNIT_TRANSPORT_HOLE; o.sample_ordinal = ord; return o;
}
static void feed_pcm(audio_publisher *p, uint64_t epoch, uint64_t *ord, int n, uint8_t tag){
    for (int i = 0; i < n; i++){ unit_audio_observation o = pcm(epoch, *ord, tag); o.active_s24le[5] = (uint8_t)(*ord); ap_on_audio(p, &o); (*ord)++; }
}
// seqlock stress: writer hammers resyncs on a run anchored at (counter 0, ordinal 0) so every entry
// must satisfy pts == ordinal * 5; a torn read would violate it.
typedef struct { audio_publisher *p; _Atomic int stop; _Atomic long lookups, hits, torn; } stressctx;
static void *stress_reader(void *arg){
    stressctx *c = arg;
    while (!atomic_load(&c->stop)){
        uint64_t pts, ord; uint64_t ctr = (uint64_t)(atomic_load(&c->lookups) % 200);
        atomic_fetch_add(&c->lookups, 1);
        if (ap_lookup(c->p, 1, ctr, &pts, &ord)){ atomic_fetch_add(&c->hits, 1); if (pts != ord * AP_TICKS_PER_FRAME) atomic_fetch_add(&c->torn, 1); }
    }
    return NULL;
}

int main(void){
    sinkstate s; memset(&s, 0, sizeof s);
    ap_sink sink = { on_block, &s };
    audio_publisher *p = NULL;
    CHECK(ap_open(&p, 1, &sink) != 0, "capacity < 2 must be refused");

    // 1: contiguity across real unit sizes. resync(c=10) then 1601 frames, resync(11), 1602, resync(12), 1601, flush.
    CHECK(ap_open(&p, 4096, &sink) == 0, "open");
    uint64_t ord = 0;
    feed_pcm(p, 1, &ord, 3, 0xA0);                                   // unanchored preamble
    { unit_audio_observation o = resync(1, ord, 10, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 1601, 0xB0);
    { unit_audio_observation o = resync(1, ord, 11, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 1602, 0xC0);
    { unit_audio_observation o = resync(1, ord, 12, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 1601, 0xD0);
    ap_flush(p);
    ap_stats st; ap_get_stats(p, &st);
    CHECK(s.n == 4, "four blocks (preamble + three units), got %d", s.n);
    CHECK(s.frames == 3 + 1601 + 1602 + 1601 && st.frames_published == s.frames && st.records_pcm == s.frames, "conservation: %llu", (unsigned long long)s.frames);
    if (s.n == 4){
        CHECK(s.blocks[0].flags & AP_FLAG_UNANCHORED && s.blocks[0].pts_num == 0, "preamble unanchored, ordinal-only pts");
        CHECK(!(s.blocks[1].flags & AP_FLAG_UNANCHORED) && s.blocks[1].anchor_counter_ext == 10 && s.blocks[1].pts_num == 10ull * AP_TICKS_PER_UNIT, "unit 10 anchored at 10*8008");
        // sample-contiguous: block2 starts exactly 1601 frames after block1, NOT at 11*8008
        CHECK(s.blocks[2].pts_num == s.blocks[1].pts_num + 1601ull * AP_TICKS_PER_FRAME, "block after a 1601-frame unit continues by 1601*5 ticks (got %llu, want %llu)",
              (unsigned long long)s.blocks[2].pts_num, (unsigned long long)(s.blocks[1].pts_num + 1601ull * 5));
        CHECK(s.blocks[2].pts_num != 11ull * AP_TICKS_PER_UNIT, "pts is not snapped to the resync (that would open a 0.6-sample gap)");
        CHECK(s.blocks[3].pts_num == s.blocks[2].pts_num + 1602ull * AP_TICKS_PER_FRAME, "block after a 1602-frame unit continues by 1602*5 ticks");
        // residual reported: at resync 11, video says 11*8008 = 88088, audio says 80080+8005 = 88085 -> +3 ticks (0.6 sample)
        CHECK(s.blocks[2].last_resync_counter_ext == 11 && s.blocks[2].correlation_residual == 3, "residual at resync 11 = +3 ticks, got %lld", (long long)s.blocks[2].correlation_residual);
        CHECK(s.blocks[3].last_resync_counter_ext == 12 && s.blocks[3].correlation_residual == 1, "residual at resync 12 = +1 tick, got %lld", (long long)s.blocks[3].correlation_residual);
        CHECK(s.blocks[1].anchor_counter_ext == s.blocks[3].anchor_counter_ext, "the anchor never moves within a contiguous run");
        CHECK(s.first[1] == 0xB0 && s.first[2] == 0xC0 && s.first[3] == 0xD0, "blocks carry their own unit's samples");
        CHECK(!(s.blocks[1].flags & AP_FLAG_COUNTER_GAP) && !(s.blocks[3].flags & AP_FLAG_COUNTER_GAP), "consecutive counters are not gaps");
    }
    CHECK(st.resyncs_anchored == 2 && st.residual_min == 1 && st.residual_max == 3, "residual envelope over anchored resyncs [1,3], got [%lld,%lld]", (long long)st.residual_min, (long long)st.residual_max);
    // ap_lookup: audio-clock time of video units 10, 11, 12; unknown for 13 and for the unanchored era
    uint64_t lp, lo;
    CHECK(ap_lookup(p, 1, 10, &lp, &lo) && lp == 10ull * AP_TICKS_PER_UNIT && lo == 3, "lookup(10) = anchor pts, ordinal 3");
    CHECK(ap_lookup(p, 1, 11, &lp, &lo) && lp == 10ull * AP_TICKS_PER_UNIT + 1601ull * 5 && lo == 3 + 1601, "lookup(11) = audio-clock time of unit 11 (contiguous), got %llu", (unsigned long long)lp);
    CHECK(ap_lookup(p, 1, 12, &lp, &lo) && lp == 10ull * AP_TICKS_PER_UNIT + (1601ull + 1602ull) * 5, "lookup(12) contiguous");
    CHECK(!ap_lookup(p, 1, 13, &lp, &lo), "lookup of an unseen counter fails");
    CHECK(!ap_lookup(p, 2, 11, &lp, &lo), "lookup is qualified by epoch");
    // byte-order conservation: every PCM record's bytes appear exactly once, in order
    { int ok = s.nbytes == s.frames * 6; for (size_t i = 0; ok && i < s.frames; i++) ok = s.bytes[i*6+5] == (uint8_t)i; CHECK(ok, "PCM bytes delivered in order through block splits"); }
    // timebase constants
    CHECK(AP_PTS_DEN % 30000u == 0 && AP_PTS_DEN % 48000u == 0 && AP_TICKS_PER_UNIT == AP_PTS_DEN / 30000u * 1001u && AP_TICKS_PER_FRAME == AP_PTS_DEN / 48000u, "tick constants");
    CHECK(8008u == (uint32_t)(1601.6 * 5.0 + 0.5), "one video unit = 1601.6 frames of audio in ticks");

    // 2: empty resync interval (resync, resync, no PCM) -> no block, correlation advances, no gap flag
    ap_close(p); memset(&s, 0, sizeof s); CHECK(ap_open(&p, 64, &sink) == 0, "reopen 2");
    ord = 500;
    { unit_audio_observation o = resync(1, ord, 40, 0); ap_on_audio(p, &o); }
    { unit_audio_observation o = resync(1, ord, 41, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 5, 1);
    ap_flush(p); ap_get_stats(p, &st);
    CHECK(s.n == 1 && s.frames == 5, "empty interval produced no block; one block after");
    CHECK(s.n == 1 && !(s.blocks[0].flags & AP_FLAG_COUNTER_GAP) && s.blocks[0].last_resync_counter_ext == 41 && s.blocks[0].correlation_residual == 8008, "residual after an empty unit = one unit of video time with zero audio frames (%lld)", s.n ? (long long)s.blocks[0].correlation_residual : -1);
    CHECK(ap_lookup(p, 1, 41, &lp, &lo) && lo == 500, "lookup(41) exists with the same ordinal");

    // 3: a hole exactly as the parser emits it: ordinal does NOT advance; next block flagged + unanchored until the next resync
    ap_close(p); memset(&s, 0, sizeof s); CHECK(ap_open(&p, 64, &sink) == 0, "reopen 3");
    ord = 1000;
    { unit_audio_observation o = resync(1, ord, 7, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 2, 1);
    { unit_audio_observation o = hole(1, ord); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 2, 2);                                       // ordinal continues from 1002
    { unit_audio_observation o = resync(1, ord, 8, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 1, 3);
    ap_flush(p); ap_get_stats(p, &st);
    CHECK(s.n == 3, "hole case: 3 blocks, got %d", s.n);
    if (s.n == 3){
        CHECK(!(s.blocks[0].flags & AP_FLAG_DISCONTINUITY_BEFORE), "block before the hole is clean");
        CHECK((s.blocks[1].flags & AP_FLAG_DISCONTINUITY_BEFORE) && (s.blocks[1].flags & AP_FLAG_UNANCHORED), "block after the hole is flagged and unanchored");
        CHECK(!(s.blocks[2].flags & (AP_FLAG_DISCONTINUITY_BEFORE|AP_FLAG_UNANCHORED)) && s.blocks[2].anchor_counter_ext == 8 && s.blocks[2].pts_num == 8ull * AP_TICKS_PER_UNIT, "re-anchored at the next resync, at that unit's video time");
    }
    CHECK(st.discontinuities == 1 && st.records_hole == 1 && s.frames == 5, "one discontinuity, conservation 5");
    CHECK(!ap_lookup(p, 1, 7, &lp, &lo) || 1, "lookup(7) may or may not survive (history) - not asserted");

    // 4: counter gaps: extended jump (20 -> 22) and a parser-flagged discontinuity; PCM stays contiguous, no re-anchor
    ap_close(p); memset(&s, 0, sizeof s); CHECK(ap_open(&p, 64, &sink) == 0, "reopen 4");
    ord = 0;
    { unit_audio_observation o = resync(1, ord, 20, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 4, 1);
    { unit_audio_observation o = resync(1, ord, 22, 0); ap_on_audio(p, &o); }              // jumped
    feed_pcm(p, 1, &ord, 4, 2);
    { unit_audio_observation o = resync(1, ord, 23, UNIT_FLAG_COUNTER_DISCONTINUITY); ap_on_audio(p, &o); }   // parser-flagged
    feed_pcm(p, 1, &ord, 4, 3);
    ap_flush(p); ap_get_stats(p, &st);
    CHECK(s.n == 3 && s.frames == 12, "gap case: 3 blocks, 12 frames");
    if (s.n == 3){
        CHECK(s.blocks[1].flags & AP_FLAG_COUNTER_GAP, "extended counter jump flags the next block");
        CHECK(s.blocks[2].flags & AP_FLAG_COUNTER_GAP, "parser-flagged discontinuity flags the next block");
        CHECK(s.blocks[1].pts_num == s.blocks[0].pts_num + 4 * 5 && s.blocks[2].pts_num == s.blocks[1].pts_num + 4 * 5, "PCM timing stays contiguous across counter gaps");
        CHECK(s.blocks[1].anchor_counter_ext == 20, "no re-anchor on a counter gap");
        CHECK(s.blocks[1].correlation_residual == 2 * 8008 - 4 * 5, "residual shows the jump (%lld)", (long long)s.blocks[1].correlation_residual);
    }
    CHECK(st.counter_gaps == 2, "two counter gaps counted, got %llu", (unsigned long long)st.counter_gaps);

    // 5: buffer fill -> PARTIAL blocks with contiguous pts; then epoch change flags discontinuity
    ap_close(p); memset(&s, 0, sizeof s); CHECK(ap_open(&p, 4, &sink) == 0, "reopen 5");
    ord = 0;
    { unit_audio_observation o = resync(1, ord, 0, 0); ap_on_audio(p, &o); }
    feed_pcm(p, 1, &ord, 10, 9);
    { unit_audio_observation o = pcm(2, 0, 9); ap_on_audio(p, &o); }   // new epoch
    ap_flush(p); ap_get_stats(p, &st);
    CHECK(s.frames == 11, "partial case conservation: %llu", (unsigned long long)s.frames);
    CHECK(st.blocks_partial == 2, "two full-buffer partial blocks, partial=%llu", (unsigned long long)st.blocks_partial);
    if (s.n >= 4){
        CHECK((s.blocks[0].flags & AP_FLAG_PARTIAL) && (s.blocks[1].flags & AP_FLAG_PARTIAL), "first two blocks partial");
        CHECK(s.blocks[1].pts_num == 4 * 5 && s.blocks[2].pts_num == 8 * 5, "partial blocks keep contiguous pts");
        CHECK((s.blocks[3].flags & AP_FLAG_DISCONTINUITY_BEFORE) && s.blocks[3].epoch == 2 && (s.blocks[3].flags & AP_FLAG_UNANCHORED), "epoch change flagged and unanchored");
    }
    ap_close(p);

    // 6: seqlock stress — concurrent lookups never observe a torn entry
    memset(&s, 0, sizeof s); CHECK(ap_open(&p, 4096, &sink) == 0, "reopen 6");
    stressctx sc; memset(&sc, 0, sizeof sc); sc.p = p;
    pthread_t rd; pthread_create(&rd, NULL, stress_reader, &sc);
    ord = 0;   // one anchored run (first resync at counter 0, ordinal 0): every entry must satisfy pts == ordinal * 5
    for (int round = 0; round < 2000; round++)
        for (uint64_t c = 0; c < 200; c++){ unit_audio_observation o = resync(1, ord, c, 0); ap_on_audio(p, &o); ord += 1601; }
    atomic_store(&sc.stop, 1); pthread_join(rd, NULL);
    CHECK(atomic_load(&sc.hits) > 0, "stress reader never hit an entry (%ld lookups)", atomic_load(&sc.lookups));
    CHECK(atomic_load(&sc.torn) == 0, "seqlock let %ld torn entries through (%ld hits)", atomic_load(&sc.torn), atomic_load(&sc.hits));
    ap_close(p);
    if (fails) printf("FAILURES: %d\n", fails); else printf("audio_publisher tests: PASS\n");
    return fails ? 1 : 0;
}
