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
    /* 720x480 clean-aperture crop: NTSC lines 23 and 286. */
    FIELDREG_FIELD1_START = 19,
    FIELDREG_FIELD2_START = 282,
    FIELDREG_PICTURE_ORIGIN_F1 = 19,
    FIELDREG_PICTURE_ORIGIN_F2 = 282,
    FIELDREG_INSERT_F1 = 17,
    FIELDREG_INSERT_F2 = 280,
    FIELDREG_MIN_OFFSET = -6,
    FIELDREG_FIELD1_MAX_OFFSET = 9,
    FIELDREG_FIELD2_MAX_OFFSET = 3,
    FIELDREG_UNKNOWN = -128,
    FIELDREG_ALGORITHM_VERSION = 9,
};

typedef enum fieldreg_lock_state {
    FIELDREG_LOCK_UNLOCKED = 0,
    FIELDREG_LOCK_ACQUIRE_ONE,
    FIELDREG_LOCK_LOCKED,
} fieldreg_lock_state;

typedef enum fieldreg_clip_state {
    FIELDREG_CLIP_UNKNOWN = 0,
    FIELDREG_CLIP_FITTING,
    FIELDREG_CLIP_FITTED,
} fieldreg_clip_state;

typedef enum fieldreg_mode {
    FIELDREG_MODE_INVALID_UNIT = 0,
    FIELDREG_MODE_ACQUIRING,
    FIELDREG_MODE_LINE21_PLACEMENT,
    FIELDREG_MODE_ALIGNED_CORROBORATED,
    FIELDREG_MODE_GEOMETRY_LOCK_DECIDES,
    FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT,
    FIELDREG_MODE_INSERT_ABSENT,
    FIELDREG_MODE_GEOMETRY_UNMEASURABLE,
    FIELDREG_MODE_LOCK_BROKEN,
    FIELDREG_MODE_LINE21_AMBIGUOUS,
    FIELDREG_MODE_OUT_OF_RANGE_HOLD,
    FIELDREG_MODE_INSERT_GEOMETRY_CONFLICT,
    FIELDREG_MODE_LINE22_DATA_PRESENT,
    FIELDREG_MODE_GAUGE_CONFLICT,
    FIELDREG_MODE_MIXED_FIELD_DECISION,
} fieldreg_mode;

typedef enum fieldreg_gauge_source {
    FIELDREG_GAUGE_NONE = 0,
    FIELDREG_GAUGE_CEA608_PARITY,
    FIELDREG_GAUGE_INSERT_DATA,
    FIELDREG_GAUGE_GEOMETRY,
    FIELDREG_GAUGE_FIELD2_ENVELOPE,
    FIELDREG_GAUGE_LINE22_DATA,
    FIELDREG_GAUGE_HOLD,
} fieldreg_gauge_source;

/* v9 has no thresholds, dwell, FIFO, or tunable evidence model. */
typedef struct fieldreg_config {
    uint32_t reserved;
} fieldreg_config;

typedef struct fieldreg_field_decision {
    int8_t measured_d;
    int8_t applied_d;
    int8_t geometry_d;
    fieldreg_mode reason;
    fieldreg_gauge_source gauge;
    bool insert_present;
    uint8_t insert_byte1;
    uint8_t insert_byte2;
    uint16_t parity_candidate_count;
    uint16_t fallback_candidate_count;
    int16_t gauge_row;
    uint8_t gauge_byte1;
    uint8_t gauge_byte2;
    double gauge_amplitude;
    double blank_mean;
    int16_t raw_top;
    int16_t raw_bottom;
    int16_t raw_height;
    bool geometry_measurable;
    bool bottom_censored;
    fieldreg_lock_state lock_state;
    uint32_t lock_id;
    int16_t lock_top;
    int16_t lock_height;
    bool lock_height_known;
    fieldreg_clip_state clip_state;
    int16_t clip_ceiling;
    int16_t expected_bottom;
    int16_t lines_lost;
    int16_t invariant_residual;
} fieldreg_field_decision;

typedef struct fieldreg_decision {
    int8_t decision_d1;
    int8_t decision_d2;
    int8_t applied_d1;
    int8_t applied_d2;
    int8_t baseline_d1;
    int8_t baseline_d2;
    int8_t frame_observation_d1;
    int8_t frame_observation_d2;
    uint8_t frame_observation_support;
    fieldreg_mode mode;
    /* Binary accepted-evidence flag, not a probability. */
    double confidence;
    bool transport_ok;
    bool comb_safe;
    uint32_t segment_id;
    fieldreg_field_decision field[2];
} fieldreg_decision;

typedef struct fieldreg_field_state {
    int16_t top;
    int16_t height;
    int16_t clip_ceiling;
    int16_t acquire_top;
    int16_t acquire_height;
    int16_t clip_candidate;
    int8_t last_applied;
    int8_t clip_candidate_d;
    fieldreg_lock_state lock_state;
    bool height_known;
    bool acquire_height_known;
    uint8_t clip_candidate_count;
    uint32_t lock_id;
} fieldreg_field_state;

/* Caller-owned, allocation-free hot-path state. The clip fit is deliberately
 * pending data, not a lock state: a lock remains LOCKED while C settles. */
typedef struct field_registration {
    fieldreg_config config;
    fieldreg_field_state field[2];
    uint32_t segment_id;
} field_registration;

fieldreg_config fieldreg_default_config(void);
size_t fieldreg_state_size(void);
size_t fieldreg_config_size(void);
size_t fieldreg_decision_size(void);
uint32_t fieldreg_algorithm_version(void);
/* Two observations acquire a geometry-only lock; gauged placement is still
 * immediate and the engine has no dwell window or buffered confirmation. */
uint32_t fieldreg_confirmation_units(const field_registration *engine);
uint32_t fieldreg_buffer_units(const field_registration *engine);
void fieldreg_init(field_registration *engine, const fieldreg_config *config);
void fieldreg_begin_segment(field_registration *engine);
void fieldreg_discontinuity(field_registration *engine);
bool fieldreg_process(field_registration *engine,
                      const uint8_t unit[FIELDREG_UNIT_BYTES],
                      fieldreg_decision *out);

const char *fieldreg_mode_name(fieldreg_mode mode);
const char *fieldreg_gauge_name(fieldreg_gauge_source source);
const char *fieldreg_lock_state_name(fieldreg_lock_state state);
const char *fieldreg_clip_state_name(fieldreg_clip_state state);

#ifdef __cplusplus
}
#endif

#endif
