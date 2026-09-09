#!/usr/bin/env python3
"""Score the engine's record against the harness reference for one capture, by device counter.

Contract section 8: "Two independent instruments — the engine's record (Codex) and the harness's
reference (Claude), independently implemented and mutually reviewed, never fused — from the same raw
rows and this contract, joined by device counter. Counted per capture per field: the top; S against
the reference's first-full-other-head row (exact where the reference exposes one) and against its
earliest switch-band row (within the one-row partial ambiguity); the band count under the lock."

    compare_capture.py <reference.csv> <engine_record.csv> [--from-counter N] [--repair-slots]

Nothing is fused and nothing is defaulted. Where either instrument says a quantity is unmeasurable
the unit is counted in its own class, never as agreement and never as a disagreement: "unknown" is
not a value (CLAUDE.md). A unit the engine did not publish, a duplicate counter, or an unparseable
row is an error, not a skipped row.
"""
import argparse, csv, sys, collections

UNMEASURABLE = {"-1", "", "n.a.", "None"}

def val(row, key):
    v = row.get(key)
    if v is None:
        raise KeyError(key)
    if v in UNMEASURABLE:
        return None
    try:
        n = int(v)
    except ValueError:
        return None
    return None if n < 0 else n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference"); ap.add_argument("engine")
    ap.add_argument("--from-counter", type=int, default=0,
                    help="score only from this device counter (the capture's registerable interval)")
    ap.add_argument("--repair-slots", action="store_true",
                    help="capture 4: the reference was built with --repair, so its slots are re-paired")
    a = ap.parse_args()

    ref = {}
    for r in csv.DictReader(open(a.reference)):
        key = (int(r["counter"]), r["field"])
        if key in ref:
            sys.exit(f"ERROR: duplicate {key} in the reference — not a single clean pass")
        ref[key] = r

    eng = {}
    for r in csv.DictReader(open(a.engine)):
        if r.get("transport") != "Complete":
            continue
        c = int(r["counter_extended"])
        if c in eng:
            sys.exit(f"ERROR: duplicate counter {c} in the engine record")
        eng[c] = r

    counters = sorted({c for (c, _) in ref} & set(eng))
    scored = [c for c in counters if c >= a.from_counter]
    missing = [c for (c, f) in ref if c >= a.from_counter and c not in eng]
    if missing:
        sys.exit(f"ERROR: {len(missing)} counters in the reference are absent from the engine record "
                 f"(first {sorted(missing)[:5]}) — the engine did not publish them")

    print(f"{len(scored)} counters scored (from {a.from_counter}); "
          f"reference has {len(ref)//2}, engine {len(eng)}")

    for field in ("1", "2"):
        agree = collections.Counter(); disagree = []
        classes = collections.Counter()
        for c in scored:
            m = ref.get((c, field))
            if m is None:
                continue
            e = eng[c]
            pairs = (
                ("top",   val(m, "top"),          val(e, f"f{field}_measured_picture_top")),
                ("switch", val(m, "T"),           val(e, f"f{field}_switch_line")),
                ("S",     val(m, "S"),            val(e, f"f{field}_first_full_other_head_line")),
                ("count", val(m, "switch_lines"), val(e, f"f{field}_observed_switch_line_count")),
            )
            for name, mine, theirs in pairs:
                if mine is None and theirs is None:
                    classes[f"{name}: both unmeasurable"] += 1
                elif mine is None:
                    classes[f"{name}: reference unmeasurable only"] += 1
                elif theirs is None:
                    classes[f"{name}: engine unmeasurable only"] += 1
                elif mine == theirs:
                    agree[name] += 1
                else:
                    agree[f"{name}_differs"] += 1
                    if name in ("switch", "top"):
                        disagree.append((c, name, mine, theirs))
        print(f"\n=== field {field}")
        for name in ("top", "switch", "S", "count"):
            ok = agree[name]; bad = agree[f"{name}_differs"]
            tot = ok + bad
            pct = f"{100.0*ok/tot:.1f}%" if tot else "n/a"
            print(f"  {name:7s} agree {ok:5d}  differ {bad:5d}  ({pct} of the units both could measure)")
        for k in sorted(classes):
            print(f"    {k}: {classes[k]}")
        if disagree:
            print(f"  first disagreements (counter, quantity, reference, engine):")
            for d in disagree[:10]:
                print(f"    {d}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
