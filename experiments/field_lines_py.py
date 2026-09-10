"""Mirror of src/field_registration/field_lines.h for harness use.

Checked against the C header by experiments/field_lines_py_test.py, which compiles the header and
compares all 525 rows. Do not edit one without the other.
"""


def row_to_field_twice(row: int):
    if row < 0 or row >= 525: return (0, -1)
    if row == 259: return (1, 525)
    if 260 <= row <= 521: return (2, 2 * (row - 259))
    return (1, 2 * (row - 521 if row >= 522 else row + 4))


def row_to_line(row: int) -> str:
    f, t = row_to_field_twice(row)
    if not f: return "-1"
    return "%d%s" % (t // 2, ".5" if t % 2 else "")


def row_to_field(row: int) -> int:
    return row_to_field_twice(row)[0]
