// Known-answer tests for the tracking meter: a picture with flat areas, edges and texture, the same
// in both fields, with chosen noise added to each field and channel. The meter must report the
// chosen noise and, above all, the chosen field 2 / field 1 ratio.
#include "tracking_meter.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FW 720
#define FH 480
static unsigned long long rng = 88172645463325252ull;
static double urand(void){ rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (rng >> 11) * (1.0 / 9007199254740992.0); }
static double gauss(void){ double u = urand(), v = urand(); if (u < 1e-12) u = 1e-12; return sqrt(-2 * log(u)) * cos(2 * M_PI * v); }
static uint8_t clip(double v){ return v < 0 ? 0 : v > 255 ? 255 : (uint8_t)lround(v); }

// Picture: smooth gradients, a few hard-edged rectangles and a textured band, identical per field
// line (field 2's line n shows what field 1's line n shows, one raster line lower).
static double pic_y(int x, int line){
    double v = 60 + 100.0 * x / FW + 30.0 * line / 240;
    if (x > 100 && x < 260 && line > 40 && line < 120) v = 190;
    if (x > 400 && x < 640 && line > 150 && line < 200) v = 45 + 25 * sin(x * 0.7) * sin(line * 0.9);   // texture
    if (x > 300 && x < 330) v = 230;                                                                    // a bright bar (clipped area)
    return v;
}
static double pic_c(int cx, int line, int which){ return 128 + (which ? 20 : -15) * sin(cx * 0.01 + line * 0.02) + (cx > 50 && cx < 130 && line > 40 && line < 120 ? (which ? 40 : -30) : 0); }

static void make_frame(uint8_t *f, const double sd[2][3]){
    for (int r = 0; r < FH; r++){
        int field = r & 1, line = r >> 1;
        uint8_t *row = f + (size_t)r * FW * 2;
        for (int cx = 0; cx < FW / 2; cx++){
            row[4 * cx + 0] = clip(pic_c(cx, line, 0) + sd[field][1] * gauss());
            row[4 * cx + 1] = clip(pic_y(2 * cx, line) + sd[field][0] * gauss());
            row[4 * cx + 2] = clip(pic_c(cx, line, 1) + sd[field][2] * gauss());
            row[4 * cx + 3] = clip(pic_y(2 * cx + 1, line) + sd[field][0] * gauss());
        }
    }
}

static int fails;
static void check(const char *what, double got, double want, double tol){
    int ok = fabs(got - want) <= tol * want;
    printf("  %-34s got %6.3f  want %6.3f  %s\n", what, got, want, ok ? "ok" : "FAIL");
    if (!ok) fails++;
}

int main(void){
    uint8_t *f = malloc((size_t)FW * FH * 2);
    const double cases[][2][3] = {
        { {1.8, 2.0, 1.6}, {1.8, 2.0, 1.6} },          // balanced
        { {1.8, 2.0, 1.6}, {1.94, 2.3, 1.89} },        // field 2 worse: Y +8%, Cb +15%, Cr +18% (the bars clip)
        { {2.0, 3.0, 2.0}, {2.0, 3.6, 2.6} },          // a bad head: Cb +20%, Cr +30%
        { {2.2, 3.1, 2.4}, {2.0, 2.7, 2.2} },          // field 1 the worse one
    };
    for (unsigned c = 0; c < sizeof cases / sizeof *cases; c++){
        tm_window w; tm_window_reset(&w);
        for (int i = 0; i < TM_WINDOW; i++){
            make_frame(f, cases[c]);
            tm_frame m; tm_measure_uyvy(f, FW * 2, &m);
            if (!m.valid){ printf("case %u frame %d: not valid (blocks %u/%u)\n", c, i, m.blocks[0], m.blocks[1]); fails++; }
            tm_window_add(&w, &m);
        }
        tm_reading r; tm_window_read(&w, &r);
        printf("case %u (%u frames):\n", c, r.frames);
        const char *ch[3] = { "Y", "Cb", "Cr" };
        for (int k = 0; k < 3; k++){
            char what[64];
            snprintf(what, sizeof what, "%s ratio field 2 / field 1", ch[k]);
            check(what, r.ratio[k], cases[c][1][k] / cases[c][0][k], 0.03);
            snprintf(what, sizeof what, "%s noise field 1 (codes)", ch[k]);
            check(what, r.noise[0][k], cases[c][0][k], 0.08);
        }
    }
    // An all-black frame (nothing between the clipping gates) must say "can't tell", not "balanced".
    memset(f, 16, (size_t)FW * FH * 2);
    tm_frame m; tm_measure_uyvy(f, FW * 2, &m);
    printf("black frame: valid=%d (want 0)\n", m.valid);
    if (m.valid) fails++;
    free(f);
    printf(fails ? "FAILED %d\n" : "all tracking meter tests passed\n", fails);
    return fails != 0;
}
