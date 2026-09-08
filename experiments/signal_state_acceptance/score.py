#!/usr/bin/env python3
"""Score a frameserver decision log against the fixture, so a signal-state change cannot trade one
error for another (owner, 2026-09-09: "any changes should not introduce false positives (or false
negatives)").

    score.py <decision.csv> [--fixture experiments/signal_state_acceptance/fixture_a_units.csv]

The decision log is what `frameserver_replay` writes over the WHOLE of fixture A. Unit index =
device counter - 4511. Three counts, and the gate is that none of them may get worse:

  MISSED      units the fixture says are not normal picture, that the run calls ProgramLike/Present.
              Baseline 17, MEASURED against this fixture and the build at 44cfb94, not carried
              from any report. A change is only an improvement if this falls; it may never rise.
  FALSE_MUTE  units the fixture says are programme, that the run gives a mute/no-input label or a
              Muted/NoInput source. Baseline 108, measured the same way. This may never rise.
  UNGATED     units the fixture says are not normal picture, where the run still applied a
              registration displacement. Baseline 270. After rule 5 it must be 0 across every
              not_program range.
  FALSE_LOSS  units the fixture says are programme, that the run marks snow or a lock-like loss.
              Must be 0. This is a harder failure than a false mute: under rule 5b a lock-like loss
              resets the geometry, so a false one destroys a good lock on real picture. Added
              2026-09-09 after reviewing a classifier change that could newly produce one; the
              earlier version of this scorer could not see it.

A third class, `boundary`, is scored in NEITHER direction. It covers the relock ramps at the end of
an event, where adjacent-row coherence is climbing from the event's incoherent floor to settled
picture and neither answer is a defect. Demanding a verdict there would push the classifier toward
false positives, which is the failure this fixture exists to prevent (owner, 2026-09-09: "any
changes should not introduce false positives (or false negatives)"). Each range is derived from its
own event's tail, not typed in.

Fails closed: a missing unit, a duplicate counter, or an unparseable row is an error, not a skip."""
import csv, sys, argparse

MUTE_APPEARANCES = {"NeutralGrayMuteLike", "SubBlackMuteLike", "DeviceNoSignal0800"}
MUTE_SOURCES = {"Muted", "NoInput"}

def load_fixture(path):
    ranges = []
    for r in csv.DictReader(open(path)):
        ranges.append((int(r["first"]), int(r["last"]), r["expect"], r["note"]))
    return ranges

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decision")
    ap.add_argument("--fixture", default="experiments/signal_state_acceptance/fixture_a_units.csv")
    ap.add_argument("--counter-base", type=int, default=4511)
    a = ap.parse_args()

    # Only exact, complete units carry a fixed raster and a classification worth scoring. The log's
    # leading rows are unframed or other-format observations (the 0x0800 startup unit among them) and
    # share counter 0; they are skipped by transport, never by deduplication, so a genuine duplicate
    # among the exact units is still an error.
    rows = {}
    seen_any = set()          # every counter the log carries, whatever its transport
    non_exact = {}            # unit -> its transport, for units present but not fixed-raster
    skipped = 0
    with open(a.decision) as h:
        for r in csv.DictReader(h):
            try:
                c = int(r["counter_extended"])
            except (KeyError, ValueError) as e:
                sys.exit(f"ERROR: unparseable row: {e}")
            if c >= a.counter_base:
                seen_any.add(c - a.counter_base)
            if "lock_like_loss" in r:
                loss_column_present = True
            if r.get("transport") != "Complete":
                if c >= a.counter_base:
                    non_exact[c - a.counter_base] = r.get("transport", "?")
                skipped += 1
                continue
            if c < a.counter_base:
                skipped += 1
                continue
            u = c - a.counter_base
            if u in rows:
                sys.exit(f"ERROR: duplicate counter for unit {u} — the log is not a single clean pass")
            rows[u] = r
    if not rows:
        sys.exit("ERROR: no exact units in the log")
    print(f"scored {len(rows)} exact units; skipped {skipped} non-exact or pre-base rows")

    fixture = load_fixture(a.fixture)
    missed, false_mute, ungated, absent, not_applicable = [], [], [], [], []
    false_loss = []
    loss_column_present = False
    for first, last, expect, note in fixture:
        for u in range(first, last + 1):
            r = rows.get(u)
            if r is None:
                # A device-short or unframed unit has no fixed raster, so it carries no
                # classification to score. That is "not applicable", not a missing unit; only a
                # unit the log never mentions means the run did not cover the tape.
                if u in non_exact:
                    not_applicable.append(u)
                else:
                    absent.append(u)
                continue
            app, src = r.get("appearance", ""), r.get("source", "")
            if expect == "boundary":
                continue
            if expect.startswith("not_program"):
                if app == "ProgramLike" and src == "Present":
                    missed.append(u)
                try:
                    if int(r.get("applied_d1", 0)) or int(r.get("applied_d2", 0)):
                        ungated.append(u)
                except ValueError:
                    sys.exit(f"ERROR: unparseable applied_d at unit {u}")
            elif expect == "program":
                if app in MUTE_APPEARANCES or src in MUTE_SOURCES:
                    false_mute.append(u)
                # A false SNOW on programme is worse than a false mute: snow is a lock-like loss
                # under rule 5b, so it resets the geometry on real picture. Counted separately
                # because its cost is different, and it must be zero.
                if app == "SNOW_LIKE" or app == "SnowLike" or r.get("lock_like_loss") in ("1", "true", "True"):
                    false_loss.append(u)

    if absent:
        sys.exit(f"ERROR: {len(absent)} fixture units absent from the log "
                 f"(first {absent[:5]}) — the run did not cover the whole tape")

    if not_applicable:
        print(f"not applicable: {len(not_applicable)} fixture units are device-short or unframed "
              f"({sorted(not_applicable)[:6]}), so they carry no fixed raster to classify")
    print(f"MISSED     {len(missed):5d}   (baseline 17; must not rise)")
    print(f"FALSE_MUTE {len(false_mute):5d}   (baseline 108; must not rise)")
    print(f"UNGATED    {len(ungated):5d}   (must be 0 once rule 5 lands)")
    if loss_column_present:
        print(f"FALSE_LOSS {len(false_loss):5d}   (must be 0: a lock-like loss on programme resets real geometry)")
    else:
        print("FALSE_LOSS   n/a   the log has no lock_like_loss column, so this cannot be measured "
              "on it — that is unknown, not zero")
    for name, lst in (("missed", missed), ("false_mute", false_mute), ("ungated", ungated), ("false_loss", false_loss if loss_column_present else [])):
        if lst:
            print(f"  {name}: {lst[:12]}{' ...' if len(lst) > 12 else ''}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
