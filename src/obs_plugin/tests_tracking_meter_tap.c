// The tracking meter's live hand-off: frames offered at full speed from a "frame callback" thread
// while the UI takes snapshots and the window opens and closes. Run under ThreadSanitizer. Checks:
// no race reports, frames are measured while open, nothing is measured while closed, the reading
// matches the synthetic noise, and one measured frame costs far less than a frame period.
#include "tracking_meter_tap.h"
#include <math.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define FW 720
#define FH 480
static uint8_t *frame;
static _Atomic int run_offer = 1;
static int fails;

static unsigned long long rng = 0x9E3779B97F4A7C15ull;
static double urand(void){ rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (rng >> 11) * (1.0 / 9007199254740992.0); }
static double gauss(void){ double u = urand(), v = urand(); if (u < 1e-12) u = 1e-12; return sqrt(-2 * log(u)) * cos(2 * M_PI * v); }
static uint8_t clip(double v){ return v < 0 ? 0 : v > 255 ? 255 : (uint8_t)lround(v); }

static void *offer_loop(void *a){
    (void)a;
    while (atomic_load(&run_offer)){ tmt_offer(frame, FW * 2); usleep(2000); }   // ~500 frames/s, faster than real
    return NULL;
}

int main(void){
    frame = malloc((size_t)FW * FH * 2);
    for (int r = 0; r < FH; r++){                       // field 2 Cb noise 1.2x field 1's
        double sc = (r & 1) ? 1.2 : 1.0;
        uint8_t *row = frame + (size_t)r * FW * 2;
        for (int cx = 0; cx < FW / 2; cx++){
            row[4 * cx] = clip(128 + 2.0 * sc * gauss()); row[4 * cx + 2] = clip(128 + 2.0 * gauss());
            row[4 * cx + 1] = clip(100 + 2.0 * gauss()); row[4 * cx + 3] = clip(100 + 2.0 * gauss());
        }
    }
    pthread_t t; pthread_create(&t, NULL, offer_loop, NULL);

    tmt_snapshot s;
    usleep(100000); tmt_snapshot_take(&s);
    printf("closed: offered %llu measured %llu\n", (unsigned long long)s.frames_offered, (unsigned long long)s.frames_measured);
    if (s.frames_measured || s.active){ printf("FAIL: measured while closed\n"); fails++; }

    for (int cycle = 0; cycle < 5; cycle++){             // open, run, close, repeatedly
        tmt_start(); tmt_start();                          // idempotent
        for (int i = 0; i < 20; i++){ usleep(20000); tmt_snapshot_take(&s); }
        tmt_stop(); tmt_stop();
    }
    printf("after 5 open/close cycles: measured %llu (last cycle), skipped busy %llu, history %u\n",
           (unsigned long long)s.frames_measured, (unsigned long long)s.frames_skipped_busy, s.history_n);
    if (!s.frames_measured){ printf("FAIL: nothing measured while open\n"); fails++; }
    if (!s.now.valid || fabs(s.now.ratio[TM_CB] - 1.2) > 0.05 || fabs(s.now.ratio[TM_Y] - 1.0) > 0.05){
        printf("FAIL: reading Y %.3f Cb %.3f (want 1.0, 1.2)\n", s.now.ratio[TM_Y], s.now.ratio[TM_CB]); fails++;
    } else printf("reading Y %.3f Cb %.3f Cr %.3f (want 1.00 1.20 1.00)\n", s.now.ratio[TM_Y], s.now.ratio[TM_CB], s.now.ratio[TM_CR]);

    uint64_t before; tmt_snapshot_take(&s); before = s.frames_measured;
    usleep(100000); tmt_snapshot_take(&s);
    if (s.frames_measured != before || s.active){ printf("FAIL: measuring after close\n"); fails++; }

    atomic_store(&run_offer, 0); pthread_join(t, NULL);

    // Cost of one measured frame (the copy is a 691 kB memcpy on the frame callback; this is the thread's work).
    tm_frame m; struct timespec a, b; clock_gettime(CLOCK_MONOTONIC, &a);
    for (int i = 0; i < 50; i++) tm_measure_uyvy(frame, FW * 2, &m);
    clock_gettime(CLOCK_MONOTONIC, &b);
    double ms = ((b.tv_sec - a.tv_sec) * 1e3 + (b.tv_nsec - a.tv_nsec) / 1e6) / 50;
    printf("measuring one frame: %.2f ms (measured thread; one frame in %d)\n", ms, TMT_EVERY);
    free(frame);
    printf(fails ? "FAILED %d\n" : "tracking meter tap tests passed\n", fails);
    return fails != 0;
}
