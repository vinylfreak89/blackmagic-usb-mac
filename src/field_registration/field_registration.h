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
    /* Field 1 may read captured hard padding after source content clips at
     * line 260. The pixels remain honest device output; the sidecar marks the
     * censored source extent. Field 2 cannot address beyond unit line 524. */
    FIELDREG_FIELD1_MAX_OFFSET = 9,
    FIELDREG_FIELD2_MAX_OFFSET = 4,
    FIELDREG_X_SAMPLES = 180,
    /* One second at 30000/1001. This governs fallback-candidate settlement;
     * the default live path presents authoritative observations immediately
     * and adds no FIFO latency. */
    FIELDREG_PHASE_CONFIRM_UNITS = 30,
    FIELDREG_MAX_CONFIRM_UNITS = 120,
    /* Physical reacquisition horizon, independent of caller ring depth. */
    FIELDREG_TRAJECTORY_STALENESS_UNITS = 75,
    FIELDREG_RELATIVE_SEARCH_MIN = -3,
    FIELDREG_RELATIVE_SEARCH_MAX = 3,
    FIELDREG_RELATIVE_STATIC_RUN = 16,
    FIELDREG_ALGORITHM_VERSION = 8,
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
    FIELDREG_MODE_RELATIVE_ONLY,
    FIELDREG_MODE_BOTTOM_EDGE_PLACEMENT,
    FIELDREG_MODE_BOTTOM_EDGE_RELATIVE_PLACEMENT,
    FIELDREG_MODE_UNKNOWN_BOTTOM_EDGE_HOLD,
} fieldreg_mode;

typedef enum fieldreg_bottom_hold_reason {
    FIELDREG_BOTTOM_HOLD_NONE = 0,
    FIELDREG_BOTTOM_HOLD_TARGET_LEARNING,
    FIELDREG_BOTTOM_HOLD_TRANSPORT,
    FIELDREG_BOTTOM_HOLD_FLAT_OR_DARK,
    FIELDREG_BOTTOM_HOLD_NOISY,
    FIELDREG_BOTTOM_HOLD_SCENE_CUT,
    FIELDREG_BOTTOM_HOLD_TEMPORAL_CONTRADICTION,
    FIELDREG_BOTTOM_HOLD_EDGE_JUMP,
    FIELDREG_BOTTOM_HOLD_OUT_OF_RANGE,
} fieldreg_bottom_hold_reason;

typedef enum fieldreg_evidence_model {
    FIELDREG_EVIDENCE_TOP_ONLY = 0,
    FIELDREG_EVIDENCE_DUAL_EDGE = 1,
    FIELDREG_EVIDENCE_MOTION_PHASE = 2,
} fieldreg_evidence_model;

typedef enum fieldreg_relative_gauge_source {
    FIELDREG_RELATIVE_GAUGE_NONE = 0,
    FIELDREG_RELATIVE_GAUGE_PRIOR,
    FIELDREG_RELATIVE_GAUGE_TEMPORAL_F1,
    FIELDREG_RELATIVE_GAUGE_TEMPORAL_F2,
    FIELDREG_RELATIVE_GAUGE_TEMPORAL_BOTH,
    FIELDREG_RELATIVE_GAUGE_MIN_CROP,
} fieldreg_relative_gauge_source;

typedef struct fieldreg_config {
    /* Minimum weave runner-up margin before changing relative registration. */
    double switch_margin;
    fieldreg_evidence_model evidence_model;
    /* Fallback-candidate support span; not live presentation latency. */
    uint32_t confirmation_units;
    /* Required agreeing observations inside confirmation_units. */
    uint32_t minimum_support_units;
    /* Optional archival caller's retained depth; live callers use zero. */
    uint32_t maximum_buffered_units;
} fieldreg_config;

typedef struct fieldreg_decision {
    int8_t decision_d1;
    int8_t decision_d2;
    int8_t applied_d1;
    int8_t applied_d2;
    /* Stable fallback state for units whose own geometry abstains. */
    int8_t baseline_d1;
    int8_t baseline_d2;
    /* Strong absolute observation for this unit, independent of hysteresis. */
    int8_t frame_observation_d1;
    int8_t frame_observation_d2;
    uint8_t frame_observation_support;
    bool frame_observation_motion_priority;
    bool frame_observation_conflict;
    fieldreg_mode mode;
    double confidence;

    int8_t best_d1;
    int8_t best_d2;
    int8_t pending_d1;
    int8_t pending_d2;
    uint32_t pending_count;
    uint32_t pending_span;
    uint32_t decision_backdate;
    bool trajectory_reset;
    bool trajectory_locked;
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
    bool content_evidence_available;
    bool top_f1_censored;
    bool top_f2_censored;
    bool global_envelope_authority;
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

    /* Static-region relative-only authority. Energies are 8-pixel
     * horizontally low-passed inter-field curvature costs. This path reports
     * an honest unknown absolute gauge when temporal evidence cannot identify
     * which field moved. */
    bool relative_only;
    bool relative_only_gauge_unknown;
    fieldreg_relative_gauge_source relative_only_gauge_source;
    int8_t relative_only_phase;
    double relative_only_best_energy;
    double relative_only_runner_energy;
    double relative_only_prior_energy;
    double relative_only_margin;
    double relative_only_ratio;
    uint16_t relative_only_static_columns;
    uint16_t relative_only_persistent_columns;
    bool relative_only_transport_gate;
    bool relative_only_cut_gate;
    bool bottom_f1_censored;
    bool bottom_f2_censored;

    /* v8 direct-placement provenance. raw_edge is the final captured line
     * which is not majority-black; target is frozen per acquisition segment.
     * direct placement = raw_edge - target on measurable units. The final
     * applied pair may additionally carry a labelled body-relative refinement.
     * An unmeasurable field holds its own last presentation and names why. */
    int16_t bottom_raw_edge_f1;
    int16_t bottom_raw_edge_f2;
    int16_t bottom_target_f1;
    int16_t bottom_target_f2;
    uint8_t bottom_blanking_level_f1;
    uint8_t bottom_blanking_level_f2;
    uint8_t bottom_black_threshold_f1;
    uint8_t bottom_black_threshold_f2;
    bool bottom_measurable_f1;
    bool bottom_measurable_f2;
    bool bottom_placement_f1;
    bool bottom_placement_f2;
    fieldreg_bottom_hold_reason bottom_hold_reason_f1;
    fieldreg_bottom_hold_reason bottom_hold_reason_f2;
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
    /* Physical candidate age. This is not caller ring occupancy. */
    uint32_t trajectory_age;
    /* Best phase assigned to the immediately preceding raw unit. An
     * abstention holds this phase; only new corroborated evidence, convergence,
     * or an explicit reset may create a presentation transition. */
    int8_t previous_phase[2];
    bool previous_phase_valid;

    /* Raw source-carried envelope landmarks from the immediately preceding
     * unit.  Absolute landmark offsets can be ambiguous in a multi-layer
     * raster; coherent top+bottom motion across broad bands remains a usable
     * per-unit displacement observation. */
    int16_t previous_picture_top[2];
    int16_t previous_picture_bottom[2];
    int16_t previous_spatial_top[2][3];
    int16_t previous_spatial_bottom[2][3];
    bool previous_edge_valid;
    int16_t motion_anchor_picture_top[2];
    int16_t motion_anchor_picture_bottom[2];
    int16_t motion_anchor_spatial_top[2][3];
    int16_t motion_anchor_spatial_bottom[2][3];
    int8_t motion_anchor_phase[2];
    bool motion_anchor_valid;

    int8_t relative_gauge_phase[2];
    bool relative_gauge_unknown_active;
    bool relative_only_active;

    /* Direct bottom-edge placement is deliberately independent per field.
     * Four program-qualified observations establish the segment target;
     * mute/flat content cannot move it. */
    int16_t bottom_target[2];
    int16_t bottom_target_samples[2][4];
    uint8_t bottom_target_sample_count[2];
    bool bottom_target_valid[2];
    int16_t bottom_last_raw[2];
    bool bottom_last_raw_valid[2];
    int8_t bottom_applied[2];

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
uint32_t fieldreg_confirmation_units(const field_registration *engine);
uint32_t fieldreg_buffer_units(const field_registration *engine);
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
const char *fieldreg_relative_gauge_name(fieldreg_relative_gauge_source source);
const char *fieldreg_bottom_hold_reason_name(fieldreg_bottom_hold_reason reason);

#ifdef __cplusplus
}
#endif

#endif
