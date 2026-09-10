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

    const fieldreg_confirmation expected_confirmation[] = {
        FIELDREG_CONFIRM_AGREES,
        FIELDREG_CONFIRM_DISAGREES,
        FIELDREG_CONFIRM_AGREES,
        FIELDREG_CONFIRM_NOT_APPLICABLE,
        FIELDREG_CONFIRM_NOT_APPLICABLE,
    };
    const int expected_d[] = {2, 2, 2, 0, 0};
    for (size_t i = 0; i < sizeof expected_d / sizeof expected_d[0]; ++i) {
        assert(fread(unit, 1, FIELDREG_UNIT_BYTES, raw) ==
               FIELDREG_UNIT_BYTES);
        fieldreg_decision decision;
        memset(&decision, 0, sizeof decision);
        assert(fieldreg_process(&engine, unit, &decision));
        /* The first qualified caption confirms the geometry, even without
         * a switch. Later caption disagreement does not replace geometry. */
        assert(decision.field[0].lock_state == FIELDREG_LOCK_LOCKED);
        assert(!decision.field[0].lock_switch_line_count_known);
        assert(decision.field[0].lock_switch_line_count == -1);
        assert(decision.applied_d1 == expected_d[i]);
        assert(decision.field[0].measured_d == expected_d[i]);
        assert(decision.field[0].geometry_d == expected_d[i]);
        assert(decision.field[0].gauge == FIELDREG_GAUGE_GEOMETRY);
        assert(decision.field[0].caption_confirmation ==
               expected_confirmation[i]);
    }

    assert(fgetc(raw) == EOF);
    if (!getenv("FIELDREG_BENCHMARK")) {
        fclose(raw); free(unit);
        puts("FIELDREG-V10-RULE1: 5/5 (correctness only)");
        return 0;
    }
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
    /* Owner: optimize after correctness; always report the budget breach. */
    if(getenv("FIELDREG_ENFORCE_BUDGET"))assert(p95 <= 10000.0);
    if(p95>10000.0)fprintf(stderr,"PERFORMANCE BUDGET EXCEEDED: %.3f us/unit p95\n",p95);
    fclose(raw);
    free(unit);
    printf("FIELDREG-V10-RULE1: 5/5 cost median=%.3f us/unit "
           "p95=%.3f us/unit budget=10000.000 us/unit\n", median, p95);
    return 0;
}
