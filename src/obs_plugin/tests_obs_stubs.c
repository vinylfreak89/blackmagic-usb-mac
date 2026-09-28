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
#include <time.h>
#include "tests_obs_stubs.h"

const struct obs_source_info *stub_info;
_Atomic int stub_started_signals, stub_ended_signals;
_Atomic uint64_t stub_video_frames;
int stub_verbose;
struct obs_data { _Atomic(const char *) path; _Atomic int use_replay; };   /* OBS's obs_data is thread-safe; so is this */
static struct obs_data g_settings;
obs_data_t *stub_settings(const char *path, int use_replay){ atomic_store(&g_settings.path, path); atomic_store(&g_settings.use_replay, use_replay); return &g_settings; }

void blog(int level, const char *fmt, ...){
    if (!stub_verbose && level > LOG_WARNING) return;
    va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap); fputc('\n', stderr);
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
    if (!strcmp(name, "registration")) return true;
    return false;   /* hretime, raw_tpc, restart/stop-on-record, sidecar: off */
}
const char *obs_data_get_string(obs_data_t *d, const char *name){ return !strcmp(name, "replay_path") ? atomic_load(&d->path) : !strcmp(name, "input") ? "svideo" : ""; }
void obs_data_release(obs_data_t *d){ (void)d; }
void obs_data_set_default_bool(obs_data_t *d, const char *n, bool v){ (void)d; (void)n; (void)v; }
void obs_data_set_default_string(obs_data_t *d, const char *n, const char *v){ (void)d; (void)n; (void)v; }
obs_data_t *obs_source_get_settings(const obs_source_t *s){ (void)s; return &g_settings; }
void obs_frontend_add_event_callback(obs_frontend_event_cb cb, void *p){ (void)cb; (void)p; }
void obs_frontend_remove_event_callback(obs_frontend_event_cb cb, void *p){ (void)cb; (void)p; }
char *obs_frontend_get_last_recording(void){ return NULL; }
obs_output_t *obs_frontend_get_recording_output(void){ return NULL; }
bool obs_frontend_recording_active(void){ return false; }
void obs_frontend_recording_stop(void){}
void *obs_obj_get_data(void *o){ (void)o; return NULL; }
bool obs_output_active(const obs_output_t *o){ (void)o; return false; }
void obs_output_release(obs_output_t *o){ (void)o; }
obs_properties_t *obs_properties_create(void){ return NULL; }
obs_property_t *obs_properties_add_bool(obs_properties_t *p, const char *n, const char *d){ (void)p; (void)n; (void)d; return NULL; }
obs_property_t *obs_properties_add_list(obs_properties_t *p, const char *n, const char *d, enum obs_combo_type t, enum obs_combo_format f){ (void)p; (void)n; (void)d; (void)t; (void)f; return NULL; }
obs_property_t *obs_properties_add_path(obs_properties_t *p, const char *n, const char *d, enum obs_path_type t, const char *f, const char *dp){ (void)p; (void)n; (void)d; (void)t; (void)f; (void)dp; return NULL; }
size_t obs_property_list_add_string(obs_property_t *p, const char *n, const char *v){ (void)p; (void)n; (void)v; return 0; }
void obs_register_source_s(const struct obs_source_info *info, size_t size){ (void)size; stub_info = info; }
obs_weak_source_t *obs_source_get_weak_source(obs_source_t *s){ (void)s; return NULL; }
obs_source_t *obs_weak_source_get_source(obs_weak_source_t *w){ (void)w; return NULL; }
void obs_weak_source_release(obs_weak_source_t *w){ (void)w; }
void obs_source_release(obs_source_t *s){ (void)s; }
void obs_source_media_started(obs_source_t *s){ (void)s; atomic_fetch_add(&stub_started_signals, 1); }
void obs_source_media_ended(obs_source_t *s){ (void)s; atomic_fetch_add(&stub_ended_signals, 1); }
void obs_source_output_video(obs_source_t *s, const struct obs_source_frame *f){ (void)s; if (f) atomic_fetch_add(&stub_video_frames, 1); }
void obs_source_output_audio(obs_source_t *s, const struct obs_source_audio *a){ (void)s; (void)a; }
void obs_source_set_async_decoupled(obs_source_t *s, bool v){ (void)s; (void)v; }
void obs_source_set_async_unbuffered(obs_source_t *s, bool v){ (void)s; (void)v; }
void obs_source_set_deinterlace_field_order(obs_source_t *s, enum obs_deinterlace_field_order o){ (void)s; (void)o; }
void obs_source_set_deinterlace_mode(obs_source_t *s, enum obs_deinterlace_mode m){ (void)s; (void)m; }
bool video_format_get_parameters(enum video_colorspace c, enum video_range_type r, float m[16], float mn[3], float mx[3]){
    (void)c; (void)r; memset(m, 0, 16 * sizeof *m); memset(mn, 0, 3 * sizeof *mn); memset(mx, 0, 3 * sizeof *mx); return true;
}
uint64_t os_gettime_ns(void){ return clock_gettime_nsec_np(CLOCK_UPTIME_RAW); }
