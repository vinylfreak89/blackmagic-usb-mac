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

int main(void)
{
    field_registration engine;
    fieldreg_init(&engine, NULL);
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

    fieldreg_discontinuity(&engine);
    assert(!engine.previous_valid[0] && !engine.previous_valid[1]);
    assert(engine.band_total[0] == 12 && engine.band_total[1] == 12);

    /* A false content run before the real first-field fiducial must not move it. */
    make_unit(unit, 12);
    set_line(unit, 10, 80, 96, 160);
    set_line(unit, 11, 72, 96, 160);
    assert(fieldreg_process(&engine, unit, &decision));
    assert(!decision.transport_ok);
    assert(decision.mode == FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI);
    assert(decision.applied_d1 == 0 && decision.applied_d2 == 0);

    unit[6] = 0;
    assert(!fieldreg_process(&engine, unit, &decision));
    assert(decision.mode == FIELDREG_MODE_INVALID_UNIT);

    free(unit);
    printf("field_registration unit tests: PASS (state %zu bytes)\n", sizeof(engine));
    return 0;
}
