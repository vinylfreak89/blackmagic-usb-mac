#!/usr/bin/env python3
"""Generate a synthetic horizontal-switch line-account golden."""

import argparse

from gen_v9_units import BYTES_PER_LINE, HEADER_BYTES, PIXELS, make_unit


def set_line(unit, row, values):
    line = memoryview(unit)[
        HEADER_BYTES + row * BYTES_PER_LINE:
        HEADER_BYTES + (row + 1) * BYTES_PER_LINE
    ]
    line[1::2] = bytes(values)
    # Recorded decoder noise remains present even where the other head is
    # dark. It makes the synthetic clip independently measurable.
    line[0::2] = bytes(124 if (x + row) & 1 else 132 for x in range(PIXELS))


def horizontal_pattern():
    state = 0x6D2B79F5
    values = []
    for _ in range(PIXELS):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        values.append(32 + ((state >> 24) % 192))
    return values


def account_unit(counter, d1):
    unit = make_unit(counter, picture=(d1, 0), insert=False,
                     bottom_overrides=(258, 521), content_phases=(0, 0))
    pattern = horizontal_pattern()
    shifted = pattern[60:] + pattern[:60]

    top1 = 19 + d1
    switch1 = 256 + d1
    for row in range(top1, switch1):
        set_line(unit, row, pattern)
    for row in range(switch1, 259):
        set_line(unit, row, shifted)

    # Field 2 stays at standard placement with a three-line visible band.
    for row in range(282, 519):
        set_line(unit, row, pattern)
    for row in range(519, 522):
        set_line(unit, row, shifted)
    return unit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    units = [account_unit(0, 0), account_unit(1, 1)]
    with open(args.output, "wb") as output:
        for unit in units:
            output.write(unit)
    print(f"wrote {len(units)} v10 rule-3 units")


if __name__ == "__main__":
    main()
