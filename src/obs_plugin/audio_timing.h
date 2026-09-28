#ifndef SHUTTLE_AUDIO_TIMING_H
#define SHUTTLE_AUDIO_TIMING_H
#include "../frameserver/audio_publisher.h"

/* Audio-worker owned. Preserve the plugin's existing >10-tick step policy;
 * this adapter advances timestamps in ticks, not the renderer's sample grid. */
typedef struct {
    int64_t applied_ticks, last_residual;
    int have_residual;
} shuttle_audio_clock;

/* -1: unanchored, do not publish; 0: ordinary block; 1: applied a step.
 * Queue drops retain the baseline so a step in omitted blocks is still seen.
 * A real break resets BEFORE discarding an unanchored block: its successor may
 * be anchored without repeating the break flag.
 * A step is applied in whole audio frames and reported in *step_frames (may be
 * NULL): the caller delivers that many frames of silence right before this block
 * (step > 0: the device lost samples) or drops that many frames from its start
 * (step < 0), so the consumer sees contiguous audio. OBS mishandles a bare
 * timestamp jump: a 974-sample step became ~50 ms of garble, silence and
 * repeated audio, then a permanent 1,606-sample offset (2026-09-28 capture). */
static inline int shuttle_audio_time_step(shuttle_audio_clock *s, const ap_block *b, uint64_t *ticks, int64_t *step_frames) {
    if (step_frames) *step_frames = 0;
    if (b->flags & AP_FLAG_DISCONTINUITY_BEFORE) *s = (shuttle_audio_clock){0};
    if (b->flags & AP_FLAG_UNANCHORED) return -1;
    int stepped = 0;
    if (s->have_residual) {
        int64_t delta = b->correlation_residual - s->last_residual;
        if (delta > 10 || delta < -10) {
            int64_t frames = (delta + (delta > 0 ? 2 : -2)) / (int64_t)AP_TICKS_PER_FRAME;   /* nearest whole frame */
            s->applied_ticks += frames * (int64_t)AP_TICKS_PER_FRAME; stepped = 1;
            if (step_frames) *step_frames = frames;
        }
    }
    s->last_residual = b->correlation_residual; s->have_residual = 1;
    int64_t t = (int64_t)b->pts_num + s->applied_ticks;
    *ticks = t < 0 ? 0 : (uint64_t)t;
    return stepped;
}
/* Contiguous delivery of a step: frames of silence to emit right before the block (gap), and
 * frames to drop from the block's start (skip), carrying an early-audio overlap longer than the
 * block into the next ones via *pending. A gap or a break cancels a pending overlap. */
static inline void shuttle_audio_plan(int64_t step, int discontinuity, uint32_t n_frames,
                                      int64_t *pending, int64_t *gap, uint32_t *skip) {
    if (step > 0 || discontinuity) *pending = 0;
    if (step < 0) *pending += -step;
    *gap = step > 0 ? step : 0;
    *skip = (uint32_t)(*pending < (int64_t)n_frames ? *pending : (int64_t)n_frames);
    *pending -= *skip;
}
static inline int shuttle_audio_time(shuttle_audio_clock *s, const ap_block *b, uint64_t *ticks) {
    return shuttle_audio_time_step(s, b, ticks, NULL);
}
#endif
