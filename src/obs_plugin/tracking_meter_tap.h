// Live tap for the tracking meter. The frame callback offers each published frame; while the meter
// window is open, one frame in TMT_EVERY is copied into the tap (if the measuring thread has taken
// the previous one) and measured on the tap's own thread. Nothing is copied or measured while the
// window is closed. The window reads a snapshot. One tap per process (the plugin allows one source).
#ifndef TRACKING_METER_TAP_H
#define TRACKING_METER_TAP_H
#include <stddef.h>
#include <stdint.h>
#include "tracking_meter.h"

#define TMT_EVERY 4                     // measure one published frame in 4 (about 7.5 a second)
#define TMT_HISTORY 240                 // half-second history points: two minutes

typedef struct {
    int      active;                    // the window is open and measuring
    int      fresh;                     // a frame arrived within the last 1.5 s
    uint64_t frames_offered, frames_measured, frames_skipped_busy, frames_no_reading;
    tm_reading now;                     // the running reading (median of the last TM_WINDOW measured frames)
    unsigned history_n;                 // valid points in history, oldest first
    double   history[TMT_HISTORY][TM_CHANNELS];   // ratio field 2 / field 1 per point (0: no reading)
} tmt_snapshot;

void tmt_start(void);                   // window opened: start measuring (idempotent)
void tmt_stop(void);                    // window closed: stop and join the thread (idempotent)
// From the frame callback, with the surface locked: cheap when inactive or busy.
void tmt_offer(const uint8_t *uyvy, size_t bytes_per_row);
// Called on the UI's own cadence; also advances the history by one point.
void tmt_snapshot_take(tmt_snapshot *out);

#endif
