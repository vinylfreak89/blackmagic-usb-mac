#ifndef BLACKMAGIC_FIELD_LINES_H
#define BLACKMAGIC_FIELD_LINES_H

#include <stdio.h>

/* Presentation coordinates only. Never use labels for raster addressing,
 * displacements, spans or band counts. The owner settled this delivered-row
 * map in geometry_first_engine.md section 1, including padding and the cyclic
 * field-1 origin. The observation's field need not own the addressed row.
 * This identifier is reserved for the coordinated exporter migration; merely
 * including this header does not change the current sidecar schema. */
#define FIELDREG_LINE_CONVENTION "field-relative-v1"
#define FIELDREG_LINE_LABEL_BYTES 6 /* "262.5" plus the terminator */

typedef struct fieldreg_line_coordinate {
    int field;      /* Physical field 1 or 2; 0 means Unknown. */
    int twice_line; /* Exact half-line units, not a floating-point row index. */
} fieldreg_line_coordinate;

static inline fieldreg_line_coordinate fieldreg_line_from_row(int row)
{
    if (row < 0 || row >= 525)
        return (fieldreg_line_coordinate){0, -1};
    if (row == 259)
        return (fieldreg_line_coordinate){1, 525};
    if (row >= 260 && row <= 521)
        return (fieldreg_line_coordinate){2, 2 * (row - 259)};
    return (fieldreg_line_coordinate){1, 2 * (row >= 522 ? row - 521 : row + 4)};
}

/* The inverse is for coordinate interchange/verification, not an invitation
 * to convert engine storage to field labels. Reject invalid/nonexistent lines. */
static inline int fieldreg_row_from_line(fieldreg_line_coordinate c)
{
    if (c.field == 1 && c.twice_line == 525) return 259;
    if (c.twice_line < 2 || c.twice_line > 524 || c.twice_line % 2) return -1;
    int line = c.twice_line / 2;
    if (c.field == 1) return line < 4 ? line + 521 : line - 4;
    if (c.field == 2) return line + 259;
    return -1;
}

/* Keep the returned physical field alongside the numeric label whenever a
 * diagnostic search can cross fields. Unknown stays -1, never a wrapped row. */
static inline int fieldreg_format_row_line(char label[FIELDREG_LINE_LABEL_BYTES], int row)
{
    fieldreg_line_coordinate c = fieldreg_line_from_row(row);
    if (!c.field) snprintf(label, FIELDREG_LINE_LABEL_BYTES, "-1");
    else snprintf(label, FIELDREG_LINE_LABEL_BYTES, "%d%s", c.twice_line / 2,
                  c.twice_line % 2 ? ".5" : "");
    return c.field;
}

#endif
