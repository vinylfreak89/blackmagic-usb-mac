# Registration v9: line 21 plus a geometry lock

`field_registration` corrects independent whole-line vertical displacement of
the two NTSC fields in one exact 756,048-byte Shuttle unit. It never
deinterlaces, allocates on the unit path, retains input, duplicates a line, or
manufactures pixels. Positive `d` selects a later whole UYVY source line.

The 720x480 clean-aperture output starts at unit rows 19/282 (NTSC lines
23/286). The engine scans the complete captured fields, unit rows 8..262 and
268..524 (NTSC lines 12..266 and 272..528), for CEA-608. A parity-valid line
away from the Shuttle's insert at rows 17/280 is the primary displacement
gauge and applies immediately, except for the line-22 ambiguity below.
Non-null data re-encoded on the insert is never a displacement gauge: the
sidecar retains its bytes and names whether live geometry corroborated or
contradicted it. Field 2 additionally uses the frozen smeared-XDS discriminator
documented in `CLAUDE.md` when parity cannot decode that field. Its invariant
is the measured pulse followed by its dark bin, at least two consecutive
bright bins in the four-bin bar corridor, and the following two-bin drop in
the left 40%, plus a row mean below 95. The right half is unconstrained because
picture can bleed into it.
A line with CEA-608 carrier energy is VBI but is never an XDS fallback
candidate; this keeps the adjacent run-in fragment out of the fallback set.

A parity-valid row exactly one line below an insert carrying non-null data and
agreeing aligned geometry is classified as station line-22/285 data. The sole
`GaugeConflict` is the corresponding ambiguity beneath a null insert when a
live lock reads zero. A parity displacement of two or more lines is never
treated as line-22 data and applies unconditionally. Every physical parity or
field-2 fallback reading re-anchors the lock top immediately; the old
content-acquired zero is not retained. The sidecar records the parity row and
bytes, `geometry_d`, and the resulting zero source. Precedence for other
one-line gauge conflicts remains pending owner ruling.
When a unique off-insert or field-2 fallback gauge exists, the picture-top
scan begins below that gauge. This excludes bright/leaking VBI bands above a
displaced line 21 from the geometry lock without trying to classify their
waveform as picture content.

When the insert contains null data and there is no primary gauge, v9 measures
the picture top and bottom by row-mean luma. A row is picture-like when its
active-area mean exceeds that field's measured blanking mean by 4 luma codes;
the top additionally requires three consecutive picture-like, non-VBI rows.
This relative threshold preserves dark program near Y=10 against a blanking
floor near Y=1.4 without mistaking mute/black for picture. A candidate that is
flat (luma variance at most 16) and less than half the mean of the three rows
below is the measured tape line-22 gap, not picture; all three rows in the
accepted top run must independently escape that classification.

Each field starts every segment locked to the standard picture origin (NTSC
lines 23/286). There is no content-acquired position and no acquisition dwell:
`geometry_d = measured_top - standard_or_gauge_anchored_top` applies on the
first measurable unit when the height/clip validity check permits it. A
parity/fallback gauge may re-anchor the source's zero immediately. `H` is a
content-validity quantity only; the first measurable envelope supplies it,
possibly as a censored lower bound. The first credible uncensored observation
fixes `H`; until then the sidecar reports `lock_height_known=0`.

```
uncensored_bottom = T + H - 1 + d
expected_bottom   = min(uncensored_bottom, C)  # when C is known
residual          = measured_bottom - expected_bottom
```

Residual zero directly permits an ungauged `GeometryLockDecides`. A bounded
one-unit body witness independently measures field motion: the engine compares
320 evenly spaced luma samples (half horizontal resolution) over NTSC lines
44..203 / 307..466 with the immediately previous unit at integer shifts
-3..+3. A minimum MAD at most 25 is measurable only when it beats both
adjacent shifts by at least 20%. The earlier row-mean profile and shallow 3%
minima were falsified by flat/tied witnesses on fixture A.

The witness is anchored to the previous unit's measured picture top, never to
`last_applied`. If current top and body motion agree, their current position is
used even after a hold. If a top moves while a reliable body stands still, the
top is a brightness/content flicker: `TopBodyDisagree` keeps the body-derived
position. If the body witness abstains on a changed geometry top, a measurable
comb check is the second witness: the matching move is
`TopCombCorroborated`, while a contradiction is `TopCombVetoed`. A flat or
unavailable comb has no testimony, so the measured top applies as `TopOnly`.
This check is allowed before the segment's field-2 zero has frozen, but cannot
by itself calibrate or drift that zero. With no top, a still body or motion differing between the two fields
can supply `BodyOnlyPlacement`; equal nonzero motion in both fields is an
undecidable pan/common-mode case and `CommonModeBodyHold` is named. A unit with
no accepted physical position invalidates the reference for the next unit, so
a remembered crop can never latch into motion evidence. Picture content never
redefines zero. A parity/envelope zero survives secondary content changes.
Dark/unmeasurable content holds without destroying a valid lock. A clip
ceiling is learned only when two parity/fallback-gauged observations at
different offsets saturate at the same bottom line; its candidate/count are separate
from the lock state, so fitting never makes a locked field appear unlocked.
The candidate is the greatest observed bottom and can be confirmed only at a
different gauged offset, preventing dark bottom flicker from fitting multiple
ceilings. While `C` is unknown, any bottom inside the measured clip band is
censored: top position decides, and bottom flicker within the band can neither
break the lock nor change the displacement.

`fieldreg_begin_segment()` restores both standard-origin locks and starts the
new segment at `d=0`. `fieldreg_discontinuity()` preserves installed zeros,
parity calibration, and each last applied offset; it invalidates only the
previous-unit luma/position witnesses and unfinished consecutive evidence.
Neither call buffers, backdates, drops, or repeats a unit.
The remaining per-segment ambiguity is field 2's zero: picture geometry cannot
distinguish a source whose second field begins one display line lower from an
actual one-line crossing. Static picture detail resolves that zero once. The
engine applies an 8-pixel horizontal low-pass, retains same-parity pixels whose
temporal delta is below six luma codes in both fields, and searches field-2
re-weaves -3..+3. Three consecutive measurements with at least 3% static
pixels, a unique minimum, and a 25% advantage over the second-best freeze the
field-2 top; `zero_source=Comb`. Calibration requires field 1 to be placed by
CEA-608 parity in that unit and field 2's measured picture position to be
applied against its current zero. The candidate zero is derived from the raw
field-2 picture top and the tested crop shift, never integrated from the old
zero. Field 2 then continues to track its own top and body motion against that
zero. Comb does not vote on a crop from one unit. When a decisive comb zero
contradicts an Envelope zero, picture comb wins once and that installation row
is `ZeroConflict`; subsequent Envelope observations cannot overwrite it.

Whenever a previous unit is available, the engine searches -3..+3 around the
ordinary per-unit crops. This correction path is independent of zero
calibration: the deciding minute-43 slice has no caption with which to
calibrate a cold replay. Three successive decisive readings of the same
nonzero shift install
that shift as one bounded, absolute relative correction; it is never added to
the preceding correction. Field 1 parity makes field 2 the moved field.
Otherwise the field whose current picture top points in the correction's
direction moves; when neither identifies it, field 2 is the deterministic
choice. This equivalent field assignment is made per unit, so a later
parity-placed field 1 is never displaced by an earlier field choice. The
correction survives flat/unmeasurable units, body-corroborated
motion, and byte discontinuities. Three decisive zero-shift readings clear it;
only `fieldreg_begin_segment()` clears it immediately. Its measurement always
uses the uncorrected crops, so later identical evidence corroborates rather
than accumulates it. `comb_safe` requires both field locks, calibrated parity,
and a correction that can be honored within the crop bounds.
One missing Shuttle insert is an `InsertAbsent` hold and does not itself erase
a lock; a real mute/unlock is already a signal-state segment boundary, while
subsequent measurable geometry can independently invalidate a stale lock.

Parity places its current unit immediately unless reliable picture testimony
contradicts it. A tied or absent body witness abstains and cannot veto parity.
If a unique decoded caption and the measurable top plus 2-D body witness report
different positions, the picture wins symmetrically: a still body is
`CaptionOnlyMotion`, and a differently moving body is
`CaptionBodyDisagree`. This applies whether the caption changed and picture
stood still or the caption stood still and picture moved. A censored or absent
bottom supplies no contrary evidence; when fully measurable it must conserve
the same body-consistent placement.
A parity or Envelope reading moves a segment zero only after three consecutive
gauge-placed units imply the identical base. Until then it still places each
unit as `ZeroCandidate`, leaving the zero and lock geometry intact. A candidate
more than three source lines from the standard origin is immediately refused
as `ZeroOutOfBounds`. This candidate memory never delays or smooths crop
placement.

## Sidecar schema 9

The frameserver retains its transport/signal columns and writes the following
v9 provenance for each field. Values named `*_line` are NTSC line numbers
(engine internals use unit row = line - 4).

- reason and gauge;
- insert presence and decoded bytes;
- parity/fallback candidate counts;
- selected gauge line, decoded bytes, correlation amplitude, and the live
  lock's independent `geometry_d` reading;
- blank-row mean; the 2-D body witness's validity, shift and MAD; its previous
  measured top, implied current top, top agreement, differential/common-mode
  classification; the resolved current picture top and whether it came from
  the body; plus raw picture top/bottom/height, measurability and censoring;
- lock state/id, `None`/`Standard`/`Parity`/`Envelope`/`Comb` zero source, frozen
  top/height, whether that height is uncensored,
  `ClipUnknown`/`ClipFitting`/`ClipFitted`, and the optional clip ceiling; and
- expected bottom, lost-line count, and invariant residual.

The row also records `parity_state` (Uncalibrated/Calibrated; `Drift` remains
an ABI name but is not produced by this policy),
`comb_check` (agree/disagree/flat/n.a.), the best re-weave shift, installed
field-2 parity bias, best/second energy and static fraction, the installed
`comb_correction` and its live installation ordinal, the applied pair,
whether both locks make the vertical-registration claim (`comb_safe`),
publication/drop accounting, and schema version. The offline renderer emits
the same per-field engine provenance.
`confidence` is binary: `1` means at least one field supplied an accepted
observation, `0` means neither did. `fieldreg_confirmation_units() == 1`
records that standard-origin geometry placement is immediate; it is not a
dwell or smoothing window.

The signal-state API currently accepts only a complete `(d1,d2)` observation.
Frameserver therefore marks `observation_known` only for support 2; support 1
still updates the full applied pair through `applied_known`, but never feeds an
unknown-field sentinel into signal-state's chatter counter.

## Deliberately absent

No one-unit comb authority, spatial bands, multi-candidate trajectory, dwell, chatter
suppression, common-mode arbitration, learned position mode, FIFO, or
backtracking remains in the live path. The bounded comb measurement above
calibrates/checks a segment constant, can corroborate or veto an independent
geometry-top reading, and can install a relative crop correction only after
three decisive matching readings. The
other temporal measurement is the
bounded previous-unit body profile above: it confirms a current top reading;
it cannot smooth, vote, or redefine a lock. The old tools
remain offline diagnostics only; `docs/registration_archaeology*.md` records
why those models were retired.

Build and run the deciding tests with:

```sh
make -C src/field_registration test
```

The synthetic v9 golden landed first and scored 8/29 on v7; later red-first
extensions exercise each measured defect. The current contract must score
186/186, the decoder unit test 3/3, and the fixture agreement harness must
match `experiments/cc608_decode.py` line verdicts and bytes exactly.

### Round-8 instrument correction (2026-09-05)

The d871f1f experiment proved that holding whenever the body witness abstained
was wrong: it created 2,621 parity-oracle disagreements and changed late,
correct repairs into misses. Round 8 restores parity authority and treats a
tied body as no testimony. Its whole-tape paced replay has 40,208 field-1 and
24 field-2 parity agreements, 30 named reliable-picture vetoes, and zero
unexplained disagreements. Across the six measured slices, absolute comb
misregistration falls from d871f1f's 33 units to 10. Unit-to-unit
`ENGINE-MOTION` remains diagnostic only: it calls a correct one-unit-late repair
motion even when the resulting crop is absolutely registered.

Field 2 remains bounded to the validated `+3` crop. A physically possible
`+4` registration requires an explicit padding-extension path; that is a named
follow-up, not an implicit relaxation of the crop limit.
