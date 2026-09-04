#include "../field_registration.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int read_truth(FILE *f, unsigned *index, char scenario[96], int *begin,
                      int *ok, int *d1, int *d2)
{
    char line[256];
    if (!fgets(line, sizeof line, f)) return 0;
    return sscanf(line, "%u,%95[^,],%d,%d,%d,%d", index, scenario, begin, ok,
                  d1, d2) == 6;
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
    int begin, expected_ok, expected_d1, expected_d2;
    while (read_truth(truth, &index, scenario, &begin, &expected_ok,
                      &expected_d1, &expected_d2)) {
        if (fread(unit, 1, FIELDREG_UNIT_BYTES, raw) != FIELDREG_UNIT_BYTES) {
            fprintf(stderr, "short fixture at unit %u\n", index);
            return 2;
        }
        if (begin) fieldreg_begin_segment(&engine);
        fieldreg_decision decision;
        memset(&decision, 0, sizeof decision);
        int actual_ok = fieldreg_process(&engine, unit, &decision);
        int match = actual_ok == expected_ok &&
                    (!actual_ok || (decision.applied_d1 == expected_d1 &&
                                    decision.applied_d2 == expected_d2));
        if (match) passed++;
        else fprintf(stderr,
                     "V9-MISMATCH unit=%u scenario=%s expected=%d:(%d,%d) actual=%d:(%d,%d) mode=%s\n",
                     index, scenario, expected_ok, expected_d1, expected_d2,
                     actual_ok, decision.applied_d1, decision.applied_d2,
                     actual_ok ? fieldreg_mode_name(decision.mode) : "Rejected");
        total++;
    }
    free(unit);
    fclose(raw);
    fclose(truth);
    printf("V9-GOLDEN: %u/%u\n", passed, total);
    return passed == total ? 0 : 1;
}
