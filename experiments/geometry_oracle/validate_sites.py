#!/usr/bin/env python3
"""Regenerate raw oracle tables for the owner-selected fixture-A sites."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from oracle import measure_file, parse_ranges


@dataclass(frozen=True)
class Site:
    name: str
    path: str
    base_ordinal: int
    selection: str | None = None


# Base ordinals are the transport-observation ordinals used by the owner.  They
# intentionally include the three leading unframed observations and the seven
# device-short observations preceding the later fixture slices.
SITES = (
    Site("unit_300", "/private/tmp/hw-session/w_10s.tpc", 3, "294-304"),
    Site("minute_01_26", "/private/tmp/hw-session/w_86s.tpc", 2540),
    Site("minute_05_00", "/private/tmp/hw-session/w_300s.tpc", 8990),
    Site("minute_35_00", "/private/tmp/hw-session/w_2100s.tpc", 62900),
    Site("minute_37_01", "/private/tmp/hw-session/w_2216s.tpc", 66420),
    Site("minute_43", "/private/tmp/hw-session/w_43m_77890.tpc", 77887),
    Site("damage_34_16", "/private/tmp/hw-session/w_3416.tpc", 61586),
    Site("damage_34_35", "/private/tmp/hw-session/w_3435.tpc", 62130),
    Site("damage_34_40", "/private/tmp/hw-session/w_3440.tpc", 62325),
    Site("transition_24_20", "/private/tmp/hw-session/w_2417.tpc", 43574, "105-175"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "reports" / "sites",
    )
    parser.add_argument("--site", action="append", help="regenerate only the named site")
    args = parser.parse_args()
    selected_names = set(args.site or [])
    unknown = selected_names - {site.name for site in SITES}
    if unknown:
        parser.error(f"unknown site(s): {', '.join(sorted(unknown))}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for site in SITES:
        if selected_names and site.name not in selected_names:
            continue
        source = Path(site.path)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = args.output_dir / f"{site.name}.csv"
        count = measure_file(
            source,
            destination,
            base_ordinal=site.base_ordinal,
            selected=parse_ranges(site.selection) if site.selection else None,
            allow_slice_boundary_provenance=True,
        )
        print(f"{site.name}: {count} rows -> {destination}")
        total += count
    print(f"owner sites: {total} measured rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
