// Minimal stand-ins for the libobs / obs-frontend-api functions shuttle_source.c calls, so its
// control logic can run in a test process against the real frameserver (tests_media_controls.c).
// They record what the plugin asked of OBS; they do not emulate OBS.
#include <obs-module.h>
#include <obs-frontend-api.h>
#include <util/dstr.h>
#include <util/platform.h>
#include <media-io/video-io.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "tests_obs_stubs.h"

const struct obs_source_info *stub_info;
_Atomic int stub_started_signals, stub_ended_signals;
_Atomic uint64_t stub_video_frames;
int stub_verbose;
struct obs_data { _Atomic(const char *) path; _Atomic int use_replay, restart_on_record; };   /* OBS's obs_data is thread-safe; so is this */
void *stub_data; obs_source_t *stub_source;
static obs_frontend_event_cb g_event_cb; static void *g_event_param;
void stub_fire_event(enum obs_frontend_event ev){ if (g_event_cb) g_event_cb(ev, g_event_param); }
static struct obs_data g_settings;
void stub_restart_on_record(int on){ atomic_store(&g_settings.restart_on_record, on); }
obs_data_t *stub_settings(const char *path, int use_replay){ atomic_store(&g_settings.path, path); atomic_store(&g_settings.use_replay, use_replay); return &g_settings; }

_Atomic int stub_late_reports;
void blog(int level, const char *fmt, ...){
    char line[2048]; va_list ap; va_start(ap, fmt); vsnprintf(line, sizeof line, fmt, ap); va_end(ap);
    if (strstr(line, "delivery timing: counter")) atomic_fetch_add(&stub_late_reports, 1);
    if (stub_verbose || level <= LOG_WARNING) fprintf(stderr, "%s\n", line);
}
void *bmalloc(size_t n){ return malloc(n ? n : 1); }
void bfree(void *p){ free(p); }
void *bmemdup(const void *p, size_t n){ void *q = bmalloc(n); memcpy(q, p, n); return q; }
void dstr_ncat(struct dstr *d, const char *a, const size_t n){
    d->array = realloc(d->array, d->len + n + 1); memcpy(d->array + d->len, a, n); d->len += n; d->array[d->len] = 0; d->capacity = d->len + 1;
}
static void vcat(struct dstr *d, const char *f, va_list ap){ char *t = NULL; if (vasprintf(&t, f, ap) >= 0){ dstr_ncat(d, t, strlen(t)); free(t); } }
void dstr_printf(struct dstr *d, const char *f, ...){ if (d->array) d->array[0] = 0; d->len = 0; va_list ap; va_start(ap, f); vcat(d, f, ap); va_end(ap); }
void dstr_catf(struct dstr *d, const char *f, ...){ va_list ap; va_start(ap, f); vcat(d, f, ap); va_end(ap); }
bool text_lookup_getstr(lookup_t *l, const char *v, const char **out){ (void)l; *out = v; return false; }
void text_lookup_destroy(lookup_t *l){ (void)l; }
lookup_t *obs_module_load_locale(obs_module_t *m, const char *d, const char *l){ (void)m; (void)d; (void)l; return NULL; }
bool obs_data_get_bool(obs_data_t *d, const char *name){
    if (!strcmp(name, "use_replay")) return atomic_load(&d->use_replay);
    if (!strcmp(name, "replay_restart_on_record")) return atomic_load(&d->restart_on_record);
    if (!strcmp(name, "registration")) return true;
    if (!strcmp(name, "setup_7_5_ire")) return true;   /* the device default: setup bit on */
    return false;   /* hretime, raw_tpc, restart/stop-on-record, sidecar: off */
}
const char *obs_data_get_string(obs_data_t *d, const char *name){ return !strcmp(name, "replay_path") ? atomic_load(&d->path) : !strcmp(name, "input") ? "svideo" : ""; }
void obs_data_release(obs_data_t *d){ (void)d; }
void obs_data_set_default_bool(obs_data_t *d, const char *n, bool v){ (void)d; (void)n; (void)v; }
void obs_data_set_default_string(obs_data_t *d, const char *n, const char *v){ (void)d; (void)n; (void)v; }
obs_property_t *obs_properties_add_text(obs_properties_t *p, const char *n, const char *d, enum obs_text_type t){ (void)p; (void)n; (void)d; (void)t; return NULL; }
obs_data_t *obs_source_get_settings(const obs_source_t *s){ (void)s; return &g_settings; }
void obs_frontend_add_event_callback(obs_frontend_event_cb cb, void *p){ g_event_cb = cb; g_event_param = p; }
void obs_frontend_remove_event_callback(obs_frontend_event_cb cb, void *p){ (void)cb; (void)p; g_event_cb = NULL; }
char *obs_frontend_get_last_recording(void){ return NULL; }
obs_output_t *obs_frontend_get_recording_output(void){ return NULL; }
bool obs_frontend_recording_active(void){ return false; }
void obs_frontend_recording_stop(void){}
/* streaming (the discard stream drives the same session logic as recording) */
obs_output_t *obs_frontend_get_streaming_output(void){ return NULL; }
bool obs_frontend_streaming_active(void){ return false; }
void obs_frontend_streaming_stop(void){}
config_t *obs_frontend_get_profile_config(void){ return NULL; }
char *obs_frontend_get_current_record_output_path(void){ return NULL; }
const char *config_get_string(config_t *c, const char *sec, const char *n){ (void)c; (void)sec; (void)n; return NULL; }
bool config_get_bool(config_t *c, const char *sec, const char *n){ (void)c; (void)sec; (void)n; return false; }
char *os_generate_formatted_filename(const char *ext, bool space, const char *fmt){ (void)ext; (void)space; (void)fmt; return NULL; }
bool os_file_exists(const char *p){ return access(p, F_OK) == 0; }
void dstr_copy(struct dstr *d, const char *a){ dstr_printf(d, "%s", a); }
void dstr_ncopy(struct dstr *d, const char *a, const size_t n){ if (d->array) d->array[0] = 0; d->len = 0; dstr_ncat(d, a, n); }
void discard_stream_register(void){}
void tracking_meter_menu_register(void){}
void tracking_meter_shutdown(void){}
int discard_service_selected(void){ return 1; }
void *obs_obj_get_data(void *o){ return o == stub_source ? stub_data : NULL; }
bool obs_output_active(const obs_output_t *o){ (void)o; return false; }
void obs_output_release(obs_output_t *o){ (void)o; }
obs_properties_t *obs_properties_create(void){ return NULL; }
obs_property_t *obs_properties_add_bool(obs_properties_t *p, const char *n, const char *d){ (void)p; (void)n; (void)d; return NULL; }
obs_property_t *obs_properties_add_list(obs_properties_t *p, const char *n, const char *d, enum obs_combo_type t, enum obs_combo_format f){ (void)p; (void)n; (void)d; (void)t; (void)f; return NULL; }
obs_property_t *obs_properties_add_path(obs_properties_t *p, const char *n, const char *d, enum obs_path_type t, const char *f, const char *dp){ (void)p; (void)n; (void)d; (void)t; (void)f; (void)dp; return NULL; }
size_t obs_property_list_add_string(obs_property_t *p, const char *n, const char *v){ (void)p; (void)n; (void)v; return 0; }
void obs_register_source_s(const struct obs_source_info *info, size_t size){ (void)size; stub_info = info; }
obs_weak_source_t *obs_source_get_weak_source(obs_source_t *s){ return (obs_weak_source_t *)s; }   /* the recording output never starts here, */
obs_source_t *obs_weak_source_get_source(obs_weak_source_t *w){ return (obs_source_t *)w; }        /* so restart_check finds the source alive */
void obs_weak_source_release(obs_weak_source_t *w){ (void)w; }
void obs_source_release(obs_source_t *s){ (void)s; }
void obs_source_media_started(obs_source_t *s){ (void)s; atomic_fetch_add(&stub_started_signals, 1); }
void obs_source_media_ended(obs_source_t *s){ (void)s; atomic_fetch_add(&stub_ended_signals, 1); }
/* What the plugin hands OBS: I210, byte linesizes 1440/720/720, contiguous Y/U/V planes, codes as 4c
 * (fixture_plain is Y16/C128 everywhere -> 64/512), range clamp opened, limited range kept. */
_Atomic uint64_t stub_frame_errors;
_Atomic uint64_t stub_blank_calls;
void obs_source_output_video(obs_source_t *s, const struct obs_source_frame *f){
    (void)s; if (!f){ atomic_fetch_add(&stub_blank_calls, 1); return; }
    atomic_fetch_add(&stub_video_frames, 1);
    const uint16_t *y = (const uint16_t *)f->data[0], *u = (const uint16_t *)f->data[1], *v = (const uint16_t *)f->data[2];
    int ok = f->format == VIDEO_FORMAT_I210 && f->width == 720 && f->height == 480 && !f->full_range &&
             f->linesize[0] == 1440 && f->linesize[1] == 720 && f->linesize[2] == 720 &&
             f->data[1] == f->data[0] + 720 * 480 * 2 && f->data[2] == f->data[1] + 360 * 480 * 2 &&
             f->color_range_min[0] == 0.0f && f->color_range_max[0] == 1.0f;
    for (unsigned i = 0; ok && i < 720 * 480; i += 997) ok = y[i] == 64;
    for (unsigned i = 0; ok && i < 360 * 480; i += 499) ok = u[i] == 512 && v[i] == 512;
    if (!ok && atomic_fetch_add(&stub_frame_errors, 1) == 0)
        fprintf(stderr, "stub: frame not as expected: format %d %ux%u linesize %u/%u/%u full_range %d y0 %u u0 %u\n", (int)f->format,
                f->width, f->height, f->linesize[0], f->linesize[1], f->linesize[2], (int)f->full_range, y ? y[0] : 0, u ? u[0] : 0);
}
void obs_source_output_audio(obs_source_t *s, const struct obs_source_audio *a){ (void)s; (void)a; }
void obs_source_set_async_decoupled(obs_source_t *s, bool v){ (void)s; (void)v; }
void obs_source_set_async_unbuffered(obs_source_t *s, bool v){ (void)s; (void)v; }
void obs_source_set_deinterlace_field_order(obs_source_t *s, enum obs_deinterlace_field_order o){ (void)s; (void)o; }
void obs_source_set_deinterlace_mode(obs_source_t *s, enum obs_deinterlace_mode m){ (void)s; (void)m; }
bool video_format_get_parameters(enum video_colorspace c, enum video_range_type r, float m[16], float mn[3], float mx[3]){
    (void)c; (void)r; memset(m, 0, 16 * sizeof *m); memset(mn, 0, 3 * sizeof *mn); memset(mx, 0, 3 * sizeof *mx); return true;
}
bool video_format_get_parameters_for_format(enum video_colorspace c, enum video_range_type r, enum video_format f, float m[16], float mn[3], float mx[3]){
    (void)f; return video_format_get_parameters(c, r, m, mn, mx);
}
uint64_t os_gettime_ns(void){ return clock_gettime_nsec_np(CLOCK_UPTIME_RAW); }
