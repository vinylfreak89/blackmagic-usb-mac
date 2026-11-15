// unit_repair — put back a picture unit the Shuttle sent at the wrong length, from its byte order alone.
//
// What the device does (measured 2026-11-15 on two captures, every USB packet in sequence, status 0, so the bytes are
// exactly as the Shuttle sent them):
//   - a unit 224 bytes short: 748 bytes of one line gone, 524 zeros written in their place (also -496, -512);
//   - a unit 512 bytes long: one sample (a chroma and a luma byte) held over 512 bytes inside a line, each byte within
//     one code (Y160/161 U92/93 V92/93 on one capture, C135/136 Y129 and C125 Y84/85 on another);
//   - units about 23 1/3 lines long (+33,104 to +33,616): whole USB packets of one repeating 4-byte word (a stale buffer,
//     about 40 packets; every word measured ends in 00 08) then zeros where ~80 lines should be, after which the
//     Shuttle restarts its raster with its padding. The restart can fall anywhere, the top of the unit included. Its
//     restart padding fell on the same picture height in two consecutive fields at 25:25 of one capture: something
//     sync-like in the signal at that height, which it took for vertical sync;
//   - the same stall running over the next unit's marker: one unit about two units long, its successor numbered two on;
//   - a stall running to the unit's end: nothing after it in that unit.
// The audio clock gave every such unit its normal frame time: the extra bytes are not extra picture.
//
// Why nothing has to be inferred:
//   - Everything the Shuttle writes itself is an exact pattern: its padding Y16/C128, zeros, a word repeated that carries
//     a reserved code (00/FF, which picture never does) or runs straight into the stall's zeros. A unit marker outside
//     the stall is another unit's header: declined. Its held-sample insert is the one pattern picture can share (flat
//     lines, the vertical interval), so it is taken only from a unit too long with no stall in it, as the single held
//     stretch (each byte position within one code, any level) at least the length error long between the last padding
//     block on the unit's grid and the first one displaced; any other there and it is declined.
//   - Every other byte is decoded picture, one row of 1440 bytes per line period, in time order.
//   - Its padding always starts on a row boundary of its own line grid. The padding after the stall therefore gives
//     the displaced part's exact byte phase; the displacement is the value of that phase nearest the length error
//     (they differ by a few bytes when the unit ends inside a row: measured -12 to +12, +8 at 25:25 of one capture).
//     Picture samples that look like padding (Cb128/Y16) join a padding run at either edge; a run over whole rows has
//     its true start anywhere in the excess, and every grid that range allows is a candidate: one fixes it, several
//     must be settled by another block, else declined.
//   - With exactly one stretch of junk: the bytes before it are in place; the bytes after it are the same raster at
//     the displacement; the lost bytes are the gap between, plus the lines under padding the Shuttle wrote away from
//     its padding rows (it did not digitise those lines). Junk running to the unit's end displaces nothing. With
//     several stalls the bytes between the first and the last have no whole-row position: that whole stretch is lost
//     (never placed) and its rows rebuilt, within the rebuild limit.
// Only the lost bytes are rebuilt (a whole row, or the lost stretch of one): from the same field across a gap of one or
// two lines, otherwise from the other field's lines above and below; where both fields lost the same height, from the
// previous unit when it shows the same picture around the gap, else interpolated down the frame.
// Picture is never used to place anything. It only checks the result: where this tape's lines start on blanking inside
// the window, the displaced picture rows must too, and must sit on the blanking as the picture beside it does (to a
// sample); where they do not (picture at the window's left edge), the displaced rows must show the same sideways
// motion against the previous unit as the rows in place (to a sample, summed over 20+ rows); no tear may remain; and no
// block of rows may sit 24+ samples sideways against the other field's lines (whole frame, vertical interval included).
// A unit the bytes do not place (no junk, two stretches, padding that disagrees) or that fails a check is declined
// (UR_* status), and the caller keeps its old handling. Same bytes in, same frame out.
// Padding after the stall: the Shuttle's restart (an 8-row block within two rows after the junk, both measured restarts
// left 824 / 1,982 bytes of data before it, then its next field block 262 rows on) marks lines never digitised; every
// other block must sit exactly on the raster's padding rows (one landing rows off means the unit is short: declined).
// A block starting at the junk's end is always the rest of the raster's own block and must end at its standard row.
// Known limits (adversarial reviews 2026-11-15; fuzz of 30,000 units: no single fault published wrong, nor with padding-like picture injected at row edges, except an insert cut inside flat picture and the cut-block case below): a second length error in the same unit that
// leaves no device fill is invisible to the bytes, caught only when it tears 24+ samples, shifts the grid or moves the
// picture against the previous unit or the other field (a fill-less 1-64 byte error hidden beside one fault: 361 of 3,195 published wrong; never seen in a capture); an insert inside flat picture is cut from the
// start of the held stretch (identical bytes to within one code). Accepted by the owner (2026-11-15) over declining
// every fault below row ~270: the final padding block, cut by the unit's end, is read as the grid (whole rows, or a few
// bytes short), and is wrong when padding-like picture ends row 522 (2 of 74 real units) while the unit ends early (both
// field-2 tears measured did, by 12 bytes): a 2-sample shift (second review: 6 of 256 real trials, 8 of 2,889
// adversarial tears; none in realistic fuzz). It can also settle an ambiguous 261 block the wrong way. Declines that are conservative:
// an insert sharing its window with another held stretch (the vertical interval: most field-1 inserts), a stall running
// straight into restart padding (never measured), a tear from row 522 into the final padding (no padding after it
// gives the grid), stalls so far apart that more than UR_MAX_REBUILT_ROWS rows would be rebuilt, and a run of two units
// with stalls before the second unit's place in both (either could have taken its marker).
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
    UR_MARKER,              // a unit marker among the bytes outside the stall: another unit's header, not one unit's fault
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
/* A stall that ran over the next unit's marker: count about two units. scratch: UR_SCRATCH_BYTES; out: two units
 * (counters c and c + 1). Each is put back on its own evidence: res[i].status says which (UR_OK returned only for both). */
#define UR_SCRATCH_BYTES ((size_t)UNIT_PARSER_VIDEO_UNIT_BYTES + 64)
ur_status ur_repair2(const uint8_t *unit, size_t count, const uint8_t *previous, uint8_t *scratch, uint8_t *out, ur_result res[2]);
/* Where the Shuttle's own writing (a stall's zeros or stale words, or the no-signal raster it writes after losing its input
 * mid-unit: all carry a 00 byte, which picture never does) first begins, at the start of its row, or count if nowhere: a
 * unit shown as it is (a partial unit) is shown only that far. */
size_t ur_picture_bytes(const uint8_t *unit, size_t count);
const char *ur_status_name(ur_status s);

#ifdef __cplusplus
}
#endif
#endif
