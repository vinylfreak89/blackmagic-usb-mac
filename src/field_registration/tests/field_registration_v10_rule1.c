#include "../field_registration.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum { BENCHMARK_UNITS = 1000 };

static double now_us(void)
{
    struct timespec value;
    assert(clock_gettime(CLOCK_MONOTONIC, &value) == 0);
    return (double)value.tv_sec * 1000000.0 + (double)value.tv_nsec / 1000.0;
}

static int compare_double(const void *left, const void *right)
{
    const double a = *(const double *)left;
    const double b = *(const double *)right;
    return (a > b) - (a < b);
}

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
        assert(decision.field[0].raw_bottom == 252);
        assert(decision.field[0].raw_height == 232);
        assert(decision.field[0].gauge == FIELDREG_GAUGE_GEOMETRY);
        assert(decision.field[0].caption_confirmation == expected[i]);
    }

    assert(fgetc(raw) == EOF);
    double timings[BENCHMARK_UNITS];
    for (size_t i = 0; i < BENCHMARK_UNITS; ++i) {
        fieldreg_decision decision;
        const double start = now_us();
        assert(fieldreg_process(&engine, unit, &decision));
        timings[i] = now_us() - start;
    }
    qsort(timings, BENCHMARK_UNITS, sizeof timings[0], compare_double);
    const double median = timings[BENCHMARK_UNITS / 2];
    const double p95 = timings[(BENCHMARK_UNITS * 95) / 100];
    assert(p95 <= 10000.0);
    fclose(raw);
    free(unit);
    printf("FIELDREG-V10-RULE1: 3/3 cost median=%.3f us/unit "
           "p95=%.3f us/unit budget=10000.000 us/unit\n", median, p95);
    return 0;
}
