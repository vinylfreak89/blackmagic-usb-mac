#ifndef BLACKMAGIC_USB_MAC_CEA608_H
#define BLACKMAGIC_USB_MAC_CEA608_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    CEA608_PIXELS_PER_LINE = 720,
    CEA608_BYTES_PER_UYVY_LINE = 1440,
};

typedef struct cea608_decode_result {
    bool run_in_present;
    bool framing_present;
    bool parity_valid;
    uint8_t byte1;
    uint8_t byte2;
    uint8_t run_length;
    double amplitude;
} cea608_decode_result;

typedef struct cea608_candidate {
    int16_t raster_row;
    uint8_t byte1;
    uint8_t byte2;
    double amplitude;
} cea608_candidate;

/* Decode one 720-sample luma line. Allocation-free and deterministic. */
void cea608_decode_luma(const uint8_t luma[CEA608_PIXELS_PER_LINE],
                        cea608_decode_result *out);

/* Scan inclusive raster rows in ascending order from a packed UYVY raster. */
size_t cea608_scan_uyvy(const uint8_t *raster, int first_row, int last_row,
                        cea608_candidate *out, size_t capacity);

#endif
