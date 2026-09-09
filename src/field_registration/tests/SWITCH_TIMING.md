# Commercial switch replacement: counter 6687 fixed, capture gate NOT passed

This replaces the rejected 35-code MAD / independent-aperture-lag predicate.
It is an engine measurement under review, not a new reference and not an
acceptance claim. Work stayed on the commercial capture. The owner's accepted
one-unit miss at 43678 was not pursued; signal_state was not changed.

## Measurement and premise

Rule 3 names the picture bottom as the row above the first measurable switch
discontinuity, including the partial row. A change in picture brightness is
not such a discontinuity. The replacement reads positive relocation of
blanking against locally observed timing, not a band size or a luma step.

`blanking_profile` scans every sample position. The 858-sample NTSC line,
720-sample delivery window, and nominal 147-sample blanking interval give
nine delivered blanking samples in total. Nine-sample windows wrap across
the two delivered ends so a split overlap is not mistaken for its absence.
A separate scan records whether a complete 147-sample interval is exposed.
Window means are compared with this unit's measured maximum regenerated
blanking sample, not a typed luma code. A blank-equivalent whole row supplies
no phase. These are nominal-standard apertures, not proof that every noisy
analog blanking interval will pass them.

The local reference stores sixteen preceding row profiles (memory capacity),
excluding the immediately preceding row while testing S because it may be
partial. Its union of blanking-window positions admits observed local timing
variation. Its intersection of individual blank samples identifies remnants
of normal timing. Columns blank throughout the field are nondiscriminating
and excluded from that remnant test: on counter 6687 field 1, sample 719
remains blank even in the other-head rows. That position is discovered,
never hardcoded. This is not a claim that every such column is device-written.

A full-row candidate requires a relocated complete blanking interval, no
overlap with the local normal phase, and no retained discriminating normal
blank samples. The row above is called partial only when it positively
retains normal blanking as well as exposing relocated blanking. A partial
row may itself contain a complete interval; that alone never makes it S.
A previous row already carrying the same displaced phase cannot silently be
skipped merely because the next row is easier to measure. An ambiguous first
row leaves the measurement Unknown. A subsequent return to the prior normal
phase cancels a terminal-band candidate.

References are local variables rebuilt from the current unit, not stored
across resets or gated input. Unreadable rows age out the local reference;
an early excursion cannot be carried across a long unmeasurable region and
attached to a much later full interval. No expected switch-line count,
bottom corridor, unconditional left/right-end label, or RF-peak detector was
introduced. The existing lock-count lifecycle was not changed.

This method remains incomplete: normal-looking black content and blanking
can coincide; noise can hide an interval or leave ambiguous remnants. It
abstains rather than substitutes a count. The census below quantifies how
far that remains from capture acceptance.

## Deciding tests

The initial failing-first golden is commit `99d1b06`. The expanded
`switch_timing_test` now checks three constructed partial/full transitions
at different vertical positions and blanking levels, including a partial
row containing a complete interval; content steps and black rectangles;
an interior departure and return; absent timing; aged-out references;
blank-equivalent picture; and a noisy first interval that must not move S
to its easier successor. No capture samples are committed.

The optional counter-6687 input is the exact 756,048-byte UYVY transport
unit exported by `switch_probe`. The first golden version accepted a luma
PGM and discarded chroma; that could not reproduce the measured clip. It
was corrected to consume the exact unit. Running the expanded test against
the pre-change implementation produces **1/30 passed**, exit 1; the final
implementation gives **30/30**, including ASan/UBSan. The synthetic-only
test on `make test` is **24/24**.

The rule-3/4 fixture formerly repeated arbitrary texture over all 720
samples without any horizontal blanking. It now constructs an 858-sample
line with its 147 blank samples and shifts that line. All existing vertical
geometry and lock-count assertions are unchanged. This corrects the input
model rather than retaining a content matcher just to satisfy its fixture.

Other tests: field-registration unit 18/18; CEA-608 3/3; rules 1/3/4
5/5, 2/2, 5/5. Live gate tests `non_program_never_measured` (9 gated units)
and `signal_gate_preserves_published_crop` pass. Merged scorer tests pass.

## Counter 6687, NTSC lines

| Reading | Field 1 | Field 2 |
|---|---:|---:|
| Picture top | 23 | 286 |
| Picture bottom | 259 | 521 |
| Partial switch T | 260 | 522 |
| First full other-head S | 261 | 523 |
| Measured clip | 262 | 525 |

The actual production record carries `BlankingPartial` in both fields.
The old false hits at 236/498 are gone. Counts derived from these rows are
observations of this unit, not expectations for this source or another one.

## Entire commercial capture: diagnostic and live path are distinct

The native CAP1/parser probe sees 919 eligible exact units. It measures every
exact raster in a separate scalar diagnostic, including gated rasters; that
diagnostic never places a crop or trains a lock. The live-equivalent path
invokes registration 452 times, 440 in the 582-unit interval counter >=6593.
Against the prior build's same-capture probe, eligibility changes are zero
and measured-top changes are zero. Other captures were not run.

Diagnostic T histograms in the 582-unit interval:

| NTSC T | Field 1 count | NTSC T | Field 2 count |
|---|---:|---|---:|
| Unknown | 401 | Unknown | 463 |
| 259 | 1 | 522 | 15 |
| 260 | 69 | 523 | 98 |
| 261 | 111 | 524 | 6 |

Compared by counter/field with the saved harness `ref_capture1_ends.csv`:

| Engine minus reference | F1 T | F2 T | F1 S | F2 S |
|---|---:|---:|---:|---:|
| -1 | 3 | 1 | 0 | 0 |
| 0 | 77 | 42 | 123 | 86 |
| +1 | 101 | 75 | 57 | 32 |
| +2 | 0 | 0 | 1 | 0 |
| Engine Unknown | 401 | 463 | 401 | 463 |
| Reference Unknown, engine known | 0 | 1 | 0 | 1 |

The previous long false bands are absent in this diagnostic, but this is
**not a pass**: abstentions and the partial/full disagreements remain.
Even where T is within the one-row fallback ambiguity, S is not universally
adjudicated. The retained-sample distinction is deliberately conservative;
it is not demonstrated to recover every readable timing departure.

For example, the raw panel at 6593 has blank-equivalent picture down through
259/523, then flat pedestal rows: field-1 lines 261/262 have mean 9.33/9.63,
sigma .78/.88, with no readable blanking interval. Calling those observations
Unknown is different from proving that the whole region has no measurable
geometry by any other method. This detector supplies no flat-band fallback.

There is also no acquired geometry lock in the commercial stable interval:
the existing engine only has caption confirmation implemented at acquisition,
not the pending comb confirmation path. Count constancy is therefore **not
validated by this capture**, rather than vacuously reported as a pass. The
rule-4 synthetic lock/freeze/conflict/reset checks do pass. Existing field-2
top errors also remain unchanged; this is strictly a switch-detector change.

Native probe timings, 452 actual engine calls, O3: engine median **2.018 ms**,
p95 **3.235 ms**; classifier plus engine **2.363 / 3.584 ms**. Neither is
the complete publishing worker. The old incorrect detector measured .434 /
.486 ms on this capture; correctness, not that speed, motivated replacement.

The final production replay at 8,000-us pacing processed and published all
919 eligible units with zero pool/ring/surface drops, zero counter holes,
and 930 observation-log rows. Registration ran 452 times; all other
observations were unmeasured. The final sidecar confirms the 6687 table.

## Reproduction and artifacts

`make -C src/field_registration test` runs the synthetic goldens. Compile
`tests/switch_probe.c` with `cea608.c`, `signal_state.c`, and `unit_parser.c`
at O3. Its arguments are capture path, first selected counter, last selected
counter, and an existing scratch directory. It exports selected exact units
and raw PGM panels, per-row profiles, and `geometry.csv`; stdout is the
gated-path timing table. Select 6687 and pass its `.raw` to
`tests/switch_timing_test` for the six raw-unit assertions.

Artifacts are under `/private/tmp/v10-switch-relocation/`: `geometry.csv`,
`rows.csv`, `units.csv`, and the final paced `registration_final.csv`.
The production replay takes the decision CSV as its **positional second
argument**, with `--pace-us 8000 --ring-mb 512 --pool 32`. `--dump-log` is
instead an A/V-publication log. An initial analysis used that wrong log and
failed with `KeyError: 'registration_measured'`; it was rerun correctly.
Two later attempts to reuse the positional CSV failed with `open failed`:
`fs_open` uses `fopen(..., "wx")` and refuses to overwrite evidence. The
final replay uses a fresh filename; the earlier file remains intact.

Saved harness reference SHA-256:
`f3c59cfb4b6f5b4cf7660caf386b5aac33b7b10a8a85c880842315578296e67c`.
Exact counter-6687 unit SHA-256:
`cff83b14d1076ab8609adba2512add98c14743742f4910bfceae122ba9d344d0`.
Final production sidecar SHA-256:
`d6af1222fbf02370b04efa3262a3361f8b1091c007d64833b19799da30564ac9`.
Diagnostic geometry table SHA-256:
`f7de3b911680057e8e19110233573b2a320daf7ef560f306cc8f845f3cfd75f7`.
