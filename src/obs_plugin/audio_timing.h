#ifndef SHUTTLE_AUDIO_TIMING_H
#define SHUTTLE_AUDIO_TIMING_H
#include "../frameserver/audio_publisher.h"

/* Audio is the clock.
 *
 * The device's unit counter is not time. It steps once per unit, and a unit is a full frame only while the device
 * holds a full frame: a deck in search sends one short field per unit (the counter ran 5,197 units in 41 s of
 * fast-forward, 2026-10-02), a stopped deck's no-signal units carry about one sample more than a frame's worth,
 * and the short units at play start are short in time, not short of samples. Timing video from the counter and
 * filling every shortfall of audio against it with silence put minutes of silence into OBS during a wind, and
 * the audio that followed arrived late until something reset it.
 *
 * Samples are real time whatever the counter does. So audio blocks go out on the publisher's sample-contiguous
 * timeline untouched, and a video frame takes the audio-clock time of its own unit (fp_frame.audio_pts_num).
 * Nothing is inserted or dropped here. */

typedef struct { int have; uint64_t last; } shuttle_video_clock;

/* A video frame's time in audio-clock ticks (1/AP_PTS_DEN s): its unit's audio-clock time when known. When it
 * is not known (no resync for that unit yet), the previous frame's time plus `nominal` ticks, or `first` for
 * the first frame of a session; *estimated is set. Times never go back: a known time at or before the previous
 * frame's (after an estimate ran ahead) is placed one tick after it. */
static inline uint64_t shuttle_video_time(shuttle_video_clock *c, int known, uint64_t audio_ticks,
                                          uint64_t nominal, uint64_t first, int *estimated) {
    uint64_t t = known ? audio_ticks : c->have ? c->last + nominal : first;
    if (estimated) *estimated = !known;
    if (c->have && t <= c->last) t = c->last + 1;
    c->have = 1; c->last = t;
    return t;
}

/* An audio block's time: the publisher's, as it is. -1: not yet placed on the timeline (no resync in this run),
 * do not publish. Counts, for the log only, the blocks whose correlation residual stepped by more than two
 * samples from the block before: the places the old policy would have inserted or dropped audio. */
typedef struct { int have; int64_t last_residual; uint64_t residual_steps; } shuttle_audio_clock;
static inline int shuttle_audio_time(shuttle_audio_clock *s, const ap_block *b, uint64_t *ticks) {
    if (b->flags & AP_FLAG_DISCONTINUITY_BEFORE) s->have = 0;
    if (b->flags & AP_FLAG_UNANCHORED) return -1;
    if (s->have) { int64_t d = b->correlation_residual - s->last_residual; if (d > 10 || d < -10) s->residual_steps++; }
    s->have = 1; s->last_residual = b->correlation_residual;
    *ticks = b->pts_num;
    return 0;
}
#endif
