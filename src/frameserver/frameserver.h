// frameserver — assembly (design doc §8, §11 P3, docs/geometry_engine.md).
//
//   capture_core (device or replay) --on_packet--> unit_parser --on_video--> [pool slot + SPSC ring]
//     --> processing worker: signal_state_classify -> geometry_engine
//         -> frame_publisher -> decision-log row
//
// Approved v11 is the default for tools and OBS. Aligned fields publish immediately;
// reversed pairing delays one unit to finish its own-field offsets.
// This is a transport-unit publisher, not a temporal field re-pairer. Consumers of
// reversed-pair material must pair next-unit field 1 over current-unit field 2,
// as geometry_render.py --pair-next does. Decision rows remain unit-keyed.
//
// Threading: the parser runs on capture_core's delivery thread, snapshots bounded audio
// correlation evidence for the log, and copies an eligible unit
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
#include "../field_registration/geometry_engine.h"
#include "../signal_state/signal_state.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct frameserver frameserver;

#define FS_GEOMETRY_LOG_SCHEMA 28
#define FS_HRETIME_LOG_SCHEMA 36

typedef struct {
    cc_config capture;          // device input or replay_path
    unsigned pool_units;        // unit slots between delivery thread and worker (0 => as many as the capture ring holds: 355 at 256 MB)
    unsigned surface_pool;      // IOSurface pool for the publisher (0 => 6)
    const char *decision_log;   // schema 28 CSV (35 with hretime), or NULL;
                                // opened exclusively (must not exist).
    fp_sink sink;               // consumer of published frames (may be {NULL,NULL} => count only)
    ap_sink audio_sink;         // consumer of PCM blocks on the device timebase ({NULL,NULL} => count only)
    unsigned audio_block_frames; // audio publisher block buffer (0 => 4096 stereo frames, > 2 units)
    unsigned audio_queue_blocks; // bounded queue between the publisher and the sink (0 => 32 blocks, ~1 s)
    void (*on_end)(void *ctx, enum cc_end reason);   // optional; fires once BOTH the video and audio workers have drained
                                                     // (no media callback of either kind follows it); never call fs_stop/fs_close from any callback
    void *end_ctx;
    /* Reversed pairing buffers one source unit, not an unbounded lookahead. Published units retain
     * their own fields; downstream weaving must use the same pairing parameter. */
    const ge_config *geometry_config; /* NULL: approved defaults; copied by fs_open */
    const signal_state_config *signal_config; /* NULL: classifier defaults; copied by fs_open */
    int geometry_pair_next;
    const char *pairing_schedule; // CSV snapshot loaded by fs_open;
                                 // excludes geometry_pair_next. First row starts at 0.
    int hretime;               // default 0; post-placement horizontal repair only
    int registration_off;      // default 0; 1 publishes every field at the nominal (0,0) placement.
                               // The engine still runs and logs its evaluation; applied/frame offsets
                               // in the sidecar are the published 0. H-retiming uses that placement.
} fs_config;

// Audio: every PCM record the parser emits is published through audio_publisher as bounded
// blocks with sample-contiguous device-timebase pts (see audio_publisher.h). The publisher runs
// on the capture delivery thread; its blocks are COPIED into a bounded preallocated queue and
// handed to the user's audio sink by a dedicated audio worker (never the video worker, never
// the delivery thread), so a slow or blocking consumer can only cause an explicit downstream
// drop (audio_dropped_blocks, and AP_FLAG_DROPPED_BEFORE on the next delivered block) —
// never upstream HostLoss (§8 properties 7 and 10). Video frames carry the audio-clock time of
// their unit (fp_frame.audio_pts_*) when the unit's resync has been seen, for audio-as-master
// consumers.
// Decision-log audio evidence has a deterministic input-order cutoff: the parser's
// video-unit callback. The same delivery thread owns audio correlation writes;
// the snapshot travels with the unit through the bounded queue/reversed pairing.
// A resync not yet observed at that cutoff (or outside the correlation history)
// produces empty audio-evidence cells, even if it arrives before publication.
// No video is deferred and no thread waits for audio. Live audio_pts_known/num
// retain their separate, publication-time best-effort lookup semantics.

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
    uint64_t log_rows;                // cumulative over every attached log file
    uint64_t log_files;               // decision-log files opened (cfg.decision_log + fs_log_start)
    uint64_t log_write_errors;        // rows whose fprintf failed (NOT counted in log_rows): the sidecar is incomplete
    uint64_t log_close_errors;        // fclose failures at detach/stop: the tail of that file may be missing
    uint64_t log_last_file_errors;    // write+close errors of the most recently CLOSED log file (fs_log_stop or fs_stop): 0 => that file is complete
    unsigned pool_high_water;
    unsigned pool_units;        // slots actually allocated (after defaulting)
} fs_stats;

int  fs_open (frameserver **out, const fs_config *cfg);
int  fs_start(frameserver *f);
int  fs_stop (frameserver *f);            // stops capture, drains the worker, closes the log
// Runtime decision-log attachment, for a recorder that aligns the sidecar to its own recording
// rather than to the session: rows are written only while a log is attached; the first row after
// fs_log_start is the first unit the worker processed after the call (it anchors the recording on
// the device clock via counter_extended). Same schema and header as cfg.decision_log. One log at
// a time. For v11 reversed pairing this means the first COMPLETED decision after
// attachment; its source unit may have arrived one unit earlier.
// Start fails (-1) while one is attached (including cfg.decision_log) — stop it first.
// Refused from the worker/audio callbacks and after stop. fs_stop closes an attached log.
// The path must not exist (opened exclusively: a sidecar is evidence and is never truncated).
// Control-thread ownership: fs_open/start/stop/close and fs_log_start/stop are serialized
// against each other internally (life_m/log_m), but the sidecar's PATH policy is the caller's —
// a growing file must not live in a cloud-synced root (CLAUDE.md writer output rule).
// Rows reach the disk on a writer thread (async_file.h): the video worker only copies a finished
// row into a 32 MiB ring, so a stalled disk never delays delivery (disk-hang test). Measured before
// this, 2026-09-28: row writes of 280-943 ms under fsync'd disk load, each a late frame handoff. A
// ring overflow or a failed write makes the file incomplete (every later row fails, fs_log_stop
// returns -1), never silently thinner. fs_log_stop drains the ring and fsyncs, so it can block.
int  fs_log_start(frameserver *f, const char *path);
int  fs_log_stop (frameserver *f);        // -1 if none attached, the close failed, or any row write failed in this file (it is then incomplete: do not publish it as complete)
// Runtime raw-transport tee: every packet, loss and error record the capture core delivers is
// also written to `path` as a .tpc (the shuttle-capture format), through cc_async_sink: the
// capture delivery thread only copies into a bounded ring (ring_bytes) and a writer thread
// writes in <=1 MiB pieces, so a stalled destination never blocks acquisition -- it loses tee
// packets instead, confessed as exact HostLoss records in the file. The file is created
// exclusively and grows at its final path (owner, 2026-09-28: a LucidLink volume takes growing
// files). The first records are mid-unit: a tee starts wherever the stream is. One at a time.
int  fs_tee_start(frameserver *f, const char *path, const char *session_note, size_t ring_bytes);
// Detach and hand the writer back; the caller closes it (cc_async_sink_close drains and may
// block). NULL if none. fs_stop closes a still-attached tee itself.
cc_async_sink *fs_tee_detach(frameserver *f);
// Video-worker time accounting between consecutive frame handoffs (ns, CLOCK_UPTIME_RAW), to
// attribute a late handoff: did the unit arrive late (idle), wait behind a busy worker
// (queue_wait), or did a stage stall? Covers the time since the previous handoff returned, so the
// previous unit's sidecar row write counts here. Valid only on the worker thread, i.e. called
// from inside the frame sink; values are the worker's own, never shared.
typedef struct {
    uint64_t since_prev_ns;   // since the previous handoff returned
    uint64_t idle_ns;         // worker waiting on an empty input queue
    uint64_t queue_wait_ns;   // this unit: parser enqueue -> worker pickup
    uint64_t classify_ns, geometry_ns, hretime_ns, log_ns, other_ns;
    uint32_t items;           // input items processed since the previous handoff
} fs_handoff_timing;
void fs_handoff_timing_get(const frameserver *f, fs_handoff_timing *out);
// Authoritative after fs_stop. During streaming worker-owned members are diagnostic only and
// may be momentarily inconsistent; atomic ingress counters remain individually safe.
void fs_get_stats(const frameserver *f, fs_stats *out);
// The capture core's completed packet deliveries (both endpoints, including empty packets).
// Race-free while streaming; independent of whether the parser emits an observation.
uint64_t fs_packets_delivered(const frameserver *f);
void fs_close(frameserver *f);

#ifdef __cplusplus
}
#endif
#endif
