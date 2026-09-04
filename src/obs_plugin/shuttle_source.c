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
#include "publish_copy.h"
#include "publish_queue.h"
#include <stdio.h>      /* renamex_np (macOS 10.12+): RENAME_EXCL makes the publish rename fail instead of replacing a file that appeared meanwhile */
#include "../frameserver/frameserver.h"

OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("shuttle-source", "en-US")

#define S_INPUT       "input"
#define S_REPLAY      "replay_path"
#define S_USE_REPLAY  "use_replay"
#define S_SIDECAR     "sidecar_with_recording"

#define AP_TICKS_TO_NS(t) ((uint64_t)((__uint128_t)(t) * 1000000000ull / AP_PTS_DEN))
#define RESIDUAL_STEP_TICKS 10            /* 2 samples: below this it is quantization, not a lost-sample event */

typedef struct {
    obs_source_t *source;
    frameserver *fs;
    uint8_t *vbuf;                         /* 720*480*2 UYVY staging (one frame; libobs copies) */
    int32_t *abuf; uint32_t abuf_frames;   /* S32 interleaved stereo staging */
    float color_matrix[16], color_min[3], color_max[3];
    _Atomic uint64_t frames_out, audio_frames_out, audio_steps;
    int64_t residual_applied_ticks;        /* accumulated residual steps applied to audio time */
    int64_t last_residual; int have_residual;
    _Atomic int ended; enum cc_end end_reason;
    pthread_mutex_t m;                      /* serializes session + sidecar transitions (frontend events, update, destroy) */
    int sidecar_enabled;                    /* property: attach the decision log to each OBS recording */
    char *sidecar_base;                     /* <recording path> of the active recording (bfree), NULL when none */
    unsigned sidecar_part;                  /* 0 = first file of this recording; N>0 => .partN+1 (source restarted mid-recording) */
    int sidecar_attached;
    char *sidecar_partial, *sidecar_final;  /* growing scratch path, and the published name it gets at detach */
    publish_queue *pq;                       /* persistent publisher (publish_queue.h): frontend callbacks only enqueue; drained at destroy */
    _Atomic uint64_t last_counter;          /* counter_ext of the last frame delivered to OBS */
} shuttle_src;
#define SIDECAR_SCRATCH_FMT "/private/tmp/shuttle-source-%u"   /* per-uid, mode 0700, non-synced; published by rename on the same filesystem, by verified copy otherwise */

static _Atomic int g_instances;

static const char *shuttle_get_name(void *td){ (void)td; return "Blackmagic Intensity Shuttle (frameserver)"; }

static void on_frame(void *ctx, const fp_frame *fr){
    shuttle_src *s = ctx;
    if (!fr->surface) return;
    IOSurfaceLock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    const uint8_t *base = IOSurfaceGetBaseAddress(fr->surface); size_t bpr = IOSurfaceGetBytesPerRow(fr->surface);
    for (unsigned y = 0; y < FP_FRAME_HEIGHT; y++) memcpy(s->vbuf + (size_t)y * FP_FRAME_WIDTH * 2, base + (size_t)y * bpr, FP_FRAME_WIDTH * 2);
    IOSurfaceUnlock(fr->surface, kIOSurfaceLockReadOnly, NULL);
    struct obs_source_frame f; memset(&f, 0, sizeof f);
    f.data[0] = s->vbuf; f.linesize[0] = FP_FRAME_WIDTH * 2;
    f.width = FP_FRAME_WIDTH; f.height = FP_FRAME_HEIGHT; f.format = VIDEO_FORMAT_UYVY;
    f.timestamp = (uint64_t)((__uint128_t)fr->pts_num * 1000000000ull / fr->pts_den);
    memcpy(f.color_matrix, s->color_matrix, sizeof f.color_matrix);
    memcpy(f.color_range_min, s->color_min, sizeof f.color_range_min); memcpy(f.color_range_max, s->color_max, sizeof f.color_range_max);
    f.full_range = false;
    obs_source_output_video(s->source, &f);
    atomic_fetch_add(&s->frames_out, 1); atomic_store(&s->last_counter, fr->counter_ext);
}

static void on_audio(void *ctx, const ap_block *b){
    shuttle_src *s = ctx;
    if (b->flags & AP_FLAG_UNANCHORED) return;            /* no device time yet: nothing honest to stamp */
    if (b->n_frames > s->abuf_frames) return;             /* cannot happen: publisher capacity == staging capacity */
    /* correlation residual: apply only where it STEPS (a lost-sample event), never continuously */
    if (!(b->flags & AP_FLAG_DISCONTINUITY_BEFORE)){
        if (s->have_residual){
            int64_t d = b->correlation_residual - s->last_residual;
            if (d > RESIDUAL_STEP_TICKS || d < -RESIDUAL_STEP_TICKS){ s->residual_applied_ticks += d; atomic_fetch_add(&s->audio_steps, 1); }
        }
    } else { s->residual_applied_ticks = 0; }             /* a new run re-anchors to video time on its own */
    s->last_residual = b->correlation_residual; s->have_residual = 1;
    const uint8_t *p = b->s24le;
    for (uint32_t i = 0; i < b->n_frames; i++){
        int32_t l = (int32_t)((uint32_t)p[0] << 8 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 24);
        int32_t r = (int32_t)((uint32_t)p[3] << 8 | (uint32_t)p[4] << 16 | (uint32_t)p[5] << 24);
        s->abuf[2 * i] = l; s->abuf[2 * i + 1] = r; p += AP_BYTES_PER_FRAME;
    }
    struct obs_source_audio a; memset(&a, 0, sizeof a);
    a.data[0] = (const uint8_t *)s->abuf; a.frames = b->n_frames;
    a.speakers = SPEAKERS_STEREO; a.format = AUDIO_FORMAT_32BIT; a.samples_per_sec = AP_SAMPLE_RATE;
    int64_t ticks = (int64_t)b->pts_num + s->residual_applied_ticks; if (ticks < 0) ticks = 0;
    a.timestamp = AP_TICKS_TO_NS((uint64_t)ticks);
    obs_source_output_audio(s->source, &a);
    atomic_fetch_add(&s->audio_frames_out, b->n_frames);
}

static void on_end(void *ctx, enum cc_end r){ shuttle_src *s = ctx; s->end_reason = r; atomic_store(&s->ended, 1);
    blog(LOG_INFO, "[shuttle-source] capture ended: reason %d", (int)r); }

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
static int same_filesystem(const char *dir_a, const char *dir_b){
    struct stat a, b; if (stat(dir_a, &a) != 0 || stat(dir_b, &b) != 0) return 0; return a.st_dev == b.st_dev;
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
    dstr_printf(&part, "%s/%s.partial-%08x%08x", scratch, basename(namecopy), (unsigned)arc4random(), (unsigned)arc4random()); bfree(namecopy);   /* random, exclusive (fs_log_start opens "wx") */
    if (fs_log_start(s->fs, part.array) == 0){
        s->sidecar_attached = 1; s->sidecar_part++;
        bfree(s->sidecar_partial); s->sidecar_partial = bstrdup(part.array);
        bfree(s->sidecar_final); s->sidecar_final = bstrdup(fin.array);
        blog(LOG_INFO, "[shuttle-source] sidecar attached -> %s (growing as %s); last unit delivered before attach: counter %llu — the recording's first frame is that unit or the next",
             fin.array, part.array, (unsigned long long)atomic_load(&s->last_counter));
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
    char *dircopy = bstrdup(final); char *scratchcopy = bstrdup(partial);
    int same = same_filesystem(dirname(scratchcopy), dirname(dircopy)); bfree(dircopy); bfree(scratchcopy);
    if (same){
        if (renamex_np(partial, final, RENAME_EXCL) != 0) blog(LOG_ERROR, "[shuttle-source] sidecar publish refused (%s); the complete file is left at %s", strerror(errno), partial);
        else blog(LOG_INFO, "[shuttle-source] sidecar published: %s", final);
    } else {
        int rc = publish_by_copy(partial, final);
        if (rc == -2) blog(LOG_ERROR, "[shuttle-source] sidecar publish by copy failed (%s) AND its staging file could not be removed: look for %s.partial-*; the complete file is at %s", strerror(errno), final, partial);
        else if (rc < 0) blog(LOG_ERROR, "[shuttle-source] sidecar publish by copy failed or did not verify (%s); the complete file is left at %s", strerror(errno), partial);
        else if (rc == 1) blog(LOG_WARNING, "[shuttle-source] sidecar published by verified copy: %s — the scratch copy was KEPT at %s (directory fsync or scratch removal failed: %s)", final, partial, strerror(errno));
        else blog(LOG_INFO, "[shuttle-source] sidecar published by verified copy (different filesystem; cache-visible on a cloud volume): %s", final);
    }
}
static void sidecar_publish(shuttle_src *s){
    if (!s->pq){ blog(LOG_ERROR, "[shuttle-source] no publisher thread: complete sidecar left at %s (wanted %s)", s->sidecar_partial, s->sidecar_final); return; }
    if (pq_enqueue(s->pq, s->sidecar_partial, s->sidecar_final) != 0)
        blog(LOG_ERROR, "[shuttle-source] publisher queue %s: complete sidecar left at %s (wanted %s)", errno == ENOSPC ? "full" : strerror(errno), s->sidecar_partial, s->sidecar_final);
}
static void sidecar_detach(shuttle_src *s){
    if (!s->sidecar_attached) return;
    s->sidecar_attached = 0;
    if (!s->fs){ blog(LOG_ERROR, "[shuttle-source] sidecar left unpublished at %s (capture already closed)", s->sidecar_partial); return; }
    if (fs_log_stop(s->fs) != 0){ blog(LOG_ERROR, "[shuttle-source] sidecar is INCOMPLETE (a row write or the close failed: disk full?); left unpublished at %s", s->sidecar_partial); return; }
    sidecar_publish(s);
}
static void frontend_event(enum obs_frontend_event ev, void *data){
    shuttle_src *s = data;
    pthread_mutex_lock(&s->m);
    switch (ev){
    case OBS_FRONTEND_EVENT_RECORDING_STARTED:
        if (recording_path(s) != 0){ blog(LOG_WARNING, "[shuttle-source] recording started but its path is unknown; no sidecar"); break; }
        s->sidecar_part = 0;
        if (!s->fs) blog(LOG_WARNING, "[shuttle-source] recording started while the capture is not running; sidecar starts when it does");
        sidecar_attach(s);
        break;
    case OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        sidecar_detach(s); bfree(s->sidecar_base); s->sidecar_base = NULL;
        break;
    default: break;
    }
    pthread_mutex_unlock(&s->m);
}

static void shuttle_stop(shuttle_src *s){
    if (!s->fs) return;
    /* Mid-recording restart: do NOT detach the log first — units delivered between a detach and the
     * capture stop would be recorded without sidecar rows. fs_stop closes the attached log after the
     * workers drain (every delivered unit has its row); publish afterwards from the session's stats. */
    int publish_after = s->sidecar_attached; s->sidecar_attached = 0;
    fs_stats st; fs_stop(s->fs); fs_get_stats(s->fs, &st);
    if (publish_after){
        if (st.log_last_file_errors) blog(LOG_ERROR, "[shuttle-source] sidecar part is INCOMPLETE (%llu write/close errors in this file); left unpublished at %s", (unsigned long long)st.log_last_file_errors, s->sidecar_partial);
        else sidecar_publish(s);
    }
    blog(LOG_INFO, "[shuttle-source] stopped: published %llu frames (%llu to OBS), audio %llu frames delivered / %llu dropped, pool-full %llu, ring-full %llu, holes %llu, residual steps applied %llu",
         (unsigned long long)st.published, (unsigned long long)atomic_load(&s->frames_out), (unsigned long long)st.audio_frames_delivered,
         (unsigned long long)st.audio_dropped_frames, (unsigned long long)st.dropped_pool_full, (unsigned long long)st.dropped_ring_full,
         (unsigned long long)st.holes, (unsigned long long)atomic_load(&s->audio_steps));
    fs_close(s->fs); s->fs = NULL;
}

static int shuttle_start(shuttle_src *s, obs_data_t *settings){
    fs_config cfg; memset(&cfg, 0, sizeof cfg);
    const char *input = obs_data_get_string(settings, S_INPUT);
    cfg.capture.input = !strcmp(input, "composite") ? CC_INPUT_COMPOSITE : !strcmp(input, "component") ? CC_INPUT_COMPONENT : CC_INPUT_SVIDEO;
    if (obs_data_get_bool(settings, S_USE_REPLAY)){
        const char *rp = obs_data_get_string(settings, S_REPLAY);
        if (!rp || !*rp){ blog(LOG_WARNING, "[shuttle-source] replay selected but no file given"); return -1; }
        cfg.capture.replay_path = rp; cfg.capture.replay_pace_us = 16000;    /* device cadence */
    }
    cfg.pool_units = 64; cfg.surface_pool = 6;
    cfg.sink.on_frame = on_frame; cfg.sink.ctx = s;
    cfg.audio_sink.on_block = on_audio; cfg.audio_sink.ctx = s;
    cfg.audio_block_frames = s->abuf_frames;
    cfg.on_end = on_end; cfg.end_ctx = s;
    atomic_store(&s->ended, 0); s->residual_applied_ticks = 0; s->have_residual = 0;
    atomic_store(&s->frames_out, 0); atomic_store(&s->audio_frames_out, 0); atomic_store(&s->audio_steps, 0);   /* per-session accounting */
    if (fs_open(&s->fs, &cfg) != 0){ blog(LOG_ERROR, "[shuttle-source] frameserver open failed (device present? replay path?)"); s->fs = NULL; return -1; }
    if (fs_start(s->fs) != 0){ blog(LOG_ERROR, "[shuttle-source] frameserver start failed"); fs_close(s->fs); s->fs = NULL; return -1; }
    blog(LOG_INFO, "[shuttle-source] started (%s)", cfg.capture.replay_path ? "replay" : "device");
    s->sidecar_enabled = obs_data_get_bool(settings, S_SIDECAR);
    if (s->sidecar_enabled && obs_frontend_recording_active() && s->sidecar_base) sidecar_attach(s);   /* restarted mid-recording: continue as the next part */
    return 0;
}

static void *shuttle_create(obs_data_t *settings, obs_source_t *source){
    if (atomic_fetch_add(&g_instances, 1) != 0){
        atomic_fetch_sub(&g_instances, 1);
        blog(LOG_ERROR, "[shuttle-source] a second instance was refused: the device has exactly one owner per process");
        return NULL;
    }
    shuttle_src *s = bzalloc(sizeof *s); s->source = source;
    s->vbuf = bmalloc((size_t)FP_FRAME_WIDTH * FP_FRAME_HEIGHT * 2);
    s->abuf_frames = 4096; s->abuf = bmalloc((size_t)s->abuf_frames * 2 * sizeof(int32_t));
    video_format_get_parameters(VIDEO_CS_601, VIDEO_RANGE_PARTIAL, s->color_matrix, s->color_min, s->color_max);
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
    pthread_mutex_init(&s->m, NULL);
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
    pthread_mutex_lock(&s->m); shuttle_stop(s); pthread_mutex_unlock(&s->m); pq_close(s->pq); s->pq = NULL; pthread_mutex_destroy(&s->m);   /* drains every queued sidecar before the code unloads */
    bfree(s->sidecar_base); bfree(s->sidecar_partial); bfree(s->sidecar_final);
    bfree(s->vbuf); bfree(s->abuf); bfree(s);
    atomic_fetch_sub(&g_instances, 1);
}

static void shuttle_update(void *data, obs_data_t *settings){
    shuttle_src *s = data; if (!s) return;
    pthread_mutex_lock(&s->m); shuttle_stop(s); shuttle_start(s, settings); pthread_mutex_unlock(&s->m);
}

static void shuttle_defaults(obs_data_t *settings){
    obs_data_set_default_string(settings, S_INPUT, "svideo");
    obs_data_set_default_bool(settings, S_USE_REPLAY, false);
    obs_data_set_default_string(settings, S_REPLAY, "");
    obs_data_set_default_bool(settings, S_SIDECAR, true);
}

static obs_properties_t *shuttle_properties(void *data){
    (void)data;
    obs_properties_t *p = obs_properties_create();
    obs_property_t *in = obs_properties_add_list(p, S_INPUT, "Analog input", OBS_COMBO_TYPE_LIST, OBS_COMBO_FORMAT_STRING);
    obs_property_list_add_string(in, "S-Video", "svideo");
    obs_property_list_add_string(in, "Composite", "composite");
    obs_property_list_add_string(in, "Component", "component");
    obs_properties_add_bool(p, S_USE_REPLAY, "Replay a tagged capture (.tpc) instead of the device");
    obs_properties_add_path(p, S_REPLAY, "Tagged capture file", OBS_PATH_FILE, "Tagged capture (*.tpc *.cap6)", NULL);
    obs_properties_add_bool(p, S_SIDECAR, "Write the registration sidecar (<recording>.registration.csv) with each OBS recording");
    return p;
}

static uint32_t shuttle_width(void *d){ (void)d; return FP_FRAME_WIDTH; }
static uint32_t shuttle_height(void *d){ (void)d; return FP_FRAME_HEIGHT; }

static struct obs_source_info shuttle_info = {
    .id = "blackmagic_shuttle_frameserver",
    .type = OBS_SOURCE_TYPE_INPUT,
    .output_flags = OBS_SOURCE_ASYNC_VIDEO | OBS_SOURCE_AUDIO | OBS_SOURCE_DO_NOT_DUPLICATE,
    .get_name = shuttle_get_name,
    .create = shuttle_create,
    .destroy = shuttle_destroy,
    .update = shuttle_update,
    .get_defaults = shuttle_defaults,
    .get_properties = shuttle_properties,
    .get_width = shuttle_width,
    .get_height = shuttle_height,
    .icon_type = OBS_ICON_TYPE_CAMERA,
};

bool obs_module_load(void){
    obs_register_source(&shuttle_info);
    blog(LOG_INFO, "[shuttle-source] loaded (libobs API %u.%u.%u)", LIBOBS_API_MAJOR_VER, LIBOBS_API_MINOR_VER, LIBOBS_API_PATCH_VER);
    return true;
}
void obs_module_unload(void){}
