// Known-answer tests for unit_repair: a synthetic whole unit with the Shuttle's raster structure (padding rows, a dark
// vertical interval, ~20 samples of blanking at code 1-2 starting every picture line, picture at setup and above),
// damaged the ways the device was measured to damage units (2026-11-15). The repair places everything from the bytes:
// rows outside the lost bytes must come back byte-identical, an insertion of the device's fill must come back exactly,
// the lost bytes must be close to the truth, and what the bytes cannot place must be declined.
#include "unit_repair.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { U = UNIT_PARSER_VIDEO_UNIT_BYTES, HB = 48, L = 1440, ROWS = 525 };
static int failures;
#define CHECK(c, ...) do { if (!(c)) { failures++; printf("FAIL %s:%d: ", __FILE__, __LINE__); printf(__VA_ARGS__); puts(""); } } while (0)

static uint32_t rng = 1;
static unsigned rnd(void){ rng = rng * 1664525u + 1013904223u; return rng >> 16; }

static int pad_row(int k){ return k <= 6 || (k >= 261 && k <= 269) || k >= 523; }
static int dark_row(int k){ return (k >= 7 && k <= 18) || (k >= 257 && k <= 260) || (k >= 270 && k <= 281) || (k >= 519 && k <= 522); }

/* Frame line y (0..479) of a smooth picture: the two fields sample one image, so the other field predicts a lost line. */
static double image(int x, double y, int dark){
    double v = 0.5 + 0.35 * sin(x / 37.0 + y / 23.0) + 0.15 * cos(x / 11.0 - y / 41.0);
    return dark ? 18 + 10 * v : 30 + 180 * v;
}
static void make_unit(uint8_t *u, int dark_picture, int flag_top){
    memset(u, 0, HB);
    u[2] = u[3] = 0xff; u[4] = 0x34; u[5] = 0x12; u[6] = 0x01; u[7] = 0xe8;
    for (int k = 0; k < ROWS; k++){
        uint8_t *w = u + HB + (size_t)k * L;
        if (pad_row(k)){ for (int i = 0; i < L; i += 2){ w[i] = 0x80; w[i + 1] = 0x10; } continue; }
        if (dark_row(k)){ for (int i = 0; i < L; i += 2){ w[i] = (uint8_t)(127 + rnd() % 3); w[i + 1] = (uint8_t)(1 + rnd() % 2); } continue; }
        double y = k < 262 ? 2.0 * (k - 19) : 2.0 * (k - 282) + 1;
        int blank = flag_top && k >= 20 && k < 26 ? 0 : 20;            // a top-of-field flag: picture runs to the window edge
        for (int c = 0; c < 720; c++){
            int Y, C = 128 + (int)(18 * sin(c / 29.0 + y / 17.0)) + (int)(rnd() % 3) - 1;
            if (c < blank){ Y = 1 + (int)(rnd() % 2); C = 128 + (int)(rnd() % 9) - 4; }
            else { Y = (int)image(c, y, dark_picture) + (int)(rnd() % 7) - 3; if (Y < 12) Y = 12; if (Y > 235) Y = 235; }
            w[2 * c] = (uint8_t)C; w[2 * c + 1] = (uint8_t)Y;
        }
    }
}
static void make_dark_unit(uint8_t *u){        // sub-blanking black everywhere (a deck without RF)
    make_unit(u, 0, 0);
    for (int k = 0; k < ROWS; k++){ uint8_t *w = u + HB + (size_t)k * L; if (!pad_row(k)) for (int i = 1; i < L; i += 2) w[i] = (uint8_t)(1 + rnd() % 2); }
}

static uint8_t orig[U], odd[U + 2 * 64 * L], out[U];
static size_t n;
static void put(const uint8_t *p, size_t len){ memcpy(odd + n, p, len); n += len; }
static void fill_word(const uint8_t w[4], size_t len){ for (size_t i = 0; i < len; i++) odd[n++] = w[i % 4]; }
static void zeros(size_t len){ memset(odd + n, 0, len); n += len; }
static void dither(size_t len){ for (size_t i = 0; i < len; i += 4){ uint8_t f[4] = {0x5d, (uint8_t)(0xa0 + (i % 12 == 0)), 0x5c, 0xa1}; put(f, 4); } }

/* Rows of out that differ from orig: count, range, and the largest mean absolute difference among picture rows. */
static void compare(int *differ, int *first, int *last, double *worst){
    *differ = 0; *first = -1; *last = -1; *worst = 0;
    CHECK(!memcmp(out, orig, HB), "header changed");
    for (int k = 0; k < ROWS; k++){
        const uint8_t *a = orig + HB + (size_t)k * L, *b = out + HB + (size_t)k * L;
        if (!memcmp(a, b, L)) continue;
        double s = 0; for (int i = 0; i < L; i++) s += abs(a[i] - b[i]);
        s /= L; if (s > *worst && ((k >= 19 && k < 256) || (k >= 282 && k < 518))) *worst = s;
        (*differ)++; if (*first < 0) *first = k; *last = k;
    }
}
static ur_result expect_ok(const char *name, const uint8_t *prev, int max_rows, int lo, int hi, double max_mad){
    ur_result r; ur_status s = ur_repair(odd, n, prev, out, &r);
    CHECK(s == UR_OK, "%s: status %s (grid %+d, lost %ld)", name, ur_status_name(s), r.grid_offset, r.lost_bytes);
    if (s != UR_OK) return r;
    int d, f, l; double w; compare(&d, &f, &l, &w);
    CHECK(d <= max_rows && (d == 0 || (f >= lo && l <= hi)) && w <= max_mad,
          "%s: %d rows differ (%d..%d, allowed %d in %d..%d), worst row MAD %.2f (allowed %.2f)", name, d, f, l, max_rows, lo, hi, w, max_mad);
    printf("  %-36s ok: grid %+d, %6ld bytes lost, rebuilt %3u+%-3u (prev %u), differing rows %3d (%d..%d) worst MAD %.2f\n", name,
           r.grid_offset, r.lost_bytes, r.rebuilt_rows[0], r.rebuilt_rows[1], r.rebuilt_previous, d, f, l, w);
    return r;
}
static void expect_status(const char *name, ur_status want){
    ur_result r; ur_status s = ur_repair(odd, n, NULL, out, &r);
    CHECK(s == want, "%s: status %s, want %s", name, ur_status_name(s), ur_status_name(want));
    printf("  %-36s declined: %s\n", name, ur_status_name(s));
}

int main(void){
    static const uint8_t filler1[4] = {0xaf, 0x8c, 0x00, 0x08}, filler2[4] = {0xa0, 0xad, 0x00, 0x08};
    size_t p, q;

    /* 748 bytes of a line deleted, 524 zeros written there (10:13.25 of one capture). Lost: exactly those 748 bytes. */
    make_unit(orig, 0, 0); n = 0; p = HB + 220 * L + 950;
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    { ur_result r = expect_ok("tear (-224 B, zeros)", NULL, 2, 220, 221, 12);
      CHECK(r.lost_bytes == 748, "tear: %ld bytes lost, want 748", r.lost_bytes); }
    make_unit(orig, 1, 0); n = 0; put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear in a dark scene", NULL, 2, 220, 221, 6);
    make_unit(orig, 0, 1); n = 0; put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear with flagged top lines", NULL, 2, 220, 221, 12);
    make_unit(orig, 0, 0);                                     // picture crushed to blanking level beside it changes nothing
    for (int k = 190; k < 220; k++) for (int c = 590; c <= 640; c++) orig[HB + (size_t)k * L + 2 * c + 1] = 2;
    n = 0; put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear below crushed black", NULL, 2, 220, 221, 12);
    make_dark_unit(orig); n = 0; put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear in sub-blanking black", NULL, 2, 220, 221, 255);
    make_unit(orig, 0, 0); n = 0; p = HB + 257 * L + 700;     // in the head-switch lines
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear in head-switch row 257", NULL, 2, 257, 258, 12);
    make_unit(orig, 0, 0); n = 0; p = HB + 519 * L + 700;
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear in head-switch row 519", NULL, 2, 519, 520, 12);

    /* 512 bytes of the device's dithered fill inserted (10:13.61): removed, the unit comes back exactly. */
    make_unit(orig, 0, 0); n = 0; p = HB + 426 * L + 624;
    put(orig, p); dither(512); put(orig + p, U - p);
    { ur_result r = expect_ok("dithered fill inserted (+512 B)", NULL, 0, 0, 0, 0);
      CHECK(r.lost_bytes == 0, "insert: %ld bytes lost, want 0", r.lost_bytes); }
    make_unit(orig, 0, 0); n = 0; p = HB + 518 * L + 600;
    put(orig, p); dither(512); put(orig + p, U - p);
    expect_ok("dithered fill in head-switch row 518", NULL, 0, 0, 0, 0);
    make_unit(orig, 0, 0); n = 0; p = HB + 200 * L;           // whole lines of zeros inserted: still exact
    put(orig, p); zeros(10 * L); put(orig + p, U - p);
    expect_ok("whole lines of zeros inserted", NULL, 0, 0, 0, 0);

    /* Filler packets then zeros over lines while sync recovers (20:43): unit 23 1/3 lines long. */
    make_unit(orig, 0, 0); n = 0; p = HB + 234 * L + 20; q = p + 113920 + 36580 - 33600;
    put(orig, p); fill_word(filler1, 113920); zeros(36580); put(orig + q, U - q);
    { ur_result r = expect_ok("filler mid-unit (+33,600 B)", NULL, 85, 234, 316, 12);
      CHECK(r.lost_bytes == (long)(q - p), "filler: %ld bytes lost, want %zu", r.lost_bytes, q - p); }

    /* The Shuttle restarting its raster (25:25): filler from row 0, its padding over the lines at field-1 rows 85-92 and
     * at field-2 rows 347-355 (not digitised), and the unit stopping 8 bytes into its last row: placed by the padding's
     * grid, 8 bytes from the length error. With the previous unit, the rows lost in both fields come from it exactly. */
    for (int with_prev = 1; with_prev >= 0; with_prev--){
        make_unit(orig, 0, 0); n = 0; q = HB + 85 * L;
        put(orig, HB + 480); fill_word(filler2, (size_t)(79.47 * L) - 480); zeros(q - 1982 + 33592 - n);
        size_t t = n + 1982; put(orig + q - 1982, U - q + 1982 - 8);           // 1,982 bytes of data before the restart padding (as 127695); ends 8 bytes into its last row
        for (int k = 85; k <= 92; k++){ uint8_t *w = odd + t + (size_t)(k - 85) * L; for (int i = 0; i < L; i += 2){ w[i] = 0x80; w[i + 1] = 0x10; } }
        for (int k = 347; k <= 355; k++){ uint8_t *w = odd + t + (size_t)(k - 85) * L; for (int i = 0; i < L; i += 2){ w[i] = 0x80; w[i + 1] = 0x10; } }
        CHECK(n == U + 33584, "restart length %zu", n);
        ur_result r = expect_ok(with_prev ? "raster restart (previous unit)" : "raster restart (no previous)", with_prev ? orig : NULL, 110, 0, 524, 12);
        CHECK(r.grid_offset == 8, "restart: grid offset %+d, want +8", r.grid_offset);
        if (with_prev){
            int exact = 1; for (int k = 87; k <= 92; k++) exact &= !memcmp(out + HB + (size_t)k * L, orig + HB + (size_t)k * L, L);
            CHECK(r.rebuilt_previous > 0 && exact, "restart: rows lost in both fields not taken exactly from the previous unit (%u rows)", r.rebuilt_previous);
        }
    }
    { static uint8_t other[U]; memcpy(other, orig, U);          // the previous unit is another scene (a cut): not used
      for (int k = 0; k < ROWS; k++) if (!pad_row(k) && !dark_row(k)) for (int i = 2 * 20 + 1; i < L; i += 2) other[HB + (size_t)k * L + i] = (uint8_t)(235 - other[HB + (size_t)k * L + i] / 2);   // picture only: a cut keeps the tape's blanking
      ur_result r = expect_ok("raster restart, previous is a cut", other, 110, 0, 524, 12);
      CHECK(r.rebuilt_previous == 0, "restart: a previous unit of another scene was used (%u rows)", r.rebuilt_previous); }

    /* Review 2026-11-15, each a case the first byte model got wrong or declined. */
    make_unit(orig, 0, 0); n = 0; p = HB + 234 * L + 20; q = p + 113920 + 36580 - 33600;   // picture sample = padding before the restart padding
    orig[HB + 315 * L + 1436] = 0x80; orig[HB + 315 * L + 1437] = 0x10; orig[HB + 315 * L + 1438] = 0x80; orig[HB + 315 * L + 1439] = 0x10;
    put(orig, p); fill_word(filler1, 113920); zeros(36580); put(orig + q, U - q);
    for (int k = 316; k <= 323; k++){ uint8_t *w = odd + HB + (size_t)k * L + 33600; for (int i = 0; i < L; i += 2){ w[i] = 0x80; w[i + 1] = 0x10; } }
    { ur_result r = expect_ok("padding-like sample before restart padding", NULL, 95, 234, 323, 12);
      CHECK(r.grid_offset == 0, "padding-like sample: grid %+d, want 0", r.grid_offset); }
    make_unit(orig, 0, 0); n = 0; p = HB + 100 * L + 624;      // unit about a row short of the raster end: a row off, declined
    put(orig, p); dither(512); put(orig + p, U - p - 1400);
    { ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);
      CHECK(st != UR_OK, "unit a row short accepted (grid %+d)", r.grid_offset); printf("  %-36s declined: %s\n", "unit about a row short", ur_status_name(st)); }
    make_unit(orig, 0, 0); n = 0; p = HB + 234 * L + 20; q = p + 113920 + 36580 - 33600;   // dark picture (Y16-17) ending the row before padding
    for (int c = 700; c < 720; c++){ orig[HB + 315 * L + 2 * c] = 0x84; orig[HB + 315 * L + 2 * c + 1] = 0x11; }
    put(orig, p); fill_word(filler1, 113920); zeros(36580); put(orig + q, U - q);
    for (int k = 316; k <= 323; k++){ uint8_t *w = odd + HB + (size_t)k * L + 33600; for (int i = 0; i < L; i += 2){ w[i] = 0x80; w[i + 1] = 0x10; } }
    expect_ok("dark row end before restart padding", NULL, 95, 234, 323, 12);
    make_unit(orig, 0, 0); n = 0; p = HB + 264 * L + 200;      // a stall inside the padding rows
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear inside padding rows", NULL, 2, 264, 265, 12);
    make_unit(orig, 0, 0); n = 0; p = HB + 234 * L + 20; q = p + 113920 + 2 + 36580 - 33600;   // fill, half a word, zeros: one stall
    put(orig, p); fill_word(filler1, 113920); fill_word(filler1, 2); zeros(36580); put(orig + q, U - q);
    expect_ok("fill, half a word, zeros", NULL, 85, 234, 316, 12);

    make_unit(orig, 0, 0); n = 0; p = HB + 300 * L + 624;      // junk in field 2, unit a row short: the end block lands a row off
    put(orig, p); dither(512); put(orig + p, U - p - 1440);
    { ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);
      CHECK(st != UR_OK, "field-2 junk, unit a row short, accepted (grid %+d)", r.grid_offset); printf("  %-36s declined: %s\n", "field-2 junk, unit a row short", ur_status_name(st)); }
    make_unit(orig, 0, 0); n = 0; p = HB + 426 * L + 624;      // a picture sample at Y16 right before padding is not junk
    orig[HB + 522 * L + 1437] = 16; orig[HB + 522 * L + 1439] = 16;
    put(orig, p); dither(512); put(orig + p, U - p);
    expect_ok("Y16 sample before the end padding", NULL, 0, 0, 0, 0);

    make_unit(orig, 0, 0); n = 0; q = HB + 150 * L;             // a stall running into the restart padding (no fragment between)
    put(orig, HB + 60 * L + 20); fill_word(filler1, 113920); zeros(q + 33600 - n + 8);
    { size_t t = n; put(orig + q + 8, U - q - 8);
      for (size_t i = t; i < t + 8 * L - 8; i += 2){ odd[i] = 0x80; odd[i + 1] = 0x10; } }
    { ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);   // never measured, and not tellable from a shifted standard block
      CHECK(st != UR_OK, "stall running straight into restart padding accepted"); printf("  %-36s declined: %s\n", "stall running into restart padding", ur_status_name(st)); }
    make_unit(orig, 0, 0); n = 0; p = HB + 300 * L + 624;      // field-2 junk, the unit missing its whole final padding
    put(orig, p); dither(512); put(orig + p, U - p - 2880);
    { ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);
      CHECK(st != UR_OK, "no padding after the junk, accepted"); printf("  %-36s declined: %s\n", "no padding after the junk", ur_status_name(st)); (void)r; }

    for (int short_rows = 9; short_rows <= 15; short_rows += 3){   // unit missing 9-15 rows at its end: the 261 block lands rows off
        make_unit(orig, 0, 0); n = 0; p = HB + 100 * L + 624;
        put(orig, p); dither(512); put(orig + p, U - p - (size_t)short_rows * L);
        ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);
        CHECK(st != UR_OK, "unit %d rows short accepted (grid %+d)", short_rows, r.grid_offset);
        if (short_rows == 9) printf("  %-36s declined: %s\n", "unit 9-15 rows short", ur_status_name(st));
    }

    for (int t2 = 0; t2 < 12; t2++){                              // a stall inside padding rows (row 2 / 263), unit 2-40 rows short
        static const int shorts[6] = {2, 6, 15, 16, 24, 40}; int short_rows = shorts[t2 % 6];
        make_unit(orig, 0, 0); n = 0; p = HB + (t2 < 6 ? 263 : 2) * L + 300;
        put(orig, p); zeros(524); put(orig + p + 748, U - p - 748 - (size_t)short_rows * L);
        ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);
        CHECK(st != UR_OK, "stall in padding, unit %d rows short, accepted (grid %+d)", short_rows, r.grid_offset);
        if (t2 == 0) printf("  %-36s declined: %s\n", "stall in padding, unit 2-40 rows short", ur_status_name(st));
    }

    for (int short_rows = 2; short_rows <= 8; short_rows += 3){   // a tear from picture row 260 running into the 261 padding, unit short
        make_unit(orig, 0, 0); n = 0; p = HB + 260 * L + 1000;
        put(orig, p); zeros(524); put(orig + p + 748, U - p - 748 - (size_t)short_rows * L);
        ur_result r; ur_status st = ur_repair(odd, n, NULL, out, &r);
        CHECK(st != UR_OK, "tear into the 261 padding, unit %d rows short, accepted", short_rows);
        if (short_rows == 2) printf("  %-36s declined: %s\n", "tear into 261 padding, unit short", ur_status_name(st));
    }
    make_unit(orig, 0, 0); n = 0; p = HB + 260 * L + 1000;       // ... and not short: repaired
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear into the 261 padding", NULL, 2, 260, 261, 12);

    /* Declines: what the bytes cannot place. */
    make_unit(orig, 0, 0); n = 0; p = HB + 220 * L + 950;     // bytes gone with no fill to say where
    put(orig, p); put(orig + p + 224, U - p - 224);
    expect_status("deletion without fill", UR_NO_FILL);
    make_unit(orig, 0, 0); n = 0;                             // two stalls
    put(orig, HB + 100 * L + 500); zeros(300); put(orig + HB + 100 * L + 1024, 200 * L - 524); zeros(300);
    put(orig + HB + 300 * L + 1024, U - (HB + 300 * L + 1024));
    expect_status("two stretches of fill", UR_SECOND_EVENT);
    make_unit(orig, 0, 0); n = 0; p = HB + 220 * L + 950;     // padding after the junk off the displaced grid
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    for (size_t i = HB + 300 * L + 100; i < HB + 301 * L + 100; i += 2){ odd[i] = 0x80; odd[i + 1] = 0x10; }
    expect_status("padding off the grid", UR_GRID);
    make_unit(orig, 0, 0); n = 0; p = HB + 100 * L;           // noise over the rest: no fill, nothing to place
    put(orig, p); while (n < U + 33600) odd[n++] = (uint8_t)(1 + rnd() % 254);
    expect_status("noise after line 100", UR_NO_FILL);
    make_unit(orig, 0, 0); n = 0; put(orig, U); zeros(65 * L + 100);
    expect_status("longer than one unit", UR_DELTA_RANGE);
    make_unit(orig, 0, 0); n = 0; put(orig, U);
    expect_status("whole unit", UR_NOT_A_UNIT);
    make_unit(orig, 0, 0); n = 0; put(orig, U - 224); odd[7] = 0x08; odd[6] = 0x00;
    expect_status("no-signal format", UR_NOT_A_UNIT);

    puts(failures ? "unit_repair tests: FAIL" : "unit_repair tests: PASS");
    return failures != 0;
}
