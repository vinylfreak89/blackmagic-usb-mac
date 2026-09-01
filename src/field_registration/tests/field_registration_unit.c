#include "../field_registration.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void set_line(uint8_t *unit, int line, uint8_t y, uint8_t u, uint8_t v)
{
    uint8_t *dst = unit + FIELDREG_HEADER_BYTES +
                   (size_t)line * FIELDREG_BYTES_PER_LINE;
    for (int x = 0; x < 720; x += 2) {
        *dst++ = u;
        *dst++ = (uint8_t)(y + ((x / 2 + line) % 7));
        *dst++ = v;
        *dst++ = (uint8_t)(y + ((x / 2 + line + 3) % 7));
    }
}

static void set_flat_line(uint8_t *unit, int line, uint8_t y, uint8_t u, uint8_t v)
{
    uint8_t *dst = unit + FIELDREG_HEADER_BYTES +
                   (size_t)line * FIELDREG_BYTES_PER_LINE;
    for (int x = 0; x < 720; x += 2) {
        *dst++ = u;
        *dst++ = y;
        *dst++ = v;
        *dst++ = y;
    }
}

static void make_unit(uint8_t *unit, uint16_t counter)
{
    memset(unit, 0, FIELDREG_UNIT_BYTES);
    unit[2] = 0xff;
    unit[3] = 0xff;
    unit[4] = (uint8_t)counter;
    unit[5] = (uint8_t)(counter >> 8);
    unit[6] = 0x01;
    unit[7] = 0xe8;

    for (int line = 0; line < FIELDREG_RASTER_LINES; ++line)
        set_line(unit, line, 2, 128, 128);
    for (int line = 0; line < 7; ++line)
        set_flat_line(unit, line, 16, 128, 128);
    for (int line = 261; line < 270; ++line)
        set_flat_line(unit, line, 16, 128, 128);
    for (int line = 523; line < 525; ++line)
        set_flat_line(unit, line, 16, 128, 128);

    /* Two-line VBI signatures yield transport fiducials 17 and 280. */
    set_line(unit, 16, 80, 96, 160);
    set_line(unit, 17, 72, 96, 160);
    set_line(unit, 279, 80, 96, 160);
    set_line(unit, 280, 72, 96, 160);

    /* Three-line picture starts are 19 and 282 (the learned band baseline). */
    for (int line = 19; line <= 256; ++line)
        set_line(unit, line, (uint8_t)(38 + line % 83), 110, 145);
    for (int line = 282; line <= 518; ++line)
        set_line(unit, line, (uint8_t)(38 + (line - 263) % 83), 110, 145);
}

static void shift_first_picture_down_one(uint8_t *unit)
{
    uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    memmove(raster + (size_t)20 * FIELDREG_BYTES_PER_LINE,
            raster + (size_t)19 * FIELDREG_BYTES_PER_LINE,
            (size_t)(257 - 19) * FIELDREG_BYTES_PER_LINE);
    set_line(unit, 19, 2, 128, 128);
}

static void shift_picture_up(uint8_t *unit, int top, int bottom, int lines)
{
    uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    memmove(raster + (size_t)top * FIELDREG_BYTES_PER_LINE,
            raster + (size_t)(top + lines) * FIELDREG_BYTES_PER_LINE,
            (size_t)(bottom - top + 1 - lines) * FIELDREG_BYTES_PER_LINE);
    for (int line = bottom - lines + 1; line <= bottom; ++line)
        set_line(unit, line, 2, 128, 128);
}

static void match_second_field(uint8_t *unit)
{
    uint8_t *raster = unit + FIELDREG_HEADER_BYTES;
    memcpy(raster + (size_t)FIELDREG_FIELD2_START * FIELDREG_BYTES_PER_LINE,
           raster + (size_t)FIELDREG_FIELD1_START * FIELDREG_BYTES_PER_LINE,
           (size_t)FIELDREG_FIELD_LINES * FIELDREG_BYTES_PER_LINE);
}

static void texture_first_field(uint8_t *unit)
{
    for (int line = 19; line <= 256; ++line) {
        int row = line - 19;
        uint8_t y = (uint8_t)(32 + (row * 37 + row * row * 11) % 180);
        set_line(unit, line, y, 110, 145);
    }
}

int main(void)
{
    assert(fieldreg_state_size() == sizeof(field_registration));
    assert(fieldreg_config_size() == sizeof(fieldreg_config));
    assert(fieldreg_decision_size() == sizeof(fieldreg_decision));
    assert(fieldreg_algorithm_version() == FIELDREG_ALGORITHM_VERSION);
    field_registration engine;
    fieldreg_config config = fieldreg_default_config();
    assert(config.evidence_model == FIELDREG_EVIDENCE_MOTION_PHASE);
    /* The first block preserves the legacy absolute-edge regression tests. */
    config.evidence_model = FIELDREG_EVIDENCE_DUAL_EDGE;
    fieldreg_init(&engine, &config);
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    assert(unit);

    fieldreg_decision decision;
    for (uint16_t counter = 0; counter < 12; ++counter) {
        make_unit(unit, counter);
        assert(fieldreg_process(&engine, unit, &decision));
        assert(decision.applied_d1 == 0 && decision.applied_d2 == 0);
        assert(decision.transport_ok);
        assert(decision.observed_transport_f1 == FIELDREG_FIELD1_START);
        assert(decision.observed_transport_f2 == FIELDREG_FIELD2_START);
        if (counter < 8)
            assert(decision.mode == FIELDREG_MODE_UNKNOWN_WARMUP_HOLD);
        else
            assert(decision.mode == FIELDREG_MODE_STABLE);
    }

    /* Strong, coherent top+bottom evidence may correct a real one-unit jump. */
    make_unit(unit, 12);
    shift_first_picture_down_one(unit);
    assert(fieldreg_process(&engine, unit, &decision));
    assert(decision.picture_top_f1 == 20 && decision.picture_bottom_f1 == 257);
    assert(decision.dual_edge_agreement);
    assert(decision.applied_d1 == 1 && decision.applied_d2 == 0);
    assert(decision.mode == FIELDREG_MODE_CONVERGED_RELATIVE_BAND);

    /* A source-carried top-line feature alone is not a registration event. */
    make_unit(unit, 13);
    shift_first_picture_down_one(unit);
    /* Restore the bottom edge, leaving only the top landmark displaced. */
    memcpy(unit + FIELDREG_HEADER_BYTES +
               (size_t)257 * FIELDREG_BYTES_PER_LINE,
           unit + FIELDREG_HEADER_BYTES +
               (size_t)258 * FIELDREG_BYTES_PER_LINE,
           FIELDREG_BYTES_PER_LINE);
    set_line(unit, 258, 2, 128, 128);
    assert(fieldreg_process(&engine, unit, &decision));
    assert(!decision.dual_edge_agreement);
    assert(decision.applied_d1 == 1 && decision.applied_d2 == 0);
    assert(decision.mode == FIELDREG_MODE_UNKNOWN_BAND_DISAGREEMENT);

    fieldreg_discontinuity(&engine);
    assert(!engine.previous_valid[0] && !engine.previous_valid[1]);
    assert(engine.band_total[0][0] == 14 && engine.band_total[1][0] == 14);
    assert(engine.band_total[0][1] == 14 && engine.band_total[1][1] == 14);

    /* A false content run before the real first-field fiducial must not move it. */
    make_unit(unit, 14);
    set_line(unit, 10, 80, 96, 160);
    set_line(unit, 11, 72, 96, 160);
    assert(fieldreg_process(&engine, unit, &decision));
    assert(!decision.transport_ok);
    assert(decision.mode == FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI);
    assert(decision.applied_d1 == 1 && decision.applied_d2 == 0);

    unit[6] = 0;
    assert(!fieldreg_process(&engine, unit, &decision));
    assert(decision.mode == FIELDREG_MODE_INVALID_UNIT);

    fieldreg_begin_segment(&engine);
    assert(engine.frames_seen == 0);
    assert(engine.band_total[0][0] == 0 && engine.band_total[1][1] == 0);
    assert(engine.selected[0] == 0 && engine.selected[1] == 0);

    /* Motion-phase mode derives relative phase without a mutable edge gauge. */
    config.evidence_model = FIELDREG_EVIDENCE_MOTION_PHASE;
    fieldreg_init(&engine, &config);
    for (uint16_t counter = 20; counter <= 169; ++counter) {
        make_unit(unit, counter);
        texture_first_field(unit);
        match_second_field(unit);
        assert(fieldreg_process(&engine, unit, &decision));
    }
    assert(decision.phase_support == 3);
    int baseline_phase = decision.phase_consensus;
    int baseline_d1 = decision.applied_d1;
    int baseline_d2 = decision.applied_d2;
    assert(baseline_phase != FIELDREG_UNKNOWN);
    assert(decision.selected_relative == baseline_phase);

    /* A fast absolute edge vote is logged but cannot move production state. */
    make_unit(unit, 170);
    texture_first_field(unit);
    match_second_field(unit);
    shift_first_picture_down_one(unit);
    assert(fieldreg_process(&engine, unit, &decision));
    assert(decision.fast_edge_d1 == 1 && decision.fast_edge_d2 == 0);
    assert(decision.mode == FIELDREG_MODE_UNKNOWN_EDGE_TRANSIENT);
    assert(decision.decision_d1 == FIELDREG_UNKNOWN);
    assert(decision.applied_d1 == baseline_d1 &&
           decision.applied_d2 == baseline_d2);

    /* A persistent one-line first-field phase moves that field, not field 2. */
    make_unit(unit, 171);
    texture_first_field(unit);
    match_second_field(unit);
    shift_first_picture_down_one(unit);
    assert(fieldreg_process(&engine, unit, &decision));
    for (uint16_t counter = 172; counter <= 310; ++counter) {
        make_unit(unit, counter);
        texture_first_field(unit);
        match_second_field(unit);
        shift_first_picture_down_one(unit);
        assert(fieldreg_process(&engine, unit, &decision));
    }
    assert(decision.phase_support == 3);
    assert(decision.phase_consensus == baseline_phase - 1);
    assert(decision.selected_relative == baseline_phase - 1);
    assert(decision.mode == FIELDREG_MODE_STABLE_MOTION_PHASE ||
           decision.mode == FIELDREG_MODE_CONVERGED_MOTION_PHASE);

    /* A motion minimum clipped at +/-6 is censored and must abstain. */
    fieldreg_begin_segment(&engine);
    make_unit(unit, 400);
    texture_first_field(unit);
    match_second_field(unit);
    assert(fieldreg_process(&engine, unit, &decision));
    make_unit(unit, 401);
    texture_first_field(unit);
    match_second_field(unit);
    shift_picture_up(unit, 19, 256, 6);
    shift_picture_up(unit, 282, 518, 6);
    assert(fieldreg_process(&engine, unit, &decision));
    assert(decision.phase_motion_left == FIELDREG_UNKNOWN);
    assert(decision.phase_motion_center == FIELDREG_UNKNOWN);
    assert(decision.phase_motion_right == FIELDREG_UNKNOWN);

    free(unit);
    printf("field_registration unit tests: PASS (state %zu bytes)\n", sizeof(engine));
    return 0;
}
