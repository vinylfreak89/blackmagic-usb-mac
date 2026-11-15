// unit_repair — put back a picture unit the Shuttle sent at the wrong length.
//
// What the device does (measured 2026-11-15 on a capture made through a JVC deck; every USB packet in sequence, status 0,
// so the bytes are exactly as the Shuttle sent them):
//   - deletes bytes inside a line, sometimes writing zeros over part of it (a unit 224 bytes short: 748 bytes of one line
//     gone, 524 of them zeros), so everything after arrives early and the picture tears sideways;
//   - inserts samples inside a line (256 samples of flat colour, a unit 512 bytes long), so everything after arrives late;
//   - while it recovers sync, writes filler (whole USB packets of a repeating 4-byte word, then zeros) over 60-110 lines
//     of picture, and the unit comes out 23 1/3 lines long (+33,600 / +33,584 bytes).
// In every case the unit is three parts: a trusted start in place, damage, and a trusted end displaced by exactly
// delta = byte_count - 756,048 bytes. The audio clock gave every such unit its normal frame time: the extra bytes are
// not extra picture.
//
// How the parts are found, without looking at picture content: every picture line the Shuttle delivers starts with
// samples of horizontal blanking at about code 1-2, below picture black (setup, about code 17). A row read at the
// right offset starts with that blanking; read at the wrong offset (a displacement of 16 samples or more) its start
// lands inside picture. Each of the 525 rows is classified at offset 0 and at offset delta (picture / Shuttle padding /
// dark / filler / other); the split [0,a) in place, [b,525) displaced, maximises the agreeing rows minus a small cost
// per rebuilt row. Rows a..b-1, and row a-1 (it holds the start of the damage), are rebuilt: from the same field when
// the gap there is one or two lines, otherwise from the other field's lines above and below, which the measured
// faults always left intact. Rows that read as picture at both offsets count for neither part and, next to the damage,
// are rebuilt; picture rows displaced by some third amount (a second length error) decline the unit. Anything the
// evidence does not settle is declined (UR_* status), and the caller keeps its old handling.
#ifndef UNIT_REPAIR_H
#define UNIT_REPAIR_H
#include <stddef.h>
#include <stdint.h>
#include "../unit_parser/unit_parser.h"

#ifdef __cplusplus
extern "C" {
#endif

#define UR_ROWS 525
#define UR_MAX_DELTA_BYTES ((long)UNIT_PARSER_VIDEO_LONG_SLACK_BYTES)   // either way; longer runs are not one unit
#define UR_MAX_REBUILT_ROWS 200                                         // more than this is not a repair

typedef enum {
    UR_OK = 0,
    UR_NOT_A_UNIT,          // no marker / not 0xe801 / whole already
    UR_DELTA_RANGE,         // more than UR_MAX_DELTA_BYTES from a whole unit
    UR_WHOLE_LINE_DELTA,    // displacement within 16 samples of a whole number of lines: blanking cannot tell the parts apart
    UR_NO_EVIDENCE,         // too few rows say which part they belong to (dark or no-signal picture)
    UR_TOO_MUCH_LOST,       // more than UR_MAX_REBUILT_ROWS rows would be rebuilt
    UR_NO_SOURCE,           // a lost row has no intact line in either field to be rebuilt from
    UR_SECOND_EVENT,        // picture rows inside a trusted part are displaced by another amount: two length errors in one unit
} ur_status;

typedef struct {
    ur_status status;
    long delta;                 // byte_count - 756,048
    unsigned prefix_rows;       // rows [0,prefix_rows) are taken in place (less rows that are fill: rebuilt)
    unsigned suffix_row;        // rows [suffix_row,525) are read delta bytes later (less rows that are fill)
    unsigned rebuilt_rows[2];   // rebuilt rows of field 1 (rows 0..261) and field 2 (rows 262..524)
    unsigned rebuilt_same_field, rebuilt_other_field;
    int prefix_agree, prefix_disagree;   // picture/padding rows that confirm / contradict the in-place reading
    int suffix_agree, suffix_disagree;   // the same for the displaced reading
} ur_result;

// unit: the unit as it arrived (header + rows), count bytes. out: 756,048 bytes, holding the put-back unit when UR_OK is
// returned (header copied, rows in place / displaced / rebuilt); otherwise its contents are unspecified. Allocation-free;
// about 3.5 ms (M3, -O2), most of it the second-error check.
// Known limits (adversarial review 2026-11-15; never seen on real units, which have shown one error each): a second
// length error whose sideways offset is under 24 samples, or that lies in picture of under 8 codes of contrast, AND whose
// misread line starts land on picture crushed to blanking level, is not detected and those rows are published displaced.
ur_status ur_repair(const uint8_t *unit, size_t count, uint8_t *out, ur_result *result);
const char *ur_status_name(ur_status s);

#ifdef __cplusplus
}
#endif
#endif
