#define _POSIX_C_SOURCE 200809L

#include "field_registration.h"

#include <dlfcn.h>
#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef size_t (*state_size_fn)(void);
typedef size_t (*object_size_fn)(void);
typedef fieldreg_config (*default_config_fn)(void);
typedef void (*init_fn)(field_registration *, const fieldreg_config *);
typedef void (*begin_segment_fn)(field_registration *);
typedef bool (*process_fn)(field_registration *, const uint8_t *, fieldreg_decision *);
typedef const char *(*mode_name_fn)(fieldreg_mode);

typedef struct api {
    void *handle;
    state_size_fn state_size;
    object_size_fn config_size;
    object_size_fn decision_size;
    default_config_fn default_config;
    init_fn init;
    begin_segment_fn begin_segment;
    process_fn process;
    mode_name_fn mode_name;
} api;

typedef struct truth_row {
    size_t index;
    unsigned counter;
    unsigned segment;
    char scenario[80];
    int d1;
    int d2;
    bool abstain;
    bool reset_before;
} truth_row;

typedef struct class_result {
    char scenario[80];
    uint64_t rows;
    uint64_t match;
    uint64_t abstain;
    uint64_t opposite;
} class_result;

static void fail(const char *message)
{
    fprintf(stderr, "field_registration_truth: %s\n", message);
    exit(2);
}

static void fail_errno(const char *context)
{
    fprintf(stderr, "field_registration_truth: %s: %s\n", context, strerror(errno));
    exit(2);
}

static void *symbol(void *handle, const char *name)
{
    dlerror();
    void *value = dlsym(handle, name);
    const char *error = dlerror();
    if (error) {
        fprintf(stderr, "field_registration_truth: dlsym(%s): %s\n", name, error);
        exit(2);
    }
    return value;
}

static api load_api(const char *path)
{
    api value = {0};
    value.handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!value.handle) {
        fprintf(stderr, "field_registration_truth: dlopen(%s): %s\n", path, dlerror());
        exit(2);
    }
    *(void **)(&value.state_size) = symbol(value.handle, "fieldreg_state_size");
    *(void **)(&value.config_size) = symbol(value.handle, "fieldreg_config_size");
    *(void **)(&value.decision_size) = symbol(value.handle, "fieldreg_decision_size");
    *(void **)(&value.default_config) = symbol(value.handle, "fieldreg_default_config");
    *(void **)(&value.init) = symbol(value.handle, "fieldreg_init");
    *(void **)(&value.begin_segment) = symbol(value.handle, "fieldreg_begin_segment");
    *(void **)(&value.process) = symbol(value.handle, "fieldreg_process");
    *(void **)(&value.mode_name) = symbol(value.handle, "fieldreg_mode_name");
    return value;
}

static uint64_t monotonic_ns(void)
{
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value) != 0)
        fail_errno("clock_gettime");
    return (uint64_t)value.tv_sec * 1000000000ull + (uint64_t)value.tv_nsec;
}

static int compare_double(const void *left, const void *right)
{
    double a = *(const double *)left;
    double b = *(const double *)right;
    return (a > b) - (a < b);
}

static size_t split_csv(char *line, char **fields, size_t capacity)
{
    size_t count = 0;
    char *field = line;
    for (char *p = line;; ++p) {
        if (*p == ',' || *p == '\n' || *p == '\r' || *p == '\0') {
            char end = *p;
            *p = '\0';
            if (count >= capacity)
                fail("too many truth CSV columns");
            fields[count++] = field;
            field = p + 1;
            if (end != ',')
                return count;
        }
    }
}

static bool parse_truth(char *line, truth_row *row)
{
    char *fields[8];
    if (split_csv(line, fields, 8) != 8)
        return false;
    row->index = (size_t)strtoull(fields[0], NULL, 10);
    row->counter = (unsigned)strtoul(fields[1], NULL, 10);
    row->segment = (unsigned)strtoul(fields[2], NULL, 10);
    snprintf(row->scenario, sizeof(row->scenario), "%s", fields[3]);
    row->d1 = (int)strtol(fields[4], NULL, 10);
    row->d2 = (int)strtol(fields[5], NULL, 10);
    row->abstain = strcmp(fields[6], "abstain") == 0;
    row->reset_before = strtol(fields[7], NULL, 10) != 0;
    return true;
}

static class_result *class_for(class_result *values, size_t *count,
                               const char *scenario)
{
    for (size_t i = 0; i < *count; ++i) {
        if (strcmp(values[i].scenario, scenario) == 0)
            return &values[i];
    }
    if (*count >= 64)
        fail("too many truth classes");
    class_result *value = &values[(*count)++];
    memset(value, 0, sizeof(*value));
    snprintf(value->scenario, sizeof(value->scenario), "%s", scenario);
    return value;
}

static bool opposite(int truth, int applied)
{
    return (truth > 0 && applied < 0) || (truth < 0 && applied > 0);
}

static uint16_t load_u16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)p[1] << 8;
}

static void usage(const char *program)
{
    fprintf(stderr,
            "usage: %s --library LIB --raw UNITS --truth TRUTH.csv "
            "[--budget-ms-per-unit 33.3667] [--decisions OUTPUT.csv]\n",
            program);
    exit(2);
}

int main(int argc, char **argv)
{
    const char *library = NULL;
    const char *raw_path = NULL;
    const char *truth_path = NULL;
    const char *decision_path = NULL;
    double budget_ms = 33.3667;
    for (int i = 1; i < argc; ++i) {
        if (i + 1 >= argc)
            usage(argv[0]);
        if (strcmp(argv[i], "--library") == 0)
            library = argv[++i];
        else if (strcmp(argv[i], "--raw") == 0)
            raw_path = argv[++i];
        else if (strcmp(argv[i], "--truth") == 0)
            truth_path = argv[++i];
        else if (strcmp(argv[i], "--budget-ms-per-unit") == 0)
            budget_ms = strtod(argv[++i], NULL);
        else if (strcmp(argv[i], "--decisions") == 0)
            decision_path = argv[++i];
        else
            usage(argv[0]);
    }
    if (!library || !raw_path || !truth_path || budget_ms <= 0.0)
        usage(argv[0]);

    api engine_api = load_api(library);
    if (engine_api.state_size() != sizeof(field_registration))
        fail("header/library field_registration ABI size mismatch");
    if (engine_api.config_size() != sizeof(fieldreg_config))
        fail("header/library config ABI size mismatch");
    if (engine_api.decision_size() != sizeof(fieldreg_decision))
        fail("header/library decision ABI size mismatch");
    field_registration *engine = calloc(1, engine_api.state_size());
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    if (!engine || !unit)
        fail("out of memory");
    fieldreg_config config = engine_api.default_config();
    config.evidence_model = FIELDREG_EVIDENCE_MOTION_PHASE;
    engine_api.init(engine, &config);

    FILE *raw = fopen(raw_path, "rb");
    FILE *truth = fopen(truth_path, "r");
    FILE *decisions = decision_path ? fopen(decision_path, "w") : NULL;
    if (!raw)
        fail_errno(raw_path);
    if (!truth)
        fail_errno(truth_path);
    if (decision_path && !decisions)
        fail_errno(decision_path);
    if (decisions)
        fputs("unit_index,counter,scenario,truth_d1,truth_d2,expect,"
              "applied_d1,applied_d2,decision_d1,decision_d2,mode,confidence,"
              "frame_observation_d1,frame_observation_d2,frame_support,"
              "temporal_best_f1,temporal_best_f2,temporal_margin_f1,"
              "temporal_margin_f2,scene_cut,reset_before\n", decisions);

    char line[1024];
    if (!fgets(line, sizeof(line), truth))
        fail("empty truth CSV");
    size_t timing_capacity = 512;
    double *timings_us = calloc(timing_capacity, sizeof(*timings_us));
    if (!timings_us)
        fail("out of memory allocating timings");
    size_t timing_count = 0;
    class_result classes[64] = {{0}};
    size_t class_count = 0;
    uint64_t rows = 0, unambiguous = 0, matches = 0;
    uint64_t ambiguous = 0, abstentions = 0, opposites = 0;
    uint64_t mismatch_examples = 0;

    while (fgets(line, sizeof(line), truth)) {
        truth_row expected;
        if (!parse_truth(line, &expected))
            fail("malformed truth CSV row");
        if (fread(unit, FIELDREG_UNIT_BYTES, 1, raw) != 1)
            fail("raw unit stream ended before truth CSV");
        if (expected.index != rows)
            fail("truth unit_index is not contiguous");
        if (load_u16(unit + 4) != expected.counter)
            fail("raw counter does not match truth CSV");
        if (expected.reset_before)
            engine_api.begin_segment(engine);

        fieldreg_decision actual;
        uint64_t begin = monotonic_ns();
        bool accepted = engine_api.process(engine, unit, &actual);
        uint64_t end = monotonic_ns();
        if (!accepted)
            fail("engine rejected a synthetic exact unit");
        if (timing_count == timing_capacity) {
            timing_capacity *= 2;
            double *grown = realloc(timings_us, timing_capacity * sizeof(*grown));
            if (!grown)
                fail("out of memory growing timings");
            timings_us = grown;
        }
        timings_us[timing_count++] = (end - begin) / 1000.0;

        class_result *class_value = class_for(classes, &class_count,
                                               expected.scenario);
        ++class_value->rows;
        bool is_match = actual.applied_d1 == expected.d1 &&
                        actual.applied_d2 == expected.d2;
        bool is_abstain = actual.decision_d1 == FIELDREG_UNKNOWN &&
                          actual.decision_d2 == FIELDREG_UNKNOWN;
        bool is_opposite = opposite(expected.d1, actual.applied_d1) ||
                           opposite(expected.d2, actual.applied_d2);
        class_value->match += is_match;
        class_value->abstain += is_abstain;
        class_value->opposite += is_opposite;
        opposites += is_opposite;
        if (expected.abstain) {
            ++ambiguous;
            abstentions += is_abstain;
        } else {
            ++unambiguous;
            matches += is_match;
        }
        if (((!expected.abstain && !is_match) ||
             (expected.abstain && !is_abstain)) && mismatch_examples < 32) {
            fprintf(stderr,
                    "truth disagreement unit=%zu scenario=%s truth=(%d,%d) "
                    "expect=%s got applied=(%d,%d) decision=(%d,%d) mode=%s "
                    "frame=(%d,%d) temporal=(%d,%d) cut=%d\n",
                    expected.index, expected.scenario, expected.d1, expected.d2,
                    expected.abstain ? "abstain" : "match", actual.applied_d1,
                    actual.applied_d2, actual.decision_d1, actual.decision_d2,
                    engine_api.mode_name(actual.mode),
                    actual.frame_observation_d1, actual.frame_observation_d2,
                    actual.temporal_best_f1, actual.temporal_best_f2,
                    actual.temporal_scene_cut ? 1 : 0);
            ++mismatch_examples;
        }
        if (decisions) {
            fprintf(decisions,
                    "%zu,%u,%s,%d,%d,%s,%d,%d,%d,%d,%s,%.9f,"
                    "%d,%d,%u,%d,%d,%.9f,%.9f,%d,%d\n",
                    expected.index, expected.counter, expected.scenario,
                    expected.d1, expected.d2,
                    expected.abstain ? "abstain" : "match",
                    actual.applied_d1, actual.applied_d2,
                    actual.decision_d1, actual.decision_d2,
                    engine_api.mode_name(actual.mode), actual.confidence,
                    actual.frame_observation_d1, actual.frame_observation_d2,
                    actual.frame_observation_support,
                    actual.temporal_best_f1, actual.temporal_best_f2,
                    actual.temporal_margin_f1, actual.temporal_margin_f2,
                    actual.temporal_scene_cut ? 1 : 0,
                    expected.reset_before ? 1 : 0);
        }
        ++rows;
    }
    if (fgetc(raw) != EOF)
        fail("raw unit stream contains units absent from truth CSV");

    qsort(timings_us, timing_count, sizeof(*timings_us), compare_double);
    double median_us = timings_us[timing_count / 2];
    double p95_us = timings_us[(size_t)((timing_count - 1) * 0.95)];
    double max_us = timings_us[timing_count - 1];
    printf("synthetic truth: rows=%" PRIu64 " unambiguous=%" PRIu64
           " ambiguous=%" PRIu64 "\n", rows, unambiguous, ambiguous);
    printf("applied truth agreement: %.3f%% (%" PRIu64 "/%" PRIu64 ")\n",
           unambiguous ? 100.0 * matches / unambiguous : 100.0,
           matches, unambiguous);
    printf("ambiguous abstention: %.3f%% (%" PRIu64 "/%" PRIu64 ")\n",
           ambiguous ? 100.0 * abstentions / ambiguous : 100.0,
           abstentions, ambiguous);
    printf("opposite-direction corrections: %" PRIu64 "\n", opposites);
    printf("cost: median=%.3f us/unit p95=%.3f us/unit max=%.3f us/unit "
           "budget=%.3f us/unit\n", median_us, p95_us, max_us,
           budget_ms * 1000.0);
    puts("classes:");
    for (size_t i = 0; i < class_count; ++i) {
        class_result *value = &classes[i];
        printf("  %-32s rows=%" PRIu64 " match=%" PRIu64
               " abstain=%" PRIu64 " opposite=%" PRIu64 "\n",
               value->scenario, value->rows, value->match,
               value->abstain, value->opposite);
    }

    bool pass = matches == unambiguous && abstentions == ambiguous &&
                opposites == 0 && p95_us <= budget_ms * 1000.0;
    printf("RESULT: %s\n", pass ? "PASS" : "FAIL");
    if (decisions)
        fclose(decisions);
    fclose(raw);
    fclose(truth);
    free(timings_us);
    free(unit);
    free(engine);
    dlclose(engine_api.handle);
    return pass ? 0 : 1;
}
