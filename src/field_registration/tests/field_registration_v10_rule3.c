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
        fprintf(stderr, "usage: %s registration_v10_rule3.raw\n", argv[0]);
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

    const int expected_d[] = {0, 1};
    const int expected_top[] = {19, 20};
    const int expected_switch[] = {256, 257};
    const int expected_bottom[] = {255, 256};
    const int expected_band[] = {3, 2};
    const int expected_span[] = {237, 238};
    for (size_t i = 0; i < 2; ++i) {
        assert(fread(unit, 1, FIELDREG_UNIT_BYTES, raw) ==
               FIELDREG_UNIT_BYTES);
        fieldreg_decision decision;
        memset(&decision, 0, sizeof decision);
        assert(fieldreg_process(&engine, unit, &decision));
        const fieldreg_field_decision *field = &decision.field[0];
        assert(field->applied_d == expected_d[i]);
        assert(field->raw_top == expected_top[i]);
        assert(field->recorded_last == 258);
        assert(field->switch_measurable);
        assert(field->first_full_other_head_line == expected_switch[i]);
        assert(field->switch_line == expected_switch[i]);
        assert(field->raw_bottom == expected_bottom[i]);
        assert(field->band_extent == expected_band[i]);
        assert(field->raw_span == expected_span[i]);
        assert(field->observed_switch_line_count == 3);
        assert(field->picture_rows == 237);
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
    printf("FIELDREG-V10-RULE3: 2/2 cost median=%.3f us/unit "
           "p95=%.3f us/unit budget=10000.000 us/unit\n", median, p95);
    return 0;
}
