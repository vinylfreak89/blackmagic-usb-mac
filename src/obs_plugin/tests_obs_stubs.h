// tests_obs_stubs.c: what the plugin asked of OBS during a test.
#ifndef TESTS_OBS_STUBS_H
#define TESTS_OBS_STUBS_H
#include <obs-module.h>
#include <stdatomic.h>
extern const struct obs_source_info *stub_info;       /* registered by obs_module_load */
extern _Atomic int stub_started_signals, stub_ended_signals;
extern _Atomic uint64_t stub_video_frames;
extern int stub_verbose;
obs_data_t *stub_settings(const char *path, int use_replay);
#endif
