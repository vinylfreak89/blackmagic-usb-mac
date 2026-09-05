# Registration v9 — clean-sheet plan (agreed 2026-09-04, no code written yet)

Agreed between the owner, Codex and Claude after the v8 review. This replaces the live path of
`field_registration` entirely; nothing of v6/v7/v8's evidence graph survives in the live engine.
Measured facts behind every rule are in CLAUDE.md §6/§7 and `docs/registration_vsync_research.md`.

## The problem (measured)

The Shuttle delivers a rigid 525-line raster: the padding ruler, the deck's fixed timing line
(unit row 16) and the deck's regenerated line 21 (row 17; row 280 for field 2) never move. Inside
it the deck places each field's picture, and field 1's picture moves vertically by whole field
lines — unit to unit and in plateaus — while field 2 almost never does. A displaced field carries
the tape's own line-21 waveform with it (two rows above the picture top), so a displaced field
shows TWO line-21-like rows (the insert at 17 and the tape's at 17+d) while an aligned field
shows one. Per-field, whole-line displacement inside a stable regenerated raster is a documented
VHS capture problem; the correction is a per-field whole-window shift.

## Coordinates

- Crop origin, 720×480 (clean aperture, SMPTE RP-202): rows 19/282 = lines 23/286. Captions are
  not in the 480 render.
- 720×486 (alternate output mode, to be added): rows 17/280, lines 21–263 / 283–525, captions kept.
- Picture origin in both modes: rows 19/282. `d = 0` means the picture starts there and the tape's
  line 21 rides on the deck's line 21, invisible — that is correct alignment and a picture lock.

## The golden rule

Assume the picture is locked in the right place (reference = the deck's line 21, rows 17/280)
unless the tape's line 21 is found anywhere else in the field — search the whole field, top first,
including the bottom. Only that can change the lock, which may produce one or two line jumps near
the beginning of a recording; each is recorded. Everything derives from the lock: field parity
keeps both fields aligned at the correct picture start (field 2 one display line below field 1).

## Measurement, per field, per unit

- **Line 21 (primary gauge).** The BLANK CEA-608 waveform: seven-cycle 503.5 kHz run-in, start
  bits, two null bytes with parity. No caption data needed. A tolerant template/period match with
  tolerance to level, horizontal displacement and moderate skew; uniqueness across the field.
  Classes: none / unique / duplicate / split / skewed / leaking-VBI-band. Only `unique` carries a
  displacement: `d = row − 17` (field 1), `row − 280` (field 2).
- **Picture envelope (secondary gauge).** Black is relative to the field's own blanking rows
  above the VBI band (field 1 rows 7–16, field 2 rows 270–279); a line is mostly black when
  ≥ 60 % of its luma samples over x = 40..679 lie at or below blank + max(6, 4×MAD). Top = first
  non-black picture row scanning down from 17/280 with line-21-like and timing lines excluded by
  signature (never by row number); bottom = last non-black row followed by ≥ 2 mostly-black
  rows before the ADC boundary; height = bottom − top + 1. Top at the first scanned row or a
  bottom that reaches the ADC boundary is censored. Valid only with both edges credible and the
  height equal to the height frozen for this lock (the only learned quantity, per field).
- **Secondary confirmations, never gauges:** the black line 22 at 18+d; the NEXT field's
  line-21-like waveform in the head-switch band at the bottom (row 256 when aligned); picture
  content above the deck's insert (rows 7–16 must never carry video); leaking-VBI bands (broad
  bright rows without the null-line-21 structure) are excluded from everything.

## Decision table

| Condition | Applied | Reason |
|---|---|---|
| Open / segment begin / transport discontinuity | Hold last applied (0 at open); reacquire only the envelope HEIGHT from consistent measurable units; the reference is never learned | `AcquiringEnvelopeHeight` |
| Only one line-21-like row, at the insert | No caption-derived move (aligned, or no caption service) | `Line21CoincidentOrAbsent` (confirmation when the tape's waveform is visibly on the insert) |
| Unique second line-21 row at 17+d, valid envelope shows the same d | Apply d now | `Line21Placement`, `EnvelopeConfirmed` |
| Unique second line-21 row, envelope unmeasurable (dark, flat, fade) | Apply d from line 21 alone | `Line21OnlyPlacement` |
| Unique second line-21 row, valid envelope disagrees | Hold previous | `Line21EnvelopeConflict` |
| Unique line-21 row off the insert while the envelope sits at the origin, consistently over the confirmation span | This recording's line 21 lives at a nonstandard row: re-lock the caption reference once, picture untouched | `CaptionRelock` (sidecar event) |
| Line-21 candidates duplicate / split / skewed / band | Discard them; envelope-only if valid, else hold | the ambiguity class |
| No second line-21 row, valid rigid envelope | Apply top − 19/282 now, every unit, jitter and plateaus included; no dwell, no magnitude cutoff | `EnvelopeOnlyPlacement` (`Oscillation` / `Return` noted from one unit of memory) |
| Envelope height ≠ frozen height, or dark / fade / snow / mute / censored | Hold previous | named hold |
| Content changes inside an unchanged envelope | Keep placement, preserve content | `ContentChangeWithinRaster` |
| Proposed (d1,d2) would put field 2 above field 1 | Reject atomically, keep last valid pair | `ParityInvariantHold` |
| Requested crop not representable from the captured unit | Hold, flag | `OutOfRangeHold` |

Hysteresis: exactly one unit of memory per field (last envelope, last applied). It names
oscillation and returns; it never delays a correction. No lookahead, FIFO or backtracking (those
belong to the offline archival pass only). Every accepted placement shifts the whole UYVY crop
window (chroma with luma); no line is ever duplicated, dropped or synthesized. Every hold is a
recorded absence of placement, never a pinned crop presented as registration.

## Sidecar (schema 5)

Per unit: segment/lock ids; transport and signal-state; per field: blank level, MAD, black
threshold, line-21 candidates and class, selected line-21 row, raw top/bottom/height, censor and
credibility flags, frozen height, gauge used, measured and applied offsets, hold reason,
`CaptionRelock` events, secondary-confirmation flags; output geometry mode; publish/drop accounting.
The v7/v8 columns disappear.

## Goldens (synthetic, first) and acceptance (fixture A)

Synthetic: rigid ±1/±2 jitter per field; plateaus and returns; a large credible excursion; dark
frames and fades; grey mute → program; letterbox / height change (hold); top censored by VBI;
bottom into padding; snow → relock → height reacquired; transport discontinuity; unchanged raster
(zero crop changes); null and data line 21 at 17, at 17+d, duplicated, split across rows/fields,
skewed, and leaking bright bands; parity-violating pairs rejected.

Tape: every unit with a unique second line-21 row ends with `row − 17 == applied_d1` and the
picture top at row 19; `picture_envelope_census.py` shows every rigid move followed, zero crop
changes on a still raster, registered top/bottom constant per lock; split/skewed EP captions and
leaking-band units counted and never used (EP at 1,300 s: 458 units with ≥ 2 band rows, 138 with
one); the 720×480 render caption-free, a 720×486 diagnostic render caption-visible with identical
decisions; static-comb no worse than 5/2,011 (SP) and 138/2,865 (credits); cost well under
1 ms/unit; state under 1 KiB; no allocation per unit.

## Deleted from the live engine

Band hierarchy, spatial phase voting, relative comb authority, temporal searches and vetoes,
multi-candidate selection, support dwell, chatter suppression, common-mode arbitration,
provisional trajectories, FIFO, backdating, learned position references. `static_comb_metric.py`,
`picture_envelope_census.py` and the overlay remain offline diagnostics and acceptance tests.

## Amendments from the whole-tape envelope census (2026-09-04 evening, measured, not yet ruled on)

1. **The bottom is censored under downward displacement.** In the 395 first-recording units with
   the caption at row 19 (d = +2) the bottom sits at 257, not 258: the deck clips field 1 one line
   above where the picture would end. So "rigid shift with unchanged height" fails on exactly the
   displaced units. Rule to adopt: when the bottom sits at or beyond the clip row (256–258 for
   field 1, 518 for field 2) it is censored; validity then comes from line 21 plus the top, and
   the learned height is an upper bound, not an equality.
2. **Top-only changes with a fixed bottom are content.** The SP intro's top-20/bottom-256
   majority carries no line-21 waveform at row 18: locked, line 23 blank. The second recording's
   field 2 sits at 284/518 for 25 minutes with its bottom fixed. Neither is a displacement. The
   envelope may only report a displacement when top and bottom move together (or the bottom is
   censored per item 1 and line 21 agrees).
3. **The second recording (1,461 s–end) — RULED by the owner (2026-09-04 evening).** Its
   captions are never on the insert; they sit at rows 19/20 with the picture right underneath
   (gap 1 in ~3,500 units, gap 2 in ~1,300, caption below the detected top in 682), and the
   line-21 waveform often spans two rows (run-in on both, start/data on one). Ruling: **if a unit
   shows line-21-like waveforms on more than one row, or a partial waveform, give up on line 21
   for that unit** — a timing signal that unstable cannot be a reference. The fallback fix
   points are then promoted from "secondary checks" to a real gauge: the leaked VBI framing
   pulses of the next field in the head-switch band at the bottom of the field, and picture
   content appearing above the deck's line-21 band (video must never be there). Only after those
   does the envelope apply, then hold-last. Open measurement before the goldens: the owner's
   observation of the EP render differs from Claude's 600-unit window at 2,400 s — he sees the
   waveform extend across both rows sometimes (usually when it carries real caption data, which
   in a bob render appears every other field: CC1 data is on field 1, field 2's line 284 is
   usually null) and not in the stable state, with an occasional unsplit line 21. Classify per
   unit and per field across the whole second recording (rows found; run-in-only / null /
   data-bearing; single or multi-row) before writing the ambiguity detector.
4. **Field 2 is rigid on the whole tape:** 224 rigid moves in 86,293 units; the plan's "field 2
   from the same lock and its own envelope" stands, and its 282↔283 top flicker must be treated
   as content.

## Rulings of 2026-09-04 night (owner, after Codex's independent weigh-in)

1. **Output geometry stays standard.** 720×480 = SMPTE RP-202 lines 23–262 / 286–525 (main
   today). 720×486 = the SMPTE 125M/259M active area, lines 21–263 / 283–525, is the
   preservation mode for anyone who wants lines 21–22 / 284–285 (captions, station data, a
   station's picture on line 22) kept. The owner's 22/285-first idea was withdrawn in favour of
   following the standard; Codex independently recommended the same. Commercial-tape check
   (composite capture, 800 units): first line with content is 23/286 in 632 units and 23/287
   (dark first field-2 line) in 156; lines 22 and 285 are blanking-level in every unit.
2. **The engine is the simplest one.** Per field per unit: candidates = lines carrying a
   COMPLETE 608-format waveform (run-in energy AND start-bit energy) off the regenerated line
   21/284; a partial waveform (run-in only) is never a candidate. Exactly one candidate ⇒
   `d = line − 21` (field 2: `− 284`), applied now, `Line21Placement`. None, with the insert
   present ⇒ `AssumedAligned` (d = 0; a positive-looking label is forbidden — it is a default,
   not a measurement). More than one ⇒ hold last applied, `Line21Ambiguous`. Insert absent ⇒
   hold, `NoSyncReference` (mute / no input; the classifier's state). No bottom edge, no
   envelope, no height, no comb, no learned position. Whole UYVY lines; parity kept.
   Measured on the second recording with exactly that rule: field 2 unique +2 in 120/200
   (30:38), 431/600 (35:00), 319/600 (45:00), the rest `multi` (286 with 287/288/289) ⇒ hold
   at +2; field 1 unique +2/+3 in 182/200, 451/600, 271/600, the rest `multi` (23,24 in the
   jitter units) ⇒ hold. The first recording (21:40): no off-insert candidate in 300/300 ⇒
   `AssumedAligned`, correct.
3. **Open, needs the owner's word before code:** the no-caption-service secondary. The owner
   wants the first picture line usable as a lock when no 608 waveform exists anywhere; Codex
   objects that an absolute 23/286 reference is wrong on a source with picture on line 22 (the
   second recording) and on dark or letterboxed first lines, and proposes a segment-local modal
   picture-start used only for relative motion — which is a learned position reference, a
   class the plan deleted. Choices: (a) no secondary at all (caption-less tapes get
   `AssumedAligned` and no jitter correction); (b) Codex's relative-only modal reference,
   named `PictureStartRelative`; (c) absolute 23/286, knowing it mis-places line-22 sources by
   one line. Claude recommends (a) for the first build and (b) as a measured follow-up.

## Amendment: the candidate test is a CEA-608 decode with parity (measured 2026-09-04 night)

The "complete waveform" candidate test in ruling 2 is replaced by an actual decode: a line is
the tape's line 21 if and only if it decodes as CEA-608 with valid odd parity on both bytes
(`experiments/cc608_decode.py`). On fixture A this leaves no ambiguity in field 1 at all:
exactly one parity-valid line per unit in every window measured (first recording: line 21
itself, d = 0; second recording: 23 or 24, d = +2 / +3, per unit), the vertical duplicates
never pass, and `Line21Ambiguous` never fires there. Field 2's tape line does not decode on this
tape (smeared XDS), so field 2 keeps the unique-608-like-candidate envelope rule with parity
decode attempted first. Cost: one correlation and 19 samples per candidate line, negligible.

## The lock model, confirmed by Codex (2026-09-04 night) — supersedes ruling 2's fallback text

Owner's model: the picture's start line and the deck's clip are constants per source (letterbox
included); a lock is the golden master until its own invariant fails, tested every unit; line 21
is gold, picture geometry is the secondary; no real-time claim until a lock settles. Codex's
verdict: **model holds, with four changes**, all accepted:

1. **Censored-height arithmetic.** With locked top `T`, uncensored height `H`, displacement `d`
   and the last deck-passable line `C`: expected bottom = `min(T + H − 1 + d, C)`, lines lost
   below = `max(0, T + H − 1 + d − C)`. `C` is fitted per source and field as the one saturation
   line across repeated parity-gauged offsets, never from a single dark bottom; if no gauged
   displacement ever reaches the clip, `C` stays unknown and censored height cannot invalidate
   a lock. Only three geometry values are learned per field: source top, uncensored height,
   optional clip ceiling.
2. **Parity authority is immediate.** A parity-valid field-1 decode applies on that unit with
   no settling delay: line 21 = 0, another line = its offset. Field 2, which has no parity
   decode on fixture A, settles its unique-608-like-candidate reference (line 286 ⇒ +2) before
   its registration is known; the units before it settles are named, not claimed.
3. **"Neither" is subdivided and named** (owner correction: the Shuttle's re-encoded bytes at
   21 are the device's own slicing decision, corroboration only — the raw whole-field parity
   search is the authority; the slicer's window is measured not to reach ±2 and is unmeasured
   at ±1): non-null bytes at 21 with no parity-valid line elsewhere = `AlignedCorroborated`;
   parity-valid line elsewhere = `MeasuredDisplaced(d)`; null at 21 and nothing elsewhere =
   the geometry lock decides, never evidence of alignment; orphan run-ins and leaking bands are
   rejected by parity; insert absent = `InsertAbsent` hold, never geometry; dark / fade / snow
   or a broken conservation equation = `GeometryUnmeasurable` / `LockBroken`; device-short
   units are excluded before registration.
4. **Comb-safe interlaced output is claimed only after both field locks are valid.** Until
   then the sidecar says so and a presentation that needs the guarantee bobs field-isolated or
   delays; the no-comb guarantee begins when both locks exist. Horizontal flagging and
   chroma/line-phase damage stay outside this vertical model.

With these, the engine is: per field per unit, decode candidates with parity; apply the reading
immediately; maintain one lock (top, height, clip) per field and test the conservation
equation every unit; re-lock when a gauged offset and the picture agree; name every state.
No comb, no bands, no temporal search, no trajectories.

## Acceptance test for the geometry lock (owner, 2026-09-04 night)

The parity readings are sparse on the first recording (first 1,800 units: 64 units with data
bytes at 21, 202 with a raw parity-valid caption at 23, the other 1,514 nulls-only or none), so
the geometry lock carries most units there. That makes the first recording the test: run the
engine with the geometry lock deciding, and at every unit where a parity reading exists compare
the lock's answer with it — raw caption at 23 ⇒ the lock must say +2 for that unit; data bytes
at 21 with nothing elsewhere ⇒ the lock must say 0. Agreements and disagreements are counted
over the whole tape (the parity search is the truth set, thousands of units); a disagreement
is a defect in the lock or its invariant, never in the reading. If the lock agrees with the
readings wherever they exist, the secondary gauge is validated by the primary one on real tape.

## Round 3 (2026-09-05, after the owner's review of the first v9 render): the never-bounce invariant and the parity calibration

**Invariant (owner).** The regenerated raster is identical in every unit; the tape's field position is
directly readable every unit (the TAPE's line 21 when visible, else the picture's first line); the
crop is set to the reading; so the output picture position is `measured − crop = 0` by construction
and can never bounce except during the initial lock of a program segment. A bounce is always a
wrong reading or a remembered value substituted for a reading. Holds are legitimate only where
nothing is measurable: true signal loss, or the first units of a segment. Design test for every
engine state: *if the tape moves while I am in this state, does my output move?* If yes, the state
is allowed only where nothing is measurable.

**Parity calibration (owner).** Which display row the source's picture begins on is a per-segment
constant; picture geometry cannot distinguish "the source starts one display row lower" from
"field 1 displaced +1", and that ambiguity is exactly a crossing (a relative offset of one line
between the fields inverts the weave's parity; 42% of fixture A is crossed in the raw). Static-
region comb measures the content's own interleave and resolves it. So: once per segment lock,
measure the relative offset `r = d1 − d2` by static comb over the first units with static detail
and freeze it. Field 1's absolute position comes from its caption (or its picture top against the
standard origin); field 2's is field 1's minus `r`, cross-checked against field 2's own gauge when
one exists; the common mode is the standard origin by the golden rule until a caption re-anchors
it. From that point the picture geometry is known and where the first line of picture must sit is
known; every later unit is an exact equality to track, and `r` is re-checked cheaply on static
content, a persistent disagreement being a named fault that ends the segment, never a vote. This
is not v7: comb is a one-time calibration and a consistency check, never a per-unit authority.

**Root causes found in the first v9 render, all with failing goldens owed:** (A) VBI-type lines
that fail parity or the amplitude gate counted as the picture top (damaged captions, the smeared
XDS bar) — exclude by signature; (B) bottom flicker inside the deck's near-blank band (lines
260–264 / 522–526) breaking locks — the band is censored; (C) the lock zero acquired from content
instead of the standard origin — the golden rule; (D) an absolute luma threshold that reads a dark
picture as blank — relative to the field's own blanking.

**Review copies** come from the live frameserver's own output with its own sidecar burned in over
the entire tape, never from `capture_render.py`, never an excerpt; every non-locked state outside
true signal loss or a cut is audited against the raw 525-line raster before hand-over.

## Round 3 measurements on `render-live` (2026-09-05, 03:00–05:00)

- A/B/C/D landed (see CLAUDE.md §11). Whole-tape replay of the C/D build: parity 40,237/40,237,
  field-1 `LockBroken` 2,657 → 19, field-2 1,713 → 11, `OutOfRangeHold` 59 → 35; transitions
  7,032 → 10,510 and one-unit flips 2,797 → 4,068 (geometry now decides every unit — judged by the
  raw follow audit, not by the count).
- 45:00 field-2 regression closed: the XDS bar's signature is its LEFT half only (picture bleeds
  into the right half); run-in fragments excluded by 503.5 kHz energy regardless of variance
  (`09d59ee`, `945c6a3`, `a64003a`, `7de0b14`); field 2 +2 ×620, unique candidate 620/620.
- The tape's grey line 22 (luma ≈ 7 above a picture at ≈ 90) is VBI type 'gap', never a top
  (`30e1fa5`).
- 37:01 field 2: Claude's dark-scene guess was FALSE (Codex measured lines 288–290 as picture at
  33–65 against blanking 3.4); the OLD broad bar exclusion classified picture lines through 293
  as VBI and pushed the top to 294 (+8, `OutOfRangeHold` 52/329). Fix in progress: the narrow
  left-half signature for the exclusion too; no picture line may ever be excluded by a bar test.
- **Caption vs picture, measured (Codex, low-MAD transitions only):** 35:00 — caption and body
  moved together 180, body still 5, different 15, excluded 24; 45:00 — 9 / 0 / 0. So the tape's
  caption line moves without the picture in roughly 2.5% of caption transitions on this tape.
  **Owner ruling (2026-09-05, ~03:00 JST): the PICTURE wins the crop and the lock is kept.** A caption
  reading that disagrees with the settled lock while the picture's own edges agree with the lock
  is invalid geometry for that unit: it loses its vote (treated as non-picture VBI data), the crop
  follows the picture, the lock is unchanged, and the sidecar logs `CaptionOnlyMotion` with the
  edges as evidence. After the lock, parity is no longer unconditional: the lock plus the
  picture's edges outrank a single contradicting caption reading. A caption that agrees with the
  picture's edges still places the unit directly (the 180/200 case). To be implemented on
  `render-live` after Codex's current unit reports, with a golden from the 35:00 units.

## Round 3, state at 03:50 JST on 2026-09-05 (`render-live` at `be7691a`, not merged)

Landed with goldens (105/105): A (VBI-type lines excluded by signature, weak captions separated
from picture rows at run-in variance 20), B (near-blank band censored), C (standard origin, gauges
re-anchor, content never), D (threshold relative to blanking), the gap line, the XDS bar's
left-half signature with fragments excluded, the caption-only veto by conserved edges, and
`AnchorUncorroborated` (a single parity hit places its unit but does not move the zero). Codex
confirmed the invariant in writing. Slices: 37:01 field 2 100% at +2, 45:00 and 35:00 exact,
disaster region 3 engine-motion units in 79, 1:26 one.

Open, in the order they go to Codex: (1) the veto never fires at 35:00 because the bottom is
censored there and Claude's rule demanded both edges — a censored bottom is absence of evidence;
the picture's testimony becomes the top edge plus a body-shift witness (the follow audit's
measurement, in the engine); (2) every hold state that can occur with usable geometry
(Line21Ambiguous, GaugeConflict, LockBroken, OutOfRangeHold) is placed by geometry with the
state as provenance; InsertAbsent, GeometryUnmeasurable and discontinuity stay legitimate holds;
ClipUnknownHold is dead and deleted; (3) the per-segment parity calibration by static comb;
(4) the raster-damage state.

## Whole-tape follow audit of the round-2 engine (baseline; raw raster; 2026-09-05 04:00 JST)

`experiments/follow_audit.py` over all 86,293 units of the published v9 sidecar (content motion =
both fields' bodies moving together with no applied change): field 1 — engine-motion **954**
(Line21Placement 738, GeometryLockDecides 212), missed moves **2,259** (GeometryLockDecides 843,
Line21Placement 768, LockBroken 482, Acquiring 145), correct follows 5,822, content motion 7,174;
field 2 — engine-motion 95, missed moves 3,056, follows 21. Engine-motion concentrates in the
second recording (30–50 min: 748 of 954). The ~1,500 Line21Placement rows where the caption and
the picture body disagree in either direction (caption moved / picture still, and picture moved /
caption still) are the VBI-versus-picture class the owner ruled on: **the picture wins the crop
in both directions** — after the lock, the picture's own testimony (top edge + body witness)
decides the crop whenever it is measurable; the caption places a unit only when the picture is
not measurable, corroborates otherwise, and anchors the segment zero. That is the general form
of the ruling and the next brief to Codex. The same audit is running on the C/D build for the
before/after.

## Round 4: the C/D build and the body witness `dc8a459`, measured (2026-09-05, 04:40–05:30 JST)

**C/D build (`021eb0d`) on the whole tape** (same audit, same script with the content-motion
class): field 1 engine-motion **2,971** (baseline 954), missed moves 2,631 (baseline 2,259),
follows 5,729; field 2 engine-motion 1,723, missed 2,916. The engine-motion rose in minutes 2–12
of the SP recording (1,623 events: GeometryLockDecides 1,542, applied change ±1 alternating, body
MAD below 4 in 924 of them): the no-caption path chases the picture's first visible line as it
flickers between lines 23 and 24 while the body stands still. It fell in the second recording.

**Body witness `dc8a459`** (verified in a detached checkout: goldens 122/122, whole tape
86,293/86,293 exact, zero drops) trades engine motion for missed moves and the net wrongness at
the owner's sites went up — 35:00 wrong 40→46 (engine-motion 33→11, missed 7→35), 37:01 wrong
7→30 (3→5, 4→25); every missed move is differential (field 2 still). On the raw raster at 37:01
(ordinals 30–47 of the slice sidecar) the tape's line 21, the black line 22 and the picture move
together by one line unit to unit — a rigid whole-field jitter that the engine's caption reading,
its own top edge and its geometry candidate all see. Four defects, sent to Codex as one brief
(`/private/tmp/hw-session/briefs/r4_body_witness.md`):

1. The witness is a 1-D row-mean profile with MAD 0.5–2.0 and a flat minimum; it reads 0 on
   units that moved by one line and disagrees with the 2-D body shift on 12–55% of the moving
   units (37:01 field 1 19 of 88; 35:00 field 2 17 of 31). It must be a 2-D block MAD.
2. It is anchored on the last APPLIED offset, so one wrong hold is inherited by every following
   unit until a caption reading rescues it (37:01 ordinals 34, 42, 43, 46). Anchor on the previous
   unit's measured position; a top edge that moved with the body is physical and places the crop
   regardless of what was applied last unit.
3. The picture-wins ruling is implemented in one direction only: a caption reading that did NOT
   change while the picture moved is still applied unchanged (Line21Placement missed moves, 19
   at 35:00, 7 at 37:01). Differential body motion with an unmeasurable top follows the body;
   common-mode motion with no measurable top is the one undecidable case and stays a named hold.
4. With no caption, a top edge that moves against a reliable still body still moves the crop
   (05:00 slice: 33 engine-motions, all GeometryLockDecides, body 0 by both witnesses).

Tools added: `experiments/raw_panel.py` (four strips per unit, both fields' top and bottom, crop
drawn in, NTSC line labels) and `experiments/held_vs_top_runs.py` (runs where the applied offset
contradicts the engine's own top candidate). The whole-tape follow audit of `dc8a459` is running.

**Second instrument, same verdict.** `experiments/relative_comb_audit.py` weaves the two
published crops and measures comb energy on static pixels at field-2 re-weave shifts −3..+3; a
registered pair has its minimum at 0. On `dc8a459`: 05:00 slice 549 registered / 23 flat /
**35 misregistered**, 37:01 298 / 15 / 15, 35:00 536 / 77 / 7, 01:26 70 / 6 / 2. The
misregistered units are exactly the follow audit's engine-motion units plus the held runs the
follow audit cannot see: at 05:00 ordinals 475–488 (14 units) the tape's caption sits on line
23, the engine's own top edge and geometry candidate say +2, and the crop is held at 0 by
`CaptionBodyDisagree` because the 1-D witness read +3 on the first unit and the hold was then
inherited (defects 1 and 2 above); at 37:01 the latched units 34, 43, 46. The comb audit is the
acceptance instrument for "no combing under yadif": it sees persistent wrong holds, which a
unit-to-unit follow audit scores as still.

## Round 4 result: `2efc416` (2-D body witness anchored on the measured position), verified 2026-09-05 ~06:00 JST

Codex implemented defects 1–4 (goldens 132/132; witness agreement with the audit 534/534). Six
slices, field 1, follow audit (still/follow/missed/engine-motion) and comb audit
(registered/flat/misregistered): 35:00 292/185/10/29 | 554/65/1; 37:01 240/78/5/1 | 321/7/0;
05:00 521/53/16/9 | 572/23/12; 35:38 51/20/3/3 | 39/21/18; 01:26 66/9/2/0 | 60/9/9. The
37:01 site is closed. Two classes remain, both measured on the raw and sent as round 5 with the
per-segment parity calibration and the damage state:

- **Field 2 without a gauge sits at the standard zero while field 1 is parity-placed at +3**
  (35:38, 18 of 78 units misregistered by two lines). The per-segment relative offset
  `r = d1 − d2`, frozen once by static comb at the segment lock, places field 2 from field 1
  structurally; the comb consistency check names any later disagreement.
- **A tied body witness overrides a measurable top** (05:00 units 441–451, 01:26 units 40–50:
  the picture, bright over a black gap, moved up one line; the 2-D MAD at shifts 0 and −1 was
  9.78 vs 10.05, a 3% tie on moving content, against a 2× margin on neighbouring units). A
  witness is reliable only with a margin; tied, it abstains and the top decides.

**Damage site corrected:** on the raw panel the wrecked raster is at ordinals 62322–62326 (the
owner's original u062323), not 62308–62314. Two candidate damage metrics (row-to-row horizontal
skew; per-row skew against the previous unit) do not separate it from its neighbours because the
camera is moving; the observable is a measurement item for Codex before any state is built.

**Correction from Codex (05:56 JST), accepted:** the applied difference `d1 − d2` is NOT the
segment constant — field 1 jitters independently while field 2 holds +2, so `d1 − d2` takes +1
and 0 within one segment (35:00: (3,2)×355, (2,2)×266). Freezing it would manufacture the
crossing it is meant to remove. The segment constant is **field 2's zero** (its parity bias:
the offset between field 2's content-derived geometry coordinate and the crop that registers it
with a correctly placed field 1). Static comb calibrates that zero once per segment lock, with
field 1 known-correct at calibration; afterwards field 2 tracks its own motion against it, and
the comb runs only as a per-unit consistency check whose tie-break is the top edges under the
witness-margin rule. Corrected brief dispatched as round 5b.

## Round 5 result: `a683926` (witness margin + field-2 comb-zero calibration), verified 2026-09-05 07:45 JST

Codex's slice table reproduced exactly in the detached checkout (goldens 138/138). Comb audit
registered/flat/misregistered: 35:00 559/61/0, 37:01 322/6/0, 05:00 584/21/2, 35:38 47/23/8,
01:26 71/6/1, 45:00 608/11/0. The 35:38 residue is the causal warm-up (three decisive static
units after each segment start) and one unit the internal confidence test calls flat.
**Damage state not built:** Codex's census at 62322–62326 found the Shuttle inserts decoding,
tops measurable, body MAD 5.7–11.1, and the same torn morphology already at 62319–62321; no
observable separates the site from both neighbour ranges, and no threshold was tuned to
ordinals. Cost: engine 2.0 ms median / 2.65 ms p95 per unit (was 0.44; §11b budget 10 ms),
state 168,088 bytes.

**Whole tape, `2efc416` (before calibration):** follow audit field 1 engine-motion **837**
(round-2 baseline 954, C/D 2,971), missed moves 2,104 (2,259), follows 6,065; field 2
engine-motion 32, missed 3,078. Comb audit over 86,292 unit pairs: **78,908 registered, 3,693
flat, 3,691 misregistered** (+1 ×2,038, +2 ×902, −1 ×691, others 60) — the whole-tape
"combing under yadif" figure before calibration. The `a683926` whole-tape pass is running.

## Round 5 whole-tape sidecar of `a683926` (2026-09-05 07:45 JST) — two zero defects, sent as round 6

Paced replay 86,293/86,293, zero drops; parity Calibrated 83,705 / Uncalibrated 2,514 / Drift
74; field-2 zero Comb 51,035 (first recording 43,671), Envelope 34,805, Standard 406.

- **Runaway field-2 zero** at minute 43: the bias walks from 4 to 41 lines, one line every ~4
  units — field 2 is held out of range so its crop never follows the zero, the comb at the held
  crops keeps reading +1, Drift fires, and recalibration derives the next zero from the current
  one (an integrator with no feedback); 852 units end with |bias| > 3. The comb's +1 there was
  field 1's error (geometry-placed under a corrupted zero), mis-attributed to field 2.
- **Single-unit zero re-anchor** (`seed_from_gauge`), both gauges, both fields: field 1's zero
  flips 23↔22 320 times, always on a caption-placed unit whose measured top alternates between
  caption+1 and caption+2 because this recording's line 22 carries flickering video; lock_top is
  22 in 28,359 second-recording units. Every geometry-placed unit under the wrong zero is one
  line off (the (4,2) class, 777 units; the first recording's one-too-low classes, 513). Field
  2's envelope gauge re-anchors from a single picture-line hit the same way.
- **ZeroConflict** (175 units, minutes 28–35): envelope zero one line high against a decisive
  comb with field 1 parity-placed; under the picture-over-VBI rule the comb should win the zero.
- A plain discontinuity discards the calibrated zero, against the plan's contract.

Rules sent: the zero is a segment constant, re-anchored only on ≥ 3 consecutive identical
gauge readings; bounded to ±3 lines of the standard origin; calibration and drift only with a
parity-placed field 1 and a field 2 actually placed on its zero; the target zero derived from
the observed geometry, never from the current zero.

**Whole-tape raw audits of `a683926` (2026-09-05 ~08:10 JST):** comb misregistered
**3,691 → 2,485** (registered 78,908 → 80,422); follow field 1 engine-motion **837 → 1,238**,
missed 2,104 → 2,013; field 2 engine-motion 32 → 146 (the calibration moving field 2). The
regression is the margin rule's fallback: 550 of the 570 new engine-motion units have the body
witness abstaining as tied and the crop then placed on the top alone (GeometryLockDecides 418)
while the 2-D shift without margin reads 0 in 393 of them — a tied witness must not hand the
crop to the top alone. Remaining misregistered classes: (4,2) under field-1 zero 22 — 717
(round 6, item B); first recording (0,0) held by `TopBodyDisagree` with the top at line 24 in
every unit, body still, comb disagreeing by one in 178 of 464 — runs that begin right after a
unit whose witness was invalid (a cut), i.e. a wrong first placement or a missed move that the
still body then preserves (114 runs, up to 15 units); ZeroConflict 270 (item C); (3,0) at the
standard zero 82 (warm-up). Rule for round 7: the top and the comb check agreeing against a
still or absent body is picture evidence and moves the crop; the top alone never does after
the segment's first placement.

## Round 6 result: `7e10fee` (Codex, 2026-09-05 08:30 JST; Claude's verification running)

Zero handling rebuilt with failing-first goldens (146/146 → 169/169): a different zero needs
three consecutive identical gauge bases (alternating bases and a singleton envelope leave it);
comb calibration requires a parity-placed field 1 and a field-2 crop actually on its zero, the
candidate zero comes from observed geometry, and either field's zero is refused outside the
standard origin ±3; a decisive parity-referenced comb replaces a conflicting envelope zero once
(`ZeroConflict` is an installation event, two on the tape); a byte hole preserves installed
zeros and calibration. Codex's whole tape: 86,293/86,293, zero drops; parity truth 40,237/40,237
and 25/25; Calibrated 81,960 / Uncalibrated 4,329 / Drift 4; field-2 zero Comb 80,064,
Envelope 2,104, Standard 4,101; bias 0 ×49,688, +1 ×23,604, +2 ×13,001, none beyond ±3; minute
43 flat at +2. Engine 0.386 ms median / 1.358 p95. Slice tables unchanged from `a683926` (the
stricter reference reduces calibration coverage: 05:00 calibrated 325/608 instead of 601/608).
Not merge-ready by either agent: the round-7 classes (tied-witness fallback, top+comb against a
still body) and the 35:38 warm-up remain, and the damage discriminator is unresolved.

## Round 7 result: `d871f1f` — a falsification (Codex, 2026-09-05 09:20 JST)

Claude's slice verification of `7e10fee` reproduced Codex's table exactly (whole tape running).
Round 7 implemented "the top alone never moves the crop": geometry tops need a body or comb
witness (`TopUncorroborated`), and — beyond the brief — parity-placed tops too
(`53e93e7 corroborate parity-top motion`); an unfrozen comb may corroborate a top. Result: the
F golden slice (0:57) goes 23 → 0 misregistered and the crop reaches +1 by the third unit, but
the whole tape loses **2,616 parity-truth placements** (field 1 37,524 agree, 97 vetoes, 2,616
disagree, nearly all `TopUncorroborated`), 35:00 missed moves rise 7 → 53, 37:01 4 → 30, and
the uncalibrated comb witness itself produces 19 false moves at 05:00 (engine-motion 11 → 19).
Comb `n.a.` explained and fixed: the current-unit comb measurement had been gated on the
calibration-reference eligibility (field 1 parity-placed and field 2 on its zero), which must
gate only calibration and drift. Merge-ready: no, by both agents. Lesson: a caption placement
is a gauge reading, not a top; the picture may veto it when the picture is measurable, but a
tied or absent witness is not a veto. Claude is measuring the 19 false comb moves before the
next brief.

**Round 7 post-mortem, measured (2026-09-05 09:30 JST).** The 19 "false" comb-corroborated
moves at 05:00 are late CORRECT moves: the raster moved one line at a unit where the body
witness was tied (margins 12% and 18%), the engine held (`TopUncorroborated`), and the comb
corroborated the still-displaced top one unit later. A unit-to-unit follow audit labels the
late correction "engine-motion" and cannot tell it from a false move; **the comb audit and the
parity acceptance are the deciding instruments; follow-audit engine-motion counts are
indicative only.** Witness margin against caption truth (35:00, 37:01): a reading with
MAD(best)/MAD(second) ≤ 0.8 is wrong in about 1 of 500 units, so 0.8 is the right reliability
threshold — but 32 of 175 and 15 of 61 true moves lie above it, so abstention is frequent and
must not become a hold. Rule E is reversed: a parity placement applies unless a reliable
witness contradicts it; on a tied body the comb decides when measurable and otherwise the top
does. Sent as round 8.

## Round 8 result: `490877b` (Codex, 2026-09-05 10:10 JST; Claude's whole-tape verification running)

Parity gate removed; on a tied body a measurable comb decides (`TopCombCorroborated` /
`TopCombVetoed`) and a flat comb leaves the top to place (`TopOnly`); F kept. Goldens 183/186 →
186/186; the 05:00 sequence 63–68 places 64 and 67 at +1 by the top with no hold. Slices, comb
misregistered: 35:00 0, 37:01 0, 05:00 2, 35:38 7, 01:26 1, 45:00 0 (total 10; `d871f1f` 33;
`a683926` 12). Codex's whole tape: 86,293/86,293, zero drops; parity acceptance field 1 40,208
agree + 29 named vetoes + 0 disagreements, field 2 24 + 1 + 0; Calibrated 82,051 / Uncalibrated
4,239 / Drift 3; bias 0 ×49,688, +1 ×22,027, +2 ×14,578, none beyond ±3. Field-1 reasons:
GeometryLockDecides 43,469, Line21Placement 39,007, TopBodyDisagree 1,153, ZeroCandidate 1,077,
TopOnly 966, TopCombVetoed 159, TopCombCorroborated 118. Engine 1.35 ms median / 1.37 p95.
Codex: merge-ready for the round-8 changes; the raster-damage state remains deferred (no
discriminator). Claude's gate: the whole-tape comb audit against `a683926`'s 2,485 and the
parity acceptance by my own script; then a Codex review of my instruments.

**Codex's review of Claude's instruments (2026-09-05 10:18 JST), ten findings, seven fixed on
main:** the comb audit sampled the previous unit at the current crop and built a different
static mask per candidate shift (now one mask at the previous unit's own published crops);
"registered" bypassed the uniqueness test (now both verdicts need a unique minimum with a 25%
drop, so many units move to `flat`: 37:01 322/6/0 → 246/82/0, 05:00 584/21/2 → 446/160/1); the
readers failed open on a truncated walk and compared exact units across a short unit (now fail
with exit 2 unless every exact sidecar row was audited; pairs need consecutive ordinals);
content-motion was ungated (now MAD ≤ 25 in both fields); the parity acceptance did not require
complete coverage, truncated mismatched lists through `zip`, and trusted vetoes by label
(`AnchorUncorroborated` wrongly exempt) — now key sets must be equal, lengths asserted, and a
veto counts only with the sidecar's body evidence. Documented, not fixed: the comb metric is a
weave-continuity proxy, not a yadif output measurement; the low-16-bit counter join is safe only
for a sidecar produced by the same capture walk. Both agents' acceptance rules give the same
figures on the round-8 sidecar (40,208 + 26 + 3 + 0).

## Round 8 verified and accepted (2026-09-05 12:06 JST)

Claude's replay of `490877b`: 86,293/86,293, zero drops; parity acceptance with the fixed script
field 1 **40,208 agree + 26 + 3 evidence-checked vetoes + 0 disagreements**, field 2 24 + 1 + 0
(identical to Codex's); comb audit with the fixed rule **55,024 registered / 30,213 flat /
1,052 misregistered** (`a683926` under the same rule: 53,933 / 30,467 / 1,889; the old rule's
2,485 and 3,691 are not comparable). The first recording is essentially clean; minutes with
≥ 30 misregistered units: 27 (87), 42 (37), **43 (715)**, 44 (93). Merge requested.

**The minute-43 class (715 of 1,798 units, +1):** no caption for ~1,740 units; field 1's zero
is 22 (three consecutive captions with the top at caption+1), field 2's zero 284 was installed
by the comb calibration while line 285 was dark; then both measured tops sit one line lower
than their zeros predict (26 and 288), field 1 places at 4, field 2 measures 4, out of range,
holds 2, and the comb disagrees by one for 668 units with `Drift` ineligible because field 2 is
held. Diagnosis: on a recording whose blank lines 22 and 285 carry intermittent video, the
picture top is one line ambiguous and `d = top − zero` inherits the ambiguity no matter how
the zero is chosen. Proposal put to Codex as a concept question (no code until agreed):
body-primary tracking between gauge readings, the top as veto only, the comb check correcting
a persistent disagreement, the zero used only when nothing else exists.

## Round 9 (2026-09-05 12:22 JST): tracking falsified offline, comb correction proposed; render-live merged

Codex simulated Claude's body-primary tracking proposal from the `490877b` sidecar and it fails
decisively: anchored at the last caption/comb-registered pair (ordinal 77,899, (3,2)) and
accumulating every reliable body shift, the tracked pair ends at **(34, 36)**; it matches only
172 of the 715 decisive comb readings at minute 43 (resetting per classifier interval: 101).
The 0.8 margin proves a unique CONTENT match, not raster displacement — camera and subject
motion integrate as false registration. Availability: on caption-absent field-1 units of the
second recording the body witness is reliable in 62.6% (minute-43 tail 37.5%), and only 7.1%
of caption-absent units lie in a classifier interval that ever had a caption. **Codex's
proposal, accepted:** the body stays a one-unit corroborator, never an integrator; after three
decisive static-comb readings install a bounded RELATIVE crop correction computed from the
current crops (never an incremented zero), persist it across flat units, clear it only on
signal-lock loss; a content cut invalidates the body profile but not the source's line/parity
reference. Field-2 `+4` stays out of range: the raw comb says the needed correction at minute
43 is `d2 = 3`, and a 240-line crop from `+4` needs one row beyond the 525-line buffer (a
separately named padding-extension path, later). Merge: `render-live` `490877b` merged into
main via Codex's tested merge commit `339b83a` (all suites pass on the merged tree), landed as
`cb1b4ed` because main had moved by one experiments commit; goldens 186/186 on main.

## Owner ruling on damaged rasters (2026-09-05, after the night's rounds)

"The previous good geometry should be saved each frame, not overwritten. Damaged rasters should
not be corrected but held at that geometry. Once the damage clears, the new geometry should be
checked against the old geometry and the position readjusted accordingly."

Engine consequences (to Codex after round 10): a per-field **saved good geometry** (top, bottom,
height, applied offset, the gauge that placed it) written only by units that placed on evidence,
never by a hold or a damaged unit — distinct from `last_applied`; a damaged unit (readings that
contradict each other: top against a reliable body, height change without a clip explanation,
undecidable comb — the only damage signature measured so far, since the Shuttle's inserts still
decode and tops stay measurable on the torn units) holds the saved geometry and is named
`DamageHold` in the sidecar; on the first clean units after a hold the new measurement is
checked against the saved geometry, the crop readjusts once if they differ, and the sidecar
records the jump and the difference — the one place the picture may move.

**Owner (2026-09-05):** once the algorithm is right, take it through optimization rounds — but
only after the watch copy has been verified correct. Order: round 10, round 11, live-path watch
copy with the full-tape overlay, owner review, then optimization.

## Round 10 in progress (2026-09-05 14:30 JST): bounded comb relative correction

Codex: red golden `b16b2f4` (install once on the third decisive reading, no accumulation,
survives a discontinuity, cleared only by begin_segment), implementation `d697f4e`, then a
regression it caught itself on the first whole-tape oracle — widening the engine's existing
per-unit comb check from ±1 to ±3 changed the top-veto semantics and converted 63 parity
placements into picture vetoes — fixed at `11d6378` (the ±3 search serves only the three-sample
correction state; the per-unit ±1 check is untouched), goldens 194/194. Slices: comb
misregistered 0/0/1/6/1/0 on the six established windows and 3 cold-start units on the
minute-43 slice (the correction installs on its third decisive reading and holds (4,3) for the
remaining 303 units). Codex's final whole-tape pass from `11d6378` is running; Claude's
verification (seven slices, whole tape, acceptance, both audits) targets `11d6378`.

## v7 and v8 on the same instruments (2026-09-05 15:00 JST), answering the owner's question

Whole-tape replays of v7 (`abfa648`) and v8 (`bottom-edge-v8` at `0fc4ade`) through the
fixed comb audit and the parity acceptance. Both older engines use the pre-RP-202 crop origin
(rows 17/280), so their field-1 placement is compared to the caption truth after the best
constant offset (+2 for both); round 8 needs none.

| engine | comb misregistered / flat / registered (86,293 pairs) | field-1 agreement with the tape's caption (40,237 readings) | applied-pair transitions / one-unit flips |
|---|---|---|---|
| v7 | 1,851 / 35,405 / 49,027 | 31,092 (77.3%) | follow audit: field 1 engine-motion 2,059 / missed 3,527; field 2 engine-motion 84 |
| v8 | **326** / 35,372 / 50,591 | 30,403 (75.6%): 7,018 of the 16,670 +3 excursions missed | 11,544 / 3,921 (follow audit: field 1 engine-motion 2,525 / missed 2,973; field 2 engine-motion 3,091 — round 8: 1,181 / 2,023; 116) |
| v9 round 8 | 1,052 / 30,213 / 55,024 | **40,208 (99.9%)** | 7,614 / 2,974 |
| v9 round 10 (`2f8bb86`, merged `7254d58`) | **165** / 30,073 / 56,051 | **40,208 (99.9%)** | follow audit: field 1 engine-motion 1,190 / missed 2,031; field 2 181 |

Reading: v8 places both fields from the same kind of gauge (bottom edges), so they stay
mutually consistent — where v8 is one line off the caption it is usually one line off in BOTH
fields (its (0,−1) ≡ (2,1) in round-8 coordinates carries the same weave as round 8's (3,2)),
which the comb audit cannot see and the caption can: the whole picture sits a line high and
jumps when v8 later moves. On the 35:00 slice, units whose caption puts field 1 at +3 register
at (3,2) in 129 of 129 measurable units and never at (2,2) or (3,3), so round 8's absolute
placement is confirmed by the comb where it can judge. v9 fixes the absolute-placement class
(the owner's never-bounce invariant) that v7/v8 could not measure; v8 combs less today only
because round 8's residual relative class at minute 43 (715 units) is still open — round 10
closes it. Both metrics are needed: the comb sees relative error, the caption sees absolute.
Follow-up commit `094b3fb` (14:36 JST): the installed correction persists, but the field it
moves is chosen per unit from current absolute testimony, so a parity-placed field 1 is never
displaced by a correction installed on a caption-less unit. Codex's whole-tape pass from it:
parity 40,208 + 26/3 vetoes + 0, bias 0..+1, correction −1..+2; a first cold-slice rerun at
1 ms pacing shed ring/pool units and was discarded as invalid, rerun at the device cadence.
Claude's verification retargeted to `094b3fb`.

**Round 10 final (Codex, 15:39 JST; branch `round10-comb-relative` head `2f8bb86`, tree-identical
to the reported `094b3fb`):** goldens 190/194 → 194/194; whole tape 86,293/86,293, zero drops;
parity 40,208 + 26/3 vetoes + 0; Calibrated 80,329; bias 0..+1; relative correction −1..+2
(0 ×83,410, +1 ×1,657, +2 ×864, −1 ×362; 22 distinct installations); comb_safe 80,329. Minute
43 in continuous context: 296 registered / 21 flat / **1 misregistered** (ordinal 77,902, the
unit before the correction installs on its third decisive reading at 77,903); cold slice 3.
Slices (comb): 35:00 348/272/0, 37:01 246/82/0, 05:00 446/160/1, 35:38 44/28/6, 01:26 27/50/1,
45:00 294/325/0. Codex marks the branch not merge-ready over the literal zero-misregistration
slice criterion; Claude accepts the one- to three-unit calibration latency as the cost of the
three-reading rule (no backdating on the live path). Claude's whole-tape verification is running;
round 11 (damage ruling) dispatched on top of the branch.

## Round 11 falsified as specified (Codex, 16:31 JST; branch `round11-damage-hold`, `293c499`/`84274f9`)

The contradiction-based damage classifier does not fire on the torn units 62322–62326 (their
measurements are ABSENT, not contradictory: body witness unmeasurable, comb flat, inserts
present; field 2 moved 0 → 2 → 2 → 2 → 0 by `TopOnly`) and fires falsely on clean units
(05:00 `DamageHold` 14 / `DamageCleared` 6 on field 1, comb misregistered 1 → 5; 01:26
2/1). Codex stopped before the whole tape. Engine cost on that branch 4.24 ms median (round
10: ~1.4) — unexplained, to be asked. Claude's reading of the same evidence: the damage
signature is "no measurable picture testimony at all while the top changes" — body
unmeasurable (MAD > 25), comb flat — and round 8's `TopOnly` (flat comb ⇒ the top decides)
is exactly what moved field 2 on the torn units; the top alone must never place when the body
is unmeasurable. That is the round-12 rule, being checked on the round-10 sidecar first.

**Round 12 rule, from the round-10 sidecar (16:35 JST).** In whole-tape context the torn passage
62313–62328 sits between caption placements at (3,2); inside it the body witness is tied on every
unit (valid 0, MAD 5–11), the comb is flat, and the tops flip 23↔25 / 286↔289 — the engine
follows them by `TopOnly` and geometry-on-a-tied-body, which is the bounce the owner saw. The
same `TopOnly` excursions occur between captions elsewhere (62303, 62306: single-unit 2-line
bounces). Whole tape, field 1: 966 `TopOnly` moves; the comb is flat on 702 by construction, so
neither absolute instrument can score them; judged by the next caption within 30 units, 69 were
WRONG (the caption returns to the saved geometry) and 11 RIGHT. So the owner's ruling is made
operational without a damage detector: the signature is absent evidence. Evidence placements
(parity, envelope, comb calibration/correction, comb-corroborated top, geometry with a reliable
body) write the saved good geometry; a unit with no evidence holds it (`SavedGeometryHold` with
a cause); the first evidence unit after a hold compares against it and moves once if different
(`SavedGeometryReplaced` with the signed jump). `TopOnly` is removed. Expected cost: real
tied-body moves (05:00 units 64, 67) are corrected one unit late by comb corroboration.
Dispatched as round 12 on top of round 10.

## Round 10 verified and merged (2026-09-05 17:35 JST)

Claude's replay of `094b3fb` (tree-identical to `2f8bb86`): 86,293/86,293, zero drops; parity
acceptance 40,208 + 26 + 3 + 0 (field 2 24 + 1 + 0); comb audit **56,051 registered / 30,073
flat / 165 misregistered** (round 8: 1,052; v8: 326; +1 ×118, −1 ×32, +2 ×11, others 4); follow
field 1 engine-motion 1,190 / missed 2,031, field 2 181 / 2,998. Seven slices identical to
Codex's table (minute-43 cold slice 295/20/3). Merged into main as `7254d58`, goldens 194/194
on main. The one- to three-unit calibration latency of the three-reading rule is accepted.

## Round 12 in progress (Codex, branch `round12-saved-geometry`, head `a1a91c8`, 17:38 JST)

Red contract 194/205 → green; `TopOnly` removed from the vocabulary; tied/unmeasurable and
comb-vetoed paths hold the last evidence snapshot (schema 10: saved crop, hold cause, run
length, signed confirmation/replacement jump). Two regressions Codex caught itself on partial
whole-tape logs and fixed red-to-green (212/212): parity placements whose display mode was
`ZeroCandidate` were being turned into saved holds (evidence must be classified by gauge, not by
mode name), and a reliable picture veto arriving during a hold was being hidden as a hold (it
must clear the hold, update the good geometry and keep its veto name). Slices, comb
misregistered: 35:00 0, 37:01 0, 05:00 2 (the two expected late corrections), 35:38 6, 01:26 9,
45:00 0, minute-43 0, torn slice 0. The round-11 cost anomaly was contention: under identical
load round 10 is 2.95 ms and round 12 2.97 ms engine median (+0.02 ms). Codex's definitive
whole-tape pass is running; Claude's verification of `a1a91c8` started (eight slices + tape).

**Round 12 slice findings (Claude, 17:51 JST; `a1a91c8` not merged).** Codex's whole tape:
parity 40,221 + 15 + 1 + 0 (17 former vetoes became agreements, 4 the other way), torn passage
fixed (62322–62326 fixed at (2,2); the saved pair before it was (2,2)/(2,3), not the (3,2) the
brief assumed), field-1 `SavedGeometryHold` 23,442 (TiedBody 22,107) with a maximum run of 8,998
units, engine 2.97 ms median under load (round 10 2.95 under the same load; the round-11 4.24 was
contention). Two regressions on the slices, traced on the sidecars: **(A) 01:26** — a real
one-line displacement entered and left under a tied witness (units 57 and 72) and the hold kept
the stale position for 15 units while the body, reliable and still, could not prove a move; the
audit's comb calls seven of those units misregistered but the engine's comb_check reads flat on
all of them, so the comb corroboration never fired — the two comb implementations disagree.
**(B) minute 43 cold** — the raster jitters by a line each unit with the body agreeing whenever
it is reliable; on tied units the hold freezes whichever jitter phase the last evidence unit
was in (40 misregistered vs round 10's 3), and the persistent comb correction cannot follow
differential per-unit jitter. Flicker (05:00, 01:26) wants the tied-body top NOT to place;
jitter (37:01, minute 43) wants it TO place; the discriminator is the body's verdict on the
top's moves in the surrounding reliable units. Sent to Codex as an analysis turn (comb
reconciliation; the discriminator measured on the sidecars) before any code.

## Round 13 analysis (Codex, 18:14 JST) — accepted

(A) The engine's comb and the audit's differ: per-shift masks vs one mask, only the energy row
tested static vs both adjacent field-2 rows, previous unit at the current crop vs its own
published crops, and the logged reading taken at the provisional `baseline_d` before saved
geometry and the installed correction — which explains much of minute 43. Reconciliation:
the C code reproduces the audit exactly, with two sidecar readings (`comb_input_*` at the
provisional crops as decision evidence; `comb_check` recomputed at the published crops,
identical to the acceptance audit). Hold causes to be named truthfully (nine of the fourteen
01:26 hold units had a reliable, still body: `TopDisagreesBodyStill`, not `TiedBody`).
(B) A learned "top reliability" history does NOT separate real jitter from first-line
flicker: at the best window (N = 16, ≥ 90% corroborated) it accepts 8 of 10 RIGHT top-only
placements but also 43 of 69 WRONG ones; 37:01, minute 43 and 01:26 all show 100%
corroborated histories. Rejected. Codex's replacement: a physical landmark — locate the tape's
black gap line independently and require it to translate with the picture top (a rigid move
shifts both; a first-line brightness flicker moves the thresholded top while the gap stays);
where neither landmark nor comb is available, `SavedGeometryHold` is the honest result.
Comb-correction installation guards: three readings of the same nonzero shift, reliable bodies
in both fields, no differential body motion across each transition. Round 14 dispatched:
reconciliation, guards and cause names as code; the landmark measured on the raw first (05:00
unit 440→441 is the case that could falsify it).

**The tape's black line 22 is a per-unit displacement gauge (Claude, raw, 18:17 JST).** Rows
16..26 at 01:26 and 05:00: row 18 is black in EVERY unit (the regenerated line 22, like the
inserts); the TAPE's black line 22 (Y ≈ 4–7, above the 1.4 blanking, below any picture) sits at
row 18 + d: at row 20 below the caption when the field is at +2 (01:26 units 55–56: `22 24 1 57
4 136`), at row 19 when at +1 (01:26 units 57–71 `22 24 1 4 134`; 05:00 units 64, 67, 440 `22
23 1 4 139`), coincident with row 18 when aligned (05:00 unit 441 `22 24 1 136`). So the 05:00
"first-line brightness flicker" of round 4 was WRONG: those were one-line moves the body
witness was blind to, and the comb agreed. In the first recording, where captions are scarce
and line 22 is black on the tape, this gauge reads d1 every unit — including the tied-body
units that round 8 placed late and round 12 holds. Steered into Codex's landmark measurement:
tape_gap = the last dark row before the picture in rows 18..24, d1 = tape_gap − 18, valid when
unique and when the segment's gap gauge agrees with its captions where both exist; the second
recording (video on line 22) has no gap but has captions nearly everywhere.
**Gap gauge validated against the caption truth (Claude, 18:28 JST):** rule = the last dark row
(row mean ≤ 10) before the first two picture rows (> 12) in rows 18..29, d1 = row − 18. Where a
caption exists in the first recording the two agree **263/263** (first 100 s) and **46/46**
(05:00), all at d = 2. Without a caption the gauge reads +1 in 2,065 of ~3,000 first-100-s units
and 0 in 445 (None 198; > 2 in 5 dark units — bound it to 0..3); at 05:00 +1 in 438, 0 in 122 —
so the SP intro sits at +1, as round 10's (1,0) placements and the comb audit say, and the
2026-09-04 census reading of the intro as "locked with a blank line 23" was wrong. On the
second recording a naive gap reading returns 0 in 621/621 units where the truth is +2/+3 (line
22 carries video): the gauge must be gated per segment by agreement with its captions. Both
facts steered into Codex's round-14 measurement.

## Round 14 in progress (Codex, 19:19 JST; branch `round12-saved-geometry`, head `e310f47`)

Red goldens `ffb626c` (218/220) → 226/226. **Canonical comb:** the engine now reproduces
`relative_comb_audit.py` exactly — 2,677/2,677 jointly computed slice verdicts identical (nine
`n.a.` rows where a signal-state reset cleared the engine's previous raster). **Gap gauge**
implemented as a field-1 gauge behind a segment gate: Codex's first census found that letting a
displaced dark row enable the gate by itself transiently enabled it in the second recording
before a caption rejected it, so self-enablement was removed with its own red golden — only
caption agreement authorizes gap placement, one disagreement rejects it until relock. Bounded
results before the final pass: 01:26 re-places on the first caption-less unit (57); 05:00 units
64 and 67 place immediately; second-recording slices reject the gate and keep their caption /
envelope placements. Comb-correction installation guards and truthful hold causes landed. The
strict caption-authorized build's whole-tape pass is Codex's final report; Claude's verification
of `e310f47` starts when the round-12 audits finish.
**Round 12 (`a1a91c8`) whole tape, Claude (19:37 JST):** parity 40,221 + 15 + 1 + 0 as Codex
reported; comb **54,737 registered / 30,932 flat / 620 misregistered** (round 10: 165) — the
hold-on-absent-evidence rule fixed the torn passage but froze stale positions and the wrong
phase of real jitter across the tape (+1 ×489, −1 ×58, −2 ×54, +2 ×19); follow field 1
engine-motion 1,039 / missed 2,884. Not merged; superseded on the same branch by round 14 (gap
gauge, canonical comb), whose verification is running.

## History rewrite: commit-message trailers (2026-09-05 20:38 JST, owner order)

Eighteen of Codex's commits since 2026-09-04 22:02 carried the two characters `\n` in the
message body instead of line breaks (a shell string that never interpreted the escape), so
Git did not parse their `Co-authored-by` trailer. Found by scanning every commit's message
bytes; Claude's reviews had read code and numbers, never the message bytes — a review gap,
now on the merge checklist. Fixed with `git filter-branch --msg-filter` over every non-backup
branch: trees byte-identical to the backups on all 14 branches, author and committer dates and
subjects identical (main and round12 diffed line by line), zero offenders remaining on any
working branch. Backups kept as `backup/<branch>-pre-trailer-fix` until the owner releases
them. Cited hashes in this document and CLAUDE.md map as follows (old → new; commits before
the first offender are unchanged, e.g. `e1c91f6`, `dc8a459`, `2efc416`):
`490877b → 56edda0`, `339b83a → 92963f3`, `cb1b4ed → fb582c9`, `7254d58 → 5b6ae68`,
`2f8bb86 → 63b5bf7`, `a683926 → a4a1bec`, `af6ff63 → 1a660cf`, `7e10fee → 72c1260`,
`d871f1f → 67a9752`, `a1a91c8 → ac36073`, `e310f47 → 7fa4a64`, `3aacdc7 → 6d919a2`.
Codex's worktree on `round12-saved-geometry` follows the rewritten branch (head `6d919a2`).

## STOP-WORK and role switch (owner, 2026-09-05 evening)

The v9 engine, rounds 1–14, inverted the contract: geometry is the authority, everything else
confirms it; holds only on a torn raster (keep the previous decision, re-evaluate on
restabilising) or a lost lock (invalidate, restart at zero); line 22 never renders. No further
rounds on this base. Sequence: (1) archaeology Part II in `docs/registration_archaeology.md`
(one document; Codex's own account merged with attribution); (2) a new branch on which Claude
writes the geometry-first engine from the reference raster and the owner's words, and Codex
writes the validation harness, neither reading the other's prior engine/harness work; (3) the
round-14 audits run to completion so the merged round-10 main stays a measured fallback. Every
constant in the new engine derives from the raster or is labelled a tape-fitted default.

**Gap-gauge placement audit, whole tape (22:27 JST; `gap_gauge_audit.py`, valid only where the
source's line 22 is black — the OFF+2/OFF+3 masses are the second recording, where the naive gap
reads 0 against a caption truth of +2/+3 and must be ignored).** First-recording-relevant
classes, field 1 (sign = applied − gap): **crop too HIGH by one** (the tape's black line inside
the top of the frame, OFF−1): round 10 319, round 12 885; **crop too LOW by one** (the picture's
first line cut off and one more line of the head-switch band pulled in, OFF+1): round 10 2,956,
round 12 3,813; agree 46,312 / 44,825. Field 2: too high 367 / 275, too low 1,197 / 608. Both
error directions exist in the merged round 10; round 12 made both worse on field 1. (An earlier
version of this note called the OFF+1 class "the black line in the crop"; that is the OFF−1
class — corrected 2026-09-06 after the owner asked.) Round-14 figures
follow when its verification lands; all three are the fallback-base record, not acceptance.

**Round 14 (`6d919a2`) verification, Claude (22:51 JST): NOT a valid acceptance run.** Goldens
235/235 and all eight slices reproduce Codex's table (comb misregistered 0/0/1/5/1/0, minute-43
cold 25, torn 0). But the whole-tape paced replay in my checkout, run while three other whole-tape
audits shared the machine, dropped **4,154 units at the pool and 153 at the ring** (published
81,986 of 86,293; the acceptance failed closed on the first `PoolFull` row). Round 14's worker
cost (Codex: 6.4 ms median / 10.06 ms p95) no longer keeps up with a 4 ms transfer pace under
load — the §11b concern made concrete. The audits of the incomplete run are indicative only: comb
763 misregistered, gap gauge field 1 OFF+1 1,791 (round 10: 2,956), follow field 1 engine-motion
5,215. Round 10 (`5b6ae68`, merged main) remains the only verified fallback base. A second
round-14 pass at half pace on an idle machine is running for the record.

**Round 14 half-pace record run (Claude, 2026-09-06 00:59 JST; `6d919a2`, idle machine, 8 ms
pace, pool 128): clean — 86,293/86,293, zero drops.** Parity 40,217 + 18/2 vetoes + 0. Comb
**55,315 registered / 30,352 flat / 622 misregistered** (round 10: 165; −1 ×388, +1 ×188). Gap
gauge field 1: too high 277 (round 10: 319), too low 2,642 (2,956); field 2: too high 323 (367),
too low 1,066 (1,197). Round 14 buys a small gain on the absolute classes with a large loss on
the relative one. **Round 10 (`5b6ae68`) remains the fallback base.** Round 14 is not merged.

**Owner refinement of the hold contract (2026-09-06 00:55):** a vertically torn picture is the
same class as a lost lock — old geometry invalid, re-acquire from zero when the lock returns.
Horizontal tearing is not a geometry event (Codex's damage census keyed on it, wrongly). Only
dropout or RF noise that makes the bottom edge unstable is the "keep the previous decision and
re-evaluate when it restabilises" case. The ruling on damage therefore reduces to something the
raster decides; no owner ruling is needed per unit.
