/* Optional downstream concealment. Never an input to registration. */
#ifndef FS_TEAR_REPAIR_H
#define FS_TEAR_REPAIR_H
#include <stdint.h>

enum { TR_WIDTH=720, TR_LINE_BYTES=1440, TR_ROWS=240, TR_RASTER_ROWS=525 };
typedef struct {
    double blank;
    int first, last, flagged, repaired, fill, interpolate; /* flagged NTSC extent */
    int repaired_first, repaired_last; /* NTSC lines; 0 = none */
} tr_field_result;
typedef struct { tr_field_result field[2]; } tr_result;

/* Pure detector; range is storage rows [start,end). The larger reference-census
 * ranges are supported for diagnostic comparison, not for publication. */
void tr_detect(const uint8_t *raster, int field, int start, int end,
               uint8_t picture[TR_RASTER_ROWS], uint8_t flagged[TR_RASTER_ROWS],
               tr_field_result *result);

/* Two raw UYVY rasters belonging to the ACTUAL woven frame; destinations must
 * contain copies and must not alias either source. Only repaired aperture rows
 * are written. Aligned destinations may be the same full-raster copy. */
void tr_repair(const uint8_t *top, const uint8_t *bottom, int d1, int d2,
               uint8_t *out_top, uint8_t *out_bottom, tr_result *result);
#endif
