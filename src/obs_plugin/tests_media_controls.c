// The plugin's media controls, driven as OBS would drive them, against the real frameserver replaying
// the plain synthetic fixture (120 units, counters 0..119; the last complete unit is 118, so the
// timeline is 118 units = 3,937 ms). libobs is replaced by tests_obs_stubs.c; the render thread is
// this test thread (media callbacks and video_tick), the UI getters are called from it as well.
#include "tests_obs_stubs.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <CoreFoundation/CoreFoundation.h>

bool obs_module_load(void);
void shuttle_test_device_gone(void *d);
int shuttle_test_reconnect_wanted(void *d);
unsigned shuttle_test_reconnect_tries(void *d);
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
    stub_source = (obs_source_t *)&fails;   /* any non-NULL pointer stands for the source */
    void *d = I->create(st, stub_source);
    CHECK(d != NULL, "create");
    if (!d) return 1;
    stub_data = d;

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

#if !defined(__has_feature) || !__has_feature(thread_sanitizer)
    /* A pause is not a delivery stall: resuming must not report the held time as a late handoff. Not under
     * TSan: there the pipeline runs so far behind the pacer that frames are genuinely late, and the file
     * is read to its end before the second pause could hold it. */
    int late = stub_late_reports;
    I->media_play_pause(d, false);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING && stub_video_frames > held + 5, 10, "resume");
    usleep(200000);
    CHECK(stub_late_reports == late, "resuming after a 600 ms pause logged %d late-handoff warnings", stub_late_reports - late);
    I->media_play_pause(d, true);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, 10, "the second pause");
#endif

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

    /* 4b. a record press whose output fails to start: RECORDING_STARTING stops the replay (actions in that
     * blank gap are ignored), restart_check (main queue) finds no active output and resumes the replay with
     * restart_pending still set. From there the controls must act; before the fix they were ignored. */
    stub_restart_on_record(1);
    I->media_restart(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 10, "playing before the record press");
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STARTING);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "RECORDING_STARTING left state %d", I->media_get_state(d));
    started = stub_started_signals;
    for (double t0 = now(); stub_started_signals == started && now() - t0 < 10; ) CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.05, false);
    CHECK(stub_started_signals == started + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "restart_check did not resume the replay");
    I->media_play_pause(d, true);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, 5, "a pause after a failed record press");
    I->media_stop(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, 5, "a stop after a failed record press");
    started = stub_started_signals;
    I->media_restart(d);   /* stopped, restart_pending still set: the controls must still act */
    WAIT(stub_started_signals == started + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 5, "a restart after stop, after a failed record press");
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STOPPED);

    /* 4c. the same through streaming (the discard stream): STREAMING_STARTING stops the replay, restart_check
     * finds no active streaming output and resumes it, and STREAMING_STOPPED ends the session. */
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 10, "playing before the stream press");
    stub_fire_event(OBS_FRONTEND_EVENT_STREAMING_STARTING);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "STREAMING_STARTING left state %d", I->media_get_state(d));
    started = stub_started_signals;
    for (double t0 = now(); stub_started_signals == started && now() - t0 < 10; ) CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.05, false);
    CHECK(stub_started_signals == started + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "restart_check did not resume the replay after a stream press");
    /* 4d. while the stream owns the session, a record press is ignored: the replay keeps playing */
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STARTING);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "a record press during the stream changed the replay (state %d)", I->media_get_state(d));
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STOPPED);
    stub_fire_event(OBS_FRONTEND_EVENT_STREAMING_STOPPED);
    /* 4e. after the stream stopped, a record press acts again */
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STARTING);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "a record press after the stream stopped was ignored (state %d)", I->media_get_state(d));
    started = stub_started_signals;
    for (double t0 = now(); stub_started_signals == started && now() - t0 < 10; ) CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.05, false);
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STOPPED);
    stub_restart_on_record(0);

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
    I->video_tick(d, 0.016f);   /* the switch from replay armed one re-grey: consume it first */
    int ended = stub_ended_signals;
    I->video_tick(d, 0.016f);
    CHECK(stub_ended_signals == ended, "a tick with no live action emitted media_ended");
    I->update(d, st); I->video_tick(d, 0.016f);   /* live to live: nothing to grey */
    CHECK(stub_ended_signals == ended, "a live-to-live settings update emitted media_ended");
    I->media_restart(d); I->video_tick(d, 0.016f);
    CHECK(stub_ended_signals == ended + 1, "live restart was not followed by media_ended on the next tick");
    I->video_tick(d, 0.016f);
    CHECK(stub_ended_signals == ended + 1, "media_ended repeated on a later tick");   /* sanity only: the live-to-live update above decides the arming */
    I->media_set_time(d, 1000); I->media_play_pause(d, true);
    usleep(50000);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "live state after pause/seek: %d", I->media_get_state(d));

    /* 6a. live, the device drops off USB (reported as the capture core does). There is no device here, so every
     * reconnect attempt fails: the picture is blanked at once, attempts repeat (RECONNECT_INTERVAL_NS is 20 ms in
     * this build) and stop after the limit; a second disconnect then a user stop cancels the attempts. */
    {
        uint64_t blanks = stub_blank_calls;
        shuttle_test_device_gone(d);
        CHECK(stub_blank_calls == blanks + 1, "a disconnect did not blank the source (%llu blank calls)", (unsigned long long)(stub_blank_calls - blanks));
        CHECK(shuttle_test_reconnect_wanted(d), "a disconnect did not start reconnecting");
        WAIT(shuttle_test_reconnect_tries(d) >= 30, 10, "timed reconnect attempts to stop after the limit (30 x 20 ms)");
        usleep(200000);
        CHECK(shuttle_test_reconnect_tries(d) == 30, "attempts went on past the limit: %u", shuttle_test_reconnect_tries(d));
        CHECK(shuttle_test_reconnect_wanted(d), "after the limit it should still wait for the device to come back");
        shuttle_test_device_gone(d);
        CHECK(shuttle_test_reconnect_wanted(d), "a second disconnect did not keep reconnecting");
        I->media_stop(d);
        WAIT(!shuttle_test_reconnect_wanted(d), 2, "a user stop to cancel reconnecting");
        I->update(d, st);
    }

    /* 6b. a replay path that cannot be opened: the previous file's length does not stay on the bar */
    st = stub_settings(argv[1], 1);
    I->update(d, st);
    WAIT(I->media_get_duration(d) == 3937, 10, "the fixture's length again");
    ended = stub_ended_signals;
    st = stub_settings("/nonexistent/volume/capture.tpc", 1);
    I->update(d, st);
    CHECK(I->media_get_duration(d) == 0 && stub_ended_signals == ended + 1, "after a failed replay start: duration %lld, ended signals +%d",
          (long long)I->media_get_duration(d), stub_ended_signals - ended);

    /* 7. back to replay, then destroy while it plays: prompt, no hang */
    st = stub_settings(argv[1], 1);
    I->update(d, st);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 10, "replay after live");
    double t0 = now();
    I->destroy(d);
#if defined(__has_feature) && __has_feature(thread_sanitizer)
    const double destroy_bound = 60;   /* fs_stop drains the pipeline's backlog, which TSan's slow workers let grow */
#else
    const double destroy_bound = 3;
#endif
    CHECK(now() - t0 < destroy_bound, "destroy took %.2f s", now() - t0);
    CHECK(stub_frame_errors == 0, "%llu frames handed to OBS were not I210 4c with the expected planes", (unsigned long long)stub_frame_errors);
    printf(fails ? "MEDIA CONTROLS: %d FAILURES\n" : "MEDIA CONTROLS PASS\n", fails);
    return fails ? 1 : 0;
}
