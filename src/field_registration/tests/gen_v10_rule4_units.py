#!/usr/bin/env python3
"""Generate the fixed switch-line-count lock golden."""

import argparse

from gen_v10_rule3_units import account_unit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # The first unit's pass-through caption confirms d=+2 while its measured
    # visible band is one line: the lock takes count 1+2=3. Three later units
    # claim a count of four. Repetition must not re-learn the lock. The last
    # unit returns to the confirmed geometry.
    units = [account_unit(0, 2, switch1=258, caption_d=2)]
    units.extend(account_unit(counter, 2, switch1=257)
                 for counter in range(1, 4))
    units.append(account_unit(4, 2, switch1=258))

    with open(args.output, "wb") as output:
        for unit in units:
            output.write(unit)
    print(f"wrote {len(units)} v10 rule-4 units")


if __name__ == "__main__":
    main()
