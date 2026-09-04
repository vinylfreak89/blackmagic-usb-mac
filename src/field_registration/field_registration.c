#include "field_registration.h"

#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

enum {
    REGISTRATION_WARMUP = 8,
    FAST_EDGE_WARMUP = 4,
    REGISTRATION_VBI_MARGIN = 25,
    PHASE_BANDS = 3,
    BAND_BIAS = 64,
    BAND_SLOTS = 129,
    BOTTOM_TARGET_SAMPLES = 4,
    BOTTOM_X_FIRST = 10, /* source pixel 40 after 4:1 luma reduction */
    BOTTOM_X_AFTER = 170, /* source pixel 680 */
    BOTTOM_BLACK_NUMERATOR = 3,
    BOTTOM_BLACK_DENOMINATOR = 5,
    BOTTOM_BLACK_MARGIN = 16,
    BOTTOM_TILE_COLUMNS = 15,
    BOTTOM_TILE_ROWS = 15,
    BOTTOM_TILE_COUNT = BOTTOM_TILE_COLUMNS * BOTTOM_TILE_ROWS,
    /* Match signal_state's planned overlay-aware boundary: content in less
     * than 30% of broad tiles is a localized overlay, not program extent. */
    BOTTOM_MIN_ACTIVE_TILES = 68,
    BOTTOM_TILE_RANGE = 12,
    BOTTOM_NOISE_LIMIT = 35,
    BOTTOM_MAX_STEP = 3,
    BOTTOM_REACQUIRE_UNITS = 2,
};

static const int phase_bounds[PHASE_BANDS][2] = {
    {12, 62},   /* source pixels 48..247 */
    {65, 115},  /* source pixels 260..459 */
    {118, 168}, /* source pixels 472..671 */
};

/* A weak temporal minimum cannot positively establish registration, but an
 * opposite-direction minimum is still useful as a veto. This lower bar keeps
 * a content-derived top/bottom edge from moving the whole field against the
 * dominant same-parity picture asset. */
static const double temporal_contradiction_margin = 0.05;

static bool unit_header_valid(const uint8_t *unit)
{
    return unit[0] == 0 && unit[1] == 0 && unit[2] == 0xff &&
           unit[3] == 0xff && unit[6] == 0x01 && unit[7] == 0xe8;
}

static void unknown_decision(fieldreg_decision *out)
{
    memset(out, 0, sizeof(*out));
    out->decision_d1 = FIELDREG_UNKNOWN;
    out->decision_d2 = FIELDREG_UNKNOWN;
    out->frame_observation_d1 = FIELDREG_UNKNOWN;
    out->frame_observation_d2 = FIELDREG_UNKNOWN;
    out->best_d1 = FIELDREG_UNKNOWN;
    out->best_d2 = FIELDREG_UNKNOWN;
    out->pending_d1 = FIELDREG_UNKNOWN;
    out->pending_d2 = FIELDREG_UNKNOWN;
    out->observed_transport_f1 = -1;
    out->observed_transport_f2 = -1;
    out->picture_top_f1 = -1;
    out->picture_top_f2 = -1;
    out->picture_bottom_f1 = -1;
    out->picture_bottom_f2 = -1;
    out->learned_band_mode_f1 = FIELDREG_UNKNOWN;
    out->learned_band_mode_f2 = FIELDREG_UNKNOWN;
    out->learned_bottom_mode_f1 = FIELDREG_UNKNOWN;
    out->learned_bottom_mode_f2 = FIELDREG_UNKNOWN;
    out->phase_vote_left = FIELDREG_UNKNOWN;
    out->phase_vote_center = FIELDREG_UNKNOWN;
    out->phase_vote_right = FIELDREG_UNKNOWN;
    out->phase_motion_left = FIELDREG_UNKNOWN;
    out->phase_motion_center = FIELDREG_UNKNOWN;
    out->phase_motion_right = FIELDREG_UNKNOWN;
    out->phase_priority_band = FIELDREG_UNKNOWN;
    out->phase_consensus = FIELDREG_UNKNOWN;
    out->phase_window = FIELDREG_UNKNOWN;
    out->fast_edge_d1 = FIELDREG_UNKNOWN;
    out->fast_edge_d2 = FIELDREG_UNKNOWN;
    out->relative_only_phase = FIELDREG_UNKNOWN;
    out->relative_only_gauge_source = FIELDREG_RELATIVE_GAUGE_NONE;
    out->bottom_raw_edge_f1 = -1;
    out->bottom_raw_edge_f2 = -1;
    out->bottom_target_f1 = -1;
    out->bottom_target_f2 = -1;
    out->bottom_hold_reason_f1 = FIELDREG_BOTTOM_HOLD_TARGET_LEARNING;
    out->bottom_hold_reason_f2 = FIELDREG_BOTTOM_HOLD_TARGET_LEARNING;
}

fieldreg_config fieldreg_default_config(void)
{
    fieldreg_config config = {
        .switch_margin = 1.5,
        .evidence_model = FIELDREG_EVIDENCE_MOTION_PHASE,
        .confirmation_units = FIELDREG_PHASE_CONFIRM_UNITS,
        .minimum_support_units = FIELDREG_PHASE_CONFIRM_UNITS,
        .maximum_buffered_units = FIELDREG_PHASE_CONFIRM_UNITS + 6,
    };
    return config;
}

size_t fieldreg_state_size(void)
{
    return sizeof(field_registration);
}

size_t fieldreg_config_size(void)
{
    return sizeof(fieldreg_config);
}

size_t fieldreg_decision_size(void)
{
    return sizeof(fieldreg_decision);
}

uint32_t fieldreg_algorithm_version(void)
{
    return FIELDREG_ALGORITHM_VERSION;
}

uint32_t fieldreg_confirmation_units(const field_registration *engine)
{
    return engine ? engine->config.confirmation_units
                  : FIELDREG_PHASE_CONFIRM_UNITS;
}

uint32_t fieldreg_buffer_units(const field_registration *engine)
{
    return engine ? engine->config.maximum_buffered_units
                  : FIELDREG_PHASE_CONFIRM_UNITS + 6;
}

void fieldreg_init(field_registration *engine, const fieldreg_config *config)
{
    fieldreg_config chosen = config ? *config : fieldreg_default_config();
    if (chosen.confirmation_units == 0 ||
        chosen.confirmation_units > FIELDREG_MAX_CONFIRM_UNITS)
        chosen.confirmation_units = FIELDREG_PHASE_CONFIRM_UNITS;
    if (chosen.minimum_support_units == 0 ||
        chosen.minimum_support_units > chosen.confirmation_units)
        chosen.minimum_support_units = chosen.confirmation_units;
    if (chosen.maximum_buffered_units == 0 ||
        chosen.maximum_buffered_units > FIELDREG_MAX_CONFIRM_UNITS)
        chosen.maximum_buffered_units = FIELDREG_PHASE_CONFIRM_UNITS + 6;
    memset(engine, 0, sizeof(*engine));
    engine->config = chosen;
}

void fieldreg_begin_segment(field_registration *engine)
{
    fieldreg_config config = engine->config;
    fieldreg_init(engine, &config);
}

void fieldreg_discontinuity(field_registration *engine)
{
    engine->pending_valid = false;
    engine->pending_count = 0;
    engine->pending_age = 0;
    engine->trajectory_age = 0;
    engine->previous_valid[0] = false;
    engine->previous_valid[1] = false;
    engine->previous_phase_valid = false;
    engine->previous_edge_valid = false;
    engine->motion_anchor_valid = false;
    engine->relative_only_active = false;
    engine->relative_gauge_unknown_active = false;
    engine->bottom_last_raw_valid[0] = false;
    engine->bottom_last_raw_valid[1] = false;
}

static void extract_luma(field_registration *engine, const uint8_t *unit)
{
    const uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    for (int line = 0; line < FIELDREG_RASTER_LINES; ++line) {
        const uint8_t *src = raster + (size_t)line * FIELDREG_BYTES_PER_LINE + 1;
        for (int x = 0; x < FIELDREG_X_SAMPLES; ++x) {
            size_t base = (size_t)x * 8;
            unsigned sum = src[base] + src[base + 2] + src[base + 4] +
                           src[base + 6];
            engine->luma[line][x] = (uint8_t)((sum + 2) / 4);
        }
    }
}

static void line_stats(const uint8_t *unit, int line, double *mean,
                       double *sigma, bool *hard)
{
    const uint8_t *src = unit + FIELDREG_HEADER_BYTES +
                         (size_t)line * FIELDREG_BYTES_PER_LINE;
    uint64_t sum = 0;
    uint64_t square_sum = 0;
    bool is_hard = true;
    for (int pixel = 0; pixel < 720; ++pixel) {
        uint8_t chroma = src[pixel * 2];
        uint8_t luma = src[pixel * 2 + 1];
        sum += luma;
        square_sum += (uint64_t)luma * luma;
        is_hard = is_hard && luma == 16 && chroma == 128;
    }
    *mean = sum / 720.0;
    double variance = square_sum / 720.0 - *mean * *mean;
    *sigma = sqrt(variance > 0.0 ? variance : 0.0);
    *hard = is_hard;
}

static int fiducial(const bool content[FIELDREG_RASTER_LINES], int lo, int hi)
{
    int first = lo > 4 ? lo : 4;
    int after = hi < FIELDREG_RASTER_LINES - 1 ? hi : FIELDREG_RASTER_LINES - 1;
    for (int line = first; line < after; ++line) {
        bool prior = false;
        for (int lookback = line - 4; lookback < line; ++lookback)
            prior = prior || content[lookback];
        if (content[line] && content[line + 1] && !prior)
            return line + 1;
    }
    return -1;
}

static bool transport_geometry(const uint8_t *unit, int *observed_f1,
                               int *observed_f2, bool hard[FIELDREG_RASTER_LINES],
                               double mean[FIELDREG_RASTER_LINES],
                               double sigma[FIELDREG_RASTER_LINES])
{
    bool content[FIELDREG_RASTER_LINES];
    for (int line = 0; line < FIELDREG_RASTER_LINES; ++line) {
        line_stats(unit, line, &mean[line], &sigma[line], &hard[line]);
        bool blank = mean[line] < 8.0 && sigma[line] < 8.0;
        content[line] = !(hard[line] || blank);
    }
    bool hard_ok = true;
    for (int line = 0; line < 7; ++line)
        hard_ok = hard_ok && hard[line];
    for (int line = 261; line < 270; ++line)
        hard_ok = hard_ok && hard[line];
    for (int line = 523; line < 525; ++line)
        hard_ok = hard_ok && hard[line];
    *observed_f1 = fiducial(content, 0, 48);
    *observed_f2 = fiducial(content, 250, 320);
    /* Hard padding is transport truth. VBI/content fiducials are optional
     * source evidence and must not turn a flat but byte-complete field into a
     * transport discontinuity. */
    return hard_ok;
}

static bool picture_signal(bool hard, double mean, double sigma)
{
    return !hard && (sigma > 5.0 || mean > 24.0);
}

static int picture_top(const bool hard[FIELDREG_RASTER_LINES],
                      const double mean[FIELDREG_RASTER_LINES],
                      const double sigma[FIELDREG_RASTER_LINES],
                      int start, int stop)
{
    bool picture[FIELDREG_RASTER_LINES];
    for (int line = 0; line < FIELDREG_RASTER_LINES; ++line)
        picture[line] = picture_signal(hard[line], mean[line], sigma[line]);
    int after = stop < FIELDREG_RASTER_LINES - 2 ? stop : FIELDREG_RASTER_LINES - 2;
    for (int line = start + 1; line < after; ++line) {
        if (picture[line] && picture[line + 1] && picture[line + 2])
            return line;
    }
    return -1;
}

static int picture_bottom(const bool hard[FIELDREG_RASTER_LINES],
                         const double mean[FIELDREG_RASTER_LINES],
                         const double sigma[FIELDREG_RASTER_LINES],
                         int start, int stop)
{
    bool picture[FIELDREG_RASTER_LINES];
    for (int line = 0; line < FIELDREG_RASTER_LINES; ++line)
        picture[line] = picture_signal(hard[line], mean[line], sigma[line]);
    int last = stop < FIELDREG_RASTER_LINES ? stop - 1 : FIELDREG_RASTER_LINES - 1;
    for (int line = last; line >= start + 2; --line) {
        if (picture[line] && picture[line - 1] && picture[line - 2])
            return line;
    }
    return -1;
}

typedef struct bottom_observation {
    int edge;
    uint8_t blanking_level;
    uint8_t black_threshold;
    bool program_extent;
    bool noisy;
} bottom_observation;

static uint8_t histogram_quantile(const uint16_t histogram[256], unsigned count,
                                  unsigned numerator, unsigned denominator)
{
    unsigned rank = count == 0 ? 0 : ((count - 1) * numerator) / denominator;
    unsigned seen = 0;
    for (unsigned value = 0; value < 256; ++value) {
        seen += histogram[value];
        if (seen > rank)
            return (uint8_t)value;
    }
    return 255;
}

/* Measure the lower program boundary without assuming that program black is
 * code 16. The black reference comes from the field's four source-carried
 * near-blank rows; hard padding is deliberately outside this estimator. */
static bottom_observation measure_bottom_edge(const field_registration *engine,
                                              int field)
{
    int scan_first = field == 0 ? FIELDREG_FIELD1_START : FIELDREG_FIELD2_START;
    int scan_last = field == 0 ? 260 : 522;
    int blank_first = field == 0 ? 257 : 519;
    uint16_t histogram[256] = {0};
    unsigned blank_count = 0;
    for (int line = blank_first; line <= scan_last; ++line) {
        for (int x = BOTTOM_X_FIRST; x < BOTTOM_X_AFTER; ++x) {
            ++histogram[engine->luma[line][x]];
            ++blank_count;
        }
    }
    uint8_t blanking = histogram_quantile(histogram, blank_count, 1, 4);
    unsigned threshold = (unsigned)blanking + BOTTOM_BLACK_MARGIN;
    if (threshold > 255)
        threshold = 255;

    uint8_t tile_min[BOTTOM_TILE_COUNT];
    uint8_t tile_max[BOTTOM_TILE_COUNT];
    memset(tile_min, 255, sizeof(tile_min));
    memset(tile_max, 0, sizeof(tile_max));
    uint64_t horizontal_energy = 0;
    uint64_t horizontal_samples = 0;
    for (int line = scan_first; line <= scan_last; ++line) {
        uint8_t prior = engine->luma[line][BOTTOM_X_FIRST];
        for (int x = BOTTOM_X_FIRST; x < BOTTOM_X_AFTER; ++x) {
            uint8_t value = engine->luma[line][x];
            int tile_y = (line - scan_first) * BOTTOM_TILE_ROWS /
                         (scan_last - scan_first + 1);
            int tile_x = (x - BOTTOM_X_FIRST) * BOTTOM_TILE_COLUMNS /
                         (BOTTOM_X_AFTER - BOTTOM_X_FIRST);
            int tile = tile_y * BOTTOM_TILE_COLUMNS + tile_x;
            if (value < tile_min[tile])
                tile_min[tile] = value;
            if (value > tile_max[tile])
                tile_max[tile] = value;
            if (x != BOTTOM_X_FIRST) {
                horizontal_energy += value > prior ? value - prior
                                                   : prior - value;
                ++horizontal_samples;
            }
            prior = value;
        }
    }
    unsigned active_tiles = 0;
    for (int tile = 0; tile < BOTTOM_TILE_COUNT; ++tile)
        active_tiles +=
            (unsigned)(tile_max[tile] - tile_min[tile] >= BOTTOM_TILE_RANGE);

    int edge = -1;
    unsigned samples = BOTTOM_X_AFTER - BOTTOM_X_FIRST;
    unsigned black_required =
        (samples * BOTTOM_BLACK_NUMERATOR + BOTTOM_BLACK_DENOMINATOR - 1) /
        BOTTOM_BLACK_DENOMINATOR;
    for (int line = scan_last; line >= scan_first; --line) {
        unsigned black = 0;
        for (int x = BOTTOM_X_FIRST; x < BOTTOM_X_AFTER; ++x)
            black += engine->luma[line][x] <= threshold;
        if (black < black_required) {
            edge = line;
            break;
        }
    }

    bottom_observation result = {
        .edge = edge,
        .blanking_level = blanking,
        .black_threshold = (uint8_t)threshold,
        .program_extent = active_tiles >= BOTTOM_MIN_ACTIVE_TILES,
        .noisy = horizontal_samples != 0 &&
                 horizontal_energy / horizontal_samples > BOTTOM_NOISE_LIMIT,
    };
    return result;
}

static int median_four(const int16_t values[4])
{
    int sorted[4] = {values[0], values[1], values[2], values[3]};
    for (int i = 1; i < 4; ++i) {
        int value = sorted[i];
        int j = i;
        while (j > 0 && sorted[j - 1] > value) {
            sorted[j] = sorted[j - 1];
            --j;
        }
        sorted[j] = value;
    }
    return (sorted[1] + sorted[2] + 1) / 2;
}

static bool apply_bottom_field(field_registration *engine, int field,
                               bottom_observation observation,
                               bool transport_ok,
                               bool scene_cut,
                               int temporal_best,
                               double temporal_margin,
                               fieldreg_bottom_hold_reason *reason)
{
    int minimum = FIELDREG_MIN_OFFSET;
    int maximum = field == 0 ? FIELDREG_FIELD1_MAX_OFFSET
                             : FIELDREG_FIELD2_MAX_OFFSET;
    *reason = FIELDREG_BOTTOM_HOLD_NONE;
    if (!transport_ok) {
        engine->bottom_reacquire_count[field] = 0;
        engine->bottom_reacquire_armed[field] = false;
        *reason = FIELDREG_BOTTOM_HOLD_TRANSPORT;
        return false;
    }
    if (!observation.program_extent || observation.edge < 0) {
        engine->bottom_reacquire_count[field] = 0;
        engine->bottom_reacquire_armed[field] =
            engine->bottom_target_valid[field];
        if (!engine->bottom_target_valid[field])
            engine->bottom_target_sample_count[field] = 0;
        *reason = FIELDREG_BOTTOM_HOLD_FLAT_OR_DARK;
        return false;
    }
    if (observation.noisy) {
        engine->bottom_reacquire_count[field] = 0;
        engine->bottom_reacquire_armed[field] =
            engine->bottom_target_valid[field];
        if (!engine->bottom_target_valid[field])
            engine->bottom_target_sample_count[field] = 0;
        *reason = FIELDREG_BOTTOM_HOLD_NOISY;
        return false;
    }
    if (scene_cut && !engine->bottom_target_valid[field]) {
        engine->bottom_reacquire_count[field] = 0;
        engine->bottom_reacquire_armed[field] = false;
        engine->bottom_target_sample_count[field] = 0;
        *reason = FIELDREG_BOTTOM_HOLD_SCENE_CUT;
        return false;
    }
    if (!engine->bottom_target_valid[field]) {
        int nominal_bottom = field == 0 ? FIELDREG_ACTIVE_BOTTOM_F1
                                        : FIELDREG_ACTIVE_BOTTOM_F2;
        if (observation.edge < nominal_bottom - BOTTOM_MAX_STEP) {
            *reason = FIELDREG_BOTTOM_HOLD_FLAT_OR_DARK;
            return false;
        }
        unsigned count = engine->bottom_target_sample_count[field];
        if (count > 0 &&
            abs(observation.edge -
                engine->bottom_target_samples[field][count - 1]) > 1) {
            count = 0;
            engine->bottom_target_sample_count[field] = 0;
        }
        if (count < BOTTOM_TARGET_SAMPLES) {
            engine->bottom_target_samples[field][count] =
                (int16_t)observation.edge;
            engine->bottom_target_sample_count[field] = (uint8_t)(count + 1);
        }
        engine->bottom_last_raw[field] = (int16_t)observation.edge;
        engine->bottom_last_raw_valid[field] = true;
        if (engine->bottom_target_sample_count[field] < BOTTOM_TARGET_SAMPLES) {
            *reason = FIELDREG_BOTTOM_HOLD_TARGET_LEARNING;
            return false;
        }
        engine->bottom_target[field] =
            (int16_t)median_four(engine->bottom_target_samples[field]);
        engine->bottom_target_valid[field] = true;
    }
    int desired = observation.edge - engine->bottom_target[field];
    /* A dark/cut excursion can leave last_raw at a censored interior line.
     * Returning exactly to the frozen segment target is self-authenticating
     * recovery and must not be rejected forever by the one-unit jump bound. */
    if (desired < minimum || desired > maximum) {
        engine->bottom_reacquire_count[field] = 0;
        *reason = FIELDREG_BOTTOM_HOLD_OUT_OF_RANGE;
        return false;
    }
    bool edge_jump = desired != 0 && engine->bottom_last_raw_valid[field] &&
                     abs(observation.edge - engine->bottom_last_raw[field]) >
                         BOTTOM_MAX_STEP;
    bool reacquired = false;
    if (edge_jump && engine->bottom_reacquire_armed[field]) {
        if (engine->bottom_reacquire_count[field] != 0 &&
            engine->bottom_reacquire_edge[field] == observation.edge) {
            if (engine->bottom_reacquire_count[field] < UINT8_MAX)
                ++engine->bottom_reacquire_count[field];
        } else {
            engine->bottom_reacquire_edge[field] =
                (int16_t)observation.edge;
            engine->bottom_reacquire_count[field] = 1;
        }
        if (engine->bottom_reacquire_count[field] < BOTTOM_REACQUIRE_UNITS) {
            *reason = FIELDREG_BOTTOM_HOLD_EDGE_JUMP;
            return false;
        }
        /* One implausible unit remains a cut/dark-frame guard. Two
         * consecutive measurable units at the same new edge establish a
         * fresh current geometry even when last_raw predates a dark hold. */
        reacquired = true;
    } else if (edge_jump) {
        engine->bottom_reacquire_count[field] = 0;
        *reason = FIELDREG_BOTTOM_HOLD_EDGE_JUMP;
        return false;
    } else {
        engine->bottom_reacquire_count[field] = 0;
    }
    int observed_step = engine->bottom_last_raw_valid[field]
                            ? observation.edge - engine->bottom_last_raw[field]
                            : 0;
    bool temporal_supports_step = engine->bottom_last_raw_valid[field] &&
                                  observed_step != 0 &&
                                  temporal_margin >=
                                      temporal_contradiction_margin &&
                                  temporal_best == observed_step;
    if (!reacquired && desired != 0 && scene_cut &&
        desired != engine->bottom_applied[field] &&
        !temporal_supports_step) {
        *reason = FIELDREG_BOTTOM_HOLD_SCENE_CUT;
        return false;
    }
    if (!reacquired && desired != 0 &&
        engine->bottom_last_raw_valid[field] &&
        observed_step != 0 &&
        temporal_margin >= temporal_contradiction_margin &&
        temporal_best != observed_step) {
        *reason = FIELDREG_BOTTOM_HOLD_TEMPORAL_CONTRADICTION;
        return false;
    }
    engine->bottom_applied[field] = (int8_t)desired;
    engine->bottom_last_raw[field] = (int16_t)observation.edge;
    engine->bottom_last_raw_valid[field] = true;
    engine->bottom_reacquire_count[field] = 0;
    engine->bottom_reacquire_armed[field] = false;
    return true;
}

/* Keep the bottom measurements as the absolute gauge while satisfying an
 * independently earned field-relative phase. There are few legal integer
 * pairs, so an exhaustive fixed-bound search is simpler and deterministic.
 * Distance from the direct-bottom pair is primary; the older evidence pair
 * breaks representation ties (which field to move). */
static bool constrain_bottom_relative(int bottom1, int bottom2,
                                      int preferred1, int preferred2,
                                      int relative, int *result1,
                                      int *result2)
{
    bool found = false;
    int best_bottom_cost = INT_MAX;
    int best_preferred_cost = INT_MAX;
    int best_magnitude = INT_MAX;
    for (int d1 = FIELDREG_MIN_OFFSET;
         d1 <= FIELDREG_FIELD1_MAX_OFFSET; ++d1) {
        int d2 = d1 + relative;
        if (d2 < FIELDREG_MIN_OFFSET || d2 > FIELDREG_FIELD2_MAX_OFFSET)
            continue;
        int bottom_cost = abs(d1 - bottom1) + abs(d2 - bottom2);
        int preferred_cost =
            abs(d1 - preferred1) + abs(d2 - preferred2);
        int magnitude = abs(d1) + abs(d2);
        if (!found || bottom_cost < best_bottom_cost ||
            (bottom_cost == best_bottom_cost &&
             preferred_cost < best_preferred_cost) ||
            (bottom_cost == best_bottom_cost &&
             preferred_cost == best_preferred_cost &&
             magnitude < best_magnitude)) {
            found = true;
            best_bottom_cost = bottom_cost;
            best_preferred_cost = preferred_cost;
            best_magnitude = magnitude;
            *result1 = d1;
            *result2 = d2;
        }
    }
    return found;
}

static bool spatial_picture_signal(const field_registration *engine, const bool *hard,
                                   int line, int x_start, int x_stop)
{
    if (hard[line])
        return false;
    double sum = 0.0;
    double square_sum = 0.0;
    for (int x = x_start; x < x_stop; ++x) {
        double value = engine->luma[line][x];
        sum += value;
        square_sum += value * value;
    }
    double mean = sum / (x_stop - x_start);
    double variance = square_sum / (x_stop - x_start) - mean * mean;
    double sigma = sqrt(variance > 0.0 ? variance : 0.0);
    return sigma > 5.0 || mean > 24.0;
}

static int spatial_picture_top(const field_registration *engine, const bool *hard,
                               int x_start, int x_stop, int start, int stop)
{
    for (int line = start + 1; line < stop - 2; ++line) {
        if (spatial_picture_signal(engine, hard, line, x_start, x_stop) &&
            spatial_picture_signal(engine, hard, line + 1, x_start, x_stop) &&
            spatial_picture_signal(engine, hard, line + 2, x_start, x_stop))
            return line;
    }
    return -1;
}

static int spatial_picture_bottom(const field_registration *engine, const bool *hard,
                                  int x_start, int x_stop, int start, int stop)
{
    for (int line = stop - 1; line >= start + 2; --line) {
        if (spatial_picture_signal(engine, hard, line, x_start, x_stop) &&
            spatial_picture_signal(engine, hard, line - 1, x_start, x_stop) &&
            spatial_picture_signal(engine, hard, line - 2, x_start, x_stop))
            return line;
    }
    return -1;
}

static double runner_up_margin(const double values[13])
{
    double best = INFINITY;
    double runner_up = INFINITY;
    for (int i = 0; i < 13; ++i) {
        double value = values[i];
        if (!isfinite(value))
            continue;
        if (value < best) {
            runner_up = best;
            best = value;
        } else if (value < runner_up) {
            runner_up = value;
        }
    }
    return isfinite(runner_up) ? runner_up - best : 0.0;
}

static int interfield_registration_band(const field_registration *engine, int x_start,
                                        int x_stop, double *margin)
{
    double scores[13];
    for (int relative = FIELDREG_MIN_OFFSET;
         relative <= FIELDREG_MAX_OFFSET; ++relative) {
        int second_start = FIELDREG_FIELD2_START + relative;
        if (second_start < 0 ||
            second_start + FIELDREG_FIELD_LINES > FIELDREG_RASTER_LINES) {
            scores[relative - FIELDREG_MIN_OFFSET] = INFINITY;
            continue;
        }
        double sum = 0.0;
        uint64_t count = 0;
        /* Curvature over the 480-line weave after excluding 25 lines/end. */
        for (int woven_line = REGISTRATION_VBI_MARGIN + 1;
             woven_line < FIELDREG_FIELD_LINES * 2 - REGISTRATION_VBI_MARGIN - 1;
             ++woven_line) {
            int parity0 = (woven_line - 1) & 1;
            int parity1 = woven_line & 1;
            int parity2 = (woven_line + 1) & 1;
            int row0 = (woven_line - 1) / 2;
            int row1 = woven_line / 2;
            int row2 = (woven_line + 1) / 2;
            int base0 = parity0 ? second_start : FIELDREG_FIELD1_START;
            int base1 = parity1 ? second_start : FIELDREG_FIELD1_START;
            int base2 = parity2 ? second_start : FIELDREG_FIELD1_START;
            for (int x = x_start; x < x_stop; ++x) {
                int a = engine->luma[base0 + row0][x];
                int b = engine->luma[base1 + row1][x];
                int c = engine->luma[base2 + row2][x];
                int curvature = 2 * b - a - c;
                sum += curvature < 0 ? -curvature : curvature;
                ++count;
            }
        }
        scores[relative - FIELDREG_MIN_OFFSET] = sum / (double)count;
    }
    int best_index = 0;
    for (int i = 1; i < 13; ++i) {
        if (scores[i] < scores[best_index])
            best_index = i;
    }
    *margin = runner_up_margin(scores);
    return best_index + FIELDREG_MIN_OFFSET;
}

static int interfield_registration(const field_registration *engine, double *margin)
{
    return interfield_registration_band(engine, 0, FIELDREG_X_SAMPLES,
                                        margin);
}

static double histogram_median(const uint16_t histogram[256], int count)
{
    int lower_rank = (count - 1) / 2;
    int upper_rank = count / 2;
    int seen = 0;
    int lower = 0;
    int upper = 0;
    bool lower_found = false;
    for (int value = 0; value < 256; ++value) {
        int next = seen + histogram[value];
        if (!lower_found && lower_rank < next) {
            lower = value;
            lower_found = true;
        }
        if (upper_rank < next) {
            upper = value;
            break;
        }
        seen = next;
    }
    return (lower + upper) * 0.5;
}

static void temporal_costs_band(const field_registration *engine, int parity, int start,
                                int x_start, int x_stop, double costs[13])
{
    if (!engine->previous_valid[parity]) {
        for (int i = 0; i < 13; ++i)
            costs[i] = 0.0;
        return;
    }
    for (int delta = FIELDREG_MIN_OFFSET; delta <= FIELDREG_MAX_OFFSET; ++delta) {
        uint16_t histogram[256] = {0};
        for (int row = 16; row < FIELDREG_FIELD_LINES - 16; ++row) {
            uint64_t sum = 0;
            for (int x = x_start; x < x_stop; ++x) {
                int difference = (int)engine->luma[start + delta + row][x] -
                                 (int)engine->previous[parity][row][x];
                sum += (uint64_t)(difference < 0 ? -difference : difference);
            }
            unsigned average = (unsigned)((sum + (uint64_t)(x_stop - x_start) / 2) /
                                          (uint64_t)(x_stop - x_start));
            if (average > 255)
                average = 255;
            ++histogram[average];
        }
        costs[delta - FIELDREG_MIN_OFFSET] =
            histogram_median(histogram, FIELDREG_FIELD_LINES - 32);
    }
}

static void temporal_costs(const field_registration *engine, int parity, int start,
                           double costs[13])
{
    temporal_costs_band(engine, parity, start, 0, FIELDREG_X_SAMPLES, costs);
}

static int best_cost_index(const double costs[13], double *cost)
{
    int best = 0;
    for (int i = 1; i < 13; ++i) {
        if (costs[i] < costs[best])
            best = i;
    }
    *cost = costs[best];
    return best + FIELDREG_MIN_OFFSET;
}

static double field_luma_mean(const field_registration *engine, int parity, int start,
                              bool previous)
{
    uint64_t sum = 0;
    size_t count = 0;
    /* Stay well inside active picture; VBI and head-switch edges are geometry
     * evidence, not scene-luminance evidence. */
    for (int row = 16; row < FIELDREG_FIELD_LINES - 16; ++row) {
        const uint8_t *samples = previous ? engine->previous[parity][row]
                                          : engine->luma[start + row];
        for (int x = 0; x < FIELDREG_X_SAMPLES; ++x) {
            sum += samples[x];
            ++count;
        }
    }
    return (double)sum / (double)count;
}

enum {
    RELATIVE_LP_COLUMNS = FIELDREG_X_SAMPLES - 1,
    RELATIVE_FIRST_ROW = 28,
    RELATIVE_LAST_ROW = FIELDREG_FIELD_LINES - 28,
    RELATIVE_TEMPORAL_MAX = 18,
};

typedef struct relative_only_evidence {
    bool valid;
    int8_t phase;
    double best_energy;
    double runner_energy;
    double prior_energy;
    double margin;
    double ratio;
    uint16_t static_columns;
    uint16_t persistent_columns;
} relative_only_evidence;

static unsigned lowpass8_current(const field_registration *engine, int line,
                                 int x)
{
    return ((unsigned)engine->luma[line][x] +
            (unsigned)engine->luma[line][x + 1] + 1u) /
           2u;
}

static unsigned lowpass8_previous(const field_registration *engine, int parity,
                                  int row, int x)
{
    return ((unsigned)engine->previous[parity][row][x] +
            (unsigned)engine->previous[parity][row][x + 1] + 1u) /
           2u;
}

static unsigned histogram_midpoint_u16(const uint16_t *histogram, int slots,
                                       unsigned count)
{
    if (count == 0)
        return 0;
    unsigned lower_rank = (count - 1) / 2;
    unsigned upper_rank = count / 2;
    unsigned seen = 0;
    unsigned lower = 0;
    bool lower_found = false;
    for (int value = 0; value < slots; ++value) {
        unsigned next = seen + histogram[value];
        if (!lower_found && lower_rank < next) {
            lower = (unsigned)value;
            lower_found = true;
        }
        if (upper_rank < next)
            return (lower + (unsigned)value) / 2u;
        seen = next;
    }
    return lower;
}

/*
 * Measure a deliberately narrow authority class: broad columns whose current
 * picture body is static against both previous same-parity fields, followed by
 * a persistent, noise-tolerant inter-field curvature minimum.  The input luma
 * samples already average four source pixels; averaging adjacent samples is
 * the specified eight-pixel horizontal low-pass.  No input-dependent storage
 * or allocation is used.
 */
static relative_only_evidence static_relative_evidence(
    const field_registration *engine, bool scene_cut, int prior_relative)
{
    relative_only_evidence out;
    memset(&out, 0, sizeof(out));
    out.phase = FIELDREG_UNKNOWN;
    out.prior_energy = INFINITY;
    if (scene_cut || !engine->previous_valid[0] ||
        !engine->previous_valid[1])
        return out;

    uint8_t temporal_cost[RELATIVE_LP_COLUMNS];
    uint8_t detail[RELATIVE_LP_COLUMNS];
    uint16_t temporal_histogram[256] = {0};
    for (int x = 0; x < RELATIVE_LP_COLUMNS; ++x) {
        uint64_t temporal_sum = 0;
        uint64_t detail_sum = 0;
        unsigned count = 0;
        for (int row = RELATIVE_FIRST_ROW; row < RELATIVE_LAST_ROW; ++row) {
            /* Static means static in the transport coordinates, not merely
             * alignable by a vertical motion search.  Motion compensation here
             * admits scrolling/source motion and turns it into a false gauge. */
            unsigned current1 = lowpass8_current(
                engine, FIELDREG_FIELD1_START + row, x);
            unsigned current2 = lowpass8_current(
                engine, FIELDREG_FIELD2_START + row, x);
            unsigned previous1 = lowpass8_previous(engine, 0, row, x);
            unsigned previous2 = lowpass8_previous(engine, 1, row, x);
            temporal_sum += current1 > previous1 ? current1 - previous1
                                                 : previous1 - current1;
            temporal_sum += current2 > previous2 ? current2 - previous2
                                                 : previous2 - current2;
            if (row + 1 < RELATIVE_LAST_ROW) {
                unsigned next1 = lowpass8_current(
                    engine, FIELDREG_FIELD1_START + row + 1, x);
                unsigned next2 = lowpass8_current(
                    engine, FIELDREG_FIELD2_START + row + 1, x);
                detail_sum += current1 > next1 ? current1 - next1
                                               : next1 - current1;
                detail_sum += current2 > next2 ? current2 - next2
                                               : next2 - current2;
            }
            count += 2;
        }
        unsigned average = count ? (unsigned)((temporal_sum + count / 2) / count)
                                 : 255u;
        if (average > 255)
            average = 255;
        temporal_cost[x] = (uint8_t)average;
        ++temporal_histogram[average];
        unsigned detail_average =
            count ? (unsigned)((detail_sum + count / 2) / count) : 0u;
        if (detail_average > 255)
            detail_average = 255;
        detail[x] = (uint8_t)detail_average;
    }

    unsigned median_temporal = histogram_midpoint_u16(
        temporal_histogram, 256, RELATIVE_LP_COLUMNS);
    unsigned temporal_limit = median_temporal + 4u;
    if (temporal_limit > RELATIVE_TEMPORAL_MAX)
        temporal_limit = RELATIVE_TEMPORAL_MAX;
    bool static_column[RELATIVE_LP_COLUMNS];
    unsigned run = 0;
    unsigned longest = 0;
    for (int x = 0; x < RELATIVE_LP_COLUMNS; ++x) {
        static_column[x] = temporal_cost[x] <= temporal_limit && detail[x] >= 2;
        if (static_column[x]) {
            ++out.static_columns;
            ++run;
            if (run > longest)
                longest = run;
        } else {
            run = 0;
        }
    }
    out.persistent_columns = longest > UINT16_MAX ? UINT16_MAX
                                                   : (uint16_t)longest;
    if (out.static_columns < FIELDREG_RELATIVE_STATIC_RUN ||
        out.persistent_columns < FIELDREG_RELATIVE_STATIC_RUN)
        return out;

    double scores[FIELDREG_RELATIVE_SEARCH_MAX -
                  FIELDREG_RELATIVE_SEARCH_MIN + 1];
    enum { CURVATURE_SLOTS = 512 };
    for (int relative = FIELDREG_RELATIVE_SEARCH_MIN;
         relative <= FIELDREG_RELATIVE_SEARCH_MAX; ++relative) {
        uint16_t column_histogram[CURVATURE_SLOTS] = {0};
        unsigned columns = 0;
        int second_start = FIELDREG_FIELD2_START + relative;
        for (int x = 0; x < RELATIVE_LP_COLUMNS; ++x) {
            if (!static_column[x])
                continue;
            uint64_t sum = 0;
            unsigned samples = 0;
            for (int woven = REGISTRATION_VBI_MARGIN + 1;
                 woven < FIELDREG_FIELD_LINES * 2 - REGISTRATION_VBI_MARGIN - 1;
                 ++woven) {
                int parity0 = (woven - 1) & 1;
                int parity1 = woven & 1;
                int parity2 = (woven + 1) & 1;
                int row0 = (woven - 1) / 2;
                int row1 = woven / 2;
                int row2 = (woven + 1) / 2;
                int base0 = parity0 ? second_start : FIELDREG_FIELD1_START;
                int base1 = parity1 ? second_start : FIELDREG_FIELD1_START;
                int base2 = parity2 ? second_start : FIELDREG_FIELD1_START;
                int a = (int)lowpass8_current(engine, base0 + row0, x);
                int b = (int)lowpass8_current(engine, base1 + row1, x);
                int c = (int)lowpass8_current(engine, base2 + row2, x);
                int curvature = 2 * b - a - c;
                sum += (uint64_t)(curvature < 0 ? -curvature : curvature);
                ++samples;
            }
            unsigned average = samples ? (unsigned)((sum + samples / 2) / samples)
                                       : CURVATURE_SLOTS - 1;
            if (average >= CURVATURE_SLOTS)
                average = CURVATURE_SLOTS - 1;
            ++column_histogram[average];
            ++columns;
        }
        scores[relative - FIELDREG_RELATIVE_SEARCH_MIN] =
            (double)histogram_midpoint_u16(column_histogram, CURVATURE_SLOTS,
                                           columns);
    }

    int best_index = 0;
    int runner_index = 1;
    if (scores[runner_index] < scores[best_index]) {
        int swap = best_index;
        best_index = runner_index;
        runner_index = swap;
    }
    int score_count = FIELDREG_RELATIVE_SEARCH_MAX -
                      FIELDREG_RELATIVE_SEARCH_MIN + 1;
    for (int i = 2; i < score_count; ++i) {
        if (scores[i] < scores[best_index]) {
            runner_index = best_index;
            best_index = i;
        } else if (scores[i] < scores[runner_index]) {
            runner_index = i;
        }
    }
    out.phase = (int8_t)(best_index + FIELDREG_RELATIVE_SEARCH_MIN);
    out.best_energy = scores[best_index];
    out.runner_energy = scores[runner_index];
    out.margin = out.runner_energy - out.best_energy;
    out.ratio = out.runner_energy > 0.0
                    ? out.best_energy / out.runner_energy
                    : 1.0;
    if (prior_relative >= FIELDREG_RELATIVE_SEARCH_MIN &&
        prior_relative <= FIELDREG_RELATIVE_SEARCH_MAX)
        out.prior_energy =
            scores[prior_relative - FIELDREG_RELATIVE_SEARCH_MIN];

    /* Boundary minima are censored. A useful vote must be both absolutely
     * separated and materially better than its runner-up. */
    out.valid = out.phase > FIELDREG_RELATIVE_SEARCH_MIN &&
                out.phase < FIELDREG_RELATIVE_SEARCH_MAX &&
                out.margin >= 1.0 && out.ratio <= 0.85;
    return out;
}

static bool relative_pair_in_range(int d1, int d2)
{
    return d1 >= FIELDREG_MIN_OFFSET &&
           d1 <= FIELDREG_FIELD1_MAX_OFFSET &&
           d2 >= FIELDREG_MIN_OFFSET &&
           d2 <= FIELDREG_FIELD2_MAX_OFFSET;
}

static void choose_relative_gauge(
    const field_registration *engine, int relative, int temporal_best1,
    int temporal_best2, double temporal_margin1, double temporal_margin2,
    int *d1, int *d2, fieldreg_relative_gauge_source *source,
    bool *gauge_unknown)
{
    int prior1 = engine->previous_phase_valid ? engine->previous_phase[0]
                                              : engine->selected[0];
    int prior2 = engine->previous_phase_valid ? engine->previous_phase[1]
                                              : engine->selected[1];
    *d1 = FIELDREG_UNKNOWN;
    *d2 = FIELDREG_UNKNOWN;
    *source = FIELDREG_RELATIVE_GAUGE_NONE;
    *gauge_unknown = false;

    if (prior2 - prior1 == relative && relative_pair_in_range(prior1, prior2)) {
        *d1 = prior1;
        *d2 = prior2;
        *source = FIELDREG_RELATIVE_GAUGE_PRIOR;
        *gauge_unknown = engine->relative_gauge_unknown_active &&
                         engine->relative_gauge_phase[0] == prior1 &&
                         engine->relative_gauge_phase[1] == prior2;
        return;
    }

    bool known1 = temporal_margin1 >= 0.25 &&
                  temporal_best1 > FIELDREG_MIN_OFFSET &&
                  temporal_best1 < FIELDREG_MAX_OFFSET;
    bool known2 = temporal_margin2 >= 0.25 &&
                  temporal_best2 > FIELDREG_MIN_OFFSET &&
                  temporal_best2 < FIELDREG_MAX_OFFSET;
    int relative_delta = relative - (prior2 - prior1);
    int field1_candidate = prior1 - relative_delta;
    int field2_candidate = prior2 + relative_delta;
    bool temporal_field1 =
        known1 && temporal_best1 == -relative_delta &&
        (!known2 || temporal_best2 == 0);
    bool temporal_field2 =
        known2 && temporal_best2 == relative_delta &&
        (!known1 || temporal_best1 == 0);
    if (temporal_field1 && !temporal_field2 &&
        relative_pair_in_range(field1_candidate, prior2)) {
        *d1 = field1_candidate;
        *d2 = prior2;
        *source = known2 ? FIELDREG_RELATIVE_GAUGE_TEMPORAL_BOTH
                         : FIELDREG_RELATIVE_GAUGE_TEMPORAL_F1;
        return;
    }
    if (temporal_field2 && !temporal_field1 &&
        relative_pair_in_range(prior1, field2_candidate)) {
        *d1 = prior1;
        *d2 = field2_candidate;
        *source = known1 ? FIELDREG_RELATIVE_GAUGE_TEMPORAL_BOTH
                         : FIELDREG_RELATIVE_GAUGE_TEMPORAL_F2;
        return;
    }

    int best_cost = INT32_MAX;
    int best_crop = INT32_MAX;
    int best_negative = INT32_MAX;
    for (int candidate1 = FIELDREG_MIN_OFFSET;
         candidate1 <= FIELDREG_FIELD1_MAX_OFFSET; ++candidate1) {
        int candidate2 = candidate1 + relative;
        if (!relative_pair_in_range(candidate1, candidate2))
            continue;
        int cost = abs(candidate1 - prior1) + abs(candidate2 - prior2);
        int crop = abs(candidate1) + abs(candidate2);
        int negative = (candidate1 < 0) + (candidate2 < 0);
        if (crop < best_crop ||
            (crop == best_crop && cost < best_cost) ||
            (crop == best_crop && cost == best_cost && negative < best_negative) ||
            (crop == best_crop && cost == best_cost && negative == best_negative &&
             candidate1 > *d1)) {
            best_cost = cost;
            best_crop = crop;
            best_negative = negative;
            *d1 = candidate1;
            *d2 = candidate2;
        }
    }
    if (*d1 != FIELDREG_UNKNOWN) {
        *source = FIELDREG_RELATIVE_GAUGE_MIN_CROP;
        *gauge_unknown = true;
    }
}

typedef struct phase_evidence {
    int8_t vote[PHASE_BANDS];
    int8_t motion[PHASE_BANDS];
    double margin[PHASE_BANDS];
    int8_t priority_band;
    int8_t consensus;
    uint8_t support;
    bool conflict;
    double confidence;
} phase_evidence;

/*
 * A moving image biases a direct weave search: four raster lines of vertical
 * motion per frame naturally appear as roughly two lines between its fields.
 * Estimate that motion from each field against its previous same-parity field,
 * subtract half of it from the inter-field displacement, and do this in three
 * independent horizontal bands.  This separates registration phase from a
 * scrolling credit/overlay and makes spatially incompatible source phases
 * explicit instead of allowing one narrow asset to poison a global gauge.
 */
static phase_evidence motion_phase_evidence(const field_registration *engine,
                                            bool scene_cut)
{
    phase_evidence out;
    memset(&out, 0, sizeof(out));
    out.consensus = FIELDREG_UNKNOWN;
    out.priority_band = FIELDREG_UNKNOWN;
    out.confidence = INFINITY;
    for (int band = 0; band < PHASE_BANDS; ++band) {
        out.vote[band] = FIELDREG_UNKNOWN;
        out.motion[band] = FIELDREG_UNKNOWN;
        out.margin[band] = 0.0;
        if (scene_cut || !engine->previous_valid[0] ||
            !engine->previous_valid[1])
            continue;
        double first_costs[13];
        double second_costs[13];
        temporal_costs_band(engine, 0, FIELDREG_FIELD1_START,
                            phase_bounds[band][0], phase_bounds[band][1],
                            first_costs);
        temporal_costs_band(engine, 1, FIELDREG_FIELD2_START,
                            phase_bounds[band][0], phase_bounds[band][1],
                            second_costs);
        double first_cost;
        double second_cost;
        int motion1 = best_cost_index(first_costs, &first_cost);
        int motion2 = best_cost_index(second_costs, &second_cost);
        double margin1 = runner_up_margin(first_costs);
        double margin2 = runner_up_margin(second_costs);
        double weave_margin;
        int weave = interfield_registration_band(
            engine, phase_bounds[band][0], phase_bounds[band][1],
            &weave_margin);
        /* A minimum at either search boundary is censored, not measured. */
        if (motion1 == FIELDREG_MIN_OFFSET ||
            motion1 == FIELDREG_MAX_OFFSET ||
            motion2 == FIELDREG_MIN_OFFSET ||
            motion2 == FIELDREG_MAX_OFFSET ||
            margin1 < 0.25 || margin2 < 0.25 || weave_margin < 0.05 ||
            abs(motion1 - motion2) > 1)
            continue;
        int motion_sum = motion1 + motion2;
        if ((motion_sum & 1) != 0)
            continue;
        int motion = motion_sum / 2;
        /* Odd full-frame motion has an irreducible half-line ambiguity. */
        if ((motion & 1) != 0)
            continue;
        int phase = weave - motion / 2;
        if (phase < FIELDREG_MIN_OFFSET || phase > FIELDREG_MAX_OFFSET)
            continue;
        out.vote[band] = (int8_t)phase;
        out.motion[band] = (int8_t)motion;
        out.margin[band] = fmin(weave_margin, fmin(margin1, margin2));
    }

    int valid = 0;
    for (int band = 0; band < PHASE_BANDS; ++band)
        valid += out.vote[band] != FIELDREG_UNKNOWN;
    for (int band = 0; band < PHASE_BANDS; ++band) {
        if (out.vote[band] == FIELDREG_UNKNOWN)
            continue;
        int support = 0;
        double confidence = INFINITY;
        for (int other = 0; other < PHASE_BANDS; ++other) {
            if (out.vote[other] == out.vote[band]) {
                ++support;
                confidence = fmin(confidence, out.margin[other]);
            }
        }
        if (support > out.support) {
            out.support = (uint8_t)support;
            out.consensus = out.vote[band];
            out.confidence = confidence;
        }
    }
    if (out.support < 2) {
        out.consensus = FIELDREG_UNKNOWN;
        out.confidence = 0.0;
    }

    /*
     * When source layers carry incompatible phases, prefer a uniquely moving
     * broad asset over static borders/overlays.  This is deliberately based
     * on coherent vertical translation, not raw temporal energy: VHS dot
     * crawl is energetic but should not look like the same integer motion in
     * both parity histories.  The rolling phase window still supplies the
     * actual hysteresis before this vote can move applied state.
     */
    int moving_band = FIELDREG_UNKNOWN;
    int moving_magnitude = 0;
    int runner_magnitude = 0;
    for (int band = 0; band < PHASE_BANDS; ++band) {
        if (out.vote[band] == FIELDREG_UNKNOWN ||
            out.motion[band] == FIELDREG_UNKNOWN || out.margin[band] < 0.5)
            continue;
        int magnitude = abs(out.motion[band]);
        if (magnitude > moving_magnitude) {
            runner_magnitude = moving_magnitude;
            moving_magnitude = magnitude;
            moving_band = band;
        } else if (magnitude > runner_magnitude) {
            runner_magnitude = magnitude;
        }
    }
    if (moving_band != FIELDREG_UNKNOWN && moving_magnitude >= 2 &&
        moving_magnitude - runner_magnitude >= 2) {
        out.priority_band = (int8_t)moving_band;
        out.consensus = out.vote[moving_band];
        out.support = 1;
        out.confidence = out.margin[moving_band];
    }
    out.conflict = valid >= 2 && out.support < 2;
    return out;
}

static int band_slot(int value)
{
    int slot = value + BAND_BIAS;
    return slot >= 0 && slot < BAND_SLOTS ? slot : -1;
}

static int band_mode(const field_registration *engine, int parity, int edge)
{
    uint32_t best_count = 0;
    uint32_t best_first = UINT32_MAX;
    int best_value = FIELDREG_UNKNOWN;
    for (int slot = 0; slot < BAND_SLOTS; ++slot) {
        uint32_t count = engine->band_counts[parity][edge][slot];
        uint32_t first = engine->band_first_seen[parity][edge][slot];
        if (count > best_count ||
            (count == best_count && count != 0 && first < best_first)) {
            best_count = count;
            best_first = first;
            best_value = slot - BAND_BIAS;
        }
    }
    return best_value;
}

static void add_band(field_registration *engine, int parity, int edge, int value)
{
    int slot = band_slot(value);
    if (slot < 0)
        return;
    if (engine->band_counts[parity][edge][slot] == 0)
        engine->band_first_seen[parity][edge][slot] = ++engine->band_serial;
    ++engine->band_counts[parity][edge][slot];
    ++engine->band_total[parity][edge];
}

static void clear_band_history(field_registration *engine)
{
    memset(engine->band_counts, 0, sizeof(engine->band_counts));
    memset(engine->band_first_seen, 0, sizeof(engine->band_first_seen));
    memset(engine->band_total, 0, sizeof(engine->band_total));
    memset(engine->spatial_edge_counts, 0,
           sizeof(engine->spatial_edge_counts));
    memset(engine->spatial_edge_total, 0,
           sizeof(engine->spatial_edge_total));
    engine->band_serial = 0;
}

static int spatial_edge_mode(const field_registration *engine, int parity, int edge,
                             int band)
{
    uint16_t best = 0;
    int value = FIELDREG_UNKNOWN;
    for (int slot = 0; slot < BAND_SLOTS; ++slot) {
        uint16_t count = engine->spatial_edge_counts[parity][edge][band][slot];
        if (count > best) {
            best = count;
            value = slot - BAND_BIAS;
        }
    }
    return value;
}

static void add_spatial_edge(field_registration *engine, int parity, int edge,
                             int band, int value)
{
    int slot = band_slot(value);
    if (slot < 0)
        return;
    if (engine->spatial_edge_counts[parity][edge][band][slot] != UINT16_MAX)
        ++engine->spatial_edge_counts[parity][edge][band][slot];
    if (engine->spatial_edge_total[parity][edge][band] != UINT16_MAX)
        ++engine->spatial_edge_total[parity][edge][band];
}

static void save_previous(field_registration *engine, int parity, int start)
{
    for (int row = 0; row < FIELDREG_FIELD_LINES; ++row)
        memcpy(engine->previous[parity][row], engine->luma[start + row],
               FIELDREG_X_SAMPLES);
    engine->previous_valid[parity] = true;
}

/* Return an absolute field offset from a top/bottom envelope pair. The first
 * searchable top line is a censored observation: the real edge may be there
 * or above it. In that case the still-visible bottom is the absolute ruler. */
static int envelope_offset(int top, int bottom, int search_start,
                           int nominal_top, int nominal_bottom,
                           int maximum_offset, bool *top_censored)
{
    bool censored = top == search_start + 1;
    if (top_censored)
        *top_censored = censored;
    if (bottom < 0)
        return FIELDREG_UNKNOWN;
    int bottom_d = bottom - nominal_bottom;
    if (bottom_d < FIELDREG_MIN_OFFSET || bottom_d > maximum_offset)
        return FIELDREG_UNKNOWN;
    if (top < 0 || censored)
        return bottom_d;
    int top_d = top - nominal_top;
    return top_d == bottom_d ? bottom_d : FIELDREG_UNKNOWN;
}

bool fieldreg_process(field_registration *engine, const uint8_t *unit,
                       fieldreg_decision *out)
{
    if (!engine || !unit || !out)
        return false;
    unknown_decision(out);
    out->baseline_d1 = engine->selected[0];
    out->baseline_d2 = engine->selected[1];
    out->applied_d1 = engine->selected[0];
    out->applied_d2 = engine->selected[1];
    out->mode = FIELDREG_MODE_INVALID_UNIT;
    if (!unit_header_valid(unit))
        return false;

    extract_luma(engine, unit);
    bottom_observation bottom_observation_f1 = measure_bottom_edge(engine, 0);
    bottom_observation bottom_observation_f2 = measure_bottom_edge(engine, 1);
    bool hard[FIELDREG_RASTER_LINES];
    double mean[FIELDREG_RASTER_LINES];
    double sigma[FIELDREG_RASTER_LINES];
    int observed_f1 = -1;
    int observed_f2 = -1;
    bool transport_ok = transport_geometry(unit, &observed_f1, &observed_f2,
                                           hard, mean, sigma);
    bool content_evidence_available =
        observed_f1 == FIELDREG_FIELD1_START &&
        observed_f2 == FIELDREG_FIELD2_START;
    int top1 = picture_top(hard, mean, sigma, FIELDREG_FIELD1_START,
                           FIELDREG_FIELD1_START + 48);
    int top2 = picture_top(hard, mean, sigma, FIELDREG_FIELD2_START,
                           FIELDREG_FIELD2_START + 48);
    int bottom1 = picture_bottom(hard, mean, sigma, 200, 262);
    int bottom2 = picture_bottom(hard, mean, sigma, 462, 525);
    int spatial_top[2][PHASE_BANDS];
    int spatial_bottom[2][PHASE_BANDS];
    for (int band = 0; band < PHASE_BANDS; ++band) {
        spatial_top[0][band] = spatial_picture_top(
            engine, hard, phase_bounds[band][0], phase_bounds[band][1],
            FIELDREG_FIELD1_START, FIELDREG_FIELD1_START + 48);
        spatial_top[1][band] = spatial_picture_top(
            engine, hard, phase_bounds[band][0], phase_bounds[band][1],
            FIELDREG_FIELD2_START, FIELDREG_FIELD2_START + 48);
        spatial_bottom[0][band] = spatial_picture_bottom(
            engine, hard, phase_bounds[band][0], phase_bounds[band][1],
            200, 262);
        spatial_bottom[1][band] = spatial_picture_bottom(
            engine, hard, phase_bounds[band][0], phase_bounds[band][1],
            462, 525);
    }
    int mode1 = band_mode(engine, 0, 0);
    int mode2 = band_mode(engine, 1, 0);
    int bottom_mode1 = band_mode(engine, 0, 1);
    int bottom_mode2 = band_mode(engine, 1, 1);

    double weave_margin;
    int best_relative = interfield_registration(engine, &weave_margin);
    double temporal1[13];
    double temporal2[13];
    temporal_costs(engine, 0, FIELDREG_FIELD1_START, temporal1);
    temporal_costs(engine, 1, FIELDREG_FIELD2_START, temporal2);
    double temporal_margin1 = runner_up_margin(temporal1);
    double temporal_margin2 = runner_up_margin(temporal2);
    double temporal_best_cost1;
    double temporal_best_cost2;
    int temporal_best1 = best_cost_index(temporal1, &temporal_best_cost1);
    int temporal_best2 = best_cost_index(temporal2, &temporal_best_cost2);
    bool had_temporal = engine->previous_valid[0] && engine->previous_valid[1];
    double luma_step1 = 0.0;
    double luma_step2 = 0.0;
    if (had_temporal) {
        luma_step1 = field_luma_mean(engine, 0, FIELDREG_FIELD1_START, false) -
                     field_luma_mean(engine, 0, FIELDREG_FIELD1_START, true);
        luma_step2 = field_luma_mean(engine, 1, FIELDREG_FIELD2_START, false) -
                     field_luma_mean(engine, 1, FIELDREG_FIELD2_START, true);
    }
    bool global_luma_step = had_temporal && fabs(luma_step1) >= 2.0 &&
                            fabs(luma_step2) >= 2.0 &&
                            ((luma_step1 > 0.0) == (luma_step2 > 0.0));
    double cut_threshold1 = engine->temporal_cost_ema[0] * 1.8 + 2.0;
    double cut_threshold2 = engine->temporal_cost_ema[1] * 1.8 + 2.0;
    bool temporal_discontinuity =
        had_temporal && engine->temporal_cost_ema_valid &&
        temporal_best_cost1 > cut_threshold1 &&
        temporal_best_cost2 > cut_threshold2;
    /* A vertical translation can change the sampled global mean. Once a
     * temporal noise floor exists, luma alone is not a cut: a real cut/fade
     * also collapses displaced same-parity correlation in both fields. */
    bool scene_cut = temporal_discontinuity ||
                     (global_luma_step && !engine->temporal_cost_ema_valid);
    int prior_relative = engine->previous_phase_valid
                             ? engine->previous_phase[1] -
                                   engine->previous_phase[0]
                             : engine->selected[1] - engine->selected[0];
    relative_only_evidence relative_only = static_relative_evidence(
        engine, scene_cut, prior_relative);
    double independent_evidence = fmax(weave_margin,
                                       fmax(temporal_margin1, temporal_margin2));
    bool phase_model =
        engine->config.evidence_model == FIELDREG_EVIDENCE_MOTION_PHASE;
    if (!phase_model &&
        (best_relative == engine->selected_relative ||
         weave_margin >= engine->config.switch_margin))
        engine->selected_relative = (int8_t)best_relative;

    bool dual_edge = engine->config.evidence_model == FIELDREG_EVIDENCE_DUAL_EDGE;
    bool enough_history = engine->band_total[0][0] >= REGISTRATION_WARMUP &&
                          engine->band_total[1][0] >= REGISTRATION_WARMUP &&
                          (!dual_edge ||
                           (engine->band_total[0][1] >= REGISTRATION_WARMUP &&
                            engine->band_total[1][1] >= REGISTRATION_WARMUP));
    double stability1 = mode1 == FIELDREG_UNKNOWN || engine->band_total[0][0] == 0
                            ? 0.0
                            : (double)engine->band_counts[0][0][band_slot(mode1)] /
                                  engine->band_total[0][0];
    double stability2 = mode2 == FIELDREG_UNKNOWN || engine->band_total[1][0] == 0
                            ? 0.0
                            : (double)engine->band_counts[1][0][band_slot(mode2)] /
                                  engine->band_total[1][0];
    double bottom_stability1 =
        bottom_mode1 == FIELDREG_UNKNOWN || engine->band_total[0][1] == 0
            ? 0.0
            : (double)engine->band_counts[0][1][band_slot(bottom_mode1)] /
                  engine->band_total[0][1];
    double bottom_stability2 =
        bottom_mode2 == FIELDREG_UNKNOWN || engine->band_total[1][1] == 0
            ? 0.0
            : (double)engine->band_counts[1][1][band_slot(bottom_mode2)] /
                  engine->band_total[1][1];
    /*
     * These are absolute decoded-raster landmarks, not a mutable content
     * gauge.  Learning the first visible picture edge as zero made a source
     * acquired while displaced permanently invert every later decision.  It
     * also let the selected correction feed back into the learned baseline.
     * The hard-padding transport ruler fixes the coordinate system; both
     * independently measured edges of a field must report the same offset.
     */
    bool top_censored1 = false;
    bool top_censored2 = false;
    bool bottom_censored1 = bottom1 == 260;
    bool bottom_censored2 = bottom2 == 522;
    int band_d1 = envelope_offset(top1, bottom1, FIELDREG_FIELD1_START,
                                  FIELDREG_ACTIVE_TOP_F1,
                                  FIELDREG_ACTIVE_BOTTOM_F1,
                                  FIELDREG_FIELD1_MAX_OFFSET,
                                  &top_censored1);
    int band_d2 = envelope_offset(top2, bottom2, FIELDREG_FIELD2_START,
                                  FIELDREG_ACTIVE_TOP_F2,
                                  FIELDREG_ACTIVE_BOTTOM_F2,
                                  FIELDREG_FIELD2_MAX_OFFSET,
                                  &top_censored2);
    bool edge_known1 = band_d1 != FIELDREG_UNKNOWN;
    bool edge_known2 = band_d2 != FIELDREG_UNKNOWN;
    bool edge_agreement1 = edge_known1;
    bool edge_agreement2 = edge_known2;
    bool candidate_in_range1 = edge_agreement1 &&
                               band_d1 >= FIELDREG_MIN_OFFSET &&
                               band_d1 <= FIELDREG_FIELD1_MAX_OFFSET;
    bool candidate_in_range2 = edge_agreement2 &&
                               band_d2 >= FIELDREG_MIN_OFFSET &&
                               band_d2 <= FIELDREG_FIELD2_MAX_OFFSET;
    candidate_in_range1 = candidate_in_range1 && content_evidence_available;
    candidate_in_range2 = candidate_in_range2 && content_evidence_available;
    bool dual_edge_agreement = edge_agreement1 && edge_agreement2;
    int target_d1 = candidate_in_range1 ? band_d1 : engine->selected[0];
    int target_d2 = candidate_in_range2 ? band_d2 : engine->selected[1];
    bool common_mode_ambiguous = candidate_in_range1 && candidate_in_range2 &&
                                 target_d1 != 0 && target_d2 != 0 &&
                                 ((target_d1 > 0) == (target_d2 > 0));
    bool temporal_reliable1 = engine->previous_valid[0] && !scene_cut &&
                              temporal_margin1 >= 0.25;
    bool temporal_reliable2 = engine->previous_valid[1] && !scene_cut &&
                              temporal_margin2 >= 0.25;
    bool changed1 = target_d1 != engine->selected[0];
    bool changed2 = target_d2 != engine->selected[1];
    bool temporal_conflict1 = changed1 && temporal_reliable1 &&
                              temporal_best1 != target_d1;
    bool temporal_conflict2 = changed2 && temporal_reliable2 &&
                              temporal_best2 != target_d2;
    phase_evidence phase = motion_phase_evidence(engine, scene_cut);
    bool phase_heterogeneous = false;
    for (int left = 0; left < PHASE_BANDS; ++left) {
        if (phase.vote[left] == FIELDREG_UNKNOWN)
            continue;
        for (int right = left + 1; right < PHASE_BANDS; ++right) {
            if (phase.vote[right] != FIELDREG_UNKNOWN &&
                phase.vote[right] != phase.vote[left])
                phase_heterogeneous = true;
        }
    }
    int phase_window = transport_ok && !scene_cut
                           ? phase.consensus
                           : FIELDREG_UNKNOWN;
    uint8_t phase_window_margin = phase.support;
    bool absolute_phase_pair =
        band_d1 != FIELDREG_UNKNOWN && band_d2 != FIELDREG_UNKNOWN &&
        band_d1 >= FIELDREG_MIN_OFFSET &&
        band_d1 <= FIELDREG_FIELD1_MAX_OFFSET &&
        band_d2 >= FIELDREG_MIN_OFFSET &&
        band_d2 <= FIELDREG_FIELD2_MAX_OFFSET;

    /* A buffered trajectory does not make a strong observation wait for a
     * one-second plateau. Real TBC registration faults can last one unit.
     * Establish the current unit's absolute candidate from coherent top+bottom
     * geometry in independent horizontal bands, preferring the uniquely
     * moving broad asset when the raster contains two real phases. The
     * same-parity differential veto below decides whether that source-carried
     * candidate is safe to apply to the whole field. */
    int band_pair_d1[PHASE_BANDS];
    int band_pair_d2[PHASE_BANDS];
    for (int band = 0; band < PHASE_BANDS; ++band) {
        band_pair_d1[band] = FIELDREG_UNKNOWN;
        band_pair_d2[band] = FIELDREG_UNKNOWN;
        int candidate1 = envelope_offset(
            spatial_top[0][band], spatial_bottom[0][band],
            FIELDREG_FIELD1_START, FIELDREG_ACTIVE_TOP_F1,
            FIELDREG_ACTIVE_BOTTOM_F1, FIELDREG_FIELD1_MAX_OFFSET, NULL);
        int candidate2 = envelope_offset(
            spatial_top[1][band], spatial_bottom[1][band],
            FIELDREG_FIELD2_START, FIELDREG_ACTIVE_TOP_F2,
            FIELDREG_ACTIVE_BOTTOM_F2, FIELDREG_FIELD2_MAX_OFFSET, NULL);
        if (candidate1 != FIELDREG_UNKNOWN &&
            candidate2 != FIELDREG_UNKNOWN) {
            band_pair_d1[band] = candidate1;
            band_pair_d2[band] = candidate2;
        }
    }
    int motion_delta[2] = {FIELDREG_UNKNOWN, FIELDREG_UNKNOWN};
    int anchor_delta[2] = {FIELDREG_UNKNOWN, FIELDREG_UNKNOWN};
    uint8_t motion_band_support[2] = {0, 0};
    uint8_t anchor_band_support[2] = {0, 0};
    if (engine->previous_edge_valid) {
        const int current_top[2] = {top1, top2};
        const int current_bottom[2] = {bottom1, bottom2};
        for (int field = 0; field < 2; ++field) {
            if (current_top[field] < 0 || current_bottom[field] < 0 ||
                engine->previous_picture_top[field] < 0 ||
                engine->previous_picture_bottom[field] < 0)
                continue;
            int top_delta = current_top[field] -
                            engine->previous_picture_top[field];
            int bottom_delta = current_bottom[field] -
                               engine->previous_picture_bottom[field];
            if (top_delta != bottom_delta ||
                top_delta < FIELDREG_MIN_OFFSET ||
                top_delta > FIELDREG_MAX_OFFSET)
                continue;
            for (int band = 0; band < PHASE_BANDS; ++band) {
                int previous_top = engine->previous_spatial_top[field][band];
                int previous_bottom =
                    engine->previous_spatial_bottom[field][band];
                if (spatial_top[field][band] < 0 ||
                    spatial_bottom[field][band] < 0 || previous_top < 0 ||
                    previous_bottom < 0)
                    continue;
                int band_top_delta =
                    spatial_top[field][band] - previous_top;
                int band_bottom_delta =
                    spatial_bottom[field][band] - previous_bottom;
                if (band_top_delta == top_delta &&
                    band_bottom_delta == top_delta)
                    ++motion_band_support[field];
            }
            if (motion_band_support[field] >= 2)
                motion_delta[field] = top_delta;
        }
    }
    if (engine->motion_anchor_valid) {
        const int current_top[2] = {top1, top2};
        const int current_bottom[2] = {bottom1, bottom2};
        for (int field = 0; field < 2; ++field) {
            if (current_top[field] < 0 || current_bottom[field] < 0 ||
                engine->motion_anchor_picture_top[field] < 0 ||
                engine->motion_anchor_picture_bottom[field] < 0)
                continue;
            int top_delta = current_top[field] -
                            engine->motion_anchor_picture_top[field];
            int bottom_delta = current_bottom[field] -
                               engine->motion_anchor_picture_bottom[field];
            if (top_delta != bottom_delta ||
                top_delta < FIELDREG_MIN_OFFSET ||
                top_delta > FIELDREG_MAX_OFFSET)
                continue;
            for (int band = 0; band < PHASE_BANDS; ++band) {
                int anchor_top =
                    engine->motion_anchor_spatial_top[field][band];
                int anchor_bottom =
                    engine->motion_anchor_spatial_bottom[field][band];
                if (spatial_top[field][band] < 0 ||
                    spatial_bottom[field][band] < 0 || anchor_top < 0 ||
                    anchor_bottom < 0)
                    continue;
                int band_top_delta = spatial_top[field][band] - anchor_top;
                int band_bottom_delta =
                    spatial_bottom[field][band] - anchor_bottom;
                if (band_top_delta == top_delta &&
                    band_bottom_delta == top_delta)
                    ++anchor_band_support[field];
            }
            if (anchor_band_support[field] >= 2)
                anchor_delta[field] = top_delta;
        }
    }
    /* Some real rasters contain two vertical phases: for example a broad
     * program layer whose top and bottom landmarks are not one nominal-height
     * envelope.  Absolute offsets then abstain, but a coherent displacement
     * remains observable.  Full-width top and bottom must move together,
     * independently in at least two broad bands, and the same-parity temporal
     * search must report that exact delta for both fields.  This is the
     * zero-latency FOLLOW path; localized/edge-only chatter cannot enter it. */
    bool global_motion_authority =
        phase_model && transport_ok && content_evidence_available &&
        engine->previous_phase_valid && !scene_cut &&
        motion_delta[0] != FIELDREG_UNKNOWN &&
        motion_delta[1] != FIELDREG_UNKNOWN &&
        anchor_delta[0] != FIELDREG_UNKNOWN &&
        anchor_delta[1] != FIELDREG_UNKNOWN &&
        (motion_delta[0] != 0 || motion_delta[1] != 0) &&
        temporal_margin1 >= 0.25 && temporal_margin2 >= 0.25 &&
        temporal_best1 == motion_delta[0] &&
        temporal_best2 == motion_delta[1];
    int motion_target_d1 = FIELDREG_UNKNOWN;
    int motion_target_d2 = FIELDREG_UNKNOWN;
    if (global_motion_authority) {
        /* The stable raw-edge anchor is the gauge. Do not integrate adjacent
         * deltas: one abstaining reverse sample would otherwise turn bounded
         * 0/1 jitter into an impossible walk toward +/-6. */
        motion_target_d1 =
            engine->motion_anchor_phase[0] + anchor_delta[0];
        motion_target_d2 =
            engine->motion_anchor_phase[1] + anchor_delta[1];
        /* Delta authority tracks bounded field-rate jitter around the last
         * independently established absolute gauge. Larger excursions are
         * content motion or a new absolute plateau and must go through the
         * absolute/relative paths; otherwise scrolling layers can walk the
         * crop to a search boundary. */
        if (abs(motion_target_d1 - engine->baseline[0]) > 1 ||
            abs(motion_target_d2 - engine->baseline[1]) > 1)
            global_motion_authority = false;
        if (motion_target_d1 < FIELDREG_MIN_OFFSET ||
            motion_target_d1 > FIELDREG_FIELD1_MAX_OFFSET ||
            motion_target_d2 < FIELDREG_MIN_OFFSET ||
            motion_target_d2 > FIELDREG_FIELD2_MAX_OFFSET) {
            global_motion_authority = false;
            motion_target_d1 = FIELDREG_UNKNOWN;
            motion_target_d2 = FIELDREG_UNKNOWN;
        }
    }
    int absolute_d1 = FIELDREG_UNKNOWN;
    int absolute_d2 = FIELDREG_UNKNOWN;
    uint8_t frame_support = 0;
    bool frame_motion_priority = false;
    bool frame_conflict = false;
    bool global_envelope_authority = false;
    if (phase.priority_band >= 0 &&
        band_pair_d1[(int)phase.priority_band] != FIELDREG_UNKNOWN) {
        int band = phase.priority_band;
        absolute_d1 = band_pair_d1[band];
        absolute_d2 = band_pair_d2[band];
        frame_support = 1;
        frame_motion_priority = true;
    } else {
        int valid_band_pairs = 0;
        for (int band = 0; band < PHASE_BANDS; ++band) {
            if (band_pair_d1[band] == FIELDREG_UNKNOWN)
                continue;
            ++valid_band_pairs;
            int support = 0;
            for (int other = 0; other < PHASE_BANDS; ++other)
                support += band_pair_d1[other] == band_pair_d1[band] &&
                           band_pair_d2[other] == band_pair_d2[band];
            if (support > frame_support) {
                frame_support = (uint8_t)support;
                absolute_d1 = band_pair_d1[band];
                absolute_d2 = band_pair_d2[band];
            }
        }
        frame_conflict = valid_band_pairs >= 2 && frame_support < 2;
        if (frame_support < 2) {
            bool phase_corroborates_global =
                absolute_phase_pair && phase.support >= 2 &&
                phase.consensus == band_d2 - band_d1;
            bool continues_previous_absolute =
                absolute_phase_pair && engine->previous_phase_valid &&
                band_d1 == engine->previous_phase[0] &&
                band_d2 == engine->previous_phase[1];
            if (absolute_phase_pair &&
                (phase_corroborates_global ||
                 (!frame_conflict && continues_previous_absolute))) {
                absolute_d1 = band_d1;
                absolute_d2 = band_d2;
                frame_support = 1;
            } else {
                absolute_d1 = FIELDREG_UNKNOWN;
                absolute_d2 = FIELDREG_UNKNOWN;
                frame_support = 0;
            }
        }
    }
    /* Authority is by independent evidence, not horizontal-band headcount.
     * When the full-width top+bottom envelope and the motion-compensated
     * inter-field consensus agree, a conflicting two-of-three local-band vote
     * is a secondary-layer observation. Follow the global field geometry at
     * unit rate; transition penalties are not allowed to smooth this case. */
    bool global_relative_authority =
        absolute_phase_pair && phase.support >= 2 && !scene_cut &&
        phase.consensus == band_d2 - band_d1;
    global_envelope_authority = global_relative_authority;
    if (global_relative_authority &&
        (absolute_d1 == FIELDREG_UNKNOWN || absolute_d1 != band_d1 ||
         absolute_d2 != band_d2)) {
        absolute_d1 = band_d1;
        absolute_d2 = band_d2;
        frame_support = phase.support;
        frame_motion_priority = false;
    }
    if (global_motion_authority) {
        absolute_d1 = motion_target_d1;
        absolute_d2 = motion_target_d2;
        uint8_t support0 = motion_band_support[0] < anchor_band_support[0]
                               ? motion_band_support[0]
                               : anchor_band_support[0];
        uint8_t support1 = motion_band_support[1] < anchor_band_support[1]
                               ? motion_band_support[1]
                               : anchor_band_support[1];
        frame_support = support0 < support1 ? support0 : support1;
        frame_motion_priority = false;
        global_envelope_authority = true;
    }
    /* At the last ADC row before hard padding, the lower edge is censored: a
     * source may continue beyond the capturable slot. A visible top may name
     * the offset only when same-parity body motion supplies the same delta.
     * This is deliberately asymmetric with ordinary exact envelopes and is
     * guarded by the stationary-boundary-card golden. */
    int boundary_d1 = top1 >= 0 ? top1 - FIELDREG_ACTIVE_TOP_F1
                                : FIELDREG_UNKNOWN;
    int boundary_prior1 = engine->previous_phase_valid
                              ? engine->previous_phase[0]
                              : engine->selected[0];
    bool boundary_motion1 =
        bottom_censored1 && boundary_d1 > 4 &&
        boundary_d1 <= FIELDREG_FIELD1_MAX_OFFSET &&
        temporal_reliable1 && temporal_best1 == boundary_d1 - boundary_prior1;
    bool boundary_continues1 =
        bottom_censored1 && boundary_d1 == boundary_prior1 &&
        boundary_d1 > 4 && boundary_d1 <= FIELDREG_FIELD1_MAX_OFFSET;
    bool bottom_censored_authority =
        phase_model && content_evidence_available && !scene_cut &&
        band_d2 != FIELDREG_UNKNOWN &&
        (boundary_motion1 || boundary_continues1);
    if (bottom_censored_authority) {
        absolute_d1 = boundary_d1;
        absolute_d2 = band_d2;
        frame_support = 1;
        frame_motion_priority = true;
        global_envelope_authority = true;
    }
    if (!content_evidence_available) {
        absolute_d1 = FIELDREG_UNKNOWN;
        absolute_d2 = FIELDREG_UNKNOWN;
        frame_support = 0;
        global_envelope_authority = false;
    }
    /* Common-mode movement has no relative-phase corroboration. Require both
     * same-parity temporal searches to independently see it. */
    int common_prior_d1 = engine->previous_phase_valid
                              ? engine->previous_phase[0]
                              : engine->selected[0];
    int common_prior_d2 = engine->previous_phase_valid
                              ? engine->previous_phase[1]
                              : engine->selected[1];
    if (absolute_d1 != FIELDREG_UNKNOWN &&
        absolute_d1 - common_prior_d1 == absolute_d2 - common_prior_d2 &&
        (absolute_d1 != common_prior_d1 || absolute_d2 != common_prior_d2) &&
        !(temporal_margin1 >= 0.5 && temporal_margin2 >= 0.5 &&
          temporal_best1 == absolute_d1 - common_prior_d1 &&
          temporal_best2 == absolute_d2 - common_prior_d2)) {
        absolute_d1 = FIELDREG_UNKNOWN;
        absolute_d2 = FIELDREG_UNKNOWN;
        frame_support = 0;
    }

    /*
     * The picture envelope is source-carried.  Even top+bottom agreement can
     * change at a scene boundary or when a local overlay enters/leaves, so it
     * is a candidate absolute phase, not by itself proof that this one field
     * moved. Preserve real one-unit jumps when either two independent bands,
     * motion-compensated relative phase, or same-parity motion corroborates
     * the change. Otherwise abstain for this unit; a persistent candidate may
     * still establish a new baseline through the bounded dwell below and will
     * then be backdated by the caller's raw-unit FIFO.
     */
    int frame_d1 = absolute_d1;
    int frame_d2 = absolute_d2;
    bool geometry_overrides_cut = false;
    if (frame_d1 != FIELDREG_UNKNOWN) {
        int prior_d1 = engine->previous_phase_valid
                           ? engine->previous_phase[0]
                           : engine->selected[0];
        int prior_d2 = engine->previous_phase_valid
                           ? engine->previous_phase[1]
                           : engine->selected[1];
        bool change1 = frame_d1 != prior_d1;
        bool change2 = frame_d2 != prior_d2;
        bool temporal_supports1 =
            !change1 || (temporal_reliable1 &&
                         temporal_best1 == frame_d1 - prior_d1);
        bool temporal_supports2 =
            !change2 || (temporal_reliable2 &&
                         temporal_best2 == frame_d2 - prior_d2);
        bool relative_supports_absolute =
            phase_window != FIELDREG_UNKNOWN && phase.support >= 2 &&
            phase_window == frame_d2 - frame_d1;
        bool independent_spatial_support =
            frame_support >= 2 || frame_motion_priority ||
            (frame_support == 1 && relative_supports_absolute);
        bool temporal_supports_change =
            engine->previous_phase_valid && temporal_supports1 &&
            temporal_supports2;
        bool weak_temporal_geometry_support =
            engine->previous_phase_valid && engine->previous_valid[0] &&
            engine->previous_valid[1] && temporal_margin1 >= 0.05 &&
            temporal_margin2 >= 0.05 &&
            (!change1 || temporal_best1 == frame_d1 - prior_d1) &&
            (!change2 || temporal_best2 == frame_d2 - prior_d2);
        geometry_overrides_cut =
            (change1 || change2) && frame_support >= 2 &&
            (temporal_supports_change || weak_temporal_geometry_support);
        int requested_delta1 = frame_d1 - prior_d1;
        int requested_delta2 = frame_d2 - prior_d2;
        bool temporal_veto_ready1 = engine->previous_valid[0] && !scene_cut &&
                                    temporal_margin1 >=
                                        temporal_contradiction_margin;
        bool temporal_veto_ready2 = engine->previous_valid[1] && !scene_cut &&
                                    temporal_margin2 >=
                                        temporal_contradiction_margin;
        bool relative_change = requested_delta1 != requested_delta2;
        bool temporal_contradicts_change;
        if (relative_change && temporal_veto_ready1 && temporal_veto_ready2) {
            /* Cancel coherent source motion. A field-registration event is
             * the difference between the two same-parity motions, not either
             * field's absolute motion against a moving picture. */
            temporal_contradicts_change =
                temporal_best1 - temporal_best2 !=
                requested_delta1 - requested_delta2;
        } else {
            /* Common-mode registration has no differential signature. When
             * only one temporal field is usable, retain its weaker absolute
             * veto rather than manufacturing evidence for the other field. */
            temporal_contradicts_change =
                (change1 && temporal_veto_ready1 &&
                 temporal_best1 != requested_delta1) ||
                (change2 && temporal_veto_ready2 &&
                 temporal_best2 != requested_delta2);
        }
        if ((change1 || change2) &&
            ((scene_cut && !geometry_overrides_cut) ||
             (temporal_contradicts_change && !global_envelope_authority) ||
             (!independent_spatial_support && !temporal_supports_change))) {
            frame_d1 = FIELDREG_UNKNOWN;
            frame_d2 = FIELDREG_UNKNOWN;
        }
    }
    bool registration_scene_cut = scene_cut && !geometry_overrides_cut;

    bool relative_only_authority = false;
    bool relative_gauge_unknown = false;
    int relative_d1 = FIELDREG_UNKNOWN;
    int relative_d2 = FIELDREG_UNKNOWN;
    fieldreg_relative_gauge_source relative_gauge =
        FIELDREG_RELATIVE_GAUGE_NONE;
    /* Absolute geometry keeps priority. Relative-only authority is admitted
     * only when that path abstains, the raw relative optimum materially
     * contradicts the currently presented phase, and the static/cut/transport
     * gates all pass. */
    if (phase_model && transport_ok && !registration_scene_cut &&
        frame_d1 == FIELDREG_UNKNOWN && !absolute_phase_pair &&
        !bottom_censored_authority && !phase_heterogeneous &&
        relative_only.valid) {
        choose_relative_gauge(
            engine, relative_only.phase, temporal_best1, temporal_best2,
            temporal_margin1, temporal_margin2, &relative_d1, &relative_d2,
            &relative_gauge, &relative_gauge_unknown);
        /* Without a temporal field identity, require unanimous independent
         * broad-band phase. A two-band majority can be a real secondary layer
         * over the main picture (the multiphase golden). */
        if (relative_gauge_unknown &&
            !(phase.support == PHASE_BANDS &&
              phase.consensus == relative_only.phase)) {
            relative_d1 = FIELDREG_UNKNOWN;
            relative_d2 = FIELDREG_UNKNOWN;
            relative_gauge = FIELDREG_RELATIVE_GAUGE_NONE;
            relative_gauge_unknown = false;
        }
        relative_only_authority =
            relative_d1 != FIELDREG_UNKNOWN &&
            (relative_d1 != engine->selected[0] ||
             relative_d2 != engine->selected[1] ||
             !engine->phase_baseline_valid || engine->relative_only_active);
        if (relative_only_authority) {
            frame_d1 = relative_d1;
            frame_d2 = relative_d2;
            frame_support = relative_only.static_columns > UINT8_MAX
                                ? UINT8_MAX
                                : (uint8_t)relative_only.static_columns;
        }
    }

    int phase_target_d1 = FIELDREG_UNKNOWN;
    int phase_target_d2 = FIELDREG_UNKNOWN;
    bool absolute_changes_baseline =
        absolute_d1 != FIELDREG_UNKNOWN &&
        (!engine->phase_baseline_valid || absolute_d1 != engine->selected[0] ||
         absolute_d2 != engine->selected[1]);
    bool absolute_common_mode =
        absolute_d1 != FIELDREG_UNKNOWN && absolute_d1 == absolute_d2;
    bool absolute_relative_corroborated =
        phase_window != FIELDREG_UNKNOWN &&
        phase_window == absolute_d2 - absolute_d1;
    if (absolute_d1 != FIELDREG_UNKNOWN &&
        (!absolute_changes_baseline || absolute_common_mode ||
         absolute_relative_corroborated)) {
        phase_target_d1 = absolute_d1;
        phase_target_d2 = absolute_d2;
    } else if (phase_window != FIELDREG_UNKNOWN && engine->pending_valid &&
               engine->pending[1] - engine->pending[0] == phase_window) {
        /* Absolute edges may abstain inside a candidate run. Relative phase
         * may continue that already-anchored exact pair, but cannot invent a
         * new absolute gauge. */
        phase_target_d1 = engine->pending[0];
        phase_target_d2 = engine->pending[1];
    } else if (phase_window != FIELDREG_UNKNOWN &&
               engine->phase_baseline_valid &&
               engine->selected[1] - engine->selected[0] == phase_window) {
        phase_target_d1 = engine->selected[0];
        phase_target_d2 = engine->selected[1];
    }
    bool phase_pair_valid = phase_target_d1 != FIELDREG_UNKNOWN &&
                            phase_target_d2 != FIELDREG_UNKNOWN;
    out->mode = FIELDREG_MODE_INVALID_UNIT;
    bool phase_changed = false;
    if (phase_model) {
        if (relative_only_authority) {
            /* Relative phase is current-unit authority, not an absolute
             * gauge. Present it now, but never promote it into selected[]:
             * an unrelated following abstention must hold the last absolute
             * lock rather than latch a relative presentation indefinitely. */
            engine->pending_valid = false;
            engine->pending_count = 0;
            engine->pending_age = 0;
            engine->trajectory_age = 0;
            phase_target_d1 = relative_d1;
            phase_target_d2 = relative_d2;
            phase_pair_valid = true;
            engine->relative_gauge_unknown_active = relative_gauge_unknown;
            engine->relative_gauge_phase[0] = (int8_t)relative_d1;
            engine->relative_gauge_phase[1] = (int8_t)relative_d2;
            engine->relative_only_active = true;
        }
        if (global_motion_authority) {
            /* This is a current-unit physical displacement observation, not
             * a plateau hypothesis.  Commit it immediately so an abstaining
             * following unit holds the phase just presented. */
            engine->selected[0] = (int8_t)motion_target_d1;
            engine->selected[1] = (int8_t)motion_target_d2;
            engine->selected_relative =
                (int8_t)(motion_target_d2 - motion_target_d1);
            engine->phase_baseline_valid = true;
            engine->phase_baseline_age = 0;
            engine->pending_valid = false;
            engine->pending_count = 0;
            engine->pending_age = 0;
            engine->trajectory_age = 0;
            phase_target_d1 = motion_target_d1;
            phase_target_d2 = motion_target_d2;
            phase_pair_valid = true;
        }
        bool initial_authoritative_lock =
            !engine->phase_baseline_valid && frame_d1 != FIELDREG_UNKNOWN &&
            (frame_support >= 2 || frame_motion_priority ||
             global_envelope_authority);
        if (initial_authoritative_lock) {
            engine->selected[0] = (int8_t)frame_d1;
            engine->selected[1] = (int8_t)frame_d2;
            engine->baseline[0] = (int8_t)frame_d1;
            engine->baseline[1] = (int8_t)frame_d2;
            engine->selected_relative = (int8_t)(frame_d2 - frame_d1);
            engine->phase_baseline_valid = true;
            engine->phase_baseline_age = 0;
            phase_target_d1 = frame_d1;
            phase_target_d2 = frame_d2;
            phase_pair_valid = true;
            phase_changed = false;
        }
        phase_changed = phase_pair_valid &&
                        (!engine->phase_baseline_valid ||
                         phase_target_d1 != engine->selected[0] ||
                         phase_target_d2 != engine->selected[1]);
        if (relative_only_authority) {
            out->decision_d1 = (int8_t)relative_d1;
            out->decision_d2 = (int8_t)relative_d2;
            out->mode = FIELDREG_MODE_RELATIVE_ONLY;
        } else if (!transport_ok) {
            engine->pending_valid = false;
            engine->pending_count = 0;
            engine->pending_age = 0;
            engine->trajectory_age = 0;
            out->mode = FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI;
        } else if (registration_scene_cut) {
            /* MPEG/new-picture boundaries are deliberately absent evidence:
             * preserve a candidate, but neither support nor contradict it. */
            if (engine->pending_valid) {
                ++engine->pending_age;
                ++engine->trajectory_age;
            }
            out->mode = FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD;
        } else if (!phase_pair_valid && phase_window == FIELDREG_UNKNOWN) {
            if (engine->pending_valid) {
                ++engine->pending_age;
                ++engine->trajectory_age;
            }
            out->mode = FIELDREG_MODE_UNKNOWN_SPATIAL_PHASE;
        } else if (!phase_pair_valid) {
            /* Relative-only evidence has no absolute gauge, but a sustained
             * contradiction is still an unsettled interval. Preserve the
             * committed gauge, age the interval, and abstain; do not invent
             * which field moved. */
            engine->pending_valid = false;
            engine->pending_count = 0;
            ++engine->pending_age;
            ++engine->trajectory_age;
            out->mode = FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE;
        } else if (!phase_changed) {
            engine->pending_valid = false;
            engine->pending_count = 0;
            engine->pending_age = 0;
            engine->trajectory_age = 0;
            out->decision_d1 = engine->selected[0];
            out->decision_d2 = engine->selected[1];
            out->mode = FIELDREG_MODE_STABLE_MOTION_PHASE;
        } else {
            /* A candidate is a contiguous exact (d1,d2) trajectory, not a
             * trailing majority. Contradictory current evidence replaces it
             * immediately, so old votes can never fire after a jump ends. */
            if (engine->pending_valid &&
                engine->pending[0] == phase_target_d1 &&
                engine->pending[1] == phase_target_d2) {
                ++engine->pending_count;
            } else {
                engine->pending[0] = (int8_t)phase_target_d1;
                engine->pending[1] = (int8_t)phase_target_d2;
                engine->pending_valid = true;
                engine->pending_count = 1;
                engine->pending_age = 0;
            }
            ++engine->pending_age;
            ++engine->trajectory_age;
            if (engine->pending_age >= engine->config.confirmation_units &&
                engine->pending_count >= engine->config.minimum_support_units) {
                engine->selected[0] = (int8_t)phase_target_d1;
                engine->selected[1] = (int8_t)phase_target_d2;
                engine->baseline[0] = (int8_t)phase_target_d1;
                engine->baseline[1] = (int8_t)phase_target_d2;
                engine->phase_baseline_valid = true;
                engine->phase_baseline_age = 0;
                engine->selected_relative =
                    (int8_t)(phase_target_d2 - phase_target_d1);
                out->decision_backdate =
                    engine->pending_age < engine->config.maximum_buffered_units
                        ? engine->pending_age
                        : engine->config.maximum_buffered_units;
                clear_band_history(engine);
                engine->pending_valid = false;
                engine->pending_count = 0;
                engine->pending_age = 0;
                engine->trajectory_age = 0;
                out->decision_d1 = engine->selected[0];
                out->decision_d2 = engine->selected[1];
                out->mode = FIELDREG_MODE_CONVERGED_MOTION_PHASE;
            } else {
                out->mode = FIELDREG_MODE_UNKNOWN_PHASE_DWELL;
            }
        }
        if (!relative_only_authority && frame_d1 != FIELDREG_UNKNOWN) {
            engine->relative_only_active = false;
            engine->relative_gauge_unknown_active = false;
        }
        if (engine->trajectory_age >= FIELDREG_TRAJECTORY_STALENESS_UNITS) {
            /* The bounded caller FIFO cannot retain an unfinalized path
             * forever. It flushes each unit at the phase already assigned,
             * logs this reset, and demands a fresh stable lock; the engine
             * never asks the caller to drop, repeat, or retroactively rewrite
             * those units to raw. */
            engine->pending_valid = false;
            engine->pending_count = 0;
            engine->pending_age = 0;
            engine->trajectory_age = 0;
            engine->phase_baseline_valid = false;
            /* Confidence resets; presentation phase does not. Snapping the
             * fallback to raw here creates a visible transition with no
             * current-unit observation. The invalid baseline forces fresh
             * acquisition while selected[] remains the honest last-known
             * phase for intervening abstentions. */
            out->trajectory_reset = true;
            out->decision_d1 = FIELDREG_UNKNOWN;
            out->decision_d2 = FIELDREG_UNKNOWN;
            out->mode = FIELDREG_MODE_UNKNOWN_PHASE_DWELL;
        }
    } else if (scene_cut && !changed1 && !changed2) {
        out->mode = FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD;
    } else if (!transport_ok) {
        out->mode = FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI;
    } else if (!enough_history) {
        out->mode = FIELDREG_MODE_UNKNOWN_WARMUP_HOLD;
    } else if (common_mode_ambiguous) {
        out->mode = FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE;
    } else if (!candidate_in_range1 && !candidate_in_range2) {
        out->mode = (edge_known1 || edge_known2)
                        ? FIELDREG_MODE_UNKNOWN_BAND_DISAGREEMENT
                        : FIELDREG_MODE_UNKNOWN_BAND_LANDMARK;
    } else if (!changed1 && !changed2) {
        engine->pending_valid = false;
        engine->pending_count = 0;
        engine->pending_age = 0;
        out->decision_d1 = engine->selected[0];
        out->decision_d2 = engine->selected[1];
        out->mode = candidate_in_range1 && candidate_in_range2
                        ? FIELDREG_MODE_STABLE
                        : FIELDREG_MODE_UNKNOWN_BAND_DISAGREEMENT;
    } else {
        bool temporal_conflict = temporal_conflict1 || temporal_conflict2;
        /* A coherent top+bottom displacement is the absolute raster vote. */
        int required_dwell = dual_edge ? 1 : temporal_conflict ? 2 : 1;
        if (engine->pending_valid && engine->pending[0] == target_d1 &&
            engine->pending[1] == target_d2 && engine->pending_age <= 2) {
            ++engine->pending_count;
        } else {
            engine->pending[0] = (int8_t)target_d1;
            engine->pending[1] = (int8_t)target_d2;
            engine->pending_valid = true;
            engine->pending_count = 1;
        }
        engine->pending_age = 0;
        if ((int)engine->pending_count >= required_dwell) {
            engine->selected[0] = (int8_t)target_d1;
            engine->selected[1] = (int8_t)target_d2;
            engine->selected_relative = (int8_t)(target_d2 - target_d1);
            engine->pending_valid = false;
            engine->pending_count = 0;
            out->decision_d1 = (int8_t)target_d1;
            out->decision_d2 = (int8_t)target_d2;
            out->mode = FIELDREG_MODE_CONVERGED_RELATIVE_BAND;
        } else {
            out->mode = temporal_conflict
                            ? FIELDREG_MODE_UNKNOWN_EVIDENCE_DISAGREEMENT
                            : FIELDREG_MODE_UNKNOWN_CANDIDATE_DWELL;
        }
    }

    if (phase_model && engine->phase_baseline_valid && !phase_changed &&
        engine->phase_baseline_age != UINT16_MAX)
        ++engine->phase_baseline_age;

    if (phase_model && transport_ok && engine->phase_baseline_valid &&
        engine->phase_baseline_age >= engine->config.confirmation_units) {
        int fast_d[2] = {FIELDREG_UNKNOWN, FIELDREG_UNKNOWN};
        uint8_t fast_support[2] = {0, 0};
        bool fast_conflict = false;
        for (int parity = 0; parity < 2; ++parity) {
            int votes[PHASE_BANDS];
            int valid = 0;
            for (int band = 0; band < PHASE_BANDS; ++band) {
                votes[band] = FIELDREG_UNKNOWN;
                bool history =
                    engine->spatial_edge_total[parity][0][band] >=
                        FAST_EDGE_WARMUP &&
                    engine->spatial_edge_total[parity][1][band] >=
                        FAST_EDGE_WARMUP;
                int top_mode = spatial_edge_mode(engine, parity, 0, band);
                int bottom_mode = spatial_edge_mode(engine, parity, 1, band);
                if (!history || spatial_top[parity][band] < 0 ||
                    spatial_bottom[parity][band] < 0 ||
                    top_mode == FIELDREG_UNKNOWN ||
                    bottom_mode == FIELDREG_UNKNOWN)
                    continue;
                int top_origin = parity == 0 ? FIELDREG_FIELD1_START
                                             : FIELDREG_FIELD2_START;
                int bottom_origin = parity == 0 ? 256 : 518;
                int top_delta = spatial_top[parity][band] - top_origin -
                                top_mode;
                int bottom_delta = spatial_bottom[parity][band] -
                                   bottom_origin - bottom_mode;
                if (top_delta == bottom_delta) {
                    votes[band] = top_delta;
                    ++valid;
                }
            }
            for (int band = 0; band < PHASE_BANDS; ++band) {
                if (votes[band] == FIELDREG_UNKNOWN)
                    continue;
                int support = 0;
                for (int other = 0; other < PHASE_BANDS; ++other)
                    support += votes[other] == votes[band];
                if (support > fast_support[parity]) {
                    fast_support[parity] = (uint8_t)support;
                    fast_d[parity] = votes[band];
                }
            }
            if (fast_support[parity] < 2) {
                fast_d[parity] = FIELDREG_UNKNOWN;
                fast_conflict = fast_conflict || valid >= 2;
            }
        }
        int fast_d1 = fast_d[0];
        int fast_d2 = fast_d[1];
        out->fast_edge_d1 = (int8_t)fast_d1;
        out->fast_edge_d2 = (int8_t)fast_d2;
        out->fast_edge_support_f1 = fast_support[0];
        out->fast_edge_support_f2 = fast_support[1];
    out->fast_edge_spatial_conflict = fast_conflict;
        /* This historical-mode delta remains diagnostic-only. Heterogeneous
         * rasters can move a local edge without moving the field. The current
         * unit's independently coherent absolute pair was already fused
         * above; this path only reports a sudden delta from learned modes. */
        bool common_mode = fast_d1 != FIELDREG_UNKNOWN && fast_d1 != 0 &&
                           fast_d1 == fast_d2;
        bool fast_valid = fast_d1 != FIELDREG_UNKNOWN &&
                          fast_d2 != FIELDREG_UNKNOWN && !common_mode &&
                          fast_support[0] >= 2 && fast_support[1] >= 2;
        if (fast_valid) {
            int fast_target1 = engine->baseline[0] + fast_d1;
            int fast_target2 = engine->baseline[1] + fast_d2;
            bool target_in_range =
                fast_target1 >= FIELDREG_MIN_OFFSET &&
                fast_target1 <= FIELDREG_FIELD1_MAX_OFFSET &&
                fast_target2 >= FIELDREG_MIN_OFFSET &&
                fast_target2 <= FIELDREG_FIELD2_MAX_OFFSET;
            if (target_in_range &&
                (fast_target1 != engine->selected[0] ||
                 fast_target2 != engine->selected[1])) {
                out->decision_d1 = FIELDREG_UNKNOWN;
                out->decision_d2 = FIELDREG_UNKNOWN;
                out->mode = FIELDREG_MODE_UNKNOWN_EDGE_TRANSIENT;
            }
        }
    }

    int legacy_d1 = engine->selected[0];
    int legacy_d2 = engine->selected[1];
    int prior_presented_d1 = engine->previous_phase_valid
                                 ? engine->previous_phase[0]
                                 : legacy_d1;
    int prior_presented_d2 = engine->previous_phase_valid
                                 ? engine->previous_phase[1]
                                 : legacy_d2;
    int prior_bottom_applied1 = engine->bottom_applied[0];
    int prior_bottom_applied2 = engine->bottom_applied[1];
    fieldreg_bottom_hold_reason bottom_reason1;
    fieldreg_bottom_hold_reason bottom_reason2;
    bool bottom_placed1 = apply_bottom_field(
        engine, 0, bottom_observation_f1, transport_ok, scene_cut,
        temporal_best1, temporal_margin1, &bottom_reason1);
    bool bottom_placed2 = apply_bottom_field(
        engine, 1, bottom_observation_f2, transport_ok, scene_cut,
        temporal_best2, temporal_margin2, &bottom_reason2);
    bool bottom_changed =
        prior_bottom_applied1 != engine->bottom_applied[0] ||
        prior_bottom_applied2 != engine->bottom_applied[1];

    /* Each field holds the last actually presented placement when its own
     * boundary abstains. bottom_applied[] is only the direct-boundary gauge;
     * it may lag a body-relative refinement and must not snap that refinement
     * away on the next unmeasurable unit. */
    int direct_d1 = bottom_placed1 ? engine->bottom_applied[0]
                                   : prior_presented_d1;
    int direct_d2 = bottom_placed2 ? engine->bottom_applied[1]
                                   : prior_presented_d2;
    int direct_relative = direct_d2 - direct_d1;
    int legacy_relative = legacy_d2 - legacy_d1;
    int prior_presented_relative =
        prior_presented_d2 - prior_presented_d1;
    int chosen_relative = direct_relative;
    int preferred_d1 = direct_d1;
    int preferred_d2 = direct_d2;
    if (relative_only.valid && !registration_scene_cut &&
        relative_only.persistent_columns >= FIELDREG_RELATIVE_STATIC_RUN) {
        chosen_relative = relative_only.phase;
        if (relative_only_authority) {
            preferred_d1 = relative_d1;
            preferred_d2 = relative_d2;
        } else if (relative_only.phase == prior_presented_relative) {
            /* The current body agrees with the immediately preceding
             * presentation even when the lower envelope changes shape. */
            preferred_d1 = prior_presented_d1;
            preferred_d2 = prior_presented_d2;
        } else if (relative_only.phase == legacy_relative) {
            /* Two independent body estimators agree that the direct lower
             * boundary under-reported relative phase. */
            preferred_d1 = legacy_d1;
            preferred_d2 = legacy_d2;
        }
    }
    int presented_d1 = direct_d1;
    int presented_d2 = direct_d2;
    bool relative_refined =
        chosen_relative != direct_relative &&
        constrain_bottom_relative(direct_d1, direct_d2,
                                  preferred_d1, preferred_d2,
                                  chosen_relative,
                                  &presented_d1, &presented_d2);

    /* v8 uses the two lower boundaries as its absolute gauge. An independently
     * earned body-relative phase may refine d2-d1 when the visible envelope
     * under-reports a field displacement; it cannot add common-mode motion. */
    out->applied_d1 = (int8_t)presented_d1;
    out->applied_d2 = (int8_t)presented_d2;
    out->baseline_d1 = (int8_t)presented_d1;
    out->baseline_d2 = (int8_t)presented_d2;
    out->decision_backdate = 0;
    if (bottom_placed1 || bottom_placed2) {
        out->decision_d1 = out->applied_d1;
        out->decision_d2 = out->applied_d2;
        out->mode = relative_refined
                        ? FIELDREG_MODE_BOTTOM_EDGE_RELATIVE_PLACEMENT
                        : FIELDREG_MODE_BOTTOM_EDGE_PLACEMENT;
    } else {
        out->decision_d1 = FIELDREG_UNKNOWN;
        out->decision_d2 = FIELDREG_UNKNOWN;
        out->mode = FIELDREG_MODE_UNKNOWN_BOTTOM_EDGE_HOLD;
    }
    if (scene_cut && !bottom_changed) {
        out->decision_d1 = FIELDREG_UNKNOWN;
        out->decision_d2 = FIELDREG_UNKNOWN;
        out->mode = FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD;
    }
    out->frame_observation_d1 = (int8_t)frame_d1;
    out->frame_observation_d2 = (int8_t)frame_d2;
    out->frame_observation_support = frame_support;
    out->frame_observation_motion_priority = frame_motion_priority;
    out->frame_observation_conflict = frame_conflict;
    /* A positive per-unit observation is provisional. Once that unit has
     * passed, an abstention falls back to the committed phase, never to the
     * last positive observation. This prevents a single contradicted sample
     * from latching indefinitely (the frame-8169 class). */
    engine->previous_phase[0] = out->applied_d1;
    engine->previous_phase[1] = out->applied_d2;
    engine->previous_phase_valid = transport_ok;
    out->confidence = phase_model
                          ? phase.confidence
                          : dual_edge
                                ? fmin(fmin(stability1, stability2),
                                       fmin(bottom_stability1,
                                            bottom_stability2))
                                : weave_margin;
    out->best_d1 = phase_model
                       ? (int8_t)phase_target_d1
                       : candidate_in_range1 ? (int8_t)band_d1
                                             : engine->selected[0];
    out->best_d2 = phase_model
                       ? (int8_t)phase_target_d2
                       : candidate_in_range2 ? (int8_t)band_d2
                                             : engine->selected[1];
    out->pending_d1 = engine->pending_valid ? engine->pending[0] : engine->selected[0];
    out->pending_d2 = engine->pending_valid ? engine->pending[1] : engine->selected[1];
    out->pending_count = engine->pending_count;
    out->pending_span = engine->pending_age;
    out->trajectory_locked = engine->phase_baseline_valid;
    out->best_relative = phase_model ? (int8_t)phase_window
                                     : (int8_t)best_relative;
    out->selected_relative = engine->selected_relative;
    out->independent_evidence_margin = independent_evidence;
    out->weave_margin = weave_margin;
    out->temporal_margin_f1 = temporal_margin1;
    out->temporal_margin_f2 = temporal_margin2;
    out->temporal_best_f1 = (int8_t)temporal_best1;
    out->temporal_best_f2 = (int8_t)temporal_best2;
    out->temporal_best_cost_f1 = temporal_best_cost1;
    out->temporal_best_cost_f2 = temporal_best_cost2;
    out->temporal_scene_cut = scene_cut;
    out->transport_ok = transport_ok;
    out->content_evidence_available = content_evidence_available;
    out->top_f1_censored = top_censored1;
    out->top_f2_censored = top_censored2;
    out->global_envelope_authority = global_envelope_authority;
    out->observed_transport_f1 = (int16_t)observed_f1;
    out->observed_transport_f2 = (int16_t)observed_f2;
    out->picture_top_f1 = (int16_t)top1;
    out->picture_top_f2 = (int16_t)top2;
    out->picture_bottom_f1 = (int16_t)bottom1;
    out->picture_bottom_f2 = (int16_t)bottom2;
    out->learned_band_mode_f1 = (int16_t)mode1;
    out->learned_band_mode_f2 = (int16_t)mode2;
    out->learned_bottom_mode_f1 = (int16_t)bottom_mode1;
    out->learned_bottom_mode_f2 = (int16_t)bottom_mode2;
    out->learned_band_stability_f1 = stability1;
    out->learned_band_stability_f2 = stability2;
    out->learned_bottom_stability_f1 = bottom_stability1;
    out->learned_bottom_stability_f2 = bottom_stability2;
    out->dual_edge_agreement = dual_edge_agreement;
    out->phase_vote_left = phase.vote[0];
    out->phase_vote_center = phase.vote[1];
    out->phase_vote_right = phase.vote[2];
    out->phase_motion_left = phase.motion[0];
    out->phase_motion_center = phase.motion[1];
    out->phase_motion_right = phase.motion[2];
    out->phase_priority_band = phase.priority_band;
    out->phase_consensus = phase.consensus;
    out->phase_support = phase.support;
    out->spatial_phase_conflict = phase.conflict;
    out->phase_window = (int8_t)phase_window;
    out->phase_window_count =
        engine->pending_count > UINT8_MAX ? UINT8_MAX
                                          : (uint8_t)engine->pending_count;
    out->phase_window_margin = phase_window_margin;
    out->relative_only = relative_only_authority;
    out->relative_only_gauge_unknown =
        relative_only_authority && relative_gauge_unknown;
    out->relative_only_gauge_source = relative_gauge;
    out->relative_only_phase = relative_only.phase;
    out->relative_only_best_energy = relative_only.best_energy;
    out->relative_only_runner_energy = relative_only.runner_energy;
    out->relative_only_prior_energy = relative_only.prior_energy;
    out->relative_only_margin = relative_only.margin;
    out->relative_only_ratio = relative_only.ratio;
    out->relative_only_static_columns = relative_only.static_columns;
    out->relative_only_persistent_columns =
        relative_only.persistent_columns;
    out->relative_only_transport_gate = transport_ok;
    out->relative_only_cut_gate = !registration_scene_cut;
    out->bottom_f1_censored = bottom_censored1;
    out->bottom_f2_censored = bottom_censored2;
    out->bottom_raw_edge_f1 = (int16_t)bottom_observation_f1.edge;
    out->bottom_raw_edge_f2 = (int16_t)bottom_observation_f2.edge;
    out->bottom_target_f1 = engine->bottom_target_valid[0]
                                ? engine->bottom_target[0]
                                : -1;
    out->bottom_target_f2 = engine->bottom_target_valid[1]
                                ? engine->bottom_target[1]
                                : -1;
    out->bottom_blanking_level_f1 = bottom_observation_f1.blanking_level;
    out->bottom_blanking_level_f2 = bottom_observation_f2.blanking_level;
    out->bottom_black_threshold_f1 = bottom_observation_f1.black_threshold;
    out->bottom_black_threshold_f2 = bottom_observation_f2.black_threshold;
    out->bottom_measurable_f1 = bottom_observation_f1.program_extent &&
                                !bottom_observation_f1.noisy;
    out->bottom_measurable_f2 = bottom_observation_f2.program_extent &&
                                !bottom_observation_f2.noisy;
    out->bottom_placement_f1 = bottom_placed1;
    out->bottom_placement_f2 = bottom_placed2;
    out->bottom_hold_reason_f1 = bottom_reason1;
    out->bottom_hold_reason_f2 = bottom_reason2;

    /*
     * While an absolute dual-edge candidate is in dwell, retain the current
     * field in that candidate's coordinates.  Saving it with the old applied
     * offset makes the next temporal comparison prefer the old offset and can
     * self-lock a one-frame release forever.
     */
    int save_d1 = phase_model ? 0 : engine->selected[0];
    int save_d2 = phase_model ? 0 : engine->selected[1];
    if (dual_edge && candidate_in_range1 && !common_mode_ambiguous)
        save_d1 = band_d1;
    if (dual_edge && candidate_in_range2 && !common_mode_ambiguous)
        save_d2 = band_d2;
    save_previous(engine, 0, FIELDREG_FIELD1_START + save_d1);
    save_previous(engine, 1, FIELDREG_FIELD2_START + save_d2);
    if (!scene_cut && transport_ok && top1 >= 0 && top2 >= 0) {
        int gauge1 = phase_model ? 0 : engine->selected[0];
        int gauge2 = phase_model ? 0 : engine->selected[1];
        add_band(engine, 0, 0, top1 - FIELDREG_FIELD1_START - gauge1);
        add_band(engine, 1, 0, top2 - FIELDREG_FIELD2_START - gauge2);
        if (bottom1 >= 0)
            add_band(engine, 0, 1, bottom1 - 256 - gauge1);
        if (bottom2 >= 0)
            add_band(engine, 1, 1, bottom2 - 518 - gauge2);
        for (int band = 0; band < PHASE_BANDS; ++band) {
            if (spatial_top[0][band] >= 0)
                add_spatial_edge(engine, 0, 0, band,
                                 spatial_top[0][band] -
                                     FIELDREG_FIELD1_START);
            if (spatial_top[1][band] >= 0)
                add_spatial_edge(engine, 1, 0, band,
                                 spatial_top[1][band] -
                                     FIELDREG_FIELD2_START);
            if (spatial_bottom[0][band] >= 0)
                add_spatial_edge(engine, 0, 1, band,
                                 spatial_bottom[0][band] - 256);
            if (spatial_bottom[1][band] >= 0)
                add_spatial_edge(engine, 1, 1, band,
                                 spatial_bottom[1][band] - 518);
        }
    }
    if (!scene_cut && had_temporal) {
        if (!engine->temporal_cost_ema_valid) {
            engine->temporal_cost_ema[0] = temporal_best_cost1;
            engine->temporal_cost_ema[1] = temporal_best_cost2;
            engine->temporal_cost_ema_valid = true;
        } else {
            engine->temporal_cost_ema[0] =
                engine->temporal_cost_ema[0] * 0.95 + temporal_best_cost1 * 0.05;
            engine->temporal_cost_ema[1] =
                engine->temporal_cost_ema[1] * 0.95 + temporal_best_cost2 * 0.05;
        }
    }
    bool current_edges_valid =
        transport_ok && content_evidence_available && !scene_cut;
    bool adjacent_edges_trackable =
        motion_delta[0] != FIELDREG_UNKNOWN &&
        motion_delta[1] != FIELDREG_UNKNOWN;
    bool refresh_motion_anchor =
        !engine->motion_anchor_valid || !adjacent_edges_trackable ||
        (global_relative_authority && !global_motion_authority);
    if (!current_edges_valid) {
        engine->motion_anchor_valid = false;
    } else if (refresh_motion_anchor) {
        engine->motion_anchor_picture_top[0] = (int16_t)top1;
        engine->motion_anchor_picture_top[1] = (int16_t)top2;
        engine->motion_anchor_picture_bottom[0] = (int16_t)bottom1;
        engine->motion_anchor_picture_bottom[1] = (int16_t)bottom2;
        if (global_relative_authority && !global_motion_authority) {
            engine->motion_anchor_phase[0] = out->applied_d1;
            engine->motion_anchor_phase[1] = out->applied_d2;
        } else {
            engine->motion_anchor_phase[0] = engine->baseline[0];
            engine->motion_anchor_phase[1] = engine->baseline[1];
        }
        for (int field = 0; field < 2; ++field) {
            for (int band = 0; band < PHASE_BANDS; ++band) {
                engine->motion_anchor_spatial_top[field][band] =
                    (int16_t)spatial_top[field][band];
                engine->motion_anchor_spatial_bottom[field][band] =
                    (int16_t)spatial_bottom[field][band];
            }
        }
        engine->motion_anchor_valid = true;
    }
    engine->previous_edge_valid = current_edges_valid;
    if (engine->previous_edge_valid) {
        engine->previous_picture_top[0] = (int16_t)top1;
        engine->previous_picture_top[1] = (int16_t)top2;
        engine->previous_picture_bottom[0] = (int16_t)bottom1;
        engine->previous_picture_bottom[1] = (int16_t)bottom2;
        for (int field = 0; field < 2; ++field) {
            for (int band = 0; band < PHASE_BANDS; ++band) {
                engine->previous_spatial_top[field][band] =
                    (int16_t)spatial_top[field][band];
                engine->previous_spatial_bottom[field][band] =
                    (int16_t)spatial_bottom[field][band];
            }
        }
    }
    ++engine->frames_seen;
    return true;
}

const char *fieldreg_mode_name(fieldreg_mode mode)
{
    switch (mode) {
    case FIELDREG_MODE_INVALID_UNIT: return "InvalidUnit";
    case FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI: return "UnknownTransportOrVBI";
    case FIELDREG_MODE_UNKNOWN_WARMUP_HOLD: return "UnknownWarmupHold";
    case FIELDREG_MODE_UNKNOWN_BAND_LANDMARK: return "UnknownBandLandmark";
    case FIELDREG_MODE_UNKNOWN_BAND_DISAGREEMENT: return "UnknownBandDisagreement";
    case FIELDREG_MODE_UNKNOWN_EVIDENCE_DISAGREEMENT: return "UnknownEvidenceDisagreement";
    case FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE: return "UnknownCommonModeGauge";
    case FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD: return "UnknownSceneCutHold";
    case FIELDREG_MODE_UNKNOWN_TEMPORAL_RELEASE_DWELL: return "UnknownTemporalReleaseDwell";
    case FIELDREG_MODE_UNKNOWN_CANDIDATE_DWELL: return "UnknownCandidateDwell";
    case FIELDREG_MODE_STABLE: return "Stable";
    case FIELDREG_MODE_CONVERGED_RELATIVE_BAND: return "ConvergedRelativeBand";
    case FIELDREG_MODE_CONVERGED_TEMPORAL_RELEASE: return "ConvergedTemporalRelease";
    case FIELDREG_MODE_UNKNOWN_SPATIAL_PHASE: return "UnknownSpatialPhase";
    case FIELDREG_MODE_UNKNOWN_PHASE_DWELL: return "UnknownPhaseDwell";
    case FIELDREG_MODE_UNKNOWN_EDGE_TRANSIENT: return "UnknownEdgeTransient";
    case FIELDREG_MODE_STABLE_MOTION_PHASE: return "StableMotionPhase";
    case FIELDREG_MODE_CONVERGED_MOTION_PHASE: return "ConvergedMotionPhase";
    case FIELDREG_MODE_RELATIVE_ONLY: return "RelativeOnly";
    case FIELDREG_MODE_BOTTOM_EDGE_PLACEMENT: return "BottomEdgePlacement";
    case FIELDREG_MODE_BOTTOM_EDGE_RELATIVE_PLACEMENT:
        return "BottomEdgeRelativePlacement";
    case FIELDREG_MODE_UNKNOWN_BOTTOM_EDGE_HOLD: return "UnknownBottomEdgeHold";
    }
    return "InvalidMode";
}

const char *fieldreg_bottom_hold_reason_name(fieldreg_bottom_hold_reason reason)
{
    switch (reason) {
    case FIELDREG_BOTTOM_HOLD_NONE: return "None";
    case FIELDREG_BOTTOM_HOLD_TARGET_LEARNING: return "TargetLearning";
    case FIELDREG_BOTTOM_HOLD_TRANSPORT: return "Transport";
    case FIELDREG_BOTTOM_HOLD_FLAT_OR_DARK: return "FlatOrDark";
    case FIELDREG_BOTTOM_HOLD_NOISY: return "Noisy";
    case FIELDREG_BOTTOM_HOLD_SCENE_CUT: return "SceneCut";
    case FIELDREG_BOTTOM_HOLD_TEMPORAL_CONTRADICTION:
        return "TemporalContradiction";
    case FIELDREG_BOTTOM_HOLD_EDGE_JUMP: return "EdgeJump";
    case FIELDREG_BOTTOM_HOLD_OUT_OF_RANGE: return "OutOfRange";
    }
    return "Unknown";
}

const char *fieldreg_relative_gauge_name(fieldreg_relative_gauge_source source)
{
    switch (source) {
    case FIELDREG_RELATIVE_GAUGE_NONE:
        return "None";
    case FIELDREG_RELATIVE_GAUGE_PRIOR:
        return "Prior";
    case FIELDREG_RELATIVE_GAUGE_TEMPORAL_F1:
        return "TemporalF1";
    case FIELDREG_RELATIVE_GAUGE_TEMPORAL_F2:
        return "TemporalF2";
    case FIELDREG_RELATIVE_GAUGE_TEMPORAL_BOTH:
        return "TemporalBoth";
    case FIELDREG_RELATIVE_GAUGE_MIN_CROP:
        return "MinCrop";
    }
    return "Unknown";
}
