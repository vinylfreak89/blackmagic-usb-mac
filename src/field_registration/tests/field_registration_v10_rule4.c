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
        fprintf(stderr, "usage: %s registration_v10_rule4.raw\n", argv[0]);
        return 2;
    }
    FILE *raw = fopen(argv[1], "rb");
    if (!raw) {
        perror("open");
        return 2;
    }
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    assert(unit);
    field_registration engine;
    fieldreg_config config = fieldreg_default_config();
    fieldreg_init(&engine, &config);
    fieldreg_begin_segment(&engine);

    for (size_t i = 0; i < 5; ++i) {
        assert(fread(unit, 1, FIELDREG_UNIT_BYTES, raw) ==
               FIELDREG_UNIT_BYTES);
        fieldreg_decision decision;
        memset(&decision, 0, sizeof decision);
        assert(fieldreg_process(&engine, unit, &decision));
        const fieldreg_field_decision *field = &decision.field[0];
        assert(field->applied_d == 2);
        assert(field->lock_state == FIELDREG_LOCK_LOCKED);
        assert(field->lock_switch_line_count_known);
        assert(field->lock_switch_line_count == 3);
        if (i == 0) {
            assert(field->caption_confirmation == FIELDREG_CONFIRM_AGREES);
            assert(field->observed_switch_line_count == 3);
            assert(field->switch_count_agrees);
            assert(!field->switch_count_conflict);
        } else if (i < 4) {
            assert(field->observed_switch_line_count == 4);
            assert(field->switch_count_conflict);
            assert(!field->switch_count_agrees);
            assert(field->reason == FIELDREG_MODE_SWITCH_COUNT_CONFLICT);
        } else {
            assert(field->observed_switch_line_count == 3);
            assert(field->switch_count_agrees);
            assert(!field->switch_count_conflict);
        }
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
    /* Owner: optimize after correctness; always report the budget breach. */
    if(getenv("FIELDREG_ENFORCE_BUDGET"))assert(p95 <= 10000.0);
    if(p95>10000.0)fprintf(stderr,"PERFORMANCE BUDGET EXCEEDED: %.3f us/unit p95\n",p95);
    fclose(raw);
    free(unit);
    printf("FIELDREG-V10-RULE4: 5/5 cost median=%.3f us/unit "
           "p95=%.3f us/unit budget=10000.000 us/unit\n", median, p95);
    return 0;
}
