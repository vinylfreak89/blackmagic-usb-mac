#ifndef BLACKMAGIC_USB_MAC_FIELD_REGISTRATION_H
#define BLACKMAGIC_USB_MAC_FIELD_REGISTRATION_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    FIELDREG_UNIT_BYTES = 756048,
    FIELDREG_HEADER_BYTES = 48,
    FIELDREG_RASTER_LINES = 525,
    FIELDREG_BYTES_PER_LINE = 1440,
    FIELDREG_FIELD_LINES = 240,
    FIELDREG_FIELD1_START = 17,
    FIELDREG_FIELD2_START = 280,
    FIELDREG_MIN_OFFSET = -6,
    FIELDREG_MAX_OFFSET = 6,
    FIELDREG_X_SAMPLES = 180,
    FIELDREG_UNKNOWN = -128,
};

typedef enum fieldreg_mode {
    FIELDREG_MODE_INVALID_UNIT = 0,
    FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI,
    FIELDREG_MODE_UNKNOWN_WARMUP_HOLD,
    FIELDREG_MODE_UNKNOWN_BAND_LANDMARK,
    FIELDREG_MODE_UNKNOWN_EVIDENCE_DISAGREEMENT,
    FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE,
    FIELDREG_MODE_UNKNOWN_CANDIDATE_DWELL,
    FIELDREG_MODE_STABLE,
    FIELDREG_MODE_CONVERGED_RELATIVE_BAND,
} fieldreg_mode;

typedef struct fieldreg_config {
    /* Minimum weave runner-up margin before changing relative registration. */
    double switch_margin;
} fieldreg_config;

typedef struct fieldreg_decision {
    int8_t decision_d1;
    int8_t decision_d2;
    int8_t applied_d1;
    int8_t applied_d2;
    fieldreg_mode mode;
    double confidence;

    int8_t best_d1;
    int8_t best_d2;
    int8_t pending_d1;
    int8_t pending_d2;
    uint32_t pending_count;
    int8_t best_relative;
    int8_t selected_relative;
    double independent_evidence_margin;
    double weave_margin;
    double temporal_margin_f1;
    double temporal_margin_f2;

    bool transport_ok;
    int16_t observed_transport_f1;
    int16_t observed_transport_f2;
    int16_t picture_top_f1;
    int16_t picture_top_f2;
    int16_t learned_band_mode_f1;
    int16_t learned_band_mode_f2;
    double learned_band_stability_f1;
    double learned_band_stability_f2;
} fieldreg_decision;

/*
 * State is caller-owned and intentionally contains all working storage.
 * fieldreg_process() performs no allocation and retains no input pointer.
 * Keep one instance per stream/processing thread.
 */
typedef struct field_registration {
    fieldreg_config config;
    int8_t selected[2];
    int8_t selected_relative;
    int8_t pending[2];
    bool pending_valid;
    uint32_t pending_count;
    uint32_t pending_age;
    uint32_t frames_seen;

    /* Band offsets are bounded by the estimator's landmark windows. */
    uint32_t band_counts[2][129];
    uint32_t band_first_seen[2][129];
    uint32_t band_total[2];
    uint32_t band_serial;

    bool previous_valid[2];
    uint8_t previous[2][FIELDREG_FIELD_LINES][FIELDREG_X_SAMPLES];
    uint8_t luma[FIELDREG_RASTER_LINES][FIELDREG_X_SAMPLES];
} field_registration;

fieldreg_config fieldreg_default_config(void);
void fieldreg_init(field_registration *engine, const fieldreg_config *config);

/* Break temporal/dwell evidence after unknown byte placement or a stream cut. */
void fieldreg_discontinuity(field_registration *engine);

/* Process one exact e801 unit. Returns false only for an invalid unit/header. */
bool fieldreg_process(field_registration *engine,
                       const uint8_t unit[FIELDREG_UNIT_BYTES],
                       fieldreg_decision *out);

const char *fieldreg_mode_name(fieldreg_mode mode);

#ifdef __cplusplus
}
#endif

#endif
