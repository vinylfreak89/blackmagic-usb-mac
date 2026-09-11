#!/usr/bin/env python3
"""Synthetic algebra checks for the proposed set observable, not a detector repair.

No captures, source classification, or D16 verdicts. The union/intersection and
leave-one-out maximum below implement explicit candidate choices for review only.
"""
import numpy as np

from source_reference import settled_samples


def mask(*intervals):
    result = np.zeros(720, dtype=bool)
    for start, end in intervals:
        result[start:end] = True
    return result


def expectation(rows):
    return np.logical_and.reduce(rows), ~np.logical_or.reduce(rows)


def departure(row, expected):
    expected_blank, expected_nonblank = expected
    return (int(np.count_nonzero(row & expected_nonblank)),
            int(np.count_nonzero(~row & expected_blank)))


def loo_max(rows):
    scores = [departure(row, expectation(rows[:i] + rows[i + 1:]))
              for i, row in enumerate(rows)]
    return tuple(np.max(scores, axis=0).tolist())


def main():
    reference = [mask((700, 716)) for _ in range(13)]
    expected = expectation(reference)
    print("ONE FIXED, KNOWN-INTERVAL REFERENCE; EXACT SYNTHETIC SAMPLES")
    cases = [
        ("translated", mask((400, 416)), (16, 16)),
        ("split", mask((400, 408), (600, 608)), (16, 16)),
        ("start extends left", mask((690, 716)), (10, 0)),
        ("end extends to delivered edge", mask((700, 720)), (4, 0)),
        ("end moves but remains visible", mask((700, 718)), (2, 0)),
    ]
    for name, row, want in cases:
        got = departure(row, expected)
        assert got == want
        print(name, "b,p", got)

    # Same sampled signal, two constructions: moved blanking boundary, or dark
    # picture added before an unchanged blanking interval. Identity is not an input
    # to a level mask, so this observation cannot discriminate the constructions.
    timing_extension = np.where(mask((690, 716)), 1.4, 90.)
    unchanged_timing = np.where(mask((700, 716)), 1.4, 90.)
    unchanged_timing[690:700] = 1.4
    assert np.array_equal(timing_extension, unchanged_timing)
    print("start extension vs dark-picture addition: identical sampled row True")

    # Both directions also fire when a dark patch moves and the actual blanking
    # interval (0:5) stays unchanged throughout. Low-valued is not an identity.
    dark_reference = [mask((0, 5), (700, 716)) for _ in range(13)]
    got = departure(mask((0, 5), (400, 416)), expectation(dark_reference))
    assert got == (16, 16)
    print("dark picture moves; true blanking unchanged: b,p", got)

    print("ONE EXTRA LOW-LEVEL REGION IN ONE CALIBRATION ROW")
    contaminated = reference[:-1] + [mask((700, 716), (400, 450))]
    target = mask((400, 416))
    clean = departure(target, expected)
    contaminated_score = departure(target, expectation(contaminated))
    tolerance = loo_max(contaminated)
    assert (clean, contaminated_score, tolerance) == ((16, 16), (0, 16), (50, 0))
    print("same target: clean", clean, "contaminated", contaminated_score,
          "LOO maxima", tolerance)

    # One above-maximum known-blanking sample erases a sample from intersection.
    # Since level masking is binary, its complement would then call it picture.
    noisy_reference = [row.copy() for row in reference]
    noisy_reference[-1][705] = False
    expected_blank, _ = expectation(noisy_reference)
    assert not expected_blank[705]
    print("one level-mask miss erases expected blank at 705:", not expected_blank[705])

    # Source pool selection is not automatically qualified by its function name.
    # All six samples here are specified as true, settled noisy blanking.
    known_blank = np.array([3., 1., 3., 1., 1., 1.])
    selected = settled_samples(known_blank, 0)
    assert selected is not None and selected.max() == 1.
    print("known settled blanking: mean", known_blank.mean(), "max", known_blank.max(),
          "selected mean", selected.mean(), "selected max", selected.max())
    print("ALGEBRA/DEPENDENCY CONTROLS PASS; no switch identity was certified")


if __name__ == "__main__":
    main()
