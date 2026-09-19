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
typedef enum { GE_UNKNOWN, GE_NOTHING, GE_VALID_MOVE, GE_BOTTOM_ONLY,
               GE_TOP_ONLY, GE_NOT_IN_TANDEM } ge_class;
enum { GE_T1=1, GE_UNMEASURABLE=2, GE_FIELD1=4, GE_FIELD2=8, GE_CONFIRM=16 };
typedef struct { int shift, decided; double margin; } ge_comb_result;
typedef struct {
    int first[2], last[2], bottom[2], rule_first, auto_first, plain23;
    double blank[2], runin;
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
    ge_class motion[2];
} ge_decision;
typedef struct geometry_engine geometry_engine;
size_t ge_size(void);
void ge_init(geometry_engine *, int pair_next, int audit_comb);
/* All input rows are contiguous 720-byte luma, independent of UYVY decoding. */
void ge_measure(const uint8_t *, ge_features *);
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
