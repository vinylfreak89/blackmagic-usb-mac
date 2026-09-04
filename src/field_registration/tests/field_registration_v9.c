#include "../field_registration.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int read_truth(FILE *f, unsigned *index, char scenario[96], int *begin,
                      int *ok, int *d1, int *d2, char f1_reason[48],
                      char f2_reason[48], char f1_lock[24], char f2_lock[24],
                      char f1_zero[24], char f2_zero[24], int *f1_lock_top,
                      int *f2_lock_top, int *comb_safe)
{
    char line[768];
    if (!fgets(line, sizeof line, f)) return 0;
    return sscanf(line, "%u,%95[^,],%d,%d,%d,%d,%47[^,],%47[^,],%23[^,],%23[^,],%23[^,],%23[^,],%d,%d,%d",
                  index, scenario, begin, ok, d1, d2, f1_reason, f2_reason,
                  f1_lock, f2_lock, f1_zero, f2_zero, f1_lock_top,
                  f2_lock_top, comb_safe) == 15;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s registration_v9.raw registration_v9.csv\n", argv[0]);
        return 2;
    }
    FILE *raw = fopen(argv[1], "rb");
    FILE *truth = fopen(argv[2], "r");
    if (!raw || !truth) { perror("open"); return 2; }
    char header[256];
    if (!fgets(header, sizeof header, truth)) return 2;
    uint8_t *unit = malloc(FIELDREG_UNIT_BYTES);
    if (!unit) return 2;
    field_registration engine;
    fieldreg_config config = fieldreg_default_config();
    fieldreg_init(&engine, &config);
    unsigned passed = 0, total = 0, index;
    char scenario[96];
    char expected_reason[2][48], expected_lock[2][24], expected_zero[2][24];
    int begin, expected_ok, expected_d1, expected_d2, expected_lock_top[2],
        expected_comb;
    while (read_truth(truth, &index, scenario, &begin, &expected_ok,
                      &expected_d1, &expected_d2, expected_reason[0],
                      expected_reason[1], expected_lock[0], expected_lock[1],
                      expected_zero[0], expected_zero[1],
                      &expected_lock_top[0], &expected_lock_top[1],
                      &expected_comb)) {
        if (fread(unit, 1, FIELDREG_UNIT_BYTES, raw) != FIELDREG_UNIT_BYTES) {
            fprintf(stderr, "short fixture at unit %u\n", index);
            return 2;
        }
        if (begin) fieldreg_begin_segment(&engine);
        fieldreg_decision decision;
        memset(&decision, 0, sizeof decision);
        int actual_ok = fieldreg_process(&engine, unit, &decision);
        int match = actual_ok == expected_ok;
        if (actual_ok) {
            match = match && decision.applied_d1 == expected_d1 &&
                    decision.applied_d2 == expected_d2;
            for (int field = 0; field < 2; ++field) {
                if (strcmp(expected_reason[field], "-") != 0)
                    match = match && strcmp(fieldreg_mode_name(
                        decision.field[field].reason), expected_reason[field]) == 0;
                if (strcmp(expected_lock[field], "-") != 0)
                    match = match && strcmp(fieldreg_lock_state_name(
                        decision.field[field].lock_state), expected_lock[field]) == 0;
                if (strcmp(expected_zero[field], "-") != 0)
                    match = match && strcmp(fieldreg_zero_source_name(
                        decision.field[field].zero_source), expected_zero[field]) == 0;
                if (expected_lock_top[field] != -999)
                    match = match && decision.field[field].lock_top ==
                                      expected_lock_top[field];
            }
            if (expected_comb >= 0)
                match = match && decision.comb_safe == (expected_comb != 0);
            match = match && decision.confidence ==
                    (decision.frame_observation_support > 0 ? 1.0 : 0.0);
        }
        if (match) passed++;
        else fprintf(stderr,
                     "V9-MISMATCH unit=%u scenario=%s expected=%d:(%d,%d) actual=%d:(%d,%d) mode=%s f1=%s/%s f2=%s/%s comb=%d\n",
                     index, scenario, expected_ok, expected_d1, expected_d2,
                     actual_ok, decision.applied_d1, decision.applied_d2,
                     actual_ok ? fieldreg_mode_name(decision.mode) : "Rejected",
                     actual_ok ? fieldreg_mode_name(decision.field[0].reason) : "Rejected",
                     actual_ok ? fieldreg_lock_state_name(decision.field[0].lock_state) : "Rejected",
                     actual_ok ? fieldreg_mode_name(decision.field[1].reason) : "Rejected",
                     actual_ok ? fieldreg_lock_state_name(decision.field[1].lock_state) : "Rejected",
                     actual_ok ? decision.comb_safe : 0);
        total++;
    }
    free(unit);
    fclose(raw);
    fclose(truth);
    printf("V9-GOLDEN: %u/%u\n", passed, total);
    return passed == total ? 0 : 1;
}
