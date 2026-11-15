// unit_repair — put back a picture unit the Shuttle sent at the wrong length, from its byte order alone.
//
// What the device does (measured 2026-11-15 on a capture made through a JVC deck; every USB packet in sequence, status 0,
// so the bytes are exactly as the Shuttle sent them):
//   - a unit 224 bytes short: 748 bytes of one line gone, 524 zeros written in their place;
//   - a unit 512 bytes long: 512 bytes of a dithered constant (Y160/161 U92/93 V92/93) inserted inside a line;
//   - units 23 1/3 lines long (+33,600 / +33,584): whole USB packets of one repeating 4-byte word (a stale buffer, about
//     40 packets) then zeros where ~80 lines should be, after which the Shuttle restarts its raster with its padding.
//     At 25:25 of that capture its padding fell on the same picture height in two consecutive fields: something
//     sync-like in the signal at that height, which it took for vertical sync.
// The audio clock gave every such unit its normal frame time: the extra bytes are not extra picture.
//
// Why nothing has to be inferred:
//   - Everything the Shuttle writes itself is an exact pattern tape picture never produces (its padding Y16/C128, zeros,
//     one word repeated, a dithered constant above blanking level). Every other byte is decoded picture, one row of
//     1440 bytes per line period, in time order.
//   - Its padding always starts on a row boundary of its own line grid. The padding after the stall therefore gives
//     the displaced part's exact byte phase; the displacement is the value of that phase nearest the length error
//     (they differ when the unit stops short inside its last row: 8 bytes at 25:25).
//   - With exactly one stretch of junk: the bytes before it are in place; the bytes after it are the same raster at
//     the displacement; the lost bytes are the gap between, plus the lines under padding the Shuttle wrote away from
//     its padding rows (it did not digitise those lines).
// Only the lost bytes are rebuilt (a whole row, or the lost stretch of one): from the same field across a gap of one or
// two lines, otherwise from the other field's lines above and below; where both fields lost the same height, from the
// previous unit when it shows the same picture around the gap, else interpolated down the frame.
// Picture is never used to place anything. It only checks the result: kept picture rows start on the tape's blanking,
// the displaced part sits on the blanking as the picture beside it does (to a sample), and no tear remains. A unit the
// bytes do not place (no junk, two stretches, padding that disagrees) or that fails a check is declined (UR_* status),
// and the caller keeps its old handling. Same bytes in, same frame out.
// Padding after the stall: the Shuttle's restart (an 8-row block within two rows after the junk, both measured restarts
// left 824 / 1,982 bytes of data before it, then its next field block 262 rows on) marks lines never digitised; every
// other block must sit exactly on the raster's padding rows (one landing rows off means the unit is short: declined).
// A block starting at the junk's end is always the rest of the raster's own block and must end at its standard row.
// Known limits (adversarial review, 2026-11-15, 8 rounds; on 894 real units with the measured damage no wrong output
// beyond the second): a second length error in the same unit that leaves no device fill is invisible to the bytes,
// caught only when it tears 24+ samples or shifts the grid (random two-error units: 0.84% published wrong); a dithered
// fill whose first byte matches the picture byte before it within one code is found one byte early (one luma byte off
// by at most one code, 5 of 894 trials). Declines that are conservative: a stall running straight into restart padding
// (never measured), and a tear from row 522 into the final padding (no padding after it gives the grid).
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
    UR_NO_FILL,             // no Shuttle-written junk: nothing in the bytes says where the error is
    UR_SECOND_EVENT,        // two separate stretches of junk, or a tear left after placing: more than one error
    UR_GRID,                // padding off its grid before the junk, padding disagreeing after it, or the parts would overlap
    UR_TOO_MUCH_LOST,       // more than UR_MAX_REBUILT_ROWS rows would be rebuilt
    UR_NO_SOURCE,           // a lost row has no intact line in either field to be rebuilt from
    UR_CHECK,               // the placed picture failed a check (line starts, blanking edge, or nothing confirms the phase)
} ur_status;

typedef struct {
    ur_status status;
    long delta;                 // byte_count - 756,048
    int grid_offset;            // displacement used - delta, bytes (the padding's phase; 0 without padding after the junk)
    long lost_bytes;            // bytes of picture the stall took (the gap between the two parts)
    unsigned prefix_rows;       // rows [0,prefix_rows) are wholly in place
    unsigned suffix_row;        // rows [suffix_row,525) are wholly displaced
    unsigned rebuilt_rows[2];   // rows rebuilt (wholly or in part) of field 1 (rows 0..261) and field 2 (262..524)
    unsigned rebuilt_same_field, rebuilt_other_field, rebuilt_previous;   // by source
    int edge_check;             // the blanking-edge check: displaced part minus the reference, half-samples
} ur_result;

// unit: the unit as it arrived (header + rows), count bytes. previous: the whole unit just before it (counter - 1), or NULL.
// out: 756,048 bytes, holding the put-back unit when UR_OK is returned; otherwise its contents are unspecified.
// Allocation-free; a few milliseconds (M3, -O2), most of it the tear check.
ur_status ur_repair(const uint8_t *unit, size_t count, const uint8_t *previous, uint8_t *out, ur_result *result);
const char *ur_status_name(ur_status s);

#ifdef __cplusplus
}
#endif
#endif
