/* v11: forward-only implementation of experiment entry 11, amendments 1–5.
 * Coordinates in decisions are NTSC lines; zero means an unavailable census.
 * Storage is caller-owned, initialized once, and bounded. No hot-path allocation.
 * Reversed pairing delays one unit; outputs still describe each unit's OWN fields.
 */
#ifndef GEOMETRY_ENGINE_H
#define GEOMETRY_ENGINE_H
#include <stddef.h>
#include <stdint.h>
#define GE_PIXELS (525u * 720u)
/* Configure once before workers start. The library never reads the environment. */
extern double ge_wave_bar; /* default .45; first step strictly greater wins */
extern int ge_wave_clamp; /* default 5; symmetric displacement from 23 / 286 */
typedef struct { int first; double step, max_step; } ge_wave_result;
typedef enum { GE_WAVE_ABSTAIN, GE_WAVE_ACCEPTED, GE_WAVE_DISCARDED } ge_wave_status;
typedef enum { GE_SOURCE_NONE, GE_SOURCE_CENSUS, GE_SOURCE_HELD, GE_SOURCE_COMB,
               GE_SOURCE_PREVIOUS, GE_SOURCE_START } ge_source;
typedef enum { GE_UNKNOWN, GE_NOTHING, GE_VALID_MOVE, GE_BOTTOM_ONLY,
               GE_TOP_ONLY, GE_NOT_IN_TANDEM } ge_class;
enum { GE_T1=1, GE_UNMEASURABLE=2, GE_FIELD1=4, GE_FIELD2=8, GE_CONFIRM=16,
       GE_BASIS_CHANGED=32 };
typedef struct {
    int shift, decided;
    double margin;
    double energies[11]; /* shift order -5..+5; valid iff margin is not NAN */
} ge_comb_result;
typedef struct {
    int first[2], last[2], bottom[2]; /* first is accepted census, zero unavailable */
    ge_wave_result wave[2]; /* immutable pre-clamp observations */
    ge_wave_status wave_status[2];
    double blank[2];
    double hblank_level[2];
    int hblank_cols[2];
    uint16_t profile[2][12][672]; /* exact eight-sample sums */
    ge_class motion[2];
} ge_features;
typedef struct {
    uint64_t counter, top_unit;
    int d1, d2, unused1, unused2, reset_before, has_frame;
    int frame_d1, frame_d2, published_d, held, comb_ran;
    unsigned triggers;
    ge_comb_result comb; /* unknown (NAN margin) unless run or audit requested */
    int first[2], last[2], bottom[2];
    double hblank_level[2]; /* this unit's own fields, also on unused boundaries */
    int hblank_cols[2];
    ge_wave_result wave[2]; /* this UNIT's raw observations, not frame-owned */
    ge_wave_status wave_status[2];
    ge_source relative_source, anchor_source; /* frame-owned publication basis */
    ge_class motion[2];
} ge_decision;
typedef struct geometry_engine geometry_engine;
size_t ge_size(void);
void ge_init(geometry_engine *, int pair_next, int audit_comb);
/* All input rows are contiguous 720-byte luma, independent of UYVY decoding. */
void ge_measure(const uint8_t *, ge_features *);
/* Raw entry-33 observation: no step returns first=0 and step=0. NTSC lines.
 * ge_measure applies the independent symmetric clamp to each raw observation. */
ge_wave_result ge_wave_scan(const uint8_t *, int field, double bar);
int ge_wave_accept(ge_wave_result, int field, int clamp);
const char *ge_wave_status_name(ge_wave_status);
const char *ge_source_name(ge_source);
ge_comb_result ge_comb(const uint8_t *top, const uint8_t *bottom);
/* Returns 0..2 completed unit decisions, in source order. Reset applies before
 * the first frame using this unit, even when that frame belongs to its predecessor.
 * Counter gaps implicitly break the pair and reset. Do not cross epochs: call break.
 */
unsigned ge_push(geometry_engine *, const uint8_t *, uint64_t counter,
                 int reset, ge_decision out[2]);
/* EOF/broken adjacency completes the unused boundary field using its own census.
 * Clears all history; preserves the two configuration flags. */
unsigned ge_break(geometry_engine *, ge_decision out[2]);
const char *ge_class_name(ge_class);
#endif
