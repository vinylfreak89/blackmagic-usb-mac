#include "signal_state.h"

#include <math.h>
#include <stdalign.h>
#include <stdlib.h>
#include <string.h>

enum {
    RASTER_LINES = 525,
    BYTES_PER_LINE = 1440,
    HEADER_BYTES = 48,
    X_SAMPLES = 180,
    SAMPLE_STEP_PIXELS = 4,
    MAX_PHASE_WINDOW = 64,
};

struct signal_state {
    signal_state_config config;
    uint64_t epoch;
    signal_appearance appearance_candidate;
    uint32_t appearance_candidate_count;
    signal_source_state stable_source;
    signal_source_state source_candidate;
    uint32_t source_candidate_count;
    bool acquisition_open;

    bool unsettled;
    uint64_t interval_serial;
    uint64_t active_interval;
    uint32_t stable_phase_count;
    bool phase_valid;
    int8_t phase_d1;
    int8_t phase_d2;
    uint64_t phase_change_bits;
    uint32_t phase_window_count;

    bool previous_valid;
    uint8_t previous[RASTER_LINES][X_SAMPLES];
};

size_t signal_state_size(void)
{
    return sizeof(signal_state);
}

size_t signal_state_alignment(void)
{
    return alignof(signal_state);
}

signal_state_config signal_state_default_config(void)
{
    signal_state_config config = {
        .appearance_confirm_units = 2,
        .acquisition_confirm_units = 3,
        .mute_confirm_units = 3,
        .phase_chatter_window_units = 30,
        .phase_chatter_threshold = 4,
        .settle_confirm_units = 30,
    };
    return config;
}

static uint32_t clamp_nonzero(uint32_t value, uint32_t fallback)
{
    return value ? value : fallback;
}

void signal_state_init(signal_state *state, const signal_state_config *config)
{
    signal_state_config chosen = config ? *config : signal_state_default_config();
    chosen.appearance_confirm_units = clamp_nonzero(
        chosen.appearance_confirm_units, 2);
    chosen.acquisition_confirm_units = clamp_nonzero(
        chosen.acquisition_confirm_units, 3);
    chosen.mute_confirm_units = clamp_nonzero(chosen.mute_confirm_units, 3);
    chosen.phase_chatter_window_units = clamp_nonzero(
        chosen.phase_chatter_window_units, 30);
    if (chosen.phase_chatter_window_units > MAX_PHASE_WINDOW)
        chosen.phase_chatter_window_units = MAX_PHASE_WINDOW;
    chosen.phase_chatter_threshold = clamp_nonzero(
        chosen.phase_chatter_threshold, 4);
    if (chosen.phase_chatter_threshold > chosen.phase_chatter_window_units)
        chosen.phase_chatter_threshold = chosen.phase_chatter_window_units;
    chosen.settle_confirm_units = clamp_nonzero(chosen.settle_confirm_units, 30);
    memset(state, 0, sizeof(*state));
    state->config = chosen;
}

void signal_state_begin_epoch(signal_state *state, uint64_t epoch)
{
    signal_state_config config = state->config;
    signal_state_init(state, &config);
    state->epoch = epoch;
}

static bool hard_line_expected(int line)
{
    return line <= 6 || (line >= 261 && line <= 269) || line >= 523;
}

static bool sampled_picture_line(int line)
{
    return (line >= 20 && line <= 256) || (line >= 282 && line <= 518);
}

static double clamp01(double value)
{
    if (value < 0.0)
        return 0.0;
    if (value > 1.0)
        return 1.0;
    return value;
}

static void measure_raster(signal_state *state, const uint8_t *unit,
                           signal_measurements *out)
{
    const uint8_t *raster = unit + HEADER_BYTES;
    double sum_y = 0.0, sum_y2 = 0.0, chroma = 0.0;
    double gradient = 0.0, temporal = 0.0;
    uint64_t samples = 0, gradients = 0, temporal_samples = 0;
    uint64_t flat = 0, hard = 0, hard_total = 0;
    double vbi_sum = 0.0, vbi_sum2 = 0.0;
    uint64_t vbi_samples = 0;

    for (int line = 0; line < RASTER_LINES; ++line) {
        const uint8_t *row = raster + (size_t)line * BYTES_PER_LINE;
        if (hard_line_expected(line)) {
            for (int x = 0; x < 720; ++x) {
                ++hard_total;
                hard += row[x * 2] == 128 && row[x * 2 + 1] == 16;
            }
        }
        bool vbi = line == 16 || line == 17 || line == 279 || line == 280;
        uint8_t prior = 0;
        for (int sx = 0; sx < X_SAMPLES; ++sx) {
            int x = sx * SAMPLE_STEP_PIXELS;
            uint8_t c = row[x * 2];
            uint8_t y = row[x * 2 + 1];
            if (vbi) {
                vbi_sum += y;
                vbi_sum2 += (double)y * y;
                ++vbi_samples;
            }
            if (!sampled_picture_line(line))
                continue;
            sum_y += y;
            sum_y2 += (double)y * y;
            chroma += fabs((double)c - 128.0);
            if (sx) {
                gradient += abs((int)y - (int)prior);
                ++gradients;
            }
            prior = y;
            if (state->previous_valid) {
                temporal += abs((int)y - (int)state->previous[line][sx]);
                ++temporal_samples;
            }
            state->previous[line][sx] = y;
            ++samples;
        }
    }
    double mean = samples ? sum_y / samples : 0.0;
    double variance = samples ? sum_y2 / samples - mean * mean : 0.0;
    if (variance < 0.0)
        variance = 0.0;
    /* Second pass for the fraction within two code values of the mean. */
    for (int line = 0; line < RASTER_LINES; ++line) {
        if (!sampled_picture_line(line))
            continue;
        const uint8_t *row = raster + (size_t)line * BYTES_PER_LINE;
        for (int sx = 0; sx < X_SAMPLES; ++sx) {
            uint8_t y = row[sx * SAMPLE_STEP_PIXELS * 2 + 1];
            flat += fabs((double)y - mean) <= 2.0;
        }
    }
    double vbi_mean = vbi_samples ? vbi_sum / vbi_samples : 0.0;
    double vbi_variance = vbi_samples
                              ? vbi_sum2 / vbi_samples - vbi_mean * vbi_mean
                              : 0.0;
    if (vbi_variance < 0.0)
        vbi_variance = 0.0;
    out->luma_mean = mean;
    out->luma_sigma = sqrt(variance);
    out->chroma_distance = samples ? chroma / samples : 0.0;
    out->spatial_gradient_energy = gradients ? gradient / gradients : 0.0;
    out->temporal_mad = temporal_samples ? temporal / temporal_samples : 0.0;
    out->hard_padding_fraction = hard_total ? (double)hard / hard_total : 0.0;
    out->vbi_signature_energy = sqrt(vbi_variance);
    out->flat_pixel_fraction = samples ? (double)flat / samples : 0.0;
    state->previous_valid = true;
}

static signal_appearance classify_appearance(const signal_measurements *m,
                                             double *confidence)
{
    if (m->hard_padding_fraction < 0.98) {
        *confidence = clamp01((0.98 - m->hard_padding_fraction) * 10.0);
        return SIGNAL_APPEARANCE_UNKNOWN;
    }
    bool neutral = m->chroma_distance < 3.0;
    if (neutral && m->luma_mean < 8.0 && m->luma_sigma < 4.0 &&
        m->spatial_gradient_energy < 3.0) {
        *confidence = clamp01((8.0 - m->luma_mean) / 8.0 +
                              (4.0 - m->luma_sigma) / 8.0);
        return SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE;
    }
    if (neutral && m->luma_mean >= 8.0 && m->luma_mean <= 240.0 &&
        m->luma_sigma < 3.0 && m->spatial_gradient_energy < 2.0) {
        *confidence = clamp01(1.0 - m->luma_sigma / 3.0);
        return SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE;
    }
    if (m->luma_sigma > 35.0 && m->spatial_gradient_energy > 30.0) {
        *confidence = clamp01(fmin((m->luma_sigma - 30.0) / 25.0,
                                  (m->spatial_gradient_energy - 25.0) / 30.0));
        return SIGNAL_APPEARANCE_SNOW_LIKE;
    }
    if (m->luma_sigma < 5.0 && m->spatial_gradient_energy < 3.0) {
        *confidence = clamp01(1.0 - m->luma_sigma / 5.0);
        return SIGNAL_APPEARANCE_FLAT_AMBIGUOUS;
    }
    *confidence = clamp01(fmax(m->luma_sigma / 24.0,
                              m->spatial_gradient_energy / 18.0));
    return SIGNAL_APPEARANCE_PROGRAM_LIKE;
}

static signal_source_state appearance_source(signal_appearance appearance,
                                             const signal_context *context)
{
    switch (appearance) {
    case SIGNAL_APPEARANCE_PROGRAM_LIKE:
        return SIGNAL_SOURCE_PRESENT;
    case SIGNAL_APPEARANCE_SNOW_LIKE:
        return SIGNAL_SOURCE_REACQUIRING;
    case SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE:
    case SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE:
        return SIGNAL_SOURCE_MUTED;
    case SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800:
        return SIGNAL_SOURCE_NO_INPUT;
    case SIGNAL_APPEARANCE_FLAT_AMBIGUOUS:
        if (context && context->audio_mute_known && context->audio_muted &&
            context->osd_activity_known && context->osd_active)
            return SIGNAL_SOURCE_MUTED;
        return SIGNAL_SOURCE_UNKNOWN;
    default:
        return SIGNAL_SOURCE_UNKNOWN;
    }
}

static uint32_t confirmation_for(const signal_state *state,
                                 signal_source_state source)
{
    if (source == SIGNAL_SOURCE_MUTED || source == SIGNAL_SOURCE_NO_INPUT)
        return state->config.mute_confirm_units;
    return state->config.acquisition_confirm_units;
}

static void open_interval(signal_state *state)
{
    if (!state->unsettled) {
        state->unsettled = true;
        state->active_interval = ++state->interval_serial;
    }
    state->stable_phase_count = 0;
}

bool signal_state_classify(signal_state *state,
                           const unit_video_observation *unit,
                           const signal_context *context,
                           signal_result *out)
{
    if (!state || !unit || !out)
        return false;
    memset(out, 0, sizeof(*out));
    out->transport = unit->transport;
    out->transport_flags = unit->transport_flags;
    out->settled_d1 = out->settled_d2 = 0;

    if (unit->transport == UNIT_TRANSPORT_HOLE ||
        unit->transport == UNIT_TRANSPORT_UNFRAMED ||
        unit->transport == UNIT_TRANSPORT_SHORT) {
        out->appearance = SIGNAL_APPEARANCE_UNKNOWN;
        out->source = SIGNAL_SOURCE_UNKNOWN;
        out->actions |= SIGNAL_ACTION_REGISTRATION_DISCONTINUITY;
        open_interval(state);
        state->previous_valid = false;
    } else if (unit->kind == UNIT_VIDEO_DEVICE_NO_SIGNAL_0800) {
        out->appearance = SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800;
        out->appearance_confidence = 1.0;
    } else if (!unit->fixed_raster_eligible || !unit->bytes) {
        out->appearance = SIGNAL_APPEARANCE_UNKNOWN;
        out->source = SIGNAL_SOURCE_UNKNOWN;
        open_interval(state);
        state->previous_valid = false;
    } else {
        measure_raster(state, unit->bytes, &out->measurements);
        out->appearance = classify_appearance(&out->measurements,
                                              &out->appearance_confidence);
    }

    if (out->appearance == state->appearance_candidate) {
        ++state->appearance_candidate_count;
    } else {
        state->appearance_candidate = out->appearance;
        state->appearance_candidate_count = 1;
    }
    signal_source_state target = appearance_source(out->appearance, context);
    if (target == state->source_candidate) {
        ++state->source_candidate_count;
    } else {
        state->source_candidate = target;
        state->source_candidate_count = 1;
    }

    uint32_t needed = confirmation_for(state, target);
    if (needed < state->config.appearance_confirm_units)
        needed = state->config.appearance_confirm_units;
    if (target != SIGNAL_SOURCE_UNKNOWN &&
        state->source_candidate_count >= needed) {
        signal_source_state prior = state->stable_source;
        state->stable_source = target;
        if (target == SIGNAL_SOURCE_REACQUIRING &&
            prior != SIGNAL_SOURCE_REACQUIRING) {
            out->actions |= SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT;
            state->acquisition_open = true;
            open_interval(state);
        } else if (target == SIGNAL_SOURCE_PRESENT &&
                   prior != SIGNAL_SOURCE_PRESENT) {
            if (!state->acquisition_open)
                out->actions |= SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT;
            state->acquisition_open = true;
            open_interval(state);
        } else if (target == SIGNAL_SOURCE_MUTED ||
                   target == SIGNAL_SOURCE_NO_INPUT) {
            state->acquisition_open = false;
            open_interval(state);
        }
        out->source = state->stable_source;
        out->source_confidence = clamp01(
            (double)state->source_candidate_count / needed);
    } else {
        out->source = SIGNAL_SOURCE_UNKNOWN;
        out->source_confidence = 0.0;
    }

    if (out->appearance == SIGNAL_APPEARANCE_UNKNOWN ||
        out->source == SIGNAL_SOURCE_UNKNOWN)
        open_interval(state);
    out->unsettled = state->unsettled;
    out->unsettled_interval_id = state->active_interval;
    out->settled_phase_known = state->phase_valid && !state->unsettled;
    if (state->phase_valid) {
        out->settled_d1 = state->phase_d1;
        out->settled_d2 = state->phase_d2;
    }
    return true;
}

static uint32_t popcount64(uint64_t value)
{
    uint32_t count = 0;
    while (value) {
        value &= value - 1;
        ++count;
    }
    return count;
}

void signal_state_note_registration(signal_state *state, signal_result *result,
                                    bool observation_known, int8_t d1, int8_t d2,
                                    double confidence)
{
    if (!state || !result)
        return;
    bool changed = observation_known && state->phase_valid &&
                   (d1 != state->phase_d1 || d2 != state->phase_d2);
    uint32_t window = state->config.phase_chatter_window_units;
    uint64_t mask = window == 64 ? UINT64_MAX : ((UINT64_C(1) << window) - 1);
    state->phase_change_bits = ((state->phase_change_bits << 1) |
                                (changed ? 1u : 0u)) & mask;
    if (state->phase_window_count < window)
        ++state->phase_window_count;
    if (popcount64(state->phase_change_bits) >=
        state->config.phase_chatter_threshold)
        open_interval(state);

    if (observation_known && confidence >= 0.25) {
        if (!state->phase_valid || (d1 == state->phase_d1 && d2 == state->phase_d2)) {
            if (!state->phase_valid) {
                state->phase_d1 = d1;
                state->phase_d2 = d2;
                state->phase_valid = true;
            }
            ++state->stable_phase_count;
        } else {
            /* Positive departures are provisional until the trajectory layer
             * resolves them; do not overwrite the settled phase here. */
            open_interval(state);
        }
    } else if (state->unsettled) {
        state->stable_phase_count = 0;
    }

    if (state->unsettled && state->stable_source == SIGNAL_SOURCE_PRESENT &&
        state->stable_phase_count >= state->config.settle_confirm_units &&
        popcount64(state->phase_change_bits) == 0) {
        state->unsettled = false;
        state->acquisition_open = false;
    }
    result->unsettled = state->unsettled;
    result->unsettled_interval_id = state->active_interval;
    result->settled_phase_known = state->phase_valid && !state->unsettled;
    if (state->phase_valid) {
        result->settled_d1 = state->phase_d1;
        result->settled_d2 = state->phase_d2;
    }
}

void signal_state_commit_registration(signal_state *state, int8_t d1, int8_t d2)
{
    if (!state)
        return;
    state->phase_valid = true;
    state->phase_d1 = d1;
    state->phase_d2 = d2;
    state->stable_phase_count = 0;
    state->phase_change_bits = 0;
    state->phase_window_count = 0;
}

const char *signal_appearance_name(signal_appearance appearance)
{
    switch (appearance) {
    case SIGNAL_APPEARANCE_PROGRAM_LIKE: return "ProgramLike";
    case SIGNAL_APPEARANCE_SNOW_LIKE: return "SnowLike";
    case SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE: return "NeutralGrayMuteLike";
    case SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE: return "SubBlackMuteLike";
    case SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800: return "DeviceNoSignal0800";
    case SIGNAL_APPEARANCE_FLAT_AMBIGUOUS: return "FlatAmbiguous";
    default: return "Unknown";
    }
}

const char *signal_source_state_name(signal_source_state source)
{
    switch (source) {
    case SIGNAL_SOURCE_PRESENT: return "Present";
    case SIGNAL_SOURCE_REACQUIRING: return "Reacquiring";
    case SIGNAL_SOURCE_MUTED: return "Muted";
    case SIGNAL_SOURCE_NO_INPUT: return "NoInput";
    default: return "Unknown";
    }
}
