// frameserver — P3 assembly (design doc §8, §11 P3, field_registration/TRAJECTORY.md).
//
//   capture_core (device or replay) --on_packet--> unit_parser --on_video--> [pool slot + SPSC ring]
//     --> processing worker: signal_state_classify -> registration actions -> fieldreg_process
//         -> signal_state_note_registration -> frame_publisher -> decision-log row
//
// Policy implemented here is the contract's LOW-LATENCY LIVE policy: every fixed-raster unit is
// published immediately with the engine's per-unit applied phase (provisional; marked unsettled
// when the classifier says so), and the sidecar records enough for an archival re-render. The
// gated trajectory redesign (delayed/corrected policy) plugs in behind the same log schema later.
//
// Threading: the parser runs on capture_core's delivery thread and only copies an eligible unit
// into a free pool slot and pushes an item onto the SPSC ring; if no slot is free the unit is
// DROPPED and counted — never blocked (§8 property 7) — but its observation still reaches the
// worker and the sidecar (drop_reason=PoolFull), so a later re-render sees a marked hole, never an
// unmarked one. The worker does all analysis and I/O. Lifecycle: open -> start -> stop -> close;
// fs_stop is idempotent and fs_close performs it if the caller did not.
// No per-unit allocation anywhere: pool, engine, classifier and parser are allocated at open.
#ifndef FRAMESERVER_H
#define FRAMESERVER_H
#include <stdint.h>
#include <stddef.h>
#include "../capture_core/capture_core.h"
#include "frame_publisher.h"
#include "audio_publisher.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct frameserver frameserver;

#define FS_DECISION_LOG_SCHEMA 3

typedef struct {
    cc_config capture;          // device input or replay_path
    unsigned pool_units;        // unit slots between delivery thread and worker (0 => 16)
    unsigned surface_pool;      // IOSurface pool for the publisher (0 => 6)
    const char *decision_log;   // schema FS_DECISION_LOG_SCHEMA CSV, or NULL. The current P3
                                // schema records decisions/baselines and loss; full raw evidence
                                // vectors remain an explicit later-P3 extension.
    fp_sink sink;               // consumer of published frames (may be {NULL,NULL} => count only)
    ap_sink audio_sink;         // consumer of PCM blocks on the device timebase ({NULL,NULL} => count only)
    unsigned audio_block_frames; // audio publisher block buffer (0 => 4096 stereo frames, > 2 units)
    unsigned audio_queue_blocks; // bounded queue between the publisher and the sink (0 => 32 blocks, ~1 s)
    void (*on_end)(void *ctx, enum cc_end reason);   // optional; fires once BOTH the video and audio workers have drained
                                                     // (no media callback of either kind follows it); never call fs_stop/fs_close from any callback
    void *end_ctx;
} fs_config;

// Audio: every PCM record the parser emits is published through audio_publisher as bounded
// blocks with sample-contiguous device-timebase pts (see audio_publisher.h). The publisher runs
// on the capture delivery thread; its blocks are COPIED into a bounded preallocated queue and
// handed to the user's audio sink by a dedicated audio worker (never the video worker, never
// the delivery thread), so a slow or blocking consumer can only cause an explicit downstream
// drop (audio_dropped_blocks, and AP_FLAG_DISCONTINUITY_BEFORE on the next delivered block) —
// never upstream HostLoss (§8 properties 7 and 10). Video frames carry the audio-clock time of
// their unit (fp_frame.audio_pts_*) when the unit's resync has been seen, for audio-as-master
// consumers.

typedef struct {
    uint64_t video_observations, exact_units, short_units, holes, unframed, other_format, no_signal_0800;
    uint64_t audio_records, audio_resync;
    uint64_t audio_pcm_records, audio_blocks, audio_frames_published, audio_discontinuities, audio_blocks_unanchored;
    uint64_t audio_counter_gaps; int64_t audio_residual_min, audio_residual_max;   // A/V correlation provenance
    uint64_t audio_blocks_delivered, audio_frames_delivered, audio_dropped_blocks, audio_dropped_frames;   // sink side
    uint64_t audio_master_frames;     // video frames published with a known audio-clock pts
    // Invariants after fs_stop: audio_frames_published == audio_pcm_records (publisher never invents/drops);
    //   audio_frames_delivered + audio_dropped_frames == audio_frames_published (queue accounts every block).
    uint64_t eligible_observations;   // fixed-raster-eligible units seen at ingress (the denominator)
    uint64_t published, dropped_pool_full, dropped_ring_full, publisher_dropped, ring_drops_logged;
    uint64_t eligible_ring_drops, ring_gap_rows;
    // dropped_pool_full: eligible unit, no free slot -> bytes shed, observation still logged (drop_reason=PoolFull).
    // dropped_ring_full: item ring full -> observation never reaches the worker; counted, and folded
    //   into the next sidecar row's preceding_ring_drops column. Tail loss gets one synthetic
    //   RingFullTail row, so every missing range remains chronologically locatable.
    // Invariants: published + dropped_pool_full + publisher_dropped == exact_units;
    //             exact_units + eligible ring drops == eligible_observations.
    uint64_t unsettled_units, begin_segment_calls, discontinuity_calls;
    uint64_t log_rows;
    unsigned pool_high_water;
} fs_stats;

int  fs_open (frameserver **out, const fs_config *cfg);
int  fs_start(frameserver *f);
int  fs_stop (frameserver *f);            // stops capture, drains the worker, closes the log
// Authoritative after fs_stop. During streaming worker-owned members are diagnostic only and
// may be momentarily inconsistent; atomic ingress counters remain individually safe.
void fs_get_stats(const frameserver *f, fs_stats *out);
void fs_close(frameserver *f);

#ifdef __cplusplus
}
#endif
#endif
