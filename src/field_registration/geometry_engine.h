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
extern double ge_comb_reject; /* default 2; strict proposed-energy / minimum bar */
extern int ge_anchor_vote; /* default 0; last 30 confident frame anchors */
extern int ge_level_fill; /* default 0; ABSTAIN-only vote input, never census */
extern int ge_level_flat; /* default 0; also accept level candidates with sd<10 */
extern int ge_vote_pair; /* default 0; floor high end +1 AND paired top rows */
extern double ge_vote_pair_min; /* default .6; inclusive Pearson threshold */
extern int ge_bottom_flat; /* default 0; same-unit flat-band bottom reference */
extern double ge_bottom_flat_margin; /* default 3; inclusive, tolerance 1e-9 */
extern int ge_vote_blankspot; /* default 0; skipped field-2 rows need VI blanking */
extern int ge_comb_still; /* default 0; same-field motion gates comb authority */
extern int ge_comb_motion_min; /* default 1; positive whole lines; 99 withholds none */
#define GE_VOTE_WINDOW 30
#define GE_COMB_SELECTION_MARGIN 1.5
typedef struct { int first; double step, max_step; } ge_wave_result;
typedef enum { GE_WAVE_ABSTAIN, GE_WAVE_ACCEPTED, GE_WAVE_DISCARDED } ge_wave_status;
typedef enum { GE_SOURCE_NONE, GE_SOURCE_CENSUS, GE_SOURCE_HELD, GE_SOURCE_COMB,
               GE_SOURCE_PREVIOUS, GE_SOURCE_START, GE_SOURCE_REJECT,
               GE_SOURCE_DISCARD_PREVIOUS, GE_SOURCE_DISCARD_START, GE_SOURCE_VOTE } ge_source;
typedef struct {
    int first, accepted, measured; /* raw candidate plus clamp/continuation verdict */
    double reference, mean, sd, corr_below;
} ge_level_result;
typedef enum { GE_BOTTOM_UNKNOWN, GE_BOTTOM_FLAT_REFERENCE, GE_BOTTOM_FALLBACK } ge_bottom_rule;
typedef struct {
    double p5,p50,p95; /* F: body of storage row 258 / 521 */
    int measured; /* reference is measured only with the control enabled */
    ge_bottom_rule rule; /* UNKNOWN if no row supplies an answer */
} ge_bottom_evidence;
typedef enum { GE_UNKNOWN, GE_NOTHING, GE_VALID_MOVE, GE_BOTTOM_ONLY,
               GE_TOP_ONLY, GE_NOT_IN_TANDEM } ge_class;
enum { GE_T1=1, GE_UNMEASURABLE=2, GE_FIELD1=4, GE_FIELD2=8, GE_CONFIRM=16,
       GE_BASIS_CHANGED=32, GE_STILL=64 };
typedef struct {
    double error, second_error; /* exact integer SAD / (180*640) */
    int known, shift;
} ge_vertical_motion;
typedef enum { GE_PICTURE_UNKNOWN, GE_PICTURE_STILL, GE_PICTURE_MOVING } ge_picture_motion;
typedef struct {
    int shift, decided;
    double margin;
    double energies[11]; /* shift order -5..+5; valid iff margin is not NAN */
} ge_comb_result;
typedef struct {
    double ratio, rise_left, rise_right; /* NAN when not measured / no side */
    int floor_lo, floor_hi; /* shifts, inclusive contiguous <=1.5*minimum */
    int basin; /* interior floor with both rises >= selection margin */
} ge_comb_evidence;
typedef struct {
    int first[2], last[2], bottom[2]; /* first is accepted census, zero unavailable */
    ge_wave_result wave[2]; /* immutable pre-clamp observations */
    ge_wave_status wave_status[2];
    double blank[2];
    double hblank_level[2];
    int hblank_cols[2];
    uint16_t profile[2][12][672]; /* exact eight-sample sums */
    ge_class motion[2];
    ge_level_result level[2]; /* supplemental evidence, never used by classify */
    ge_bottom_evidence bottom_evidence[2];
    ge_vertical_motion vertical[2]; /* this unit against its adjacent predecessor */
} ge_features;
typedef struct {
    uint64_t counter, top_unit;
    int d1, d2, unused1, unused2, reset_before, has_frame;
    int frame_d1, frame_d2, published_d, held, comb_ran;
    unsigned triggers;
    ge_comb_result comb; /* NAN margin unless triggered, audited, or vote enabled */
    ge_comb_evidence rejection; /* frame-owned; ratio is BEFORE rejection */
    int rejected, discarded, refused_d, substituted_d;
    int first[2], last[2], bottom[2];
    double hblank_level[2]; /* this unit's own fields, also on unused boundaries */
    int hblank_cols[2];
    ge_wave_result wave[2]; /* this UNIT's raw observations, not frame-owned */
    ge_wave_status wave_status[2];
    ge_source relative_source, anchor_source; /* frame-owned publication basis */
    ge_class motion[2];
    int vote_confident, vote_anchor, vote_engine_anchor, vote_count, vote_winner_count;
    int vote_top[2]; /* frame-owned waveform or accepted fill, not census */
    ge_level_result level[2]; /* frame-owned, measured only on ABSTAIN fields */
    double vote_rB; /* NAN unless pairing is enabled and both vote tops exist */
    int vote_pair_pass; /* correlation test only, not the complete confidence */
    ge_bottom_evidence bottom_evidence[2]; /* frame-owned, like last[] */
    ge_vertical_motion vertical[2]; /* frame-owned, field 1 from top_unit */
    ge_picture_motion picture_motion;
    int still_trigger, comb_suppressed;
    int vote_blankspot_measured, vote_blankspot_pass, vote_blankspot_line;
} ge_decision;
typedef struct geometry_engine geometry_engine;
size_t ge_size(void);
void ge_init(geometry_engine *, int pair_next, int audit_comb);
/* After ge_break flushes the old pairing, reset for a new pairing within the
 * same session. Retains only the published vote anchor, never prior votes. */
void ge_set_pairing(geometry_engine *, int pair_next);
/* All input rows are contiguous 720-byte luma, independent of UYVY decoding. */
void ge_measure(const uint8_t *, ge_features *);
/* Raw entry-33 observation: no step returns first=0 and step=0. NTSC lines.
 * ge_measure applies the independent symmetric clamp to each raw observation. */
ge_wave_result ge_wave_scan(const uint8_t *, int field, double bar);
int ge_wave_accept(ge_wave_result, int field, int clamp);
ge_level_result ge_level_scan(const uint8_t *, int field, int clamp, int flat);
const char *ge_wave_status_name(ge_wave_status);
const char *ge_source_name(ge_source);
const char *ge_bottom_rule_name(ge_bottom_rule);
ge_comb_result ge_comb(const uint8_t *top, const uint8_t *bottom);
/* Pure evidence; does not adopt, alter decided, or run another search.
 * A proposed shift outside -5..5 has no measured energy: ratio is NAN. */
ge_comb_evidence ge_comb_examine(const ge_comb_result *, int proposed);
ge_vertical_motion ge_motion_measure(const uint8_t *current,const uint8_t *previous,int field);
const char *ge_picture_motion_name(ge_picture_motion);
/* Returns 0..2 completed unit decisions, in source order. Reset applies before
 * the first frame using this unit, even when that frame belongs to its predecessor.
 * Counter gaps implicitly break the pair and reset. Do not cross epochs: call break.
 */
unsigned ge_push(geometry_engine *, const uint8_t *, uint64_t counter,
                 int reset, ge_decision out[2]);
/* EOF/broken adjacency completes the unused boundary field using its own census.
 * Clears decision/vote evidence; retains the published vote anchor and config. */
unsigned ge_break(geometry_engine *, ge_decision out[2]);
const char *ge_class_name(ge_class);
#endif
