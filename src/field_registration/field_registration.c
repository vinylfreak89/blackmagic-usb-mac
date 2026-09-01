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

void fieldreg_init(field_registration *engine, const fieldreg_config *config)
{
    fieldreg_config chosen = config ? *config : fieldreg_default_config();
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
    engine->previous_valid[0] = false;
    engine->previous_valid[1] = false;
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
    double sum = 0.0;
    double square_sum = 0.0;
    bool is_hard = true;
    for (int pixel = 0; pixel < 720; ++pixel) {
        uint8_t chroma = src[pixel * 2];
        uint8_t luma = src[pixel * 2 + 1];
        sum += luma;
        square_sum += (double)luma * luma;
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
    return hard_ok && *observed_f1 == FIELDREG_FIELD1_START &&
           *observed_f2 == FIELDREG_FIELD2_START;
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

static int compare_double(const void *left, const void *right)
{
    double a = *(const double *)left;
    double b = *(const double *)right;
    return (a > b) - (a < b);
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
        double line_costs[FIELDREG_FIELD_LINES - 32];
        for (int row = 16; row < FIELDREG_FIELD_LINES - 16; ++row) {
            uint64_t sum = 0;
            for (int x = x_start; x < x_stop; ++x) {
                int difference = (int)engine->luma[start + delta + row][x] -
                                 (int)engine->previous[parity][row][x];
                sum += (uint64_t)(difference < 0 ? -difference : difference);
            }
            line_costs[row - 16] = (double)sum / (x_stop - x_start);
        }
        qsort(line_costs, FIELDREG_FIELD_LINES - 32, sizeof(line_costs[0]),
              compare_double);
        int middle = (FIELDREG_FIELD_LINES - 32) / 2;
        costs[delta - FIELDREG_MIN_OFFSET] =
            (line_costs[middle - 1] + line_costs[middle]) * 0.5;
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

static int update_phase_window(field_registration *engine, int phase,
                               uint8_t *best_count, uint8_t *best_margin)
{
    if (engine->phase_history_filled == FIELDREG_PHASE_HISTORY) {
        int old = engine->phase_history[engine->phase_history_index];
        if (old >= FIELDREG_MIN_OFFSET && old <= FIELDREG_MAX_OFFSET)
            --engine->phase_counts[old - FIELDREG_MIN_OFFSET];
    } else {
        ++engine->phase_history_filled;
    }
    engine->phase_history[engine->phase_history_index] = (int8_t)phase;
    engine->phase_history_index =
        (engine->phase_history_index + 1) % FIELDREG_PHASE_HISTORY;
    if (phase >= FIELDREG_MIN_OFFSET && phase <= FIELDREG_MAX_OFFSET)
        ++engine->phase_counts[phase - FIELDREG_MIN_OFFSET];

    int best = 0;
    int runner = 0;
    int best_phase = FIELDREG_UNKNOWN;
    for (int i = 0; i < 13; ++i) {
        int count = engine->phase_counts[i];
        if (count > best) {
            runner = best;
            best = count;
            best_phase = i + FIELDREG_MIN_OFFSET;
        } else if (count > runner) {
            runner = count;
        }
    }
    *best_count = (uint8_t)best;
    *best_margin = (uint8_t)(best - runner);
    /* Roughly 2/3 second of actual evidence and a decisive local mode. */
    if (best < 20 || best - runner < 8)
        return FIELDREG_UNKNOWN;
    return best_phase;
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

bool fieldreg_process(field_registration *engine, const uint8_t *unit,
                       fieldreg_decision *out)
{
    if (!engine || !unit || !out)
        return false;
    unknown_decision(out);
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
    double cut_threshold1 = engine->temporal_cost_ema[0] * 1.8 + 2.0;
    double cut_threshold2 = engine->temporal_cost_ema[1] * 1.8 + 2.0;
    bool scene_cut = had_temporal && engine->temporal_cost_ema_valid &&
                     temporal_best_cost1 > cut_threshold1 &&
                     temporal_best_cost2 > cut_threshold2;
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
    int band_d1 = top1 < 0 ? FIELDREG_UNKNOWN
                           : top1 - FIELDREG_ACTIVE_TOP_F1;
    int band_d2 = top2 < 0 ? FIELDREG_UNKNOWN
                           : top2 - FIELDREG_ACTIVE_TOP_F2;
    int bottom_d1 = bottom1 < 0 ? FIELDREG_UNKNOWN
                                : bottom1 - FIELDREG_ACTIVE_BOTTOM_F1;
    int bottom_d2 = bottom2 < 0 ? FIELDREG_UNKNOWN
                                : bottom2 - FIELDREG_ACTIVE_BOTTOM_F2;
    bool edge_known1 = band_d1 != FIELDREG_UNKNOWN &&
                       (!dual_edge || bottom_d1 != FIELDREG_UNKNOWN);
    bool edge_known2 = band_d2 != FIELDREG_UNKNOWN &&
                       (!dual_edge || bottom_d2 != FIELDREG_UNKNOWN);
    bool edge_agreement1 = edge_known1 &&
                           (!dual_edge || band_d1 == bottom_d1);
    bool edge_agreement2 = edge_known2 &&
                           (!dual_edge || band_d2 == bottom_d2);
    bool candidate_in_range1 = edge_agreement1 &&
                               band_d1 >= FIELDREG_MIN_OFFSET &&
                               band_d1 <= FIELDREG_FIELD1_MAX_OFFSET;
    bool candidate_in_range2 = edge_agreement2 &&
                               band_d2 >= FIELDREG_MIN_OFFSET &&
                               band_d2 <= FIELDREG_FIELD2_MAX_OFFSET;
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
    uint8_t phase_window_count = 0;
    uint8_t phase_window_margin = 0;
    int phase_window = update_phase_window(
        engine, phase.consensus, &phase_window_count, &phase_window_margin);
    int phase_target_d1 = engine->baseline[0];
    int phase_target_d2 = engine->baseline[1];
    if (phase_window != FIELDREG_UNKNOWN) {
        /*
         * Relative phase cannot identify an absolute anchor.  Move the field
         * whose raw top+bottom landmarks have been less stable; on a tie use
         * field 2 as the anchor, but log every band vote so post can revisit
         * the choice.  No source-specific field is hard-coded as always stable.
         */
        double geometry1 = fmin(stability1, bottom_stability1);
        double geometry2 = fmin(stability2, bottom_stability2);
        if (geometry2 + 0.05 < geometry1) {
            phase_target_d1 = 0;
            phase_target_d2 = phase_window;
        } else {
            phase_target_d1 = -phase_window;
            phase_target_d2 = 0;
        }
        if (phase_target_d1 < FIELDREG_MIN_OFFSET ||
            phase_target_d1 > FIELDREG_FIELD1_MAX_OFFSET ||
            phase_target_d2 < FIELDREG_MIN_OFFSET ||
            phase_target_d2 > FIELDREG_FIELD2_MAX_OFFSET) {
            phase_window = FIELDREG_UNKNOWN;
        }
    }
    ++engine->pending_age;

    out->mode = FIELDREG_MODE_INVALID_UNIT;
    bool phase_changed = false;
    if (phase_model) {
        phase_changed = phase_window != FIELDREG_UNKNOWN &&
                        (!engine->phase_baseline_valid ||
                         phase_target_d1 != engine->baseline[0] ||
                         phase_target_d2 != engine->baseline[1]);
        if (!transport_ok) {
            out->mode = FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI;
        } else if (scene_cut) {
            out->mode = FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD;
        } else if (phase_window == FIELDREG_UNKNOWN) {
            out->mode = FIELDREG_MODE_UNKNOWN_SPATIAL_PHASE;
        } else if (!phase_changed) {
            /* Contrary evidence drains, rather than instantly erases, a
             * pending re-estimate. This is a bounded leaky hysteresis window. */
            if (engine->pending_valid && engine->pending_count > 0)
                --engine->pending_count;
            if (engine->pending_count == 0)
                engine->pending_valid = false;
            out->decision_d1 = engine->selected[0];
            out->decision_d2 = engine->selected[1];
            out->mode = FIELDREG_MODE_STABLE_MOTION_PHASE;
        } else {
            /* The rolling spatial phase mode is the hysteresis. */
            int required_dwell = 1;
            if (engine->pending_valid &&
                engine->pending[0] == phase_target_d1 &&
                engine->pending[1] == phase_target_d2 &&
                engine->pending_age <= 30) {
                ++engine->pending_count;
            } else {
                engine->pending[0] = (int8_t)phase_target_d1;
                engine->pending[1] = (int8_t)phase_target_d2;
                engine->pending_valid = true;
                engine->pending_count = 1;
            }
            engine->pending_age = 0;
            if ((int)engine->pending_count >= required_dwell) {
                engine->selected[0] = (int8_t)phase_target_d1;
                engine->selected[1] = (int8_t)phase_target_d2;
                engine->baseline[0] = (int8_t)phase_target_d1;
                engine->baseline[1] = (int8_t)phase_target_d2;
                engine->phase_baseline_valid = true;
                engine->phase_baseline_age = 0;
                engine->selected_relative = (int8_t)phase_window;
                clear_band_history(engine);
                engine->pending_valid = false;
                engine->pending_count = 0;
                out->decision_d1 = engine->selected[0];
                out->decision_d2 = engine->selected[1];
                out->mode = FIELDREG_MODE_CONVERGED_MOTION_PHASE;
            } else {
                out->mode = FIELDREG_MODE_UNKNOWN_PHASE_DWELL;
            }
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
        engine->phase_baseline_age >= FIELDREG_PHASE_HISTORY) {
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
        /*
         * These absolute-edge observations are deliberately diagnostic-only.
         * Heterogeneous rasters can contain two real spatial phases (an
         * overlay and the underlying programme), and dot crawl can move a
         * local edge without any transport-registration change.  The full
         * tape audit showed that granting this fast path authority produced
         * thousands of false transitions.  Log the candidate, but let only
         * the broad, motion-compensated rolling phase estimate move state.
         */
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

    out->applied_d1 = engine->selected[0];
    out->applied_d2 = engine->selected[1];
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
    out->phase_window_count = phase_window_count;
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
