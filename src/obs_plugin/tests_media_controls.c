// The plugin's media controls, driven as OBS would drive them, against the real frameserver replaying
// the plain synthetic fixture (120 units, counters 0..119; the last complete unit is 118, so the
// timeline is 118 units = 3,937 ms). libobs is replaced by tests_obs_stubs.c; the render thread is
// this test thread (media callbacks and video_tick), the UI getters are called from it as well.
#include "tests_obs_stubs.h"
#include "capture_core.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <CoreFoundation/CoreFoundation.h>

bool obs_module_load(void);
void shuttle_test_device_gone(void *d);
int shuttle_test_reconnect_wanted(void *d);
unsigned shuttle_test_reconnect_tries(void *d);
void shuttle_test_power(void *d, unsigned msg);
int shuttle_test_asleep(void *d);
void shuttle_test_full_wake(void *d);
extern int shuttle_test_power_acks, shuttle_test_ack_with_session, shuttle_test_sleep_replays, shuttle_test_display_on;
static int fails;
#define CHECK(c, ...) do{ if(!(c)){ fails++; fprintf(stderr,"FAIL: "); fprintf(stderr,__VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
/* bounded wait on a condition OBS's own controls would poll */
/* lines the failure paths below must log (counted, not printed: tests_obs_stubs.c) */
static const char *const L_REC_IDLE = "the recording output is not active after the press";
static const char *const L_STREAM_IDLE = "the streaming output is not active after the press";
static const char *const L_OWNED = "recording started while the stream owns the raw file and sidecar";
static const char *const L_OPEN = "frameserver open failed";
static const char *const L_RESTART = "capture restart failed";
static const char *const L_GONE = "disconnected (USB connection lost)";
static const char *const L_GAVE_UP = "could not reconnect to the Shuttle after 30 attempts";
static const char *const L_NOFILE = "replay file cannot be opened";
static const char *const L_SLEEP = "the Mac is going to sleep: stopping the Shuttle session";
static const char *const L_HELD = "the Mac is asleep: the Shuttle session starts when it wakes";
static const char *const L_WOKE = "the Mac woke";
#define WAIT(cond, secs, what) do{ double t0_ = now(); while(!(cond) && now() - t0_ < (secs)) usleep(2000); CHECK((cond), "timed out after %g s waiting for %s", (double)(secs), what); }while(0)

int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s fixture_plain.tpc\n", argv[0]); return 9; }
    stub_verbose = getenv("VERBOSE") != NULL;
    setenv("SHUTTLE_SOURCE_NO_SPILL_RECOVERY", "1", 1);   /* the load starts spill recovery: not on this user's scratch */
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
    stub_expect(L_REC_IDLE); stub_expect(L_STREAM_IDLE); stub_expect(L_OWNED);
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
    { int r = stub_expect_end(L_REC_IDLE), t = stub_expect_end(L_STREAM_IDLE), o = stub_expect_end(L_OWNED);   /* 4b + 4e; 4c; 4d */
      CHECK(r == 2 && t == 1 && o == 1, "failed-press warnings: recording %d (want 2), stream %d (want 1), owned %d (want 1)", r, t, o); }

    /* 5. stop */
    I->media_stop(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, 10, "stop");
    CHECK(I->media_get_time(d) == 0, "time after stop %lld", (long long)I->media_get_time(d));

    /* 6. live (no device here, so the capture does not start): controls report STOPPED with no duration,
     * and after an action the next tick re-greys OBS's controls */
    stub_expect(L_OPEN); stub_expect(L_RESTART);
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
    { int o = stub_expect_end(L_OPEN), r = stub_expect_end(L_RESTART);   /* two live updates and a restart, no device */
      CHECK(o == 3 && r == 1, "live without a device: %d open failures (want 3), %d restart failures (want 1)", o, r); }
    /* the USB stack drop-down reaches capture_core's config: unset and "libusb" select libusb, "iousbhost" IOUSBHost
     * (each update is another refused live start, after the count above) */
    CHECK(shuttle_test_usb_backend == CC_USB_LIBUSB, "unset USB stack selected %d, not libusb", shuttle_test_usb_backend);
    stub_usb_backend("iousbhost"); I->update(d, st);
    CHECK(shuttle_test_usb_backend == CC_USB_IOUSBHOST, "\"iousbhost\" selected %d, not IOUSBHost", shuttle_test_usb_backend);
    stub_usb_backend("libusb"); I->update(d, st);
    CHECK(shuttle_test_usb_backend == CC_USB_LIBUSB, "\"libusb\" selected %d, not libusb", shuttle_test_usb_backend);
    stub_usb_backend(NULL);

    /* 6a. live, the device drops off USB (reported as the capture core does). There is no device here, so every
     * reconnect attempt fails: the picture is blanked at once, attempts repeat (RECONNECT_INTERVAL_NS is 20 ms in
     * this build) and stop after the limit; a second disconnect then a user stop cancels the attempts. */
    {
        uint64_t blanks = stub_blank_calls;
        stub_expect(L_OPEN); stub_expect(L_GONE); stub_expect(L_GAVE_UP);
        shuttle_test_device_gone(d);
        CHECK(stub_blank_calls == blanks + 1, "a disconnect did not blank the source (%llu blank calls)", (unsigned long long)(stub_blank_calls - blanks));
        CHECK(shuttle_test_reconnect_wanted(d), "a disconnect did not start reconnecting");
        WAIT(shuttle_test_reconnect_tries(d) >= 30, 10, "timed reconnect attempts to stop after the limit (30 x 20 ms)");
        usleep(200000);
        CHECK(shuttle_test_reconnect_tries(d) == 30, "attempts went on past the limit: %u", shuttle_test_reconnect_tries(d));
        CHECK(shuttle_test_reconnect_wanted(d), "after the limit it should still wait for the device to come back");
        { int o = stub_expect_end(L_OPEN), g = stub_expect_end(L_GONE), u = stub_expect_end(L_GAVE_UP);   /* one per attempt; one disconnect; one give-up */
          CHECK(o == 30 && g == 1 && u == 1, "reconnecting: %d open failures (want 30), %d disconnects (want 1), %d give-ups (want 1)", o, g, u); }
        /* while it is already reconnecting a second disconnect logs nothing new; attempts made before the stop
         * lands depend on timing, and the update afterwards tries the device once more */
        stub_expect(L_OPEN); stub_expect(L_GONE); stub_expect(L_GAVE_UP);
        shuttle_test_device_gone(d);
        CHECK(shuttle_test_reconnect_wanted(d), "a second disconnect did not keep reconnecting");
        I->media_stop(d);
        WAIT(!shuttle_test_reconnect_wanted(d), 2, "a user stop to cancel reconnecting");
        I->update(d, st);
        { int o = stub_expect_end(L_OPEN), g = stub_expect_end(L_GONE), u = stub_expect_end(L_GAVE_UP);
          CHECK(o >= 1 && g == 0 && u <= 1, "after the second disconnect: %d open failures (want at least 1), %d disconnect lines (want 0), %d give-ups (want at most 1)", o, g, u); }
    }

    /* 6c. system sleep (IOKit's messages, as power_cb receives them; NSWorkspace's wake notifications reach the same
     * power_wake). A running session is stopped and the picture blanked BEFORE the sleep is acknowledged; a replay
     * stands in for the live session (no device here), and a real replay is left running. A wake counts only with the
     * main display on (shuttle_test_display_on stands for it): HasPoweredOn also comes on the dark wakes a Mac makes
     * with its lid shut, and a wake notification can be late. A user action ends the sleep. */
    {
        enum { CAN_SLEEP = 0xe0000270, WILL_SLEEP = 0xe0000280, WILL_NOT_SLEEP = 0xe0000290, POWERED_ON = 0xe0000300 };
        shuttle_test_display_on = 0;
        st = stub_settings(argv[1], 1); I->update(d, st);
        WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 10, "a session to put to sleep");
        stub_expect(L_SLEEP); stub_expect(L_WOKE);
        int acks = shuttle_test_power_acks, with = shuttle_test_ack_with_session; uint64_t blanks = stub_blank_calls;
        shuttle_test_sleep_replays = 1;
        shuttle_test_power(d, CAN_SLEEP);
        CHECK(shuttle_test_power_acks == acks + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "an idle-sleep query was not allowed, or it stopped the session");
        shuttle_test_power(d, WILL_SLEEP);
        CHECK(shuttle_test_power_acks == acks + 2, "the sleep was not acknowledged");
        CHECK(shuttle_test_ack_with_session == with + 1, "the sleep was acknowledged while a session was still running (%d of 2 acks with a session; only the query may)", shuttle_test_ack_with_session - with);
        CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED && shuttle_test_asleep(d), "after WillSleep: state %d, asleep %d", I->media_get_state(d), shuttle_test_asleep(d));
        CHECK(stub_blank_calls == blanks + 1, "the sleep stop did not blank the picture (%llu blank calls)", (unsigned long long)(stub_blank_calls - blanks));
        uint64_t f = stub_video_frames;
        shuttle_test_power(d, POWERED_ON);   /* a dark wake: display off */
        shuttle_test_full_wake(d);           /* a wake notification that arrives with the display off: stale */
        usleep(200000);
        CHECK(shuttle_test_asleep(d) && stub_video_frames == f, "a dark or stale wake ended the sleep (asleep %d) or frames arrived (%llu)", shuttle_test_asleep(d), (unsigned long long)(stub_video_frames - f));
        shuttle_test_power(d, WILL_SLEEP);   /* back to sleep: nothing left to stop */
        CHECK(shuttle_test_power_acks == acks + 3 && shuttle_test_ack_with_session == with + 1, "the second sleep was not acknowledged cleanly");
        CHECK(stub_expect_count(L_WOKE) == 0, "a wake was logged before the display came on");
        shuttle_test_display_on = 1;
        shuttle_test_full_wake(d);
        CHECK(!shuttle_test_asleep(d) && stub_expect_count(L_WOKE) == 1, "the full wake (display on) did not end the sleep (asleep %d, %d wake lines)", shuttle_test_asleep(d), stub_expect_count(L_WOKE));
        CHECK(stub_expect_end(L_SLEEP) == 1, "the sleep stop was not logged once");
        shuttle_test_sleep_replays = 0;
        /* IOKit's power-on with the display on ends a sleep too (a sleep aborted after WillSleep) */
        shuttle_test_power(d, WILL_SLEEP); shuttle_test_power(d, POWERED_ON);
        CHECK(!shuttle_test_asleep(d), "power-on with the display on left the source asleep");
        stub_expect_end(L_WOKE);
        /* a real replay keeps running through a sleep; a refused idle-sleep query (WillNotSleep) changes nothing */
        I->update(d, st);
        WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, 10, "a replay before a sleep");
        shuttle_test_power(d, CAN_SLEEP); shuttle_test_power(d, WILL_NOT_SLEEP);
        CHECK(!shuttle_test_asleep(d) && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "a refused sleep query changed the source");
        acks = shuttle_test_power_acks;
        shuttle_test_power(d, WILL_SLEEP);
        CHECK(shuttle_test_power_acks == acks + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "a sleep stopped a replay, or was not acknowledged");
        shuttle_test_full_wake(d);
        /* live, the device drops off USB while asleep: no attempt through a dark wake, attempts after the full wake */
        st = stub_settings(argv[1], 0);
        stub_expect(L_OPEN); stub_expect(L_GONE); stub_expect(L_GAVE_UP);
        I->update(d, st);                      /* one refused live start */
        shuttle_test_power(d, WILL_SLEEP);
        shuttle_test_device_gone(d);
        shuttle_test_display_on = 0; shuttle_test_power(d, POWERED_ON);   /* a dark wake */
        usleep(300000);
        CHECK(stub_expect_end(L_OPEN) == 1, "reconnect attempts ran while asleep or in a dark wake");
        stub_expect(L_OPEN);
        shuttle_test_display_on = 1; shuttle_test_full_wake(d);
        WAIT(stub_expect_count(L_OPEN) >= 1, 5, "a reconnect attempt after the full wake");
        I->media_stop(d);
        WAIT(!shuttle_test_reconnect_wanted(d), 2, "a user stop to cancel reconnecting after the wake");
        { int o = stub_expect_end(L_OPEN), g = stub_expect_end(L_GONE), u = stub_expect_end(L_GAVE_UP);
          CHECK(o >= 1 && g == 1 && u == 0, "after the wake: %d open failures (want at least 1), %d disconnects (want 1), %d give-ups (want 0)", o, g, u); }
        /* a missed wake: a user action proves the Mac is awake. A settings change while "asleep" starts at once (not held),
         * a restart likewise, and a stop clears the sleep so a later wake restarts nothing. */
        stub_expect(L_OPEN); stub_expect(L_HELD); stub_expect(L_RESTART);
        shuttle_test_power(d, WILL_SLEEP);
        I->update(d, st);
        CHECK(!shuttle_test_asleep(d) && stub_expect_count(L_OPEN) == 1 && stub_expect_count(L_HELD) == 0, "a settings change while asleep: asleep %d, %d opened (want 1), %d held (want 0)", shuttle_test_asleep(d), stub_expect_count(L_OPEN), stub_expect_count(L_HELD));
        shuttle_test_power(d, WILL_SLEEP);
        I->media_restart(d);
        WAIT(stub_expect_count(L_OPEN) == 2, 5, "a restart while asleep to try the device at once");
        CHECK(!shuttle_test_asleep(d) && stub_expect_count(L_HELD) == 0, "a restart while asleep: asleep %d, %d held", shuttle_test_asleep(d), stub_expect_count(L_HELD));
        shuttle_test_power(d, WILL_SLEEP);
        I->media_stop(d);
        WAIT(!shuttle_test_asleep(d), 5, "a stop while asleep to end the sleep");
        shuttle_test_full_wake(d);
        usleep(200000);
        CHECK(stub_expect_count(L_OPEN) == 2 && !shuttle_test_reconnect_wanted(d), "a wake after a user stop restarted something (%d opens)", stub_expect_count(L_OPEN));
        { int o = stub_expect_end(L_OPEN), h = stub_expect_end(L_HELD), r = stub_expect_end(L_RESTART);
          CHECK(o == 2 && h == 0 && r == 1, "user actions while asleep: %d opens (want 2), %d held (want 0), %d restart failures (want 1)", o, h, r); }
        shuttle_test_display_on = 0;
    }

    /* 6b. a replay path that cannot be opened: the previous file's length does not stay on the bar */
    st = stub_settings(argv[1], 1);
    I->update(d, st);
    WAIT(I->media_get_duration(d) == 3937, 10, "the fixture's length again");
    ended = stub_ended_signals;
    stub_expect(L_NOFILE); stub_expect(L_OPEN);
    st = stub_settings("/nonexistent/volume/capture.tpc", 1);
    I->update(d, st);
    { int n = stub_expect_end(L_NOFILE), o = stub_expect_end(L_OPEN);
      CHECK(n == 1 && o == 0, "unopenable replay: %d file errors (want 1), %d open failures (want 0: it stops before opening)", n, o); }
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
    obs_module_unload();                                   /* joins what the load started */
    printf(fails ? "MEDIA CONTROLS: %d FAILURES\n" : "MEDIA CONTROLS PASS\n", fails);
    return fails ? 1 : 0;
}
