# Geometry-first registration engine — the contract

The single current contract for the registration engine and its validation harness, edited in place only by both
agents' agreement (HANDBACK.md §2). Codex writes the engine (`src/field_registration/`, C, branch `v10-engine`),
Claude the harness (`experiments/`, branch `v10-harness`); each reviews the other's code and intent (CLAUDE.md §14;
the owner, 2026-09-07 20:10: "The roles reverse again ... Codex will go back to owning the code, you owning the test
harness"). Line numbers are NTSC lines; unit row r is line r+4.
Every number is a standard (NTSC, SMPTE RP-202, CEA-608), a measurement on the captures (stated with its value), or a
memory capacity; any other number in the code is a defect.

## 1. The owner's rules, verbatim

**Intent (2026-09-04/06).** Geometry is the authority. Each field's active picture area — its top edge, bottom edge
and height — measured on every unit places the crop. Everything else (the tape's line 21, its black line 22, static
comb, any temporal witness) exists only to confirm that reading where geometry alone cannot decide: (1) the
head-switch region makes the bottom edge noisy and field-to-field inconsistent; (2) geometry does not say which
field's lines interleave on top — field precedence is settled once per lock and held; (3) boxed pictures have their
own geometry, centred in the raster, and black level is not assumed constant. Tracking breaks only on a vertically
torn raster or a lost lock — both are one class: old geometry invalid, back to zero, re-acquire when the lock
returns. Horizontal tearing is not a geometry event. Dropout or RF noise that hides an edge keeps the previous
decision and re-evaluates when it clears. Line 22 never renders. The output picture never moves except at a
segment's initial lock and after such a re-acquisition.

**The model (2026-09-06 evening, written back and accepted).** One question per field per unit: where does the
picture start, and did it move since the last unit. The conserved quantity is the line account, not the height:
the number of bands above the picture and the number of bands below it; a field moved when the bands above it grew
by X and the bands below it shrank by X (or the reverse), and this holds past the raster bounds — nothing deletes
lines from the middle of a field except a vertical tear. A picture movement seen in both fields is content, not
displacement; new lines of luma appearing at the top alone never mean the picture moved, unless that shift causes a
comb disagreement on the settled comb. No lock is claimed without at least one confirmation that the geometry is
correct — combing, captions, or both; without it the picture stays at standard placement (23/286) and the record
says there was not enough to lock on. The row directly above the picture that sometimes carries data and sometimes
a faint copy of the line below is decided by geometry, never by classifying the row: if the bands below did not
change, the field did not move. Captions are confirmation; a caption may place the very first unit of a segment; a
caption that disagrees with measured geometry is logged, geometry wins. Segment events (splice, signal loss, relock)
come from the signal-state layer as explicit inputs; never inferred from a body-half heuristic. A raster whose edges
cannot be measured at all is Unknown, held and labelled, never a substituted number. Tests are dumb and brute force: picture visible is the top, picture gone is the bottom; black is
the hard case and every not-sure class is worked through, never thresholded away.

**The head switch (2026-09-07 03:09–03:35, the owner's transcript, `briefs/owner_verbatim_transcript.md`).**
Blanking bounds the geometry above and below; the picture is the rows between, and a field closes to 240 lines
(top + 239) whether or not all of them are visible. The reliable geometry is the top of the picture to the row before
the head switch. The head switch is one of: discontinuous horizontal skew, an RF peak in the luma, or both, plus an
AGC level mismatch where present; the peak carries the tear with it, so its horizontal position on the line is
measured when present; it drifts slowly and never jumps from one side to the other; the TBC can smooth it away and
render the partial line as picture, and then the band's row count is what survives. The head switch is optional (not
every source is VHS): "not applicable" is distinct from "unmeasurable". The band is the unreliable part of the
geometry; its row count is confirmed by secondary signals (comb between the fields, VBI, captions), ideally more
than one; the band count alone never moves anything. A whole field can mistime and fall out of the Shuttle's raster:
cues present one frame and absent the next mean they shifted away, near-certain when the top shifts too.

**2026-09-07 afternoon, verbatim.**
> The horizontal line carrying the peak either moving into the other field or disappearing off the edge should
> maintain that as the head switch line even if it has a fully stable line of picture. [Clarified later the same day:]
> its height should be fixed, or which is the top line shouldn't move — not the band itself, which absolutely can move
> if the whole picture does.

> Blank lines at the bottom of the picture could be indicative that the entire picture is shifted up.

> Why is the engine measuring garbage in the rewind section. As there is not a stable VBI yet, why isn't that measured
> as no stable lock?

> It should not be fixed in the case the picture shifts. It is NOT a fixed position. The height of it I expect to be
> fixed not its position, but if that height changes other than for the reason I said, I should know about it.

> The number of switch lines below the top line either stays constant or decreases. The top switch line should be the
> only variable one as that's the actual area of travel.

> [The black line 22 comparator] should not be per source. No magic numbers. It should be derived and stabilized. ie,
> check the number of times that level has appeared. If it's appeared more often than any other level, then it becomes
> the comparator and replaces the previous comparator which the number of times it has appeared.

> You also need to keep a fixed number. If it falls below that number it drops out and the entire array shifts. No
> dynamic memory allocation (in the real C engine). [And:] Why are you ever decrementing counts.

> A change of geometry (a loss of source lock or lock like loss) resets everything immediately.

> Whenever you don't have extreme confidence in something go back to the design. If your understanding is
> contradictory, understand why; don't just assume the contract is right.

> [On the hidden upward top, 16:20:] If the source has real picture on line 22 that originated correctly on line 22
> it should get dropped. If it's line 23 shifted to line 22, that should become the first line of the 480 line render.
> If the picture is truly shifted up by 1, then the top line of the render will be a blank line. If it's shifted up
> by 2, then the first line will be line 21 captions, etc. The real derived line 23 should be the consistent line 23
> that is displayed by that source. If the Shuttle overwrote it, tough noogies.

> [On damage:] There are only two true program splits across this tape. Anything that's not snow-like or a vertical
> tear (cross-program or true tear) should be indicative of continuing program and therefore previous geometry (not
> position) holds through the damage. [On snow:] Snow units mean the lock is gone. Everything resets — both fields at
> the same time. [On the body shift:] It is not a fixed −3..+3; it is whatever is required. Cross-correlation between
> the two fields might be needed, but is probably overkill — a maybe.

> [15:40] [Blank lines under the picture] could be indicative. Needs to be confirmed against the comb. The height
> counts should be both head switching and non head switching. Number of picture lines should indicate position
> assuming the number of head switch lines stay fixed. In other words, 237 real picture lines + 3 head switch lines =
> 0 offset (basis assumption of geometry requiring confirmation). Most important is agreement. Line 23 remains the
> top line always. VBI should never be rendered (so for instance extra black on the bottom is okay but obviously
> letterboxing and such the picture should be centered). If the full picture starts at 23 and goes say to 235 only
> and then head switch from 236–238 then full geometry is 237 lines, not 238 lines, not 240.


## 2. What the captures show (measured)

| unit rows | NTSC lines | content | origin |
|---|---|---|---|
| 0–6, 261–269, 523–524 | 4–10, 265–273, 527–528 | padding, Y 16.0 / C 128.0 exactly | Shuttle |
| 7–15, 270–278 | 11–19, 274–282 | blanking, Y 1.4 ± 0.5 | Shuttle |
| 16, 279 | 20, 283 | timing pulse pattern, std 40–54 when present | Shuttle, when its decoder has sync |
| 17, 280 | 21, 284 | CEA-608 insert: the tape's bytes when it decodes them at the standard line, else nulls | Shuttle, when its decoder has sync |
| 18, 281 | 22, 285 | blanking, Y 1.4 | Shuttle |
| 19–260, 282–522 | 23–264, 286–526 | pass-through from the tape and deck | source |

- Nothing the tape carries above line 23 (286) reaches us except the re-encoded bytes on the insert. The tape's own
  VBI becomes visible only when the field is displaced downward: at +1 its black line 22 appears on line 23 (luma
  4–7 on fixture A), at +2 its line 21 on 23, at +3 its line 20 on 23 and its line 21 on 24.
- The deck clips each field at line 262 / 525 on every capture (its clip line); lines 263–264 / 526 of the
  pass-through region carry only the near-blank remainder and the chroma noise of the decoder.
- Noise gaps on the commercial capture: the Shuttle's regenerated rows have chroma noise ≤ 1.48 times the blanking
  rows'; recorded rows ≥ 2.02 times. The blanking rows' luma noise is 0.5 (std within a row).
- Row signatures (SP recording, both passes, verified units 20/78/105/106/200): picture rows match the row above
  at a segment lag of 0–1 with mean |difference| 8–17; the first other-head row has a median segment lag ≥ 10 and
  mean |difference| 35–80; the RF peak is a spike ≥ 4 times the row's mean |difference| at the same sample in both
  passes, on an otherwise aligned row, with the next row torn from that sample on; the V-stabilize-on pass ends the
  band with a flat pedestal row (std < 1.1). On the commercial tape the other head's rows carry its horizontal
  blanking in mid-row (luma 1–2 at the blank's noise, samples ~60–200); on the SP recording that run sits at the
  pedestal (luma ~11), not at the blank.
- A row of chroma noise can sit below the band (commercial rewind units, line 263: chroma std 3.08 against 0.5), so
  chroma alone overstates the band bottom by one line there.
- "Field 1" and "field 2" name transport slots. The Shuttle grouped the same field sequence one field later on the
  V-stabilize-off capture of the SP passage (its field-1 slot is the original's field 2 of the previous unit, MAD
  2.6–3.0 against 7–12 for any other pairing); every per-field quantity is measured per capture on the slot's own
  content.
- The deck's line TBC (V-stabilize) drops rows it cannot time at the top of a field and shifts the rest down by that
  count (one line in most SP units, two where the tear is worse), clipping the bottom by as much; with it off the
  picture starts on its standard line in every unit, the first one or two lines carry a horizontal timing error
  that varies along the row (flagging), and the head switch's RF peak and timing step are visible. The rows from the
  picture top to the switch line are the same in both passes (237 at units 20, 105, 200).
- The commercial tape's picture is stable from counter 6593 onward (before it the tape is rewinding); its pedestal
  measures 9–11, the same as fixture A's 11.4 (both tapes have setup); its head switch sits on line 260 or 261 in
  every measurable unit, and with the peak present the rows from the top to the switch row are 238 in 31 of 36
  field-1 units and 237 in 48 of 59 field-2 units.
- Field 2's band is one row longer than field 1's on the SP, EP and commercial tapes (SP: two rows in 427 of 606
  units against three or four in 597 of 608).

## 3. Definitions

- **Recorded row**: a pass-through row that came through the analog decoder, told from the Shuttle's regenerated
  rows by the decoder's noise: chroma noise above twice the blanking rows' (the measured gap of section 2, regenerated
  ≤ 1.48×, recorded ≥ 2.02×, the test at its lower bound), or luma above the blank; padding is neither.
- **Pedestal**: the tape's black — the other head's black rows at the bottom of the band.
- **VBI row**: a recorded row carrying a vertical-interval signal, recognised by signature: the CEA-608 waveform
  (standard), the run-in burst without data (standard), the tape's line-20 timing pattern (the same pattern as the
  Shuttle's regenerated line 20), the smeared XDS bar (measured on the EP recording), the tape's black line 22, the
  tape's grey line 22 (a flat row under half the brightness of the three rows below it, owner ruling 2026-09-05).
  "Line 22" in this document is the TAPE's line 22 wherever it lands in the raster (line 23 at +1); the Shuttle's own
  line 22 (row 18) is regenerated blanking and is only ever a stable-VBI check. The tape's line 22 is one line below the tape's line 21; it carries a specific level or
  sometimes faint picture (owner). Its level is a comparator by running count (ruling four), not a constant.
- **Picture row**: a recorded row that is not a VBI row. **Picture top**: the first picture row (owner: "the first
  picture row is the first picture row"). It may be hidden by the Shuttle's overwrite blanking: if the Shuttle's
  insert decodes captions on line 21, the real line 21 is somewhere between lines 20 and 22; a bottom band that does
  not extend to the end of the frame, or a mostly black head-switch area, is suspect that the top landed in the
  Shuttle's blanking; confirmed when new luma that is neither blanking nor darkened picture appears at line 23 —
  every band's luma shifting about one row down (owner, 04:29) — superseded by the owner's 06:11 ruling that new
  luma alone never means the picture moved: the hidden top is read from the account (definition of d: the band's
  extent against the count, blank rows under the band) and confirmed by the comb.
- **Head switch**: discontinuous horizontal skew, an RF peak, or both, plus an AGC mismatch where present (owner,
  2026-09-07 morning); the other head's blanking intruding into the row and the pedestal rows are what the captures
  show (section 2). **Switch line** (the top switch line): the horizontal line carrying the peak, the partial line;
  it keeps being the switch line when the peak moves into the other field or disappears off the edge, even if it
  then holds a fully stable line of picture (owner, afternoon). With the peak absent it is S, the first row entirely
  the other head, or the partial line above S where that row's later part departs; that one row is the travel.
  **Switch lines / the band**: the head-switch lines counted from the top switch line down, the partial line
  included (owner); the black rows the deck's TBC makes of them are band rows, not picture. Measured, TBC off against on on the same recorded fields
  (2026-09-07): with the deck's line TBC off the SP's field 1 shows 2 switch lines in 434 of 597 units and field 2
  shows 3 in 335 of 577, the band running to the clip in 576 of 577; with the TBC on, 1–2 switch lines remain and one
  (field 1) or two (field 2) of them have become flat black rows, so the TBC clears switch lines into black, one more
  in field 2; the peak shows in 31 of 597 and 5 of 577 units with the TBC off and in 1–2 of 606 with it on. The
  commercial tape shows 2 (field 1, 422 of 582) and 3 (field 2, 507 of 576) switch lines with no black under them.
- **Offset d** (signed; positive when the picture sits lower in the raster). When the picture top sits below line
  23, d = the bands above the picture (the recorded rows between line 23 and the picture's first line). When the
  top reads line 23 the picture may sit at or above it (a **clamped top**: its true first line in the Shuttle's
  regenerated rows): d = the switch-line count minus the band's extent (≤ 0), confirmed by the comb (rule 9).
  **Band's extent**: the rows from the top switch line to the clip, inclusive — the switch lines and whatever black
  or blank rows lie under them; counted per field. **Switch-line count**: the field's number of head-switch lines, a
  comparator by running count, measured per unit as the band's extent + d (the lines past the clip are the
  offset's). Worked with three lines: offset 0, picture 23–259, band 260–262 (3 + 0); offset +1, picture 24–260,
  band 261–262, one line past the clip (2 + 1); offset −1, picture from line 22 (overwritten), band 259–262 with a
  blank row at its bottom (4 − 1). **Height**: the rows from line 23 to the row before the switch line = (240 −
  switch lines) + d. (From the owner's 15:40 ruling "237 real picture lines + 3 head switch lines = 0 offset" and
  16:05: 237 is 240 minus the count, not a constant; "the count excludes the partial line (not 238)" refers to the
  picture lines, which end above the partial line.) **Bands above the picture**: the recorded rows between line 23
  and the picture top that are not the Shuttle's. **Bands below**: the band's extent. **Clip line**: the last row
  the deck delivers (262/525 on every capture seen), measured per source as the last recorded row's constant, never
  typed in.
- **Closure**: a field is 240 lines; top + 239 is the expected bottom; rows past the clip are lost (owner). The
  picture bottom placed by the engine is the row above the switch line; the expected bottom is the closure check.
- **S**: the first row belonging entirely to the other head (an engine measurement; the switch lies in S or the
  partial line above it). **Segment lag**: the horizontal lag, in samples, at which a short segment of a row best
  matches the row above (the segment's length is the engine's measurement aperture, not a decision constant). **Provenance error**: a capture whose packet accounting is not complete at a unit; the
  engine emits no record for it (fail closed).
- **Displacement**: the picture top against its standard line (23 / 286).
- **Comparator**: the value seen most often since the last reset, held in a fixed array of eight slots (owner: "8
  sounds fine"); equal counts do not change the ordering (owner); a ninth distinct value replaces the least-counted
  entry, and an evicted value that returns starts again at one (the fixed array's approximation of the running
  count). The comparators, per field: the switch-line count and the level of the tape's line 22 where it is
  visible (integers: rows, counts, the row's luma mean rounded to a unit).
- **Source lock**: exists only after at least one confirmation that the geometry is correct — combing, captions, or
  both (owner) — with the Shuttle's regenerated rows present (**stable VBI**: the timing pattern and the insert on
  lines 20/21 (283/284) present and line 22 (285) blank in the unit; the rewind passage carries them and stays
  unlocked for want of a confirmation, not of VBI). **Lock-like loss**: snow-like signal, a vertical tear (cross-program
  or true), a counter discontinuity, a signal-state relock or splice, the Shuttle's regenerated rows absent; a unit
  event, both fields.
- **Crop**: line 23 (286) is always the output's top line (owner); the crop takes the picture's first line to it, so
  its origin in the raster is 23 + d (286 + d) for every sign of d: the render's line 23 is the source's real line
  23 wherever it landed, and whatever the Shuttle put there is what is rendered — its blank at −1, its caption
  insert at −2, its timing line at −3 (owner, 16:20). A source whose own line 22 carries picture keeps its origin at
  23 and that line is dropped ("VBI never rendered").
  Extra black at the bottom is acceptable; rows past the clip read as legal black (owner, 2026-09-03); a letterboxed
  picture is centred; before a lock, standard placement. **Displacement sign**: positive is lower in the raster.
- **Comb**: the relative vertical shift between the two fields' crops that minimises the comb energy of their weave on
  static, detailed picture; measured first at standard placement, it confirms a lock when it reads zero at the placed
  crops; thereafter it stands, confirming or vetoing each move (a veto is reported, never acted on by either agent).
  Field precedence is the half-line order the zero reading fixes (which field's line sits between the other's). On a
  unit without static detail the comb reads nothing, the geometry is applied and the unit is marked unconfirmed.
- **Body shift**: the vertical shift of a field's picture body against the previous unit of the same field, over
  whatever range is required (never a fixed one); a maybe, not an authority.
- **Comparator order**: the first observed value leads; a replacement enters at the bottom; equal counts do not change
  the ordering.

## 4. Rules (the owner's, from section 1; the engine implements, the harness checks)

1. Geometry is the authority; every other signal confirms or contradicts and is recorded, never acted on alone.
2. The head switch's position moves with the picture; the source's switch-line count is fixed; the top switch line
   is the only variable one (the area of travel); the visible switch lines below it stay constant or decrease by the
   offset; a count change (visible + d against the comparator) for any other reason than the peak disappearing is
   reported loudly and the geometry is held — it is not a reset, since only
   snow-like signal or a vertical tear is a lost lock (owner, 04:29; both agents at extreme confidence, 2026-09-07
   15:50).
3. The line account is conserved; the picture bottom is the row above the switch line; lines past the clip are lost.
4. Locks are comparators by running count in fixed arrays; counts never decrement; the most frequent value is the
   comparator and is replaced by a value whose count passes it; no magic numbers, no per-source constants typed in.
5. A change of geometry — loss of source lock or a lock-like loss — resets everything immediately, both fields at
   once (there is no snow in one field only); without a stable VBI there is no lock and no geometry is claimed.
6. Damage that is not snow-like and not a vertical tear (cross-program or true) is continuing program: the previous
   geometry — the comparators and the lock — holds through it; the unit's own position is recorded Unknown, the crop
   is left where it was because nothing measurable says to move it (not a claim that the position held), and the
   position is re-measured when the edge returns. Horizontal tearing
   is not a geometry event. Snow-like signal or a vertical tear is a lost lock: everything resets, both fields at once.
7. Line 22 never renders. Rows past the clip render as legal black in the output (owner, 2026-09-03), whatever the
   raster carries there.
8. The output picture never moves except at a segment's initial lock and after a re-acquisition; field precedence
   (which field's line sits between the other's) is settled once per lock by the comb; boxed pictures are centred;
   black level is never assumed. Snow-like signal, splices and relocks are delivered by the signal-state layer; the
   engine reads the raster only.
9. Blank lines under the picture could indicate that the field sits high and need confirmation against the comb
   (owner); the band's extent alone never moves anything; new luma at the top alone never moves anything either. The
   offset is read every unit from the bands above the picture, or, with the top at line 23, from the band's extent
   against the switch-line count (definition of d); the settled comb confirms or vetoes it — it never proposes a
   move, and a veto is a true disagreement reported to the owner (section 8); most important is agreement (owner).
   Black rows under the band that the deck's TBC makes are constant for a field and sit inside the count; a change
   against it is the evidence, confirmed by the comb. After a displacement is applied the settled comb stands and
   must agree again at the moved crop. A field partly out of the raster is a displacement of that field, tracked and
   confirmed; a field with no picture at all in a unit is a hidden edge (rule 6), the other field continuing. Switch
   lines past the clip are counted by the account: the count is fixed for a field, so with the picture lower by d
   the band's extent is the count minus d. (Interpretations resolved from the owner's words by both agents at
   extreme confidence, 2026-09-07 15:50; the deciding quotes are in the harness report
   interpretation_resolution_a80c7e6.md.)
10. Not applicable (no head switch on the source) is distinct from unmeasurable.

## 5. Measured every unit, per field (what the record must carry)

The recorded region; the picture top with the VBI rows above it and their signatures; the caption line when
visible; the switch line and the signatures that carried it; the RF peak's line and position along the line when
present; the height and the band count; the comparators with their counts and the runner-up's counts; the lock
state and every hold or reset with its cause; the caption and the comb (the engine's own, for its lock) as
confirmations, the body shift if used. Provenance errors fail
closed.

## 6. The engine deliberately does not have

No zero re-anchoring, no learned numeric offsets, no evidence-voting hierarchy, no body-witness veto of a measurable
top, no comb correction of the crop (the settled comb confirms, it never moves a field), no position claimed through
damage (the geometry holds, the position is Unknown),
no top-reliability history, no windows, no thresholds that are not a stated measurement. Each was measured to fit fixture A rather than the raster.

## 7. (reserved)

## 8. Acceptance

Two independent instruments — the engine's record (Codex) and the harness's reference (Claude), independently
implemented and mutually reviewed, never fused — from the same raw rows and this contract, joined by device counter. Counted per capture per field: the top; S against the reference's first-full-other-head row
(exact where the reference exposes one) and against its earliest switch-band row (within the one-row partial
ambiguity); the band count under the lock; the comb on the engine's crops. A disagreement between the two instruments
about what a row IS (a measurement error in one of them) is decided on the raw rows by both agents and listed with
its rows; a true disagreement about the geometry (the comb not matching the placed crops) is not adjudicated by
either agent — it is reported to the owner as below. Invariants: on the
commercial tape from counter 6593, the top constant, the switch-line comparator constant, the switch line moving only
with the top within the partial line's one-row travel; on fixture A, output moves only at its two relocks (units 300/301 and 43,737/43,738) and at real boxing
changes, no placement on the snow units 43,686–43,736, field precedence constant within a lock. Every render (two
captures × two fields per frame, rows doubled, red = picture top and bottom, yellow = the band bottom) is read back
by machine on every frame — bar positions and decisive picture shifts — before anyone looks at it. The owner's
watch copy is the live path's output with its record burned in. No work product stands in one instrument alone.

Owner, verbatim (2026-09-07 15:15): "any true disagreement (such as comb not matching) should be reported loudly for
me to examine unit by unit in the test harness (Codex's job). please present a single frame rendered (and shifted)
bwdif image in that case." [The harness was Codex's at 15:15 and is Claude's since 20:10.] So every true disagreement — the engine's crop against the settled comb, the two
instruments against each other on a unit — is reported by the harness (Claude produces the report and the frames)
and handed to the owner, who examines them one by one: per unit, one rendered frame — the two fields' 240-row crops
as the engine placed them, woven into a 720×480 frame, deinterlaced with bwdif (one frame per unit, top field first),
labelled with the unit, its counter, both crop origins and the comb's reading. Neither agent adjudicates these.

## 9. Open

1. The V-stabilize-off pass's flagged first lines (120 units): held under the lock, or the top read through the
   flagging?
