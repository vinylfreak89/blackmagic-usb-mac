// Tracking meter: per-field noise in flat areas of the published picture, so the deck's tracking
// can be set by watching field 2's noise against field 1's (a head reading off the centre of its
// track is noisier, most of all in chroma). Plain C, no OBS: the plugin, its window and the
// offline validation tool all call these same functions.
//
// Measurement, per field and per channel (Y, Cb, Cr): the frame is cut into blocks of 8 field
// lines by 16 luma samples (8 samples of each chroma channel). Each block's plane (mean and both
// slopes) is removed and the rest is its noise. Blocks whose luma sits near black or white are
// skipped, because clipping hides noise there. The field's figure is a low percentile of its block
// figures (the flattest blocks are the ones whose residual is noise rather than picture),
// corrected for the bias a low percentile has on pure noise. Both fields show nearly the same
// picture, so whatever picture survives cancels in the ratio field 2 / field 1.
#ifndef TRACKING_METER_H
#define TRACKING_METER_H
#include <stddef.h>
#include <stdint.h>

enum { TM_Y = 0, TM_CB = 1, TM_CR = 2, TM_CHANNELS = 3 };

// Why a frame gave no reading. A frame must be real interlaced picture: two different fields with detail.
enum { TM_OK = 0, TM_TOO_FEW_BLOCKS = 1, TM_FIELDS_IDENTICAL = 2, TM_NO_DETAIL = 3, TM_SNOW = 4 };

typedef struct {
    int    valid;                       // 0: no reading; `why` says which test failed
    int    why;                         // TM_* above
    double noise[2][TM_CHANNELS];       // [field 0 = field 1 (top), 1 = field 2][channel], 8-bit codes
    unsigned blocks[2];                 // usable blocks per field
} tm_frame;

// Measure one 720x480 TFF UYVY frame ('2vuy', row 0 = field 1). bytes_per_row >= 1440.
void tm_measure_uyvy(const uint8_t *frame, size_t bytes_per_row, tm_frame *out);

// A running figure over the last TM_WINDOW measured frames: the median of each per-frame value.
#define TM_WINDOW 15
typedef struct {
    tm_frame recent[TM_WINDOW];
    unsigned n, next;
} tm_window;

typedef struct {
    int    valid;
    unsigned frames;                    // valid frames in the window
    double noise[2][TM_CHANNELS];       // medians, codes
    double ratio[TM_CHANNELS];          // field 2 / field 1
    double snr_db[2][TM_CHANNELS];      // 20 log10(219 / noise) for Y, (224 / noise) for chroma
} tm_reading;

void tm_window_reset(tm_window *w);
void tm_window_add(tm_window *w, const tm_frame *f);
void tm_window_read(const tm_window *w, tm_reading *out);

#endif
