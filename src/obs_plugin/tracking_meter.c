#include "tracking_meter.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define W 720
#define FIELD_LINES 240
#define BLK_LINES 8
#define BLK_Y 16                        // luma samples per block; 8 of each chroma channel
#define EDGE_X 32                       // skip the window edges (blanking, edge transients)
#define EDGE_LINES 8                    // and the head-switch / top-of-field disturbance
#define LUMA_LO 40                      // block mean luma outside [LO, HI]: clipping hides the noise
#define LUMA_HI 210
#define PCTL 0.10                       // the flattest 10% of blocks
#define MIN_BLOCKS 40
#define MAX_BLOCKS (((W - 2 * EDGE_X) / BLK_Y) * ((FIELD_LINES - 2 * EDGE_LINES) / BLK_LINES))

// Residual standard deviation of v (bw x BLK_LINES, row stride `stride` elements apart in `step`)
// after removing its least-squares plane.
static double plane_residual_sd(const uint8_t *frame, size_t bpr, int field, int line0, int x0,
                                int bw, int offset, int step){
    double s = 0, sx = 0, sy = 0, ss = 0;
    const double cx = (bw - 1) / 2.0, cy = (BLK_LINES - 1) / 2.0;
    for (int j = 0; j < BLK_LINES; j++){
        const uint8_t *row = frame + (size_t)(2 * (line0 + j) + field) * bpr;
        for (int i = 0; i < bw; i++){
            double v = row[(size_t)(x0 + i) * step + offset];
            s += v; ss += v * v; sx += (i - cx) * v; sy += (j - cy) * v;
        }
    }
    const double n = (double)bw * BLK_LINES;
    double sxx = 0, syy = 0;                                  // sums of squared centred coordinates
    for (int i = 0; i < bw; i++) sxx += (i - cx) * (i - cx);
    sxx *= BLK_LINES;
    for (int j = 0; j < BLK_LINES; j++) syy += (j - cy) * (j - cy);
    syy *= bw;
    double rss = ss - s * s / n - sx * sx / sxx - sy * sy / syy;
    if (rss < 0) rss = 0;
    return sqrt(rss / (n - 3));
}

static int cmp_double(const void *a, const void *b){
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

// Expected low-percentile of a sample standard deviation with `dof` degrees of freedom, as a
// fraction of the true sigma (normal approximation to the chi distribution).
static double pctl_bias(double dof){
    const double z10 = -1.2816;                                // 10th percentile of N(0,1)
    return 1.0 + z10 / sqrt(2.0 * dof);
}

void tm_measure_uyvy(const uint8_t *frame, size_t bpr, tm_frame *out){
    static const int chan_offset[TM_CHANNELS] = { 1, 0, 2 };  // Y in odd bytes; U at 0, V at 2 of each 4
    double *vals = malloc(sizeof(double) * MAX_BLOCKS * TM_CHANNELS);
    memset(out, 0, sizeof *out);
    if (!vals) return;
    int ok = 1;
    for (int f = 0; f < 2; f++){
        unsigned nb = 0;
        double *vy = vals, *vu = vals + MAX_BLOCKS, *vv = vals + 2 * MAX_BLOCKS;
        for (int l = EDGE_LINES; l + BLK_LINES <= FIELD_LINES - EDGE_LINES; l += BLK_LINES)
            for (int x = EDGE_X; x + BLK_Y <= W - EDGE_X; x += BLK_Y){
                double mean = 0;                               // block mean luma: the clipping gate
                for (int j = 0; j < BLK_LINES; j++){
                    const uint8_t *row = frame + (size_t)(2 * (l + j) + f) * bpr;
                    for (int i = 0; i < BLK_Y; i++) mean += row[2 * (x + i) + 1];
                }
                mean /= BLK_Y * BLK_LINES;
                if (mean < LUMA_LO || mean > LUMA_HI) continue;
                vy[nb] = plane_residual_sd(frame, bpr, f, l, x, BLK_Y, chan_offset[TM_Y], 2);
                vu[nb] = plane_residual_sd(frame, bpr, f, l, x / 2, BLK_Y / 2, chan_offset[TM_CB], 4);
                vv[nb] = plane_residual_sd(frame, bpr, f, l, x / 2, BLK_Y / 2, chan_offset[TM_CR], 4);
                nb++;
            }
        out->blocks[f] = nb;
        if (nb < MIN_BLOCKS){ ok = 0; continue; }
        const unsigned k = (unsigned)(PCTL * nb);
        const double dof[TM_CHANNELS] = { BLK_Y * BLK_LINES - 3.0, BLK_Y / 2 * BLK_LINES - 3.0, BLK_Y / 2 * BLK_LINES - 3.0 };
        for (int c = 0; c < TM_CHANNELS; c++){
            double *v = vals + c * MAX_BLOCKS;
            qsort(v, nb, sizeof *v, cmp_double);
            out->noise[f][c] = v[k] / pctl_bias(dof[c]);
        }
    }
    out->valid = ok;
    free(vals);
}

void tm_window_reset(tm_window *w){ memset(w, 0, sizeof *w); }

void tm_window_add(tm_window *w, const tm_frame *f){
    if (!f->valid) return;
    w->recent[w->next] = *f;
    w->next = (w->next + 1) % TM_WINDOW;
    if (w->n < TM_WINDOW) w->n++;
}

static double median_of(double *v, unsigned n){
    qsort(v, n, sizeof *v, cmp_double);
    return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
}

void tm_window_read(const tm_window *w, tm_reading *out){
    memset(out, 0, sizeof *out);
    out->frames = w->n;
    if (w->n == 0) return;
    double v[TM_WINDOW];
    for (int f = 0; f < 2; f++)
        for (int c = 0; c < TM_CHANNELS; c++){
            for (unsigned i = 0; i < w->n; i++) v[i] = w->recent[i].noise[f][c];
            out->noise[f][c] = median_of(v, w->n);
            out->snr_db[f][c] = out->noise[f][c] > 0 ? 20.0 * log10((c == TM_Y ? 219.0 : 224.0) / out->noise[f][c]) : 0;
        }
    for (int c = 0; c < TM_CHANNELS; c++)
        out->ratio[c] = out->noise[0][c] > 0 ? out->noise[1][c] / out->noise[0][c] : 0;
    out->valid = 1;
}
