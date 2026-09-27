/* Optional post-registration horizontal timing repair. Sources are immutable
 * full 48+525*1440-byte units; f1/f2 may belong to different transport units.
 * Destinations are caller-owned copies. No geometry/temporal state is touched. */
#ifndef FS_HRETIME_H
#define FS_HRETIME_H
#include <stddef.h>
#include <stdint.h>
enum { HRT_WIDTH=720, HRT_ROWS=480, HRT_FIELD_ROWS=240, HRT_MAX_BANDS=480 };
enum hrt_action { HRT_NONE, HRT_RETIME, HRT_INTERPOLATE, HRT_UNAVAILABLE };
typedef struct {
    int field, first, last; /* field 1/2, NTSC, before switch-row exclusion */
    float breaks[2];
} hrt_band;
typedef struct {
    int bands, retimed, interpolated, unavailable, first, last;
} hrt_field_result;
typedef struct {
    int measured, band_count, abstained;
    hrt_band band[HRT_MAX_BANDS];
    hrt_field_result field[2];
    uint8_t action[HRT_ROWS]; /* actual woven row: 2*i=f1, 2*i+1=f2 */
    int shift[HRT_ROWS];
    double blank[2], width[2], tolerance[2];
} hrt_result;
typedef struct hrt_workspace hrt_workspace;
size_t hrt_size(void);
void hrt_apply(hrt_workspace *, const uint8_t *f1, const uint8_t *f2,
               int d1, int d2, uint8_t *out1, uint8_t *out2, hrt_result *);
#endif
