#include "signal_state.h"

#include <math.h>
#include <stdalign.h>
#include <stdlib.h>
#include <string.h>

enum {
    RASTER_LINES = 525,
    RASTER_WIDTH = 720,
    UYVY_PIXEL_BYTES = 2,
    CHROMA_CENTER = 128,
    HARD_PADDING_Y = 16,
    LUMA_MAX = 255,
    PICTURE_F1_FIRST = 20, PICTURE_F1_LAST = 256,
    PICTURE_F2_FIRST = 282, PICTURE_F2_LAST = 518,
    PICTURE_FIELD_LINES = PICTURE_F1_LAST - PICTURE_F1_FIRST + 1,
    PADDING_HEAD_LAST = 6, PADDING_MIDDLE_FIRST = 261,
    PADDING_MIDDLE_LAST = 269, PADDING_TAIL_FIRST = 523,
    VBI_F1_FIRST = 16, VBI_F1_LAST = 17,
    VBI_F2_FIRST = 279, VBI_F2_LAST = 280,
    TILE_COLUMNS = 15, TILE_ROWS_PER_FIELD = 15,
    TILE_COUNT = 2 * TILE_COLUMNS * TILE_ROWS_PER_FIELD,
    BYTES_PER_LINE = 1440,
    HEADER_BYTES = 48,
    X_SAMPLES = 180,
    SAMPLE_STEP_PIXELS = 4,
    MAX_PHASE_WINDOW = 64,
};

struct signal_state {
    signal_state_config config;
    uint64_t epoch;
    signal_appearance stable_appearance;
    double stable_appearance_confidence;
    signal_appearance appearance_candidate;
    double appearance_candidate_confidence;
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
        .appearance_confirm_units = 2, /* 4fc8e9e: initial appearance confirmation. */
        .acquisition_confirm_units = 5, /* edcabf0: robust source acquisition confirmation. */
        .mute_confirm_units = 3, /* 4fc8e9e: initial mute confirmation. */
        .phase_chatter_window_units = 30, /* 4fc8e9e: initial optional phase window. */
        .phase_chatter_threshold = 4, /* 4fc8e9e: initial optional phase chatter count. */
        .settle_confirm_units = 30, /* 4fc8e9e: initial applied-phase settling window. */
        .tile_activity_min = 12, /* edcabf0: Tile luma range >= value counts as active. */
        .flat_luma_distance_max = 2.0, /* 4fc8e9e: Sample |Y - mean| <= value counts as flat. */
        .neutral_chroma_distance_max = 4, /* edcabf0: Sample |C - 128| <= value counts as neutral. */
        .subblack_luma_cutoff = 16, /* edcabf0: Sample Y < value counts as sub-black (not the padding code). */
        .overlay_static_mad_max = 3.0, /* edcabf0: Static score clamp((value - temporal MAD) / value). */
        .overlay_extent_rise = 0.02, /* edcabf0: Rising extent-score denominator. */
        .overlay_extent_fall_start = 0.35, /* edcabf0: Falling extent-score zero crossing. */
        .overlay_extent_fall_width = 0.25, /* edcabf0: Falling extent-score denominator. */
        .padding_fraction_min = 0.98, /* 4fc8e9e: Padding fraction below value makes appearance unknown. */
        .padding_confidence_gain = 10.0, /* 4fc8e9e: Unknown confidence multiplier for padding deficit. */
        .neutral_chroma_median_max = 4.0, /* edcabf0: Median chroma distance <= value permits neutral rules. */
        .neutral_chroma_fraction_min = 0.75, /* edcabf0: Neutral sample fraction >= value permits neutral rules. */
        .subblack_median_max = 12.0, /* edcabf0: Neutral luma median <= value selects sub-black. */
        .subblack_confidence_luma_reference = 16.0, /* edcabf0: Sub-black confidence luma zero reference. */
        .subblack_confidence_luma_span = 8.0, /* edcabf0: Sub-black confidence luma denominator. */
        .subblack_confidence_fraction_offset = 0.70, /* edcabf0: Sub-black confidence fraction subtrahend. */
        .snow_sigma_min = 35.0, /* edcabf0: Sigma > value required for snow. */
        .snow_gradient_min = 30.0, /* edcabf0: Gradient > value required for snow. */
        .snow_extent_min = 0.50, /* edcabf0: Active extent > value required for snow. */
        .snow_confidence_sigma_offset = 30.0, /* edcabf0: Snow confidence sigma subtrahend. */
        .snow_confidence_sigma_span = 25.0, /* edcabf0: Snow confidence sigma denominator. */
        .snow_confidence_gradient_offset = 25.0, /* edcabf0: Snow confidence gradient subtrahend. */
        .snow_confidence_gradient_span = 30.0, /* edcabf0: Snow confidence gradient denominator. */
        .gray_sigma_max = 3.0, /* 7928b67: Uniform sigma < value; also uniform confidence denominator. */
        .gray_gradient_max = 2.0, /* 7928b67: Uniform gradient < value. */
        .gray_flat_fraction_min = 0.55, /* 7928b67: Overlay branch requires flat fraction > value. */
        .gray_extent_max = 0.30, /* edcabf0: Overlay branch requires extent < value. */
        .gray_temporal_mad_max = 3.0, /* edcabf0: Overlay branch permits zero MAD or MAD < value. */
        .gray_mean_min = 8.0, /* 4fc8e9e: Neutral-gray rule requires mean >= value. */
        .gray_mean_max = 240.0, /* 4fc8e9e: Neutral-gray rule requires mean <= value. */
        .gray_confidence_flat_offset = 0.50, /* edcabf0: Overlay confidence flat-fraction subtrahend. */
        .gray_confidence_flat_gain = 2.0, /* edcabf0: Overlay confidence flat-fraction multiplier. */
        .ambiguous_extent_max = 0.12, /* edcabf0: Extent < value selects flat ambiguity; also confidence denominator. */
        .program_confidence_sigma_span = 24.0, /* 4fc8e9e: Program confidence sigma denominator. */
        .program_confidence_gradient_span = 18.0, /* 4fc8e9e: Program confidence gradient denominator. */
        .held_source_confidence = 0.5, /* edcabf0: Confidence when retaining source across contrary or absent evidence. */
        .phase_change_confidence_min = 0.25, /* edcabf0: Optional phase feedback accepts confidence >= value. */
    };
    return config;
}

static uint32_t clamp_nonzero(uint32_t value, uint32_t fallback)
{
    return value ? value : fallback;
}

void signal_state_init(signal_state *state, const signal_state_config *config)
{
    const signal_state_config defaults = signal_state_default_config();
    signal_state_config chosen = config ? *config : defaults;
    chosen.appearance_confirm_units = clamp_nonzero(
        chosen.appearance_confirm_units, defaults.appearance_confirm_units);
    chosen.acquisition_confirm_units = clamp_nonzero(
        chosen.acquisition_confirm_units, defaults.acquisition_confirm_units);
    chosen.mute_confirm_units = clamp_nonzero(chosen.mute_confirm_units, defaults.mute_confirm_units);
    chosen.phase_chatter_window_units = clamp_nonzero(
        chosen.phase_chatter_window_units, defaults.phase_chatter_window_units);
    if (chosen.phase_chatter_window_units > MAX_PHASE_WINDOW)
        chosen.phase_chatter_window_units = MAX_PHASE_WINDOW;
    chosen.phase_chatter_threshold = clamp_nonzero(
        chosen.phase_chatter_threshold, defaults.phase_chatter_threshold);
    if (chosen.phase_chatter_threshold > chosen.phase_chatter_window_units)
        chosen.phase_chatter_threshold = chosen.phase_chatter_window_units;
    chosen.settle_confirm_units = clamp_nonzero(chosen.settle_confirm_units, defaults.settle_confirm_units);
    memset(state, 0, sizeof(*state));
    state->config = chosen;
}

const signal_state_config *signal_state_get_config(const signal_state *state)
{
    return &state->config;
}

void signal_state_begin_epoch(signal_state *state, uint64_t epoch)
{
    signal_state_config config = state->config;
    signal_state_init(state, &config);
    state->epoch = epoch;
}

static bool hard_line_expected(int line)
{
    return line <= PADDING_HEAD_LAST ||
           (line >= PADDING_MIDDLE_FIRST && line <= PADDING_MIDDLE_LAST) ||
           line >= PADDING_TAIL_FIRST;
}

static bool sampled_picture_line(int line)
{
    return (line >= PICTURE_F1_FIRST && line <= PICTURE_F1_LAST) ||
           (line >= PICTURE_F2_FIRST && line <= PICTURE_F2_LAST);
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
    const signal_state_config *c = &state->config;
    const uint8_t *raster = unit + HEADER_BYTES;
    double sum_y = 0.0, sum_y2 = 0.0, chroma = 0.0;
    double gradient = 0.0, temporal = 0.0;
    uint64_t samples = 0, gradients = 0, temporal_samples = 0;
    uint64_t flat = 0, hard = 0, hard_total = 0, neutral_chroma = 0;
    uint64_t subblack = 0;
    uint32_t luma_histogram[LUMA_MAX + 1] = {0};
    uint32_t chroma_distance_histogram[CHROMA_CENTER + 1] = {0};
    uint8_t tile_min[TILE_COUNT], tile_max[TILE_COUNT];
    uint8_t previous_line[X_SAMPLES];
    bool previous_line_valid = false;
    memset(tile_min, LUMA_MAX, sizeof tile_min);
    memset(tile_max, 0, sizeof tile_max);
    double vbi_sum = 0.0, vbi_sum2 = 0.0;
    uint64_t vbi_samples = 0;
    bool had_temporal_reference = state->previous_valid;

    for (int line = 0; line < RASTER_LINES; ++line) {
        const uint8_t *row = raster + (size_t)line * BYTES_PER_LINE;
        if (hard_line_expected(line)) {
            for (int x = 0; x < RASTER_WIDTH; ++x) {
                ++hard_total;
                hard += row[x * UYVY_PIXEL_BYTES] == CHROMA_CENTER &&
                        row[x * UYVY_PIXEL_BYTES + 1] == HARD_PADDING_Y;
            }
        }
        bool vbi = line == VBI_F1_FIRST || line == VBI_F1_LAST ||
                   line == VBI_F2_FIRST || line == VBI_F2_LAST;
        if (line == PICTURE_F1_FIRST || line == PICTURE_F2_FIRST)
            previous_line_valid = false;
        uint8_t prior = 0;
        for (int sx = 0; sx < X_SAMPLES; ++sx) {
            int x = sx * SAMPLE_STEP_PIXELS;
            uint8_t chroma_sample = row[x * UYVY_PIXEL_BYTES];
            uint8_t y = row[x * UYVY_PIXEL_BYTES + 1];
            if (vbi) {
                vbi_sum += y;
                vbi_sum2 += (double)y * y;
                ++vbi_samples;
            }
            if (!sampled_picture_line(line))
                continue;
            sum_y += y;
            sum_y2 += (double)y * y;
            int chroma_delta = abs((int)chroma_sample - CHROMA_CENTER);
            chroma += chroma_delta;
            neutral_chroma += chroma_delta <= c->neutral_chroma_distance_max;
            ++chroma_distance_histogram[chroma_delta];
            subblack += y < c->subblack_luma_cutoff;
            ++luma_histogram[y];
            if (sx) {
                gradient += abs((int)y - (int)prior);
                ++gradients;
            }
            if (previous_line_valid) {
                gradient += abs((int)y - (int)previous_line[sx]);
                ++gradients;
            }
            prior = y;
            previous_line[sx] = y;
            int field = line >= PICTURE_F2_FIRST;
            int relative_line = line - (field ? PICTURE_F2_FIRST : PICTURE_F1_FIRST);
            int tile_y = relative_line * TILE_ROWS_PER_FIELD / PICTURE_FIELD_LINES;
            int tile_x = sx * TILE_COLUMNS / X_SAMPLES;
            int tile = field * TILE_COLUMNS * TILE_ROWS_PER_FIELD +
                       tile_y * TILE_COLUMNS + tile_x;
            if (y < tile_min[tile]) tile_min[tile] = y;
            if (y > tile_max[tile]) tile_max[tile] = y;
            if (state->previous_valid) {
                temporal += abs((int)y - (int)state->previous[line][sx]);
                ++temporal_samples;
            }
            state->previous[line][sx] = y;
            ++samples;
        }
        if (sampled_picture_line(line))
            previous_line_valid = true;
    }
    double mean = samples ? sum_y / samples : 0.0;
    double variance = samples ? sum_y2 / samples - mean * mean : 0.0;
    if (variance < 0.0)
        variance = 0.0;
    /* Second pass for the configured flat-pixel distance from the mean. */
    for (int line = 0; line < RASTER_LINES; ++line) {
        if (!sampled_picture_line(line))
            continue;
        const uint8_t *row = raster + (size_t)line * BYTES_PER_LINE;
        for (int sx = 0; sx < X_SAMPLES; ++sx) {
            uint8_t y = row[sx * SAMPLE_STEP_PIXELS * UYVY_PIXEL_BYTES + 1];
            flat += fabs((double)y - mean) <= c->flat_luma_distance_max;
        }
    }
    double vbi_mean = vbi_samples ? vbi_sum / vbi_samples : 0.0;
    double vbi_variance = vbi_samples
                              ? vbi_sum2 / vbi_samples - vbi_mean * vbi_mean
                              : 0.0;
    if (vbi_variance < 0.0)
        vbi_variance = 0.0;
    uint64_t midpoint = samples / 2;
    uint64_t cumulative = 0;
    unsigned median = 0;
    for (; median < LUMA_MAX; ++median) {
        cumulative += luma_histogram[median];
        if (cumulative > midpoint)
            break;
    }
    cumulative = 0;
    unsigned chroma_median = 0;
    for (; chroma_median < CHROMA_CENTER; ++chroma_median) {
        cumulative += chroma_distance_histogram[chroma_median];
        if (cumulative > midpoint)
            break;
    }
    unsigned active_tiles = 0;
    for (int tile = 0; tile < TILE_COUNT; ++tile)
        active_tiles += (unsigned)(tile_max[tile] - tile_min[tile] >= c->tile_activity_min);
    double extent = (double)active_tiles / TILE_COUNT;
    double static_score = had_temporal_reference
                              ? clamp01((c->overlay_static_mad_max - (temporal_samples ? temporal / temporal_samples : 0.0)) / c->overlay_static_mad_max)
                              : 0.0;
    double localized = clamp01(extent / c->overlay_extent_rise) *
                       clamp01((c->overlay_extent_fall_start - extent) / c->overlay_extent_fall_width);
    out->luma_mean = mean;
    out->luma_median = median;
    out->luma_sigma = sqrt(variance);
    out->chroma_distance = samples ? chroma / samples : 0.0;
    out->chroma_distance_median = chroma_median;
    out->neutral_chroma_fraction = samples ? (double)neutral_chroma / samples : 0.0;
    out->subblack_pixel_fraction = samples ? (double)subblack / samples : 0.0;
    out->spatial_gradient_energy = gradients ? gradient / gradients : 0.0;
    out->program_extent_fraction = extent;
    out->localized_overlay_score = localized *
                                    (samples ? (double)flat / samples : 0.0) *
                                    static_score;
    out->temporal_mad = temporal_samples ? temporal / temporal_samples : 0.0;
    out->hard_padding_fraction = hard_total ? (double)hard / hard_total : 0.0;
    out->vbi_signature_energy = sqrt(vbi_variance);
    out->flat_pixel_fraction = samples ? (double)flat / samples : 0.0;
    state->previous_valid = true;
}

static signal_appearance classify_appearance(const signal_state_config *c,
                                             const signal_measurements *m,
                                             double *confidence)
{
    if (m->hard_padding_fraction < c->padding_fraction_min) {
        *confidence = clamp01((c->padding_fraction_min - m->hard_padding_fraction) * c->padding_confidence_gain);
        return SIGNAL_APPEARANCE_UNKNOWN;
    }
    bool neutral = m->chroma_distance_median <= c->neutral_chroma_median_max &&
                   m->neutral_chroma_fraction >= c->neutral_chroma_fraction_min;
    /* A robustly sub-blanking neutral background is not program, even when
     * sparse white streaks or an OSD contribute arbitrarily sharp edges. */
    if (neutral && m->luma_median <= c->subblack_median_max) {
        *confidence = clamp01((c->subblack_confidence_luma_reference - m->luma_median) / c->subblack_confidence_luma_span +
                              (m->subblack_pixel_fraction - c->subblack_confidence_fraction_offset));
        return SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE;
    }
    if (m->luma_sigma > c->snow_sigma_min && m->spatial_gradient_energy > c->snow_gradient_min &&
        m->program_extent_fraction > c->snow_extent_min) {
        *confidence = clamp01(fmin((m->luma_sigma - c->snow_confidence_sigma_offset) / c->snow_confidence_sigma_span,
                                  (m->spatial_gradient_energy - c->snow_confidence_gradient_offset) / c->snow_confidence_gradient_span));
        return SIGNAL_APPEARANCE_SNOW_LIKE;
    }
    bool uniform_neutral = m->luma_sigma < c->gray_sigma_max &&
                           m->spatial_gradient_energy < c->gray_gradient_max;
    bool neutral_with_small_overlay =
        m->flat_pixel_fraction > c->gray_flat_fraction_min &&
        m->program_extent_fraction < c->gray_extent_max &&
        (!m->temporal_mad || m->temporal_mad < c->gray_temporal_mad_max);
    if (neutral && m->luma_mean >= c->gray_mean_min && m->luma_mean <= c->gray_mean_max &&
        (uniform_neutral || neutral_with_small_overlay)) {
        *confidence = uniform_neutral
                          ? clamp01(1.0 - m->luma_sigma / c->gray_sigma_max)
                          : clamp01(fmax((m->flat_pixel_fraction - c->gray_confidence_flat_offset) * c->gray_confidence_flat_gain,
                                        m->localized_overlay_score));
        return SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE;
    }
    if (m->program_extent_fraction < c->ambiguous_extent_max) {
        *confidence = clamp01(1.0 - m->program_extent_fraction / c->ambiguous_extent_max);
        return SIGNAL_APPEARANCE_FLAT_AMBIGUOUS;
    }
    *confidence = clamp01(fmax(m->luma_sigma / c->program_confidence_sigma_span,
                              m->spatial_gradient_energy / c->program_confidence_gradient_span));
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
    if (source == SIGNAL_SOURCE_UNKNOWN)
        return state->config.appearance_confirm_units;
    return state->config.acquisition_confirm_units;
}

static uint32_t appearance_confirmation_for(const signal_state *state,
                                             signal_appearance appearance)
{
    uint32_t needed = state->config.appearance_confirm_units;
    uint32_t contextual = (appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE ||
                           appearance == SIGNAL_APPEARANCE_SNOW_LIKE)
                              ? state->config.acquisition_confirm_units
                              : (appearance == SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE ||
                                 appearance == SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE ||
                                 appearance == SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800)
                                    ? state->config.mute_confirm_units
                                    : state->config.appearance_confirm_units;
    return contextual > needed ? contextual : needed;
}

static void increment_saturating(uint32_t *value)
{
    if (*value != UINT32_MAX)
        ++*value;
}

static void open_interval(signal_state *state)
{
    if (!state->unsettled) {
        state->unsettled = true;
        state->active_interval = ++state->interval_serial;
    }
    state->stable_phase_count = 0;
}

static void invalidate_phase(signal_state *state)
{
    state->phase_valid = false;
    state->stable_phase_count = 0;
    state->phase_change_bits = 0;
    state->phase_window_count = 0;
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
    bool host_unobserved = context && context->host_raster_unobserved;
    if (context && context->host_observations_missing_before)
        state->previous_valid = false;

    /* A downstream shed says only that this classifier did not receive the
     * raster. Keep every inferred state bit unchanged. In particular, do not
     * turn host pressure into a source transition or registration epoch. */
    if (host_unobserved) {
        out->host_raster_unobserved = true;
        out->appearance = SIGNAL_APPEARANCE_UNKNOWN;
        out->source = state->stable_source;
        out->source_confidence = state->stable_source == SIGNAL_SOURCE_UNKNOWN
                                     ? 0.0
                                     : state->config.held_source_confidence;
        out->unsettled = state->unsettled;
        out->unsettled_interval_id = state->active_interval;
        out->settled_phase_known = state->phase_valid && !state->unsettled;
        if (state->phase_valid) {
            out->settled_d1 = state->phase_d1;
            out->settled_d2 = state->phase_d2;
        }
        return true;
    }
    bool structural_unknown = false;

    if (unit->transport == UNIT_TRANSPORT_HOLE ||
        unit->transport == UNIT_TRANSPORT_UNFRAMED ||
        unit->transport == UNIT_TRANSPORT_SHORT) {
        out->appearance = SIGNAL_APPEARANCE_UNKNOWN;
        out->source = SIGNAL_SOURCE_UNKNOWN;
        out->actions |= SIGNAL_ACTION_REGISTRATION_DISCONTINUITY;
        open_interval(state);
        structural_unknown = true;
        state->previous_valid = false;
    } else if (unit->kind == UNIT_VIDEO_DEVICE_NO_SIGNAL_0800) {
        out->appearance = SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800;
        out->appearance_confidence = 1.0;
    } else if (!unit->fixed_raster_eligible || !unit->bytes) {
        out->appearance = SIGNAL_APPEARANCE_UNKNOWN;
        out->source = SIGNAL_SOURCE_UNKNOWN;
        open_interval(state);
        structural_unknown = true;
        state->previous_valid = false;
    } else {
        measure_raster(state, unit->bytes, &out->measurements);
        out->appearance = classify_appearance(&state->config, &out->measurements,
                                              &out->appearance_confidence);
    }

    signal_appearance observed_appearance = out->appearance;
    double observed_confidence = out->appearance_confidence;
    if (observed_appearance == state->appearance_candidate) {
        increment_saturating(&state->appearance_candidate_count);
        if (observed_confidence < state->appearance_candidate_confidence)
            state->appearance_candidate_confidence = observed_confidence;
    } else {
        state->appearance_candidate = observed_appearance;
        state->appearance_candidate_count = 1;
        state->appearance_candidate_confidence = observed_confidence;
    }
    uint32_t appearance_needed = appearance_confirmation_for(
        state, observed_appearance);
    if (structural_unknown ||
        observed_appearance == SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800 ||
        observed_appearance == SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE) {
        state->stable_appearance = observed_appearance;
        state->stable_appearance_confidence = observed_confidence;
    } else if (observed_appearance == state->stable_appearance) {
        state->stable_appearance_confidence = observed_confidence;
    } else if (state->appearance_candidate_count >= appearance_needed) {
        state->stable_appearance = observed_appearance;
        state->stable_appearance_confidence = state->appearance_candidate_confidence;
    }
    out->appearance = state->stable_appearance;
    out->appearance_confidence = state->stable_appearance_confidence;

    /* Source inference accumulates the instantaneous property observation in
     * parallel with appearance hysteresis, so confirmation is not paid twice. */
    signal_source_state target = appearance_source(observed_appearance, context);
    if (target == state->source_candidate) {
        increment_saturating(&state->source_candidate_count);
    } else {
        state->source_candidate = target;
        state->source_candidate_count = 1;
    }

    uint32_t needed = confirmation_for(state, target);
    if (needed < state->config.appearance_confirm_units)
        needed = state->config.appearance_confirm_units;
    if (structural_unknown) {
        invalidate_phase(state);
        state->stable_source = SIGNAL_SOURCE_UNKNOWN;
        state->source_candidate = SIGNAL_SOURCE_UNKNOWN;
        state->source_candidate_count = 1;
    } else if ((target == SIGNAL_SOURCE_MUTED &&
                observed_appearance == SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE) ||
               state->source_candidate_count >= needed) {
        signal_source_state prior = state->stable_source;
        state->stable_source = target;
        if (target != prior && target == SIGNAL_SOURCE_REACQUIRING) {
            invalidate_phase(state);
            out->actions |= SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT;
            state->acquisition_open = true;
            open_interval(state);
        } else if (target != prior && target == SIGNAL_SOURCE_PRESENT) {
            invalidate_phase(state);
            if (!state->acquisition_open)
                out->actions |= SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT;
            state->acquisition_open = true;
            open_interval(state);
        } else if (target != prior &&
                   (target == SIGNAL_SOURCE_MUTED ||
                    target == SIGNAL_SOURCE_NO_INPUT)) {
            invalidate_phase(state);
            state->acquisition_open = false;
            open_interval(state);
            /* The confirmed non-picture state is itself a settled endpoint;
             * raster registration has no meaning until acquisition resumes. */
            state->unsettled = false;
        } else if (target != prior && target == SIGNAL_SOURCE_UNKNOWN) {
            state->acquisition_open = false;
            open_interval(state);
        }
    }
    out->source = state->stable_source;
    out->source_confidence = state->stable_source == SIGNAL_SOURCE_UNKNOWN
                                 ? 0.0
                                 : target == state->stable_source
                                       ? clamp01((double)state->source_candidate_count / needed)
                                       : state->config.held_source_confidence;

    if (state->interval_serial == 0 && out->source == SIGNAL_SOURCE_UNKNOWN)
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
                                    double confidence, bool applied_known,
                                    int8_t applied_d1, int8_t applied_d2)
{
    if (!state || !result)
        return;
    if (state->stable_source != SIGNAL_SOURCE_PRESENT) {
        result->unsettled = state->unsettled;
        result->unsettled_interval_id = state->active_interval;
        result->settled_phase_known = false;
        return;
    }

    bool changed = observation_known && confidence >= state->config.phase_change_confidence_min && state->phase_valid &&
                   (d1 != state->phase_d1 || d2 != state->phase_d2);
    uint32_t window = state->config.phase_chatter_window_units;
    uint64_t mask = window == MAX_PHASE_WINDOW ? UINT64_MAX : ((UINT64_C(1) << window) - 1);
    state->phase_change_bits = ((state->phase_change_bits << 1) |
                                (changed ? 1u : 0u)) & mask;
    if (state->phase_window_count < window)
        ++state->phase_window_count;
    if (popcount64(state->phase_change_bits) >=
        state->config.phase_chatter_threshold)
        open_interval(state);

    if (applied_known) {
        if (!state->phase_valid) {
            state->phase_d1 = applied_d1;
            state->phase_d2 = applied_d2;
            state->phase_valid = true;
            state->stable_phase_count = 1;
        } else if (applied_d1 == state->phase_d1 &&
                   applied_d2 == state->phase_d2) {
            increment_saturating(&state->stable_phase_count);
        } else {
            state->phase_d1 = applied_d1;
            state->phase_d2 = applied_d2;
            open_interval(state);
            state->stable_phase_count = 1;
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
