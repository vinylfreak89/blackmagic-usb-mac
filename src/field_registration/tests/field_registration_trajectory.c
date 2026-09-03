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
               " scene-hold=%" PRIu64 " resets=%" PRIu64 "\n",
               summary->common_mode_gauge, summary->transport_unknown,
               summary->scene_cut_hold, summary->trajectory_resets);
    }

    /* This is a pre-redesign characterization test. Passing means the public
     * fixture still exposes the known semantic gap; it does not bless it. */
    bool reproduced = stale_wrong > 1 && stale_wrong_positive >= 1;
    printf("CURRENT-LIMITATION-REPRODUCED: %s\n", reproduced ? "YES" : "NO");
    free(unit);
    fclose(raw);
    fclose(truth);
    return reproduced ? 0 : 1;
}
