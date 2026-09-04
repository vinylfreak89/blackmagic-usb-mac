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
