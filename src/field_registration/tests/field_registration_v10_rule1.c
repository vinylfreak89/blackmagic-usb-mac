#include "../field_registration.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s registration_v10_rule1.raw\n", argv[0]);
        return 2;
    }

    FILE *raw = fopen(argv[1], "rb");
    if (!raw) {
        perror("open");
        return 2;
    }
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    if (!unit) return 2;

    field_registration engine;
    fieldreg_config config = fieldreg_default_config();
    fieldreg_init(&engine, &config);
    fieldreg_begin_segment(&engine);

    const fieldreg_confirmation expected[] = {
        FIELDREG_CONFIRM_AGREES,
        FIELDREG_CONFIRM_DISAGREES,
        FIELDREG_CONFIRM_AGREES,
    };
    for (size_t i = 0; i < sizeof expected / sizeof expected[0]; ++i) {
        assert(fread(unit, 1, FIELDREG_UNIT_BYTES, raw) ==
               FIELDREG_UNIT_BYTES);
        fieldreg_decision decision;
        memset(&decision, 0, sizeof decision);
        assert(fieldreg_process(&engine, unit, &decision));
        assert(decision.applied_d1 == 2);
        assert(decision.field[0].geometry_d == 2);
        assert(decision.field[0].gauge == FIELDREG_GAUGE_GEOMETRY);
        assert(decision.field[0].caption_confirmation == expected[i]);
    }

    assert(fgetc(raw) == EOF);
    fclose(raw);
    free(unit);
    puts("FIELDREG-V10-RULE1: 3/3");
    return 0;
}
