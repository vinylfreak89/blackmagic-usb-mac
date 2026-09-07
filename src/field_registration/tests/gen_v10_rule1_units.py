#!/usr/bin/env python3
"""Generate the first geometry-authority golden for v10."""

import argparse

from gen_v9_units import make_unit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # The picture envelope and line account stay at +2 throughout.  Only the
    # parity-valid caption moves to +3 for the middle unit.  Rule 1 requires
    # geometry to place all three units at +2 and records the caption conflict
    # without giving it a vote.
    units = (
        make_unit(0, picture=(2, 0), captions=((2, 0x14, 0x2c), None),
                  base_bottoms=(250, 518), content_phases=(0, 0),
                  content_shifts=(2, 0)),
        make_unit(1, picture=(2, 0), captions=((3, 0x15, 0x2b), None),
                  base_bottoms=(250, 518), content_phases=(0, 0),
                  content_shifts=(2, 0)),
        make_unit(2, picture=(2, 0), captions=((2, 0x16, 0x2a), None),
                  base_bottoms=(250, 518), content_phases=(0, 0),
                  content_shifts=(2, 0)),
    )
    with open(args.output, "wb") as output:
        for unit in units:
            output.write(unit)
    print(f"wrote {len(units)} v10 rule-1 units")


if __name__ == "__main__":
    main()
