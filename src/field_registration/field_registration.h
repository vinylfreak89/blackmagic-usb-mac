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
    FIELDREG_ACTIVE_LUMA_SAMPLES = 320,
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
    FIELDREG_LOCK_LOCKED,
} fieldreg_lock_state;

typedef enum fieldreg_clip_state {
    FIELDREG_CLIP_UNKNOWN = 0,
    FIELDREG_CLIP_FITTING,
    FIELDREG_CLIP_FITTED,
} fieldreg_clip_state;

typedef enum fieldreg_zero_source {
    FIELDREG_ZERO_NONE = 0,
    FIELDREG_ZERO_STANDARD,
    FIELDREG_ZERO_PARITY,
    FIELDREG_ZERO_ENVELOPE,
    FIELDREG_ZERO_COMB,
} fieldreg_zero_source;

typedef enum fieldreg_parity_state {
    FIELDREG_PARITY_UNCALIBRATED = 0,
    FIELDREG_PARITY_CALIBRATED,
    FIELDREG_PARITY_DRIFT,
} fieldreg_parity_state;

typedef enum fieldreg_comb_check {
    FIELDREG_COMB_NOT_APPLICABLE = 0,
    FIELDREG_COMB_AGREE,
    FIELDREG_COMB_DISAGREE,
    FIELDREG_COMB_FLAT,
} fieldreg_comb_check;

typedef enum fieldreg_insert_relation {
    FIELDREG_INSERT_RELATION_NONE = 0,
    FIELDREG_INSERT_CORROBORATES,
    FIELDREG_INSERT_CONTRADICTED,
} fieldreg_insert_relation;

typedef enum fieldreg_mode {
    FIELDREG_MODE_INVALID_UNIT = 0,
    FIELDREG_MODE_ACQUIRING,
    FIELDREG_MODE_LINE21_PLACEMENT,
    FIELDREG_MODE_GEOMETRY_LOCK_DECIDES,
    FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT,
    FIELDREG_MODE_INSERT_ABSENT,
    FIELDREG_MODE_GEOMETRY_UNMEASURABLE,
    FIELDREG_MODE_LOCK_BROKEN,
    FIELDREG_MODE_LINE21_AMBIGUOUS,
    FIELDREG_MODE_OUT_OF_RANGE_HOLD,
    FIELDREG_MODE_LINE22_DATA_PRESENT,
    FIELDREG_MODE_GAUGE_CONFLICT,
    FIELDREG_MODE_CAPTION_ONLY_MOTION,
    FIELDREG_MODE_CAPTION_BODY_DISAGREE,
    FIELDREG_MODE_ANCHOR_UNCORROBORATED,
    FIELDREG_MODE_TOP_BODY_DISAGREE,
    FIELDREG_MODE_BODY_ONLY_PLACEMENT,
    FIELDREG_MODE_COMMON_MODE_BODY_HOLD,
    FIELDREG_MODE_FIELD2_COMB_CALIBRATION,
    FIELDREG_MODE_ZERO_CONFLICT,
    FIELDREG_MODE_ZERO_CANDIDATE,
    FIELDREG_MODE_ZERO_OUT_OF_BOUNDS,
    FIELDREG_MODE_TOP_UNCORROBORATED,
    FIELDREG_MODE_TOP_COMB_CORROBORATED,
    FIELDREG_MODE_TOP_COMB_VETOED,
    FIELDREG_MODE_TOP_ONLY,
    FIELDREG_MODE_COMB_RELATIVE_CORRECTION,
    FIELDREG_MODE_DAMAGE_HOLD,
    FIELDREG_MODE_DAMAGE_CLEARED,
    FIELDREG_MODE_MIXED_FIELD_DECISION,
} fieldreg_mode;

typedef enum fieldreg_gauge_source {
    FIELDREG_GAUGE_NONE = 0,
    FIELDREG_GAUGE_CEA608_PARITY,
    FIELDREG_GAUGE_GEOMETRY,
    FIELDREG_GAUGE_FIELD2_ENVELOPE,
    FIELDREG_GAUGE_LINE22_DATA,
    FIELDREG_GAUGE_HOLD,
    FIELDREG_GAUGE_STATIC_COMB,
} fieldreg_gauge_source;

/* v9 has no thresholds, dwell, FIFO, or tunable evidence model. */
typedef struct fieldreg_config {
    uint32_t reserved;
} fieldreg_config;

typedef struct fieldreg_process_context {
    /* The live caller supplies its transport ordinal and classifier result.
     * The legacy fieldreg_process wrapper uses an engine-local exact-unit
     * ordinal and leaves program_like false. */
    uint64_t ordinal;
    bool program_like;
} fieldreg_process_context;

typedef struct fieldreg_field_decision {
    int8_t measured_d;
    int8_t applied_d;
    int8_t geometry_d;
    fieldreg_mode reason;
    fieldreg_gauge_source gauge;
    bool insert_present;
    uint8_t insert_byte1;
    uint8_t insert_byte2;
    fieldreg_insert_relation insert_relation;
    uint16_t parity_candidate_count;
    uint16_t fallback_candidate_count;
    int16_t gauge_row;
    uint8_t gauge_byte1;
    uint8_t gauge_byte2;
    double gauge_amplitude;
    double blank_mean;
    double body_mad;
    int16_t raw_top;
    int16_t raw_bottom;
    int16_t raw_height;
    bool geometry_measurable;
    bool bottom_censored;
    bool body_witness_valid;
    int8_t body_shift;
    bool body_geometry_agrees;
    /* All nonnegative *_top values are source-raster rows here. Sidecar
     * writers publish them as NTSC line numbers (row + 4). */
    int16_t body_reference_top;
    int16_t body_implied_top;
    bool body_differential;
    bool body_common_mode;
    bool picture_position_valid;
    int16_t measured_picture_top;
    bool picture_from_body;
    fieldreg_lock_state lock_state;
    fieldreg_zero_source zero_source;
    uint32_t lock_id;
    int16_t lock_top;
    int16_t lock_height;
    bool lock_height_known;
    fieldreg_clip_state clip_state;
    int16_t clip_ceiling;
    int16_t expected_bottom;
    int16_t lines_lost;
    int16_t invariant_residual;
    bool saved_good_valid;
    int16_t saved_good_top;
    int16_t saved_good_bottom;
    int16_t saved_good_height;
    bool saved_good_bottom_censored;
    int8_t saved_good_applied_d;
    fieldreg_gauge_source saved_good_gauge;
    uint64_t saved_good_ordinal;
    uint32_t damage_hold_length;
    int8_t damage_jump;
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
    fieldreg_parity_state parity_state;
    fieldreg_comb_check comb_check;
    int8_t comb_best_shift;
    int8_t parity_bias;
    /* Absolute, bounded correction relative to the ordinary per-unit crops.
     * A positive value moves field 2 down (or field 1 up) by this many lines. */
    int8_t comb_correction;
    /* 0 when inactive/not applicable; otherwise the one-based moved field. */
    int8_t comb_correction_field;
    double comb_best_energy;
    double comb_second_energy;
    double comb_static_fraction;
    uint32_t segment_id;
    fieldreg_field_decision field[2];
} fieldreg_decision;

typedef struct fieldreg_field_state {
    int16_t top;
    int16_t height;
    int16_t clip_ceiling;
    int16_t clip_candidate;
    int16_t zero_candidate;
    int8_t last_applied;
    int8_t clip_candidate_d;
    fieldreg_lock_state lock_state;
    bool height_known;
    bool placement_initialized;
    uint8_t clip_candidate_count;
    uint8_t zero_candidate_count;
    fieldreg_zero_source zero_source;
    fieldreg_zero_source zero_candidate_source;
    uint32_t lock_id;
    int16_t previous_measured_top;
    struct {
        bool valid;
        int16_t top;
        int16_t bottom;
        int16_t height;
        bool bottom_censored;
        int8_t applied_d;
        fieldreg_gauge_source gauge;
        uint64_t ordinal;
    } saved_good;
    bool damage_active;
    int8_t damage_clear_candidate_d;
    uint8_t damage_clear_candidate_count;
    int16_t damage_clear_candidate_top;
    int16_t damage_clear_candidate_bottom;
    int16_t damage_clear_candidate_height;
    uint32_t damage_hold_length;
} fieldreg_field_state;

/* Caller-owned, allocation-free hot-path state. The clip fit is deliberately
 * pending data, not a lock state: a lock remains LOCKED while C settles. */
typedef struct field_registration {
    fieldreg_config config;
    fieldreg_field_state field[2];
    /* Previous full-raster active-width luma supplies both the bounded body
     * witness and the static-comb calibration without retaining input. */
    uint8_t previous_luma[FIELDREG_RASTER_LINES *
                          FIELDREG_ACTIVE_LUMA_SAMPLES];
    bool previous_luma_valid;
    fieldreg_parity_state parity_state;
    int16_t comb_zero_candidate;
    int8_t comb_candidate_count;
    int8_t comb_correction;
    int8_t comb_correction_candidate;
    int8_t comb_correction_candidate_count;
    uint32_t segment_id;
    uint64_t process_ordinal;
} field_registration;

fieldreg_config fieldreg_default_config(void);
size_t fieldreg_state_size(void);
size_t fieldreg_config_size(void);
size_t fieldreg_decision_size(void);
uint32_t fieldreg_algorithm_version(void);
/* Geometry is compared with the standard zero immediately; no observation
 * dwell or buffered confirmation exists. */
uint32_t fieldreg_confirmation_units(const field_registration *engine);
uint32_t fieldreg_buffer_units(const field_registration *engine);
void fieldreg_init(field_registration *engine, const fieldreg_config *config);
void fieldreg_begin_segment(field_registration *engine);
void fieldreg_discontinuity(field_registration *engine);
bool fieldreg_process(field_registration *engine,
                      const uint8_t unit[FIELDREG_UNIT_BYTES],
                      fieldreg_decision *out);
bool fieldreg_process_ex(field_registration *engine,
                         const uint8_t unit[FIELDREG_UNIT_BYTES],
                         const fieldreg_process_context *context,
                         fieldreg_decision *out);

const char *fieldreg_mode_name(fieldreg_mode mode);
const char *fieldreg_gauge_name(fieldreg_gauge_source source);
const char *fieldreg_lock_state_name(fieldreg_lock_state state);
const char *fieldreg_clip_state_name(fieldreg_clip_state state);
const char *fieldreg_zero_source_name(fieldreg_zero_source source);
const char *fieldreg_insert_relation_name(fieldreg_insert_relation relation);
const char *fieldreg_parity_state_name(fieldreg_parity_state state);
const char *fieldreg_comb_check_name(fieldreg_comb_check check);

#ifdef __cplusplus
}
#endif

#endif
