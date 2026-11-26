// replay_probe — the span of a tagged capture (.tpc) in device unit counters, for a replay
// timeline (the OBS seek bar): the 16-bit counter of the first complete 0xe801 unit near the
// start of the file and of the last one near its end, read through the same capture_core
// replay backend and unit_parser a session uses (no second reader of the format).
#ifndef REPLAY_PROBE_H
#define REPLAY_PROBE_H
#include <stdint.h>
#include <stdatomic.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint64_t file_bytes;
    uint16_t first_counter, last_counter;   // counter16 of the first / last complete 0xe801 unit
    uint64_t first_offset, last_offset;     // file offsets of those units' starts, estimated (seek positions: a few
                                            // units either way); the timeline spreads unit positions over them
    int have_first, have_last;
    int incomplete;   // a run did not read its window (abort, read error, unskippable damage): a missing end is
                      // unknown, not absent, and worth retrying; 0 with a missing end means the search found no unit
} fs_replay_span;

// Reads from the start until the first complete unit (at most window_bytes of packets) and the last
// window_bytes of the file, to its end (0 => 32 MiB, about 1.4 s of NTSC stream). The last counter
// counts only if that run reached the end of the file. A capture that begins or ends without picture
// units (the deck stopped before the recording was: 0x0800 no-signal, e.g. 22 s at the end of
// 2026-11-26 17-14-15, ~28 s at the end of the no-input capture) is searched further: one sample of a few
// MB every window_bytes (so the probe reads ~4 MB per 1.4 s of no picture, not the stretch, beside a
// playing replay), then the window after the last empty sample is read whole for the unit itself. The
// search gives up after search_bytes (0 => 2 GiB, ~90 s): no span. Picture briefly inside the stretch
// between samples can be missed; positions only. Blocking; a network volume may take seconds. `abort`
// (optional) is polled while waiting (100 ms granularity): nonzero stops the probe early, with
// have_first/have_last reporting what was found. Returns 0 when both ends were found, -1 otherwise.
// Counters are 16-bit and the device restarts them at a counter epoch (§8 property 5): a caller that
// turns the span into a length must check it against the span's bytes.
int fs_replay_probe_ex(const char *path, uint64_t window_bytes, uint64_t search_bytes, _Atomic int *abort, fs_replay_span *out);
int fs_replay_probe(const char *path, uint64_t window_bytes, _Atomic int *abort, fs_replay_span *out);   // search_bytes 0

#ifdef __cplusplus
}
#endif
#endif
