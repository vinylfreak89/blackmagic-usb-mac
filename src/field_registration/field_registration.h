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
    /* Nominal decoded picture envelope inside the two fixed transport slots. */
    FIELDREG_ACTIVE_TOP_F1 = 19,
    FIELDREG_ACTIVE_BOTTOM_F1 = 256,
    FIELDREG_ACTIVE_TOP_F2 = 282,
    FIELDREG_ACTIVE_BOTTOM_F2 = 518,
    FIELDREG_MIN_OFFSET = -6,
    FIELDREG_MAX_OFFSET = 6,
    /* Larger positive shifts cross device hard padding and are unrecoverable. */
    FIELDREG_FIELD1_MAX_OFFSET = 4,
    FIELDREG_FIELD2_MAX_OFFSET = 4,
    FIELDREG_X_SAMPLES = 180,
    FIELDREG_PHASE_HISTORY = 120,
    FIELDREG_ALGORITHM_VERSION = 2,
    FIELDREG_UNKNOWN = -128,
};

typedef enum fieldreg_mode {
    FIELDREG_MODE_INVALID_UNIT = 0,
    FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI,
    FIELDREG_MODE_UNKNOWN_WARMUP_HOLD,
    FIELDREG_MODE_UNKNOWN_BAND_LANDMARK,
    FIELDREG_MODE_UNKNOWN_BAND_DISAGREEMENT,
    FIELDREG_MODE_UNKNOWN_EVIDENCE_DISAGREEMENT,
    FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE,
    FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD,
    FIELDREG_MODE_UNKNOWN_TEMPORAL_RELEASE_DWELL,
    FIELDREG_MODE_UNKNOWN_CANDIDATE_DWELL,
    FIELDREG_MODE_STABLE,
    FIELDREG_MODE_CONVERGED_RELATIVE_BAND,
    FIELDREG_MODE_CONVERGED_TEMPORAL_RELEASE,
    FIELDREG_MODE_UNKNOWN_SPATIAL_PHASE,
    FIELDREG_MODE_UNKNOWN_PHASE_DWELL,
    FIELDREG_MODE_UNKNOWN_EDGE_TRANSIENT,
    FIELDREG_MODE_STABLE_MOTION_PHASE,
    FIELDREG_MODE_CONVERGED_MOTION_PHASE,
} fieldreg_mode;

typedef enum fieldreg_evidence_model {
    FIELDREG_EVIDENCE_TOP_ONLY = 0,
    FIELDREG_EVIDENCE_DUAL_EDGE = 1,
    FIELDREG_EVIDENCE_MOTION_PHASE = 2,
} fieldreg_evidence_model;

typedef struct fieldreg_config {
    /* Minimum weave runner-up margin before changing relative registration. */
    double switch_margin;
    fieldreg_evidence_model evidence_model;
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
    int8_t temporal_best_f1;
    int8_t temporal_best_f2;
    double temporal_best_cost_f1;
    double temporal_best_cost_f2;
    bool temporal_scene_cut;

    bool transport_ok;
    int16_t observed_transport_f1;
    int16_t observed_transport_f2;
    int16_t picture_top_f1;
    int16_t picture_top_f2;
    int16_t picture_bottom_f1;
    int16_t picture_bottom_f2;
    int16_t learned_band_mode_f1;
    int16_t learned_band_mode_f2;
    int16_t learned_bottom_mode_f1;
    int16_t learned_bottom_mode_f2;
    double learned_band_stability_f1;
    double learned_band_stability_f2;
    double learned_bottom_stability_f1;
    double learned_bottom_stability_f2;
    bool dual_edge_agreement;

    /* Motion-compensated inter-field phase, independently by image band. */
    int8_t phase_vote_left;
    int8_t phase_vote_center;
    int8_t phase_vote_right;
    int8_t phase_motion_left;
    int8_t phase_motion_center;
    int8_t phase_motion_right;
    int8_t phase_priority_band;
    int8_t phase_consensus;
    uint8_t phase_support;
    bool spatial_phase_conflict;
    int8_t phase_window;
    uint8_t phase_window_count;
    uint8_t phase_window_margin;
    int8_t fast_edge_d1;
    int8_t fast_edge_d2;
    uint8_t fast_edge_support_f1;
    uint8_t fast_edge_support_f2;
    bool fast_edge_spatial_conflict;
} fieldreg_decision;

/*
 * State is caller-owned and intentionally contains all working storage.
 * fieldreg_process() performs no allocation and retains no input pointer.
 * Keep one instance per stream/processing thread.
 */
typedef struct field_registration {
    fieldreg_config config;
    int8_t selected[2];
    int8_t baseline[2];
    bool phase_baseline_valid;
    uint16_t phase_baseline_age;
    int8_t selected_relative;
    int8_t pending[2];
    bool pending_valid;
    uint32_t pending_count;
    uint32_t pending_age;
    uint32_t frames_seen;
    int8_t phase_history[FIELDREG_PHASE_HISTORY];
    uint16_t phase_history_index;
    uint16_t phase_history_filled;
    uint8_t phase_counts[13];

    /* [field][top/bottom][left/center/right][signed line + 64]. */
    uint16_t spatial_edge_counts[2][2][3][129];
    uint16_t spatial_edge_total[2][2][3];

    /* [field][0 top / 1 bottom][signed landmark offset + 64]. */
    uint32_t band_counts[2][2][129];
    uint32_t band_first_seen[2][2][129];
    uint32_t band_total[2][2];
    uint32_t band_serial;

    bool previous_valid[2];
    bool temporal_cost_ema_valid;
    double temporal_cost_ema[2];
    uint8_t previous[2][FIELDREG_FIELD_LINES][FIELDREG_X_SAMPLES];
    uint8_t luma[FIELDREG_RASTER_LINES][FIELDREG_X_SAMPLES];
} field_registration;

fieldreg_config fieldreg_default_config(void);
size_t fieldreg_state_size(void);
size_t fieldreg_config_size(void);
size_t fieldreg_decision_size(void);
uint32_t fieldreg_algorithm_version(void);
void fieldreg_init(field_registration *engine, const fieldreg_config *config);

/* Start a newly acquired source segment and clear temporal decision state. */
void fieldreg_begin_segment(field_registration *engine);

/* Break temporal/dwell evidence after unknown byte placement. */
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
