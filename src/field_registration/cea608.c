#include "cea608.h"

#include <math.h>
#include <string.h>

enum { SEARCH_LO = 10, SEARCH_HI = 230, MAX_PEAKS = 42 };
static const double CELL = 1.986e-6 * 13.5e6;
static const double PI = 3.14159265358979323846264338327950288;

static double sample_peak(const uint8_t row[CEA608_PIXELS_PER_LINE],
                          double peak, double low)
{
    long i = lround(peak);
    if (i >= CEA608_PIXELS_PER_LINE) return low;
    int begin = i < 2 ? 0 : (int)i - 2;
    int end = (int)i + 3;
    if (end > CEA608_PIXELS_PER_LINE) end = CEA608_PIXELS_PER_LINE;
    double total = 0.0;
    for (int x = begin; x < end; ++x) total += row[x];
    return total / (double)(end - begin);
}

void cea608_decode_luma(const uint8_t row[CEA608_PIXELS_PER_LINE],
                        cea608_decode_result *out)
{
    memset(out, 0, sizeof *out);
    double mean = 0.0;
    uint8_t high = 0, low = 255;
    for (int x = SEARCH_LO; x < SEARCH_HI; ++x) {
        mean += row[x];
        if (row[x] > high) high = row[x];
        if (row[x] < low) low = row[x];
    }
    mean /= (double)(SEARCH_HI - SEARCH_LO);
    const double w = 2.0 * PI / CELL;
    const double step_c = cos(w), step_s = sin(w);
    double carrier_c = cos(w * SEARCH_LO);
    double carrier_s = sin(w * SEARCH_LO);
    double c = 0.0, s = 0.0;
    for (int x = SEARCH_LO; x < SEARCH_HI; ++x) {
        const double value = (double)row[x] - mean;
        c += value * carrier_c;
        s += value * carrier_s;
        const double next_c = carrier_c * step_c - carrier_s * step_s;
        carrier_s = carrier_s * step_c + carrier_c * step_s;
        carrier_c = next_c;
    }
    out->amplitude = hypot(c, s) * 2.0 / (SEARCH_HI - SEARCH_LO);
    if (out->amplitude < 35.0) return;
    out->run_in_present = true;

    const double phase = atan2(s, c);
    double peaks[MAX_PEAKS];
    uint8_t bits[MAX_PEAKS];
    int count = 0;
    for (int k = -2; k < 40; ++k) {
        const double peak = (phase + 2.0 * PI * (double)k) / w;
        if (peak >= SEARCH_LO &&
            peak < SEARCH_HI + 24.0 * CELL)
            peaks[count++] = peak;
    }
    const double threshold = ((double)high + (double)low) * 0.5;
    for (int i = 0; i < count; ++i)
        bits[i] = sample_peak(row, peaks[i], low) > threshold;

    int first = 0;
    while (first < count && !bits[first]) ++first;
    if (first == count) return;
    int after = first;
    while (after < count && bits[after]) ++after;
    const int run = after - first;
    out->run_length = (uint8_t)run;
    if (run < 5 || run > 9 || after + 19 > count) return;
    if (bits[after] || bits[after + 1] || !bits[after + 2]) return;
    out->framing_present = true;
    uint8_t b1 = 0, b2 = 0;
    for (int bit = 0; bit < 8; ++bit) {
        b1 |= (uint8_t)(bits[after + 3 + bit] << bit);
        b2 |= (uint8_t)(bits[after + 11 + bit] << bit);
    }
    out->byte1 = b1;
    out->byte2 = b2;
    out->parity_valid = (__builtin_popcount((unsigned)b1) & 1) &&
                        (__builtin_popcount((unsigned)b2) & 1);
}

size_t cea608_scan_uyvy(const uint8_t *raster, int first_row, int last_row,
                        cea608_candidate *out, size_t capacity)
{
    size_t found = 0;
    uint8_t luma[CEA608_PIXELS_PER_LINE];
    for (int row = first_row; row <= last_row; ++row) {
        const uint8_t *packed = raster + (size_t)row * CEA608_BYTES_PER_UYVY_LINE;
        for (int x = 0; x < CEA608_PIXELS_PER_LINE; ++x)
            luma[x] = packed[x * 2 + 1];
        cea608_decode_result result;
        cea608_decode_luma(luma, &result);
        if (!result.parity_valid) continue;
        if (found < capacity) {
            out[found].raster_row = (int16_t)row;
            out[found].byte1 = result.byte1;
            out[found].byte2 = result.byte2;
            out[found].amplitude = result.amplitude;
        }
        ++found;
    }
    return found;
}
