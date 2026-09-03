// audio_publisher — turns the unit parser's per-record audio observations into bounded PCM
// blocks with SAMPLE-CONTIGUOUS timestamps on the device timebase, plus the audio<->video
// correlation each resync record establishes. Design doc §9 (audio as continuity master), §11 P3.
//
// Timebase (audio as master). Every delivered stereo frame advances time by exactly 1/48000 s.
// A run of contiguous frames is placed on the video timebase ONCE, at the first
// DeckLinkAudioResyncT record after the run began: that record carries the unit counter c whose
// video time is c * 1001/30000 s, and the frame ordinal o at that instant, so
//   pts(ordinal n) = c * 8008 + (n - o) * 5     ticks of 1/240000 s   (lcm of 30000 and 48000)
// and every later frame of the run is pts(previous) + 5. Later resyncs do NOT move the anchor;
// each one yields a signed CORRELATION RESIDUAL = c' * 8008 - pts(o') — the measured offset
// between the device's audio and video clocks (the tape-scale number is ~36 ppm, i.e. a fraction
// of a sample per unit, accumulating). The residual is reported, never applied: applying it would
// manufacture ±0.6-sample gaps at every unit boundary. A consumer that wants video locked to the
// audio clock uses ap_lookup: for a video unit counter it returns the audio pts of that unit's
// resync, so video timestamps can be derived from the audio clock (P4a decision).
//
// Blocks. Frames accumulate in a caller-sized buffer; a block is emitted at every resync (one per
// video unit, ~1601/1602 frames), when the buffer fills (PARTIAL), and at flush. Discontinuities
// (parser hole / unframed / epoch change) end the run: the buffered frames go out, the next block
// is flagged DISCONTINUITY_BEFORE, and timing is UNANCHORED (ordinal-only pts) until the next
// resync re-establishes correlation — ordinal continuity across missing audio bytes cannot locate
// them in physical time. A resync whose counter did not advance by exactly 1 (or that the parser
// flagged as a counter discontinuity) flags the next block COUNTER_GAP: the PCM is still
// continuous; it is the A/V correlation that jumped. Frames are never invented, resampled or
// dropped here; frames_published == PCM records, always.
//
// Threading. ap_* runs on the thread that delivers the parser's on_audio (capture_core's
// delivery thread). The block sink is called synchronously there and must be O(copy) — the
// frameserver puts a bounded queue + audio worker between this and any external consumer
// (§8 property 10). ap_lookup is safe from any other thread (single writer, seqlock).
// No allocation after ap_open.
#ifndef AUDIO_PUBLISHER_H
#define AUDIO_PUBLISHER_H
#include <stdint.h>
#include <stddef.h>
#include <stdatomic.h>
#include "../unit_parser/unit_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

#define AP_PTS_DEN 240000u          // lcm(30000, 48000): one unit = 8008 ticks, one frame = 5 ticks
#define AP_TICKS_PER_UNIT 8008u
#define AP_TICKS_PER_FRAME 5u
#define AP_BYTES_PER_FRAME 6u        // two active channels, S24LE each, as on the wire
#define AP_SAMPLE_RATE 48000u
#define AP_CHANNELS 2u
#define AP_LOOKUP_ENTRIES 256u       // resync correlation history: must exceed the video pool depth the worker may lag by

enum ap_flags {
    AP_FLAG_DISCONTINUITY_BEFORE = 1u << 0,  // a hole/unframed/epoch change preceded this block
    AP_FLAG_PARTIAL              = 1u << 1,  // buffer filled before the unit's resync arrived
    AP_FLAG_UNANCHORED           = 1u << 2,  // no resync yet in this run: pts is ordinal-only
    AP_FLAG_COUNTER_GAP          = 1u << 3,  // the last resync's counter was not previous + 1
};

typedef struct {
    uint64_t pts_num;              // block start, in 1/AP_PTS_DEN s (device timebase, or ordinal-only if UNANCHORED)
    uint32_t pts_den;              // == AP_PTS_DEN
    uint64_t epoch;                // parser epoch these samples belong to
    uint64_t sample_ordinal;       // cumulative stereo-frame ordinal of the first frame
    uint64_t anchor_counter_ext;   // resync counter that anchored this run (valid unless UNANCHORED)
    uint64_t last_resync_counter_ext; // most recent resync counter seen before this block (0 if none)
    int64_t  correlation_residual; // ticks: last resync's video time minus audio pts at that instant
    uint32_t n_frames;             // stereo frames in this block
    const uint8_t *s24le;          // n_frames * AP_BYTES_PER_FRAME bytes: ch0 S24LE, ch1 S24LE
    uint32_t sample_rate, channels;// AP_SAMPLE_RATE, AP_CHANNELS (explicit for future formats)
    uint32_t flags;                // enum ap_flags
} ap_block;

typedef struct {
    // Synchronous, on the delivery thread; the buffer is valid only during the call (copy it).
    void (*on_block)(void *ctx, const ap_block *block);
    void *ctx;
} ap_sink;

typedef struct {
    uint64_t records_pcm, records_resync, records_hole, records_unframed;
    uint64_t blocks, frames_published, blocks_partial, blocks_unanchored, discontinuities;
    uint64_t counter_gaps;         // resync counter jumps (incl. parser-flagged discontinuities)
    int64_t  residual_min, residual_max;   // ticks, over all anchored resyncs (drift envelope)
    uint64_t resyncs_anchored;     // resyncs that contributed a residual measurement
} ap_stats;

typedef struct audio_publisher audio_publisher;

// capacity_frames: block buffer (>= 2, e.g. 4096 > two units). Allocates once.
int  ap_open (audio_publisher **out, uint32_t capacity_frames, const ap_sink *sink);
void ap_on_audio(audio_publisher *p, const unit_audio_observation *obs);
// Emit whatever is buffered (end of stream). Safe to call repeatedly.
void ap_flush(audio_publisher *p);
void ap_get_stats(const audio_publisher *p, ap_stats *out);
void ap_close(audio_publisher *p);

// Audio-clock time of video unit `counter_ext`: the audio pts (ticks) at that unit's resync
// record, and the frame ordinal there. Any thread. Returns 1 if that counter's resync has been
// seen in that parser epoch (within the last AP_LOOKUP_ENTRIES resyncs) and the run was
// anchored, else 0. A terminal audio-queue drop (blocks dropped with no later block to flag) is
// reported only through after-stop stats (audio_dropped_*), not through an event.
int  ap_lookup(const audio_publisher *p, uint64_t epoch, uint64_t counter_ext, uint64_t *pts_num, uint64_t *ordinal);

#ifdef __cplusplus
}
#endif
#endif
