// replay_timeline — a replayed .tpc as a timeline for OBS's media controls: unit index (units since
// the first complete unit) <-> milliseconds <-> file byte offset, and a device counter observed in
// playback resolved to its unit index. Pure arithmetic; the span comes from fs_replay_probe.
//
// Byte offsets are proportional: the stream's byte rate is set by the device (every unit carries
// the same video and audio payload and tags), so unit u sits near byte_lo + u * (byte_hi - byte_lo) /
// units, between the first and last picture units' offsets (a file that ends with the deck stopped
// carries no-signal bytes past the last unit; spread over the whole file they pulled every seek
// early, by 0.9% of the position on 2026-11-26 17-14-15's 22 s tail). Seeking
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
    uint64_t byte_lo, byte_hi;    /* file offsets of unit 0 and unit `units`; byte_hi <= byte_lo: the whole file */
} rt_timeline;
/* A frame's counter further than this from where the frame count puts it is not believed, and the frame
 * count is the better position. (What used to put counters far off was the no-signal units' own numbering
 * leaking into the unit counter; picture units now follow the device counter on the audio resyncs, which
 * has not been seen to restart.) */
#define RT_RESOLVE_SLACK 900      /* units, 30 s */
/* Counters are 16-bit. The file's first and last unit headers are read raw here, so a file that begins or
 * ends in no-signal units (numbered on their own, not on the device counter) shifts the span by the
 * difference between the two numberings, and nothing here can tell. The size does not
 * decide it either: the wrap count comes from the size, so the span always lies within half a wrap of
 * the size estimate, and captures with host loss carry fewer bytes per unit. So the length can be off
 * by a counter restart's jump; the shown time cannot run past it (rt_resolve clamps and, beyond the
 * slack, follows the frame count). NTSC only: other modes need their own nominal rate (P6). */

/* The span's units spread over [byte_lo, byte_hi] (fs_replay_probe's first/last offsets); the wrap count is chosen
 * from those bytes too, not the file's. byte_hi <= byte_lo: the whole file (rt_init). */
static inline int rt_init_span(rt_timeline *t, uint64_t file_bytes, uint64_t byte_lo, uint64_t byte_hi, uint16_t first16, uint16_t last16){
    t->file_bytes = file_bytes; t->first16 = first16; t->units = 0;
    if (byte_hi <= byte_lo || byte_hi > file_bytes){ byte_lo = 0; byte_hi = file_bytes; }
    t->byte_lo = byte_lo; t->byte_hi = byte_hi;
    uint64_t base = (uint16_t)(last16 - first16);
    double est = (double)(byte_hi - byte_lo) / RT_NOMINAL_UNIT_BYTES;
    double k = (est - (double)base) / 65536.0;
    uint64_t wraps = k > 0 ? (uint64_t)(k + 0.5) : 0;
    t->units = base + 65536u * wraps;
    return t->units ? 0 : -1;
}
static inline int rt_init(rt_timeline *t, uint64_t file_bytes, uint16_t first16, uint16_t last16){
    return rt_init_span(t, file_bytes, 0, file_bytes, first16, last16);
}
/* NTSC unit period 1001/30000 s: ms = u * 1001 / 30. */
static inline int64_t rt_ms(uint64_t u){ return (int64_t)(u * 1001u / 30u); }
/* The first unit shown at or after ms: the inverse of rt_ms, so rt_unit_at_ms(rt_ms(u)) == u. */
static inline uint64_t rt_unit_at_ms(const rt_timeline *t, int64_t ms){
    if (ms <= 0) return 0;
    uint64_t u = ((uint64_t)ms * 30u + 1000u) / 1001u;
    return u > t->units ? t->units : u;
}
static inline uint64_t rt_offset(const rt_timeline *t, uint64_t u){
    uint64_t lo = t->byte_hi > t->byte_lo ? t->byte_lo : 0, hi = t->byte_hi > t->byte_lo ? t->byte_hi : t->file_bytes;
    return t->units ? lo + (uint64_t)((double)u / (double)t->units * (double)(hi - lo)) : 0;
}
/* The unit index of counter c16 observed near unit `expect`: the nearest index with that counter,
 * unless that is more than RT_RESOLVE_SLACK away (then `expect`); always within [0, units]. */
static inline uint64_t rt_resolve(const rt_timeline *t, uint16_t c16, int64_t expect){
    if (expect < 0) expect = 0;
    int d = (int16_t)(uint16_t)(c16 - (uint16_t)(t->first16 + (uint64_t)expect));
    int64_t u = d > RT_RESOLVE_SLACK || d < -RT_RESOLVE_SLACK ? expect : expect + d;
    if (u < 0) u = 0;
    return (uint64_t)u > t->units ? t->units : (uint64_t)u;
}
#endif
