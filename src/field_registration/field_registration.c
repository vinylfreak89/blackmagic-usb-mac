#include "field_registration.h"

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
        if (!transport_ok) {
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

    out->baseline_d1 = engine->selected[0];
    out->baseline_d2 = engine->selected[1];
    out->frame_observation_d1 = (int8_t)frame_d1;
    out->frame_observation_d2 = (int8_t)frame_d2;
    out->frame_observation_support = frame_support;
    out->frame_observation_motion_priority = frame_motion_priority;
    out->frame_observation_conflict = frame_conflict;
    /* A positive per-unit observation is provisional. Once that unit has
     * passed, an abstention falls back to the committed phase, never to the
     * last positive observation. This prevents a single contradicted sample
     * from latching indefinitely (the frame-8169 class). */
    int held_d1 = engine->selected[0];
    int held_d2 = engine->selected[1];
    out->applied_d1 = phase_model && frame_d1 != FIELDREG_UNKNOWN
                          ? (int8_t)frame_d1
                          : (int8_t)held_d1;
    out->applied_d2 = phase_model && frame_d2 != FIELDREG_UNKNOWN
                          ? (int8_t)frame_d2
                          : (int8_t)held_d2;
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
    }
    return "InvalidMode";
}
