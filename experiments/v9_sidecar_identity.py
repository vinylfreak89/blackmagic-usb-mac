#!/usr/bin/env python3
"""Require renderer and frameserver v9 sidecars to apply identical phases.

The renderer calls its counter column ``extended_counter`` and the frameserver
calls it ``counter_extended``.  Both are the same unwrapped device counter.
Only exact E801 units are comparable: diagnostic short-unit rows do not carry a
new registration decision in either pipeline.
"""

import argparse
import collections
import csv


def _load_renderer(path):
    rows = {}
    with open(path, newline="") as source:
        for row in csv.DictReader(source):
            if row.get("unit_state") != "Exact":
                continue
            counter = int(row["extended_counter"])
            if counter in rows:
                raise ValueError(f"renderer counter is not unique: {counter}")
            rows[counter] = row
    return rows


def _load_frameserver(path):
    rows = {}
    with open(path, newline="") as source:
        for row in csv.DictReader(source):
            if row.get("transport") != "Complete" or row.get("kind") != "0":
                continue
            counter = int(row["counter_extended"])
            if counter in rows:
                raise ValueError(f"frameserver counter is not unique: {counter}")
            rows[counter] = row
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("renderer_sidecar")
    parser.add_argument("frameserver_sidecar")
    args = parser.parse_args()

    renderer = _load_renderer(args.renderer_sidecar)
    frameserver = _load_frameserver(args.frameserver_sidecar)
    renderer_only = sorted(renderer.keys() - frameserver.keys())
    frameserver_only = sorted(frameserver.keys() - renderer.keys())
    if renderer_only or frameserver_only:
        raise SystemExit(
            "counter sets differ: "
            f"renderer-only={len(renderer_only)} frameserver-only={len(frameserver_only)}; "
            f"first renderer-only={renderer_only[:5]} first frameserver-only={frameserver_only[:5]}"
        )

    classes = collections.Counter()
    examples = []
    for counter in sorted(renderer):
        rr = renderer[counter]
        fr = frameserver[counter]
        renderer_pair = (int(rr["applied_d1"]), int(rr["applied_d2"]))
        frameserver_pair = (int(fr["applied_d1"]), int(fr["applied_d2"]))
        if renderer_pair != frameserver_pair:
            classes[(renderer_pair, frameserver_pair)] += 1
            if len(examples) < 20:
                examples.append(
                    (counter, renderer_pair, frameserver_pair,
                     rr.get("mode", ""), fr.get("registration_mode", ""))
                )

    differences = sum(classes.values())
    print(
        f"compared={len(renderer)} differences={differences} "
        f"renderer_only=0 frameserver_only=0"
    )
    for (renderer_pair, frameserver_pair), count in classes.most_common():
        print(f"  {count}: renderer={renderer_pair} frameserver={frameserver_pair}")
    for counter, renderer_pair, frameserver_pair, renderer_mode, frameserver_mode in examples:
        print(
            f"  example counter={counter} renderer={renderer_pair} "
            f"frameserver={frameserver_pair} modes={renderer_mode}/{frameserver_mode}"
        )
    if differences:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
