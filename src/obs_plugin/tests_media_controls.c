// The plugin's media controls, driven as OBS would drive them, against the real frameserver replaying
// the plain synthetic fixture (120 units, counters 0..119; the last complete unit is 118, so the
// timeline is 118 units = 3,937 ms). libobs is replaced by tests_obs_stubs.c; the render thread is
// this test thread (media callbacks and video_tick), the UI getters are called from it as well.
#include "tests_obs_stubs.h"
#include "capture_core.h"
#include "../test_supervisor.h"
#include <util/platform.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <CoreFoundation/CoreFoundation.h>

bool obs_module_load(void);
void shuttle_test_device_gone(void *d);
void shuttle_test_device_closed(void *d);
extern int shuttle_test_open_rc, shuttle_test_close_during_open;
int shuttle_test_reconnect_wanted(void *d);
unsigned shuttle_test_reconnect_tries(void *d);
void shuttle_test_power(void *d, unsigned msg);
int shuttle_test_asleep(void *d);
void shuttle_test_full_wake(void *d);
extern int shuttle_test_power_acks, shuttle_test_ack_with_session, shuttle_test_sleep_replays, shuttle_test_display_on;
int shuttle_test_replay_held(void *d);
extern void (*shuttle_test_on_late)(uint64_t prev_ns, uint64_t t0_ns);
extern void (*shuttle_test_on_applied)(void);
extern unsigned shuttle_test_resume_delay_us;
static int fails;
#define CHECK(c, ...) do{ if(!(c)){ fails++; fprintf(stderr,"FAIL: "); fprintf(stderr,__VA_ARGS__); fprintf(stderr,"\n"); } }while(0)
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
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
/* Wait for a state. Wakes on every progress event (a frame handed to OBS, a media signal, a log line, an applied media
 * action); the 10 ms re-check covers state stored just after its event (a worker counter set once the sink returns).
 * Fails only when NOTHING has moved for MC_TEST_STALL_S (default 60 s): a dead pipeline, never a slow one. The
 * ThreadSanitizer build spends ~270 ms of worker CPU per unit (2026-11-26), so a run of the 118-unit fixture takes
 * 35-50 s; a total-time limit per step measured the machine, not the plugin. The whole run is bounded separately
 * (test_supervise, MC_TEST_TOTAL_S). A failed wait stops the test: every later step would fail from it. */
static double stall_s(void){ const char *v = getenv("MC_TEST_STALL_S"); double x = v ? strtod(v, NULL) : 60; return x > 0 ? x : 60; }
static void wait_failed(const char *what, double idle){
    fails++; fprintf(stderr, "FAIL: nothing progressed for %.1f s while waiting for %s (stopping: later steps depend on it)\n", idle, what);
    printf("MEDIA CONTROLS: %d FAILURES\n", fails); fflush(NULL); _exit(1);
}
#define WAIT_WITH(cond, what, block) do{ double last_ = now(); uint64_t g_ = stub_progress_gen(); \
    while(!(cond)){ block; uint64_t h_ = stub_progress_gen(); if (h_ != g_){ g_ = h_; last_ = now(); } else if (now() - last_ >= stall_s()) wait_failed(what, now() - last_); } }while(0)
#define WAIT(cond, what) WAIT_WITH(cond, what, (void)stub_progress_wait(g_, 0.01))
/* the same, running the main queue meanwhile (restart_check is dispatched to it) */
#define WAIT_MAIN(cond, what) WAIT_WITH(cond, what, CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.01, true))
/* the resume check: a reported handoff gap that runs from before the resume press to after it timed the pause */
static _Atomic uint64_t g_resume_ns = UINT64_MAX; static _Atomic int g_pause_timed;
static _Atomic int g_destroyed;
static void *destroy_thread(void *d){ stub_info->destroy(d); stub_progress(); atomic_store(&g_destroyed, 1); stub_progress(); return NULL; }
static void on_late(uint64_t prev_ns, uint64_t t0_ns){ uint64_t r = atomic_load(&g_resume_ns); if (prev_ns < r && t0_ns >= r) atomic_fetch_add(&g_pause_timed, 1); }

int main(int argc, char **argv){
    if (argc < 2){ fprintf(stderr, "usage: %s fixture_plain.tpc [repair_many.tpc]\n", argv[0]); return 9; }
    test_supervise(argv, "MC_TEST_TOTAL_S", "tests_media_controls");   /* the whole run's bound (default 600 s) */
    stub_verbose = getenv("VERBOSE") != NULL;
    shuttle_test_on_late = on_late; shuttle_test_on_applied = stub_progress;
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
    WAIT(I->media_get_duration(d) > 0, "the replay length");
    CHECK(I->media_get_duration(d) == 3937, "duration %lld ms, expected 3937 (118 units)", (long long)I->media_get_duration(d));
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, "the first run to end");
    CHECK(I->media_get_time(d) == 3937, "time at the end %lld, expected 3937 (unit 118 resolved from its counter)", (long long)I->media_get_time(d));
    CHECK(stub_ended_signals == 1 && stub_started_signals == 1, "signals after one run: started %d ended %d", stub_started_signals, stub_ended_signals);
    CHECK(stub_video_frames == 119, "first run published %llu frames, expected 119 (units 0..118)", (unsigned long long)stub_video_frames);

    /* 2. seek from the ended state to 2,000 ms: a new session from the middle of the file */
    uint64_t f0 = stub_video_frames;
    I->media_set_time(d, 2000);
    WAIT(stub_started_signals == 2, "the seek to start a session");
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, "the seeked run to end");
    uint64_t seeked = stub_video_frames - f0;
    CHECK(seeked > 40 && seeked < 70, "the run from 2,000 ms published %llu frames (from about unit 59-63 of 118)", (unsigned long long)seeked);
    CHECK(I->media_get_time(d) == 3937, "time at the end of the seeked run %lld", (long long)I->media_get_time(d));

    /* 3. restart then pause, queued back to back as a quick double action: held near the start. Held is a state, not a quiet
     * spell: the pacer is parked and every unit it delivered before parking has been through the worker and the sink
     * (shuttle_test_replay_held). From then nothing can reach OBS until a resume; an unheld replay plays to its end. */
    I->media_restart(d); I->media_play_pause(d, true);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, "the pause");
    WAIT(shuttle_test_replay_held(d) || I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, "the paused replay to hold with every delivered unit published");
    CHECK(shuttle_test_replay_held(d), "the pause did not hold the replay (state %d)", I->media_get_state(d));
    uint64_t held = stub_video_frames;
    usleep(250000);   /* kept paused 3x the 83 ms late-handoff threshold, so the resume check below has a pause it could misreport */
    CHECK(stub_video_frames == held && I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED && shuttle_test_replay_held(d), "kept paused: frames %llu -> %llu, state %d (want %d), held %d",
          (unsigned long long)held, (unsigned long long)stub_video_frames, I->media_get_state(d), OBS_MEDIA_STATE_PAUSED, shuttle_test_replay_held(d));
    CHECK(I->media_get_time(d) < 500, "paused at %lld ms, expected near the start", (long long)I->media_get_time(d));

    /* A pause is not a delivery stall. Decided by the reported gaps themselves: none may run from a handoff before the resume
     * press to one after it. A gap from host load after the resume starts at a post-resume handoff and never matches, so a
     * loaded machine cannot fail this (the old check counted every late report: 4 of 20 loaded runs failed, 2026-11-26).
     * The control thread is held 20 ms just after it releases the replay: the window in which the old handoff_reset, stored
     * after the release, lost the first frame and timed the whole pause (611 ms reported). */
    atomic_store(&g_resume_ns, os_gettime_ns());
    shuttle_test_resume_delay_us = 20000;
    I->media_play_pause(d, false);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING && stub_video_frames > held + 5, "resume");   /* the first frame's report, if any, is posted before the next frame */
    shuttle_test_resume_delay_us = 0;
    CHECK(atomic_load(&g_pause_timed) == 0, "resuming reported the pause as a late handoff (%d report(s) from a handoff before the press to one after it)", atomic_load(&g_pause_timed));
    atomic_store(&g_resume_ns, UINT64_MAX);
    /* Step 4 starts from a held replay, made the way step 3 made one. A pause here would hold nothing on a slow build: the
     * pacer reads the file to its end long before the worker publishes six frames (ThreadSanitizer), and the end that
     * lands once the worker drains would race the paused seeks below. */
    I->media_restart(d); I->media_play_pause(d, true);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, "the second pause");
    WAIT(shuttle_test_replay_held(d) || I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, "the second pause to hold the replay");
    CHECK(shuttle_test_replay_held(d), "the second pause did not hold the replay (state %d)", I->media_get_state(d));

    /* 4. seeks while paused only move the target (OBS's drag); play starts there */
    I->media_set_time(d, 2500); I->media_set_time(d, 3000);
    WAIT(I->media_get_time(d) == 3000, "the pending seek to show");
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, "a seek while paused unpaused the replay");
    /* Counted from the new session's start signal: the paused session's frames still in its pipeline reach OBS
     * while the play stops it (fs_stop drains them), before the signal. Counted from the press, a loaded machine
     * added up to 17 of them to this run's 22 (2026-11-19). */
    int started = stub_started_signals;
    I->media_play_pause(d, false);
    WAIT(stub_started_signals == started + 1, "play to start at the pending seek");
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_ENDED, "the run from 3,000 ms to end");
    seeked = stub_video_frames - stub_frames_at_start;
    CHECK(seeked > 10 && seeked < 35, "the run from 3,000 ms published %llu frames (from about unit 89-95)", (unsigned long long)seeked);

    /* 4b. a record press whose output fails to start: RECORDING_STARTING stops the replay (actions in that
     * blank gap are ignored), restart_check (main queue) finds no active output and resumes the replay with
     * restart_pending still set. From there the controls must act; before the fix they were ignored. */
    stub_expect(L_REC_IDLE); stub_expect(L_STREAM_IDLE); stub_expect(L_OWNED);
    stub_restart_on_record(1);
    I->media_restart(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "playing before the record press");
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STARTING);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "RECORDING_STARTING left state %d", I->media_get_state(d));
    started = stub_started_signals;
    WAIT_MAIN(stub_started_signals != started, "restart_check (main queue) to resume the replay");
    CHECK(stub_started_signals == started + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "restart_check did not resume the replay");
    I->media_play_pause(d, true);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PAUSED, "a pause after a failed record press");
    I->media_stop(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "a stop after a failed record press");
    started = stub_started_signals;
    I->media_restart(d);   /* stopped, restart_pending still set: the controls must still act */
    WAIT(stub_started_signals == started + 1 && I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "a restart after stop, after a failed record press");
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STOPPED);

    /* 4c. the same through streaming (the discard stream): STREAMING_STARTING stops the replay, restart_check
     * finds no active streaming output and resumes it, and STREAMING_STOPPED ends the session. */
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "playing before the stream press");
    stub_fire_event(OBS_FRONTEND_EVENT_STREAMING_STARTING);
    CHECK(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "STREAMING_STARTING left state %d", I->media_get_state(d));
    started = stub_started_signals;
    WAIT_MAIN(stub_started_signals != started, "restart_check (main queue) to resume the replay");
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
    WAIT_MAIN(stub_started_signals != started, "restart_check (main queue) to resume the replay");
    stub_fire_event(OBS_FRONTEND_EVENT_RECORDING_STOPPED);
    stub_restart_on_record(0);
    { int r = stub_expect_end(L_REC_IDLE), t = stub_expect_end(L_STREAM_IDLE), o = stub_expect_end(L_OWNED);   /* 4b + 4e; 4c; 4d */
      CHECK(r == 2 && t == 1 && o == 1, "failed-press warnings: recording %d (want 2), stream %d (want 1), owned %d (want 1)", r, t, o); }

    /* 5. stop */
    I->media_stop(d);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_STOPPED, "stop");
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
     * (each update is another refused live start, counted here so a clean run prints none) */
    CHECK(shuttle_test_usb_backend == CC_USB_LIBUSB, "unset USB stack selected %d, not libusb", shuttle_test_usb_backend);
    stub_expect(L_OPEN);
    stub_usb_backend("iousbhost"); I->update(d, st);
    CHECK(shuttle_test_usb_backend == CC_USB_IOUSBHOST, "\"iousbhost\" selected %d, not IOUSBHost", shuttle_test_usb_backend);
    stub_usb_backend("libusb"); I->update(d, st);
    CHECK(shuttle_test_usb_backend == CC_USB_LIBUSB, "\"libusb\" selected %d, not libusb", shuttle_test_usb_backend);
    stub_usb_backend(NULL);
    { int o = stub_expect_end(L_OPEN); CHECK(o == 2, "USB stack updates: %d open failures (want 2: one per refused live start)", o); }

    /* 6a. live, the device drops off USB (reported as the capture core does). There is no device here, so every
     * reconnect attempt fails: the picture is blanked at once, attempts repeat (RECONNECT_INTERVAL_NS is 20 ms in
     * this build) and stop after the limit; a second disconnect then a user stop cancels the attempts. */
    {
        uint64_t blanks = stub_blank_calls;
        stub_expect(L_OPEN); stub_expect(L_GONE); stub_expect(L_GAVE_UP);
        shuttle_test_device_gone(d);
        CHECK(stub_blank_calls == blanks + 1, "a disconnect did not blank the source (%llu blank calls)", (unsigned long long)(stub_blank_calls - blanks));
        CHECK(shuttle_test_reconnect_wanted(d), "a disconnect did not start reconnecting");
        WAIT(shuttle_test_reconnect_tries(d) >= 30, "timed reconnect attempts to stop after the limit (30 x 20 ms)");
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
        WAIT(!shuttle_test_reconnect_wanted(d), "a user stop to cancel reconnecting");
        I->update(d, st);
        { int o = stub_expect_end(L_OPEN), g = stub_expect_end(L_GONE), u = stub_expect_end(L_GAVE_UP);
          CHECK(o >= 1 && g == 0 && u <= 1, "after the second disconnect: %d open failures (want at least 1), %d disconnect lines (want 0), %d give-ups (want at most 1)", o, g, u); }
    }

    /* 6b. the device drops off USB and comes back held open by another process (2026-11-15 03:54: Chrome opened the
     * just re-enumerated Shuttle first). The attempt is refused busy; no timed retries follow (the old code retried
     * every RECONNECT_INTERVAL_NS, 20 ms in this build: about 15 attempts in 300 ms); the holder's close notice brings
     * the next attempt at once. A close during an attempt still brings the next one (the watch is armed before the
     * attempt). After a user stop a close notice does nothing. */
    {
        static const char *const L_BUSY_OPEN = "frameserver open failed: another process holds the Shuttle open";
        static const char *const L_BUSY_WAIT = "reconnecting when it lets go";
        shuttle_test_open_rc = CC_ERR_BUSY;
        stub_expect(L_BUSY_OPEN); stub_expect(L_BUSY_WAIT); stub_expect(L_GONE);
        shuttle_test_device_gone(d);
        WAIT(stub_expect_count(L_BUSY_OPEN) >= 1, "the first reconnect attempt");
        usleep(300000);
        CHECK(stub_expect_count(L_BUSY_OPEN) == 1, "held open: %d attempts before the holder closed it (want 1: the next waits for its close)", stub_expect_count(L_BUSY_OPEN));
        shuttle_test_device_closed(d);
        WAIT(stub_expect_count(L_BUSY_OPEN) >= 2, "an attempt on the holder's close notice");
        shuttle_test_close_during_open = 1; shuttle_test_device_closed(d);   /* attempt 3 sees a close before it returns */
        WAIT(stub_expect_count(L_BUSY_OPEN) >= 4, "an attempt after a close during the previous one");
        usleep(300000);
        CHECK(stub_expect_count(L_BUSY_OPEN) == 4, "held open: %d attempts (want 4: the gone, two closes, the close during attempt 3)", stub_expect_count(L_BUSY_OPEN));
        CHECK(shuttle_test_reconnect_wanted(d), "held open: stopped wanting to reconnect");
        I->media_stop(d);
        WAIT(!shuttle_test_reconnect_wanted(d), "a user stop to cancel reconnecting");
        shuttle_test_device_closed(d); usleep(100000);
        { int o = stub_expect_end(L_BUSY_OPEN), w = stub_expect_end(L_BUSY_WAIT), g = stub_expect_end(L_GONE);
          CHECK(o == 4 && w == 1 && g == 1, "held open: %d busy attempts (want 4, none after the user stop), %d wait lines (want 1), %d disconnects (want 1)", o, w, g); }
        shuttle_test_open_rc = 0;
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
        WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "a session to put to sleep");
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
        WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "a replay before a sleep");
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
        WAIT(stub_expect_count(L_OPEN) >= 1, "a reconnect attempt after the full wake");
        I->media_stop(d);
        WAIT(!shuttle_test_reconnect_wanted(d), "a user stop to cancel reconnecting after the wake");
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
        WAIT(stub_expect_count(L_OPEN) == 2, "a restart while asleep to try the device at once");
        CHECK(!shuttle_test_asleep(d) && stub_expect_count(L_HELD) == 0, "a restart while asleep: asleep %d, %d held", shuttle_test_asleep(d), stub_expect_count(L_HELD));
        shuttle_test_power(d, WILL_SLEEP);
        I->media_stop(d);
        WAIT(!shuttle_test_asleep(d), "a stop while asleep to end the sleep");
        shuttle_test_full_wake(d);
        usleep(200000);
        CHECK(stub_expect_count(L_OPEN) == 2 && !shuttle_test_reconnect_wanted(d), "a wake after a user stop restarted something (%d opens)", stub_expect_count(L_OPEN));
        { int o = stub_expect_end(L_OPEN), h = stub_expect_end(L_HELD), r = stub_expect_end(L_RESTART);
          CHECK(o == 2 && h == 0 && r == 1, "user actions while asleep: %d opens (want 2), %d held (want 0), %d restart failures (want 1)", o, h, r); }
        /* the same user actions from automation in a dark wake (display off: hotkeys, obs-websocket, macros) do not end it */
        stub_expect(L_OPEN); stub_expect(L_HELD);
        shuttle_test_display_on = 0;
        shuttle_test_power(d, WILL_SLEEP);
        I->update(d, st);
        I->media_restart(d);
        usleep(200000);
        CHECK(shuttle_test_asleep(d) && stub_expect_count(L_OPEN) == 0 && stub_expect_count(L_HELD) == 2, "user actions with the display off: asleep %d, %d opened (want 0), %d held (want 2)", shuttle_test_asleep(d), stub_expect_count(L_OPEN), stub_expect_count(L_HELD));
        shuttle_test_display_on = 1; shuttle_test_full_wake(d);
        WAIT(stub_expect_count(L_OPEN) >= 1, "the held start to be made at the full wake");
        I->media_stop(d);
        WAIT(!shuttle_test_reconnect_wanted(d), "a user stop after the held start");
        stub_expect_end(L_OPEN); stub_expect_end(L_HELD);
        shuttle_test_display_on = 0;
    }

    /* 6b. a replay path that cannot be opened: the previous file's length does not stay on the bar */
    st = stub_settings(argv[1], 1);
    I->update(d, st);
    WAIT(I->media_get_duration(d) == 3937, "the fixture's length again");
    ended = stub_ended_signals;
    stub_expect(L_NOFILE); stub_expect(L_OPEN);
    st = stub_settings("/nonexistent/volume/capture.tpc", 1);
    I->update(d, st);
    { int n = stub_expect_end(L_NOFILE), o = stub_expect_end(L_OPEN);
      CHECK(n == 1 && o == 0, "unopenable replay: %d file errors (want 1), %d open failures (want 0: it stops before opening)", n, o); }
    CHECK(I->media_get_duration(d) == 0 && stub_ended_signals == ended + 1, "after a failed replay start: duration %lld, ended signals +%d",
          (long long)I->media_get_duration(d), stub_ended_signals - ended);

    /* 6c. unit repair follows registration: off -> on. The repair fixture has 121 picture units, every 4th 224 bytes
     * short; "Search picture" is off here, so with repair off only the 91 whole units reach OBS and with it on the 30
     * short ones come back as whole frames too, except those skipped: live, a repair waits for nothing, so a unit that
     * finds the four raw slots busy is not tried (counted). The replay runs faster than real time, so a slow worker
     * (ThreadSanitizer, or a loaded machine: 11-17 of 30 skipped at load average 20-50, 2026-11-19) skips some. */
    if (argc > 2){
        static const char *L_REP_ON = "unit repair ON", *L_REP_OFF = "unit repair off";
        stub_plain_content = 0;   /* this fixture carries picture: format and planes are still checked */
        for (int reg = 1; reg >= 0; reg--){
            stub_registration(reg);
            stub_expect(reg ? L_REP_OFF : L_REP_ON);
            ended = stub_ended_signals; f0 = stub_video_frames;
            st = stub_settings(argv[2], 1); I->update(d, st);
            int stops = stub_stop_lines;   /* after the update: it stopped the previous session */
            WAIT(stub_ended_signals > ended, "the repair fixture to play to its end");
            I->media_stop(d);   /* the session's stats line */
            WAIT(stub_stop_lines > stops, "the repair fixture's session to log its stats");
            uint64_t got = stub_video_frames - f0;
            char line[2048]; stub_last_stop_line(line, sizeof line);
            unsigned long long put = 0, dec = 0, skip = 0, refused = 0; const char *p = strstr(line, "units put back ");
            int parsed = p && sscanf(p, "units put back %llu (declined %llu, not tried or not published %llu, refused by the publisher %llu)", &put, &dec, &skip, &refused) == 4;
            /* every short unit is accounted for, and every frame put back reached OBS */
            CHECK(parsed && got == 91u + put && (reg ? put + dec + skip + refused == 0 : put + dec + skip + refused == 30),
                  "registration %s: stats %s put back %llu declined %llu skipped %llu refused %llu, %llu frames to OBS",
                  reg ? "on" : "off", parsed ? "parsed:" : "NOT PARSED", put, dec, skip, refused, (unsigned long long)got);
            int n = stub_expect_end(reg ? L_REP_OFF : L_REP_ON);
            /* Only the split between put back and skipped depends on load. Declining is decided by the unit's bytes and its
             * predecessor (this fixture's 121 units never fill the unit pool, so every predecessor is kept), and the
             * publisher never refuses here (the plugin copies each frame and holds no surface): both stay 0. */
            int frames_ok = reg ? got == 91u : got > 91u && dec == 0 && refused == 0;
            CHECK(n == 1 && frames_ok, "registration %s: %d \"%s\" start lines (want 1), %llu frames to OBS, declined %llu, refused %llu (want %s)",
                  reg ? "on" : "off", n, reg ? L_REP_OFF : L_REP_ON, (unsigned long long)got, dec, refused,
                  reg ? "91 frames" : "92-121 frames, none declined or refused: every short unit put back or skipped");
        }
        stub_registration(1); stub_plain_content = 1;
    }

    /* 7. back to replay, then destroy while it plays: no hang. Destroy stops the session, and fs_stop publishes what is already
     * queued, so how long it takes is the worker's speed (seconds under ThreadSanitizer), not a property to assert. A hang is:
     * destroy runs on its own thread and the wait fails when nothing at all has progressed for MC_TEST_STALL_S. */
    st = stub_settings(argv[1], 1);
    I->update(d, st);
    WAIT(I->media_get_state(d) == OBS_MEDIA_STATE_PLAYING, "replay after live");
    double t0 = now(); pthread_t dt;
    CHECK(pthread_create(&dt, NULL, destroy_thread, d) == 0, "destroy thread");
    WAIT_MAIN(atomic_load(&g_destroyed), "destroy while playing to return");
    pthread_join(dt, NULL);
    if (stub_verbose) fprintf(stderr, "destroy while playing took %.2f s\n", now() - t0);
    CHECK(stub_frame_errors == 0, "%llu frames handed to OBS were not I210 4c with the expected planes", (unsigned long long)stub_frame_errors);
    obs_module_unload();                                   /* joins what the load started */
    printf(fails ? "MEDIA CONTROLS: %d FAILURES\n" : "MEDIA CONTROLS PASS\n", fails);
    return fails ? 1 : 0;
}
