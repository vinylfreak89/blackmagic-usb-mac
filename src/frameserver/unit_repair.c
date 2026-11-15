#include "unit_repair.h"
#include <string.h>

enum {
    U = UNIT_PARSER_VIDEO_UNIT_BYTES,
    H = UNIT_PARSER_VIDEO_HEADER_BYTES,
    L = 1440,                 // bytes per row (720 UYVY samples)
    F2 = 262,                 // field 1 owns rows [0,262), field 2 [262,525) (frame_publisher.h)
    BLANK_MAX = 6,            // blanking is about code 1-2; picture black (setup) about 17, never below ~10
    PICTURE_MIN = 12,
    JUNK_ZERO_RUN = 16,       // picture never carries code 0 (none in any capture); 16 zero bytes are filler
    JUNK_REPEAT_RUN = 124,    // a 4-byte word repeated over 128 bytes is filler (tape noise never repeats exactly)
};

typedef enum { C_OUT = 0, C_DARK, C_PIC, C_PAD, C_JUNK, C_OTHER } row_class;

const char *ur_status_name(ur_status s){
    switch (s){
    case UR_OK: return "ok";
    case UR_NOT_A_UNIT: return "not-a-unit";
    case UR_DELTA_RANGE: return "delta-range";
    case UR_WHOLE_LINE_DELTA: return "whole-line-delta";
    case UR_NO_EVIDENCE: return "no-evidence";
    case UR_TOO_MUCH_LOST: return "too-much-lost";
    case UR_NO_SOURCE: return "no-source";
    case UR_SECOND_EVENT: return "second-event";
    }
    return "?";
}

static int is_pad(const uint8_t *w){            // the Shuttle's own fill rows: chroma 128, luma 16 exactly
    unsigned bad = 0;
    for (unsigned i = 0; i < L; i += 2){
        bad += (w[i] != 0x80) + (w[i + 1] != 0x10);
        if (bad > 16) return 0;
    }
    return 1;
}

static int has_junk(const uint8_t *w){
    unsigned zeros = 0, rep = 0;
    for (unsigned i = 0; i < L; i++){
        zeros = w[i] ? 0 : zeros + 1;
        if (zeros >= JUNK_ZERO_RUN) return 1;
        if (i >= 4){
            rep = w[i] == w[i - 4] ? rep + 1 : 0;
            if (rep >= JUNK_REPEAT_RUN && !(w[i - 1] == 0x80 && w[i] == 0x10) && !(w[i - 1] == 0x10 && w[i] == 0x80)) return 1;
        }
    }
    return 0;
}

/* The row whose first byte is at pos (unit coordinates, header included). Luma sits at the odd bytes of a row. */
static row_class classify(const uint8_t *unit, size_t count, long pos){
    if (pos < H || pos + L > (long)count) return C_OUT;
    const uint8_t *w = unit + pos;
    if (is_pad(w)) return C_PAD;
    if (has_junk(w)) return C_JUNK;
    unsigned dark = 0, maxy = 0;
    for (unsigned c = 1; c <= 8; c++) dark += w[2 * c + 1] <= BLANK_MAX;
    for (unsigned c = 32; c < 688; c++) if (w[2 * c + 1] > maxy) maxy = w[2 * c + 1];
    if (maxy <= BLANK_MAX) return C_DARK;
    return dark >= 7 && maxy >= PICTURE_MIN ? C_PIC : C_OTHER;
}
/* Evidence from row k of the whole-unit layout. Only rows that are picture in every whole unit speak for blanking:
 * the vertical-interval rows (7-18, 270-281) start with noise around codes 4-10 and the head-switch rows (257-260,
 * 519-522) can start with the line before the switch. Padding is the Shuttle's own fill at rows 0-6, 261-269 and
 * 523-524 (exact in every whole unit examined, with and without input); padding anywhere else is fill the Shuttle
 * wrote while recovering sync (seen in the middle of both long units), so it contradicts, like filler. */
static int picture_row(int k){ return (k >= 20 && k < 256) || (k >= 283 && k < 518); }
static int padding_row(int k){ return k <= 6 || (k >= 261 && k <= 269) || k >= 523; }
/* What a row holds in a whole unit, for choosing rebuild sources: 0 padding, 1 vertical interval, 2 picture (the
 * aperture's first line 19/282 and last 256/518 included), 3 head switch (257-260, 519-522: near-blank or the line
 * before the switch). */
static int row_kind(int k){
    if (padding_row(k)) return 0;
    if ((k >= 7 && k < 19) || (k >= 270 && k < 282)) return 1;
    if ((k >= 257 && k <= 260) || (k >= 519 && k <= 522)) return 3;    // rows 256/518 carry picture (CLAUDE.md census)
    return 2;
}
/* Top-of-field lines a deck's flag can bend (picture to the window edge, measured on two tapes with V-stabilize off):
 * a few disagreeing rows there are picture as it came, not a second length error. */
static int flag_zone(int k){ return (k >= 20 && k < 36) || (k >= 283 && k < 299); }
static int score(int k, row_class c){
    switch (c){
    case C_JUNK: return -1;
    case C_PAD: return padding_row(k) ? 1 : -1;
    case C_PIC: return picture_row(k);
    case C_OTHER: return -picture_row(k);
    /* A picture row is never wholly at blanking level: black picture sits at setup (about code 17). The Shuttle restarting a
     * field writes blanking-level rows into the middle of a unit (25:25 of one capture: ~5 rows after its mid-unit padding). */
    case C_DARK: return -picture_row(k);
    default: return 0;
    }
}

/* The horizontal shift (samples) that best aligns a row with a reference line, within -352..352 (a tear moves the rest
 * of a line by up to half a line either way): a 16-sample grid over every 8th luma sample of the overlap, then 4-sample
 * steps over every 4th sample within 12 of the grid's best (a repair costs about 3.5 ms; the full search took 16).
 * *clear: on the grid, the best fits at least twice as well as no shift, and well, and is unique (every grid shift more
 * than 16 samples from it fits at least 1.5 times worse: a repeating pattern fits equally at many shifts, so its best is
 * arbitrary); the refined shift is not the search limit (where picture with nothing to align ends up). */
enum { SHIFT_MAX = 352, COARSE = 16, GRID = 2 * SHIFT_MAX / COARSE + 1 };
static unsigned shift_mad(const uint8_t *row, const uint8_t *ref, int s, int step){
    unsigned sum = 0, n = 0;
    for (int c = 8; c < 712; c += step){
        int cs = c + s; if (cs < 8 || cs >= 712) continue;
        int d = (int)row[2 * cs + 1] - (int)ref[2 * c + 1]; sum += (unsigned)(d < 0 ? -d : d); n++;
    }
    return n >= 32 ? sum * 16 / n : ~0u;                       // too little overlap to judge
}
static int best_shift(const uint8_t *row, const uint8_t *ref, int *clear){
    unsigned m[GRID], best = ~0u, at0 = 0, second = ~0u; int bi = -1;
    for (int i = 0; i < GRID; i++){
        int s = -SHIFT_MAX + COARSE * i; m[i] = shift_mad(row, ref, s, 8);
        if (s == 0) at0 = m[i];
        if (m[i] < best){ best = m[i]; bi = i; }
    }
    *clear = 0;
    if (bi < 0) return 0;
    for (int i = 0; i < GRID; i++) if ((i > bi ? i - bi : bi - i) > 1 && m[i] < second) second = m[i];
    int bs = -SHIFT_MAX + COARSE * bi; unsigned fine = ~0u; int fs = bs;
    for (int s = bs - 12; s <= bs + 12; s += 4){
        if (s < -SHIFT_MAX || s > SHIFT_MAX) continue;
        unsigned v = shift_mad(row, ref, s, 4); if (v < fine){ fine = v; fs = s; }
    }
    *clear = best * 2 < at0 && at0 >= 8 * 16 && (uint64_t)second * 2 >= (uint64_t)best * 3 && fs > -SHIFT_MAX + 8 && fs < SHIFT_MAX - 8;
    return fs;
}
/* A second length error tears the picture again inside a trusted part: every row below it is offset sideways from every
 * row above. The line-start test can miss it where picture crushed to blanking level sits at the misread line start
 * (review 2026-11-15), so neighbouring trusted rows of a field are also checked for that offset, read as the repair will
 * publish them. A tear moves the lines on both sides alike: the same offset (24 samples or more, clearly better than none)
 * aligns the nearest pair across it and the pair one row further out. The tear falls between rows k and k+1, or inside
 * row k (which then matches neither side). Periodic picture aligns best unshifted between neighbouring lines, and a shallow
 * diagonal gives different offsets at the two distances. */
static int tear_at(const uint8_t *rows, int above, int below){   // rows[i] = the row's first byte as published
    int c1, c2, s1 = best_shift(rows + (long)below * L, rows + (long)above * L, &c1);
    if (!c1 || (s1 < 24 && s1 > -24)) return 0;
    int s2 = best_shift(rows + (long)(below + 1) * L, rows + (long)(above - 1) * L, &c2);
    return c2 && (s1 > s2 ? s1 - s2 : s2 - s1) <= 4;      // one search step: a diagonal's offset grows with the distance
}
static int second_event(const uint8_t *unit, long delta, int a_end, const unsigned char *trusted){
    for (int k = 2; k + 2 < UR_ROWS; k++){
        int lo = k < F2 ? 0 : F2, hi = k < F2 ? F2 : UR_ROWS;
        if (k - 2 < lo || k + 2 >= hi) continue;
        int ok = 1;
        for (int i = k - 2; i <= k + 2 && ok; i++) ok = trusted[i] && picture_row(i) && !flag_zone(i) && ((i < a_end) == (k < a_end));
        if (!ok) continue;
        const uint8_t *base = unit + H + (k < a_end ? 0 : delta);
        if (tear_at(base, k, k + 1) || tear_at(base, k - 1, k + 1)) return 1;
    }
    return 0;
}
static unsigned luma_mad(const uint8_t *a, const uint8_t *b){
    unsigned s = 0;
    for (unsigned i = 1; i < L; i += 2) s += a[i] > b[i] ? a[i] - b[i] : b[i] - a[i];
    return s / (L / 2);
}
static void blend(uint8_t *dst, const uint8_t *a, const uint8_t *b, unsigned wa, unsigned wb){
    unsigned t = wa + wb;
    for (unsigned i = 0; i < L; i++) dst[i] = (uint8_t)((a[i] * wa + b[i] * wb + t / 2) / t);
}

ur_status ur_repair(const uint8_t *unit, size_t count, uint8_t *out, ur_result *res){
    ur_result r; memset(&r, 0, sizeof r);
    r.delta = (long)count - (long)U;
    ur_status st = UR_OK;
    if (!unit || !out || count < H || unit[0] || unit[1] || unit[2] != 0xff || unit[3] != 0xff ||
        unit[6] != 0x01 || unit[7] != 0xe8 || r.delta == 0){ st = UR_NOT_A_UNIT; goto done; }
    if (r.delta > UR_MAX_DELTA_BYTES || r.delta < -UR_MAX_DELTA_BYTES){ st = UR_DELTA_RANGE; goto done; }
    long phase = ((r.delta % L) + L) % L;
    if (phase < 32 || phase > L - 32){ st = UR_WHOLE_LINE_DELTA; goto done; }

    signed char s0[UR_ROWS], sd[UR_ROWS]; unsigned char c0[UR_ROWS], cd[UR_ROWS];
    int P0[UR_ROWS + 1], PD[UR_ROWS + 1]; P0[0] = PD[0] = 0;
    for (int k = 0; k < UR_ROWS; k++){
        row_class a = classify(unit, count, H + (long)k * L), d = classify(unit, count, H + (long)k * L + r.delta);
        c0[k] = (unsigned char)a; cd[k] = (unsigned char)d;
        int x = score(k, a), y = score(k, d);
        /* A row that reads as picture at both offsets says nothing about where it belongs: picture crushed to blanking
         * level (CLAUDE.md: black floor-crushed on fixture A; sub-black undershoot at white text) can put "blanking" at
         * the displaced line start too. Counted for neither part, it cannot pull the split away from the damage. */
        if (x > 0 && y > 0) x = y = 0;
        s0[k] = (signed char)x; sd[k] = (signed char)y;
        P0[k + 1] = P0[k] + s0[k]; PD[k + 1] = PD[k] + sd[k];
    }
    // [0,a) in place needs its bytes present; [b,525) displaced needs b*L + delta >= 0; the two never share bytes.
    int amax = (int)(((long)count - H) / L); if (amax > UR_ROWS) amax = UR_ROWS;
    int best = 0, ba = -1, bb = -1;
    for (int a = 0; a <= amax; a++){
        for (int b = a; b <= UR_ROWS; b++){
            if ((long)b * L + r.delta < (long)a * L) continue;
            int j = 2 * P0[a] + 2 * (PD[UR_ROWS] - PD[b]) - (b - a);   // half a point per rebuilt row
            if (ba < 0 || j > best){ best = j; ba = a; bb = b; }
        }
    }
    if (ba < 0){ st = UR_NO_EVIDENCE; goto done; }
    int pcross = 0, scross = 0;
    for (int k = 0; k < ba; k++){ r.prefix_agree += s0[k] > 0; r.prefix_disagree += s0[k] < 0; pcross += sd[k] > 0; }
    for (int k = bb; k < UR_ROWS; k++){ r.suffix_agree += sd[k] > 0; r.suffix_disagree += sd[k] < 0; scross += s0[k] > 0; }
    // Enough rows must speak, nearly all for their part, and each part must read differently at the other offset.
    if (r.prefix_agree + r.suffix_agree < 100 ||
        r.prefix_disagree * 10 > r.prefix_agree + 30 || r.suffix_disagree * 10 > r.suffix_agree + 30 ||
        pcross * 5 > r.prefix_agree + 15 || scross * 5 > r.suffix_agree + 15){ st = UR_NO_EVIDENCE; goto done; }
    /* Trust only what a row confirmed: the in-place part ends at the last row that agrees there alone, and that row too
     * is rebuilt when it is picture (the damage can start inside it); the displaced part starts at the first row that
     * agrees there alone. Everything between (damage, rows that read either way, head-switch and vertical-interval rows
     * that carry no line-start evidence) is rebuilt; padding rows among them are the Shuttle's constant, regenerated. */
    int last0 = -1, firstd = UR_ROWS;
    /* Picture rows only: a padding block is nine identical rows, so a read a few hundred bytes off still finds padding. */
    for (int k = ba - 1; k >= 0; k--) if (s0[k] > 0 && picture_row(k)){ last0 = k; break; }
    for (int k = bb; k < UR_ROWS; k++) if (sd[k] > 0 && picture_row(k)){ firstd = k; break; }
    int a_end = last0 >= 0 && c0[last0] == C_PIC ? last0 : last0 + 1;
    r.prefix_rows = (unsigned)a_end; r.suffix_row = (unsigned)firstd;
    /* Inside the trusted parts, a row that is filler, padding out of place or blanking-level picture is Shuttle fill
     * too (25:25 of one capture: padding written over field-2 rows 345-353, one field after a block in the lost part):
     * rebuilt. Picture rows that read wrong at their part's offset are picture displaced by some other amount: three
     * in a row outside the top-of-field flag lines is a second length error in the unit, which this does not undo. */
    unsigned char trusted[UR_ROWS]; int lost = 0, run = 0;
    for (int k = 0; k < UR_ROWS; k++){
        int in = k < a_end || k >= firstd; row_class c = k < a_end ? (row_class)c0[k] : (row_class)cd[k];
        if (in && (c == C_JUNK || (c == C_PAD && !padding_row(k)) || (c == C_DARK && picture_row(k)))) in = 0;
        run = in && c == C_OTHER && picture_row(k) && !flag_zone(k) ? run + 1 : 0;
        if (run >= 3){ st = UR_SECOND_EVENT; goto done; }
        trusted[k] = (unsigned char)in; lost += !in;
    }
    if (lost > UR_MAX_REBUILT_ROWS){ st = UR_TOO_MUCH_LOST; goto done; }
    if (second_event(unit, r.delta, a_end, trusted)){ st = UR_SECOND_EVENT; goto done; }

    memcpy(out, unit, H);
    for (int k = 0; k < UR_ROWS; k++){
        if (!trusted[k]) continue;
        if (k < a_end) memcpy(out + H + (size_t)k * L, unit + H + (size_t)k * L, L);
        else memcpy(out + H + (size_t)k * L, unit + H + (long)k * L + r.delta, L);
    }
    uint8_t *rows = out + H;
    for (int k = 0; k < UR_ROWS; k++){
        if (trusted[k]) continue;
        uint8_t *dst = rows + (size_t)k * L;
        if (padding_row(k)){                   // the Shuttle's own constant fill, identical in every whole unit
            for (unsigned i = 0; i < L; i += 2){ dst[i] = 0x80; dst[i + 1] = 0x10; }
            r.rebuilt_rows[k < F2 ? 0 : 1]++; continue;
        }
        /* Sources are lines of the same kind (row_kind): picture from picture, a vertical-interval or head-switch line
         * from its own kind, so line 23 is never half the dark line above it. */
        int ap = row_kind(k), lo = k < F2 ? 0 : F2, hi = k < F2 ? F2 : UR_ROWS, u = -1, d = -1;
        for (int i = k - 1; i >= lo; i--) if (trusted[i] && row_kind(i) == ap){ u = i; break; }
        for (int i = k + 1; i < hi; i++) if (trusted[i] && row_kind(i) == ap){ d = i; break; }
        int o1 = k < F2 ? k + 262 : k - 263, o2 = k < F2 ? k + 263 : k - 262;   // the other field's lines above and below
        int t1 = o1 >= 0 && o1 < UR_ROWS && (k < F2 ? o1 >= F2 : o1 < F2) && trusted[o1] && row_kind(o1) == ap;
        int t2 = o2 >= 0 && o2 < UR_ROWS && (k < F2 ? o2 >= F2 : o2 < F2) && trusted[o2] && row_kind(o2) == ap;
        if (u >= 0 && d >= 0 && d - u <= 3){
            blend(dst, rows + (size_t)u * L, rows + (size_t)d * L, (unsigned)(d - k), (unsigned)(k - u)); r.rebuilt_same_field++;
        } else if (t1 || t2){
            const uint8_t *a1 = rows + (size_t)o1 * L, *a2 = rows + (size_t)o2 * L;
            int ref = u >= 0 && d >= 0 ? (k - u <= d - k ? u : d) : u >= 0 ? u : d;
            for (int i = 1; ref < 0 && (k - i >= lo || k + i < hi); i++){     // none of its kind: the nearest intact line
                if (k - i >= lo && trusted[k - i]) ref = k - i;
                else if (k + i < hi && trusted[k + i]) ref = k + i;
            }
            /* At the top and bottom of the picture the two lines straddle the edge (picture above, blanking below):
             * their average is a half-bright line no field ever had. Then take the one like this field's nearest line. */
            if (t1 && t2 && luma_mad(a1, a2) > 20 && ref >= 0)
                memcpy(dst, luma_mad(a1, rows + (size_t)ref * L) <= luma_mad(a2, rows + (size_t)ref * L) ? a1 : a2, L);
            else if (t1 && t2) blend(dst, a1, a2, 1, 1);
            else memcpy(dst, t1 ? a1 : a2, L);
            r.rebuilt_other_field++;
        } else if (u >= 0 && d >= 0){
            blend(dst, rows + (size_t)u * L, rows + (size_t)d * L, (unsigned)(d - k), (unsigned)(k - u)); r.rebuilt_same_field++;
        } else if (u >= 0 || d >= 0){
            memcpy(dst, rows + (size_t)(u >= 0 ? u : d) * L, L); r.rebuilt_same_field++;
        } else {
            /* No line of its kind anywhere intact. A picture line then has no source; a vertical-interval or head-switch
             * line (outside the picture, or at its very edge) takes the nearest intact line of its field. */
            int any = -1;
            for (int i = 1; ap == 2 ? 0 : (any < 0 && (k - i >= lo || k + i < hi)); i++){
                if (k - i >= lo && trusted[k - i]) any = k - i;
                else if (k + i < hi && trusted[k + i]) any = k + i;
            }
            if (any < 0){ st = UR_NO_SOURCE; goto done; }
            memcpy(dst, rows + (size_t)any * L, L); r.rebuilt_same_field++;
        }
        r.rebuilt_rows[k < F2 ? 0 : 1]++;
    }
done:
    r.status = st;
    if (res) *res = r;
    return st;
}
