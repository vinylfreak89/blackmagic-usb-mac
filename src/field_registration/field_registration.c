#include "field_registration.h"
#include "cea608.h"

#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

typedef struct field_measurement {
    bool insert_present;
    uint8_t insert_byte1;
    uint8_t insert_byte2;
    cea608_candidate off_candidate;
    uint16_t off_count;
    int16_t fallback_row;
    uint16_t fallback_count;
    double blank_mean;
    int16_t top;
    int16_t bottom;
    int16_t height;
    bool geometry_measurable;
    bool bottom_censored;
    bool body_witness_valid;
    int8_t body_shift;
    double body_mad;
    int16_t body_reference_top;
    int16_t body_implied_top;
    bool body_geometry_agrees;
    bool body_differential;
    bool body_common_mode;
    bool picture_position_valid;
    int16_t picture_top;
    bool picture_from_body;
    bool picture_conflict;
} field_measurement;

enum {
    BODY_PROFILE_ROWS = 160,
    /* Every other active luma sample: the explicitly permitted half-width
     * 2-D witness keeps caller-owned state below 256 KiB. */
    BODY_PROFILE_COLUMNS = FIELDREG_ACTIVE_LUMA_SAMPLES,
    BODY_SEARCH_RADIUS = 3,
    /* Units 440/441 at 05:00 measured MAD 9.78 versus 10.05 at the
     * adjacent shift: a 3% tie that made the old witness override a clear
     * picture edge.  Require a 20% win before body motion is testimony. */
    BODY_MARGIN_NUMERATOR = 4,
    BODY_MARGIN_DENOMINATOR = 5,
    /* Three independent static comparisons reject a one-unit content
     * coincidence while acquiring a segment's field-2 zero. Eight later
     * contradictions are long enough to distinguish a plateau from noise. */
    COMB_CALIBRATION_UNITS = 3,
    COMB_DRIFT_UNITS = 8,
    COMB_STATIC_NUMERATOR = 3,
    COMB_STATIC_DENOMINATOR = 100,
};

typedef struct comb_measurement {
    bool measurable;
    int8_t best_shift;
    double best_energy;
    double second_energy;
    double static_fraction;
} comb_measurement;

typedef enum zero_observation_result {
    ZERO_OBSERVATION_CANDIDATE = 0,
    ZERO_OBSERVATION_READY,
    ZERO_OBSERVATION_OUT_OF_BOUNDS,
} zero_observation_result;

static uint16_t read_le16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)((uint16_t)p[1] << 8);
}

static bool valid_unit(const uint8_t unit[FIELDREG_UNIT_BYTES])
{
    if (!unit || memcmp(unit, "\x00\x00\xff\xff", 4) != 0 ||
        read_le16(unit + 6) != 0xe801)
        return false;
    for (int i = 8; i < FIELDREG_HEADER_BYTES; ++i)
        if (unit[i] != 0) return false;
    return true;
}

static double row_mean(const uint8_t *raster, int row)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    uint32_t sum = 0;
    for (int x = 40; x < 680; ++x) sum += line[x * 2 + 1];
    return (double)sum / 640.0;
}

static void body_row_luma(const uint8_t *raster, int row,
                          uint8_t out[BODY_PROFILE_COLUMNS])
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    for (int column = 0; column < BODY_PROFILE_COLUMNS; ++column)
        out[column] = line[(40 + column * 2) * 2 + 1];
}

static void measure_body(const uint8_t *raster, int field,
                         const uint8_t *previous_luma, bool previous_valid,
                         fieldreg_field_state *s, field_measurement *m)
{
    const int base = field == 0 ? 40 : 303;
    uint8_t current[(BODY_PROFILE_ROWS + 2 * BODY_SEARCH_RADIUS) *
                    BODY_PROFILE_COLUMNS];
    for (int row = 0; row < BODY_PROFILE_ROWS + 2 * BODY_SEARCH_RADIUS;
         ++row)
        body_row_luma(raster, base - BODY_SEARCH_RADIUS + row,
                      current + row * BODY_PROFILE_COLUMNS);

    m->body_shift = FIELDREG_UNKNOWN;
    m->body_reference_top = s->previous_measured_top;
    m->body_implied_top = -1;
    if (previous_valid) {
        uint64_t best_cost = UINT64_MAX;
        uint64_t costs[2 * BODY_SEARCH_RADIUS + 1];
        int best_shift = 0;
        for (int shift = -BODY_SEARCH_RADIUS;
             shift <= BODY_SEARCH_RADIUS; ++shift) {
            uint64_t cost = 0;
            for (int row = 0; row < BODY_PROFILE_ROWS; ++row) {
                const uint8_t *previous = previous_luma +
                    (size_t)(base + row) * BODY_PROFILE_COLUMNS;
                const uint8_t *next = current +
                    (row + BODY_SEARCH_RADIUS + shift) * BODY_PROFILE_COLUMNS;
                for (int column = 0; column < BODY_PROFILE_COLUMNS; ++column) {
                    const int delta = (int)previous[column] - (int)next[column];
                    cost += (uint64_t)(delta < 0 ? -delta : delta);
                }
            }
            costs[shift + BODY_SEARCH_RADIUS] = cost;
            /* Match follow_audit.py: ascending shifts and the first strict
             * minimum wins. This also makes a flat minimum visible rather
             * than silently preferring zero. */
            if (cost < best_cost) {
                best_cost = cost;
                best_shift = shift;
            }
        }
        const int best_index = best_shift + BODY_SEARCH_RADIUS;
        uint64_t adjacent_cost = UINT64_MAX;
        if (best_index > 0)
            adjacent_cost = costs[best_index - 1];
        if (best_index + 1 < 2 * BODY_SEARCH_RADIUS + 1 &&
            costs[best_index + 1] < adjacent_cost)
            adjacent_cost = costs[best_index + 1];
        m->body_witness_valid = adjacent_cost != UINT64_MAX &&
            best_cost * BODY_MARGIN_DENOMINATOR <=
            adjacent_cost * BODY_MARGIN_NUMERATOR;
        m->body_shift = (int8_t)best_shift;
        m->body_mad = (double)best_cost /
                      (BODY_PROFILE_ROWS * BODY_PROFILE_COLUMNS);
    }
}

static double row_variance(const uint8_t *raster, int row, double mean)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    double sum = 0.0;
    for (int x = 40; x < 680; ++x) {
        const double delta = (double)line[x * 2 + 1] - mean;
        sum += delta * delta;
    }
    return sum / 640.0;
}

static bool gap_like_line(const uint8_t *raster, int row, int first,
                          int adc_last, const double *means,
                          double picture_threshold)
{
    if (row + 3 > adc_last || means[row - first] <= picture_threshold)
        return false;
    const double below = (means[row + 1 - first] +
                          means[row + 2 - first] +
                          means[row + 3 - first]) / 3.0;
    if (means[row - first] * 2.0 >= below) return false;
    /* The tape's line-22 gap is both dim and flat. The variance guard keeps a
     * genuinely dark, textured first picture row from being discarded. */
    return row_variance(raster, row, means[row - first]) <= 16.0;
}

static double row_bins(const uint8_t *raster, int row, double *bins,
                       int bin_count)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    uint32_t total = 0;
    for (int bin = 0; bin < bin_count; ++bin) {
        const int first = 40 + (bin * 640) / bin_count;
        const int last = 40 + ((bin + 1) * 640) / bin_count;
        uint32_t sum = 0;
        for (int x = first; x < last; ++x) sum += line[x * 2 + 1];
        bins[bin] = (double)sum / (double)(last - first);
        total += sum;
    }
    return (double)total / 640.0;
}

static bool xds_left_structure(const uint8_t *raster, int row)
{
    double bins[24];
    if (row_bins(raster, row, bins, 24) >= 95.0) return false;
    if (bins[1] <= 60.0 || bins[2] > 40.0) return false;
    int bar_run = 0;
    bool bar_present = false;
    for (int bin = 4; bin <= 7; ++bin) {
        if (bins[bin] > 60.0) {
            if (++bar_run >= 2) bar_present = true;
        } else bar_run = 0;
    }
    if (!bar_present) return false;
    return bins[8] <= 40.0 && bins[9] <= 40.0;
}

static bool field2_envelope(const uint8_t *raster, int row)
{
    /* Only the measured XDS structure in the left 40% is invariant. Picture
     * can bleed into the right half, so it is deliberately unconstrained. */
    return xds_left_structure(raster, row);
}

static bool caption_like_damage(const uint8_t *raster, int row)
{
    double bins[24];
    const double mean = row_bins(raster, row, bins, 24);
    double run_mean = 0.0;
    for (int i = 0; i < 6; ++i) run_mean += bins[i];
    run_mean /= 6.0;
    double variance = 0.0;
    for (int i = 0; i < 6; ++i) {
        const double delta = bins[i] - run_mean;
        variance += delta * delta;
    }
    variance /= 6.0;
    double pulse = bins[6];
    for (int i = 7; i < 18; ++i)
        if (bins[i] > pulse) pulse = bins[i];
    double dark = bins[18];
    for (int i = 19; i < 24; ++i)
        if (bins[i] < dark) dark = bins[i];
    /* Damaged run-in lines measured at 37:01 retain a flat coarse-bin
     * envelope (variance <= 18). Genuine consecutive picture rows at the
     * same site begin at 30.8, so do not let the weak-caption fallback erase
     * them from geometry. Full-amplitude run-in remains covered above by the
     * CEA-608 carrier detector independently of this fallback. */
    return run_mean > 35.0 && run_mean < 90.0 && variance < 20.0 &&
           pulse > 85.0 && mean < 95.0 && dark < 40.0;
}

static bool timing_like_damage(const uint8_t *raster, int row)
{
    double bins[24];
    const double mean = row_bins(raster, row, bins, 24);
    double middle = bins[2];
    for (int i = 3; i < 17; ++i)
        if (bins[i] > middle) middle = bins[i];
    double right_pulse = bins[17];
    for (int i = 18; i < 22; ++i)
        if (bins[i] > right_pulse) right_pulse = bins[i];
    return bins[0] > 80.0 && middle < 12.0 && right_pulse > 100.0 &&
           mean < 60.0;
}

static bool top_interval_vbi_damage(const uint8_t *raster, int row, int field)
{
    const int first = field == 0 ? 16 : 279; /* NTSC 20 / 283 */
    const int last = field == 0 ? 26 : 289;  /* NTSC 30 / 293 */
    if (row < first || row > last) return false;
    return caption_like_damage(raster, row) ||
           timing_like_damage(raster, row) ||
           xds_left_structure(raster, row);
}

static void measure_field(const uint8_t *raster, int field,
                          field_measurement *m)
{
    const int first = field == 0 ? 8 : 268;   /* NTSC 12 / 272 */
    const int last = field == 0 ? 262 : 524;  /* NTSC 266 / 528 */
    const int insert = field == 0 ? FIELDREG_INSERT_F1 : FIELDREG_INSERT_F2;
    const int picture_first = field == 0 ? 18 : 281; /* NTSC 22 / 285 */
    const int adc_last = field == 0 ? 260 : 522;      /* NTSC 264 / 526 */
    const int clip_band_first = field == 0 ? 256 : 518; /* NTSC 260 / 522 */
    const int blank_first = field == 0 ? 7 : 270;
    const int blank_last = field == 0 ? 16 : 279;
    bool waveform[257] = {false};
    double means[257] = {0.0};
    memset(m, 0, sizeof *m);
    m->fallback_row = -1;
    m->top = m->bottom = m->height = -1;

    for (int row = blank_first; row <= blank_last; ++row)
        m->blank_mean += row_mean(raster, row);
    m->blank_mean /= (double)(blank_last - blank_first + 1);
    const double picture_threshold = m->blank_mean + 4.0;

    uint8_t luma[CEA608_PIXELS_PER_LINE];
    for (int row = first; row <= last; ++row) {
        const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
        for (int x = 0; x < CEA608_PIXELS_PER_LINE; ++x)
            luma[x] = line[x * 2 + 1];
        cea608_decode_result decoded;
        cea608_decode_luma(luma, &decoded);
        waveform[row - first] = decoded.run_in_present;
        if (top_interval_vbi_damage(raster, row, field))
            waveform[row - first] = true;
        means[row - first] = row_mean(raster, row);
        if (decoded.parity_valid) {
            if (row == insert) {
                m->insert_present = true;
                m->insert_byte1 = decoded.byte1;
                m->insert_byte2 = decoded.byte2;
            } else {
                if (m->off_count == 0) {
                    m->off_candidate.raster_row = (int16_t)row;
                    m->off_candidate.byte1 = decoded.byte1;
                    m->off_candidate.byte2 = decoded.byte2;
                    m->off_candidate.amplitude = decoded.amplitude;
                }
                if (m->off_count != UINT16_MAX) ++m->off_count;
            }
        }
        /* The frozen smeared-XDS fallback is a top-interval classifier, not a
         * whole-picture search: NTSC lines 285..290 (unit rows 281..286).
         * Scanning the body admits picture texture by construction. */
        if (field == 1 && row > insert && row <= insert + 6 &&
            !decoded.run_in_present && !decoded.parity_valid &&
            field2_envelope(raster, row)) {
            waveform[row - first] = true;
            if (m->fallback_count == 0) m->fallback_row = (int16_t)row;
            if (m->fallback_count != UINT16_MAX) ++m->fallback_count;
        }
    }

    int top_scan_first = picture_first;
    if (m->off_count == 1)
        top_scan_first = m->off_candidate.raster_row + 1;
    else if (field == 1 && m->fallback_count == 1)
        top_scan_first = m->fallback_row + 1;
    if (top_scan_first < first) top_scan_first = first;
    if (top_scan_first > adc_last) top_scan_first = adc_last;

    /* Once a unique primary/fallback line identifies field timing, picture
     * geometry starts below that line. Bright VBI damage above the gauge is
     * neither caption nor picture and must not move the geometry lock. */
    for (int row = top_scan_first; row + 2 <= adc_last; ++row) {
        if (!waveform[row - first] && means[row - first] > picture_threshold &&
            !waveform[row + 1 - first] && means[row + 1 - first] > picture_threshold &&
            !waveform[row + 2 - first] && means[row + 2 - first] > picture_threshold &&
            !gap_like_line(raster, row, first, adc_last, means, picture_threshold) &&
            !gap_like_line(raster, row + 1, first, adc_last, means, picture_threshold) &&
            !gap_like_line(raster, row + 2, first, adc_last, means, picture_threshold)) {
            m->top = (int16_t)row;
            break;
        }
    }
    for (int row = adc_last; row >= picture_first; --row) {
        if (!waveform[row - first] && means[row - first] > picture_threshold) {
            m->bottom = (int16_t)row;
            break;
        }
    }
    if (m->top >= 0 && m->bottom >= m->top) {
        m->height = (int16_t)(m->bottom - m->top + 1);
        m->geometry_measurable = true;
        m->bottom_censored = m->bottom >= clip_band_first;
    }
}

static bool in_range(int field, int d)
{
    const int high = field == 0 ? FIELDREG_FIELD1_MAX_OFFSET :
                                  FIELDREG_FIELD2_MAX_OFFSET;
    return d >= FIELDREG_MIN_OFFSET && d <= high;
}

static void clear_clip(fieldreg_field_state *s)
{
    s->clip_ceiling = -1;
    s->clip_candidate = -1;
    s->clip_candidate_d = FIELDREG_UNKNOWN;
    s->clip_candidate_count = 0;
}

static fieldreg_clip_state clip_state(const fieldreg_field_state *s)
{
    if (s->clip_ceiling >= 0) return FIELDREG_CLIP_FITTED;
    if (s->clip_candidate_count > 0) return FIELDREG_CLIP_FITTING;
    return FIELDREG_CLIP_UNKNOWN;
}

static void copy_lock(const fieldreg_field_state *s,
                      fieldreg_field_decision *d)
{
    d->lock_state = s->lock_state;
    d->zero_source = s->zero_source;
    d->lock_id = s->lock_id;
    d->lock_top = s->top;
    d->lock_height = s->height;
    d->lock_height_known = s->height_known;
    d->clip_state = clip_state(s);
    d->clip_ceiling = s->clip_ceiling;
}

static void hold(fieldreg_field_state *s, fieldreg_field_decision *d,
                 fieldreg_mode reason)
{
    d->measured_d = FIELDREG_UNKNOWN;
    d->applied_d = s->last_applied;
    d->reason = reason;
    d->gauge = FIELDREG_GAUGE_HOLD;
}

static void clear_zero_candidate(fieldreg_field_state *s)
{
    s->zero_candidate = INT16_MIN;
    s->zero_candidate_count = 0;
    s->zero_candidate_source = FIELDREG_ZERO_NONE;
}

/* A zero is segment state. A gauge places its current unit immediately, but
 * a different base must repeat three times before it may move that state. */
static zero_observation_result observe_gauge_zero(
    fieldreg_field_state *s, int field, int measured,
    fieldreg_zero_source source, int observed_top)
{
    const int base_top = observed_top - measured;
    const int standard = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                                      FIELDREG_PICTURE_ORIGIN_F2;
    if (abs(base_top - standard) > 3) {
        clear_zero_candidate(s);
        return ZERO_OBSERVATION_OUT_OF_BOUNDS;
    }
    if (base_top == s->top) {
        clear_zero_candidate(s);
        s->zero_source = source;
        return ZERO_OBSERVATION_READY;
    }
    if (s->zero_candidate == base_top &&
        s->zero_candidate_source == source) {
        if (s->zero_candidate_count < UINT8_MAX)
            ++s->zero_candidate_count;
    } else {
        s->zero_candidate = (int16_t)base_top;
        s->zero_candidate_count = 1;
        s->zero_candidate_source = source;
    }
    if (s->zero_candidate_count < 3) return ZERO_OBSERVATION_CANDIDATE;
    s->top = (int16_t)base_top;
    s->zero_source = source;
    clear_clip(s);
    clear_zero_candidate(s);
    return ZERO_OBSERVATION_READY;
}

static void update_gauge_geometry(fieldreg_field_state *s,
                                  const field_measurement *m, int measured)
{
    if (!m->geometry_measurable) return;
    if (s->height < 0) {
        s->height = m->height;
        s->height_known = !m->bottom_censored;
        return;
    }
    if (!s->height_known) {
        const int lower_bottom = s->top + s->height - 1 + measured;
        if (!m->bottom_censored && m->bottom >= lower_bottom) {
            s->height = m->height;
            s->height_known = true;
        } else if (m->height > s->height) {
            s->height = m->height;
        }
        return;
    }

    const int uncensored_bottom = s->top + s->height - 1 + measured;
    if (s->clip_ceiling >= 0) {
        const int expected = uncensored_bottom > s->clip_ceiling ?
                             s->clip_ceiling : uncensored_bottom;
        if (m->bottom == expected) return;
        if (m->bottom < expected)
            return; /* Shorter content cannot disprove a physical ceiling. */
        s->height_known = false;
        clear_clip(s);
        return;
    } else if (m->bottom <= uncensored_bottom) {
        /* With a golden gauge and unknown C, a short visible envelope can be
         * clipping. Top placement remains authoritative until C is fitted. */
        return;
    }
    /* A gauged envelope extending a lower bound increases H; it cannot
     * contradict the independently measured position. */
    s->height = m->height;
}

static void fit_clip(fieldreg_field_state *s, const field_measurement *m,
                     int measured, int observed_top)
{
    if (!m->geometry_measurable || s->clip_ceiling >= 0)
        return;
    if (observed_top != s->top + measured) return;
    if (s->clip_candidate < m->bottom) {
        /* Track the greatest passable line. Darker/shorter content can only
         * move the apparent bottom upward and must never fit a smaller C. */
        s->clip_candidate = m->bottom;
        s->clip_candidate_d = (int8_t)measured;
        s->clip_candidate_count = 1;
    } else if (s->clip_candidate == m->bottom &&
        s->clip_candidate_d != measured) {
        if (s->clip_candidate_count < UINT8_MAX) ++s->clip_candidate_count;
        s->clip_candidate_d = (int8_t)measured;
        if (s->clip_candidate_count >= 2)
            s->clip_ceiling = s->clip_candidate;
    }
}

static void record_invariant(const fieldreg_field_state *s,
                             const field_measurement *m, int measured,
                             fieldreg_field_decision *d)
{
    if (s->lock_state != FIELDREG_LOCK_LOCKED || s->height < 0 ||
        !m->geometry_measurable)
        return;
    const int uncensored = s->top + s->height - 1 + measured;
    const int expected = s->clip_ceiling >= 0 && uncensored > s->clip_ceiling ?
                         s->clip_ceiling : uncensored;
    d->expected_bottom = (int16_t)expected;
    d->lines_lost = (int16_t)(uncensored > m->bottom ?
                              uncensored - m->bottom : 0);
    d->bottom_censored = d->lines_lost > 0 ||
                         m->bottom_censored;
    d->invariant_residual = (int16_t)(m->bottom - expected);
}

static bool body_reliable(const field_measurement *m)
{
    return m->body_witness_valid && m->body_mad <= 25.0;
}

static void resolve_picture_positions(field_measurement m[2])
{
    const bool reliable0 = body_reliable(&m[0]);
    const bool reliable1 = body_reliable(&m[1]);
    if (reliable0 && reliable1) {
        const bool common = m[0].body_shift == m[1].body_shift &&
                            m[0].body_shift != 0;
        m[0].body_common_mode = m[1].body_common_mode = common;
        m[0].body_differential = m[1].body_differential =
            m[0].body_shift != m[1].body_shift;
    }

    for (int field = 0; field < 2; ++field) {
        field_measurement *one = &m[field];
        const bool reliable = body_reliable(one);
        if (reliable && one->body_reference_top >= 0)
            one->body_implied_top = (int16_t)(one->body_reference_top +
                                              one->body_shift);

        if (one->top >= 0) {
            if (one->body_implied_top < 0) {
                one->picture_position_valid = true;
                one->picture_top = one->top;
            } else if (one->top == one->body_implied_top) {
                one->body_geometry_agrees = true;
                one->picture_position_valid = true;
                one->picture_top = one->top;
            } else if (one->body_shift == 0) {
                /* The body stood still: a one-line brightness change at the
                 * top is content, not field displacement. */
                one->picture_position_valid = true;
                one->picture_top = one->body_implied_top;
                one->picture_from_body = true;
                one->picture_conflict = true;
            } else {
                one->picture_conflict = true;
            }
        } else if (one->body_implied_top >= 0 &&
                   (one->body_shift == 0 || one->body_differential)) {
            /* With no top, differential body motion is field displacement;
             * equal nonzero motion in both fields could instead be a pan. */
            one->picture_position_valid = true;
            one->picture_top = one->body_implied_top;
            one->picture_from_body = true;
        }
    }
}

static void line_box_sums_current(const uint8_t *raster, int row,
                                  uint16_t out[BODY_PROFILE_COLUMNS])
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    unsigned sum = 0;
    for (int x = 0; x < BODY_PROFILE_COLUMNS; ++x) {
        sum += line[(40 + x * 2) * 2 + 1];
        if (x >= 4) sum -= line[(40 + (x - 4) * 2) * 2 + 1];
        out[x] = (uint16_t)sum;
    }
}

static void line_box_sums_previous(const field_registration *engine, int row,
                                   uint16_t out[BODY_PROFILE_COLUMNS])
{
    const uint8_t *line = engine->previous_luma +
                          (size_t)row * BODY_PROFILE_COLUMNS;
    unsigned sum = 0;
    for (int x = 0; x < BODY_PROFILE_COLUMNS; ++x) {
        sum += line[x];
        if (x >= 4) sum -= line[x - 4];
        out[x] = (uint16_t)sum;
    }
}

static comb_measurement measure_static_comb(const field_registration *engine,
                                            const uint8_t *raster,
                                            int d1, int d2,
                                            int first_shift,
                                            int last_shift)
{
    comb_measurement result = {0};
    result.best_shift = FIELDREG_UNKNOWN;
    result.best_energy = result.second_energy = INFINITY;
    if (!engine->previous_luma_valid) return result;
    const int a1 = FIELDREG_FIELD1_START + d1;
    const int a2 = FIELDREG_FIELD2_START + d2;
    if (a1 < 0 || a1 + FIELDREG_FIELD_LINES > FIELDREG_RASTER_LINES)
        return result;

    for (int shift = first_shift; shift <= last_shift; ++shift) {
        const int f2 = a2 + shift;
        if (f2 < 0 || f2 + FIELDREG_FIELD_LINES > FIELDREG_RASTER_LINES)
            continue;
        uint64_t cost = 0;
        uint64_t count = 0;
        for (int row = 0; row + 1 < FIELDREG_FIELD_LINES; ++row) {
            uint16_t c1a[BODY_PROFILE_COLUMNS], p1a[BODY_PROFILE_COLUMNS];
            uint16_t c1b[BODY_PROFILE_COLUMNS], p1b[BODY_PROFILE_COLUMNS];
            uint16_t c2[BODY_PROFILE_COLUMNS], p2[BODY_PROFILE_COLUMNS];
            line_box_sums_current(raster, a1 + row, c1a);
            line_box_sums_previous(engine, a1 + row, p1a);
            line_box_sums_current(raster, a1 + row + 1, c1b);
            line_box_sums_previous(engine, a1 + row + 1, p1b);
            line_box_sums_current(raster, f2 + row, c2);
            line_box_sums_previous(engine, f2 + row, p2);
            for (int x = 0; x < BODY_PROFILE_COLUMNS; ++x) {
                const int t1a = (int)c1a[x] - (int)p1a[x];
                const int t1b = (int)c1b[x] - (int)p1b[x];
                const int t2 = (int)c2[x] - (int)p2[x];
                if (abs(t1a) >= 24 || abs(t1b) >= 24 || abs(t2) >= 24)
                    continue;
                int delta = 2 * (int)c2[x] - (int)c1a[x] - (int)c1b[x];
                cost += (uint64_t)(delta < 0 ? -delta : delta);
                ++count;
            }
        }
        if (count == 0) continue;
        const double fraction = (double)count /
            ((FIELDREG_FIELD_LINES - 1) * BODY_PROFILE_COLUMNS);
        const double energy = (double)cost / (8.0 * (double)count);
        if (energy < result.best_energy) {
            result.second_energy = result.best_energy;
            result.best_energy = energy;
            result.best_shift = (int8_t)shift;
            result.static_fraction = fraction;
        } else if (energy < result.second_energy) {
            result.second_energy = energy;
        }
    }
    result.measurable = result.best_shift != FIELDREG_UNKNOWN &&
        isfinite(result.second_energy) &&
        result.static_fraction >=
            (double)COMB_STATIC_NUMERATOR / COMB_STATIC_DENOMINATOR &&
        result.best_energy <= 0.75 * result.second_energy;
    return result;
}

static void copy_current_luma(field_registration *engine,
                              const uint8_t *raster)
{
    for (int row = 0; row < FIELDREG_RASTER_LINES; ++row) {
        uint8_t *dst = engine->previous_luma +
                       (size_t)row * BODY_PROFILE_COLUMNS;
        const uint8_t *line = raster +
                              (size_t)row * FIELDREG_BYTES_PER_LINE;
        for (int x = 0; x < BODY_PROFILE_COLUMNS; ++x)
            dst[x] = line[(40 + x * 2) * 2 + 1];
    }
    engine->previous_luma_valid = true;
}

/* A censored or absent bottom is no testimony. A fully visible one must
 * conserve the settled height before picture geometry may veto caption. */
static bool bottom_allows_caption(const fieldreg_field_state *s,
                                  const field_measurement *m, int measured)
{
    if (m->bottom < 0 || m->bottom_censored) return true;
    if (s->height < 0 || !s->height_known) return false;
    const int expected = s->top + s->height - 1 + measured;
    return (s->clip_ceiling < 0 || expected <= s->clip_ceiling) &&
           m->bottom == expected;
}

static bool crop_offset_valid(int field, int measured)
{
    const int start = field == 0 ? FIELDREG_FIELD1_START :
                                   FIELDREG_FIELD2_START;
    const int low = -start;
    const int high = FIELDREG_RASTER_LINES - FIELDREG_FIELD_LINES - start;
    return measured >= low && measured <= high &&
           measured >= INT8_MIN && measured <= INT8_MAX;
}

static bool body_confirms_geometry(const fieldreg_field_state *s,
                                   const field_measurement *m, int field,
                                   int *measured)
{
    if (s->lock_state != FIELDREG_LOCK_LOCKED ||
        !m->picture_position_valid || !body_reliable(m) ||
        (!m->body_geometry_agrees && !m->picture_from_body))
        return false;
    const int candidate = m->picture_top - s->top;
    if (!crop_offset_valid(field, candidate))
        return false;
    *measured = candidate;
    return true;
}

static bool apply_body_geometry(fieldreg_field_state *s,
                                const field_measurement *m, int field,
                                fieldreg_mode provenance,
                                fieldreg_field_decision *d)
{
    int measured;
    if (!body_confirms_geometry(s, m, field, &measured)) return false;
    d->measured_d = (int8_t)measured;
    d->applied_d = (int8_t)measured;
    d->reason = provenance;
    d->gauge = FIELDREG_GAUGE_GEOMETRY;
    s->last_applied = (int8_t)measured;
    record_invariant(s, m, measured, d);
    return true;
}

static bool apply_picture_position(fieldreg_field_state *s,
                                   const field_measurement *m, int field,
                                   fieldreg_mode provenance,
                                   fieldreg_field_decision *d)
{
    if (!m->picture_position_valid) return false;
    const int measured = m->picture_top - s->top;
    if (!crop_offset_valid(field, measured)) return false;
    d->measured_d = (int8_t)measured;
    d->applied_d = (int8_t)measured;
    d->reason = provenance;
    d->gauge = FIELDREG_GAUGE_GEOMETRY;
    s->last_applied = (int8_t)measured;
    record_invariant(s, m, measured, d);
    return true;
}

static void decide_geometry(fieldreg_field_state *s,
                            const field_measurement *m, int field,
                            fieldreg_field_decision *d)
{
    if (m->picture_conflict && !m->picture_position_valid) {
        hold(s, d, FIELDREG_MODE_TOP_BODY_DISAGREE);
        return;
    }
    if (m->body_common_mode && !m->picture_position_valid) {
        hold(s, d, FIELDREG_MODE_COMMON_MODE_BODY_HOLD);
        return;
    }
    if (m->picture_from_body) {
        const fieldreg_mode provenance = m->top >= 0 ?
            FIELDREG_MODE_TOP_BODY_DISAGREE :
            FIELDREG_MODE_BODY_ONLY_PLACEMENT;
        if (apply_picture_position(s, m, field, provenance, d)) return;
    }
    if (!m->geometry_measurable) {
        if (apply_body_geometry(s, m, field,
                                FIELDREG_MODE_GEOMETRY_LOCK_DECIDES, d))
            return;
        hold(s, d, FIELDREG_MODE_GEOMETRY_UNMEASURABLE);
        return;
    }
    const int measured = m->picture_position_valid ?
                         m->picture_top - s->top : m->top - s->top;
    if (!in_range(field, measured)) {
        if (apply_body_geometry(s, m, field,
                                FIELDREG_MODE_OUT_OF_RANGE_HOLD, d))
            return;
        hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        return;
    }
    if (s->height < 0) {
        s->height = m->height;
        s->height_known = !m->bottom_censored;
    } else if (!s->height_known) {
        const int lower_bottom = s->top + s->height - 1 + measured;
        if (!m->bottom_censored) {
            if (m->bottom < lower_bottom) {
                if (apply_body_geometry(s, m, field,
                                        FIELDREG_MODE_LOCK_BROKEN, d))
                    return;
                hold(s, d, FIELDREG_MODE_LOCK_BROKEN);
                return;
            }
            s->height = (int16_t)(m->bottom - s->top - measured + 1);
            s->height_known = true;
        }
    }
    const int uncensored = s->top + s->height - 1 + measured;
    const int expected = s->clip_ceiling >= 0 && uncensored > s->clip_ceiling ?
                         s->clip_ceiling : uncensored;
    d->expected_bottom = (int16_t)expected;
    d->lines_lost = (int16_t)(uncensored - expected);
    d->invariant_residual = (int16_t)(m->bottom - expected);
    d->bottom_censored = d->lines_lost > 0 || m->bottom_censored;
    const bool unknown_clip_at_boundary = s->clip_ceiling < 0 &&
                                          m->bottom_censored &&
                                          m->bottom <= uncensored;
    if (d->invariant_residual != 0 && !unknown_clip_at_boundary &&
        !m->bottom_censored) {
        /* A parity/fallback zero is physical. A changed content envelope can
         * invalidate this unit's geometry without redefining that zero. */
        if (!apply_body_geometry(s, m, field,
                                 FIELDREG_MODE_LOCK_BROKEN, d))
            hold(s, d, FIELDREG_MODE_LOCK_BROKEN);
        return;
    }
    d->measured_d = (int8_t)measured;
    d->applied_d = (int8_t)measured;
    d->reason = FIELDREG_MODE_GEOMETRY_LOCK_DECIDES;
    d->gauge = FIELDREG_GAUGE_GEOMETRY;
    s->last_applied = (int8_t)measured;
}

static void decide_field(fieldreg_field_state *s, const field_measurement *m,
                         int field, fieldreg_field_decision *d)
{
    bool zero_observation = false;
    memset(d, 0, sizeof *d);
    d->measured_d = FIELDREG_UNKNOWN;
    d->geometry_d = FIELDREG_UNKNOWN;
    d->gauge_row = -1;
    d->expected_bottom = -1;
    d->raw_top = m->top;
    d->raw_bottom = m->bottom;
    d->raw_height = m->height;
    d->geometry_measurable = m->geometry_measurable;
    d->blank_mean = m->blank_mean;
    d->body_witness_valid = m->body_witness_valid;
    d->body_shift = m->body_shift;
    d->body_mad = m->body_mad;
    d->body_geometry_agrees = m->body_geometry_agrees;
    d->body_reference_top = m->body_reference_top;
    d->body_implied_top = m->body_implied_top;
    d->body_differential = m->body_differential;
    d->body_common_mode = m->body_common_mode;
    d->picture_position_valid = m->picture_position_valid;
    d->measured_picture_top = m->picture_position_valid ?
                              m->picture_top : -1;
    d->picture_from_body = m->picture_from_body;
    d->insert_present = m->insert_present;
    d->insert_byte1 = m->insert_byte1;
    d->insert_byte2 = m->insert_byte2;
    d->parity_candidate_count = m->off_count;
    d->fallback_candidate_count = m->fallback_count;
    if (s->lock_state == FIELDREG_LOCK_LOCKED &&
        m->picture_position_valid)
        d->geometry_d = (int8_t)(m->picture_top - s->top);
    if (m->insert_present &&
        (m->insert_byte1 != 0x80 || m->insert_byte2 != 0x80) &&
        d->geometry_d != FIELDREG_UNKNOWN)
        d->insert_relation = d->geometry_d == 0 ?
                             FIELDREG_INSERT_CORROBORATES :
                             FIELDREG_INSERT_CONTRADICTED;

    if (!m->insert_present) {
        hold(s, d, FIELDREG_MODE_INSERT_ABSENT);
        record_invariant(s, m, s->last_applied, d);
    } else if (m->off_count > 1) {
        if (!apply_body_geometry(s, m, field,
                                 FIELDREG_MODE_LINE21_AMBIGUOUS, d))
            hold(s, d, FIELDREG_MODE_LINE21_AMBIGUOUS);
    } else if (m->off_count == 1) {
        const int measured = m->off_candidate.raster_row -
                             (field == 0 ? FIELDREG_INSERT_F1 : FIELDREG_INSERT_F2);
        d->gauge_row = m->off_candidate.raster_row;
        d->gauge_byte1 = m->off_candidate.byte1;
        d->gauge_byte2 = m->off_candidate.byte2;
        d->gauge_amplitude = m->off_candidate.amplitude;
        const bool insert_nonnull = m->insert_byte1 != 0x80 ||
                                    m->insert_byte2 != 0x80;
        int picture_d = FIELDREG_UNKNOWN;
        const bool body_position = body_confirms_geometry(s, m, field,
                                                          &picture_d);
        const bool picture_testimony = body_position &&
            bottom_allows_caption(s, m, picture_d);
        const bool picture_disagrees = picture_testimony &&
                                       picture_d != measured;
        const bool picture_internally_conflicted = body_position &&
            !picture_testimony && picture_d != measured;
        if (measured == 1 && insert_nonnull && d->geometry_d == 0) {
            d->measured_d = 0;
            d->applied_d = 0;
            d->reason = FIELDREG_MODE_LINE22_DATA_PRESENT;
            d->gauge = FIELDREG_GAUGE_LINE22_DATA;
            s->last_applied = 0;
            record_invariant(s, m, 0, d);
        } else if (measured == 1 && !insert_nonnull &&
                   s->lock_state == FIELDREG_LOCK_LOCKED &&
                   d->geometry_d == 0) {
            if (!apply_body_geometry(s, m, field,
                                     FIELDREG_MODE_GAUGE_CONFLICT, d)) {
                hold(s, d, FIELDREG_MODE_GAUGE_CONFLICT);
                d->gauge = FIELDREG_GAUGE_CEA608_PARITY;
            }
        } else if (picture_disagrees) {
            d->reason = m->body_shift == 0 ?
                        FIELDREG_MODE_CAPTION_ONLY_MOTION :
                        FIELDREG_MODE_CAPTION_BODY_DISAGREE;
            d->measured_d = (int8_t)picture_d;
            d->applied_d = (int8_t)picture_d;
            d->gauge = FIELDREG_GAUGE_GEOMETRY;
            s->last_applied = (int8_t)picture_d;
            record_invariant(s, m, picture_d, d);
        } else if (picture_internally_conflicted) {
            hold(s, d, FIELDREG_MODE_CAPTION_BODY_DISAGREE);
        } else if (!in_range(field, measured)) {
            if (!apply_body_geometry(s, m, field,
                                     FIELDREG_MODE_OUT_OF_RANGE_HOLD, d))
                hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        } else {
            const int anchor_top = picture_testimony && picture_d == measured ?
                                   m->picture_top : m->top;
            const zero_observation_result zero_result =
                m->geometry_measurable && anchor_top >= 0 ?
                observe_gauge_zero(s, field, measured,
                                   FIELDREG_ZERO_PARITY, anchor_top) :
                ZERO_OBSERVATION_CANDIDATE;
            const bool anchor_ready =
                zero_result == ZERO_OBSERVATION_READY;
            zero_observation = m->geometry_measurable && anchor_top >= 0;
            d->measured_d = (int8_t)measured;
            d->applied_d = (int8_t)measured;
            d->reason = zero_result == ZERO_OBSERVATION_OUT_OF_BOUNDS ?
                        FIELDREG_MODE_ZERO_OUT_OF_BOUNDS :
                        zero_observation && !anchor_ready ?
                        FIELDREG_MODE_ZERO_CANDIDATE :
                        FIELDREG_MODE_LINE21_PLACEMENT;
            d->gauge = FIELDREG_GAUGE_CEA608_PARITY;
            s->last_applied = (int8_t)measured;
            if (anchor_ready) {
                update_gauge_geometry(s, m, measured);
                fit_clip(s, m, measured, anchor_top);
            }
            record_invariant(s, m, measured, d);
        }
    } else if (field == 1 && m->fallback_count > 1) {
        if (!apply_body_geometry(s, m, field,
                                 FIELDREG_MODE_LINE21_AMBIGUOUS, d))
            hold(s, d, FIELDREG_MODE_LINE21_AMBIGUOUS);
    } else if (field == 1 && m->fallback_count == 1) {
        const int measured = m->fallback_row - FIELDREG_INSERT_F2;
        if (!in_range(field, measured)) {
            if (!apply_body_geometry(s, m, field,
                                     FIELDREG_MODE_OUT_OF_RANGE_HOLD, d))
                hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        } else {
            const bool comb_zero = s->zero_source == FIELDREG_ZERO_COMB;
            int comb_placement = FIELDREG_UNKNOWN;
            const bool zero_conflict = comb_zero &&
                body_confirms_geometry(s, m, field, &comb_placement) &&
                comb_placement != measured;
            const zero_observation_result zero_result = comb_zero ?
                ZERO_OBSERVATION_READY : observe_gauge_zero(
                    s, field, measured, FIELDREG_ZERO_ENVELOPE, m->top);
            const bool anchor_ready =
                zero_result == ZERO_OBSERVATION_READY;
            zero_observation = true;
            d->measured_d = (int8_t)(zero_conflict ? comb_placement :
                                                     measured);
            d->applied_d = d->measured_d;
            d->reason = zero_conflict ?
                        FIELDREG_MODE_GEOMETRY_LOCK_DECIDES :
                        zero_result == ZERO_OBSERVATION_OUT_OF_BOUNDS ?
                        FIELDREG_MODE_ZERO_OUT_OF_BOUNDS :
                        !anchor_ready ? FIELDREG_MODE_ZERO_CANDIDATE :
                        FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT;
            d->gauge = zero_conflict ? FIELDREG_GAUGE_GEOMETRY :
                                      FIELDREG_GAUGE_FIELD2_ENVELOPE;
            d->gauge_row = m->fallback_row;
            s->last_applied = d->applied_d;
            if (!comb_zero && anchor_ready)
                update_gauge_geometry(s, m, measured);
            if (anchor_ready) fit_clip(s, m, measured, m->top);
            record_invariant(s, m, d->applied_d, d);
        }
    } else decide_geometry(s, m, field, d);

    if (!zero_observation) clear_zero_candidate(s);

    /* Motion for the next unit is anchored only to a position measured in
     * this unit. A held crop is presentation state, never evidence about
     * where the picture was. */
    if (m->picture_position_valid && d->measured_d != FIELDREG_UNKNOWN &&
        d->applied_d == m->picture_top - s->top)
        s->previous_measured_top = m->picture_top;
    else
        s->previous_measured_top = -1;
    copy_lock(s, d);
}

fieldreg_config fieldreg_default_config(void)
{
    fieldreg_config result = {0};
    return result;
}

size_t fieldreg_state_size(void) { return sizeof(field_registration); }
size_t fieldreg_config_size(void) { return sizeof(fieldreg_config); }
size_t fieldreg_decision_size(void) { return sizeof(fieldreg_decision); }
uint32_t fieldreg_algorithm_version(void) { return FIELDREG_ALGORITHM_VERSION; }
uint32_t fieldreg_confirmation_units(const field_registration *engine)
{
    (void)engine;
    return 1;
}
uint32_t fieldreg_buffer_units(const field_registration *engine)
{
    (void)engine;
    return 0;
}

static void reset_field(fieldreg_field_state *s, bool reset_applied, int field)
{
    const int8_t applied = reset_applied ? 0 : s->last_applied;
    const uint32_t lock_id = s->lock_id + 1;
    memset(s, 0, sizeof *s);
    s->top = s->height = -1;
    s->top = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                          FIELDREG_PICTURE_ORIGIN_F2;
    clear_clip(s);
    clear_zero_candidate(s);
    s->previous_measured_top = -1;
    s->last_applied = applied;
    s->lock_id = lock_id;
    s->lock_state = FIELDREG_LOCK_LOCKED;
    s->zero_source = FIELDREG_ZERO_STANDARD;
}

static void reset_parity(field_registration *engine)
{
    engine->parity_state = FIELDREG_PARITY_UNCALIBRATED;
    engine->comb_zero_candidate = INT16_MIN;
    engine->comb_candidate_count = 0;
    engine->comb_drift_shift = FIELDREG_UNKNOWN;
    engine->comb_drift_count = 0;
    engine->previous_luma_valid = false;
}

void fieldreg_init(field_registration *engine, const fieldreg_config *config)
{
    memset(engine, 0, sizeof *engine);
    engine->config = config ? *config : fieldreg_default_config();
    reset_field(&engine->field[0], true, 0);
    reset_field(&engine->field[1], true, 1);
    reset_parity(engine);
}

void fieldreg_begin_segment(field_registration *engine)
{
    ++engine->segment_id;
    reset_field(&engine->field[0], true, 0);
    reset_field(&engine->field[1], true, 1);
    reset_parity(engine);
}

void fieldreg_discontinuity(field_registration *engine)
{
    reset_field(&engine->field[0], false, 0);
    reset_field(&engine->field[1], false, 1);
    reset_parity(engine);
}

static bool field1_calibration_reference(const field_measurement *m,
                                         const fieldreg_field_decision *d)
{
    (void)m;
    return d->gauge == FIELDREG_GAUGE_CEA608_PARITY &&
           d->measured_d != FIELDREG_UNKNOWN &&
           d->applied_d == d->measured_d;
}

static bool field2_placed_on_zero(const field_registration *engine,
                                  const field_measurement *m,
                                  const fieldreg_field_decision *d)
{
    return m->picture_position_valid &&
           d->measured_d != FIELDREG_UNKNOWN &&
           d->applied_d == d->measured_d &&
           d->applied_d == m->picture_top - engine->field[1].top;
}

static bool zero_within_bound(int field, int top)
{
    const int standard = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                                      FIELDREG_PICTURE_ORIGIN_F2;
    return abs(top - standard) <= 3;
}

static void install_comb_zero(field_registration *engine,
                              const field_measurement *m,
                              fieldreg_decision *out, int16_t target_top)
{
    fieldreg_field_state *s = &engine->field[1];
    fieldreg_field_decision *d = &out->field[1];
    const bool physical_zero = s->zero_source == FIELDREG_ZERO_PARITY ||
                               s->zero_source == FIELDREG_ZERO_ENVELOPE;
    if (!zero_within_bound(1, target_top)) {
        d->reason = FIELDREG_MODE_ZERO_OUT_OF_BOUNDS;
        return;
    }
    const bool zero_conflict = physical_zero && target_top != s->top;
    if (target_top != s->top) clear_clip(s);
    s->top = target_top;
    s->zero_source = FIELDREG_ZERO_COMB;
    if (m->picture_position_valid) {
        const int measured = m->picture_top - s->top;
        if (crop_offset_valid(1, measured)) {
            d->measured_d = (int8_t)measured;
            d->applied_d = (int8_t)measured;
            d->geometry_d = (int8_t)measured;
            d->reason = zero_conflict ? FIELDREG_MODE_ZERO_CONFLICT :
                                        FIELDREG_MODE_FIELD2_COMB_CALIBRATION;
            d->gauge = FIELDREG_GAUGE_STATIC_COMB;
            s->last_applied = (int8_t)measured;
            record_invariant(s, m, measured, d);
        }
    }
    copy_lock(s, d);
}

static void update_parity_calibration(field_registration *engine,
                                      const uint8_t *raster,
                                      const field_measurement m[2],
                                      fieldreg_decision *out)
{
    out->comb_best_shift = FIELDREG_UNKNOWN;
    out->comb_check = FIELDREG_COMB_NOT_APPLICABLE;
    if (engine->parity_state == FIELDREG_PARITY_DRIFT) {
        engine->parity_state = FIELDREG_PARITY_UNCALIBRATED;
        engine->comb_zero_candidate = INT16_MIN;
        engine->comb_candidate_count = 0;
    }

    if (engine->parity_state == FIELDREG_PARITY_UNCALIBRATED) {
        const bool eligible = field1_calibration_reference(&m[0],
                                                            &out->field[0]) &&
                              field2_placed_on_zero(engine, &m[1],
                                                    &out->field[1]);
        comb_measurement comb = {0};
        if (eligible)
            comb = measure_static_comb(engine, raster, out->applied_d1,
                                       out->applied_d2, -3, 3);
        if (comb.best_shift != FIELDREG_UNKNOWN) {
            out->comb_best_shift = comb.best_shift;
            out->comb_best_energy = comb.best_energy;
            out->comb_second_energy = comb.second_energy;
            out->comb_static_fraction = comb.static_fraction;
        }
        if (eligible && comb.measurable) {
            const int16_t target_top = (int16_t)(m[1].picture_top -
                (out->applied_d2 + comb.best_shift));
            if (engine->comb_zero_candidate == target_top) {
                if (engine->comb_candidate_count < INT8_MAX)
                    ++engine->comb_candidate_count;
            } else {
                engine->comb_zero_candidate = target_top;
                engine->comb_candidate_count = 1;
            }
            if (engine->comb_candidate_count >= COMB_CALIBRATION_UNITS) {
                install_comb_zero(engine, &m[1], out, target_top);
                if (out->field[1].reason !=
                        FIELDREG_MODE_ZERO_OUT_OF_BOUNDS) {
                    engine->parity_state = FIELDREG_PARITY_CALIBRATED;
                    engine->comb_zero_candidate = INT16_MIN;
                    engine->comb_candidate_count = 0;
                    out->comb_check = FIELDREG_COMB_AGREE;
                } else {
                    out->comb_check = FIELDREG_COMB_DISAGREE;
                }
            }
        } else {
            engine->comb_zero_candidate = INT16_MIN;
            engine->comb_candidate_count = 0;
            if (eligible && comb.best_shift != FIELDREG_UNKNOWN)
                out->comb_check = FIELDREG_COMB_FLAT;
        }
    } else if (field1_calibration_reference(&m[0], &out->field[0]) &&
               field2_placed_on_zero(engine, &m[1], &out->field[1])) {
        const comb_measurement comb = measure_static_comb(
            engine, raster, out->applied_d1, out->applied_d2, -1, 1);
        if (comb.best_shift != FIELDREG_UNKNOWN) {
            out->comb_best_shift = comb.best_shift;
            out->comb_best_energy = comb.best_energy;
            out->comb_second_energy = comb.second_energy;
            out->comb_static_fraction = comb.static_fraction;
        }
        if (!comb.measurable) {
            out->comb_check = FIELDREG_COMB_FLAT;
            engine->comb_drift_count = 0;
            engine->comb_drift_shift = FIELDREG_UNKNOWN;
        } else if (comb.best_shift == 0) {
            out->comb_check = FIELDREG_COMB_AGREE;
            engine->comb_drift_count = 0;
            engine->comb_drift_shift = FIELDREG_UNKNOWN;
        } else {
            out->comb_check = FIELDREG_COMB_DISAGREE;
            const bool stable_field1 = field1_calibration_reference(
                &m[0], &out->field[0]);
            if (!stable_field1) {
                engine->comb_drift_count = 0;
                engine->comb_drift_shift = FIELDREG_UNKNOWN;
            } else if (engine->comb_drift_shift == comb.best_shift) {
                if (engine->comb_drift_count < INT8_MAX)
                    ++engine->comb_drift_count;
            } else {
                engine->comb_drift_shift = comb.best_shift;
                engine->comb_drift_count = 1;
            }
            if (engine->comb_drift_count >= COMB_DRIFT_UNITS)
                engine->parity_state = FIELDREG_PARITY_DRIFT;
        }
    } else {
        out->comb_check = FIELDREG_COMB_NOT_APPLICABLE;
        engine->comb_drift_count = 0;
        engine->comb_drift_shift = FIELDREG_UNKNOWN;
    }
    out->parity_state = engine->parity_state;
    out->parity_bias = (int8_t)(FIELDREG_PICTURE_ORIGIN_F2 -
                                engine->field[1].top);
}

bool fieldreg_process(field_registration *engine,
                      const uint8_t unit[FIELDREG_UNIT_BYTES],
                      fieldreg_decision *out)
{
    if (!engine || !out || !valid_unit(unit)) return false;
    memset(out, 0, sizeof *out);
    out->decision_d1 = out->decision_d2 = FIELDREG_UNKNOWN;
    out->frame_observation_d1 = out->frame_observation_d2 = FIELDREG_UNKNOWN;
    out->transport_ok = true;
    out->segment_id = engine->segment_id;
    const uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    field_measurement m[2];
    measure_field(raster, 0, &m[0]);
    measure_field(raster, 1, &m[1]);
    measure_body(raster, 0, engine->previous_luma,
                 engine->previous_luma_valid, &engine->field[0], &m[0]);
    measure_body(raster, 1, engine->previous_luma,
                 engine->previous_luma_valid, &engine->field[1], &m[1]);
    resolve_picture_positions(m);
    decide_field(&engine->field[0], &m[0], 0, &out->field[0]);
    decide_field(&engine->field[1], &m[1], 1, &out->field[1]);

    out->applied_d1 = out->field[0].applied_d;
    out->applied_d2 = out->field[1].applied_d;
    update_parity_calibration(engine, raster, m, out);

    out->applied_d1 = out->baseline_d1 = out->field[0].applied_d;
    out->applied_d2 = out->baseline_d2 = out->field[1].applied_d;
    out->decision_d1 = out->field[0].measured_d;
    out->decision_d2 = out->field[1].measured_d;
    out->frame_observation_d1 = out->decision_d1;
    out->frame_observation_d2 = out->decision_d2;
    out->frame_observation_support =
        (out->decision_d1 != FIELDREG_UNKNOWN) +
        (out->decision_d2 != FIELDREG_UNKNOWN);
    out->mode = out->field[0].reason == out->field[1].reason ?
                out->field[0].reason : FIELDREG_MODE_MIXED_FIELD_DECISION;
    out->confidence = out->frame_observation_support > 0 ? 1.0 : 0.0;
    const bool both_locked =
        engine->field[0].lock_state == FIELDREG_LOCK_LOCKED &&
        engine->field[1].lock_state == FIELDREG_LOCK_LOCKED;
    out->comb_safe = both_locked &&
                     engine->parity_state == FIELDREG_PARITY_CALIBRATED;
    copy_current_luma(engine, raster);
    return true;
}

const char *fieldreg_mode_name(fieldreg_mode mode)
{
    switch (mode) {
    case FIELDREG_MODE_INVALID_UNIT: return "InvalidUnit";
    case FIELDREG_MODE_ACQUIRING: return "Acquiring";
    case FIELDREG_MODE_LINE21_PLACEMENT: return "Line21Placement";
    case FIELDREG_MODE_GEOMETRY_LOCK_DECIDES: return "GeometryLockDecides";
    case FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT: return "Field2EnvelopePlacement";
    case FIELDREG_MODE_INSERT_ABSENT: return "InsertAbsent";
    case FIELDREG_MODE_GEOMETRY_UNMEASURABLE: return "GeometryUnmeasurable";
    case FIELDREG_MODE_LOCK_BROKEN: return "LockBroken";
    case FIELDREG_MODE_LINE21_AMBIGUOUS: return "Line21Ambiguous";
    case FIELDREG_MODE_OUT_OF_RANGE_HOLD: return "OutOfRangeHold";
    case FIELDREG_MODE_LINE22_DATA_PRESENT: return "Line22DataPresent";
    case FIELDREG_MODE_GAUGE_CONFLICT: return "GaugeConflict";
    case FIELDREG_MODE_CAPTION_ONLY_MOTION: return "CaptionOnlyMotion";
    case FIELDREG_MODE_CAPTION_BODY_DISAGREE: return "CaptionBodyDisagree";
    case FIELDREG_MODE_ANCHOR_UNCORROBORATED: return "AnchorUncorroborated";
    case FIELDREG_MODE_TOP_BODY_DISAGREE: return "TopBodyDisagree";
    case FIELDREG_MODE_BODY_ONLY_PLACEMENT: return "BodyOnlyPlacement";
    case FIELDREG_MODE_COMMON_MODE_BODY_HOLD: return "CommonModeBodyHold";
    case FIELDREG_MODE_FIELD2_COMB_CALIBRATION: return "Field2CombCalibration";
    case FIELDREG_MODE_ZERO_CONFLICT: return "ZeroConflict";
    case FIELDREG_MODE_ZERO_CANDIDATE: return "ZeroCandidate";
    case FIELDREG_MODE_ZERO_OUT_OF_BOUNDS: return "ZeroOutOfBounds";
    case FIELDREG_MODE_MIXED_FIELD_DECISION: return "MixedFieldDecision";
    }
    return "Unknown";
}

const char *fieldreg_gauge_name(fieldreg_gauge_source source)
{
    switch (source) {
    case FIELDREG_GAUGE_NONE: return "None";
    case FIELDREG_GAUGE_CEA608_PARITY: return "CEA608Parity";
    case FIELDREG_GAUGE_GEOMETRY: return "Geometry";
    case FIELDREG_GAUGE_FIELD2_ENVELOPE: return "Field2Envelope";
    case FIELDREG_GAUGE_LINE22_DATA: return "Line22Data";
    case FIELDREG_GAUGE_HOLD: return "Hold";
    case FIELDREG_GAUGE_STATIC_COMB: return "StaticComb";
    }
    return "Unknown";
}

const char *fieldreg_lock_state_name(fieldreg_lock_state state)
{
    switch (state) {
    case FIELDREG_LOCK_UNLOCKED: return "Unlocked";
    case FIELDREG_LOCK_LOCKED: return "Locked";
    }
    return "Unknown";
}

const char *fieldreg_clip_state_name(fieldreg_clip_state state)
{
    switch (state) {
    case FIELDREG_CLIP_UNKNOWN: return "ClipUnknown";
    case FIELDREG_CLIP_FITTING: return "ClipFitting";
    case FIELDREG_CLIP_FITTED: return "ClipFitted";
    }
    return "Unknown";
}

const char *fieldreg_zero_source_name(fieldreg_zero_source source)
{
    switch (source) {
    case FIELDREG_ZERO_NONE: return "None";
    case FIELDREG_ZERO_STANDARD: return "Standard";
    case FIELDREG_ZERO_PARITY: return "Parity";
    case FIELDREG_ZERO_ENVELOPE: return "Envelope";
    case FIELDREG_ZERO_COMB: return "Comb";
    }
    return "Unknown";
}

const char *fieldreg_parity_state_name(fieldreg_parity_state state)
{
    switch (state) {
    case FIELDREG_PARITY_UNCALIBRATED: return "Uncalibrated";
    case FIELDREG_PARITY_CALIBRATED: return "Calibrated";
    case FIELDREG_PARITY_DRIFT: return "Drift";
    }
    return "Unknown";
}

const char *fieldreg_comb_check_name(fieldreg_comb_check check)
{
    switch (check) {
    case FIELDREG_COMB_NOT_APPLICABLE: return "n.a.";
    case FIELDREG_COMB_AGREE: return "agree";
    case FIELDREG_COMB_DISAGREE: return "disagree";
    case FIELDREG_COMB_FLAT: return "flat";
    }
    return "unknown";
}

const char *fieldreg_insert_relation_name(fieldreg_insert_relation relation)
{
    switch (relation) {
    case FIELDREG_INSERT_RELATION_NONE: return "None";
    case FIELDREG_INSERT_CORROBORATES: return "InsertCorroborates";
    case FIELDREG_INSERT_CONTRADICTED: return "InsertContradicted";
    }
    return "Unknown";
}
