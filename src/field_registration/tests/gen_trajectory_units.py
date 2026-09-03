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
    main_ranges: tuple[tuple[int, int], ...] = ((0, 560),)
    secondary_ranges: tuple[tuple[int, int], ...] = ((560, 720),)
    vbi_present: bool = True
    flat_y: int = 2
    secondary_animated: bool = True
    main_motion: bool = False
    main_top_trim: int = 0
    obscure_edges: bool = False
    clip_at_padding: bool = False
    alternating_card: bool = False
    force_scene_cut: bool = False
    fake_bottom_censor: bool = False


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

    # Unit-rate motion is physical truth when both program-envelope edges move
    # coherently and same-parity picture content follows the same displacement.
    # A trajectory filter must follow these units, not smooth them merely
    # because their dwell is one frame.
    for index in range(24):
        phase = (1, 0) if index & 1 else (0, 0)
        out.append(Step("physical-field1-unit-rate-jitter", phase, phase,
                        unsettled=True, main_ranges=((0, 720),),
                        secondary_ranges=()))
    add(12, "after-physical-field1-jitter", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    # Real heterogeneous rasters need not expose a nominal-height absolute
    # envelope. Here the main layer's first three active rows are absent, so
    # top and bottom imply different absolute offsets. Both landmarks and all
    # broad bands still move by the same +/-1 delta, and temporal correlation
    # corroborates it. The live delta-authority path must FOLLOW every unit.
    for index in range(24):
        phase = (1, 0) if index & 1 else (0, 0)
        out.append(Step("physical-multiphase-envelope-jitter", phase, phase,
                        unsettled=True, reset_before=index == 0,
                        main_ranges=((0, 720),), secondary_ranges=(),
                        main_top_trim=3))
    out.append(Step("after-physical-multiphase-jitter", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(11, "after-physical-multiphase-jitter", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    for index in range(24):
        phase = (1, 1) if index & 1 else (0, 0)
        out.append(Step("physical-common-plus-unit-rate-jitter", phase, phase,
                        unsettled=True, main_ranges=((0, 720),),
                        secondary_ranges=()))
    add(12, "after-physical-common-plus-jitter", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    for index in range(24):
        phase = (-1, -1) if index & 1 else (0, 0)
        out.append(Step("physical-common-minus-unit-rate-jitter", phase, phase,
                        unsettled=True, main_ranges=((0, 720),),
                        secondary_ranges=()))
    add(12, "after-physical-common-minus-jitter", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    # Relative-only truth.  The body moves while deliberately uninformative
    # source-carried top/bottom strips keep the absolute envelope from naming
    # an (d1,d2) gauge.  This is the measured residual class: a strong +1
    # phase is committed, then the raster returns to nominal for a short run.
    # The current engine holds +1 because its relative vote cannot open a new
    # absolute pair.  Same-parity body motion identifies field 1 on the return.
    out.append(Step("relative-release-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(40, "relative-release-lock-10", (1, 0), (1, 0),
        main_ranges=((0, 720),), secondary_ranges=())
    add(12, "relative-only-return-temporal-gauge", (0, 0), (0, 0),
        unsettled=True, obscure_edges=True, main_ranges=((0, 720),),
        secondary_ranges=())
    # A relative-only presentation must not replace the last absolute lock.
    # With no evidence on the following unit, hold (1,0), not the relative
    # (0,0) representation that was valid only for the measured unit.
    add(1, "relative-only-following-abstain", None, (1, 0), gain=0.0,
        unsettled=True, vbi_present=False)
    add(12, "relative-release-back-10", (1, 0), (1, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    # Mirror guard: loss of absolute edges while the correctly registered +1
    # state becomes static must not release it.  Its raw relative phase still
    # says +1 even though same-parity temporal displacement is now zero.
    add(12, "relative-only-sustained-plus1-guard", (1, 0), (1, 0),
        obscure_edges=True, main_ranges=((0, 720),), secondary_ranges=())

    # A relative-only onset whose same-parity displacement identifies field 1.
    add(12, "relative-only-onset-temporal-gauge", (2, 0), (2, 0),
        unsettled=True, obscure_edges=True, main_ranges=((0, 720),),
        secondary_ranges=())
    add(12, "relative-only-onset-return-10", (1, 0), (1, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    # No prior absolute gauge: the first unit is honestly unresolvable.  Once
    # same-parity history establishes a static body, the relative phase is
    # usable but field identity remains unknown.  The live presentation uses
    # the deterministic minimum-crop/prior representation (0,+1).
    out.append(Step("relative-gauge-unknown-reset", None, (0, 0),
                    reset_before=True, vbi_present=True))
    out.append(Step("relative-gauge-unknown-warmup", (0, 1), (0, 0),
                    obscure_edges=True, main_ranges=((0, 720),),
                    secondary_ranges=(), unsettled=True))
    add(15, "relative-only-gauge-unknown", (0, 1), (0, 1),
        obscure_edges=True, main_ranges=((0, 720),), secondary_ranges=(),
        unsettled=True)

    # False-positive guards for the static-region comb vote. Each guard gets
    # an independent nominal lock so a preceding deliberately gauge-unknown
    # scenario cannot contaminate its expected fallback.
    out.append(Step("relative-guard-card-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(12, "relative-guard-card-baseline", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())
    add(12, "relative-guard-alternating-card", (0, 0), (0, 0),
        alternating_card=True, obscure_edges=True,
        main_ranges=((0, 720),), secondary_ranges=())

    out.append(Step("relative-guard-overlay-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(12, "relative-guard-overlay-baseline", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())
    add(12, "relative-guard-local-overlay", (0, 0), (0, 0),
        obscure_edges=True, main_ranges=(), secondary=(1, 0),
        secondary_ranges=((600, 640),), secondary_animated=False)

    out.append(Step("relative-guard-cut-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(12, "relative-guard-cut-baseline", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())
    out.append(Step("relative-guard-scene-cut", (0, 0), (0, 0), scene=2,
                    obscure_edges=True, force_scene_cut=True,
                    main_ranges=((0, 720),), secondary_ranges=()))

    out.append(Step("relative-guard-motion-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(12, "relative-guard-motion-baseline", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())
    add(12, "relative-guard-interfield-motion", (0, 0), (0, 0),
        obscure_edges=True, main_motion=True, main_ranges=((0, 720),),
        secondary_ranges=())

    out.append(Step("relative-guard-nominal-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(12, "relative-guard-nominal", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    # A physically clipped field at the format boundary.  Field 1 moves +5;
    # source lines that would occupy hard-padding row 261 are omitted.  The
    # top/body motion supplies magnitude, while bottom==260 is censored rather
    # than an exact +4 vote.  Repeated leading rows and chroma are deliberately
    # absent from the authority condition.
    out.append(Step("bottom-censored-reset", (0, 0), (0, 0),
                    reset_before=True, main_ranges=((0, 720),),
                    secondary_ranges=()))
    add(12, "bottom-censored-field1-plus5", (5, 0), (5, 0),
        unsettled=True, clip_at_padding=True, main_ranges=((0, 720),),
        secondary_ranges=())
    add(12, "bottom-censored-return-00", (0, 0), (0, 0),
        main_ranges=((0, 720),), secondary_ranges=())
    # Same apparent top/boundary landmarks, but a stationary body: the
    # temporal/body condition is false and the crop must remain nominal.
    add(12, "bottom-censored-static-card-guard", (0, 0), (0, 0),
        alternating_card=True, fake_bottom_censor=True,
        main_ranges=((0, 720),), secondary_ranges=())

    # Only the right-hand secondary asset moves. The designated main picture
    # remains at the committed phase, so following the edge-only artifact is a
    # policy error even if it is a plausible per-unit observation.
    out.append(Step("secondary-edge-artifact", (1, 0), (1, 0),
                    secondary=(0, 1), unsettled=True, reset_before=True))
    add(7, "secondary-edge-artifact", (1, 0), (1, 0),
        secondary=(0, 1), unsettled=True)
    add(12, "after-secondary-artifact", (1, 0), (1, 0))

    # An explicit negative control for the FOLLOW rule. Only a narrow,
    # secondary asset alternates; the broad main envelope is stationary.
    for index in range(24):
        secondary = (0, 1) if index & 1 else (2, 0)
        out.append(Step("false-edge-chatter", (1, 0), (1, 0),
                        secondary=secondary, unsettled=True,
                        main_ranges=((0, 720),),
                        secondary_ranges=((560, 640),)))
    add(12, "after-false-edge-chatter", (1, 0), (1, 0),
        main_ranges=((0, 720),), secondary_ranges=())

    # Synthetic form of the timeline-frame-8169 stale latch. The triggering
    # unit is coherent physical truth and is allowed to present (0,1); the bug
    # was holding that one observation across 103 later abstentions after the
    # committed (1,0) path contradicted it.
    add(1, "stale-positive-trigger-01", (0, 1), (0, 1), unsettled=True)
    add(103, "stale-positive-flat-hold", None, (1, 0), gain=0.0,
        unsettled=True)
    add(20, "stale-positive-recovery-10", (1, 0), (1, 0))

    # Decoder-style inversion: provisional geometry first supports (0,1), then
    # settles at (1,0). The oracle may revise the provisional portion because
    # both interval endpoints are (1,0); raster truth preserves what existed.
    add(10, "inversion-provisional-01", (0, 1), (1, 0), unsettled=True)
    add(35, "inversion-settled-10", (1, 0), (1, 0))

    # Estimator chatter is deliberately WEAK and conflicting. The main raster
    # stays at the committed phase; only a narrow secondary layer alternates.
    # Coherently moving the complete raster here would incorrectly teach the
    # policy to suppress real physical unit-rate motion.
    for index in range(20):
        secondary = (0, 1) if index & 1 else (2, 0)
        out.append(Step("phase-chatter", (1, 0), (1, 0),
                        secondary=secondary, unsettled=True,
                        main_ranges=((0, 720),),
                        secondary_ranges=((600, 680),)))
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

    # Boundary coverage missing from the original golden. The current top-edge
    # search can represent -1 exactly, but censors -2 while the bottom edge
    # remains measurable. Raster and trajectory truth agree: these are real
    # physical translations, not policy-only corrections.
    add(35, "upward-minus1-field1", (-1, 0), (-1, 0), scene=1)
    add(18, "after-upward-minus1", (0, 0), (0, 0), scene=1)
    add(40, "upward-minus2-field1", (-2, 0), (-2, 0), scene=1)
    add(18, "after-upward-minus2-field1", (0, 0), (0, 0), scene=1)
    add(40, "upward-minus2-field2", (0, -2), (0, -2), scene=1)
    add(18, "after-upward-minus2-field2", (0, 0), (0, 0), scene=1)
    add(40, "upward-minus2-common", (-2, -2), (-2, -2), scene=1)
    add(18, "after-upward-minus2-common", (0, 0), (0, 0), scene=1)

    # The underlying main picture spans the complete width at (1,0), while
    # two full motion-evidence bands are overwritten by a secondary layer at
    # (0,1). This deliberately gives the per-band voter and the designated
    # global/main-picture truth different answers.
    out.append(Step("multiphase-reset", (1, 0), (1, 0), scene=2,
                    reset_before=True, main_ranges=((0, 720),)))
    add(44, "multiphase-main-10", (1, 0), (1, 0), scene=2,
        secondary=(0, 1), main_ranges=((0, 720),),
        secondary_ranges=((48, 248), (472, 672)), unsettled=True,
        secondary_animated=False, main_motion=True)
    add(20, "after-multiphase-main-10", (1, 0), (1, 0), scene=2,
        main_ranges=((0, 720),))

    # Enter a real candidate, then remove reliable visual evidence during a
    # fade. The 29-unit prefix is one unit short of the current confirmation
    # requirement so the fade begins while the candidate is active.
    out.append(Step("fade-candidate-reset", (0, 0), (0, 0), scene=0,
                    reset_before=True))
    add(39, "fade-candidate-baseline-00", (0, 0), (0, 0), scene=0)
    add(29, "fade-active-candidate-10", (1, 0), (1, 0), scene=0,
        unsettled=True)
    fade_gains = (0.80, 0.60, 0.40, 0.20, 0.0, 0.0, 0.20, 0.40, 0.60, 0.80)
    for gain in fade_gains:
        out.append(Step("fade-with-active-candidate", (1, 0), (1, 0),
                        scene=0, gain=gain, unsettled=True))
    add(35, "fade-candidate-settled-10", (1, 0), (1, 0), scene=0)

    # Missing picture evidence must not be confused with broken transport.
    # Both classes retain byte-exact hard padding. The first retains the VBI
    # fiducial over a flat legal-black raster; the second deliberately removes
    # all content/VBI while preserving the same transport ruler.
    out.append(Step("flat-candidate-reset", (0, 0), (0, 0), scene=1,
                    reset_before=True))
    add(39, "flat-candidate-baseline-00", (0, 0), (0, 0), scene=1)
    add(29, "flat-active-candidate-10", (1, 0), (1, 0), scene=1,
        unsettled=True)
    add(10, "flat-dark-intact-padding-vbi", None, (1, 0), scene=1,
        flat_y=16, unsettled=True)
    add(10, "flat-blank-intact-padding-no-vbi", None, (1, 0), scene=1,
        flat_y=2, vbi_present=False, unsettled=True)
    add(35, "flat-candidate-recovery-10", (1, 0), (1, 0), scene=1)
    return out


def put_span(destination: bytearray, source: bytes, x0: int, x1: int) -> None:
    start = x0 * 2
    stop = x1 * 2
    destination[start:stop] = source[start:stop]


def make_unit(counter: int, index: int, step: Step,
              templates: dict[tuple[int, int, int, int], list[bytes]],
              seed: int) -> bytes:
    blank = bytes((128, step.flat_y)) * 720
    hard = bytes((128, 16)) * 720
    raster = [bytearray(blank) for _ in range(base.LINES)]
    for lo, hi in base.HARD_RANGES:
        for line in range(lo, hi + 1):
            raster[line][:] = hard
    if step.vbi_present:
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
                if row < step.main_top_trim:
                    continue
                if step.main_motion:
                    line = source[(row + phase * 2) % len(source)]
                if step.alternating_card:
                    level = 56 if (row & 1) == 0 else 188
                    line = bytes((128, level)) * 720
                line = base.scaled_line(line, step.gain)
                for x0, x1 in step.main_ranges:
                    destination = top + displacement + row
                    if destination < 0 or destination >= base.LINES:
                        continue
                    if step.clip_at_padding and any(
                            lo <= destination <= hi for lo, hi in base.HARD_RANGES):
                        continue
                    put_span(raster[destination], line, x0, x1)

    # By default the rightmost 160 pixels form the independently phased
    # secondary asset. Scenarios may place it in complete evidence bands to
    # construct a deliberately heterogeneous raster.
    secondary = step.secondary if step.secondary is not None else step.raster
    if secondary is not None:
        for parity, top, displacement in (
            (0, base.F1_TOP, secondary[0]),
            (1, base.F2_TOP, secondary[1]),
        ):
            secondary_phase = phase if step.secondary_animated else 0
            source = templates[((step.scene + 1) % 3, secondary_phase,
                                parity, 100)]
            for row, line in enumerate(source):
                line = base.scaled_line(line, step.gain)
                for x0, x1 in step.secondary_ranges:
                    put_span(raster[top + displacement + row], line, x0, x1)

    if step.obscure_edges and step.raster is not None:
        # Remove enough of both source-carried boundaries that top and bottom
        # no longer form a nominal-height absolute envelope.  The inner 220+
        # rows remain untouched for temporal and relative registration.
        for top, bottom in ((base.F1_TOP, base.F1_BOTTOM),
                            (base.F2_TOP, base.F2_BOTTOM)):
            for line in range(top, top + 6):
                raster[line][:] = blank
            for line in range(bottom - 5, bottom + 1):
                raster[line][:] = blank

    if step.force_scene_cut:
        # Change both fields globally, including their interior texture.  The
        # scene-cut gate must outrank any accidental relative minimum.
        for top, bottom in ((base.F1_TOP + 8, base.F1_BOTTOM - 8),
                            (base.F2_TOP + 8, base.F2_BOTTOM - 8)):
            for line in range(top, bottom + 1):
                for x in range(1, base.BPL, 2):
                    raster[line][x] = 230 - raster[line][x] // 2

    if step.fake_bottom_censor:
        # A boundary-shaped decoy with no body translation.  Top appears at
        # +5 and picture reaches the final ADC row before hard padding, but
        # same-parity registration of the broad body remains zero.
        for line in range(base.F1_TOP, base.F1_TOP + 5):
            raster[line][:] = blank
        source = templates[(step.scene, phase, 0, 100)]
        for line in range(257, 261):
            raster[line][:] = source[-1]

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
