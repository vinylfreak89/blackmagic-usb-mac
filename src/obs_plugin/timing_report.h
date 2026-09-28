#ifndef SHUTTLE_TIMING_REPORT_H
#define SHUTTLE_TIMING_REPORT_H
/* Late-delivery reports, written off the video worker.
 *
 * The frame sink runs on the frameserver's video worker. Logging a late handoff there (blog) is a
 * flushed write to OBS's log file on that thread; under disk load it blocked long enough to make
 * the NEXT handoff late, so one late frame reported itself into a cascade (measured 2026-09-28 in
 * the replay tool: every large gap followed a printed report). Here the worker only copies an event
 * into a preallocated ring and signals; a reporter thread hands events to `emit`. A full ring
 * drops the report, never waits, and counts it (tr_close returns the count). Single producer. */
#include <stdint.h>
#include "frameserver.h"

typedef struct { uint64_t counter, gap_ns, call_ns; fs_handoff_timing h; } tr_event;
typedef struct timing_report timing_report;

/* capacity: events held while the reporter is behind. emit runs on the reporter thread only. */
int      tr_open(timing_report **out, unsigned capacity, void (*emit)(void *ctx, const tr_event *e), void *ctx);
void     tr_post(timing_report *r, const tr_event *e);   /* producer: copy + signal; never blocks, never allocates */
uint64_t tr_close(timing_report *r);                     /* emits what is queued, joins, frees; returns reports dropped */
#endif
