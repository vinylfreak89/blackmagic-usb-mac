// replay_timeline — a replayed .tpc as a timeline for OBS's media controls: unit index (units since
// the first complete unit) <-> milliseconds <-> file byte offset, and a device counter observed in
// playback resolved to its unit index. Pure arithmetic; the span comes from fs_replay_probe.
//
// Byte offsets are proportional: the stream's byte rate is set by the device (every unit carries
// the same video and audio payload and tags), so unit u sits near u * file_bytes / units. Seeking
// lands within a few units of the target; the time shown afterwards comes from the counters of the
// frames actually played, never from the byte estimate.
#ifndef REPLAY_TIMELINE_H
#define REPLAY_TIMELINE_H
#include <stdint.h>

/* File bytes per unit on the tape-1 S-Video NTSC capture: 131,298,574,971 B over 162,634 units.
 * Used only to choose how many times the 16-bit counter wrapped between the file's first and last
 * unit, where it is off by half a wrap (32,768 units, ~26 GB) before it picks wrongly. */
#define RT_NOMINAL_UNIT_BYTES 807324.0

typedef struct {
    uint64_t file_bytes, units;   /* units: index of the last complete unit (0 = unknown) */
    uint16_t first16;             /* counter of unit 0 */
} rt_timeline;

static inline int rt_init(rt_timeline *t, uint64_t file_bytes, uint16_t first16, uint16_t last16){
    t->file_bytes = file_bytes; t->first16 = first16; t->units = 0;
    uint64_t base = (uint16_t)(last16 - first16);
    double est = (double)file_bytes / RT_NOMINAL_UNIT_BYTES;
    double k = (est - (double)base) / 65536.0;
    uint64_t wraps = k > 0 ? (uint64_t)(k + 0.5) : 0;
    t->units = base + 65536u * wraps;
    return t->units ? 0 : -1;
}
/* NTSC unit period 1001/30000 s: ms = u * 1001 / 30. */
static inline int64_t rt_ms(uint64_t u){ return (int64_t)(u * 1001u / 30u); }
static inline uint64_t rt_unit_at_ms(const rt_timeline *t, int64_t ms){
    if (ms <= 0) return 0;
    uint64_t u = (uint64_t)ms * 30u / 1001u;
    return u > t->units ? t->units : u;
}
static inline uint64_t rt_offset(const rt_timeline *t, uint64_t u){
    return t->units ? (uint64_t)((double)u / (double)t->units * (double)t->file_bytes) : 0;
}
/* The unit index of counter c16 observed near unit `expect`: the nearest index with that counter. */
static inline uint64_t rt_resolve(const rt_timeline *t, uint16_t c16, int64_t expect){
    uint16_t at = (uint16_t)(t->first16 + (uint64_t)(expect < 0 ? 0 : expect));
    int64_t u = expect + (int16_t)(uint16_t)(c16 - at);
    return u < 0 ? 0 : (uint64_t)u;
}
#endif
