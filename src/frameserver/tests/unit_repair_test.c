// Known-answer tests for unit_repair: a synthetic whole unit with the Shuttle's raster structure (padding rows, a dark
// vertical interval, ~20 samples of blanking at code 1-2 starting every picture line, picture at setup and above),
// damaged the ways the device was measured to damage units (2026-11-15), must come back with every row outside the
// damage byte-identical and the damaged rows close to the truth; units the evidence cannot settle must be declined.
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
static void make_dark_unit(uint8_t *u){        // sub-blanking black everywhere (a deck without RF): no evidence
    make_unit(u, 0, 0);
    for (int k = 0; k < ROWS; k++){ uint8_t *w = u + HB + (size_t)k * L; if (!pad_row(k)) for (int i = 1; i < L; i += 2) w[i] = (uint8_t)(1 + rnd() % 2); }
}

static uint8_t orig[U], odd[U + 2 * 64 * L], out[U];
static size_t n;
static void put(const uint8_t *p, size_t len){ memcpy(odd + n, p, len); n += len; }
static void fill_word(const uint8_t w[4], size_t len){ for (size_t i = 0; i < len; i++) odd[n++] = w[i % 4]; }
static void zeros(size_t len){ memset(odd + n, 0, len); n += len; }

/* Rows of out that differ from orig: count, range, and the largest mean absolute difference among them. */
static void compare(int *differ, int *first, int *last, double *worst){
    *differ = 0; *first = -1; *last = -1; *worst = 0;
    CHECK(!memcmp(out, orig, HB), "header changed");
    for (int k = 0; k < ROWS; k++){
        const uint8_t *a = orig + HB + (size_t)k * L, *b = out + HB + (size_t)k * L;
        if (!memcmp(a, b, L)) continue;
        double s = 0; for (int i = 0; i < L; i++) s += abs(a[i] - b[i]);
        /* Judged on picture rows: the synthetic's head-switch and vertical-interval rows are arbitrary (dark here,
         * mostly picture on tape), so what a rebuilt one should hold is not known. */
        s /= L; if (s > *worst && ((k >= 19 && k < 256) || (k >= 282 && k < 518))) *worst = s;
        (*differ)++; if (*first < 0) *first = k; *last = k;
    }
}
static void expect_ok(const char *name, int max_rows, int lo, int hi, double max_mad){
    ur_result r; ur_status s = ur_repair(odd, n, out, &r);
    CHECK(s == UR_OK, "%s: status %s (a %u b %u agree %d/%d disagree %d/%d)", name, ur_status_name(s), r.prefix_rows, r.suffix_row,
          r.prefix_agree, r.suffix_agree, r.prefix_disagree, r.suffix_disagree);
    if (s != UR_OK) return;
    int d, f, l; double w; compare(&d, &f, &l, &w);
    CHECK(d <= max_rows && (d == 0 || (f >= lo && l <= hi)) && w <= max_mad,
          "%s: %d rows differ (%d..%d, allowed %d in %d..%d), worst row MAD %.2f (allowed %.2f)", name, d, f, l, max_rows, lo, hi, w, max_mad);
    CHECK((int)(r.rebuilt_rows[0] + r.rebuilt_rows[1]) >= d, "%s: %u+%u rebuilt but %d rows differ", name, r.rebuilt_rows[0], r.rebuilt_rows[1], d);
    printf("  %-34s ok: a %3u b %3u rebuilt %3u+%-3u (same %u other %u), differing rows %d (%d..%d) worst MAD %.2f\n", name,
           r.prefix_rows, r.suffix_row, r.rebuilt_rows[0], r.rebuilt_rows[1], r.rebuilt_same_field, r.rebuilt_other_field, d, f, l, w);
}
static void expect_status(const char *name, ur_status want){
    ur_result r; ur_status s = ur_repair(odd, n, out, &r);
    CHECK(s == want, "%s: status %s, want %s (a %u b %u agree %d/%d)", name, ur_status_name(s), ur_status_name(want), r.prefix_rows, r.suffix_row,
          r.prefix_agree, r.suffix_agree);
    printf("  %-34s declined: %s\n", name, ur_status_name(s));
}

int main(void){
    static const uint8_t filler1[4] = {0xaf, 0x8c, 0x00, 0x08}, filler2[4] = {0xa0, 0xad, 0x00, 0x08};
    size_t p, q;

    /* Bytes deleted inside a line, zeros over part of it (10:13.25 of one capture: 748 bytes of line 224 gone, 524 zeros). */
    make_unit(orig, 0, 0); n = 0; p = HB + 220 * L + 950;
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    CHECK(n == U - 224, "tear length");
    expect_ok("tear (-224 B, zeros)", 3, 219, 222, 12);

    /* The same in a dark scene: picture black sits at setup, still above blanking, so the parts are still told apart. */
    make_unit(orig, 1, 0); n = 0; p = HB + 220 * L + 950;
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear in a dark scene", 3, 219, 222, 6);

    /* Samples inserted inside a line (10:13.61: 256 samples of flat colour in line 430). */
    make_unit(orig, 0, 0); n = 0; p = HB + 426 * L + 624;
    put(orig, p);
    for (int i = 0; i < 128; i++){ uint8_t f[4] = {0x5d, (uint8_t)(0xa0 + (i % 3 == 0)), 0x5c, 0xa1}; put(f, 4); }
    put(orig + p, U - p);
    CHECK(n == U + 512, "insert length");
    expect_ok("flat insert (+512 B)", 1, 426, 426, 12);

    /* Filler over lines while sync recovers (20:43): 40 packets of a repeating word, zeros, unit 23 1/3 lines long. */
    make_unit(orig, 0, 0); n = 0; p = HB + 234 * L + 20; q = p + 113920 + 36580 - 33600;
    put(orig, p); fill_word(filler1, 113920); zeros(36580); put(orig + q, U - q);
    CHECK(n == U + 33600, "filler length");
    expect_ok("filler mid-unit (+33,600 B)", 110, 233, 340, 12);

    /* Filler from the first row, and the Shuttle's padding written over field-2 rows 345-353 (25:25). */
    make_unit(orig, 0, 0); n = 0; q = HB + 85 * L;
    put(orig, HB + 480); fill_word(filler2, (size_t)(79.47 * L) - 480); zeros(q + 33584 - n);
    put(orig + q, U - q);
    CHECK(n == U + 33584, "filler-start length %zu", n);
    for (int k = 345; k <= 353; k++){ uint8_t *w = odd + HB + (size_t)k * L + 33584; for (int i = 0; i < L; i += 2){ w[i] = 0x80; w[i + 1] = 0x10; } }
    expect_ok("filler at start + misplaced padding", 100, 0, 353, 12);

    /* A top-of-field flag (picture to the window edge on lines 24-29) is real picture: kept as it came. */
    make_unit(orig, 0, 1); n = 0; p = HB + 220 * L + 950;
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_ok("tear with flagged top lines", 3, 219, 222, 12);

    /* Picture crushed to blanking level next to the damage (a Y=2 object on the 30 rows above it, where the displaced
     * line start lands): those rows read as picture at both offsets and must not move the split (review 2026-11-15:
     * the first version published 32 torn rows). They are rebuilt; nothing torn is published. */
    for (int y = 2; y <= 8; y += 6){
        make_unit(orig, 0, 0);
        for (int k = 190; k < 220; k++) for (int c = 590; c <= 640; c++) orig[HB + (size_t)k * L + 2 * c + 1] = (uint8_t)y;
        n = 0; p = HB + 220 * L + 950;
        put(orig, p); put(orig + p + 224, U - p - 224);
        expect_ok(y == 2 ? "tear below crushed black (Y=2)" : "tear below dark object (Y=8)", 40, 185, 222, 12);
    }

    /* Damage inside the head-switch lines, which carry no line-start evidence: rebuilt, not published as read. */
    make_unit(orig, 0, 0); n = 0; p = HB + 257 * L + 700;
    put(orig, p); put(orig + p + 224, U - p - 224);
    expect_ok("tear in head-switch row 257", 40, 250, 290, 12);
    make_unit(orig, 0, 0); n = 0; p = HB + 519 * L + 700;
    put(orig, p); put(orig + p + 224, U - p - 224);
    expect_ok("tear in head-switch row 519", 12, 512, 524, 12);
    make_unit(orig, 0, 0); n = 0; p = HB + 518 * L + 600;
    put(orig, p); for (int i = 0; i < 128; i++){ uint8_t f[4] = {0x5d, 0xa1, 0x5c, 0xa0}; put(f, 4); } put(orig + p, U - p);
    expect_ok("flat insert in head-switch row 518", 12, 512, 524, 12);

    /* Declines. */
    make_unit(orig, 0, 0); n = 0;                         // two length errors: rows between them are displaced by half
    put(orig, HB + 100 * L + 500); put(orig + HB + 100 * L + 724, 200 * L - 224); put(orig + HB + 300 * L + 724, U - (HB + 300 * L + 724));
    CHECK(n == U - 448, "two-event length %zu", n);
    { ur_result r; ur_status st = ur_repair(odd, n, out, &r);
      /* Declined, or put back with nothing displaced published: every rebuilt row has intact other-field sources here. */
      if (st == UR_OK){ int d, f, l; double w; compare(&d, &f, &l, &w);
          CHECK(w <= 12, "two length errors: accepted with a displaced row published (worst MAD %.2f, rows %d..%d)", w, f, l);
          printf("  %-34s ok: a %u b %u, differing rows %d (%d..%d) worst MAD %.2f\n", "two length errors", r.prefix_rows, r.suffix_row, d, f, l, w); }
      else printf("  %-34s declined: %s\n", "two length errors", ur_status_name(st)); }
    /* Two errors with picture crushed to blanking level where the rows between them are misread (review round 2): their
     * line starts read as picture at delta, so only the other field shows them displaced. */
    make_unit(orig, 0, 0);
    for (int k = 150; k <= 200; k++) for (int c = 590; c <= 640; c++) orig[HB + (size_t)k * L + 2 * c + 1] = 2;
    n = 0; put(orig, HB + 150 * L + 500); put(orig + HB + 150 * L + 724, 50 * L - 224); put(orig + HB + 200 * L + 724, U - (HB + 200 * L + 724));
    CHECK(n == U - 448, "crushed two-event length %zu", n);
    { ur_result r; ur_status st = ur_repair(odd, n, out, &r); int d = 0, f = 0, l = 0; double w = 0;
      if (st == UR_OK) compare(&d, &f, &l, &w);
      CHECK(st != UR_OK || w <= 12, "two errors under crushed black: accepted with displaced rows (MAD %.2f, rows %d..%d)", w, f, l);
      printf("  %-34s %s\n", "two errors under crushed black", st == UR_OK ? "ok, nothing displaced" : ur_status_name(st)); }
    make_unit(orig, 0, 0); n = 0;                         // ...and with the second error further on, too much is between them
    put(orig, HB + 100 * L + 500); put(orig + HB + 100 * L + 724, 300 * L - 224); put(orig + HB + 400 * L + 724, U - (HB + 400 * L + 724));
    { ur_result r; ur_status st = ur_repair(odd, n, out, &r); int d = 0, f = 0, l = 0; double w = 0;
      if (st == UR_OK) compare(&d, &f, &l, &w);
      CHECK(st != UR_OK || w <= 12, "two length errors 300 rows apart: accepted with a displaced row (MAD %.2f)", w);
      printf("  %-34s %s\n", "two errors 300 rows apart", st == UR_OK ? "ok, nothing displaced" : ur_status_name(st)); }

    make_unit(orig, 0, 0); n = 0; p = HB + 200 * L;
    put(orig, p); zeros(10 * L); put(orig + p, U - p);
    expect_status("whole lines inserted", UR_WHOLE_LINE_DELTA);

    make_dark_unit(orig); n = 0; p = HB + 220 * L + 950;
    put(orig, p); zeros(524); put(orig + p + 748, U - p - 748);
    expect_status("tear in sub-blanking black", UR_NO_EVIDENCE);

    make_unit(orig, 0, 0); n = 0; p = HB + 100 * L;
    put(orig, p); while (n < U + 33600) odd[n++] = (uint8_t)rnd();
    { ur_result r; ur_status st = ur_repair(odd, n, out, &r);
      CHECK(st == UR_TOO_MUCH_LOST || st == UR_NO_EVIDENCE, "noise after line 100: status %s", ur_status_name(st));
      printf("  %-34s declined: %s\n", "noise after line 100", ur_status_name(st)); }

    make_unit(orig, 0, 0); n = 0; put(orig, U); zeros(65 * L + 100);
    expect_status("longer than one unit", UR_DELTA_RANGE);

    make_unit(orig, 0, 0); n = 0; put(orig, U);
    expect_status("whole unit", UR_NOT_A_UNIT);

    make_unit(orig, 0, 0); n = 0; put(orig, U - 224); odd[7] = 0x08; odd[6] = 0x00;
    expect_status("no-signal format", UR_NOT_A_UNIT);

    puts(failures ? "unit_repair tests: FAIL" : "unit_repair tests: PASS");
    return failures != 0;
}
