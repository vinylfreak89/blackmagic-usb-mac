/* Optional post-registration horizontal timing repair. Sources are immutable
 * full 48+525*1440-byte units; f1/f2 may belong to different transport units.
 * Destinations are caller-owned copies. Geometry is untouched; this workspace
 * alone owns the causal clean-line summary history. */
#ifndef FS_HRETIME_H
#define FS_HRETIME_H
#include <stddef.h>
#include <stdint.h>
enum { HRT_WIDTH=720, HRT_ROWS=480, HRT_FIELD_ROWS=240, HRT_MAX_BANDS=480 };
enum hrt_action { HRT_NONE, HRT_RETIME, HRT_INTERPOLATE, HRT_UNAVAILABLE, HRT_CONTENT };
enum hrt_reason { HRT_CORRELATION=1, HRT_MISSING_EDGE=2, HRT_BLANKING_SIZE=4,
                  HRT_INTERIOR_BLANK=8, HRT_BAND_FILL=16 };
/* Coordinate directions: '-' earlier, '+' later; symmetric about normal. */
enum hrt_edge { HRT_LEFT_EARLIER=1, HRT_LEFT_LATER=2,
                HRT_RIGHT_EARLIER=4, HRT_RIGHT_LATER=8, HRT_EDGES_KNOWN=16 };
typedef struct {
    int field, first, last; /* field 1/2, NTSC, before switch-row exclusion */
    float breaks[2];
    int top_fallback, displaced[2];
} hrt_band;
typedef struct {
    int bands, retimed, interpolated, unavailable, first, last, content;
} hrt_field_result;
typedef struct {
    int measured, band_count, abstained;
    hrt_band band[HRT_MAX_BANDS];
    hrt_field_result field[2];
    uint8_t action[HRT_ROWS]; /* actual woven row: 2*i=f1, 2*i+1=f2 */
    int shift[HRT_ROWS];
    uint8_t reason[HRT_ROWS];
    double r_line[HRT_ROWS],r_neighbours[HRT_ROWS],deficit[HRT_ROWS];
    double correlation_limit[2],typical_band_length;
    double blank[2], width[2], tolerance[2];
    double edge_median[2][2], edge_spread[2][2]; /* field, left/right */
    uint8_t edge_moved[HRT_ROWS]; /* directions, '=' if known but within spread */
} hrt_result;
typedef struct hrt_workspace hrt_workspace;
size_t hrt_size(void);
/* Zero-initialise workspace at open; all temporal storage is preallocated. */
void hrt_reset(hrt_workspace *);
void hrt_begin(hrt_workspace *,uint64_t f1_counter,uint64_t f2_counter,uint64_t epoch,int reset);
void hrt_apply(hrt_workspace *, const uint8_t *f1, const uint8_t *f2,
               int d1, int d2, uint8_t *out1, uint8_t *out2, hrt_result *);
#endif
