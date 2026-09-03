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
// Threading: the video sink runs on the frameserver's video worker, the audio sink on its audio
// worker; obs_source_output_video/audio copy under libobs's own locks and return. Neither sink
// blocks, allocates, or touches OBS's graphics thread. One session per process: a second source
// instance is refused (the device has exactly one owner) — OBS_SOURCE_DO_NOT_DUPLICATE.
#include <obs-module.h>
#include <util/platform.h>
#include <media-io/video-io.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <IOSurface/IOSurface.h>
#include "../frameserver/frameserver.h"

OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("shuttle-source", "en-US")

#define S_INPUT       "input"
#define S_REPLAY      "replay_path"
#define S_USE_REPLAY  "use_replay"

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
} shuttle_src;

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
    atomic_fetch_add(&s->frames_out, 1);
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

static void shuttle_stop(shuttle_src *s){
    if (!s->fs) return;
    fs_stats st; fs_stop(s->fs); fs_get_stats(s->fs, &st);
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
    if (shuttle_start(s, settings) != 0) blog(LOG_WARNING, "[shuttle-source] created without a running capture; fix settings");
    return s;
}

static void shuttle_destroy(void *data){
    shuttle_src *s = data; if (!s) return;
    shuttle_stop(s);
    bfree(s->vbuf); bfree(s->abuf); bfree(s);
    atomic_fetch_sub(&g_instances, 1);
}

static void shuttle_update(void *data, obs_data_t *settings){
    shuttle_src *s = data; if (!s) return;
    shuttle_stop(s); shuttle_start(s, settings);
}

static void shuttle_defaults(obs_data_t *settings){
    obs_data_set_default_string(settings, S_INPUT, "svideo");
    obs_data_set_default_bool(settings, S_USE_REPLAY, false);
    obs_data_set_default_string(settings, S_REPLAY, "");
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
