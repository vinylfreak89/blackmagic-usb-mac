#include "../field_registration.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t *blank_unit(void)
{
    uint8_t *unit = calloc(1, FIELDREG_UNIT_BYTES);
    assert(unit);
    memcpy(unit, "\x00\x00\xff\xff", 4);
    unit[6] = 0x01;
    unit[7] = 0xe8;
    for (size_t i = FIELDREG_HEADER_BYTES; i < FIELDREG_UNIT_BYTES; i += 2) {
        unit[i] = 128;
        unit[i + 1] = 2;
    }
    return unit;
}

int main(void)
{
    assert(fieldreg_algorithm_version() == 9);
    assert(fieldreg_state_size() == sizeof(field_registration));
    assert(fieldreg_state_size() < 1024);
    assert(fieldreg_config_size() == sizeof(fieldreg_config));
    assert(fieldreg_decision_size() == sizeof(fieldreg_decision));
    field_registration engine;
    fieldreg_config config = fieldreg_default_config();
    fieldreg_init(&engine, &config);
    assert(fieldreg_confirmation_units(&engine) == 2);
    assert(fieldreg_buffer_units(&engine) == 0);
    uint8_t *unit = blank_unit();
    fieldreg_decision decision;
    assert(fieldreg_process(&engine, unit, &decision));
    assert(decision.transport_ok);
    assert(decision.applied_d1 == 0 && decision.applied_d2 == 0);
    assert(decision.field[0].reason == FIELDREG_MODE_INSERT_ABSENT);
    assert(decision.field[1].reason == FIELDREG_MODE_INSERT_ABSENT);
    unit[6] = 0;
    assert(!fieldreg_process(&engine, unit, &decision));
    fieldreg_discontinuity(&engine);
    assert(engine.field[0].lock_state == FIELDREG_LOCK_UNLOCKED);
    fieldreg_begin_segment(&engine);
    assert(engine.segment_id == 1 && engine.field[0].last_applied == 0);
    assert(strcmp(fieldreg_mode_name(FIELDREG_MODE_LINE21_PLACEMENT),
                  "Line21Placement") == 0);
    assert(strcmp(fieldreg_gauge_name(FIELDREG_GAUGE_CEA608_PARITY),
                  "CEA608Parity") == 0);
    free(unit);
    printf("FIELDREG-UNIT: state=%zu bytes 18/18\n", sizeof engine);
    return 0;
}
