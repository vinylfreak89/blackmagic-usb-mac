// tests_obs_stubs.c: what the plugin asked of OBS during a test.
#ifndef TESTS_OBS_STUBS_H
#define TESTS_OBS_STUBS_H
#include <obs-module.h>
#include <stdatomic.h>
extern const struct obs_source_info *stub_info;       /* registered by obs_module_load */
extern _Atomic int stub_started_signals, stub_ended_signals;
extern _Atomic uint64_t stub_video_frames;
extern _Atomic uint64_t stub_blank_calls;
extern _Atomic uint64_t stub_frame_errors;   /* frames handed to OBS not in the expected I210 layout/values */
extern int stub_verbose;
extern _Atomic int stub_late_reports;   /* late-handoff WARNINGs the plugin logged */
void stub_expect(const char *text);       /* lines containing text are counted, not printed, until stub_expect_end */
int stub_expect_end(const char *text);    /* the count since stub_expect (same pointer) */
obs_data_t *stub_settings(const char *path, int use_replay);
#include <obs-frontend-api.h>
extern void *stub_data; extern obs_source_t *stub_source;   /* the test's source and the plugin's data for it */
void stub_fire_event(enum obs_frontend_event ev);           /* as OBS's frontend would, on the calling thread */
void stub_restart_on_record(int on);
#endif
