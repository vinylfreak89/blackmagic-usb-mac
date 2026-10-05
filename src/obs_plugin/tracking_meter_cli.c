// tracking_meter_cli: the tracking meter over published frames read from stdin, for checking it
// against captures with known answers. Feed it what the frameserver publishes:
//   frameserver_replay <capture.tpc> --dump-uyvy /dev/stdout --limit-units N [--start-offset B] | tracking_meter_cli [every]
// Frames are 720x480 TFF UYVY (691200 bytes). Every `every`-th frame is measured (default 1, the
// plugin measures one frame in 4); a reading is printed after each 30 frames read and at the end.
#include "tracking_meter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FRAME_BYTES (720 * 480 * 2)

static void print_reading(unsigned long long frames, const tm_window *w){
    tm_reading r; tm_window_read(w, &r);
    if (!r.valid){ printf("%7llu frames  no reading (too little flat picture between black and white)\n", frames); return; }
    printf("%7llu frames  ratio f2/f1  Y %.3f  Cb %.3f  Cr %.3f   noise f1 %.2f %.2f %.2f  f2 %.2f %.2f %.2f codes  (%u frames)\n",
           frames, r.ratio[TM_Y], r.ratio[TM_CB], r.ratio[TM_CR],
           r.noise[0][TM_Y], r.noise[0][TM_CB], r.noise[0][TM_CR], r.noise[1][TM_Y], r.noise[1][TM_CB], r.noise[1][TM_CR], r.frames);
    fflush(stdout);
}

int main(int argc, char **argv){
    unsigned every = argc > 1 ? (unsigned)atoi(argv[1]) : 1;
    if (every < 1) every = 1;
    uint8_t *buf = malloc(FRAME_BYTES);
    tm_window w; tm_window_reset(&w);
    size_t cap = 1 << 16, nall = 0; double (*all)[2][TM_CHANNELS] = malloc(sizeof *all * cap);   /* every valid frame, for the overall median */
    unsigned long long frames = 0, measured = 0, invalid = 0;
    while (fread(buf, 1, FRAME_BYTES, stdin) == FRAME_BYTES){
        if (frames % every == 0){
            tm_frame m; tm_measure_uyvy(buf, 720 * 2, &m);
            measured++; if (!m.valid) invalid++;
            tm_window_add(&w, &m);
            if (m.valid && nall < cap) memcpy(all[nall++], m.noise, sizeof m.noise);
        }
        frames++;
        if (frames % 30 == 0) print_reading(frames, &w);
    }
    if (frames % 30) print_reading(frames, &w);
    if (nall){                                   /* overall: median of each per-frame figure */
        double *v = malloc(sizeof *v * nall), med[2][TM_CHANNELS];
        for (int f = 0; f < 2; f++) for (int c = 0; c < TM_CHANNELS; c++){
            for (size_t i = 0; i < nall; i++) v[i] = all[i][f][c];
            for (size_t i = 1; i < nall; i++){ double x = v[i]; size_t j = i; while (j && v[j-1] > x){ v[j] = v[j-1]; j--; } v[j] = x; }
            med[f][c] = nall % 2 ? v[nall/2] : 0.5 * (v[nall/2-1] + v[nall/2]); }
        printf("OVERALL %zu frames  ratio f2/f1  Y %.3f  Cb %.3f  Cr %.3f\n", nall, med[1][0]/med[0][0], med[1][1]/med[0][1], med[1][2]/med[0][2]);
        free(v);
    }
    free(all);
    fprintf(stderr, "frames %llu, measured %llu, no reading %llu\n", frames, measured, invalid);
    free(buf);
    return frames ? 0 : 1;
}
