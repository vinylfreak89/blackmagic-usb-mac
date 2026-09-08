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
    bool picture_disrupted;
    bool loss_active;
    bool epoch_started;

    bool unsettled;
    uint64_t interval_serial;
    uint64_t active_interval;

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
        .acquisition_confirm_units = 5,
        .mute_confirm_units = 3,
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
        chosen.acquisition_confirm_units, 5);
    chosen.mute_confirm_units = clamp_nonzero(chosen.mute_confirm_units, 3);
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

typedef struct correlation_sums {
    double a, b, aa, bb, ab;
    unsigned n;
} correlation_sums;

static void add_pair(correlation_sums *s, double a, double b)
{
    s->a += a; s->b += b; s->aa += a*a; s->bb += b*b;
    s->ab += a*b; ++s->n;
}

static double correlation(correlation_sums s, bool *known)
{
    double a = s.n*s.aa-s.a*s.a, b = s.n*s.bb-s.b*s.b;
    *known = a > 0 && b > 0;
    return *known ? (s.n*s.ab-s.a*s.b)/sqrt(a*b) : 0;
}

static int compare_double(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

/* Same sampled field body as the existing classifier; adjacent rows never
 * cross a field boundary. Statistics retain gain/offset invariance. */
static void measure_coherence(const signal_state *state, const uint8_t *raster,
                              signal_measurements *out)
{
    for (int f = 0; f < 2; ++f) {
        int first = f ? 282 : 20;
        double rows[236], ranges[237], sigmas[237];
        unsigned count = 0;
        correlation_sums temporal = {0};
        for (int y = first; y < first + 237; ++y) {
            correlation_sums row = {0};
            int lo = 255, hi = 0;
            double sum = 0, sum2 = 0;
            for (int x = 0; x < X_SAMPLES; ++x) {
                size_t p = (size_t)y*BYTES_PER_LINE + x*SAMPLE_STEP_PIXELS*2 + 1;
                int v = raster[p];
                sum += v; sum2 += v*v;
                if (v < lo) lo = v;
                if (v > hi) hi = v;
                if (y > first) add_pair(&row, v, raster[p-BYTES_PER_LINE]);
                if (state->previous_valid) add_pair(&temporal, v, state->previous[y][x]);
            }
            bool known;
            double c = correlation(row, &known);
            if (known) rows[count++] = c;
            ranges[y-first] = hi-lo;
            sigmas[y-first] = sqrt(fmax(0, sum2/X_SAMPLES -
                                        (sum/X_SAMPLES)*(sum/X_SAMPLES)));
        }
        qsort(rows, count, sizeof *rows, compare_double);
        qsort(ranges, 237, sizeof *ranges, compare_double);
        qsort(sigmas, 237, sizeof *sigmas, compare_double);
        out->row_coherence[f] = count ? rows[count/2] : 0;
        out->temporal_coherence[f] = correlation(temporal, &out->temporal_coherence_known[f]);
        out->median_row_range[f] = ranges[237/2];
        out->median_row_sigma[f] = sigmas[237/2];
        int lo = 255, hi = 0;
        /* Device regenerated blanking rows, excluding the insert. */
        for (int y = f ? 270 : 7; y <= (f ? 278 : 15); ++y)
            for (int x = 0; x < 720; ++x) {
                int v = raster[(size_t)y*BYTES_PER_LINE + x*2 + 1];
                if (v < lo) lo = v;
                if (v > hi) hi = v;
            }
        out->blanking_range[f] = hi-lo;
    }
}

static void measure_raster(signal_state *state, const uint8_t *unit,
                           signal_measurements *out)
{
    const uint8_t *raster = unit + HEADER_BYTES;
    measure_coherence(state, raster, out);
    double sum_y = 0.0, sum_y2 = 0.0, chroma = 0.0;
    double gradient = 0.0, temporal = 0.0;
    uint64_t samples = 0, gradients = 0, temporal_samples = 0;
    uint64_t flat = 0, hard = 0, hard_total = 0, neutral_chroma = 0;
    uint64_t subblack = 0;
    uint32_t luma_histogram[256] = {0};
    uint32_t chroma_distance_histogram[129] = {0};
    enum { TILE_COLUMNS = 15, TILE_ROWS_PER_FIELD = 15, TILE_COUNT = 450 };
    uint8_t tile_min[TILE_COUNT], tile_max[TILE_COUNT];
    uint8_t previous_line[X_SAMPLES];
    bool previous_line_valid = false;
    memset(tile_min, 255, sizeof tile_min);
    memset(tile_max, 0, sizeof tile_max);
    double vbi_sum = 0.0, vbi_sum2 = 0.0;
    uint64_t vbi_samples = 0;
    bool had_temporal_reference = state->previous_valid;

    for (int line = 0; line < RASTER_LINES; ++line) {
        const uint8_t *row = raster + (size_t)line * BYTES_PER_LINE;
        if (hard_line_expected(line)) {
            for (int x = 0; x < 720; ++x) {
                ++hard_total;
                hard += row[x * 2] == 128 && row[x * 2 + 1] == 16;
            }
        }
        bool vbi = line == 16 || line == 17 || line == 279 || line == 280;
        if (line == 20 || line == 282)
            previous_line_valid = false;
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
            int chroma_delta = abs((int)c - 128);
            chroma += chroma_delta;
            neutral_chroma += chroma_delta <= 4;
            ++chroma_distance_histogram[chroma_delta];
            subblack += y < 16;
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
            int field = line >= 282;
            int relative_line = line - (field ? 282 : 20);
            int tile_y = relative_line * TILE_ROWS_PER_FIELD / 237;
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
    uint64_t midpoint = samples / 2;
    uint64_t cumulative = 0;
    unsigned median = 0;
    for (; median < 255; ++median) {
        cumulative += luma_histogram[median];
        if (cumulative > midpoint)
            break;
    }
    cumulative = 0;
    unsigned chroma_median = 0;
    for (; chroma_median < 128; ++chroma_median) {
        cumulative += chroma_distance_histogram[chroma_median];
        if (cumulative > midpoint)
            break;
    }
    unsigned active_tiles = 0;
    for (int tile = 0; tile < TILE_COUNT; ++tile)
        active_tiles += (unsigned)(tile_max[tile] - tile_min[tile] >= 12);
    double extent = (double)active_tiles / TILE_COUNT;
    double static_score = had_temporal_reference
                              ? clamp01((3.0 - (temporal_samples ? temporal / temporal_samples : 0.0)) / 3.0)
                              : 0.0;
    double localized = clamp01(extent / 0.02) * clamp01((0.35 - extent) / 0.25);
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

static bool incoherent_noise(const signal_measurements *m)
{
    /* Measured separation, not standards: 27:18 noise rows have median
     * adjacent-row correlation -0.020..0.038; program controls across the
     * four captures' program intervals are >=0.699 (commercial >=6593).
     * Snow temporal correlation is <=0.767 in
     * at least one field; the preceding sub-black onset remains >=0.831.
     * See tests/coherence_probe.c and the measurement report. Broadband
     * extent is a median row sigma above this field's entire blanking range,
     * so sparse overlays and the blanking dither cannot supply it. */
    for (int f = 0; f < 2; ++f) {
        if (m->row_coherence[f] < 0.1 &&
            m->median_row_sigma[f] > m->blanking_range[f] &&
            m->temporal_coherence_known[f] && m->temporal_coherence[f] < 0.8) {
            return true;
        }
    }
    return false;
}

static signal_appearance classify_appearance(const signal_measurements *m,
                                             double *confidence)
{
    if (m->hard_padding_fraction < 0.98) {
        *confidence = clamp01((0.98 - m->hard_padding_fraction) * 10.0);
        return SIGNAL_APPEARANCE_UNKNOWN;
    }
    bool neutral = m->chroma_distance_median <= 4.0 &&
                   m->neutral_chroma_fraction >= 0.75;
    /* A robustly sub-blanking neutral background is not program, even when
     * sparse white streaks or an OSD contribute arbitrarily sharp edges. */
    if (neutral && m->luma_median <= 12.0) {
        *confidence = clamp01((16.0 - m->luma_median) / 8.0 +
                              (m->subblack_pixel_fraction - 0.70));
        return SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE;
    }
    if (m->luma_sigma > 35.0 && m->spatial_gradient_energy > 30.0 &&
        m->program_extent_fraction > 0.50) {
        *confidence = clamp01(fmin((m->luma_sigma - 30.0) / 25.0,
                                  (m->spatial_gradient_energy - 25.0) / 30.0));
        return SIGNAL_APPEARANCE_SNOW_LIKE;
    }
    bool uniform_neutral = m->luma_sigma < 3.0 &&
                           m->spatial_gradient_energy < 2.0;
    bool neutral_with_small_overlay =
        m->flat_pixel_fraction > 0.55 &&
        m->program_extent_fraction < 0.30 &&
        (!m->temporal_mad || m->temporal_mad < 3.0);
    if (neutral && m->luma_mean >= 8.0 && m->luma_mean <= 240.0 &&
        (uniform_neutral || neutral_with_small_overlay)) {
        *confidence = uniform_neutral
                          ? clamp01(1.0 - m->luma_sigma / 3.0)
                          : clamp01(fmax((m->flat_pixel_fraction - 0.50) * 2.0,
                                        m->localized_overlay_score));
        return SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE;
    }
    if (m->program_extent_fraction < 0.12) {
        *confidence = clamp01(1.0 - m->program_extent_fraction / 0.12);
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
                                     : 0.5;
        out->unsettled = state->unsettled;
        out->unsettled_interval_id = state->active_interval;
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
        out->appearance = classify_appearance(&out->measurements,
                                              &out->appearance_confidence);
    }

    /* Wreck onset at 49105: field-2 row/temporal coherence .295/.419;
     * none of the normal-program controls in captures 1..4 meets <.5 and <.8
     * (commercial counter >=6593; its rewind is a separate control).
     * A content cut with spatial structure alone cannot enter this state.
     * Once entered, incoherent successors cannot acquire Present merely
     * because one wrecked unit has spatially coherent bands. */
    bool disruption = false, temporal_clean = true, spatial_clean = true;
    for (int f = 0; f < 2; ++f) {
        const signal_measurements *m = &out->measurements;
        bool temporal = m->temporal_coherence_known[f];
        bool broad = m->median_row_sigma[f] > m->blanking_range[f];
        disruption |= broad && temporal && m->row_coherence[f] < 0.5 &&
                      m->temporal_coherence[f] < 0.8;
        temporal_clean &= temporal && m->temporal_coherence[f] >= 0.8;
        /* Both-field minimum over wreck 49105..49112 is at most .887;
         * returned program 49164..49168 is at least .934. Spatial recovery
         * also permits real content motion/cuts with low temporal coherence. */
        spatial_clean &= m->row_coherence[f] >= 0.9;
    }
    bool blocked_picture = out->appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE &&
        (disruption || (state->picture_disrupted && !temporal_clean && !spatial_clean));
    if (blocked_picture) {
        state->picture_disrupted = true;
    }
    bool snow = out->appearance == SIGNAL_APPEARANCE_SNOW_LIKE ||
        (unit->fixed_raster_eligible && incoherent_noise(&out->measurements));
    out->lock_like_loss = snow ||
                         out->appearance == SIGNAL_APPEARANCE_DEVICE_NO_SIGNAL_0800;
    /* A positively identified mute ends the wrecked-picture episode, not
     * the loss epoch. It stays gated; return to program still needs source
     * confirmation. Do not latch a subsequent clean fade as damaged. */
    if (!out->lock_like_loss &&
        (out->appearance == SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE ||
         out->appearance == SIGNAL_APPEARANCE_NEUTRAL_GRAY_MUTE_LIKE))
        state->picture_disrupted = false;
    if (out->lock_like_loss) {
        if (!state->loss_active) {
            out->actions |= SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT;
            open_interval(state);
        }
        state->loss_active = true;
        state->epoch_started = true;
        state->picture_disrupted = true;
    }

    signal_appearance observed_appearance = out->appearance;
    out->observed_appearance = observed_appearance;
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
    /* Safety evidence is current-unit, not subject to appearance hysteresis.
     * Keep that hysteresis independent so a snow override cannot rewrite the
     * following sub-black/grey appearance history. */
    signal_appearance safety_appearance = snow ? SIGNAL_APPEARANCE_SNOW_LIKE :
        blocked_picture ? SIGNAL_APPEARANCE_INCOHERENT : observed_appearance;
    out->observed_appearance = safety_appearance;
    if (snow || (blocked_picture && out->appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE)) {
        out->appearance = safety_appearance;
        out->appearance_confidence = 1.0;
    }

    /* Source inference accumulates the instantaneous property observation in
     * parallel with appearance hysteresis, so confirmation is not paid twice. */
    signal_source_state target = appearance_source(safety_appearance, context);
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
        state->stable_source = SIGNAL_SOURCE_UNKNOWN;
        state->source_candidate = SIGNAL_SOURCE_UNKNOWN;
        state->source_candidate_count = 1;
    } else if (out->lock_like_loss ||
               blocked_picture ||
               (target == SIGNAL_SOURCE_MUTED &&
                observed_appearance == SIGNAL_APPEARANCE_SUBBLACK_MUTE_LIKE) ||
               state->source_candidate_count >= needed) {
        signal_source_state prior = state->stable_source;
        state->stable_source = target;
        if (target != prior && target == SIGNAL_SOURCE_REACQUIRING) {
            open_interval(state);
        } else if (target != prior && target == SIGNAL_SOURCE_PRESENT) {
            if (!state->epoch_started)
                out->actions |= SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT;
            state->epoch_started = true;
            state->loss_active = false;
            state->picture_disrupted = false;
            open_interval(state);
            state->unsettled = false;
        } else if (target != prior &&
                   (target == SIGNAL_SOURCE_MUTED ||
                    target == SIGNAL_SOURCE_NO_INPUT)) {
            open_interval(state);
            /* The confirmed non-picture state is itself a settled endpoint;
             * raster registration has no meaning until acquisition resumes. */
            state->unsettled = false;
        } else if (target != prior && target == SIGNAL_SOURCE_UNKNOWN) {
            open_interval(state);
        }
    }
    out->source = state->stable_source;
    out->normal_picture = unit->fixed_raster_eligible && unit->bytes &&
        safety_appearance == SIGNAL_APPEARANCE_PROGRAM_LIKE &&
        state->stable_source == SIGNAL_SOURCE_PRESENT;
    out->source_confidence = state->stable_source == SIGNAL_SOURCE_UNKNOWN
                                 ? 0.0
                                 : target == state->stable_source
                                       ? clamp01((double)state->source_candidate_count / needed)
                                       : 0.5;

    if (state->interval_serial == 0 && out->source == SIGNAL_SOURCE_UNKNOWN)
        open_interval(state);
    out->unsettled = state->unsettled;
    out->unsettled_interval_id = state->active_interval;
    return true;
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
    case SIGNAL_APPEARANCE_INCOHERENT: return "Incoherent";
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
