#define _POSIX_C_SOURCE 200809L

#include "field_registration.h"

#include <stdbool.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { MAX_ROWS = 2048, MAX_SCENARIOS = 80, CSV_FIELDS = 11 };

typedef struct truth_row {
    size_t index;
    unsigned counter;
    char scenario[80];
    bool raster_known;
    int raster_d1;
    int raster_d2;
    int oracle_d1;
    int oracle_d2;
    bool unsettled;
    bool reset_before;
} truth_row;

typedef struct result_row {
    truth_row truth;
    int applied_d1;
    int applied_d2;
    bool observation_known;
    bool backdated;
    bool trajectory_reset;
    fieldreg_mode mode;
    int observation_d1;
    int observation_d2;
    unsigned observation_support;
    bool envelope_authority;
    int phase_consensus;
    unsigned phase_support;
    int temporal1;
    int temporal2;
    bool relative_only;
    bool relative_gauge_unknown;
    fieldreg_relative_gauge_source relative_gauge;
    int relative_phase;
    unsigned relative_static_columns;
    unsigned relative_persistent_columns;
    bool bottom_f1_censored;
} result_row;

typedef struct scenario_summary {
    char name[80];
    uint64_t rows;
    uint64_t raster_rows;
    uint64_t raster_matches;
    uint64_t oracle_matches;
    uint64_t common_mode_gauge;
    uint64_t transport_unknown;
    uint64_t scene_cut_hold;
    uint64_t trajectory_resets;
    uint64_t relative_only;
    uint64_t relative_gauge_unknown;
    uint64_t bottom_f1_censored;
} scenario_summary;

static void fail(const char *message)
{
    fprintf(stderr, "field_registration_trajectory: %s\n", message);
    exit(2);
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
                fail("too many CSV fields");
            fields[count++] = field;
            field = p + 1;
            if (end != ',')
                return count;
        }
    }
}

static bool parse_truth(char *line, truth_row *row)
{
    char *field[CSV_FIELDS];
    if (split_csv(line, field, CSV_FIELDS) != CSV_FIELDS)
        return false;
    row->index = (size_t)strtoull(field[0], NULL, 10);
    row->counter = (unsigned)strtoul(field[1], NULL, 10);
    snprintf(row->scenario, sizeof(row->scenario), "%s", field[3]);
    row->raster_known = strtol(field[4], NULL, 10) != 0;
    row->raster_d1 = row->raster_known ? (int)strtol(field[5], NULL, 10) : 0;
    row->raster_d2 = row->raster_known ? (int)strtol(field[6], NULL, 10) : 0;
    row->oracle_d1 = (int)strtol(field[7], NULL, 10);
    row->oracle_d2 = (int)strtol(field[8], NULL, 10);
    row->unsettled = strtol(field[9], NULL, 10) != 0;
    row->reset_before = strtol(field[10], NULL, 10) != 0;
    return true;
}

static uint16_t load_u16(const uint8_t *p)
{
    return (uint16_t)p[0] | (uint16_t)p[1] << 8;
}

static void usage(const char *program)
{
    fprintf(stderr, "usage: %s RAW TRUTH.csv\n", program);
    exit(2);
}

int main(int argc, char **argv)
{
    if (argc != 3)
        usage(argv[0]);
    FILE *raw = fopen(argv[1], "rb");
    FILE *truth = fopen(argv[2], "r");
    if (!raw || !truth)
        fail("could not open fixture");

    fieldreg_config config = fieldreg_default_config();
    config.evidence_model = FIELDREG_EVIDENCE_MOTION_PHASE;
    field_registration engine;
    fieldreg_init(&engine, &config);
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    if (!unit)
        fail("out of memory");

    char line[1024];
    if (!fgets(line, sizeof(line), truth))
        fail("empty truth CSV");
    result_row rows[MAX_ROWS];
    size_t count = 0;
    size_t fifo_first = 0;
    while (fgets(line, sizeof(line), truth)) {
        if (count == MAX_ROWS)
            fail("fixture exceeds MAX_ROWS");
        truth_row expected;
        if (!parse_truth(line, &expected))
            fail("malformed truth row");
        if (expected.index != count)
            fail("non-contiguous unit index");
        if (fread(unit, FIELDREG_UNIT_BYTES, 1, raw) != 1)
            fail("raw stream ended before truth");
        if (load_u16(unit + 4) != expected.counter)
            fail("counter mismatch");
        if (expected.reset_before) {
            fifo_first = count;
            fieldreg_begin_segment(&engine);
        }

        fieldreg_decision decision;
        if (!fieldreg_process(&engine, unit, &decision))
            fail("engine rejected exact synthetic unit");
        result_row *result = &rows[count];
        memset(result, 0, sizeof(*result));
        result->truth = expected;
        result->applied_d1 = decision.applied_d1;
        result->applied_d2 = decision.applied_d2;
        result->observation_known =
            decision.frame_observation_d1 != FIELDREG_UNKNOWN;
        result->trajectory_reset = decision.trajectory_reset;
        result->mode = decision.mode;
        result->observation_d1 = decision.frame_observation_d1;
        result->observation_d2 = decision.frame_observation_d2;
        result->observation_support = decision.frame_observation_support;
        result->envelope_authority = decision.global_envelope_authority;
        result->phase_consensus = decision.phase_consensus;
        result->phase_support = decision.phase_support;
        result->temporal1 = decision.temporal_best_f1;
        result->temporal2 = decision.temporal_best_f2;
        result->relative_only = decision.relative_only;
        result->relative_gauge_unknown = decision.relative_only_gauge_unknown;
        result->relative_gauge = decision.relative_only_gauge_source;
        result->relative_phase = decision.relative_only_phase;
        result->relative_static_columns = decision.relative_only_static_columns;
        result->relative_persistent_columns =
            decision.relative_only_persistent_columns;
        result->bottom_f1_censored = decision.bottom_f1_censored;

        /* Exact simulation of the current caller's limited backdating: only
         * abstaining rows still in its FIFO are rewritten. Positive
         * provisional observations are immutable here, which is the defect
         * this fixture freezes. */
        if (decision.decision_backdate) {
            size_t begin = count + 1 > decision.decision_backdate
                               ? count + 1 - decision.decision_backdate
                               : 0;
            if (begin < fifo_first)
                begin = fifo_first;
            for (size_t i = begin; i <= count; ++i) {
                if (!rows[i].observation_known) {
                    rows[i].applied_d1 = decision.baseline_d1;
                    rows[i].applied_d2 = decision.baseline_d2;
                    rows[i].backdated = true;
                }
            }
        }
        if (decision.trajectory_reset)
            fifo_first = count + 1;
        else if (count + 1 - fifo_first > config.maximum_buffered_units)
            ++fifo_first;
        ++count;
    }
    if (fgetc(raw) != EOF)
        fail("raw stream has units absent from truth CSV");

    uint64_t raster_rows = 0, raster_matches = 0;
    uint64_t oracle_matches = 0, oracle_wrong = 0;
    uint64_t unsettled_rows = 0, unsettled_wrong = 0;
    uint64_t stale_rows = 0, stale_wrong = 0;
    uint64_t stale_wrong_positive = 0;
    scenario_summary scenarios[MAX_SCENARIOS];
    memset(scenarios, 0, sizeof(scenarios));
    size_t scenario_count = 0;
    for (size_t i = 0; i < count; ++i) {
        result_row *row = &rows[i];
        bool oracle_match = row->applied_d1 == row->truth.oracle_d1 &&
                            row->applied_d2 == row->truth.oracle_d2;
        oracle_matches += oracle_match;
        oracle_wrong += !oracle_match;
        if (row->truth.raster_known) {
            bool raster_match = row->applied_d1 == row->truth.raster_d1 &&
                                row->applied_d2 == row->truth.raster_d2;
            ++raster_rows;
            raster_matches += raster_match;
        }
        if (row->truth.unsettled) {
            ++unsettled_rows;
            unsettled_wrong += !oracle_match;
        }
        if (!oracle_match &&
            (strcmp(row->truth.scenario, "multiphase-main-10") == 0 ||
             strcmp(row->truth.scenario,
                    "physical-multiphase-envelope-jitter") == 0 ||
             strcmp(row->truth.scenario,
                    "physical-field1-unit-rate-jitter") == 0 ||
             strncmp(row->truth.scenario, "relative-", 9) == 0 ||
             strncmp(row->truth.scenario, "bottom-censored-", 16) == 0)) {
            printf("  mismatch row=%zu scenario=%s applied=(%d,%d) oracle=(%d,%d) mode=%s obs=(%d,%d)/%u authority=%d phase=%d/%u temporal=(%d,%d)\n",
                   i, row->truth.scenario, row->applied_d1, row->applied_d2,
                   row->truth.oracle_d1, row->truth.oracle_d2,
                   fieldreg_mode_name(row->mode), row->observation_d1,
                   row->observation_d2, row->observation_support,
                   row->envelope_authority, row->phase_consensus,
                   row->phase_support, row->temporal1, row->temporal2);
        }
        if (strncmp(row->truth.scenario, "stale-positive-", 15) == 0) {
            ++stale_rows;
            stale_wrong += !oracle_match;
            stale_wrong_positive += !oracle_match && row->observation_known;
        }

        size_t scenario = 0;
        while (scenario < scenario_count &&
               strcmp(scenarios[scenario].name, row->truth.scenario) != 0)
            ++scenario;
        if (scenario == scenario_count) {
            if (scenario_count == MAX_SCENARIOS)
                fail("fixture exceeds MAX_SCENARIOS");
            snprintf(scenarios[scenario].name, sizeof(scenarios[scenario].name),
                     "%s", row->truth.scenario);
            ++scenario_count;
        }
        scenario_summary *summary = &scenarios[scenario];
        ++summary->rows;
        summary->oracle_matches += oracle_match;
        if (row->truth.raster_known) {
            ++summary->raster_rows;
            summary->raster_matches +=
                row->applied_d1 == row->truth.raster_d1 &&
                row->applied_d2 == row->truth.raster_d2;
        }
        summary->common_mode_gauge +=
            row->mode == FIELDREG_MODE_UNKNOWN_COMMON_MODE_GAUGE;
        summary->transport_unknown +=
            row->mode == FIELDREG_MODE_UNKNOWN_TRANSPORT_OR_VBI;
        summary->scene_cut_hold +=
            row->mode == FIELDREG_MODE_UNKNOWN_SCENE_CUT_HOLD;
        summary->trajectory_resets += row->trajectory_reset;
        summary->relative_only += row->relative_only;
        summary->relative_gauge_unknown += row->relative_gauge_unknown;
        summary->bottom_f1_censored += row->bottom_f1_censored;
    }

    printf("trajectory fixture: rows=%zu raster-known=%" PRIu64
           " unsettled=%" PRIu64 "\n", count, raster_rows, unsettled_rows);
    printf("current caller vs raster truth: %" PRIu64 "/%" PRIu64
           " (%.3f%%)\n", raster_matches, raster_rows,
           raster_rows ? 100.0 * raster_matches / raster_rows : 100.0);
    printf("current caller vs trajectory oracle: %" PRIu64 "/%zu"
           " (%.3f%%), wrong=%" PRIu64 "\n", oracle_matches, count,
           count ? 100.0 * oracle_matches / count : 100.0, oracle_wrong);
    printf("unsettled oracle errors: %" PRIu64 "/%" PRIu64 "\n",
           unsettled_wrong, unsettled_rows);
    printf("stale-latch class: wrong=%" PRIu64 "/%" PRIu64
           " positive-wrong=%" PRIu64 "\n", stale_wrong, stale_rows,
           stale_wrong_positive);
    puts("per-scenario current-engine scores:");
    for (size_t i = 0; i < scenario_count; ++i) {
        const scenario_summary *summary = &scenarios[i];
        printf("  %-36s oracle=%" PRIu64 "/%" PRIu64,
               summary->name, summary->oracle_matches, summary->rows);
        if (summary->raster_rows != 0)
            printf(" raster=%" PRIu64 "/%" PRIu64,
                   summary->raster_matches, summary->raster_rows);
        else
            printf(" raster=unknown");
        printf(" common-gauge=%" PRIu64 " transport-unknown=%" PRIu64
               " scene-hold=%" PRIu64 " resets=%" PRIu64
               " relative-only=%" PRIu64 " gauge-unknown=%" PRIu64
               " bottom1-censored=%" PRIu64 "\n",
               summary->common_mode_gauge, summary->transport_unknown,
               summary->scene_cut_hold, summary->trajectory_resets,
               summary->relative_only, summary->relative_gauge_unknown,
               summary->bottom_f1_censored);
    }

    static const char *required_live_classes[] = {
        "physical-field1-unit-rate-jitter",
        "physical-multiphase-envelope-jitter",
        "physical-common-plus-unit-rate-jitter",
        "physical-common-minus-unit-rate-jitter",
        "false-edge-chatter",
        "phase-chatter",
        "upward-minus2-field1",
        "upward-minus2-field2",
        "upward-minus2-common",
        "multiphase-main-10",
        "flat-dark-intact-padding-vbi",
        "flat-blank-intact-padding-no-vbi",
        "relative-only-return-temporal-gauge",
        "relative-only-following-abstain",
        "relative-only-sustained-plus1-guard",
        "relative-only-onset-temporal-gauge",
        "relative-only-gauge-unknown",
        "relative-guard-alternating-card",
        "relative-guard-local-overlay",
        "relative-guard-scene-cut",
        "relative-guard-interfield-motion",
        "relative-guard-nominal",
        "bottom-censored-field1-plus5",
        "bottom-censored-static-card-guard",
    };
    bool live_pass = stale_wrong == 0;
    for (size_t required = 0;
         required < sizeof(required_live_classes) /
                        sizeof(required_live_classes[0]);
         ++required) {
        bool found = false;
        for (size_t i = 0; i < scenario_count; ++i) {
            if (strcmp(scenarios[i].name, required_live_classes[required]) == 0) {
                found = true;
                live_pass = live_pass &&
                            scenarios[i].oracle_matches == scenarios[i].rows;
                break;
            }
        }
        live_pass = live_pass && found;
    }
    for (size_t i = 0; i < scenario_count; ++i) {
        const scenario_summary *summary = &scenarios[i];
        if (strcmp(summary->name, "relative-only-return-temporal-gauge") == 0 ||
            strcmp(summary->name, "relative-only-onset-temporal-gauge") == 0) {
            live_pass = live_pass && summary->relative_only == summary->rows &&
                        summary->relative_gauge_unknown == 0;
        } else if (strcmp(summary->name,
                          "relative-only-sustained-plus1-guard") == 0) {
            /* The minimum confirms the already committed phase. It is a
             * guard, not a new relative-only presentation. */
            live_pass = live_pass && summary->relative_only == 0;
        } else if (strcmp(summary->name, "relative-only-gauge-unknown") == 0) {
            live_pass = live_pass && summary->relative_only == summary->rows &&
                        summary->relative_gauge_unknown == summary->rows;
        } else if (strcmp(summary->name,
                          "relative-only-following-abstain") == 0) {
            live_pass = live_pass && summary->relative_only == 0;
        } else if (strncmp(summary->name, "relative-guard-", 15) == 0) {
            live_pass = live_pass && summary->relative_only == 0;
        } else if (strcmp(summary->name, "bottom-censored-field1-plus5") == 0) {
            live_pass = live_pass &&
                        summary->bottom_f1_censored == summary->rows;
        } else if (strcmp(summary->name,
                          "bottom-censored-static-card-guard") == 0) {
            live_pass = live_pass && summary->relative_only == 0;
        }
    }
    /* Provisional inversion is intentionally an archival-side trajectory
     * question. The zero-latency live engine follows its coherent raster and
     * reports the disagreement; this test does not pretend otherwise. */
    printf("archival-only oracle disagreements: %" PRIu64 "\n", oracle_wrong);
    printf("LIVE-AUTHORITY-GOLDEN: %s\n", live_pass ? "PASS" : "FAIL");
    free(unit);
    fclose(raw);
    fclose(truth);
    return live_pass ? 0 : 1;
}
