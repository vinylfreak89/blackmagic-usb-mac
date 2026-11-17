#include "unit_repair.h"
#include <string.h>

enum {
    U = UNIT_PARSER_VIDEO_UNIT_BYTES,
    H = UNIT_PARSER_VIDEO_HEADER_BYTES,
    L = 1440,                 // bytes per row (720 UYVY samples)
    F2 = 262,                 // field 1 owns rows [0,262), field 2 [262,525) (frame_publisher.h)
    BLANK_MAX = 6,            // blanking is about code 1-2; picture black (setup) about 17, never below ~10
    PICTURE_MIN = 12,
    PAD_MIN = 64,             // a run of the padding word this long is the Shuttle's padding (tape picture is never exactly Y16/C128)
    ZERO_MIN = 16,            // picture never carries code 0 (none in any capture): 16 zero bytes are the Shuttle's
    WORD_MIN = 64,            // one 4-byte word repeated over 64 bytes is the Shuttle's (tape noise never repeats exactly)
    DITHER_MIN = 256,         // the shortest held-sample insert looked for (one sample held, each byte within one code)
    MAX_SPANS = 96,
    GRID_SLACK = 16,          // the displaced part's grid may sit this far either side of the length error (measured -12 to +12,
                              // a unit ending inside a row); more is a second, unmarked length error and declines
};

const char *ur_status_name(ur_status s){
    switch (s){
    case UR_OK: return "ok";
    case UR_NOT_A_UNIT: return "not-a-unit";
    case UR_DELTA_RANGE: return "delta-range";
    case UR_NO_FILL: return "no-fill";
    case UR_SECOND_EVENT: return "second-event";
    case UR_GRID: return "grid";
    case UR_TOO_MUCH_LOST: return "too-much-lost";
    case UR_NO_SOURCE: return "no-source";
    case UR_CHECK: return "check";
    case UR_MARKER: return "marker";
    }
    return "?";
}

/* ---------------------------------------------------------------- the Shuttle's own bytes
 * Everything the device writes itself is an exact pattern no tape picture ever produces: its padding (Y16/C128,
 * "80 10" repeated), zeros, one 4-byte word repeated (whole USB packets of a stale buffer: af8c0008, a0ad0008), and a
 * dithered constant (every byte position holding two adjacent values: Y160/161 U92/93 V92/93 at one capture's +512).
 * A dithered constant at blanking level is the device's vertical-interval fill, which belongs where it is: not junk. */
typedef enum { S_DATA = 0, S_PAD, S_JUNK } span_kind;
typedef struct { span_kind kind; long start, end; } span;

static long run_pad(const uint8_t *a, long i, long n){
    long j = i; while (j + 1 < n && a[j] == 0x80 && a[j + 1] == 0x10) j += 2; return j - i;
}
static long run_zero(const uint8_t *a, long i, long n){ long j = i; while (j < n && !a[j]) j++; return j - i; }
static long run_word(const uint8_t *a, long i, long n){
    if (i + 8 > n || !(a[i] | a[i + 1] | a[i + 2] | a[i + 3])) return 0;
    int reserved = 0; for (int k = 0; k < 4; k++) reserved |= a[i + k] == 0 || a[i + k] == 0xff;
    if (!reserved) return 0;                         // a stale buffer word carries a reserved code (00/FF): picture never does
    if ((a[i] == 0x80 && a[i + 1] == 0x10 && a[i + 2] == 0x80 && a[i + 3] == 0x10) ||
        (a[i] == 0x10 && a[i + 1] == 0x80 && a[i + 2] == 0x10 && a[i + 3] == 0x80)) return 0;   // padding, at either phase
    long j = i + 4; while (j + 4 <= n && !memcmp(a + j, a + i, 4)) j += 4; return j - i;
}
/* A held stretch: each of the four byte positions (U, Y, V, Y) within one code, at any level, blanking included (the
 * measured inserts hold one sample, U and V alike; this takes any held pair too, so the true insert is always among the
 * candidates). Padding is its own span: a held run never runs into it. */
static long run_held(const uint8_t *a, long i, long n){
    uint8_t lo[4], hi[4]; long j = i;
    if (i + 4 > n) return 0;
    for (int k = 0; k < 4; k++) lo[k] = hi[k] = a[i + k];
    while (j + 4 <= n){
        int pad = 0;
        for (int k = 0; k < 4 && !pad; k++) pad = a[j + k] == 0x80 && a[j + k + 1] == 0x10 && run_pad(a, j + k, n) >= PAD_MIN;
        if (pad) break;
        int ok = 1;
        for (int k = 0; k < 4 && ok; k++){
            uint8_t v = a[j + k], l = v < lo[k] ? v : lo[k], h = v > hi[k] ? v : hi[k];
            if (h - l > 1) ok = 0; else { lo[k] = l; hi[k] = h; }
        }
        if (!ok) break; j += 4;
    }
    return j - i;
}
/* A stall's fill word without a reserved code (one measured word with one bit flipped would be one) is still the stall
 * when it runs straight into the stall's zeros: the repeated word ending at `end` (a partial word of up to 3 bytes
 * allowed at the end), back to no earlier than `lo`. Returns its length, 0 if under WORD_MIN. */
static long word_back(const uint8_t *a, long lo, long end){
    long best = 0;
    for (int part = 0; part < 4; part++){
        long w = end - part - 4; if (w < lo) break;
        const uint8_t *word = a + w;
        if (!(word[0] | word[1] | word[2] | word[3])) continue;
        if (word[0] == 0x80 && word[1] == 0x10 && word[2] == 0x80 && word[3] == 0x10) continue;
        if (word[0] == 0x10 && word[1] == 0x80 && word[2] == 0x10 && word[3] == 0x80) continue;
        if (part && memcmp(a + end - part, word, (size_t)part)) continue;
        long k = w; while (k - 4 >= lo && !memcmp(a + k - 4, word, 4)) k -= 4;
        if (end - k > best) best = end - k;
    }
    return best >= WORD_MIN ? best : 0;
}
static long word_fwd(const uint8_t *a, long start, long hi){
    if (start + 4 > hi) return 0;
    const uint8_t *word = a + start;
    if (!(word[0] | word[1] | word[2] | word[3])) return 0;
    if ((word[0] == 0x80 && word[1] == 0x10 && word[2] == 0x80 && word[3] == 0x10) || (word[0] == 0x10 && word[1] == 0x80 && word[2] == 0x10 && word[3] == 0x80)) return 0;
    long k = start + 4; while (k + 4 <= hi && !memcmp(a + k, word, 4)) k += 4;
    return k - start >= WORD_MIN ? k - start : 0;
}
/* Splits [H,count) into data, padding and junk spans; returns the count, or -1 if there are more than MAX_SPANS. */
static int segment(const uint8_t *a, long n, span *s){
    int m = 0; long i = H, d0 = H;
    while (i < n){
        long r; span_kind k = S_DATA;
        if ((r = run_pad(a, i, n)) >= PAD_MIN) k = S_PAD;
        else if ((r = run_zero(a, i, n)) >= ZERO_MIN) k = S_JUNK;
        else if ((r = run_word(a, i, n)) >= WORD_MIN) k = S_JUNK;
        if (k == S_DATA){ i++; continue; }
        if (d0 < i){ if (m == MAX_SPANS) return -1; s[m++] = (span){S_DATA, d0, i}; }
        if (m && s[m - 1].kind == k && s[m - 1].end == i) s[m - 1].end = i + r;     // adjacent runs of one kind merge
        else { if (m == MAX_SPANS) return -1; s[m++] = (span){k, i, i + r}; }
        i += r; d0 = i;
    }
    if (d0 < n){ if (m == MAX_SPANS) return -1; s[m++] = (span){S_DATA, d0, n}; }
    return m;
}

/* Segments [H,count) and finds its stall: junk stretches less than 16 bytes apart are one stall (a fill word ending in
 * half a word before its zeros). With several stalls everything from the first to the last is one lost stretch: the
 * part between them has no whole-row position, so it is never placed (its rows are rebuilt). Returns the span count
 * with *junk the stall's index (-1: none), or -1 when there are too many spans. */
static int stall_spans(const uint8_t *a, long n, span *sp, int *junk){
    int m = segment(a, n, sp); *junk = -1;
    if (m < 0) return -1;
    for (int i = 0; i + 2 < m; i++){
        if (sp[i].kind == S_JUNK && sp[i + 1].kind == S_DATA && sp[i + 2].kind == S_JUNK && sp[i + 1].end - sp[i + 1].start < ZERO_MIN){
            sp[i].end = sp[i + 2].end;
            memmove(sp + i + 1, sp + i + 3, sizeof(span) * (size_t)(m - i - 3)); m -= 2; i--;
        }
    }
    int last = -1;
    for (int i = 0; i < m; i++) if (sp[i].kind == S_JUNK){ if (*junk < 0) *junk = i; last = i; }
    if (last > *junk){                                   // several stalls: one lost stretch from the first to the last
        sp[*junk].end = sp[last].end;
        memmove(sp + *junk + 1, sp + last + 1, sizeof(span) * (size_t)(m - last - 1)); m -= last - *junk;
    }
    if (*junk >= 0){                                     // the stall's fill words, whatever they hold, belong to it
        int j = *junk;
        if (j > 0 && sp[j - 1].kind == S_DATA){
            long b = word_back(a, sp[j - 1].start, sp[j].start);
            if (b){ sp[j].start -= b; sp[j - 1].end -= b; if (sp[j - 1].end == sp[j - 1].start){ memmove(sp + j - 1, sp + j, sizeof(span) * (size_t)(m - j)); m--; j--; } }
        }
        if (j + 1 < m && sp[j + 1].kind == S_DATA){
            long f = word_fwd(a, sp[j].end, sp[j + 1].end);
            if (f){ sp[j].end += f; sp[j + 1].start += f; if (sp[j + 1].end == sp[j + 1].start){ memmove(sp + j + 1, sp + j + 2, sizeof(span) * (size_t)(m - j - 2)); m--; } }
        }
        *junk = j;
    }
    return m;
}
/* A unit marker (00 00 FF FF) anywhere but the unit's own header and the stall is a device header among the bytes
 * (picture never carries a 00): the run is not one unit's picture with one fault. */
static int marker_outside(const uint8_t *a, const span *sp, int m){
    for (int i = 0; i < m; i++){
        if (sp[i].kind == S_JUNK) continue;
        for (long x = sp[i].start > 4 ? sp[i].start - 3 : 4; x + 4 <= sp[i].end; x++)
            if (!a[x] && !a[x + 1] && a[x + 2] == 0xff && a[x + 3] == 0xff) return 1;
    }
    return 0;
}
/* A unit too long with no stall in it. The Shuttle's insert holds one sample over exactly the length error, so it lies
 * in [lo,hi): after the last padding block still on the unit's grid and before the first one displaced. Picture can
 * hold a sample as long (flat lines, the vertical interval, a blanking-level insert): only a single held run at least
 * the length error long in that window is the insert. Returns 1 with [*s,*e) the bytes to remove. */
static int find_insert(const uint8_t *a, long lo, long hi, long need, long *s, long *e){
    int found = 0; long work = 0;
    if (need < DITHER_MIN || hi - lo < need) return 0;
    for (long i = lo; i < hi; ){
        long r = run_held(a, i, hi); work += r + 1;
        if (work > 64L * U) return 0;                       // flat beyond reason: nothing singles out an insert
        if (r >= need){ if (found++) return 0; *s = i; *e = i + need; i += r; }
        else i++;
    }
    return found == 1;
}
/* ---------------------------------------------------------------- rows of the whole-unit layout */
static int picture_row(int k){ return (k >= 20 && k < 256) || (k >= 283 && k < 518); }
static int padding_row(int k){ return k <= 6 || (k >= 261 && k <= 269) || k >= 523; }
/* What a row holds in a whole unit, for choosing rebuild sources: 0 padding, 1 vertical interval, 2 picture (the
 * aperture's first line 19/282 and last 256/518 included), 3 head switch (257-260, 519-522). */
static int row_kind(int k){
    if (padding_row(k)) return 0;
    if ((k >= 7 && k < 19) || (k >= 270 && k < 282)) return 1;
    if ((k >= 257 && k <= 260) || (k >= 519 && k <= 522)) return 3;
    return 2;
}
/* Top-of-field lines a deck's flag can bend (picture to the window edge, measured with V-stabilize off). */
static int flag_zone(int k){ return (k >= 20 && k < 36) || (k >= 283 && k < 299); }
/* Position down the woven frame: field-1 row r sits between field-2 rows r+262 and r+263 (frame_publisher interleave). */
static int frame_line(int k){ return k < F2 ? 2 * k : 2 * (k - 263) + 1; }
static int row_at(int y){
    if (y < 0) return -1;
    int k = y % 2 ? (y - 1) / 2 + 263 : y / 2;
    return (y % 2 ? k >= F2 && k < UR_ROWS : k < F2) ? k : -1;
}

/* ---------------------------------------------------------------- checks on the assembled picture
 * Picture is never used to place anything: these only verify what the bytes placed, and a failure declines. */
static int line_start_ok(const uint8_t *w){     // the row starts with blanking (codes 1-2) and carries picture
    unsigned dark = 0, maxy = 0;
    for (unsigned c = 1; c <= 8; c++) dark += w[2 * c + 1] <= BLANK_MAX;
    for (unsigned c = 32; c < 688; c++) if (w[2 * c + 1] > maxy) maxy = w[2 * c + 1];
    if (maxy <= BLANK_MAX) return -1;            // dark: says nothing
    return dark >= 7 && maxy >= PICTURE_MIN;
}
/* Where a picture row's blanking plateau ends, in half-samples: the first sample from the left above code 8; -1 if none. */
static int plateau_end(const uint8_t *w){
    for (int c = 1; c < 4; c++) if (w[2 * c + 1] > 8) return -1;     // no blanking plateau inside the window
    for (int c = 4; c < 120; c++) if (w[2 * c + 1] > 8) return 2 * c;
    return -1;
}
enum { SHIFT_MAX = 352, COARSE = 16, GRID = 2 * SHIFT_MAX / COARSE + 1 };
static unsigned shift_mad(const uint8_t *row, const uint8_t *ref, int s, int step){
    unsigned sum = 0, n = 0;
    for (int c = 8; c < 712; c += step){
        int cs = c + s; if (cs < 8 || cs >= 712) continue;
        int d = (int)row[2 * cs + 1] - (int)ref[2 * c + 1]; sum += (unsigned)(d < 0 ? -d : d); n++;
    }
    return n >= 32 ? sum * 16 / n : ~0u;
}
/* The sideways shift aligning a row with a reference line (coarse 16-sample grid, then 4-sample steps). *clear: the
 * best fits twice as well as no shift, and well, is unique on the grid, and is not the search limit. */
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
/* A tear left in the assembled picture: the same sideways offset (24+ samples) aligns the nearest pair of lines across
 * it and the pair one further out, between rows k/k+1 or across row k. */
static int tear_at(const uint8_t *rows, int above, int below){
    int c1, c2, s1 = best_shift(rows + (long)below * L, rows + (long)above * L, &c1);
    if (!c1 || (s1 < 24 && s1 > -24)) return 0;
    int s2 = best_shift(rows + (long)(below + 1) * L, rows + (long)(above - 1) * L, &c2);
    return c2 && (s1 > s2 ? s1 - s2 : s2 - s1) <= 4;
}
static int tear_left(const uint8_t *rows, const unsigned char *kept){
    for (int k = 2; k + 2 < UR_ROWS; k++){
        int lo = k < F2 ? 0 : F2, hi = k < F2 ? F2 : UR_ROWS;
        if (k - 2 < lo || k + 2 >= hi) continue;
        int ok = 1;
        for (int i = k - 2; i <= k + 2 && ok; i++) ok = kept[i] && picture_row(i) && !flag_zone(i);
        if (ok && (tear_at(rows, k, k + 1) || tear_at(rows, k - 1, k + 1))) return 1;
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

/* ---------------------------------------------------------------- the repair */
ur_status ur_repair(const uint8_t *unit, size_t count, const uint8_t *previous, uint8_t *out, ur_result *res){
    ur_result r; memset(&r, 0, sizeof r);
    long n = (long)count;
    r.delta = n - (long)U;
    ur_status st = UR_OK;
    span sp[MAX_SPANS]; int m, junk = -1;
    if (!unit || !out || count < H || unit[0] || unit[1] || unit[2] != 0xff || unit[3] != 0xff ||
        unit[6] != 0x01 || unit[7] != 0xe8 || r.delta == 0){ st = UR_NOT_A_UNIT; goto done; }
    if (r.delta < -UR_MAX_DELTA_BYTES || n > (long)UNIT_PARSER_VIDEO_DOUBLE_MAX_BYTES){ st = UR_DELTA_RANGE; goto done; }

    /* 1. The device-written spans. Exactly one stretch of junk: everything before it is where it belongs; everything
     *    after it is the same raster displaced. No junk: nothing in the bytes says where the error is. */
    if ((m = stall_spans(unit, n, sp, &junk)) < 0){ st = UR_SECOND_EVENT; goto done; }
    if (junk < 0 && r.delta > 0){
        /* The window: after the last block on the unit's grid at its standard row, before the first block that is not. */
        long is, ie, wlo = H, whi = -1;
        for (int i = 0; i < m; i++){
            if (sp[i].kind != S_PAD) continue;
            long st0 = sp[i].start - H; int row = (int)(st0 / L);
            if (st0 % L == 0 && (row == 0 || row == 261 || row == 523)) wlo = sp[i].end;
            else { whi = sp[i].start; break; }
        }
        if (whi > wlo && find_insert(unit, wlo, whi, r.delta, &is, &ie)){
            int at = -1;
            for (int i = 0; i < m; i++) if (sp[i].kind == S_DATA && sp[i].start <= is && ie <= sp[i].end){ at = i; break; }
            if (at >= 0 && m + 2 <= MAX_SPANS){
                span d = sp[at];
                memmove(sp + at + 3, sp + at + 1, sizeof(span) * (size_t)(m - at - 1)); m += 2;
                sp[at] = (span){S_DATA, d.start, is}; sp[at + 1] = (span){S_JUNK, is, ie}; sp[at + 2] = (span){S_DATA, ie, d.end};
                if (sp[at].end == sp[at].start){ memmove(sp + at, sp + at + 1, sizeof(span) * (size_t)(m - at - 1)); m--; at--; }
                junk = at + 1;
                if (sp[junk + 1].end == sp[junk + 1].start){ memmove(sp + junk + 1, sp + junk + 2, sizeof(span) * (size_t)(m - junk - 2)); m--; }
            }
        }
    }
    if (junk < 0){ st = UR_NO_FILL; goto done; }
    /* Longer than the slack only when the stall runs to the run's end (it wrote over the units after this one: nothing
     * of theirs is here, and this one's bytes before it are in place). */
    if (r.delta > UR_MAX_DELTA_BYTES && sp[junk].end != n){ st = UR_DELTA_RANGE; goto done; }
    if (marker_outside(unit, sp, m)){ st = UR_MARKER; goto done; }
    long js = sp[junk].start, je = sp[junk].end;

    /* 2. The grid. The Shuttle's padding always starts on a row boundary of its own line grid (whole units: rows 0, 261,
     *    523), and after a stall it restarts its raster with padding. Padding before the junk must sit on the unit's
     *    grid; padding after it gives the displaced part's grid phase, all blocks agreeing. The displacement is the
     *    value of that phase nearest the length error (one capture's 25:25: the unit stops 8 bytes into its last row,
     *    so the grid sits 8 bytes from the length error). Without padding after the junk the length error is taken
     *    as it is, and the checks below must confirm it. */
    long D = r.delta; int have_phase = 0;
    long pstart[MAX_SPANS];                                  // each padding block's start on its grid (its picture-like edge trimmed)
    long amb_d[MAX_SPANS][2 * GRID_SLACK + 2], amb_s[MAX_SPANS][2 * GRID_SLACK + 2]; int amb[MAX_SPANS], amb_n[MAX_SPANS];   // a block with several possible grids
    for (int i = 0; i < m; i++){
        pstart[i] = sp[i].start; amb[i] = 0; amb_n[i] = 0;
        if (sp[i].kind != S_PAD) continue;
        long len = sp[i].end - sp[i].start, whole = len / L * L;
        if (i < junk){
            /* Before the junk: on the unit's own grid. Its start is a row boundary unless picture just before it is a
             * padding-like sample (Cb128/Y16: 0.2% of row ends): then its end is, if data follows it. */
            if ((sp[i].start - H) % L == 0) continue;
            if (len % L && sp[i].end != js && (sp[i].end - H) % L == 0){ pstart[i] = sp[i].end - whole; continue; }
            st = UR_GRID; goto done;
        }
        /* After the junk. A block's true edges are row boundaries of the displaced grid, but picture that looks like
         * padding (Cb128/Y16 samples, ending about one row in three before the 261 block) joins the run on either side:
         * the run reads early, late, or both. Its true length is whole rows, so a run e bytes over whole rows has its
         * true start somewhere in [start, start + e]. Every grid in that range on whole UYVY pairs (4 bytes) within the
         * slack of the length error is a candidate: one fixes the grid, several leave it to another block (none:
         * declined). A block continuing one the stall interrupted has only its end (late by up to the slack); a block
         * cut by the unit's end has only its start, read only when the run is whole rows or a few bytes short of them
         * (the unit ended early: padding-like picture only lengthens a run; a few bytes long cannot be told from a unit
         * ending late). */
        long cand[2 * GRID_SLACK + 2]; int nc = 0;
        int s_ok = sp[i].start != je, e_ok = sp[i].end != n;
        if (s_ok && e_ok){
            long e = len % L; if (e > 2 * GRID_SLACK){ st = UR_GRID; goto done; }
            for (long j = 0; j <= e; j++) cand[nc++] = sp[i].start + j;
        } else if (s_ok){
            long rem = len % L; if (!rem || rem > GRID_SLACK) cand[nc++] = sp[i].start;
        } else if (e_ok){
            for (long j = 0; j <= GRID_SLACK; j++) cand[nc++] = sp[i].end - j - whole;   // its end (late by j), whole rows back
        }
        long found = 0, fstart = 0; int nf = 0;
        amb_n[i] = 0;
        for (int c = 0; c < nc; c++){
            long ph = ((cand[c] - H) % L + L) % L;
            long off = (((ph - r.delta) % L) + L) % L; if (off > L / 2) off -= L;
            long d = r.delta + off;                                  // the phase's value nearest the length error
            if (d % 4 || off < -GRID_SLACK || off > GRID_SLACK) continue;
            int seen = 0; for (int k = 0; k < amb_n[i]; k++) seen |= amb_d[i][k] == d;
            if (seen) continue;
            amb_d[i][amb_n[i]] = d; amb_s[i][amb_n[i]] = cand[c]; amb_n[i]++;
            found = d; fstart = cand[c]; nf++;
        }
        if (nf >= 2){ amb[i] = 1; continue; }
        if (nf == 0 && nc){ st = UR_GRID; goto done; }           // on no grid the length error allows: not this model
        if (nf != 1) continue;                                   // no edge to read: says nothing
        if (have_phase && found != D){ st = UR_GRID; goto done; }
        D = found; have_phase = 1; pstart[i] = fstart;
    }
    /* Every unit carries padding after any stall (at least its final rows 523-524): without any to give the grid, the
     * bytes do not fix where the displaced part sits (a unit missing its end would land rows low). */
    if (je == n){                                         // junk to the unit's end: nothing displaced
        if (js > (long)U){ st = UR_GRID; goto done; }     // picture past a whole raster: not this model
        have_phase = 1; D = je - (long)U;
    }
    if (!have_phase){ st = UR_GRID; goto done; }
    for (int i = 0; i < m && je != n; i++){
        if (!amb[i]) continue;
        int k = 0; while (k < amb_n[i] && amb_d[i][k] != D) k++;
        if (k == amb_n[i]){ st = UR_GRID; goto done; }
        pstart[i] = amb_s[i][k];
    }
    r.grid_offset = je == n ? 0 : (int)(D - r.delta);
    if (r.grid_offset > GRID_SLACK || r.grid_offset < -GRID_SLACK){ st = UR_GRID; goto done; }
    long t0 = je - D;                                       // where the displaced part starts in the whole raster
    if (t0 < js){ st = UR_GRID; goto done; }               // it would overlap the part in place: not one stall
    if (js > (long)U || t0 > (long)U || js < H){ st = UR_GRID; goto done; }   // outside the raster: not one stall
    r.lost_bytes = t0 - js;
    r.prefix_rows = (unsigned)((js - H) / L); r.suffix_row = (unsigned)((t0 - H + L - 1) / L);

    /* 3. Assemble. Lost bytes: the stall [js,t0); the raster's end past the displaced part; and the lines under padding
     *    the Shuttle wrote in the displaced part away from the padding rows (it did not digitise those lines). The
     *    padding rows are its constant, regenerated. */
    unsigned short lost_lo[UR_ROWS], lost_hi[UR_ROWS];
    for (int k = 0; k < UR_ROWS; k++){ lost_lo[k] = L; lost_hi[k] = 0; }
    #define MARK_LOST(a, b) do { long a_ = (a), b_ = (b); if (a_ < H) a_ = H; if (b_ > (long)U) b_ = U; \
        for (long x = a_; x < b_; ){ int k_ = (int)((x - H) / L); long c_ = (x - H) % L, e_ = (b_ - H) - (long)k_ * L; if (e_ > L) e_ = L; \
            if (c_ < lost_lo[k_]) lost_lo[k_] = (unsigned short)c_; if (e_ > lost_hi[k_]) lost_hi[k_] = (unsigned short)e_; x = H + (long)k_ * L + e_; } } while (0)
    memcpy(out, unit, H);
    memcpy(out + H, unit + H, (size_t)(js - H));
    long tail = n - je; if (t0 + tail > (long)U) tail = U - t0;
    memcpy(out + t0, unit + je, (size_t)tail);
    MARK_LOST(js, t0);
    MARK_LOST(t0 + tail, U);
    int first_post = -1; long restart_next = 0;
    /* A block starting where the stall ended is the rest of the raster's own block that the displaced part resumes in
     * (rows 0-6, 261-269 or 523-524): it must end at that block's end. */
    int r0 = (int)((t0 - H) / L);
    int std_end = r0 < 7 ? 7 : (r0 >= 261 && r0 < 270) ? 270 : r0 >= 523 ? UR_ROWS : -1;
    for (int i = junk + 1; i < m && first_post < 0; i++) if (sp[i].kind == S_PAD) first_post = i;
    for (int i = junk + 1; i < m; i++){
        if (sp[i].kind != S_PAD) continue;
        /* Rows under this block in the whole raster: from its grid start (a block continuing one the stall interrupted
         * starts mid-row: whole rows from its end), whole rows only. A block over the padding rows must sit exactly on
         * them: one landing a row off means the grid is a row off. */
        long a = pstart[i] - D, b = sp[i].end - D;
        int cont = sp[i].start == je && sp[i].end != n, cut = sp[i].end == n;
        if (cont) a = sp[i].start - D;                          // from where the stall ended: its first row is partly covered
        /* A block continuing one the stall interrupted covers its first row only in part: that row is lost too. */
        int k0 = cont ? (int)((a - H) / L) : (int)((a - H + L - 1) / L), k1 = (int)((b - H) / L);
        if (a < H) k0 = 0;
        /* Which padding this is, from the bytes. The Shuttle restarting its raster after a stall writes an 8-row block
         * within two rows of the junk's end (measured: 824 and 1,982 bytes after it), then its next field's 9-row block
         * exactly 262 rows later; the lines under those were never digitised. Any other padding after the junk is the
         * raster's own and must sit exactly on its rows: starting at row 261 (9 rows) or 523 (2 rows, or cut by the
         * unit's end), or, continuing a block the stall interrupted, ending at row 270 or the raster's end. A block
         * anywhere else means the grid is off (a unit missing its end lands rows low): declined. */
        int restart = 0;
        if (i == first_post){
            /* A block starting where the stall ended is never a restart: both measured restarts left decoded data (824 and
             * 1,982 bytes) between the stall and their padding, and a restart the stall ran into cannot be told by its bytes
             * from the rest of one of the raster's own blocks shifted by a short unit. */
            if (!cont) restart = pstart[i] - je <= 2 * L && sp[i].end - pstart[i] == 8 * L;
            if (restart) restart_next = sp[i].end - 8 * L + 262L * L;              // the restart raster's next field block
        } else restart = restart_next && pstart[i] == restart_next && (sp[i].end - pstart[i] == 9 * L || cut);
        if (!restart){
            int ok = cont ? std_end >= 0 && k1 == std_end
                          : (k0 == 261 && k1 == 270) || (k0 == 523 && (cut || k1 == UR_ROWS));
            if (!ok){ st = UR_GRID; goto done; }
            continue;                                            // the raster's own padding: nothing lost under it
        }
        for (int k = k0; k < k1 && k < UR_ROWS; k++){
            if (padding_row(k)) continue;
            MARK_LOST(H + (long)k * L, H + (long)(k + 1) * L);
        }
    }
    #undef MARK_LOST
    uint8_t *rows = out + H;
    unsigned char kept[UR_ROWS], have[UR_ROWS], wait[UR_ROWS];
    int lost_rows = 0;
    for (int k = 0; k < UR_ROWS; k++){
        if (padding_row(k)){
            for (unsigned i = 0; i < L; i += 2){ rows[(size_t)k * L + i] = 0x80; rows[(size_t)k * L + i + 1] = 0x10; }
            kept[k] = 0; have[k] = 1; continue;
        }
        kept[k] = lost_hi[k] <= lost_lo[k]; have[k] = kept[k]; lost_rows += !kept[k];
        if (!kept[k]){ lost_lo[k] &= (unsigned short)~3u; lost_hi[k] = (unsigned short)((lost_hi[k] + 3u) & ~3u); }   // whole UYVY pairs
    }
    if (lost_rows > UR_MAX_REBUILT_ROWS){ st = UR_TOO_MUCH_LOST; goto done; }

    /* 4. Checks on what the bytes placed (never used to place anything; any failure declines). Every picture row kept
     *    must start on the tape's blanking (a few rows may not: deck flags, edits; three in a row may not), the part
     *    displaced must sit on the blanking as the picture beside it does (to a sample: row against the other field's
     *    line at the same height, else the previous unit's row), and no tear may remain. */
    {
        /* Only where this tape's lines start on blanking inside the window: the previous unit's rows, else the rows in
         * place (some tapes put picture at the window's left edge, and then a line start says nothing). */
        int ref_good = 0, ref_n = 0;
        for (int k = 0; k < UR_ROWS; k++){
            if (!picture_row(k) || flag_zone(k)) continue;
            const uint8_t *w = previous ? previous + H + (size_t)k * L : (kept[k] && k < (int)r.prefix_rows ? rows + (size_t)k * L : NULL);
            if (!w) continue;
            int v = line_start_ok(w); if (v < 0) continue;
            ref_n++; ref_good += v;
        }
        int starts = ref_n >= 40 && ref_good * 10 >= ref_n * 9;
        int run = 0, bad = 0, good = 0;
        for (int k = (int)r.suffix_row; starts && k < UR_ROWS; k++){
            if (!kept[k] || !picture_row(k) || flag_zone(k)){ run = 0; continue; }
            int v = line_start_ok(rows + (size_t)k * L);
            if (v < 0){ continue; }
            if (v){ good++; run = 0; } else { bad++; if (++run >= 3){ st = UR_CHECK; goto done; } }
        }
        if (bad * 10 > good + 30){ st = UR_CHECK; goto done; }
        /* The displaced part on the tape's blanking: where the blanking plateau ends (first sample above code 8: picture
         * black sits at setup, ~17) in each displaced picture row against a row at the same height, the other field's
         * line when it is in place, else the same row of the previous unit; the median difference must be within 2
         * samples (clean frames, field against field: within 1 sample in 99.8% of 895, at most 3). */
        int d[UR_ROWS], nd = 0;
        for (int pass = 0; pass < 2 && nd < 20; pass++){
            if (pass == 1){ if (!previous) break; nd = 0; }
            for (int k = (int)r.suffix_row; k < UR_ROWS; k++){
                if (!kept[k] || !picture_row(k) || flag_zone(k)) continue;
                int ek = plateau_end(rows + (size_t)k * L); if (ek < 0) continue;
                int er = -1;
                if (pass == 0){
                    int o1 = k < F2 ? k + 262 : k - 263, o2 = k < F2 ? k + 263 : k - 262;
                    if (o1 >= 0 && o1 < (int)r.prefix_rows && kept[o1] && picture_row(o1)) er = plateau_end(rows + (size_t)o1 * L);
                    if (er < 0 && o2 >= 0 && o2 < (int)r.prefix_rows && kept[o2] && picture_row(o2)) er = plateau_end(rows + (size_t)o2 * L);
                } else er = plateau_end(previous + H + (size_t)k * L);
                if (er >= 0) d[nd++] = ek - er;
            }
        }
        if (nd >= 20){
            for (int i = 1; i < nd; i++) for (int j = i; j > 0 && d[j - 1] > d[j]; j--){ int t = d[j]; d[j] = d[j - 1]; d[j - 1] = t; }
            r.edge_check = d[nd / 2];
            if (d[nd / 2] > 2 || d[nd / 2] < -2){ st = UR_CHECK; goto done; }   // half-samples: more than a sample apart
        }
        else if (r.suffix_row < UR_ROWS){
            /* No blanking edge to read (picture at the window's edge). The picture moves between units (a pan), so
             * the displaced rows are read against the previous unit and must show the motion the rows in place show
             * against it, to a sample. One line's fit is too soft to read on tape picture: each side sums 20 or more
             * rows (whole units, field against field: 29 of 31 at 0; a 2-sample misplacement reads 2 in 27 of 31).
             * With nothing in place to compare (a stall from the top) or no previous unit, the bytes stand alone. */
            if (previous){
                unsigned long long acc[2][17]; int cnt[2] = {0, 0};
                memset(acc, 0, sizeof acc);
                for (int k = 0; k < UR_ROWS; k++){
                    if (!kept[k] || !picture_row(k) || flag_zone(k)) continue;
                    int side = k >= (int)r.suffix_row;
                    if (!side && k >= (int)r.prefix_rows) continue;
                    for (int sft = -8; sft <= 8; sft++) acc[side][sft + 8] += shift_mad(rows + (size_t)k * L, previous + H + (size_t)k * L, sft, 1);
                    cnt[side]++;
                }
                if (cnt[0] >= 20 && cnt[1] >= 20){
                    int bi[2] = {0, 0};
                    for (int sd = 0; sd < 2; sd++) for (int i = 1; i < 17; i++) if (acc[sd][i] < acc[sd][bi[sd]]) bi[sd] = i;
                    r.edge_check = 2 * (bi[1] - bi[0]);
                    if (bi[1] - bi[0] > 1 || bi[1] - bi[0] < -1){ st = UR_CHECK; goto done; }
                }
            }
        }
        if (tear_left(rows, kept)){ st = UR_SECOND_EVENT; goto done; }
        /* Every row against the other field's line beside it, whole frame (the vertical interval and head-switch rows
         * the tear check leaves out included): a block of rows put a whole stretch of samples sideways, as removing the
         * wrong held run would, reads as a clear large shift in row after row. Fields 1/60 s apart rarely move that far;
         * if they do, the unit is declined. */
        {
            int big = 0, seen = 0;
            for (int k = 7; k < UR_ROWS; k++){
                if (padding_row(k) || !kept[k]) continue;
                int o = k < F2 ? k + 262 : k - 263;
                if (o < 0 || o >= UR_ROWS || padding_row(o) || !kept[o]) continue;
                int c, sft = best_shift(rows + (size_t)k * L, rows + (size_t)o * L, &c);
                if (!c) continue;
                seen++; if (sft >= 24 || sft <= -24) big++;
            }
            if (big >= 8 && big * 4 >= seen){ st = UR_CHECK; goto done; }
        }
    }

    /* 5. Rebuild the lost bytes (whole rows, or the lost stretch of a row). Pass 1: an intact line of its kind close by
     *    in its own field (a gap of one or two lines), or the other field's lines above and below. Pass 2 (lost in both
     *    fields at the same height): the previous unit's row when it shows the same picture where both can be seen,
     *    else interpolated down the woven frame. */
    uint8_t tmp[L];
    memset(wait, 0, sizeof wait);
    for (int k = 0; k < UR_ROWS; k++){
        if (have[k]) continue;
        int ap = row_kind(k), lo = k < F2 ? 0 : F2, hi = k < F2 ? F2 : UR_ROWS, u = -1, dd = -1;
        for (int i = k - 1; i >= lo; i--) if (kept[i] && row_kind(i) == ap){ u = i; break; }
        for (int i = k + 1; i < hi; i++) if (kept[i] && row_kind(i) == ap){ dd = i; break; }
        int o1 = k < F2 ? k + 262 : k - 263, o2 = k < F2 ? k + 263 : k - 262;
        int t1 = o1 >= 0 && o1 < UR_ROWS && (k < F2 ? o1 >= F2 : o1 < F2) && kept[o1] && row_kind(o1) == ap;
        int t2 = o2 >= 0 && o2 < UR_ROWS && (k < F2 ? o2 >= F2 : o2 < F2) && kept[o2] && row_kind(o2) == ap;
        if (u >= 0 && dd >= 0 && dd - u <= 3){
            blend(tmp, rows + (size_t)u * L, rows + (size_t)dd * L, (unsigned)(dd - k), (unsigned)(k - u)); r.rebuilt_same_field++;
        } else if (t1 || t2){
            const uint8_t *a1 = rows + (size_t)o1 * L, *a2 = rows + (size_t)o2 * L;
            int ref = u >= 0 && dd >= 0 ? (k - u <= dd - k ? u : dd) : u >= 0 ? u : dd;
            for (int i = 1; ref < 0 && (k - i >= lo || k + i < hi); i++){
                if (k - i >= lo && kept[k - i]) ref = k - i;
                else if (k + i < hi && kept[k + i]) ref = k + i;
            }
            if (t1 && t2 && luma_mad(a1, a2) > 20 && ref >= 0)
                memcpy(tmp, luma_mad(a1, rows + (size_t)ref * L) <= luma_mad(a2, rows + (size_t)ref * L) ? a1 : a2, L);
            else if (t1 && t2) blend(tmp, a1, a2, 1, 1);
            else memcpy(tmp, t1 ? a1 : a2, L);
            r.rebuilt_other_field++;
        } else { wait[k] = 1; continue; }
        memcpy(rows + (size_t)k * L + lost_lo[k], tmp + lost_lo[k], (size_t)(lost_hi[k] - lost_lo[k]));
        r.rebuilt_rows[k < F2 ? 0 : 1]++; have[k] = 1;
    }
    if (previous){
        unsigned sum = 0, cnt = 0;
        for (int k = 0; k < UR_ROWS; k++){
            if (!kept[k] || row_kind(k) != 2) continue;
            int near = 0;
            for (int j = k - 8; j <= k + 8 && !near; j++) near = j >= 0 && j < UR_ROWS && wait[j] && (j < F2) == (k < F2);
            if (near){ sum += luma_mad(rows + (size_t)k * L, previous + H + (size_t)k * L); cnt++; }
        }
        if (cnt < 4 || sum > 8 * cnt) previous = NULL;
    }
    for (int k = 0; k < UR_ROWS; k++){
        if (!wait[k]) continue;
        if (previous){
            memcpy(tmp, previous + H + (size_t)k * L, L); r.rebuilt_previous++;
        } else {
            int ap = row_kind(k), y = frame_line(k), up = -1, dn = -1, yu = 0, yd = 0;
            for (int pass = 0; pass < 2 && (up < 0 || dn < 0); pass++){
                if (pass == 1 && ap == 2) break;
                for (int dy = 1; dy < 2 * UR_ROWS && (up < 0 || dn < 0); dy++){
                    int ru = row_at(y - dy), rd = row_at(y + dy);
                    if (up < 0 && ru >= 0 && have[ru] && !padding_row(ru) && (pass || row_kind(ru) == ap)){ up = ru; yu = y - dy; }
                    if (dn < 0 && rd >= 0 && have[rd] && !padding_row(rd) && (pass || row_kind(rd) == ap)){ dn = rd; yd = y + dy; }
                }
            }
            if (up >= 0 && dn >= 0) blend(tmp, rows + (size_t)up * L, rows + (size_t)dn * L, (unsigned)(yd - y), (unsigned)(y - yu));
            else if (up >= 0 || dn >= 0) memcpy(tmp, rows + (size_t)(up >= 0 ? up : dn) * L, L);
            else { st = UR_NO_SOURCE; goto done; }
            r.rebuilt_same_field++;
        }
        memcpy(rows + (size_t)k * L + lost_lo[k], tmp + lost_lo[k], (size_t)(lost_hi[k] - lost_lo[k]));
        r.rebuilt_rows[k < F2 ? 0 : 1]++;
    }
done:
    r.status = st;
    if (res) *res = r;
    return st;
}

/* Two units in one: a stall that ran over the next unit's marker (its successor carries counter + 2). The bytes before
 * the stall are the first unit's, in place; the bytes after it end at the second unit's end. Each is then the single-unit
 * case: the first a unit whose stall runs to its end, the second a unit stalled from its top, its grid from the
 * Shuttle's restart padding. Placement does not depend on how the two are laid out in the scratch raster: the second
 * unit's displaced part ends at its end, give or take the padding's phase. The stall over the marker is the one stall
 * that leaves no more than a unit after it and no more than a unit and the slack before it (several fitting: declined);
 * each unit is then put back on its own evidence: res[i].status says which, UR_OK returned only when both are. */
ur_status ur_repair2(const uint8_t *unit, size_t count, const uint8_t *previous, uint8_t *scratch, uint8_t *out, ur_result res[2]){
    long n = (long)count, d2 = n - 2L * U;
    span sp[MAX_SPANS]; int m;
    ur_status st = UR_OK;
    memset(res, 0, 2 * sizeof *res);
    if (!unit || !out || !scratch || n < 2L * H || unit[0] || unit[1] || unit[2] != 0xff || unit[3] != 0xff || unit[6] != 0x01 || unit[7] != 0xe8){ st = UR_NOT_A_UNIT; goto fail; }
    if (d2 > UR_MAX_DELTA_BYTES || d2 < -UR_MAX_DELTA_BYTES){ st = UR_DELTA_RANGE; goto fail; }
    if ((m = segment(unit, n, sp)) < 0){ st = UR_SECOND_EVENT; goto fail; }
    /* A stall's own pieces (a fill word, half a word, zeros) less than 16 bytes apart are one, before counting stalls. */
    for (int i = 0; i + 2 < m; i++)
        if (sp[i].kind == S_JUNK && sp[i + 1].kind == S_DATA && sp[i + 2].kind == S_JUNK && sp[i + 1].end - sp[i + 1].start < ZERO_MIN){
            sp[i].end = sp[i + 2].end; memmove(sp + i + 1, sp + i + 3, sizeof(span) * (size_t)(m - i - 3)); m -= 2; i--;
        }
    /* The stall over the marker leaves at most one unit after it (the second unit, stalled from its top) and at most
     * one unit and the slack before it (the first, which may hold a stall of its own): exactly one stall must fit. */
    int k = -1, fits = 0, first = -1;
    for (int i = 0; i < m; i++){
        if (sp[i].kind != S_JUNK) continue;
        if (first < 0) first = i;
        if (sp[i].start <= (long)U + UR_MAX_DELTA_BYTES && n - sp[i].end + H + ZERO_MIN <= (long)U){ fits++; k = i; }
    }
    if (k < 0){ st = UR_NO_FILL; goto fail; }
    if (fits > 1){
        /* Which stall took the marker is not fixed, but everything before the first stall is the first unit's in
         * place either way: it alone can go out (its stall then runs to its end); the second is declined. */
        long js1 = sp[first].start;
        if (js1 > (long)U){ st = UR_SECOND_EVENT; goto fail; }
        memcpy(scratch, unit, (size_t)js1); memset(scratch + js1, 0, (size_t)(U + ZERO_MIN - js1));
        ur_status sa1 = ur_repair(scratch, U + ZERO_MIN, previous, out, &res[0]);
        res[1].status = UR_SECOND_EVENT; res[0].delta = res[1].delta = d2;
        return sa1 != UR_OK ? sa1 : UR_SECOND_EVENT;
    }
    long js = sp[k].start, je = sp[k].end;
    if (k > 0 && sp[k - 1].kind == S_DATA){ long b = word_back(unit, sp[k - 1].start, js); js -= b; }
    if (k + 1 < m && sp[k + 1].kind == S_DATA) je += word_fwd(unit, je, sp[k + 1].end);
    long tail = n - je;
    if (tail + H + ZERO_MIN > (long)U){ st = UR_GRID; goto fail; }        // more after the stall than one unit holds
    /* The first unit: its bytes to the stall, then zeros: at least a unit long, longer when it holds a stall of its own
     * (its bytes then run past a unit's length; the scratch holds a unit and the slack). */
    long alen = js + ZERO_MIN > (long)U + ZERO_MIN ? js + ZERO_MIN : (long)U + ZERO_MIN;
    if (alen > (long)UR_SCRATCH_BYTES){ st = UR_GRID; goto fail; }
    memcpy(scratch, unit, (size_t)js); memset(scratch + js, 0, (size_t)(alen - js));
    ur_status sa = ur_repair(scratch, (size_t)alen, previous, out, &res[0]);
    long z = U + ZERO_MIN - H - tail;
    memcpy(scratch, unit, H); uint16_t c = (uint16_t)(unit[4] | unit[5] << 8); c++;
    scratch[4] = (uint8_t)c; scratch[5] = (uint8_t)(c >> 8);
    memset(scratch + H, 0, (size_t)z); memcpy(scratch + H + z, unit + je, (size_t)tail);
    ur_status sb = ur_repair(scratch, U + ZERO_MIN, sa == UR_OK ? out : NULL, out + U, &res[1]);
    res[0].delta = res[1].delta = d2;
    return sa != UR_OK ? sa : sb;
fail:
    res[0].status = res[1].status = st; res[0].delta = res[1].delta = d2;
    return st;
}

size_t ur_picture_bytes(const uint8_t *unit, size_t count){
    /* Picture never carries a 00 byte (a reserved code: none in any capture); everything the Shuttle writes itself
     * does (a stall's zeros, its stale words, the no-signal raster it writes after losing its input mid-unit). Shown
     * only to the start of the row holding the first. */
    if (!unit || count <= H) return count;
    for (size_t i = H; i < count; i++) if (!unit[i]) return H + (i - H) / L * L;
    return count;
}
