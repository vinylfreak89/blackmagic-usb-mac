#!/usr/bin/env python3
"""Generate the first geometry-authority golden for v10."""

import argparse

from gen_v9_units import make_unit


def add_recorded_chroma(unit, first_row, last_row):
    """Give rows decoder noise while leaving their luma untouched."""
    raster = memoryview(unit)[48:]
    for row in range(first_row, last_row + 1):
        line = raster[row * 1440:(row + 1) * 1440]
        for x in range(720):
            line[x * 2] = 124 if (x + row) & 1 else 132


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # The picture envelope and line account stay at +2 throughout.  Only the
    # parity-valid caption moves to +3 for the middle unit.  Rule 1 requires
    # geometry to place all three units at +2 and records the caption conflict
    # without giving it a vote.
    units = [
        make_unit(0, picture=(2, 0), captions=((2, 0x14, 0x2c), None),
                  base_bottoms=(250, 518), content_phases=(0, 0),
                  content_shifts=(2, 0)),
        make_unit(1, picture=(2, 0), captions=((3, 0x15, 0x2b), None),
                  base_bottoms=(250, 518), content_phases=(0, 0),
                  content_shifts=(2, 0)),
        make_unit(2, picture=(2, 0), captions=((2, 0x16, 0x2a), None),
                  base_bottoms=(250, 518), content_phases=(0, 0),
                  content_shifts=(2, 0)),
    ]

    # Recorded black can have the same luma as regenerated blanking. Decoder
    # chroma noise still identifies it as source picture; no fixed luma delta
    # may erase the field.
    dark = make_unit(3, picture=(0, 0), field_luma=(2, None),
                     base_bottoms=(250, 518), content_phases=(0, 0))
    add_recorded_chroma(dark, 19, 250)
    units.append(dark)

    # The first picture row remains the top even when the two rows after it
    # are black picture. A three-consecutive-bright-row gate incorrectly
    # promotes the later bright body to the top.
    first_row = make_unit(4, picture=(0, 0), top_overrides=(22, None),
                          base_bottoms=(250, 518), bright_rows=(19,),
                          content_phases=(0, 0))
    add_recorded_chroma(first_row, 19, 250)
    units.append(first_row)
    with open(args.output, "wb") as output:
        for unit in units:
            output.write(unit)
    print(f"wrote {len(units)} v10 rule-1 units")


if __name__ == "__main__":
    main()
