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
 * be anchored without repeating the break flag. */
static inline int shuttle_audio_time(shuttle_audio_clock *s, const ap_block *b, uint64_t *ticks) {
    if (b->flags & AP_FLAG_DISCONTINUITY_BEFORE) *s = (shuttle_audio_clock){0};
    if (b->flags & AP_FLAG_UNANCHORED) return -1;
    int stepped = 0;
    if (s->have_residual) {
        int64_t delta = b->correlation_residual - s->last_residual;
        if (delta > 10 || delta < -10) { s->applied_ticks += delta; stepped = 1; }
    }
    s->last_residual = b->correlation_residual; s->have_residual = 1;
    int64_t t = (int64_t)b->pts_num + s->applied_ticks;
    *ticks = t < 0 ? 0 : (uint64_t)t;
    return stepped;
}
#endif
