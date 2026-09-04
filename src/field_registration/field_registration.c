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
    bool bottom_at_adc_boundary;
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

static bool field2_envelope(const uint8_t *raster, int row)
{
    const uint8_t *line = raster + (size_t)row * FIELDREG_BYTES_PER_LINE;
    uint32_t total = 0;
    double bins[48];
    for (int bin = 0; bin < 48; ++bin) {
        const int first = 40 + (bin * 640) / 48;
        const int last = 40 + ((bin + 1) * 640) / 48;
        uint32_t sum = 0;
        for (int x = first; x < last; ++x) sum += line[x * 2 + 1];
        bins[bin] = (double)sum / (double)(last - first);
        total += sum;
    }
    if ((double)total / 640.0 >= 95.0) return false;
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

static void measure_field(const uint8_t *raster, int field,
                          field_measurement *m)
{
    const int first = field == 0 ? 8 : 268;   /* NTSC 12 / 272 */
    const int last = field == 0 ? 262 : 524;  /* NTSC 266 / 528 */
    const int insert = field == 0 ? FIELDREG_INSERT_F1 : FIELDREG_INSERT_F2;
    const int picture_first = field == 0 ? 18 : 281; /* NTSC 22 / 285 */
    const int adc_last = field == 0 ? 260 : 522;      /* NTSC 264 / 526 */
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

    for (int row = picture_first; row <= adc_last; ++row) {
        if (!waveform[row - first] && means[row - first] > 12.0) {
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
        m->bottom_at_adc_boundary = m->bottom == adc_last;
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
                              const field_measurement *m, int applied)
{
    s->acquire_top = (int16_t)(m->top - applied);
    s->acquire_height = m->height;
    s->acquire_height_known = !m->bottom_at_adc_boundary;
    clear_clip(s);
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
    if (s->acquire_height_known && !m->bottom_at_adc_boundary &&
        m->height != s->acquire_height)
        return false;
    if (m->height > s->acquire_height)
        s->acquire_height = m->height;
    if (!m->bottom_at_adc_boundary && m->height >= s->acquire_height) {
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
                            const field_measurement *m, int measured)
{
    if (!m->geometry_measurable) return;
    const int base_top = m->top - measured;
    if (s->lock_state == FIELDREG_LOCK_UNLOCKED) {
        begin_acquisition(s, m, measured);
        return;
    }
    if (s->lock_state == FIELDREG_LOCK_ACQUIRE_ONE) {
        if (base_top != s->acquire_top ||
            !merge_acquisition_height(s, m))
            begin_acquisition(s, m, measured);
        else finish_acquisition(s);
        return;
    }

    if (base_top != s->top) {
        begin_acquisition(s, m, measured);
        return;
    }
    if (!s->height_known) {
        const int lower_bottom = s->top + s->height - 1 + measured;
        if (!m->bottom_at_adc_boundary && m->bottom >= lower_bottom) {
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
    } else if (m->bottom <= uncensored_bottom) {
        /* With a golden gauge and unknown C, a short visible envelope can be
         * clipping. Top placement remains authoritative until C is fitted. */
        return;
    }
    begin_acquisition(s, m, measured);
}

static void fit_clip(fieldreg_field_state *s, const field_measurement *m,
                     int measured)
{
    if (s->lock_state == FIELDREG_LOCK_UNLOCKED ||
        !m->geometry_measurable || s->clip_ceiling >= 0)
        return;
    const int base_top = s->lock_state == FIELDREG_LOCK_LOCKED ?
                         s->top : s->acquire_top;
    const int height = s->lock_state == FIELDREG_LOCK_LOCKED ?
                       s->height : s->acquire_height;
    const bool height_known = s->lock_state == FIELDREG_LOCK_LOCKED ?
                              s->height_known : s->acquire_height_known;
    if (m->top != base_top + measured) return;
    const int predicted = base_top + height - 1 + measured;
    if (!m->bottom_at_adc_boundary &&
        (!height_known || m->bottom >= predicted)) {
        s->clip_candidate = -1;
        s->clip_candidate_d = FIELDREG_UNKNOWN;
        s->clip_candidate_count = 0;
        return;
    }
    if (s->clip_candidate == m->bottom &&
        s->clip_candidate_d != measured) {
        if (s->clip_candidate_count < UINT8_MAX) ++s->clip_candidate_count;
        s->clip_candidate_d = (int8_t)measured;
    } else {
        s->clip_candidate = m->bottom;
        s->clip_candidate_d = (int8_t)measured;
        s->clip_candidate_count = 1;
    }
    if (s->clip_candidate_count >= 2)
        s->clip_ceiling = s->clip_candidate;
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
                         (!s->height_known && m->bottom_at_adc_boundary);
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
        begin_acquisition(s, m, s->last_applied);
        hold(s, d, FIELDREG_MODE_ACQUIRING);
        return;
    }
    if (s->lock_state == FIELDREG_LOCK_ACQUIRE_ONE) {
        if (acquisition_position_matches(s, m, s->last_applied) &&
            merge_acquisition_height(s, m))
            finish_acquisition(s);
        else begin_acquisition(s, m, s->last_applied);
        hold(s, d, FIELDREG_MODE_ACQUIRING);
        return;
    }
    const int measured = m->top - s->top;
    if (!in_range(field, measured)) {
        hold(s, d, FIELDREG_MODE_OUT_OF_RANGE_HOLD);
        return;
    }
    if (!s->height_known) {
        if (m->height > s->height) s->height = m->height;
        if (!m->bottom_at_adc_boundary) {
            s->height = m->height;
            s->height_known = true;
        }
    }
    const int uncensored = s->top + s->height - 1 + measured;
    const int expected = s->clip_ceiling >= 0 && uncensored > s->clip_ceiling ?
                         s->clip_ceiling : uncensored;
    d->expected_bottom = (int16_t)expected;
    d->lines_lost = (int16_t)(uncensored - expected);
    d->invariant_residual = (int16_t)(m->bottom - expected);
    d->bottom_censored = d->lines_lost > 0;
    const bool unknown_clip_at_boundary = s->clip_ceiling < 0 &&
                                          m->bottom_at_adc_boundary &&
                                          m->bottom <= uncensored;
    if (d->invariant_residual != 0 && !unknown_clip_at_boundary) {
        begin_acquisition(s, m, s->last_applied);
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

    if (!m->insert_present) {
        s->lock_state = FIELDREG_LOCK_UNLOCKED;
        hold(s, d, FIELDREG_MODE_INSERT_ABSENT);
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
        if (measured == 1 && insert_nonnull) {
            if (d->geometry_d != FIELDREG_UNKNOWN && d->geometry_d != 0) {
                hold(s, d, FIELDREG_MODE_GAUGE_CONFLICT);
                d->gauge = FIELDREG_GAUGE_CEA608_PARITY;
            } else {
                d->measured_d = 0;
                d->applied_d = 0;
                d->reason = FIELDREG_MODE_LINE22_DATA_PRESENT;
                d->gauge = FIELDREG_GAUGE_LINE22_DATA;
                s->last_applied = 0;
                seed_from_gauge(s, m, 0);
                fit_clip(s, m, 0);
                record_invariant(s, m, 0, d);
            }
        } else if (d->geometry_d != FIELDREG_UNKNOWN &&
                   (measured - d->geometry_d == 1 ||
                    d->geometry_d - measured == 1)) {
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
            seed_from_gauge(s, m, measured);
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
            seed_from_gauge(s, m, measured);
            fit_clip(s, m, measured);
            record_invariant(s, m, measured, d);
        }
    } else if (m->insert_byte1 != 0x80 || m->insert_byte2 != 0x80) {
        d->gauge_row = field == 0 ? FIELDREG_INSERT_F1 : FIELDREG_INSERT_F2;
        d->gauge_byte1 = m->insert_byte1;
        d->gauge_byte2 = m->insert_byte2;
        if (s->lock_state == FIELDREG_LOCK_LOCKED &&
            (!m->geometry_measurable || d->geometry_d != 0)) {
            hold(s, d, m->geometry_measurable ?
                 FIELDREG_MODE_INSERT_GEOMETRY_CONFLICT :
                 FIELDREG_MODE_GEOMETRY_UNMEASURABLE);
            d->gauge = FIELDREG_GAUGE_INSERT_DATA;
        } else {
            d->measured_d = 0;
            d->applied_d = 0;
            d->reason = FIELDREG_MODE_ALIGNED_CORROBORATED;
            d->gauge = FIELDREG_GAUGE_INSERT_DATA;
            s->last_applied = 0;
            seed_from_gauge(s, m, 0);
            fit_clip(s, m, 0);
            record_invariant(s, m, 0, d);
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
    out->confidence = out->frame_observation_support == 2 ? 1.0 :
                      out->frame_observation_support == 1 ? 0.9 : 0.0;
    out->comb_safe = engine->field[0].lock_state == FIELDREG_LOCK_LOCKED &&
                     engine->field[1].lock_state == FIELDREG_LOCK_LOCKED;
    return true;
}

const char *fieldreg_mode_name(fieldreg_mode mode)
{
    switch (mode) {
    case FIELDREG_MODE_INVALID_UNIT: return "InvalidUnit";
    case FIELDREG_MODE_ACQUIRING: return "Acquiring";
    case FIELDREG_MODE_LINE21_PLACEMENT: return "Line21Placement";
    case FIELDREG_MODE_ALIGNED_CORROBORATED: return "AlignedCorroborated";
    case FIELDREG_MODE_GEOMETRY_LOCK_DECIDES: return "GeometryLockDecides";
    case FIELDREG_MODE_FIELD2_ENVELOPE_PLACEMENT: return "Field2EnvelopePlacement";
    case FIELDREG_MODE_INSERT_ABSENT: return "InsertAbsent";
    case FIELDREG_MODE_GEOMETRY_UNMEASURABLE: return "GeometryUnmeasurable";
    case FIELDREG_MODE_LOCK_BROKEN: return "LockBroken";
    case FIELDREG_MODE_LINE21_AMBIGUOUS: return "Line21Ambiguous";
    case FIELDREG_MODE_OUT_OF_RANGE_HOLD: return "OutOfRangeHold";
    case FIELDREG_MODE_INSERT_GEOMETRY_CONFLICT: return "InsertGeometryConflict";
    case FIELDREG_MODE_LINE22_DATA_PRESENT: return "Line22DataPresent";
    case FIELDREG_MODE_GAUGE_CONFLICT: return "GaugeConflict";
    case FIELDREG_MODE_MIXED_FIELD_DECISION: return "MixedFieldDecision";
    }
    return "Unknown";
}

const char *fieldreg_gauge_name(fieldreg_gauge_source source)
{
    switch (source) {
    case FIELDREG_GAUGE_NONE: return "None";
    case FIELDREG_GAUGE_CEA608_PARITY: return "CEA608Parity";
    case FIELDREG_GAUGE_INSERT_DATA: return "InsertData";
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
