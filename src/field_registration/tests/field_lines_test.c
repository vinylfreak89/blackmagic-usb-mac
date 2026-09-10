#include "../field_lines.h"
#include <stdio.h>
#include <string.h>

static int failures, checks;
static void check(int row, int field, int twice_line)
{
    fieldreg_line_coordinate c = fieldreg_line_from_row(row);
#ifdef LEGACY_ROW_PLUS_FOUR
    /* Negative control: the exact row+4 numeric convention used by the old
     * writers, even granting it the correct physical field identity. */
    if (row >= 0 && row < 525) c = (fieldreg_line_coordinate){field, 2*(row+4)};
#endif
    ++checks;
    if (c.field != field || c.twice_line != twice_line) {
        if (failures < 3) fprintf(stderr, "FAIL row %d: got f%d line2=%d, expected f%d line2=%d\n",
                                 row, c.field, c.twice_line, field, twice_line);
        ++failures;
    }
}

int main(void)
{
    /* Independent enumeration: cyclic block 1 has lines 1..262 then 262.5;
     * block 2 has lines 1..262. Every storage row occurs exactly once. */
    unsigned seen[525] = {0};
    for (int i = 0; i < 263; ++i) {
        int row = (522+i)%525;
        check(row, 1, i == 262 ? 525 : 2*(i+1));
        ++seen[row];
    }
    for (int i = 0; i < 262; ++i) { check(260+i, 2, 2*(i+1)); ++seen[260+i]; }
    for (int row = 0; row < 525; ++row) {
        ++checks;
        if (seen[row] != 1 || fieldreg_row_from_line(fieldreg_line_from_row(row)) != row) ++failures;
    }
    check(-1,0,-1); check(-128,0,-1); check(525,0,-1);
    const struct {int row,field;const char *label;} labels[] = {
        {522,1,"1"},{523,1,"2"},{524,1,"3"},{0,1,"4"},{6,1,"10"},
        {17,1,"21"},{19,1,"23"},{258,1,"262"},{259,1,"262.5"},
        {260,2,"1"},{261,2,"2"},{269,2,"10"},{280,2,"21"},
        {282,2,"23"},{521,2,"262"},{-1,0,"-1"}
    };
    for (unsigned i = 0; i < sizeof labels/sizeof labels[0]; ++i) {
        char label[FIELDREG_LINE_LABEL_BYTES];
        int f = fieldreg_format_row_line(label, labels[i].row);
        ++checks;
        if (f != labels[i].field || strcmp(label, labels[i].label)) ++failures;
    }
    const fieldreg_line_coordinate invalid[] = {{0,2},{3,2},{1,0},{2,525},{1,3},{1,526}};
    for (unsigned i=0;i<sizeof invalid/sizeof invalid[0];++i) {
        ++checks; if (fieldreg_row_from_line(invalid[i]) != -1) ++failures;
    }
    printf("field_lines: %d checks, %d failures\n", checks, failures);
    return failures != 0;
}
