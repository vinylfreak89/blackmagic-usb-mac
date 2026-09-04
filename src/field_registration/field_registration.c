#include "field_registration.h"
#include "cea608.h"

#include <limits.h>
#include <math.h>
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
} field_measurement;

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

static bool field2_envelope(const uint8_t *raster, int row)
{
    double bins[48];
    if (row_bins(raster, row, bins, 48) >= 95.0) return false;
    for (int bin = 20; bin < 48; ++bin)
        if (bins[bin] > 40) return false;
    int run = 0;
    for (int bin = 0; bin < 20; ++bin) {
        if (bins[bin] > 60) {
            if (++run >= 6) return true;
        } else run = 0;
    }
    return false;
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
    return run_mean > 35.0 && run_mean < 90.0 && variance < 64.0 &&
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

static bool bar_like_damage(const uint8_t *raster, int row)
{
    double bins[48];
    if (row_bins(raster, row, bins, 48) >= 95.0) return false;
    for (int i = 20; i < 48; ++i)
        if (bins[i] > 40.0) return false;
    int run = 0;
    for (int i = 0; i < 20; ++i) {
        if (bins[i] > 60.0) {
            if (++run >= 4) return true;
        } else run = 0;
    }
    return false;
}

static bool top_interval_vbi_damage(const uint8_t *raster, int row, int field)
{
    const int first = field == 0 ? 16 : 279; /* NTSC 20 / 283 */
    const int last = field == 0 ? 26 : 289;  /* NTSC 30 / 293 */
    if (row < first || row > last) return false;
    return caption_like_damage(raster, row) ||
           timing_like_damage(raster, row) ||
           bar_like_damage(raster, row);
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
            !decoded.parity_valid &&
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
        if (!waveform[row - first] && means[row - first] > 12.0 &&
            !waveform[row + 1 - first] && means[row + 1 - first] > 12.0 &&
            !waveform[row + 2 - first] && means[row + 2 - first] > 12.0) {
            m->top = (int16_t)row;
            break;
        }
    }
    for (int row = adc_last; row >= picture_first; --row) {
        if (!waveform[row - first] && means[row - first] > 12.0) {
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

static void begin_acquisition(fieldreg_field_state *s,
                              const field_measurement *m, int applied,
                              fieldreg_zero_source zero_source)
{
    s->acquire_top = (int16_t)(m->top - applied);
    s->acquire_height = m->height;
    s->acquire_height_known = !m->bottom_censored;
    clear_clip(s);
    s->zero_source = zero_source;
    s->lock_state = FIELDREG_LOCK_ACQUIRE_ONE;
}

static bool acquisition_position_matches(const fieldreg_field_state *s,
                                         const field_measurement *m,
                                         int applied)
{
    return m->top - applied == s->acquire_top;
}

static bool merge_acquisition_height(fieldreg_field_state *s,
                                     const field_measurement *m)
{
    if (s->acquire_height_known && !m->bottom_censored &&
        m->height != s->acquire_height)
        return false;
    if (m->height > s->acquire_height)
        s->acquire_height = m->height;
    if (!m->bottom_censored && m->height >= s->acquire_height) {
        s->acquire_height = m->height;
        s->acquire_height_known = true;
    }
    return true;
}

static void finish_acquisition(fieldreg_field_state *s)
{
    s->top = s->acquire_top;
    s->height = s->acquire_height;
    s->height_known = s->acquire_height_known;
    s->lock_state = FIELDREG_LOCK_LOCKED;
    ++s->lock_id;
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

static void seed_from_gauge(fieldreg_field_state *s,
                            const field_measurement *m, int measured,
                            fieldreg_zero_source zero_source)
{
    if (!m->geometry_measurable) return;
    const int base_top = m->top - measured;
    if (s->lock_state == FIELDREG_LOCK_UNLOCKED) {
        begin_acquisition(s, m, measured, zero_source);
        return;
    }
    if (s->lock_state == FIELDREG_LOCK_ACQUIRE_ONE) {
        if (base_top != s->acquire_top)
            begin_acquisition(s, m, measured, zero_source);
        else {
            /* A golden gauge settles position even when clipping makes the
             * visible heights differ. Preserve the largest lower bound; only
             * equal uncensored heights establish exact H. */
            if (s->acquire_height_known && !m->bottom_censored &&
                m->height != s->acquire_height)
                s->acquire_height_known = false;
            if (m->height > s->acquire_height)
                s->acquire_height = m->height;
            s->zero_source = zero_source;
            finish_acquisition(s);
        }
        return;
    }

    if (base_top != s->top) {
        /* A physical gauge replaces a content-acquired zero immediately.
         * Keep H: the gauge identifies position, while a one-unit content
         * edge difference is not evidence that the frozen geometry changed. */
        s->top = (int16_t)base_top;
        s->zero_source = zero_source;
        return;
    }
    s->zero_source = zero_source;
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
                     int measured)
{
    if (s->lock_state == FIELDREG_LOCK_UNLOCKED ||
        !m->geometry_measurable || s->clip_ceiling >= 0)
        return;
    const int base_top = s->lock_state == FIELDREG_LOCK_LOCKED ?
                         s->top : s->acquire_top;
    if (m->top != base_top + measured) return;
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
    if (s->lock_state != FIELDREG_LOCK_LOCKED || !m->geometry_measurable)
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

static void decide_geometry(fieldreg_field_state *s,
                            const field_measurement *m, int field,
                            fieldreg_field_decision *d)
{
    if (!m->geometry_measurable) {
        hold(s, d, FIELDREG_MODE_GEOMETRY_UNMEASURABLE);
        return;
    }
    if (s->lock_state == FIELDREG_LOCK_UNLOCKED) {
        begin_acquisition(s, m, s->last_applied, FIELDREG_ZERO_ACQUIRED);
        hold(s, d, FIELDREG_MODE_ACQUIRING);
        return;
    }
    if (s->lock_state == FIELDREG_LOCK_ACQUIRE_ONE) {
        if (acquisition_position_matches(s, m, s->last_applied) &&
            merge_acquisition_height(s, m))
            finish_acquisition(s);
        else begin_acquisition(s, m, s->last_applied, FIELDREG_ZERO_ACQUIRED);
        hold(s, d, FIELDREG_MODE_ACQUIRING);
        return;
    }
    const int measured = m->top - s->top;
    if (!in_range(field, measured)) {
        hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        return;
    }
    if (measured != s->last_applied && s->clip_ceiling < 0 &&
        !m->bottom_censored &&
        field == 1 && s->zero_source != FIELDREG_ZERO_PARITY) {
        hold(s, d, FIELDREG_MODE_CLIP_UNKNOWN_HOLD);
        return;
    }
    if (!s->height_known) {
        const int lower_bottom = s->top + s->height - 1 + measured;
        if (!m->bottom_censored) {
            if (m->bottom < lower_bottom) {
                if (s->zero_source == FIELDREG_ZERO_ACQUIRED)
                    begin_acquisition(s, m, s->last_applied,
                                      FIELDREG_ZERO_ACQUIRED);
                hold(s, d, FIELDREG_MODE_LOCK_BROKEN);
                return;
            }
            s->height = (int16_t)(m->bottom - s->top - measured + 1);
            s->height_known = true;
        }
        d->measured_d = (int8_t)measured;
        d->applied_d = (int8_t)measured;
        d->reason = FIELDREG_MODE_GEOMETRY_LOCK_DECIDES;
        d->gauge = FIELDREG_GAUGE_GEOMETRY;
        d->expected_bottom = m->bottom;
        d->bottom_censored = m->bottom_censored;
        s->last_applied = (int8_t)measured;
        return;
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
        if (s->zero_source == FIELDREG_ZERO_ACQUIRED)
            begin_acquisition(s, m, s->last_applied, FIELDREG_ZERO_ACQUIRED);
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
    d->insert_present = m->insert_present;
    d->insert_byte1 = m->insert_byte1;
    d->insert_byte2 = m->insert_byte2;
    d->parity_candidate_count = m->off_count;
    d->fallback_candidate_count = m->fallback_count;
    if (s->lock_state == FIELDREG_LOCK_LOCKED && m->geometry_measurable)
        d->geometry_d = (int8_t)(m->top - s->top);
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
            hold(s, d, FIELDREG_MODE_GAUGE_CONFLICT);
            d->gauge = FIELDREG_GAUGE_CEA608_PARITY;
        } else if (!in_range(field, measured))
            hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        else {
            d->measured_d = (int8_t)measured;
            d->applied_d = (int8_t)measured;
            d->reason = FIELDREG_MODE_LINE21_PLACEMENT;
            d->gauge = FIELDREG_GAUGE_CEA608_PARITY;
            s->last_applied = (int8_t)measured;
            seed_from_gauge(s, m, measured, FIELDREG_ZERO_PARITY);
            fit_clip(s, m, measured);
            record_invariant(s, m, measured, d);
        }
    } else if (field == 1 && m->fallback_count > 1) {
        hold(s, d, FIELDREG_MODE_LINE21_AMBIGUOUS);
    } else if (field == 1 && m->fallback_count == 1) {
        const int measured = m->fallback_row - FIELDREG_INSERT_F2;
        if (!in_range(field, measured))
            hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        else {
            d->measured_d = (int8_t)measured;
            d->applied_d = (int8_t)measured;
            d->reason = FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT;
            d->gauge = FIELDREG_GAUGE_FIELD2_ENVELOPE;
            d->gauge_row = m->fallback_row;
            s->last_applied = (int8_t)measured;
            seed_from_gauge(s, m, measured, FIELDREG_ZERO_ENVELOPE);
            fit_clip(s, m, measured);
            record_invariant(s, m, measured, d);
        }
    } else decide_geometry(s, m, field, d);
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
    return 2;
}
uint32_t fieldreg_buffer_units(const field_registration *engine)
{
    (void)engine;
    return 0;
}

static void reset_field(fieldreg_field_state *s, bool reset_applied)
{
    const int8_t applied = reset_applied ? 0 : s->last_applied;
    const uint32_t lock_id = s->lock_id;
    memset(s, 0, sizeof *s);
    s->top = s->height = -1;
    s->acquire_top = s->acquire_height = -1;
    clear_clip(s);
    s->last_applied = applied;
    s->lock_id = lock_id;
    s->lock_state = FIELDREG_LOCK_UNLOCKED;
}

void fieldreg_init(field_registration *engine, const fieldreg_config *config)
{
    memset(engine, 0, sizeof *engine);
    engine->config = config ? *config : fieldreg_default_config();
    reset_field(&engine->field[0], true);
    reset_field(&engine->field[1], true);
}

void fieldreg_begin_segment(field_registration *engine)
{
    ++engine->segment_id;
    reset_field(&engine->field[0], true);
    reset_field(&engine->field[1], true);
}

void fieldreg_discontinuity(field_registration *engine)
{
    reset_field(&engine->field[0], false);
    reset_field(&engine->field[1], false);
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
    decide_field(&engine->field[0], &m[0], 0, &out->field[0]);
    decide_field(&engine->field[1], &m[1], 1, &out->field[1]);

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
    const bool both_physically_gauged =
        engine->field[0].zero_source != FIELDREG_ZERO_ACQUIRED &&
        engine->field[1].zero_source != FIELDREG_ZERO_ACQUIRED;
    const bool both_rigid_now =
        out->field[0].geometry_measurable &&
        out->field[1].geometry_measurable &&
        out->field[0].geometry_d != FIELDREG_UNKNOWN &&
        out->field[1].geometry_d != FIELDREG_UNKNOWN &&
        out->field[0].applied_d == out->field[0].geometry_d &&
        out->field[1].applied_d == out->field[1].geometry_d &&
        out->field[0].expected_bottom >= 0 &&
        out->field[1].expected_bottom >= 0 &&
        out->field[0].invariant_residual == 0 &&
        out->field[1].invariant_residual == 0;
    out->comb_safe = both_locked &&
                     (both_physically_gauged || both_rigid_now);
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
    case FIELDREG_MODE_CLIP_UNKNOWN_HOLD: return "ClipUnknownHold";
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
    }
    return "Unknown";
}

const char *fieldreg_lock_state_name(fieldreg_lock_state state)
{
    switch (state) {
    case FIELDREG_LOCK_UNLOCKED: return "Unlocked";
    case FIELDREG_LOCK_ACQUIRE_ONE: return "AcquireOne";
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
    case FIELDREG_ZERO_ACQUIRED: return "Acquired";
    case FIELDREG_ZERO_PARITY: return "Parity";
    case FIELDREG_ZERO_ENVELOPE: return "Envelope";
    }
    return "Unknown";
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
