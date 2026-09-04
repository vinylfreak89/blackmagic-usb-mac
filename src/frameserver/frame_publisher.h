// frame_publisher — the delivery edge of the frameserver (design doc §10 "where CoreVideo fits").
//
// Input: one exact 756,048-byte 0xe801 transport unit (48-byte header + 525 lines × 1440 B UYVY)
// plus the registration engine's applied per-field offsets (d1, d2). Output: a 720×480
// interlaced UYVY ('2vuy') frame in an IOSurface, top-field-first, rows interleaved
// field1/field2, with a monotonic PTS derived from the extended unit counter.
//
// Field crops follow §7: field 1 is read from unit rows 19+d1 .. 258+d1, field 2 from
// 282+d2 .. 521+d2 (NTSC lines 23/286 nominal). The crop is selection, never synthesis: a displaced
// field's vacated edge is whatever the source carries there.
//
// Honesty rules (§8 property 7): the surface pool is bounded; a consumer holds a surface by
// IOSurfaceIncrementUseCount and releases it with IOSurfaceDecrementUseCount. When no surface
// is free the unit is DROPPED and counted — never blocked, never silently skipped.
// Nothing here allocates on the per-unit path except the surface fill itself.
#ifndef FRAME_PUBLISHER_H
#define FRAME_PUBLISHER_H
#include <stdint.h>
#include <stddef.h>
#include <IOSurface/IOSurface.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FP_UNIT_BYTES     756048u
#define FP_UNIT_HEADER    48u
#define FP_LINE_BYTES     1440u
#define FP_SOURCE_LINES   525u
// Crop start = the standard's first VISIBLE line of each field: SMPTE RP-202 / ATSC A/54A encode
// lines 23-262 (field 1) and 286-525 (field 2) for 480i. In the Shuttle's unit the deck's line-21
// (caption) insert is row 17 and the field-2 equivalent (line 284) is row 280, so line 23 is row 19
// and line 286 is row 282. Starting at 17/280 (lines 21/284) put the caption line and the blank
// line 22 at the top of every frame (measured 2026-09-04, CLAUDE.md §6).
#define FP_FIELD1_START   19
#define FP_FIELD2_START   282
#define FP_FIELD_LINES    240
#define FP_FRAME_WIDTH    720u
#define FP_FRAME_HEIGHT   480u

enum fp_transport { FP_TRANSPORT_COMPLETE = 0, FP_TRANSPORT_SHORT = 1, FP_TRANSPORT_HOLE = 2 };

typedef struct {
    IOSurfaceRef surface;      // '2vuy', 720×480, interlaced TFF; use-count held by consumer
    uint64_t pts_num;          // PTS = pts_num / pts_den seconds (monotonic per epoch)
    uint32_t pts_den;
    uint64_t counter_ext;      // extended unit counter this frame came from (64-bit: monotonic epoch contract)
    int8_t   d1, d2;           // applied per-field offsets used for the crop
    uint8_t  transport;        // enum fp_transport of the source unit
    uint8_t  audio_pts_known;  // 1 if audio_pts_num carries this unit's time on the AUDIO clock
    uint64_t audio_pts_num;    // audio-clock time of this unit's resync (1/240000 s), for audio-as-master consumers
} fp_frame;

typedef struct fp_publisher fp_publisher;

typedef struct {
    // Called synchronously for every published frame. To keep the surface beyond the call,
    // IOSurfaceIncrementUseCount(frame->surface) and Decrement when done.
    void (*on_frame)(void *ctx, const fp_frame *frame);
    void *ctx;
} fp_sink;

typedef struct {
    uint64_t published, dropped_no_free_surface, rejected_bad_args;
    unsigned pool_size, pool_in_use;
} fp_stats;

// pool_size surfaces are created up front (allocation happens here, never per unit).
int  fp_open (fp_publisher **out, unsigned pool_size, const fp_sink *sink);
// Assemble and publish one unit. d1/d2 are clamped to keep every crop line inside the
// 525-line source; returns 0 on publish, 1 if dropped (no free surface), -1 on bad args.
int  fp_publish(fp_publisher *p, const uint8_t *unit, size_t unit_len,
                uint64_t counter_ext, int d1, int d2, uint8_t transport,
                int audio_pts_known, uint64_t audio_pts_num);
void fp_get_stats(const fp_publisher *p, fp_stats *out);
void fp_close(fp_publisher *p);

// Pure assembly, no IOSurface: writes the 480-line interlaced frame (1440 B/row) into dst.
// Exposed for tests and for consumers that own their buffers.
void fp_assemble(uint8_t *dst, const uint8_t *unit, int d1, int d2);

#ifdef __cplusplus
}
#endif
#endif
