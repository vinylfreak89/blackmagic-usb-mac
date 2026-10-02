// shuttle-source — native OBS Studio source for the Intensity Shuttle frameserver (P4a).
//
// A thin consumer of the frameserver SDK: the frameserver owns the device (or a replay of a
// .tpc), parses, classifies, registers and publishes corrected 480i UYVY frames and PCM blocks
// with timestamps; this plugin only converts them into libobs's async video/audio structures.
// OBS owns deinterlacing (per-source Deinterlacing menu; the plugin sets the TFF hint once) and
// everything downstream (compositing, encoding, ProRes).
//
// Timestamps: video = unit counter * 1001/30000 s (frameserver pts); audio = the publisher's
// sample-contiguous device pts, plus the correlation residual applied ONLY where it steps
// (a device event that lost samples: advance audio time by the lost amount once, so sync is
// restored with an honest gap) — never a continuous resample (CLAUDE.md §6, audio census).
// Both are converted to nanoseconds; OBS syncs audio to video by timestamp.
//
// Sidecar: the registration decision log is aligned to the RECORDING, not to the source's
// lifetime. On OBS's recording-started event the plugin attaches the frameserver's decision log
// (fs_log_start) and detaches it on recording-stopped. The first row is the first unit processed
// after OBS reported the recording started; the recording's first encoded frame is that unit or
// the one delivered just before the event (its counter is written to the OBS log at attach), so
// alignment is within one unit, not exact — an in-band frame counter would be needed for exact.
// The log grows in a private non-synced scratch directory and is published as
// <recording>.registration.csv at detach: by one exclusive rename when scratch and destination
// share a filesystem, otherwise by an exclusive copy that is read back and byte-compared before the
// scratch copy is deleted (CLAUDE.md writer output rule: never GROW a file inside a cloud-synced
// root — a finished 30 MB file copied whole is fine, so a recording on a cloud volume such as a
// LucidLink filespace gets its sidecar too). An existing sidecar is never truncated or replaced
// (.2, .3 suffixes); a source restart mid-recording continues in .partN.csv files.
//
// Threading: the video sink runs on the frameserver's video worker, the audio sink on its audio
// worker; obs_source_output_video/audio copy under libobs's own locks and return. Neither sink
// blocks, allocates, or touches OBS's graphics thread. One session per process: a second source
// instance is refused (the device has exactly one owner) — OBS_SOURCE_DO_NOT_DUPLICATE.
#include <obs-module.h>
#include <obs-frontend-api.h>
#include <util/platform.h>
#include <media-io/video-io.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <IOSurface/IOSurface.h>
#include <util/dstr.h>
#include <pthread.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <libgen.h>
#include <limits.h>
#include "publish_copy.h"
#include "publish_queue.h"
#include "timing_report.h"
#include <dispatch/dispatch.h>
#include <objc/runtime.h>
#include <objc/message.h>
#include <stdio.h>      /* renamex_np (macOS 10.12+): RENAME_EXCL makes the publish rename fail instead of replacing a file that appeared meanwhile */
#include "../frameserver/frameserver.h"
#include "../frameserver/replay_probe.h"
#include "replay_timeline.h"

OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("shuttle-source", "en-US")

#define S_INPUT       "input"
#define S_HRETIME     "hretime"
#define S_REGISTRATION "registration"
#define S_PARTIAL      "show_partial"
#define S_TPC         "raw_tpc"
#define S_REPLAY      "replay_path"
#define S_USE_REPLAY  "use_replay"
#define S_REPLAY_RESTART "replay_restart_on_record"
#define S_REPLAY_STOP    "replay_stop_at_end"
#define S_SIDECAR     "sidecar_with_recording"

#define AP_TICKS_TO_NS(t) ((uint64_t)((__uint128_t)(t) * 1000000000ull / AP_PTS_DEN))
#include "audio_timing.h"
#include "frame_levels.h"

#define MEDIA_QUEUE 32
enum { ACT_PLAY, ACT_PAUSE, ACT_RESTART, ACT_STOP, ACT_SEEK };
typedef struct {
    obs_source_t *source;
    frameserver *fs;
    uint16_t *vbuf;                        /* I210 staging, Y then U then V planes (one frame; libobs copies); frame_levels.h */
    int32_t *abuf; uint32_t abuf_frames;   /* S32 interleaved stereo staging */
    float color_matrix[16], color_min[3], color_max[3];
    _Atomic uint64_t frames_out, audio_frames_out, audio_steps;
    shuttle_audio_clock audio_clock; int64_t audio_skip_pending;   /* early-audio frames still to drop (audio worker only) */
    _Atomic int ended; enum cc_end end_reason;
    pthread_mutex_t m;                      /* serializes session + sidecar transitions (frontend events, update, destroy) */
    int sidecar_enabled;                    /* property: attach the decision log to each OBS recording */
    char *sidecar_base;                     /* <recording path> of the active recording (bfree), NULL when none */
    unsigned sidecar_part;                  /* 0 = first file of this recording; N>0 => .partN+1 (source restarted mid-recording) */
    int sidecar_attached;
    char *sidecar_partial, *sidecar_final;  /* growing scratch path, and the published name it gets at detach */
    publish_queue *pq;                       /* persistent publisher (publish_queue.h): frontend callbacks only enqueue; drained at destroy */
    _Atomic uint64_t last_counter;          /* counter_ext of the last frame delivered to OBS */
    /* Delivery timing (video worker only; read after fs_stop joins it). A handoff gap longer than
     * FREEZE_GAP_NS is a freeze in OBS's unbuffered presentation: it shows the newest frame per
     * tick, so a late frame repeats the previous one and a following burst is discarded. The
     * call time is how long obs_source_output_video blocked (OBS's async lock). */
    uint64_t last_handoff_ns, gap_events, max_gap_ns, max_call_ns, slow_calls;
    timing_report *reports;                 /* late-handoff reports, logged off the worker (timing_report.h) */
    void *activity;                         /* NSProcessInfo activity held while a session runs (latency_begin) */
    /* Raw .tpc beside each recording (owner, 2026-09-28: "let OBS do both"). Written at its final
     * path on the recording's volume (LucidLink takes growing files); closed off the UI thread by
     * a detached closer; destroy waits until every closer is done. */
    int tpc_enabled; unsigned tpc_part; char *tpc_path;
    _Atomic int closers; pthread_mutex_t close_m; pthread_cond_t close_c;   /* detached closers (raw .tpc, sidecar); destroy waits for 0 */
    /* Replay aligned to a recording (owner, 2026-09-28: the re-recorded file should match the
     * original's length without racing the record button). RECORDING_STARTING stops the replay and
     * blanks the source; RECORDING_STARTED restarts it from the file's first byte, so the recording
     * holds no frame of the earlier playback. At end of file, the stop is requested only after OBS
     * has ticked STOP_TICKS frames: OBS stamps the stop when it is requested, and a frame handed
     * over but not yet rendered would otherwise fall outside the recording. */
    int replaying;                          /* this session reads a .tpc */
    int restart_pending;                    /* stopped at RECORDING_STARTING, restart at RECORDING_STARTED */
    int record_gap;                         /* blank on purpose: from RECORDING_STARTING until RECORDING_STARTED/STOPPED, or until
                                               restart_check finds the start failed. Media controls wait it out. */
    _Atomic int stop_on_eof;                /* this recording ends when the replay does */
    _Atomic int stop_ticks;                 /* >0: render ticks left before requesting the stop */
    /* OBS media controls (OBS_SOURCE_CONTROLLABLE_MEDIA: play/pause, restart, stop, seek bar). libobs
     * calls the media callbacks on its render thread (process_media_actions, from obs_source_video_tick;
     * OBS 32.2.2), and a restart or seek stops and reopens the session, which can wait seconds on a
     * network read. So a callback only queues the action; the control thread applies it under s->m.
     * OBS's controls poll state, time and duration from the UI thread: atomics only. */
    pthread_t ctl_thr, probe_thr; int ctl_running, probe_running;
    pthread_mutex_t ctl_m; pthread_cond_t ctl_c;   /* guards the queue and the probe request only; never held while taking s->m */
    int ctl_quit;
    struct { int act; int64_t ms; } q[MEDIA_QUEUE]; unsigned q_head, q_n;
    char *probe_path; uint64_t probe_gen;          /* pending timeline probe (bstrdup), and the path generation it is for */
    _Atomic int probe_abort;
    _Atomic int media_state;                      /* enum obs_media_state reported to OBS */
    _Atomic int replay_mode;                      /* the settings select a replay: the controls act; live they only restart/stop */
    _Atomic int64_t time_ms;                      /* position of the last frame played (video worker; set at session start) */
    _Atomic int64_t seek_shown_ms;                /* a seek chosen while paused, shown instead (-1 none): frames still in the
                                                     pipeline after a pause must not overwrite it */
    _Atomic uint64_t tl_units, tl_bytes; _Atomic int tl_first16;   /* the replay's timeline; tl_units 0 = not known yet */
    char *tl_path; uint64_t tl_gen, tl_size;      /* under s->m: the file (and its size) the timeline describes; gen bumps when it changes */
    int tl_probing, tl_failed;                    /* under s->m: a probe for tl_gen is queued or running / found no length */
    int paused; int64_t pending_seek_ms;          /* under s->m: replay held; a seek chosen while held (-1 none) */
    uint64_t next_start_unit, next_start_offset;  /* under s->m: consumed by the next shuttle_start (0 = the file's start) */
    uint64_t session_start_unit;                  /* the running session's first unit, estimated: on_frame resolves counters from it */
    _Atomic int live_regrey;                      /* live: put OBS's controls back in their greyed restart state on the next tick */
    _Atomic int handoff_reset;                    /* resumed from a pause: the next frame's gap is the pause, not a stall */
} shuttle_src;
#define STOP_TICKS 3
#define SIDECAR_SCRATCH_FMT "/private/tmp/shuttle-source-%u"   /* per-uid, mode 0700, non-synced; published by rename on the same filesystem, by verified copy otherwise */

static _Atomic int g_instances;
#define FREEZE_GAP_NS 83000000ull   /* 2.5 unit periods: one late unit, not scheduling noise */
#define SLOW_CALL_NS  20000000ull

static void report_late(void *ctx, const tr_event *e){
    (void)ctx; const fs_handoff_timing *h = &e->h;
    blog(LOG_WARNING, "[shuttle-source] delivery timing: counter %llu handed to OBS %.1f ms after the previous frame (%.1f unit periods); output call blocked %.1f ms"
         " | worker since previous handoff %.1f ms: idle %.1f, classify %.1f, registration %.1f, h-retiming %.1f, sidecar write %.1f, other %.1f; %u items; this unit queued %.1f ms",
         (unsigned long long)e->counter, e->gap_ns / 1e6, e->gap_ns / (1e9 * 1001 / 30000), e->call_ns / 1e6,
         h->since_prev_ns / 1e6, h->idle_ns / 1e6, h->classify_ns / 1e6, h->geometry_ns / 1e6, h->hretime_ns / 1e6, h->log_ns / 1e6, h->other_ns / 1e6, h->items, h->queue_wait_ns / 1e6);
}

/* While a session runs, ask macOS not to throttle this process: NSActivityUserInitiated (no App Nap,
 * no idle sleep) plus NSActivityLatencyCritical (no timer coalescing). OBS itself requests only
 * user-initiated (libobs os_request_high_performance), and its own timers were measured waking late:
 * the 25 ms hotkey thread 94% late, up to 76 ms, in the session whose replay stalled ~100 ms inside OBS
 * while the same replay outside OBS never did (2026-09-29). Plain C via the Objective-C runtime. */
#define ACTIVITY_OPTIONS (0x00FFFFFFULL | 0xFF00000000ULL)   /* NSActivityUserInitiated | NSActivityLatencyCritical */
static void latency_begin(shuttle_src *s){
    if (s->activity) return;
    id pi = ((id (*)(id, SEL))objc_msgSend)((id)objc_getClass("NSProcessInfo"), sel_registerName("processInfo"));
    id act = pi ? ((id (*)(id, SEL, uint64_t, id))objc_msgSend)(pi, sel_registerName("beginActivityWithOptions:reason:"),
                                                               ACTIVITY_OPTIONS, (id)CFSTR("Shuttle capture/replay: real-time frame delivery")) : NULL;
    if (!act){ blog(LOG_WARNING, "[shuttle-source] could not request latency-critical scheduling; timers may be delayed while OBS is in the background"); return; }
    s->activity = ((void *(*)(id, SEL))objc_msgSend)(act, sel_registerName("retain"));
    blog(LOG_INFO, "[shuttle-source] latency-critical scheduling requested for the session");
}
static void latency_end(shuttle_src *s){
    if (!s->activity) return;
    id pi = ((id (*)(id, SEL))objc_msgSend)((id)objc_getClass("NSProcessInfo"), sel_registerName("processInfo"));
    ((void (*)(id, SEL, id))objc_msgSend)(pi, sel_registerName("endActivity:"), (id)s->activity);
    ((void (*)(id, SEL))objc_msgSend)((id)s->activity, sel_registerName("release"));
    s->activity = NULL;
}
static void diag_to_obs(void *ctx, const char *line){ (void)ctx; blog(LOG_INFO, "[shuttle-source] %s", line); }

static const char *shuttle_get_name(void *td){ (void)td; return "Blackmagic Intensity Shuttle (frameserver)"; }

static void on_frame(void *ctx, const fp_frame *fr){
    shuttle_src *s = ctx;
    if (!fr->surface) return;
    IOSurfaceLock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    const uint8_t *base = IOSurfaceGetBaseAddress(fr->surface); size_t bpr = IOSurfaceGetBytesPerRow(fr->surface);
    uint16_t *py = s->vbuf, *pu = py + (size_t)FP_FRAME_WIDTH * FP_FRAME_HEIGHT, *pv = pu + (size_t)FP_FRAME_WIDTH / 2 * FP_FRAME_HEIGHT;
    shuttle_uyvy_to_i210(base, bpr, FP_FRAME_WIDTH, FP_FRAME_HEIGHT, py, pu, pv);
    IOSurfaceUnlock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    struct obs_source_frame f; memset(&f, 0, sizeof f);
    f.data[0] = (uint8_t *)py; f.data[1] = (uint8_t *)pu; f.data[2] = (uint8_t *)pv;
    f.linesize[0] = FP_FRAME_WIDTH * 2; f.linesize[1] = f.linesize[2] = FP_FRAME_WIDTH;
    f.width = FP_FRAME_WIDTH; f.height = FP_FRAME_HEIGHT; f.format = VIDEO_FORMAT_I210;
    f.timestamp = (uint64_t)((__uint128_t)fr->pts_num * 1000000000ull / fr->pts_den);
    memcpy(f.color_matrix, s->color_matrix, sizeof f.color_matrix);
    memcpy(f.color_range_min, s->color_min, sizeof f.color_range_min); memcpy(f.color_range_max, s->color_max, sizeof f.color_range_max);
    f.full_range = false;
    uint64_t t0 = os_gettime_ns();
    obs_source_output_video(s->source, &f);
    if (atomic_exchange(&s->handoff_reset, 0)) s->last_handoff_ns = 0;
    uint64_t t1 = os_gettime_ns(), call = t1 - t0, gap = s->last_handoff_ns ? t0 - s->last_handoff_ns : 0;
    s->last_handoff_ns = t0;
    if (gap > s->max_gap_ns) s->max_gap_ns = gap;
    if (call > s->max_call_ns) s->max_call_ns = call;
    if (call > SLOW_CALL_NS) s->slow_calls++;
    if (gap > FREEZE_GAP_NS || call > SLOW_CALL_NS){
        if (gap > FREEZE_GAP_NS) s->gap_events++;
        tr_event e = { fr->counter_ext, gap, call, {0} };
        fs_handoff_timing_get(s->fs, &e.h);   /* worker thread: this sink runs on it */
        tr_post(s->reports, &e);              /* never blog here: a log write on this thread delays the next frame */
    }
    uint64_t units = atomic_load_explicit(&s->tl_units, memory_order_acquire);
    if (units){   /* the seek bar's time: this frame's own counter, resolved near the session's expected position */
        rt_timeline tl = { atomic_load(&s->tl_bytes), units, (uint16_t)atomic_load(&s->tl_first16) };
        uint64_t u = rt_resolve(&tl, (uint16_t)fr->counter_ext, (int64_t)(s->session_start_unit + atomic_load(&s->frames_out)));
        atomic_store(&s->time_ms, rt_ms(u));
    }
    atomic_fetch_add(&s->frames_out, 1); atomic_store(&s->last_counter, fr->counter_ext);
}

static void on_audio(void *ctx, const ap_block *b){
    shuttle_src *s = ctx;
    if (b->n_frames > s->abuf_frames) return;             /* cannot happen: publisher capacity == staging capacity */
    uint64_t ticks; int64_t step = 0;
    int stepped = shuttle_audio_time_step(&s->audio_clock, b, &ticks, &step);
    if (stepped < 0) return;                             /* no device time yet */
    if (stepped) atomic_fetch_add(&s->audio_steps, 1);
    struct obs_source_audio a; memset(&a, 0, sizeof a);
    a.speakers = SPEAKERS_STEREO; a.format = AUDIO_FORMAT_32BIT; a.samples_per_sec = AP_SAMPLE_RATE;
    /* Device lost samples: deliver the gap as real silence ending exactly where this block starts,
     * so OBS sees contiguous audio (a bare timestamp jump is mishandled by OBS). */
    if (step > 0){
        memset(s->abuf, 0, (size_t)s->abuf_frames * 2 * sizeof(int32_t));
        uint64_t t0 = ticks - (uint64_t)step * AP_TICKS_PER_FRAME;
        for (int64_t done = 0; done < step; ){
            uint32_t n = (uint32_t)(step - done < s->abuf_frames ? step - done : s->abuf_frames);
            a.data[0] = (const uint8_t *)s->abuf; a.frames = n; a.timestamp = AP_TICKS_TO_NS(t0 + (uint64_t)done * AP_TICKS_PER_FRAME);
            obs_source_output_audio(s->source, &a); done += n;
        }
    }
    /* Device sent audio early (negative step): drop the overlap from the start of this and, if it is
     * shorter than the overlap, the following blocks. A break or a later gap cancels what is left. */
    int64_t gap_unused; uint32_t skip;
    shuttle_audio_plan(step, (b->flags & AP_FLAG_DISCONTINUITY_BEFORE) != 0, b->n_frames, &s->audio_skip_pending, &gap_unused, &skip);
    if (skip == b->n_frames) return;
    const uint8_t *p = b->s24le + (size_t)skip * AP_BYTES_PER_FRAME;
    for (uint32_t i = 0; i < b->n_frames - skip; i++){
        int32_t l = (int32_t)((uint32_t)p[0] << 8 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 24);
        int32_t r = (int32_t)((uint32_t)p[3] << 8 | (uint32_t)p[4] << 16 | (uint32_t)p[5] << 24);
        s->abuf[2 * i] = l; s->abuf[2 * i + 1] = r; p += AP_BYTES_PER_FRAME;
    }
    a.data[0] = (const uint8_t *)s->abuf; a.frames = b->n_frames - skip;
    a.timestamp = AP_TICKS_TO_NS(ticks + (uint64_t)skip * AP_TICKS_PER_FRAME);
    obs_source_output_audio(s->source, &a);
    atomic_fetch_add(&s->audio_frames_out, b->n_frames - skip);
}

static void on_end(void *ctx, enum cc_end r){ shuttle_src *s = ctx; s->end_reason = r; atomic_store(&s->ended, 1);
    if (r == CC_END_REPLAY_EOF && atomic_load(&s->stop_on_eof)) atomic_store(&s->stop_ticks, STOP_TICKS);   /* every frame and audio block is already delivered */
    /* Any end the plugin did not request (end of file, a read error, a lost device) leaves nothing to
     * pause or seek within: OBS's controls switch to restart. A stop the plugin requested ends with
     * CC_END_STOPPED and the caller sets the state. */
    if (r != CC_END_STOPPED){ atomic_store(&s->media_state, OBS_MEDIA_STATE_ENDED); obs_source_media_ended(s->source); }
    blog(LOG_INFO, "[shuttle-source] capture ended: reason %d", (int)r); }
/* Graphics thread, once per OBS frame. obs_frontend_recording_stop only queues StopRecording onto the
 * UI thread (OBSStudioAPI: QMetaObject::invokeMethod), so calling it here is safe. */
static void shuttle_video_tick(void *data, float seconds){
    (void)seconds; shuttle_src *s = data;
    /* Live: libobs followed our media callback with its own signal (media_play/media_restart), which
     * enables the seek bar and shows a pause button. Same thread, after it: grey them out again. */
    if (atomic_exchange(&s->live_regrey, 0) && !atomic_load(&s->replay_mode)) obs_source_media_ended(s->source);
    if (atomic_load(&s->stop_ticks) > 0 && atomic_fetch_sub(&s->stop_ticks, 1) == 1 && atomic_exchange(&s->stop_on_eof, 0)){
        if (obs_frontend_recording_active()){
            blog(LOG_INFO, "[shuttle-source] replay reached the end of the file: stopping the recording");
            obs_frontend_recording_stop();
        }
    }
}

/* ---- recording-aligned sidecar (frontend events; every transition runs under s->m) ---- */
/* The recording FILE. obs_frontend_get_current_record_output_path() is the configured output
 * DIRECTORY (OBSBasic::GetCurrentOutputPath reads the FilePath/RecFilePath setting) — using it
 * produced sidecars named just ".registration.csv". obs_frontend_get_last_recording() returns
 * BasicOutputHandler::lastRecordingPath, which GetRecordingFilename() sets to the full file path
 * when the recording starts (before the output runs) and updates on a file split, so it is the
 * current recording's file at RECORDING_STARTED and at RECORDING_STOPPED (OBS 32.2.2 source).
 * Scope decision: the sidecar is SESSION-level — one CSV per press of the record button, named
 * after the recording's FIRST file. OBS's automatic file splitting emits no frontend event, so a
 * split session's later files share that one sidecar (rotating per split would need the output's
 * "file_changed" signal; follow-up). Supported outputs: the standard and advanced FILE recorders;
 * an advanced FFmpeg output to a URL never sets a file name and gets no sidecar. Auto-remux renames
 * the recording after RECORDING_STOPPED (e.g. .mkv -> .mp4); the sidecar keeps the pre-remux name. */
static int recording_path(shuttle_src *s){
    bfree(s->sidecar_base); s->sidecar_base = NULL;
    char *p = obs_frontend_get_last_recording();
    if (!p || !*p){ bfree(p); return -1; }
    s->sidecar_base = p; return 0;
}
static void sidecar_final_name(struct dstr *fin, const shuttle_src *s, unsigned dup){
    dstr_free(fin);
    if (s->sidecar_part == 0) dstr_printf(fin, "%s.registration", s->sidecar_base);
    else dstr_printf(fin, "%s.registration.part%u", s->sidecar_base, s->sidecar_part + 1);
    if (dup > 1) dstr_catf(fin, ".%u", dup);
    dstr_cat(fin, ".csv");
}
static void sidecar_attach(shuttle_src *s){
    if (!s->sidecar_enabled || !s->fs || s->sidecar_attached || !s->sidecar_base) return;
    /* final name: <recording>.registration[.partN][.dup].csv — an existing sidecar is never truncated */
    struct dstr fin = {0}; struct stat st; unsigned dup = 1;
    for (sidecar_final_name(&fin, s, dup); stat(fin.array, &st) == 0 || pq_reserved(s->pq, fin.array); sidecar_final_name(&fin, s, ++dup))
        if (dup > 999){ blog(LOG_ERROR, "[shuttle-source] sidecar: too many existing files next to %s", s->sidecar_base); dstr_free(&fin); return; }
    /* grow in private non-synced scratch on the same filesystem, publish by rename */
    char scratch[64]; snprintf(scratch, sizeof scratch, SIDECAR_SCRATCH_FMT, (unsigned)getuid());
    struct stat sd;
    if (mkdir(scratch, 0700) != 0 && errno != EEXIST){ blog(LOG_ERROR, "[shuttle-source] sidecar scratch %s: %s", scratch, strerror(errno)); dstr_free(&fin); return; }
    if (stat(scratch, &sd) != 0 || !S_ISDIR(sd.st_mode) || sd.st_uid != getuid() || (sd.st_mode & 077)){ blog(LOG_ERROR, "[shuttle-source] sidecar scratch %s is not a private directory owned by this user; refusing", scratch); dstr_free(&fin); return; }
    char *namecopy = bstrdup(fin.array); struct dstr part = {0};
    char base[PATH_MAX]; if (!basename_r(namecopy, base)){ blog(LOG_ERROR, "[shuttle-source] sidecar name too long: %s", fin.array); bfree(namecopy); dstr_free(&fin); return; }
    dstr_printf(&part, "%s/%s.partial-%08x%08x", scratch, base, (unsigned)arc4random(), (unsigned)arc4random()); bfree(namecopy);   /* random, exclusive (fs_log_start opens "wx") */
    if (fs_log_start(s->fs, part.array) == 0){
        s->sidecar_attached = 1; s->sidecar_part++;
        bfree(s->sidecar_partial); s->sidecar_partial = bstrdup(part.array);
        bfree(s->sidecar_final); s->sidecar_final = bstrdup(fin.array);
        uint64_t last = atomic_load(&s->last_counter);
        if (atomic_load(&s->frames_out)) blog(LOG_INFO, "[shuttle-source] sidecar attached -> %s (growing as %s); last unit delivered before attach: counter %llu — the recording's first frame is that unit or the next",
                       fin.array, part.array, (unsigned long long)last);
        else blog(LOG_INFO, "[shuttle-source] sidecar attached -> %s (growing as %s) before this session delivered a unit: its first row is the recording's first new frame",
                  fin.array, part.array);
    } else blog(LOG_ERROR, "[shuttle-source] sidecar could not be opened: %s", part.array);
    dstr_free(&part); dstr_free(&fin);
}
/* Publish a complete, closed scratch sidecar at its final name. Same filesystem: one exclusive
 * rename. Different filesystem (a recording on a cloud volume or a share): staged copy on the
 * destination filesystem, fsync, read-back byte-compare, exclusive rename, then the scratch copy is
 * deleted. "Published" means the destination filesystem acknowledged the bytes; on a write-back
 * cloud volume (LucidLink) that is cache-visible, and the volume's own upload counter says when it
 * is remote — the plugin cannot see that, so it does not claim it. */
/* Publication runs on a persistent per-source thread (publish_queue): OBS frontend event callbacks
 * execute on the UI thread (OBSStudioAPI::on_event is a synchronous loop called from OBSBasic), so
 * a callback only enqueues a job owning copies of both paths. Jobs run in order; a stalled cloud
 * volume delays later publications, never the UI. The queue is bounded (SIDECAR_QUEUE_CAP): when
 * full, the complete scratch file stays where it is and its path is logged — nothing is dropped.
 * The queue is drained, not abandoned, at destroy. Final names held by queued or in-progress jobs
 * are reserved so a later recording cannot pick the same name before it exists on disk. */
#define SIDECAR_QUEUE_CAP 8
static void publish_one(void *ctx, const char *partial, const char *final){
    (void)ctx;
    /* the kernel decides: exclusive rename, and a verified copy only when it reports EXDEV */
    int rc = publish_file(partial, final);
    if (rc == 2) blog(LOG_INFO, "[shuttle-source] sidecar published: %s", final);
    else {
        if (rc == -2) blog(LOG_ERROR, "[shuttle-source] sidecar publish by copy failed (%s) AND its staging file could not be removed: look for %s.partial-*; the complete file is at %s", strerror(errno), final, partial);
        else if (rc < 0) blog(LOG_ERROR, "[shuttle-source] sidecar publish failed, or its copy did not verify (%s); the complete file is left at %s", strerror(errno), partial);
        else if (rc == 1) blog(LOG_WARNING, "[shuttle-source] sidecar published by verified copy: %s — the scratch copy was KEPT at %s (directory fsync or scratch removal failed: %s)", final, partial, strerror(errno));
        else blog(LOG_INFO, "[shuttle-source] sidecar published by verified copy (different filesystem; cache-visible on a cloud volume): %s", final);
    }
}
static void sidecar_publish(shuttle_src *s){
    if (!s->pq){ blog(LOG_ERROR, "[shuttle-source] no publisher thread: complete sidecar left at %s (wanted %s)", s->sidecar_partial, s->sidecar_final); return; }
    if (pq_enqueue(s->pq, s->sidecar_partial, s->sidecar_final) != 0)
        blog(LOG_ERROR, "[shuttle-source] publisher queue %s: complete sidecar left at %s (wanted %s)", errno == ENOSPC ? "full" : strerror(errno), s->sidecar_partial, s->sidecar_final);
}
/* Recording stop runs on OBS's UI thread; closing the sidecar drains its writer ring and fsyncs
 * (async_file.h), which can block on a busy disk. So the log is detached here (instant: no row after
 * it) and closed, judged and queued for publication on a detached closer, like the raw .tpc. */
typedef struct { shuttle_src *s; FILE *log; uint64_t row_errors; char *partial, *final; } sidecar_close_job;
static void *sidecar_closer(void *arg){
    sidecar_close_job *j = arg; shuttle_src *s = j->s;
    int closed = fclose(j->log) == 0; int e = errno;
    if (!closed || j->row_errors)
        blog(LOG_ERROR, "[shuttle-source] sidecar is INCOMPLETE (%llu row write errors%s%s); left unpublished at %s",
             (unsigned long long)j->row_errors, closed ? "" : ", close failed: ", closed ? "" : strerror(e), j->partial);
    else if (!s->pq) blog(LOG_ERROR, "[shuttle-source] no publisher thread: complete sidecar left at %s (wanted %s)", j->partial, j->final);
    else if (pq_enqueue(s->pq, j->partial, j->final) != 0)
        blog(LOG_ERROR, "[shuttle-source] publisher queue %s: complete sidecar left at %s (wanted %s)", errno == ENOSPC ? "full" : strerror(errno), j->partial, j->final);
    bfree(j->partial); bfree(j->final); bfree(j);
    pthread_mutex_lock(&s->close_m); atomic_fetch_sub(&s->closers, 1); pthread_cond_broadcast(&s->close_c); pthread_mutex_unlock(&s->close_m);
    return NULL;
}
static void sidecar_detach(shuttle_src *s){
    if (!s->sidecar_attached) return;
    s->sidecar_attached = 0;
    if (!s->fs){ blog(LOG_ERROR, "[shuttle-source] sidecar left unpublished at %s (capture already closed)", s->sidecar_partial); return; }
    sidecar_close_job *j = bzalloc(sizeof *j); j->s = s;
    j->log = fs_log_detach(s->fs, &j->row_errors);
    if (!j->log){ blog(LOG_ERROR, "[shuttle-source] sidecar was not attached at recording stop; left at %s", s->sidecar_partial); bfree(j); return; }
    j->partial = bstrdup(s->sidecar_partial); j->final = bstrdup(s->sidecar_final);
    atomic_fetch_add(&s->closers, 1);
    pthread_t t; pthread_attr_t a; pthread_attr_init(&a); pthread_attr_setdetachstate(&a, PTHREAD_CREATE_DETACHED);
    if (pthread_create(&t, &a, sidecar_closer, j) != 0){ blog(LOG_WARNING, "[shuttle-source] sidecar: no closer thread; closing inline"); sidecar_closer(j); }
    pthread_attr_destroy(&a);
}

/* ~3 minutes of stream (owner, 2026-10-02: 2 or 4 GB). The 256 MiB it replaces rode out 11 s; a 90-minute recording
 * then lost 137 s of raw capture in two stretches where the writer fell behind. The sink hands drained pages back,
 * so this is address space until the writer actually falls behind. */
#define TPC_RING_BYTES ((size_t)4 << 30)
typedef struct { shuttle_src *s; cc_async_sink *k; char *path; } tpc_close_job;
static void *tpc_closer(void *arg){
    tpc_close_job *j = arg; cc_async_sink_stats st;
    int rc = cc_async_sink_close(j->k, &st);
    uint64_t lost = st.lost_packets[0] + st.lost_packets[1];
    blog(rc == CC_OK && !lost ? LOG_INFO : LOG_ERROR,
         "[shuttle-source] raw .tpc closed%s: %s — %llu records, %.1f MB written, tee loss video %llu pkts / %llu B, audio %llu pkts / %llu B, control records dropped %llu, ring peak %.1f MB, largest write %zu B | writer: %llu writes, mean %.2f ms, longest %.1f ms, %llu over 100 ms, longest wait between writes with data ready %.1f ms | loss episodes %llu, writer inside a write call at %llu of them (for up to %.1f ms by then); most found waiting after an idle wait %.1f MB | ring memory handed back %.0f MB, %llu refusals%s%s",
         rc == CC_OK ? "" : " WITH A WRITE ERROR", j->path, (unsigned long long)st.records, st.bytes_written / 1e6,
         (unsigned long long)st.lost_packets[0], (unsigned long long)st.lost_bytes[0], (unsigned long long)st.lost_packets[1], (unsigned long long)st.lost_bytes[1],
         (unsigned long long)st.control_dropped, st.high_water / 1e6, st.max_write,
         (unsigned long long)st.writes, st.writes ? st.write_ns / 1e6 / (double)st.writes : 0.0, st.max_write_ns / 1e6, (unsigned long long)st.slow_writes, st.max_ready_gap_ns / 1e6,
         (unsigned long long)st.loss_episodes, (unsigned long long)st.loss_in_write, st.max_in_write_at_loss_ns / 1e6, st.max_wake_backlog / 1e6,
         st.released_bytes / 1e6, (unsigned long long)st.release_failures, st.io_error ? ", error: " : "", st.io_error ? strerror(st.io_error) : "");
    shuttle_src *s = j->s; bfree(j->path); bfree(j);
    pthread_mutex_lock(&s->close_m); atomic_fetch_sub(&s->closers, 1); pthread_cond_broadcast(&s->close_c); pthread_mutex_unlock(&s->close_m);
    return NULL;
}
/* Detach now (instant); drain and close on a detached thread so neither OBS's UI nor the capture waits. */
static void tpc_detach(shuttle_src *s){
    if (!s->fs || !s->tpc_path) return;
    cc_async_sink *k = fs_tee_detach(s->fs);
    char *path = s->tpc_path; s->tpc_path = NULL;
    if (!k){ bfree(path); return; }
    tpc_close_job *j = bzalloc(sizeof *j); j->s = s; j->k = k; j->path = path;
    atomic_fetch_add(&s->closers, 1);
    pthread_t t; pthread_attr_t a; pthread_attr_init(&a); pthread_attr_setdetachstate(&a, PTHREAD_CREATE_DETACHED);
    if (pthread_create(&t, &a, tpc_closer, j) != 0){ blog(LOG_WARNING, "[shuttle-source] raw .tpc: no closer thread; closing inline"); tpc_closer(j); }
    pthread_attr_destroy(&a);
}
static void tpc_attach(shuttle_src *s){
    if (!s->tpc_enabled || !s->fs || s->tpc_path || !s->sidecar_base) return;
    struct dstr path = {0};
    if (++s->tpc_part == 1) dstr_printf(&path, "%s.raw.tpc", s->sidecar_base);
    else dstr_printf(&path, "%s.raw.part%u.tpc", s->sidecar_base, s->tpc_part);
    struct dstr note = {0}; char *b = bstrdup(s->sidecar_base); char base[PATH_MAX];
    dstr_printf(&note, "shuttle-source tee v1 input=svideo recording=%s part=%u", basename_r(b, base) ? base : "?", s->tpc_part); bfree(b);
    if (fs_tee_start(s->fs, path.array, note.array, TPC_RING_BYTES) == 0){
        s->tpc_path = bstrdup(path.array);
        blog(LOG_INFO, "[shuttle-source] raw .tpc started: %s", path.array);
    } else blog(LOG_ERROR, "[shuttle-source] raw .tpc could not be started (exists? volume writable?): %s", path.array);
    dstr_free(&path); dstr_free(&note);
}
static void shuttle_stop(shuttle_src *s);
static int shuttle_start(shuttle_src *s, obs_data_t *settings);

/* ---- media controls: timeline, action queue, control thread ---- */
/* Under s->m. A replay file the timeline does not describe (another path, or the same path at another
 * size) gets a new generation and a probe; until the probe publishes, the duration is 0 and seeking is
 * refused. The control thread runs the probe; the file is read through the same replay backend. */
static void timeline_track(shuttle_src *s, const char *path){
    struct stat st; uint64_t size = stat(path, &st) == 0 ? (uint64_t)st.st_size : 0;
    /* Known, on its way, or already failed for this file: a failure (no picture unit near an end) is
     * a property of the file and is not retried until the path or size changes. */
    if (s->tl_path && !strcmp(s->tl_path, path) && size == s->tl_size && (s->tl_probing || s->tl_failed || atomic_load(&s->tl_units))) return;
    atomic_store(&s->tl_units, 0);
    bfree(s->tl_path); s->tl_path = bstrdup(path); s->tl_gen++; s->tl_size = size; s->tl_probing = 1; s->tl_failed = 0;
    pthread_mutex_lock(&s->ctl_m);
    bfree(s->probe_path); s->probe_path = bstrdup(path); s->probe_gen = s->tl_gen;
    atomic_store(&s->probe_abort, 1);   /* a probe of the previous file stops early */
    pthread_cond_broadcast(&s->ctl_c); pthread_mutex_unlock(&s->ctl_m);
}
/* Under s->m: no file is being replayed; the previous file's length must not stay on the bar. */
static void timeline_forget(shuttle_src *s){
    atomic_store(&s->tl_units, 0);
    bfree(s->tl_path); s->tl_path = NULL; s->tl_gen++; s->tl_probing = s->tl_failed = 0; s->tl_size = 0;
}
static int timeline_get(shuttle_src *s, rt_timeline *tl){
    uint64_t units = atomic_load_explicit(&s->tl_units, memory_order_acquire);
    if (!units) return -1;
    tl->units = units; tl->file_bytes = atomic_load(&s->tl_bytes); tl->first16 = (uint16_t)atomic_load(&s->tl_first16);
    return 0;
}
/* Render thread (libobs process_media_actions): queue only. Consecutive seeks collapse into the latest
 * (a dragged seek bar sends one every 100 ms); a full queue refuses the action and says so. */
static void media_post(shuttle_src *s, int act, int64_t ms){
    pthread_mutex_lock(&s->ctl_m);
    unsigned last = (s->q_head + s->q_n - 1) % MEDIA_QUEUE;
    if (act == ACT_SEEK && s->q_n && s->q[last].act == ACT_SEEK) s->q[last].ms = ms;
    else if (s->q_n == MEDIA_QUEUE) blog(LOG_WARNING, "[shuttle-source] media control queue full: action %d dropped", act);
    else { unsigned i = (s->q_head + s->q_n) % MEDIA_QUEUE; s->q[i].act = act; s->q[i].ms = ms; s->q_n++; }
    pthread_cond_broadcast(&s->ctl_c); pthread_mutex_unlock(&s->ctl_m);
}
/* Under s->m: stop and start the replay at `ms`. The byte offset is proportional to time; the
 * shown time then follows the counters of the frames actually played. */
static void replay_start_at(shuttle_src *s, obs_data_t *settings, int64_t ms){
    rt_timeline tl; uint64_t u = 0, off = 0;
    if (ms > 0 && timeline_get(s, &tl) == 0){ u = rt_unit_at_ms(&tl, ms); off = rt_offset(&tl, u); }
    shuttle_stop(s);
    s->next_start_unit = u; s->next_start_offset = off;
    if (shuttle_start(s, settings) != 0) blog(LOG_ERROR, "[shuttle-source] replay could not be started at %.1f s", ms / 1000.0);
}
static void media_apply(shuttle_src *s, int act, int64_t ms){
    obs_data_t *settings = obs_source_get_settings(s->source);
    if (!atomic_load(&s->replay_mode)){
        /* Live: the tape is the transport. Restart and stop act on the capture session; pause and seek
         * have nothing to act on (holding delivery would only discard what the deck keeps playing). */
        if (act == ACT_RESTART){ shuttle_stop(s); if (shuttle_start(s, settings) != 0) blog(LOG_ERROR, "[shuttle-source] capture restart failed"); }
        else if (act == ACT_STOP) shuttle_stop(s);
        atomic_store(&s->media_state, OBS_MEDIA_STATE_STOPPED);
        obs_data_release(settings); return;
    }
    /* Between RECORDING_STARTING and RECORDING_STARTED the replay is stopped and the source blank on
     * purpose; the recording restarts it from the file's start. If the record press failed, restart_check
     * ends the gap and resumes the replay with restart_pending still set (a late RECORDING_STARTED still
     * restarts it); from there the controls act normally, stop included, and keep restart_pending. */
    if (s->record_gap){
        blog(LOG_INFO, "[shuttle-source] media control ignored while the recording starts (it restarts the replay from the beginning)");
        obs_data_release(settings); return;
    }
    int running = s->fs && !atomic_load(&s->ended);
    switch (act){
    case ACT_PAUSE:
        if (running && !s->paused && fs_replay_pause(s->fs, 1) == 0){
            /* only PLAYING becomes PAUSED: an end that landed meanwhile keeps its ENDED */
            int expect = OBS_MEDIA_STATE_PLAYING;
            if (atomic_compare_exchange_strong(&s->media_state, &expect, OBS_MEDIA_STATE_PAUSED)) s->paused = 1;
            else fs_replay_pause(s->fs, 0);
        }
        break;
    case ACT_PLAY:
        if (!running) replay_start_at(s, settings, s->pending_seek_ms >= 0 ? s->pending_seek_ms : 0);
        else if (s->pending_seek_ms >= 0) replay_start_at(s, settings, s->pending_seek_ms);
        else if (s->paused && fs_replay_pause(s->fs, 0) == 0){
            s->paused = 0; atomic_store(&s->handoff_reset, 1);
            int expect = OBS_MEDIA_STATE_PAUSED;
            atomic_compare_exchange_strong(&s->media_state, &expect, OBS_MEDIA_STATE_PLAYING);
        }
        break;
    case ACT_SEEK: {
        rt_timeline tl;
        if (timeline_get(s, &tl) != 0){ blog(LOG_WARNING, "[shuttle-source] seek refused: the replay's length is not known yet"); break; }
        if (ms < 0) ms = 0;
        if (ms > rt_ms(tl.units)) ms = rt_ms(tl.units);
        if (s->paused && running){ s->pending_seek_ms = ms; atomic_store(&s->seek_shown_ms, ms); }   /* applied on play: OBS pauses around a drag */
        else replay_start_at(s, settings, ms);
        break; }
    case ACT_RESTART: replay_start_at(s, settings, 0); break;
    case ACT_STOP: shuttle_stop(s); s->pending_seek_ms = -1; atomic_store(&s->seek_shown_ms, -1); atomic_store(&s->time_ms, 0); break;
    }
    obs_data_release(settings);
}
static void *media_thread(void *arg){
    shuttle_src *s = arg;
    pthread_setname_np("shuttle-media");
    pthread_mutex_lock(&s->ctl_m);
    for (;;){
        while (!s->ctl_quit && !s->q_n) pthread_cond_wait(&s->ctl_c, &s->ctl_m);
        if (s->ctl_quit) break;
        int act = s->q[s->q_head].act; int64_t ms = s->q[s->q_head].ms;
        s->q_head = (s->q_head + 1) % MEDIA_QUEUE; s->q_n--;
        pthread_mutex_unlock(&s->ctl_m);
        pthread_mutex_lock(&s->m); media_apply(s, act, ms); pthread_mutex_unlock(&s->m);
        pthread_mutex_lock(&s->ctl_m);
    }
    pthread_mutex_unlock(&s->ctl_m);
    return NULL;
}
/* The probe has its own thread: it can take seconds (7.7 s for the tape-1 file over LucidLink), and a
 * pause or stop pressed meanwhile must not wait for it. */
static void *probe_thread(void *arg){
    shuttle_src *s = arg;
    pthread_setname_np("shuttle-probe");
    pthread_mutex_lock(&s->ctl_m);
    for (;;){
        while (!s->ctl_quit && !s->probe_path) pthread_cond_wait(&s->ctl_c, &s->ctl_m);
        if (s->ctl_quit) break;
        char *path = s->probe_path; uint64_t gen = s->probe_gen; s->probe_path = NULL;
        atomic_store(&s->probe_abort, 0);
        pthread_mutex_unlock(&s->ctl_m);
        fs_replay_span sp; rt_timeline tl;
        int probed = fs_replay_probe(path, 0, &s->probe_abort, &sp) == 0;
        int ok = probed && rt_init(&tl, sp.file_bytes, sp.first_counter, sp.last_counter) == 0;
        int aborted = atomic_load(&s->probe_abort);
        pthread_mutex_lock(&s->m);
        if (gen == s->tl_gen && !aborted){
            s->tl_probing = 0;
            if (ok){
                atomic_store(&s->tl_bytes, tl.file_bytes); atomic_store(&s->tl_first16, tl.first16);
                atomic_store_explicit(&s->tl_units, tl.units, memory_order_release);
                blog(LOG_INFO, "[shuttle-source] replay length %.1f s (%llu units, counters %u..%u) — %s", rt_ms(tl.units) / 1000.0,
                     (unsigned long long)tl.units, sp.first_counter, sp.last_counter, path);
            } else if (sp.incomplete){
                blog(LOG_WARNING, "[shuttle-source] replay length unknown: %s could not be read to its end (read error?); no seek bar until the replay is started again", path);
            } else {
                s->tl_failed = 1;   /* a property of the file: not retried until the path or size changes */
                blog(LOG_WARNING, "[shuttle-source] replay length unknown: no complete picture unit within 32 MiB (about 1.4 s) of the %s of %s; no seek bar for this file",
                     !sp.have_first && !sp.have_last ? "start or end" : !sp.have_first ? "start" : "end", path);
            }
        }
        pthread_mutex_unlock(&s->m);
        bfree(path);
        pthread_mutex_lock(&s->ctl_m);
    }
    pthread_mutex_unlock(&s->ctl_m);
    return NULL;
}
static void media_play_pause(void *d, bool pause){ shuttle_src *s = d; if (!atomic_load(&s->replay_mode)) atomic_store(&s->live_regrey, 1); media_post(s, pause ? ACT_PAUSE : ACT_PLAY, 0); }
static void media_restart(void *d){ shuttle_src *s = d; if (!atomic_load(&s->replay_mode)) atomic_store(&s->live_regrey, 1); media_post(s, ACT_RESTART, 0); }
static void media_stop(void *d){ shuttle_src *s = d; media_post(s, ACT_STOP, 0); }
static void media_set_time(void *d, int64_t ms){ shuttle_src *s = d; if (atomic_load(&s->replay_mode)) media_post(s, ACT_SEEK, ms); }
static int64_t media_get_duration(void *d){
    shuttle_src *s = d; rt_timeline tl;
    return atomic_load(&s->replay_mode) && timeline_get(s, &tl) == 0 ? rt_ms(tl.units) : 0;
}
static int64_t media_get_time(void *d){
    shuttle_src *s = d; if (!atomic_load(&s->replay_mode)) return 0;
    int64_t seek = atomic_load(&s->seek_shown_ms);
    return seek >= 0 ? seek : atomic_load(&s->time_ms);
}
/* Live reports STOPPED whether or not it captures: OBS then greys the seek bar, shows --:--:--, and its
 * button restarts the session (MediaControls: PLAYING would enable a bar with nothing to seek and a
 * pause that cannot pause; NONE would make the button do nothing). Side effect: the re-grey is a
 * media_ended signal, so a websocket client or scene-switcher sees "ended" after each live action. */
static enum obs_media_state media_get_state(void *d){
    shuttle_src *s = d;
    return atomic_load(&s->replay_mode) ? (enum obs_media_state)atomic_load(&s->media_state) : OBS_MEDIA_STATE_STOPPED;
}
/* A recording that fails to start synchronously sends no frontend event (OBSBasic::StartRecording
 * ignores AdvancedOutput::StartRecording's false; OBS 32.0.0), which would leave the replay stopped
 * and the source blank. This runs from the main dispatch queue, i.e. after the UI thread has
 * returned from StartRecording (obs_queue_task(OBS_TASK_UI) would run inline there): if the output
 * is not active by then, the start failed. Resuming keeps restart_pending, so a RECORDING_STARTED
 * that does arrive still restarts from the beginning of the file. */
static void restart_check(void *param){
    obs_weak_source_t *w = param;
    obs_source_t *src = obs_weak_source_get_source(w); obs_weak_source_release(w);
    if (!src) return;   /* the source was destroyed meanwhile */
    shuttle_src *s = obs_obj_get_data(src);
    obs_output_t *out = obs_frontend_get_recording_output();
    int active = out && obs_output_active(out); obs_output_release(out);
    if (s){
        pthread_mutex_lock(&s->m);
        if (s->restart_pending && !active) s->record_gap = 0;   /* the start failed: the gap is over, whatever resumes */
        if (s->restart_pending && !s->fs && !active){
            obs_data_t *st = obs_source_get_settings(src);
            if (shuttle_start(s, st) == 0) blog(LOG_WARNING, "[shuttle-source] the recording output is not active after the record press (start failed?): replay resumed; it restarts from the beginning if the recording does start");
            obs_data_release(st);
        }
        pthread_mutex_unlock(&s->m);
    }
    obs_source_release(src);
}
static void frontend_event(enum obs_frontend_event ev, void *data){
    shuttle_src *s = data;
    pthread_mutex_lock(&s->m);
    obs_data_t *settings = obs_source_get_settings(s->source);
    switch (ev){
    case OBS_FRONTEND_EVENT_RECORDING_STARTING:
        atomic_store(&s->stop_ticks, 0); atomic_store(&s->stop_on_eof, 0);
        if (s->replaying && obs_data_get_bool(settings, S_REPLAY_RESTART)){
            shuttle_stop(s);
            obs_source_output_video(s->source, NULL);   /* blank until the restart: no earlier frame enters the recording */
            s->restart_pending = 1; s->record_gap = 1;
            blog(LOG_INFO, "[shuttle-source] recording starting: replay stopped; it restarts from the beginning of the file once the recording has started");
            dispatch_async_f(dispatch_get_main_queue(), obs_source_get_weak_source(s->source), restart_check);
        }
        break;
    case OBS_FRONTEND_EVENT_RECORDING_STARTED:
        if (recording_path(s) != 0) blog(LOG_WARNING, "[shuttle-source] recording started but its path is unknown; no sidecar");
        else { s->sidecar_part = 0; s->tpc_part = 0; }
        s->record_gap = 0;
        if (s->restart_pending){
            s->restart_pending = 0;
            shuttle_stop(s);   /* running if restart_check resumed it or a settings change started it */
            atomic_store(&s->stop_on_eof, obs_data_get_bool(settings, S_REPLAY_STOP) ? 1 : 0);   /* armed before the session can end */
            if (shuttle_start(s, settings) != 0) atomic_store(&s->stop_on_eof, 0);
            else {   /* shuttle_start attached the sidecar itself: the recording is active */
                blog(LOG_INFO, "[shuttle-source] replay restarted from the beginning of the file%s", atomic_load(&s->stop_on_eof) ? "; the recording stops when it ends" : "");
            }
            break;
        }
        if (!s->sidecar_base) break;
        if (!s->fs) blog(LOG_WARNING, "[shuttle-source] recording started while the capture is not running; sidecar starts when it does");
        sidecar_attach(s); tpc_attach(s);
        break;
    case OBS_FRONTEND_EVENT_RECORDING_STOPPING:
        atomic_store(&s->stop_ticks, 0); atomic_store(&s->stop_on_eof, 0);   /* a second stop request would force-stop (StopRecording(recordingStopping)) */
        break;
    case OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        atomic_store(&s->stop_ticks, 0); atomic_store(&s->stop_on_eof, 0);
        tpc_detach(s); sidecar_detach(s); bfree(s->sidecar_base); s->sidecar_base = NULL;
        s->record_gap = 0;
        if (s->restart_pending){ s->restart_pending = 0; if (!s->fs) shuttle_start(s, settings); }   /* the recording never started: resume the replay */
        break;
    default: break;
    }
    obs_data_release(settings);
    pthread_mutex_unlock(&s->m);
}

static void shuttle_stop(shuttle_src *s){
    if (!s->fs) return;
    /* Mid-recording restart: do NOT detach the log first — units delivered between a detach and the
     * capture stop would be recorded without sidecar rows. fs_stop closes the attached log after the
     * workers drain (every delivered unit has its row); publish afterwards from the session's stats. */
    tpc_detach(s);   /* before fs_stop: its drain runs on the closer, not here */
    int publish_after = s->sidecar_attached; s->sidecar_attached = 0;
    fs_stats st; fs_stop(s->fs); fs_get_stats(s->fs, &st);
    if (publish_after){
        if (st.log_last_file_errors) blog(LOG_ERROR, "[shuttle-source] sidecar part is INCOMPLETE (%llu write/close errors in this file); left unpublished at %s", (unsigned long long)st.log_last_file_errors, s->sidecar_partial);
        else sidecar_publish(s);
    }
    blog(LOG_INFO, "[shuttle-source] stopped: published %llu frames (%llu to OBS), audio %llu frames delivered / %llu dropped, pool-full %llu, ring-full %llu, holes %llu, residual steps applied %llu, search frames shown %llu",
         (unsigned long long)st.published, (unsigned long long)atomic_load(&s->frames_out), (unsigned long long)st.audio_frames_delivered,
         (unsigned long long)st.audio_dropped_frames, (unsigned long long)st.dropped_pool_full, (unsigned long long)st.dropped_ring_full,
         (unsigned long long)st.holes, (unsigned long long)atomic_load(&s->audio_steps), (unsigned long long)st.partial_shown);
    blog(LOG_INFO, "[shuttle-source] delivery timing: %llu handoff gaps over 83 ms (max %.1f ms), %llu output calls over 20 ms (max %.1f ms)",
         (unsigned long long)s->gap_events, s->max_gap_ns / 1e6, (unsigned long long)s->slow_calls, s->max_call_ns / 1e6);
    fs_close(s->fs); s->fs = NULL;
    latency_end(s);
    s->paused = 0;
    atomic_store(&s->media_state, OBS_MEDIA_STATE_STOPPED);
}

static int shuttle_start(shuttle_src *s, obs_data_t *settings){
    if (s->fs){ blog(LOG_ERROR, "[shuttle-source] start refused: a capture session is already running"); return -1; }   /* one owner of the device, one session */
    fs_config cfg; memset(&cfg, 0, sizeof cfg);
    /* NULL geometry_config selects the approved per-engine defaults, with no environment reads. */
    const char *input = obs_data_get_string(settings, S_INPUT);
    cfg.capture.input = !strcmp(input, "composite") ? CC_INPUT_COMPOSITE : !strcmp(input, "component") ? CC_INPUT_COMPONENT : CC_INPUT_SVIDEO;
    uint64_t start_unit = s->next_start_unit, start_offset = s->next_start_offset;
    s->next_start_unit = s->next_start_offset = 0;   /* every other start begins the file */
    s->pending_seek_ms = -1; s->paused = 0;
    s->session_start_unit = start_unit;   /* before any worker exists: on_frame reads it */
    atomic_store(&s->time_ms, rt_ms(start_unit)); atomic_store(&s->seek_shown_ms, -1);
    int was_replay = atomic_exchange(&s->replay_mode, obs_data_get_bool(settings, S_USE_REPLAY) ? 1 : 0);
    if (obs_data_get_bool(settings, S_USE_REPLAY)){
        const char *rp = obs_data_get_string(settings, S_REPLAY);
        if (!rp || !*rp){ blog(LOG_WARNING, "[shuttle-source] replay selected but no file given"); timeline_forget(s); obs_source_media_ended(s->source); return -1; }
        if (access(rp, R_OK) != 0){   /* renamed or moved: say so, not just "start failed" */
            blog(LOG_ERROR, "[shuttle-source] replay file cannot be opened (%s): %s", strerror(errno), rp);
            timeline_forget(s); obs_source_media_ended(s->source); return -1;   /* no stale length, and OBS's controls show restart */
        }
        cfg.capture.replay_path = rp; cfg.capture.replay_pace_us = 16000;    /* device cadence */
        cfg.capture.replay_start_offset = start_offset;                     /* a seek: aligned forward to a whole transfer */
        timeline_track(s, rp);
        cfg.capture.replay_diag = 1; cfg.capture.diag_log = diag_to_obs;     /* stall diagnosis into the OBS log at session end */
    }
    s->replaying = cfg.capture.replay_path != NULL;
    cfg.hretime = obs_data_get_bool(settings, S_HRETIME) ? 1 : 0;   /* per-tape choice; off leaves output unchanged */
    cfg.registration_off = obs_data_get_bool(settings, S_REGISTRATION) ? 0 : 1;   /* per-tape: off publishes the nominal (0,0) placement */
    cfg.show_partial = obs_data_get_bool(settings, S_PARTIAL) ? 1 : 0;            /* search and unlocked picture: units that are not whole, stretched */
    cfg.pool_units = 0; cfg.surface_pool = 6;   /* pool sized from the capture ring (frameserver default) */
    cfg.sink.on_frame = on_frame; cfg.sink.ctx = s;
    cfg.audio_sink.on_block = on_audio; cfg.audio_sink.ctx = s;
    cfg.audio_block_frames = s->abuf_frames;
    cfg.on_end = on_end; cfg.end_ctx = s;
    atomic_store(&s->ended, 0); s->audio_clock = (shuttle_audio_clock){0}; s->audio_skip_pending = 0;
    atomic_store(&s->frames_out, 0); atomic_store(&s->audio_frames_out, 0); atomic_store(&s->audio_steps, 0);   /* per-session accounting */
    atomic_store(&s->last_counter, 0); atomic_store(&s->handoff_reset, 0);
    s->last_handoff_ns = s->gap_events = s->max_gap_ns = s->max_call_ns = s->slow_calls = 0;
    if (!s->replaying && was_replay) atomic_store(&s->live_regrey, 1);   /* from replay to live: OBS's controls still show the replay's bar; grey them */
    if (fs_open(&s->fs, &cfg) != 0){
        blog(LOG_ERROR, "[shuttle-source] frameserver open failed (device present? replay path?)"); s->fs = NULL;
        if (s->replaying) obs_source_media_ended(s->source);   /* nothing plays: OBS's controls show restart */
        return -1;
    }
    /* attach before fs_start, so a session started for a recording logs its first unit */
    s->sidecar_enabled = obs_data_get_bool(settings, S_SIDECAR);
    if (s->sidecar_enabled && obs_frontend_recording_active() && s->sidecar_base) sidecar_attach(s);   /* restarted mid-recording: continue as the next part */
    /* PLAYING before the session runs: an end that arrives at once (a seek to the last units) then
     * overwrites it with ENDED, never the other way round. */
    if (s->replaying){ atomic_store(&s->media_state, OBS_MEDIA_STATE_PLAYING); obs_source_media_started(s->source); }
    if (fs_start(s->fs) != 0){
        blog(LOG_ERROR, "[shuttle-source] frameserver start failed");
        atomic_store(&s->media_state, OBS_MEDIA_STATE_STOPPED); obs_source_media_ended(s->source);
        if (s->sidecar_attached){ s->sidecar_attached = 0; blog(LOG_ERROR, "[shuttle-source] sidecar of the failed session left unpublished at %s", s->sidecar_partial); }
        fs_close(s->fs); s->fs = NULL; return -1;
    }
    latency_begin(s);
    blog(LOG_INFO, "[shuttle-source] started (%s%s), registration %s, H-retiming %s", cfg.capture.replay_path ? "replay" : "device",
         start_offset ? ", from a seek" : "", cfg.registration_off ? "OFF (nominal placement)" : "on", cfg.hretime ? "ON" : "off");
    if (start_offset) blog(LOG_INFO, "[shuttle-source] replay starts at byte %llu (unit %llu, %.1f s)", (unsigned long long)start_offset, (unsigned long long)start_unit, rt_ms(start_unit) / 1000.0);
    /* A replay IS a raw capture: teeing it would write another copy of the file being read. */
    s->tpc_enabled = obs_data_get_bool(settings, S_TPC) && !s->replaying;
    if (obs_data_get_bool(settings, S_TPC) && s->replaying) blog(LOG_INFO, "[shuttle-source] raw .tpc is not written while replaying a .tpc");
    if (obs_frontend_recording_active() && s->sidecar_base) tpc_attach(s);
    return 0;
}

static void *shuttle_create(obs_data_t *settings, obs_source_t *source){
    if (atomic_fetch_add(&g_instances, 1) != 0){
        atomic_fetch_sub(&g_instances, 1);
        blog(LOG_ERROR, "[shuttle-source] a second instance was refused: the device has exactly one owner per process");
        return NULL;
    }
    shuttle_src *s = bzalloc(sizeof *s); s->source = source;
    s->vbuf = bmalloc((size_t)FP_FRAME_WIDTH * FP_FRAME_HEIGHT * 2 * sizeof(uint16_t));   /* Y + U + V planes */
    s->abuf_frames = 4096; s->abuf = bmalloc((size_t)s->abuf_frames * 2 * sizeof(int32_t));
    /* Rec.601 limited-range matrix for 10-bit I210: 64 -> black, 940 -> white, levels unchanged.
     * The range clamp is opened to the whole code range so sub-black and super-white reach OBS's
     * float texture instead of being clipped to 16..235 (frame_levels.h has the texture path). */
    video_format_get_parameters_for_format(VIDEO_CS_601, VIDEO_RANGE_PARTIAL, VIDEO_FORMAT_I210, s->color_matrix, s->color_min, s->color_max);
    for (int k = 0; k < 3; k++){ s->color_min[k] = 0.0f; s->color_max[k] = 1.0f; }
    /* libobs keeps audio timing independent of video only when the source is BOTH decoupled and
     * unbuffered (obs-source.c: the audio path re-anchors timing_adjust on its own only in that
     * mode, and the video path stops overwriting it). Frames are shown as they arrive at device
     * pace, which is what a live device wants; A/V sync comes from the shared device clock. */
    obs_source_set_async_unbuffered(source, true);
    /* Audio and video are cut from ONE device clock and arrive on different threads with the
     * audio block for a unit completing one unit after its video frame; with coupled audio,
     * libobs holds audio for the displayed video frame and discards what arrives late — audible
     * as constant dropouts. Decoupled audio is mixed on its own device-time line (the DeckLink and
     * AV-capture sources do the same). */
    obs_source_set_async_decoupled(source, true);
    obs_source_set_deinterlace_field_order(source, OBS_DEINTERLACE_FIELD_ORDER_TOP);   /* measured TFF (CLAUDE.md §6) */
    obs_source_set_deinterlace_mode(source, OBS_DEINTERLACE_MODE_YADIF_2X);          /* default presentation; the user may change it (OBS owns deinterlacing) */
    pthread_mutex_init(&s->m, NULL); pthread_mutex_init(&s->close_m, NULL); pthread_cond_init(&s->close_c, NULL);
    pthread_mutex_init(&s->ctl_m, NULL); pthread_cond_init(&s->ctl_c, NULL);
    s->pending_seek_ms = -1; atomic_store(&s->seek_shown_ms, -1); atomic_store(&s->media_state, OBS_MEDIA_STATE_STOPPED);
    if (pthread_create(&s->ctl_thr, NULL, media_thread, s) == 0) s->ctl_running = 1;
    else blog(LOG_ERROR, "[shuttle-source] could not start the media-control thread (%s): the play/pause, stop and seek controls will do nothing", strerror(errno));
    if (pthread_create(&s->probe_thr, NULL, probe_thread, s) == 0) s->probe_running = 1;
    else blog(LOG_ERROR, "[shuttle-source] could not start the replay-length probe thread (%s): no seek bar", strerror(errno));
    if (tr_open(&s->reports, 256, report_late, s) != 0){ s->reports = NULL; blog(LOG_ERROR, "[shuttle-source] could not start the delivery-timing reporter (%s): late handoffs are counted in the stop summary only", strerror(errno)); }
    if (pq_open(&s->pq, SIDECAR_QUEUE_CAP, publish_one, s) != 0){ s->pq = NULL; blog(LOG_ERROR, "[shuttle-source] could not start the sidecar publisher (%s): sidecars will stay in scratch (paths are logged), never published inline", strerror(errno)); }
    s->sidecar_enabled = obs_data_get_bool(settings, S_SIDECAR);
    /* Register for recording events BEFORE inspecting recording state, so a recording that starts
     * in between is seen by the callback rather than missed. Frontend events and this source's
     * update/destroy all serialize on s->m; removal in destroy happens on the frontend's own thread,
     * so no already-dispatched event can enter after it returns. */
    obs_frontend_add_event_callback(frontend_event, s);
    pthread_mutex_lock(&s->m);
    if (obs_frontend_recording_active() && recording_path(s) == 0) s->sidecar_part = 0;   /* created during a recording */
    if (shuttle_start(s, settings) != 0) blog(LOG_WARNING, "[shuttle-source] created without a running capture; fix settings");
    pthread_mutex_unlock(&s->m);
    return s;
}

static void shuttle_destroy(void *data){
    shuttle_src *s = data; if (!s) return;
    obs_frontend_remove_event_callback(frontend_event, s);
    if (s->ctl_running){   /* the render thread no longer calls in (the source is being destroyed); finish the action under way */
        pthread_mutex_lock(&s->ctl_m); s->ctl_quit = 1; atomic_store(&s->probe_abort, 1); pthread_cond_broadcast(&s->ctl_c); pthread_mutex_unlock(&s->ctl_m);
        pthread_join(s->ctl_thr, NULL);
    }
    if (s->probe_running){ pthread_mutex_lock(&s->ctl_m); s->ctl_quit = 1; atomic_store(&s->probe_abort, 1); pthread_cond_broadcast(&s->ctl_c); pthread_mutex_unlock(&s->ctl_m); pthread_join(s->probe_thr, NULL); }
    pthread_mutex_lock(&s->m); shuttle_stop(s); pthread_mutex_unlock(&s->m);
    pthread_mutex_lock(&s->close_m); while (atomic_load(&s->closers)) pthread_cond_wait(&s->close_c, &s->close_m); pthread_mutex_unlock(&s->close_m);   /* every raw .tpc and sidecar closed before the code unloads */
    pq_close(s->pq); pq_destroy(s->pq); s->pq = NULL;   /* drains every queued sidecar before the code unloads; the frontend callback (the only producer) was removed above */
    uint64_t lost_reports = tr_close(s->reports); s->reports = NULL;   /* the video worker (the only producer) was joined by shuttle_stop */
    if (lost_reports) blog(LOG_WARNING, "[shuttle-source] %llu late-handoff reports were not logged (the reporter fell 256 behind); the stop summaries count every event", (unsigned long long)lost_reports);
    pthread_mutex_destroy(&s->m); pthread_mutex_destroy(&s->close_m); pthread_cond_destroy(&s->close_c);
    pthread_mutex_destroy(&s->ctl_m); pthread_cond_destroy(&s->ctl_c); bfree(s->probe_path); bfree(s->tl_path);
    bfree(s->tpc_path); bfree(s->sidecar_base); bfree(s->sidecar_partial); bfree(s->sidecar_final);
    bfree(s->vbuf); bfree(s->abuf); bfree(s);
    atomic_fetch_sub(&g_instances, 1);
}

static void shuttle_update(void *data, obs_data_t *settings){
    shuttle_src *s = data; if (!s) return;
    pthread_mutex_lock(&s->m);
    s->restart_pending = 0; s->record_gap = 0;   /* a session started here replaces a pending restart (RECORDING_STARTED would otherwise start a second) */
    shuttle_stop(s);
    /* the end-of-file stop follows the current settings; a restart here begins the file again */
    if (atomic_load(&s->stop_on_eof) && !(obs_data_get_bool(settings, S_REPLAY_RESTART) && obs_data_get_bool(settings, S_REPLAY_STOP))) atomic_store(&s->stop_on_eof, 0);
    shuttle_start(s, settings);
    pthread_mutex_unlock(&s->m);
}

static void shuttle_defaults(obs_data_t *settings){
    obs_data_set_default_string(settings, S_INPUT, "svideo");
    obs_data_set_default_bool(settings, S_USE_REPLAY, false);
    obs_data_set_default_string(settings, S_REPLAY, "");
    obs_data_set_default_bool(settings, S_SIDECAR, true);
    obs_data_set_default_bool(settings, S_HRETIME, false);
    obs_data_set_default_bool(settings, S_REGISTRATION, true);
    obs_data_set_default_bool(settings, S_PARTIAL, true);
    obs_data_set_default_bool(settings, S_TPC, false);
    obs_data_set_default_bool(settings, S_REPLAY_RESTART, false);
    obs_data_set_default_bool(settings, S_REPLAY_STOP, false);
}

static obs_properties_t *shuttle_properties(void *data){
    (void)data;
    obs_properties_t *p = obs_properties_create();
    obs_property_t *in = obs_properties_add_list(p, S_INPUT, "Analog input", OBS_COMBO_TYPE_LIST, OBS_COMBO_FORMAT_STRING);
    obs_property_list_add_string(in, "S-Video", "svideo");
    obs_property_list_add_string(in, "Composite", "composite");
    obs_property_list_add_string(in, "Component", "component");
    obs_properties_add_bool(p, S_REGISTRATION, "Registration: correct vertical field placement (per tape; off publishes both fields at the nominal position)");
    obs_properties_add_bool(p, S_HRETIME, "H-retiming: repair horizontally mistimed lines (per tape; leave off for stable tapes)");
    obs_properties_add_bool(p, S_PARTIAL, "Search picture: also show units that are not whole (fast-forward, rewind, unlocked signal), stretched to the frame");
    obs_properties_add_bool(p, S_TPC, "Raw capture: save a .tpc beside each recording (about 85 GB per hour)");
    obs_properties_add_bool(p, S_USE_REPLAY, "Replay a tagged capture (.tpc) instead of the device");
    obs_properties_add_path(p, S_REPLAY, "Tagged capture file", OBS_PATH_FILE, "Tagged capture (*.tpc *.cap6)", NULL);
    obs_properties_add_bool(p, S_REPLAY_RESTART, "Replay: restart the file from the beginning when recording starts");
    obs_properties_add_bool(p, S_REPLAY_STOP, "Replay: stop the recording when the file ends (with the option above)");
    obs_properties_add_bool(p, S_SIDECAR, "Write the registration sidecar (<recording>.registration.csv) with each OBS recording");
    return p;
}

static uint32_t shuttle_width(void *d){ (void)d; return FP_FRAME_WIDTH; }
static uint32_t shuttle_height(void *d){ (void)d; return FP_FRAME_HEIGHT; }

static struct obs_source_info shuttle_info = {
    .id = "blackmagic_shuttle_frameserver",
    .type = OBS_SOURCE_TYPE_INPUT,
    .output_flags = OBS_SOURCE_ASYNC_VIDEO | OBS_SOURCE_AUDIO | OBS_SOURCE_DO_NOT_DUPLICATE | OBS_SOURCE_CONTROLLABLE_MEDIA,
    .get_name = shuttle_get_name,
    .create = shuttle_create,
    .destroy = shuttle_destroy,
    .update = shuttle_update,
    .get_defaults = shuttle_defaults,
    .video_tick = shuttle_video_tick,
    .get_properties = shuttle_properties,
    .get_width = shuttle_width,
    .get_height = shuttle_height,
    .icon_type = OBS_ICON_TYPE_CAMERA,
    .media_play_pause = media_play_pause,
    .media_restart = media_restart,
    .media_stop = media_stop,
    .media_get_duration = media_get_duration,
    .media_get_time = media_get_time,
    .media_set_time = media_set_time,
    .media_get_state = media_get_state,
};

bool obs_module_load(void){
    obs_register_source(&shuttle_info);
    blog(LOG_INFO, "[shuttle-source] loaded (libobs API %u.%u.%u)", LIBOBS_API_MAJOR_VER, LIBOBS_API_MINOR_VER, LIBOBS_API_PATCH_VER);
    return true;
}
void obs_module_unload(void){}
