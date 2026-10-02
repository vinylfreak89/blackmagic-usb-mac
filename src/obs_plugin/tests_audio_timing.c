#include "audio_timing.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    /* audio: the publisher's time, untouched, whatever the residual does */
    shuttle_audio_clock a = {0}; uint64_t t;
    ap_block b = {.pts_num = 80080};
    assert(shuttle_audio_time(&a, &b, &t) == 0 && t == 80080);
    b.pts_num += 1601 * 5; b.correlation_residual = 4865;                 /* the counter ran ahead of the samples */
    assert(shuttle_audio_time(&a, &b, &t) == 0 && t == 80080 + 1601 * 5 && a.residual_steps == 1);
    b.pts_num += 1602 * 5; b.correlation_residual = 4868;                 /* quantization is not a step */
    assert(shuttle_audio_time(&a, &b, &t) == 0 && t == 80080 + 3203 * 5 && a.residual_steps == 1);
    b.pts_num += 800 * 5; b.correlation_residual = 4868 + 4000000;        /* a wind: thousands of counts, no time */
    assert(shuttle_audio_time(&a, &b, &t) == 0 && t == 80080 + 4003 * 5 && a.residual_steps == 2);
    b.flags = AP_FLAG_UNANCHORED | AP_FLAG_DISCONTINUITY_BEFORE;          /* not placed yet: not published */
    assert(shuttle_audio_time(&a, &b, &t) == -1);
    b.flags = 0; b.pts_num = 999990; b.correlation_residual = 0;          /* a new run starts a new comparison */
    assert(shuttle_audio_time(&a, &b, &t) == 0 && t == 999990 && a.residual_steps == 2);

    /* video: the unit's audio-clock time when known */
    shuttle_video_clock v = {0}; int est;
    assert(shuttle_video_time(&v, 1, 500000, 8008, 123, &est) == 500000 && !est);
    assert(shuttle_video_time(&v, 1, 508005, 8008, 123, &est) == 508005 && !est);      /* 1601 samples later, not 8008 ticks */
    /* a wind: the counter races, the audio clock does not; frames follow the audio clock */
    assert(shuttle_video_time(&v, 1, 508005 + 3740, 4004, 123, &est) == 511745 && !est);
    /* not known: one nominal period after the last, and marked */
    assert(shuttle_video_time(&v, 0, 0, 8008, 123, &est) == 519753 && est);
    /* the estimate ran ahead of the next known time: time does not go back */
    assert(shuttle_video_time(&v, 1, 519000, 8008, 123, &est) == 519754 && !est);
    assert(shuttle_video_time(&v, 1, 527761, 8008, 123, &est) == 527761);
    /* the first frame of a session with no audio time yet takes the fallback, never zero */
    { shuttle_video_clock w = {0}; assert(shuttle_video_time(&w, 0, 0, 8008, 777, &est) == 777 && est); }
    puts("audio timing: PASS (audio untouched by residual steps, unplaced blocks held, video on the audio clock, estimates, no step back)");
}
