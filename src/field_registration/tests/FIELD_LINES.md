# Field-relative numbering migration — foundation only

`field_lines.h` implements the owner's delivered-row naming rule. It does not
participate in measurement, acquisition, placement or rendering. The mapper
returns a physical field identity and an exact half-line label together; its
inverse is lossless over all 525 storage rows. The display formatter emits
`262.5` without requiring floating-point geometry.

## Status and handoff

The identifier reserved for the coordinated migration is `field-relative-v1`.
**No current exporter emits it yet.** Frameserver schema 20, the raw/live T/S
exports and the cross-compared harness reference remain in their legacy
frame-continuous convention. Do not flip the harness on this foundation commit.
Historical reports remain legacy-labelled measurements, not field-relative
data just because this header exists.

Next migration unit: integrate the mapper into the sidecar and diagnostic
writers, carrying the coordinate's physical field identity as well as its
label. An observation group is not necessarily the owner of every row it
addresses: the current field-1 search reaches rows 260..262, which the owner's
map assigns to field 2, and the field-2 search reaches rows 522..524, which
belong to field 1. Preserve such observations rather than relabel their owner
from the calling field, discard them, or move them. Storage arithmetic is not
changed by this naming migration. A coordinated schema/convention handoff and
unchanged-decision checks are still owed before new exports are compared.

## Checks (no captures read)

`tests/field_lines_test.c`: 1,075 checks, zero failures under O3 and under
ASan/UBSan. Independent cyclic block enumeration covers every row exactly once:
field 1 starts at row 522 and has lines 1..262 followed by 262.5; field 2 starts
at row 260 and has lines 1..262. All coordinates round-trip. Explicit checks
cover padding, both caption rows, both picture origins, boundary labels and
invalid coordinates.

The `LEGACY_ROW_PLUS_FOUR` build is an explicit negative control implementing
the old writers' numeric expression, not a claim that a production replay was
run. It fails 266 mappings:

    FAIL row 522: got f1 line2=1052, expected f1 line2=2
    FAIL row 523: got f1 line2=1054, expected f1 line2=4
    FAIL row 524: got f1 line2=1056, expected f1 line2=6
    field_lines: 1075 checks, 266 failures

`line2` is twice the field-relative line label. No classifier or engine hot path
is changed by this commit, so no ms/unit result or capture acceptance is claimed.
