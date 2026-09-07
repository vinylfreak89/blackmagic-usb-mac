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

    /* Geometry is measured independently of every caption/fallback result.
     * Recognised VBI rows are excluded by their own waveform, never because
     * a caption told the scan where to begin. */
    for (int row = picture_first; row + 2 <= adc_last; ++row) {
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


static bool crop_fits_raster(int field, int displacement)
{
    const int start = field == 0 ? FIELDREG_FIELD1_START :
                                   FIELDREG_FIELD2_START;
    const int low = -start;
    const int high = FIELDREG_RASTER_LINES - FIELDREG_FIELD_LINES - start;
    return displacement >= low && displacement <= high &&
           displacement >= INT8_MIN && displacement <= INT8_MAX;
}

static void v10_reset_field(fieldreg_field_state *state, bool reset_applied,
                            int field)
{
    const int8_t applied = reset_applied ? 0 : state->last_applied;
    const uint32_t lock_id = state->lock_id + 1;
    memset(state, 0, sizeof *state);
    state->top = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                              FIELDREG_PICTURE_ORIGIN_F2;
    state->height = -1;
    state->clip_ceiling = -1;
    state->clip_candidate = -1;
    state->zero_candidate = INT16_MIN;
    state->clip_candidate_d = FIELDREG_UNKNOWN;
    state->previous_measured_top = -1;
    state->last_applied = applied;
    /* Acquisition semantics are implemented by rules 5-6.  Until then the
     * inherited standard origin is exposed as state, never as authority over
     * a measurable current-unit edge. */
    state->lock_state = FIELDREG_LOCK_LOCKED;
    state->zero_source = FIELDREG_ZERO_STANDARD;
    state->lock_id = lock_id;
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

void fieldreg_init(field_registration *engine, const fieldreg_config *config)
{
    memset(engine, 0, sizeof *engine);
    engine->config = config ? *config : fieldreg_default_config();
    v10_reset_field(&engine->field[0], true, 0);
    v10_reset_field(&engine->field[1], true, 1);
    engine->parity_state = FIELDREG_PARITY_UNCALIBRATED;
    engine->comb_zero_candidate = INT16_MIN;
    engine->comb_correction_candidate = FIELDREG_UNKNOWN;
}

void fieldreg_begin_segment(field_registration *engine)
{
    ++engine->segment_id;
    v10_reset_field(&engine->field[0], true, 0);
    v10_reset_field(&engine->field[1], true, 1);
    engine->previous_luma_valid = false;
    engine->parity_state = FIELDREG_PARITY_UNCALIBRATED;
    engine->comb_zero_candidate = INT16_MIN;
    engine->comb_candidate_count = 0;
    engine->comb_correction = 0;
    engine->comb_correction_candidate = FIELDREG_UNKNOWN;
    engine->comb_correction_candidate_count = 0;
}

void fieldreg_discontinuity(field_registration *engine)
{
    /* Rule 5 will distinguish transport damage from lock-like loss.  Rule 1
     * only guarantees that stale temporal observations cannot place a unit. */
    engine->previous_luma_valid = false;
    engine->field[0].previous_measured_top = -1;
    engine->field[1].previous_measured_top = -1;
}

static void v10_copy_state(const fieldreg_field_state *state,
                           fieldreg_field_decision *decision)
{
    decision->lock_state = state->lock_state;
    decision->zero_source = state->zero_source;
    decision->lock_id = state->lock_id;
    decision->lock_top = state->top;
    decision->lock_height = state->height;
    decision->lock_height_known = state->height_known;
    decision->clip_state = FIELDREG_CLIP_UNKNOWN;
    decision->clip_ceiling = -1;
}

static fieldreg_confirmation caption_confirmation(
    const field_measurement *measurement, int field, int geometry_d,
    fieldreg_field_decision *decision)
{
    if (measurement->off_count > 1)
        return FIELDREG_CONFIRM_AMBIGUOUS;
    if (measurement->off_count == 1) {
        const int insert = field == 0 ? FIELDREG_INSERT_F1 :
                                        FIELDREG_INSERT_F2;
        const int caption_d = measurement->off_candidate.raster_row - insert;
        decision->gauge_row = measurement->off_candidate.raster_row;
        decision->gauge_byte1 = measurement->off_candidate.byte1;
        decision->gauge_byte2 = measurement->off_candidate.byte2;
        decision->gauge_amplitude = measurement->off_candidate.amplitude;
        if (geometry_d == FIELDREG_UNKNOWN)
            return FIELDREG_CONFIRM_AMBIGUOUS;
        return caption_d == geometry_d ? FIELDREG_CONFIRM_AGREES :
                                         FIELDREG_CONFIRM_DISAGREES;
    }
    if (measurement->insert_present &&
        (measurement->insert_byte1 != 0x80 ||
         measurement->insert_byte2 != 0x80))
        return FIELDREG_CONFIRM_AMBIGUOUS;
    return FIELDREG_CONFIRM_NOT_APPLICABLE;
}

static void v10_decide_field(fieldreg_field_state *state,
                             const field_measurement *measurement, int field,
                             fieldreg_field_decision *decision)
{
    memset(decision, 0, sizeof *decision);
    decision->measured_d = FIELDREG_UNKNOWN;
    decision->geometry_d = FIELDREG_UNKNOWN;
    decision->gauge_row = -1;
    decision->expected_bottom = -1;
    decision->raw_top = measurement->top;
    decision->raw_bottom = measurement->bottom;
    decision->raw_height = measurement->height;
    decision->geometry_measurable = measurement->geometry_measurable;
    decision->blank_mean = measurement->blank_mean;
    decision->body_shift = FIELDREG_UNKNOWN;
    decision->body_reference_top = state->previous_measured_top;
    decision->body_implied_top = -1;
    decision->measured_picture_top = measurement->top;
    decision->picture_position_valid = measurement->geometry_measurable;
    decision->insert_present = measurement->insert_present;
    decision->insert_byte1 = measurement->insert_byte1;
    decision->insert_byte2 = measurement->insert_byte2;
    decision->parity_candidate_count = measurement->off_count;
    decision->fallback_candidate_count = measurement->fallback_count;

    const int origin = field == 0 ? FIELDREG_PICTURE_ORIGIN_F1 :
                                    FIELDREG_PICTURE_ORIGIN_F2;
    if (measurement->geometry_measurable) {
        const int geometry_d = measurement->top - origin;
        if (crop_fits_raster(field, geometry_d)) {
            decision->geometry_d = (int8_t)geometry_d;
            decision->measured_d = (int8_t)geometry_d;
            decision->applied_d = (int8_t)geometry_d;
            decision->reason = FIELDREG_MODE_GEOMETRY_PLACEMENT;
            decision->gauge = FIELDREG_GAUGE_GEOMETRY;
            state->last_applied = (int8_t)geometry_d;
            state->previous_measured_top = measurement->top;
        } else {
            decision->applied_d = state->last_applied;
            decision->reason = FIELDREG_MODE_OUT_OF_RANGE_HOLD;
            decision->gauge = FIELDREG_GAUGE_HOLD;
            state->previous_measured_top = -1;
        }
    } else {
        decision->applied_d = state->last_applied;
        decision->reason = FIELDREG_MODE_GEOMETRY_UNMEASURABLE;
        decision->gauge = FIELDREG_GAUGE_HOLD;
        state->previous_measured_top = -1;
    }

    decision->caption_confirmation = caption_confirmation(
        measurement, field, decision->geometry_d, decision);
    v10_copy_state(state, decision);
}

bool fieldreg_process(field_registration *engine,
                      const uint8_t unit[FIELDREG_UNIT_BYTES],
                      fieldreg_decision *out)
{
    if (!engine || !out || !valid_unit(unit)) return false;
    memset(out, 0, sizeof *out);
    out->decision_d1 = out->decision_d2 = FIELDREG_UNKNOWN;
    out->frame_observation_d1 = out->frame_observation_d2 = FIELDREG_UNKNOWN;
    out->comb_best_shift = FIELDREG_UNKNOWN;
    out->transport_ok = true;
    out->segment_id = engine->segment_id;
    out->parity_state = engine->parity_state;
    out->comb_check = FIELDREG_COMB_NOT_APPLICABLE;

    const uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    field_measurement measurement[2];
    measure_field(raster, 0, &measurement[0]);
    measure_field(raster, 1, &measurement[1]);
    v10_decide_field(&engine->field[0], &measurement[0], 0,
                     &out->field[0]);
    v10_decide_field(&engine->field[1], &measurement[1], 1,
                     &out->field[1]);

    out->applied_d1 = out->field[0].applied_d;
    out->applied_d2 = out->field[1].applied_d;
    out->baseline_d1 = out->applied_d1;
    out->baseline_d2 = out->applied_d2;
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
    return true;
}

const char *fieldreg_mode_name(fieldreg_mode mode)
{
    switch (mode) {
    case FIELDREG_MODE_INVALID_UNIT: return "InvalidUnit";
    case FIELDREG_MODE_ACQUIRING: return "Acquiring";
    case FIELDREG_MODE_GEOMETRY_PLACEMENT: return "GeometryPlacement";
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
    case FIELDREG_MODE_TOP_UNCORROBORATED: return "TopUncorroborated";
    case FIELDREG_MODE_TOP_COMB_CORROBORATED: return "TopCombCorroborated";
    case FIELDREG_MODE_TOP_COMB_VETOED: return "TopCombVetoed";
    case FIELDREG_MODE_TOP_ONLY: return "TopOnly";
    case FIELDREG_MODE_COMB_RELATIVE_CORRECTION: return "CombRelativeCorrection";
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

const char *fieldreg_confirmation_name(fieldreg_confirmation confirmation)
{
    switch (confirmation) {
    case FIELDREG_CONFIRM_NOT_APPLICABLE: return "n.a.";
    case FIELDREG_CONFIRM_AGREES: return "agrees";
    case FIELDREG_CONFIRM_DISAGREES: return "disagrees";
    case FIELDREG_CONFIRM_AMBIGUOUS: return "ambiguous";
    }
    return "unknown";
}
