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
