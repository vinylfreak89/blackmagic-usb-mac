# Geometry-first registration engine — the contract

The single current contract for the registration engine and its validation harness, edited in place. Claude writes
the engine (`experiments/switch_geometry.py`), Codex the harness (`experiments/geometry_oracle/`, branch
`geometry-first-harness`); neither reads the other's code. Line numbers are NTSC lines; unit row r is line r+4.
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
visible picture lines + lines added above the picture + lines lost into the deck's blanking at the bottom = constant;
add X black lines at the top and the picture moved down X and is X shorter, remove X and it moved up X, and this holds
past the raster bounds — nothing deletes lines from the middle of a field except a vertical tear. No lock is claimed
without confirmation (comb agreement between the fields, or clean, significant luma at the measured edge); without
it the picture stays at standard placement (23/286) and the record says there was not enough to lock on. Body shift
0 and the account unchanged: the field did not move, the crop stays whatever any classifier says about the top row.
Both fields' bodies shifted together with no height change: picture content moved, ignore. The row directly above
the picture that sometimes carries data and sometimes a faint copy of the line below is decided by geometry, never
by classifying the row: if the bottom did not move the field did not move. Captions are confirmation; a caption may
place the very first unit of a segment; a caption that disagrees with measured geometry is logged, geometry wins.
Segment events (splice, signal loss, relock) come from the signal-state layer as explicit inputs; never inferred
from a body-half heuristic. A raster whose edges cannot be measured at all is Unknown, held and labelled, never a
substituted number. Tests are dumb and brute force: picture visible is the top, picture gone is the bottom; black is
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
> The head switch band should not move. The horizontal line carrying the peak either moving into the other field or
> disappearing off the edge should maintain that as the head switch line even if it has a fully stable line of picture.

> Blank lines at the bottom of the picture could be indicative that the entire picture is shifted up. Therefore, the
> SP capture should actually show the blanking caption and VBI lines by pulling the picture into the correct position.
> If lines come in from the overwritten blanking area, then that means the entire field might be shifted up during the
> "normal position of the tape" which explains why field 1 always gets a +1. In reality field 2 should probably be
> getting a continuous -1 if I had to guess.

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
  rows by the decoder's noise (section 2 gives the measured gaps). The exact test is the engine's to derive from those
  measurements and the harness's to check; it is not contract.
- **Pedestal**: the tape's black — the other head's black rows at the bottom of the band.
- **VBI row**: a recorded row carrying a vertical-interval signal, recognised by signature: the CEA-608 waveform
  (standard), the run-in burst without data (standard), the smeared XDS bar (measured on the EP recording), the
  tape's black line 22, the tape's grey line 22 (a flat row under half the brightness of the three rows below it,
  owner ruling 2026-09-05). The tape's line 22 is one line below the tape's line 21; it carries a specific level or
  sometimes faint picture (owner). Its level is a comparator by running count (ruling four), not a constant.
- **Picture row**: a recorded row that is not a VBI row. **Picture top**: the first picture row (owner: "the first
  picture row is the first picture row"). It may be hidden by the Shuttle's overwrite blanking: if the Shuttle's
  insert decodes captions on line 21, the real line 21 is somewhere between lines 20 and 22; a bottom band that does
  not extend to the end of the frame, or a mostly black head-switch area, is suspect that the top landed in the
  Shuttle's blanking; confirmed when new luma that is neither blanking nor darkened picture appears at line 23 —
  every band's luma shifting about one row down (owner; how to measure it is open).
- **Head switch**: discontinuous horizontal skew, an RF peak, or both, plus an AGC mismatch where present (owner,
  2026-09-07 morning); the other head's blanking intruding into the row and the pedestal rows are what the captures
  show (section 2). **Switch line**: the horizontal line carrying the peak, or where the tear crosses into the other
  field or falls off the edge (owner, afternoon). **Band**: the switch lines, counted from the top switch line
  including the partial line where the peak is (owner). Measured, TBC off against on on the same recorded fields
  (2026-09-07): with the deck's line TBC off the SP's field 1 shows 2 switch lines in 434 of 597 units and field 2
  shows 3 in 335 of 577, the band running to the clip in 576 of 577; with the TBC on, 1–2 switch lines remain and one
  (field 1) or two (field 2) of them have become flat black rows, so the TBC clears switch lines into black, one more
  in field 2; the peak shows in 31 of 597 and 5 of 577 units with the TBC off and in 1–2 of 606 with it on. The
  commercial tape shows 2 (field 1, 422 of 582) and 3 (field 2, 507 of 576) switch lines with no black under them.
- **Height**: the rows from the picture top to the switch line — fixed within a source (owner).
- **Closure**: a field is 240 lines; top + 239 is the expected bottom; rows past the clip are lost (owner).
- **Displacement**: the picture top against its standard line (23 / 286).
- **Comparator**: the value seen most often since the last reset, held in a fixed array of eight slots (owner: "8
  sounds fine"); equal counts do not change the ordering (owner).
- **Source lock**: exists only after at least one confirmation that the geometry is correct — combing, captions, or
  both (owner). **Lock-like loss**: a counter discontinuity, a signal-state relock or splice, a vertical tear, the
  Shuttle's regenerated rows absent.

## 4. Rules (the owner's, from section 1; the engine implements, the harness checks)

1. Geometry is the authority; every other signal confirms or contradicts and is recorded, never acted on alone.
2. The head switch's position moves with the picture; its height is fixed; the top switch line alone travels by
   one row; the switch lines below it stay constant or decrease; a height change for any other reason than the
   peak disappearing is reported.
3. The line account is conserved; the picture bottom is the row above the switch line; lines past the clip are lost.
4. Locks are comparators by running count in fixed arrays; counts never decrement; the most frequent value is the
   comparator and is replaced by a value whose count passes it; no magic numbers, no per-source constants typed in.
5. A change of geometry — loss of source lock or a lock-like loss — resets everything immediately; without a
   stable VBI there is no lock and no geometry is claimed (the rewind passage).
6. Dropout or RF noise that hides an edge keeps the previous decision and re-evaluates when it clears; horizontal
   tearing is not a geometry event; a vertical tear is a lost lock.
7. Line 22 never renders.
8. The output picture never moves except at a segment's initial lock and after a re-acquisition; field precedence
   is settled once per lock; boxed pictures are centred; black level is never assumed.
9. Blank lines under the picture are evidence that the field sits high; the band count alone never moves anything.
10. Not applicable (no head switch on the source) is distinct from unmeasurable.

## 5. Measured every unit, per field (what the record must carry)

The recorded region; the picture top with the VBI rows above it and their signatures; the caption line when
visible; the switch line and the signatures that carried it; the RF peak's line and position along the line when
present; the height and the band count; the comparators with their counts and the runner-up's counts; the lock
state and every hold or reset with its cause; the body shift and comb as confirmations. Provenance errors fail
closed.

## 6. The engine deliberately does not have

No zero re-anchoring, no learned numeric offsets, no evidence-voting hierarchy, no body-witness veto of a measurable
top, no persistent comb correction, no saved-geometry hold on absent evidence, no top-reliability history, no
windows, no thresholds that are not a stated measurement. Each was measured to fit fixture A rather than the raster.

## 7. (reserved)

## 8. Acceptance

Two blind instruments, the engine's record and Codex's reference, from the same raw rows and this contract, joined
by device counter. Counted per capture per field: the top; S against the reference's first-full-other-head row
(exact where the reference exposes one) and against its earliest switch-band row (within the one-row partial
ambiguity); the band count under the lock; the comb on the engine's crops. Every disagreement is decided on the raw
rows by both agents and listed with its rows; an interpretation question goes to the owner. Invariants: on the
commercial tape from counter 6593, the top constant, the band comparator constant, the switch line moving only with
the top; on fixture A, output moves only at its two relocks (units 300/301 and 43,737/43,738) and at real boxing
changes, no placement on the snow units 43,686–43,736, field precedence constant within a lock. Every render (two
captures × two fields per frame, rows doubled, red = picture top and bottom, yellow = the band bottom) is read back
by machine on every frame — bar positions and decisive picture shifts — before anyone looks at it. The owner's
watch copy is the live path's output with its record burned in. No work product stands in one instrument alone.

## 9. Open

1. The lock criterion: is one observation after a reset a lock (the comparator exists), or must the Shuttle's
   regenerated rows be stable over more than one unit first?
2. A height change with the peak present: reported only, or also a reset?
3. The shift gauge of rule 10: field 2's band one row longer on every tape.
4. The V-stabilize-off pass's flagged first lines (120 units): held under the lock, or the top read through the
   flagging?
5. S one row early where the partial line carries part of the other head's blanking (a partial line's left part
   still aligns with the row above; a full other-head row's does not): a definitional refinement to apply.
