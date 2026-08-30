#include "field_registration.h"

#include <math.h>
#include <string.h>

enum {
    REGISTRATION_WARMUP = 8,
    REGISTRATION_VBI_MARGIN = 25,
    BAND_BIAS = 64,
    BAND_SLOTS = 129,
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
}

fieldreg_config fieldreg_default_config(void)
{
    fieldreg_config config = {
        .switch_margin = 1.5,
        .evidence_model = FIELDREG_EVIDENCE_DUAL_EDGE,
    };
    return config;
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
        for (int x = 0; x < FIELDREG_X_SAMPLES; ++x)
            engine->luma[line][x] = src[(size_t)x * 8];
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

static int picture_top(const bool hard[FIELDREG_RASTER_LINES],
                       const double mean[FIELDREG_RASTER_LINES],
                       const double sigma[FIELDREG_RASTER_LINES],
                       int start, int stop)
{
    bool picture[FIELDREG_RASTER_LINES];
    for (int line = 0; line < FIELDREG_RASTER_LINES; ++line)
        picture[line] = !hard[line] && (sigma[line] > 5.0 || mean[line] > 24.0);
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
        picture[line] = !hard[line] && (sigma[line] > 5.0 || mean[line] > 24.0);
    int last = stop < FIELDREG_RASTER_LINES ? stop - 1 : FIELDREG_RASTER_LINES - 1;
    for (int line = last; line >= start + 2; --line) {
        if (picture[line] && picture[line - 1] && picture[line - 2])
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

static int interfield_registration(const field_registration *engine, double *margin)
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
            for (int x = 0; x < FIELDREG_X_SAMPLES; ++x) {
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

static int compare_double(const void *left, const void *right)
{
    double a = *(const double *)left;
    double b = *(const double *)right;
    return (a > b) - (a < b);
}

static void temporal_costs(const field_registration *engine, int parity, int start,
                           double costs[13])
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
            for (int x = 0; x < FIELDREG_X_SAMPLES; ++x) {
                int difference = (int)engine->luma[start + delta + row][x] -
                                 (int)engine->previous[parity][row][x];
                sum += (uint64_t)(difference < 0 ? -difference : difference);
            }
            line_costs[row - 16] = (double)sum / FIELDREG_X_SAMPLES;
        }
        qsort(line_costs, FIELDREG_FIELD_LINES - 32, sizeof(line_costs[0]),
              compare_double);
        int middle = (FIELDREG_FIELD_LINES - 32) / 2;
        costs[delta - FIELDREG_MIN_OFFSET] =
            (line_costs[middle - 1] + line_costs[middle]) * 0.5;
    }
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
    double independent_evidence = fmax(weave_margin,
                                       fmax(temporal_margin1, temporal_margin2));
    if (best_relative == engine->selected_relative ||
        weave_margin >= engine->config.switch_margin)
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
    int band_d1 = mode1 == FIELDREG_UNKNOWN || top1 < 0
                      ? FIELDREG_UNKNOWN
                      : top1 - FIELDREG_FIELD1_START - mode1;
    int band_d2 = mode2 == FIELDREG_UNKNOWN || top2 < 0
                      ? FIELDREG_UNKNOWN
                      : top2 - FIELDREG_FIELD2_START - mode2;
    int bottom_d1 = bottom_mode1 == FIELDREG_UNKNOWN || bottom1 < 0
                        ? FIELDREG_UNKNOWN
                        : bottom1 - 256 - bottom_mode1;
    int bottom_d2 = bottom_mode2 == FIELDREG_UNKNOWN || bottom2 < 0
                        ? FIELDREG_UNKNOWN
                        : bottom2 - 518 - bottom_mode2;
    bool dual_edge_agreement = !dual_edge ||
                               (bottom_d1 != FIELDREG_UNKNOWN &&
                                bottom_d2 != FIELDREG_UNKNOWN &&
                                band_d1 == bottom_d1 && band_d2 == bottom_d2);
    bool candidate_valid = band_d1 != FIELDREG_UNKNOWN &&
                           band_d2 != FIELDREG_UNKNOWN;
    bool candidate_in_range = candidate_valid && dual_edge_agreement &&
                              band_d1 >= FIELDREG_MIN_OFFSET &&
                              band_d1 <= FIELDREG_MAX_OFFSET &&
                              band_d2 >= FIELDREG_MIN_OFFSET &&
                              band_d2 <= FIELDREG_MAX_OFFSET;
    int candidate_relative = candidate_valid ? band_d2 - band_d1 : 0;
    bool common_mode_ambiguous = candidate_valid && band_d1 != 0 &&
                                 band_d2 != 0 &&
                                 ((band_d1 > 0) == (band_d2 > 0));
    if (dual_edge && candidate_in_range)
        engine->selected_relative = (int8_t)candidate_relative;
    ++engine->pending_age;

    out->mode = FIELDREG_MODE_INVALID_UNIT;
    if (!transport_ok) {
        out->mode = FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI;
    } else if (!enough_history) {
        out->mode = FIELDREG_MODE_UNKNOWN_WARMUP_HOLD;
    } else if (!candidate_in_range) {
        out->mode = candidate_valid && dual_edge && !dual_edge_agreement
                        ? FIELDREG_MODE_UNKNOWN_BAND_DISAGREEMENT
                        : FIELDREG_MODE_UNKNOWN_BAND_LANDMARK;
    } else if (!dual_edge && candidate_relative != engine->selected_relative) {
        out->mode = FIELDREG_MODE_UNKNOWN_EVIDENCE_DISAGREEMENT;
    } else if (common_mode_ambiguous) {
        out->mode = FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE;
    } else if (band_d1 == engine->selected[0] && band_d2 == engine->selected[1]) {
        engine->pending_valid = false;
        engine->pending_count = 0;
        engine->pending_age = 0;
        out->decision_d1 = engine->selected[0];
        out->decision_d2 = engine->selected[1];
        out->mode = FIELDREG_MODE_STABLE;
    } else {
        int changed_count = (band_d1 != engine->selected[0]) +
                            (band_d2 != engine->selected[1]);
        int changed_field = band_d1 != engine->selected[0] ? 0 : 1;
        int less_stable = stability1 + 0.01 < stability2
                              ? 0
                              : stability2 + 0.01 < stability1 ? 1 : -1;
        bool strong_dual_vote = dual_edge && dual_edge_agreement;
        int required_dwell = strong_dual_vote ||
                                     (changed_count == 1 && changed_field == less_stable)
                                 ? 1
                                 : 2;
        if (engine->pending_valid && engine->pending[0] == band_d1 &&
            engine->pending[1] == band_d2 && engine->pending_age <= 2) {
            ++engine->pending_count;
        } else {
            engine->pending[0] = (int8_t)band_d1;
            engine->pending[1] = (int8_t)band_d2;
            engine->pending_valid = true;
            engine->pending_count = 1;
        }
        engine->pending_age = 0;
        if ((int)engine->pending_count >= required_dwell) {
            engine->selected[0] = (int8_t)band_d1;
            engine->selected[1] = (int8_t)band_d2;
            engine->pending_valid = false;
            engine->pending_count = 0;
            out->decision_d1 = (int8_t)band_d1;
            out->decision_d2 = (int8_t)band_d2;
            out->mode = FIELDREG_MODE_CONVERGED_RELATIVE_BAND;
        } else {
            out->mode = FIELDREG_MODE_UNKNOWN_CANDIDATE_DWELL;
        }
    }

    out->applied_d1 = engine->selected[0];
    out->applied_d2 = engine->selected[1];
    out->confidence = dual_edge
                          ? fmin(fmin(stability1, stability2),
                                 fmin(bottom_stability1, bottom_stability2))
                          : weave_margin;
    out->best_d1 = candidate_valid ? (int8_t)band_d1 : engine->selected[0];
    out->best_d2 = candidate_valid ? (int8_t)band_d2 : engine->selected[1];
    out->pending_d1 = engine->pending_valid ? engine->pending[0] : engine->selected[0];
    out->pending_d2 = engine->pending_valid ? engine->pending[1] : engine->selected[1];
    out->pending_count = engine->pending_count;
    out->best_relative = (int8_t)best_relative;
    out->selected_relative = engine->selected_relative;
    out->independent_evidence_margin = independent_evidence;
    out->weave_margin = weave_margin;
    out->temporal_margin_f1 = temporal_margin1;
    out->temporal_margin_f2 = temporal_margin2;
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

    save_previous(engine, 0, FIELDREG_FIELD1_START + engine->selected[0]);
    save_previous(engine, 1, FIELDREG_FIELD2_START + engine->selected[1]);
    if (transport_ok && top1 >= 0 && top2 >= 0) {
        add_band(engine, 0, 0, top1 - FIELDREG_FIELD1_START - engine->selected[0]);
        add_band(engine, 1, 0, top2 - FIELDREG_FIELD2_START - engine->selected[1]);
        if (bottom1 >= 0)
            add_band(engine, 0, 1, bottom1 - 256 - engine->selected[0]);
        if (bottom2 >= 0)
            add_band(engine, 1, 1, bottom2 - 518 - engine->selected[1]);
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
    case FIELDREG_MODE_UNKNOWN_CANDIDATE_DWELL: return "UnknownCandidateDwell";
    case FIELDREG_MODE_STABLE: return "Stable";
    case FIELDREG_MODE_CONVERGED_RELATIVE_BAND: return "ConvergedRelativeBand";
    }
    return "InvalidMode";
}
