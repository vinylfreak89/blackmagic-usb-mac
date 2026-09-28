// The plugin's media controls, driven as OBS would drive them, against the real frameserver replaying
// the plain synthetic fixture (120 units, counters 0..119; the last complete unit is 118, so the
// timeline is 118 units = 3,937 ms). libobs is replaced by tests_obs_stubs.c; the render thread is
// this test thread (media callbacks and video_tick), the UI getters are called from it as well.
#include "tests_obs_stubs.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

bool obs_module_load(void);
static int fails;
#define CHECK(c, ...) do{ if(!(c)){ fails++; fprintf(stderr,"FAIL: "); fprintf(stderr,__VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
/* bounded wait on a condition OBS's own controls would poll */
#define WAIT(cond, secs, what) do{ double t0_ = now(); while(!(cond) && now() - t0_ < (secs)) usleep(2000); CHECK((cond), "timed out after %g s waiting for %s", (double)(secs), what); }while(0)

int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s fixture_plain.tpc\n", argv[0]); return 9; }
    stub_verbose = getenv("VERBOSE") != NULL;
    obs_module_load();
    const struct obs_source_info *I = stub_info;
    CHECK(I && (I->output_flags & OBS_SOURCE_CONTROLLABLE_MEDIA), "source registered with media controls");
    obs_data_t *st = stub_settings(argv[1], 1);
    void *d = I->create(st, (obs_source_t *)&fails);   /* any non-NULL pointer: the stubs ignore it */
    CHECK(d != NULL, "create");
    if (!d) return 1;

    /* 1. the probe gives the duration; the first run plays to the end and its last frame shows 3,937 ms */
    WAIT(I->media_get_duration(d) > 0, 20, "the replay length");
    CHECK(I->media_get_duration(d) == 3937, "duration %lld ms, expected 3937 (118 units)", (long long)I->media_get_duration(d));
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, 20, "the first run to end");
    CHECK(I->media_get_time(d) == 3937, "time at the end %lld, expected 3937 (unit 118 resolved from its counter)", (long long)I->media_get_time(d));
    CHECK(stub_ended_signals == 1 && stub_started_signals == 1, "signals after one run: started %d ended %d", stub_started_signals, stub_ended_signals);
    CHECK(stub_video_frames == 119, "first run published %llu frames, expected 119 (units 0..118)", (unsigned long long)stub_video_frames);

    /* 2. seek from the ended state to 2,000 ms: a new session from the middle of the file */
    uint64_t f0 = stub_video_frames;
    I->media_set_time(d, 2000);
    WAIT(stub_started_signals == 2, 10, "the seek to start a session");
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, 20, "the seeked run to end");
    uint64_t seeked = stub_video_frames - f0;
    CHECK(seeked > 40 && seeked < 70, "the run from 2,000 ms published %llu frames (from about unit 59-63 of 118)", (unsigned long long)seeked);
    CHECK(I->media_get_time(d) == 3937, "time at the end of the seeked run %lld", (long long)I->media_get_time(d));

    /* 3. restart then pause, queued back to back as a quick double action: held near the start */
    I->media_restart(d); I->media_play_pause(d, true);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, 10, "the pause");
    /* frames already inside the pipeline still arrive (slowly under ThreadSanitizer): wait until none
     * has for 300 ms, then require none for another 300 ms. The whole file plays in about 0.75 s at this
     * pace, so an unheld replay would have ended by then. */
    uint64_t held = stub_video_frames;
    for (double t0 = now(), quiet = now(); now() - t0 < 20 && now() - quiet < 0.3; usleep(5000))
        if (stub_video_frames != held){ held = stub_video_frames; quiet = now(); }
    usleep(300000);
    CHECK(stub_video_frames == held && I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, "frames advanced %llu -> %llu while paused",
          (unsigned long long)held, (unsigned long long)stub_video_frames);
    CHECK(I->media_get_time(d) < 500, "paused at %lld ms, expected near the start", (long long)I->media_get_time(d));

    /* 4. seeks while paused only move the target (OBS's drag); play starts there */
    I->media_set_time(d, 2500); I->media_set_time(d, 3000);
    WAIT(I->media_get_time(d) == 3000, 5, "the pending seek to show");
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, "a seek while paused unpaused the replay");
    int started = stub_started_signals; f0 = stub_video_frames;
    I->media_play_pause(d, false);
    WAIT(stub_started_signals == started + 1, 10, "play to start at the pending seek");
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, 20, "the run from 3,000 ms to end");
    seeked = stub_video_frames - f0;
    CHECK(seeked > 10 && seeked < 35, "the run from 3,000 ms published %llu frames (from about unit 89-95)", (unsigned long long)seeked);

    /* 5. stop */
    I->media_stop(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, 10, "stop");
    CHECK(I->media_get_time(d) == 0, "time after stop %lld", (long long)I->media_get_time(d));

    /* 6. live (no device here, so the capture does not start): controls report STOPPED with no duration,
     * and after an action the next tick re-greys OBS's controls */
    st = stub_settings(argv[1], 0);
    I->update(d, st);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED && I->media_get_duration(d) == 0 && I->media_get_time(d) == 0, "live controls: state %d duration %lld time %lld",
          I->media_get_state(d), (long long)I->media_get_duration(d), (long long)I->media_get_time(d));
    int ended = stub_ended_signals;
    I->media_restart(d); I->video_tick(d, 0.016f);
    CHECK(stub_ended_signals == ended + 1, "live restart was not followed by media_ended on the next tick");
    I->video_tick(d, 0.016f);
    CHECK(stub_ended_signals == ended + 1, "media_ended repeated on a later tick");
    I->media_set_time(d, 1000); I->media_play_pause(d, true);
    usleep(50000);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "live state after pause/seek: %d", I->media_get_state(d));

    /* 7. back to replay, then destroy while it plays: prompt, no hang */
    st = stub_settings(argv[1], 1);
    I->update(d, st);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 10, "replay after live");
    double t0 = now();
    I->destroy(d);
    CHECK(now() - t0 < 3.0, "destroy took %.2f s", now() - t0);
    printf(fails ? "MEDIA CONTROLS: %d FAILURES\n" : "MEDIA CONTROLS PASS\n", fails);
    return fails ? 1 : 0;
}
