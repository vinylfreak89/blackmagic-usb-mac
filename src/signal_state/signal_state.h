#ifndef BLACKMAGIC_USB_MAC_SIGNAL_STATE_H
#define BLACKMAGIC_USB_MAC_SIGNAL_STATE_H

#include "../unit_parser/unit_parser.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct signal_state signal_state;

typedef enum signal_appearance {
    SIGNAL_APPEARANCE_UNKNOWN = 0,
    SIGNAL_APPEARANCE_PROGRAM_LIKE,
    SIGNAL_APPEARANCE_SNOW_LIKE,
    SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE,
    SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE,
    SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800,
    SIGNAL_APPEARANCE_FLAT_AMBIGUOUS,
} signal_appearance;

typedef enum signal_source_state {
    SIGNAL_SOURCE_UNKNOWN = 0,
    SIGNAL_SOURCE_PRESENT,
    SIGNAL_SOURCE_REACQUIRING,
    SIGNAL_SOURCE_MUTED,
    SIGNAL_SOURCE_NO_INPUT,
} signal_source_state;

enum signal_action {
    SIGNAL_ACTION_NONE = 0,
    /* Call fieldreg_discontinuity(): byte placement/temporal evidence broke. */
    SIGNAL_ACTION_REGISTRATION_DISCONTINUITY = 1u << 0,
    /* Call fieldreg_begin_segment(): a new acquisition/relock epoch began. */
    SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT = 1u << 1,
};

typedef struct signal_context {
    bool audio_mute_known;
    bool audio_muted;
    bool osd_activity_known;
    bool osd_active;
} signal_context;

typedef struct signal_measurements {
    double luma_mean;
    double luma_median;
    double luma_sigma;
    double chroma_distance;
    double chroma_distance_median;
    double neutral_chroma_fraction;
    double subblack_pixel_fraction;
    double spatial_gradient_energy;
    /* Fraction of broad active-area tiles with meaningful luma range. */
    double program_extent_fraction;
    /* Static, high-contrast activity localized over an otherwise flat raster. */
    double localized_overlay_score;
    double temporal_mad;
    double hard_padding_fraction;
    double vbi_signature_energy;
    double flat_pixel_fraction;
} signal_measurements;

typedef struct signal_result {
    unit_transport_state transport;
    uint32_t transport_flags;
    signal_appearance appearance;
    signal_source_state source;
    double appearance_confidence;
    double source_confidence;
    signal_measurements measurements;
    uint32_t actions;

    bool unsettled;
    uint64_t unsettled_interval_id;
    bool settled_phase_known;
    int8_t settled_d1;
    int8_t settled_d2;
} signal_result;

typedef struct signal_state_config {
    uint32_t appearance_confirm_units;
    uint32_t acquisition_confirm_units;
    uint32_t mute_confirm_units;
    uint32_t phase_chatter_window_units;
    uint32_t phase_chatter_threshold;
    uint32_t settle_confirm_units;
} signal_state_config;

size_t signal_state_size(void);
size_t signal_state_alignment(void);
signal_state_config signal_state_default_config(void);
void signal_state_init(signal_state *state, const signal_state_config *config);
void signal_state_begin_epoch(signal_state *state, uint64_t epoch);

/* First stage: transport + raster appearance + source-state inference. */
bool signal_state_classify(signal_state *state,
                           const unit_video_observation *unit,
                           const signal_context *context,
                           signal_result *out);

/*
 * Second stage, called after field_registration examines the same unit.
 * A positive per-unit observation can open an interval.  `applied_*` is the
 * phase actually presented by the zero-latency forward engine; a stable
 * applied phase is what can settle that live interval when absolute evidence
 * legitimately abstains. This never changes pixels or calls registration.
 */
void signal_state_note_registration(signal_state *state, signal_result *result,
                                    bool observation_known, int8_t d1, int8_t d2,
                                    double confidence, bool applied_known,
                                    int8_t applied_d1, int8_t applied_d2);

/* Called only when the trajectory layer commits a newly settled endpoint. */
void signal_state_commit_registration(signal_state *state, int8_t d1, int8_t d2);

const char *signal_appearance_name(signal_appearance appearance);
const char *signal_source_state_name(signal_source_state source);

#ifdef __cplusplus
}
#endif

#endif
