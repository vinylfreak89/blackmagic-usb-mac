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
#define GE_FIELD_LINES 240 /* publisher aperture, not the 243-line review crop */
/* Process-wide experiment controls. Configure once before any measurement or
 * worker starts; never write concurrently with an engine call. Library code
 * does not read the environment. Defaults are margin 5, guard 3, and both
 * legacy placement steps off. Near-blank suppression defaults disabled. The
 * old search arm is explicitly (0,0,1,1), with suppression still disabled. */
extern double ge_top_margin; /* 5.0; finite values only */
extern int ge_top_guard; /* default 3; 0: lag correlation, 1: none, 2: high-spread chunks,
                         * 3: all-row chunks, 4: all-row structure ratio */
extern int ge_top_plain23; /* default 0; 1: apply plain23 re-search; 0: evidence only */
extern int ge_top_runin; /* default 0; 1: apply run-in step; 0: evidence only */
extern double ge_top_near_blank; /* -1: disabled; finite >=0: inclusive p95-level cutoff */
extern int ge_top_overrun_veto; /* default 0; 1: reject non-gaining census moves increasing overrun */
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
    int first[2], last[2], bottom[2], rule_first, auto_first, plain23;
    int interpreted_first[2], top_ignored[2]; /* first[] remains measured */
    int top_overrun_veto[2]; /* predicate matched; equal tops can be a no-op */
    double top_distance[2]; /* measured final-top body p95 - hblank_level; NAN if absent */
    double blank[2], runin;
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
    int interpreted_first[2], top_ignored[2]; /* same FRAME fields as first[] */
    int top_overrun_veto[2]; /* same FRAME fields */
    double top_distance[2]; /* same FRAME fields; not unit-owned hblank provenance */
    double hblank_level[2]; /* this unit's own fields, also on unused boundaries */
    int hblank_cols[2];
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
/* Latest pushed unit's own evidence/interpretation, including reversed boundaries.
 * Borrowed read-only view, invalidated by push/break/init. NULL without history. */
const ge_features *ge_current_features(const geometry_engine *);
/* EOF/broken adjacency completes the unused boundary field using its own census.
 * Clears all history; preserves the two configuration flags. */
unsigned ge_break(geometry_engine *, ge_decision out[2]);
const char *ge_class_name(ge_class);
#endif
