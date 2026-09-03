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

#ifdef __cplusplus
extern "C" {
#endif

typedef struct frameserver frameserver;

typedef struct {
    cc_config capture;          // device input or replay_path
    unsigned pool_units;        // unit slots between delivery thread and worker (0 => 64)
    unsigned surface_pool;      // IOSurface pool for the publisher (0 => 6)
    const char *decision_log;   // CSV sidecar path, or NULL
    fp_sink sink;               // consumer of published frames (may be {NULL,NULL} => count only)
    void (*on_end)(void *ctx, enum cc_end reason);   // optional; fires after the worker drains
    void *end_ctx;
} fs_config;

typedef struct {
    uint64_t video_observations, exact_units, short_units, holes, unframed, other_format, no_signal_0800;
    uint64_t audio_records, audio_resync;
    uint64_t published, dropped_pool_full, dropped_ring_full, publisher_dropped;
    // dropped_pool_full: eligible unit, no free slot -> bytes shed, observation still logged (drop_reason=PoolFull).
    // dropped_ring_full: item ring full -> observation never reaches the worker; counted only.
    uint64_t unsettled_units, begin_segment_calls, discontinuity_calls;
    uint64_t log_rows;
    unsigned pool_high_water;
} fs_stats;

int  fs_open (frameserver **out, const fs_config *cfg);
int  fs_start(frameserver *f);
int  fs_stop (frameserver *f);            // stops capture, drains the worker, closes the log
void fs_get_stats(const frameserver *f, fs_stats *out);
void fs_close(frameserver *f);

#ifdef __cplusplus
}
#endif
#endif
