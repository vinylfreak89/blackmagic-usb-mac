#!/usr/bin/env python3
"""Generate the capture-free registration-trajectory design fixture.

The output is a raw concatenation of exact 756,048-byte e801 units plus a CSV
with two deliberately separate truths:

* raster_d1/raster_d2: the physical location of the designated main picture;
* trajectory_d1/trajectory_d2: the endpoint-constrained policy oracle.

Some units contain a secondary horizontal asset at a conflicting phase.  That
asset is evidence, never truth.  ``raster_known=0`` means the main picture is
intentionally flat/absent, so no physical offset can be asserted for that unit.
This fixture describes the gated trajectory redesign; it does not change the
current estimator.
"""

from __future__ import annotations

import argparse
import csv
import struct
from dataclasses import dataclass
from pathlib import Path

import gen_registration_units as base


@dataclass(frozen=True)
class Step:
    scenario: str
    raster: tuple[int, int] | None
    oracle: tuple[int, int]
    secondary: tuple[int, int] | None = None
    scene: int = 0
    gain: float = 1.0
    reset_before: bool = False
    unsettled: bool = False


def trajectory() -> list[Step]:
    out: list[Step] = []

    def add(count: int, scenario: str, raster: tuple[int, int] | None,
            oracle: tuple[int, int], **kwargs: object) -> None:
        out.extend(Step(scenario, raster, oracle, **kwargs) for _ in range(count))

    # Establish a non-zero committed phase. This is essential: the stale-latch
    # defect is invisible when every fallback happens to be raw (0,0).
    add(50, "locked-main-10", (1, 0), (1, 0))

    # A real one-unit displacement must remain representable by the future path
    # solver. Raster and policy truth intentionally agree here.
    add(1, "physical-single-20", (2, 0), (2, 0), unsettled=True)
    add(18, "physical-single-return-10", (1, 0), (1, 0))

    # Only the right-hand secondary asset moves. The designated main picture
    # remains at the committed phase, so following the edge-only artifact is a
    # policy error even if it is a plausible per-unit observation.
    add(8, "secondary-edge-artifact", (1, 0), (1, 0),
        secondary=(0, 1), unsettled=True)
    add(12, "after-secondary-artifact", (1, 0), (1, 0))

    # Synthetic form of the timeline-frame-8169 stale latch: one coherent but
    # provisional positive observation, followed by 103 units with no spatial
    # phase evidence. The locked trajectory contradicts (0,1), so the policy
    # oracle remains (1,0). The current caller is expected to hold (0,1).
    add(1, "stale-positive-trigger-01", (0, 1), (1, 0), unsettled=True)
    add(103, "stale-positive-flat-hold", None, (1, 0), gain=0.0,
        unsettled=True)
    add(20, "stale-positive-recovery-10", (1, 0), (1, 0))

    # Decoder-style inversion: provisional geometry first supports (0,1), then
    # settles at (1,0). The oracle may revise the provisional portion because
    # both interval endpoints are (1,0); raster truth preserves what existed.
    add(10, "inversion-provisional-01", (0, 1), (1, 0), unsettled=True)
    add(35, "inversion-settled-10", (1, 0), (1, 0))

    # Chatter alternates coherent positive observations. The future path must
    # not mistake each one for a new committed trajectory.
    for index in range(20):
        raster = (0, 1) if index & 1 else (2, 0)
        out.append(Step("phase-chatter", raster, (1, 0), unsettled=True))
    add(35, "post-chatter-10", (1, 0), (1, 0))

    # A non-settling interval reaches the future horizon. Its oracle is the
    # best endpoint-constrained path, not a demand to flatten raw geometry.
    for index in range(76):
        raster = (0, 1) if (index // 4) & 1 else (2, 0)
        out.append(Step("unresolved-horizon", raster, raster, unsettled=True))

    # Epoch reset: no state from the prior unresolved path may leak across it.
    out.append(Step("segment-reset", (0, 0), (0, 0), scene=1,
                    reset_before=True))
    add(40, "segment2-locked-00", (0, 0), (0, 0), scene=1)
    return out


def put_span(destination: bytearray, source: bytes, x0: int, x1: int) -> None:
    start = x0 * 2
    stop = x1 * 2
    destination[start:stop] = source[start:stop]


def make_unit(counter: int, index: int, step: Step,
              templates: dict[tuple[int, int, int, int], list[bytes]],
              seed: int) -> bytes:
    blank = bytes((128, 2)) * 720
    hard = bytes((128, 16)) * 720
    raster = [bytearray(blank) for _ in range(base.LINES)]
    for lo, hi in base.HARD_RANGES:
        for line in range(lo, hi + 1):
            raster[line][:] = hard
    raster[16][:] = base.vbi_line(seed, 0, 0)
    raster[17][:] = base.vbi_line(seed, 0, 1)
    raster[279][:] = base.vbi_line(seed, 1, 0)
    raster[280][:] = base.vbi_line(seed, 1, 1)

    phase = index & 3
    if step.raster is not None:
        for parity, top, displacement in (
            (0, base.F1_TOP, step.raster[0]),
            (1, base.F2_TOP, step.raster[1]),
        ):
            source = templates[(step.scene, phase, parity, 100)]
            for row, line in enumerate(source):
                line = base.scaled_line(line, step.gain)
                put_span(raster[top + displacement + row], line, 0, 560)

    # The rightmost 160 pixels form the independently phased secondary asset.
    # It is deliberately substantial enough to be evidence, but smaller than
    # the designated main-picture area.
    secondary = step.secondary if step.secondary is not None else step.raster
    if secondary is not None:
        for parity, top, displacement in (
            (0, base.F1_TOP, secondary[0]),
            (1, base.F2_TOP, secondary[1]),
        ):
            source = templates[((step.scene + 1) % 3, phase, parity, 100)]
            for row, line in enumerate(source):
                line = base.scaled_line(line, step.gain)
                put_span(raster[top + displacement + row], line, 560, 720)

    header = bytearray(base.HEADER_BYTES)
    header[:4] = b"\x00\x00\xff\xff"
    struct.pack_into("<H", header, 4, counter & 0xFFFF)
    struct.pack_into("<H", header, 6, 0xE801)
    unit = bytes(header) + b"".join(bytes(line) for line in raster)
    assert len(unit) == base.UNIT_BYTES
    return unit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=0x5452414A)
    parser.add_argument("--noise", type=int, default=1)
    parser.add_argument("--start-counter", type=int, default=8000)
    args = parser.parse_args()
    if not 0 <= args.noise <= 8:
        parser.error("--noise must be in 0..8")

    steps = trajectory()
    templates = base.make_templates(args.seed, args.noise)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.truth.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as raw, args.truth.open("w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow((
            "unit_index", "counter", "segment", "scenario", "raster_known",
            "raster_d1", "raster_d2", "trajectory_d1", "trajectory_d2",
            "unsettled", "reset_before",
        ))
        segment = 0
        for index, step in enumerate(steps):
            if step.reset_before:
                segment += 1
            counter = (args.start_counter + index) & 0xFFFF
            raw.write(make_unit(counter, index, step, templates, args.seed))
            raster_d1, raster_d2 = step.raster or ("", "")
            writer.writerow((
                index, counter, segment, step.scenario, int(step.raster is not None),
                raster_d1, raster_d2, step.oracle[0], step.oracle[1],
                int(step.unsettled), int(step.reset_before),
            ))
    print(f"wrote {len(steps)} trajectory units to {args.output}")
    print(f"wrote two-truth oracle to {args.truth}")


if __name__ == "__main__":
    main()
