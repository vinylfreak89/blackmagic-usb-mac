# Geometry-first registration engine — the contract

This is the single current contract for the registration engine and its validation harness. It is edited in
place; there are no versions or addenda. Claude writes the engine (`experiments/switch_geometry.py`), Codex writes
the harness (`experiments/geometry_oracle/` on branch `geometry-first-harness`); neither reads the other's code.
Every number below is either a standard (NTSC, SMPTE RP-202, CEA-608), a measurement on the Shuttle's raster, or a
memory capacity; a number that is none of those is a defect. Line numbers are NTSC lines; "unit row r" is line r+4.

## 1. What the Shuttle delivers (measured)

| unit rows | NTSC lines | content | origin |
|---|---|---|---|
| 0–6, 261–269, 523–524 | 4–10, 265–273, 527–528 | padding, Y 16.0 / C 128.0 exactly | Shuttle |
| 7–15, 270–278 | 11–19, 274–282 | blanking, Y 1.4 ± 0.5 | Shuttle |
| 16, 279 | 20, 283 | timing pulse pattern | Shuttle, when its decoder has sync |
| 17, 280 | 21, 284 | null CEA-608 insert (re-encodes what it decodes at the standard line) | Shuttle, when its decoder has sync |
| 18, 281 | 22, 285 | blanking, Y 1.4 | Shuttle |
| 19–260, 282–522 | 23–264, 286–526 | pass-through: the source | tape and deck |

- Nothing the tape carries above line 23 (286) reaches us. The tape's own VBI becomes visible only when the field
  is displaced downward: at +1 its black line 22 appears on line 23 (Y 4–7 on a tape with setup); at +2 its line 21
  appears on 23; at +3 its line 20 on 23 and its line 21 on 24.
- The deck clips each field at line 262 / 525 on every capture seen; rows past the clip are lost.
- "Field 1" and "field 2" name transport slots. The Shuttle may group the same field sequence one field later on
  another capture of the same tape (the V-stabilize-off pass pairs the SP's field 2 of unit u−1 with its field 1 of
  u), so every per-field quantity is measured per capture on the slot's own content.
- The deck's line TBC (V-stabilize) drops torn rows at the top of a field and shifts the rest down by that count;
  with it off the picture starts on its standard line, the first one or two lines carry a horizontal timing error
  that varies along the row (flagging), and the head switch's RF peak and timing step are visible. The rows from the
  picture top to the switch line are the same in both passes (237 at the verified units).
- The commercial tape's picture is stable from counter 6593 onward (the passage before it is rewind); its pedestal
  measures 9–11 (it has setup), and its head switch sits on line 260 or 261 in every measurable unit.

## 2. Definitions

- **Recorded row**: a pass-through row that carries the analog decoder's noise, in chroma (above twice the blank
  rows' chroma noise) or in luma (above the blank level by six times the blank rows' luma noise); padding is neither.
- **Blank noise** σ_b: the luma noise of the unit's own blanking rows (lines 11–19 / 274–282), floor 0.5.
- **Pedestal**: the tape's black — the flat run of recorded rows contiguous with the clip (the other head's black at
  the bottom of the band); the blank stands in when the band has no flat row.
- **Sub-black**: a row whose mean lies below the pedestal by more than three blank noises.
- **VBI row**: a recorded row that carries a vertical-interval signal, recognised by signature only: a CEA-608
  waveform (run-in by correlation at 1.986 µs cells, start bits, odd parity per byte); a run-in burst without data;
  the smeared XDS bar (a pulse and a ~50 IRE bar over the left third of the line, flat after it); the tape's black
  line 22 (sub-black, flat, lone, before the picture — see the first-row comparator); the dim flat gap line under
  half the brightness of the three rows below it (the tape's grey line 22).
- **Picture row**: a recorded row that is not a VBI row.
- **Picture top**: the first picture row that begins a run of three picture rows, within the first four recorded rows
  (the tape's VBI can occupy at most lines 20–22 of the pass-through region). If no such run exists the top is
  unmeasurable for that unit (a black top, a torn strip, snow).
- **Head switch**: the physical event of the drum changing heads, seen in the raster as one or more of: a
  discontinuous horizontal skew or timing step; the other head's horizontal blanking intruding into the row (at its
  start, or in mid-row: luma at the blank level for longer than a sync pulse, 4.7 µs = 64 samples, and shorter than a
  blanking interval could be, 200 samples); the row's own horizontal-blanking dip missing; an RF peak (a narrow
  transient on an otherwise aligned row, carrying the tear with it, whose position along the line drifts slowly);
  an AGC level step; the other head's flat black (pedestal) rows.
- **Band**: the rows from the top switch line to the clip. **Top switch line**: the first row that shows a switch
  signature; the switch point may lie inside it (a partial line, its left part still the picture). **S**: the first
  row belonging entirely to the other head — the top of the run of band rows that is contiguous with the clip; the
  switch lies in S or S−1.
- **Reliable geometry**: the rows from the picture top to the row before the switch line.
- **Closure**: a field has 240 lines (23–262 / 286–525); the picture bottom is the row above the switch line, and
  rows past the clip are lost, never present.
- **Displacement d**: the picture top minus its standard line (23 / 286).
- **Comparator**: the value of a per-field quantity seen most often so far within the current source (section 4).

## 3. Measured every unit, per field, from the unit's own rows

1. The recorded region: its first and last rows.
2. The picture top, with the VBI rows above it and their signatures.
3. The head switch: S, the signatures that carried each band row, the RF peak's line and its position along the
   line when present, the position along the line where the other head's blanking or the timing step begins in the
   rows around S.
4. The counts: reliable rows (top to S−1), band rows (S to the clip).
5. Confirmations, never actuators: the tape's caption line when a parity-valid waveform sits off the insert; the
   static comb between the two fields (the harness measures it); the picture body's shift against the previous unit
   of the same field.

## 4. Rules

1. **Geometry is the authority.** The picture top and the head switch, measured per unit, place the crop.
   Captions, comb, the body shift and every other signal only confirm or contradict a reading; a contradiction is
   recorded, never acted on by itself.
2. **The head switch's position moves with the picture; its height is the constant.** The rows from the picture top
   to the switch line are the same in every unit of a source. The top switch line alone travels by one row, as the
   switch point moves along the line and off its edge or as the TBC smooths the peak away; when the peak or the
   timing garbage vanishes, that line is still the switch line. The band's row count below the top switch line is
   constant, or decreases when the picture drops and rows fall off the clip; it never increases. Per unit: a band
   count equal to the comparator, or one less, is the travel; a larger count means the switch was read on a picture
   row (an error, reported as `band+`); a smaller count with the top still means the picture dropped under a clamped
   top (`dropped`, displacement evidence); a smaller count with the top moved down by the same rows is the field
   falling out of the raster (`fell-out`). A height change with the peak present is an event and is reported.
3. **Locks are comparators by running count, in fixed memory.** Each comparator is an array of eight (value, count)
   slots kept in count order. A hit increments its entry and bubbles it up; a new value takes a free slot, or with
   the array full replaces the least-counted entry. Counts never decrement. The comparator is the first slot; it is
   replaced by any value whose count passes it. No window, no threshold, no per-source constant typed in. Two
   comparators per field: the band count, and the state of the first recorded row (`black22` when it is sub-black
   and flat, else `picture`). Each unit's record carries every comparator's count and the runner-up's count.
4. **A change of geometry resets everything immediately.** The loss of the source lock, or a lock-like loss — the
   Shuttle's regenerated rows absent (its decoder without sync), a counter discontinuity, a signal-state relock, a
   vertical tear — clears every comparator of the field at once; the counts restart from the next unit. No geometry
   is claimed without a lock (the commercial tape's rewind passage is `no-lock`, not coordinates).
5. **A hidden edge holds.** A unit whose top cannot be measured (torn strip, dropout, RF noise, a flat raster) keeps
   the previous decision and the comparators, and is re-evaluated when the edge returns.
6. **Line 22 never renders.** A lone sub-black flat row before the picture is the tape's black line 22 where the
   first-row comparator says the source shows one (the SP recording, displaced by the TBC); where the comparator
   says picture (the commercial tape, whose first picture lines are crushed black), it is picture. A sub-black band
   is picture.
7. **The output picture does not move.** The crop follows each field's measured top so the stabilized picture stays
   still; it moves only at a segment's initial lock and after a re-acquisition.
8. **Blank rows under the picture are a shift gauge.** With the switch height held, the band count per field is the
   vertical position gauge of that field; a band longer than the source's comparator (field 2's band is one row
   longer than field 1's on all three tapes) is to be decided on the rows: a field sitting one line high (the tape's
   line 286 fallen into the Shuttle's overwritten 285) or the raster's own half-line geometry. Open (section 7).

## 5. The per-unit record

Per field: unit, counter, top, S, the signature that carried S and each band row, the RF peak's position, the
position along the line of the timing discontinuity at S−1/S/S+1, reliable and band counts, last recorded row,
pedestal, blank level and noise, lock state (`acquiring` / `locked` / `hold` / `no-lock`), the switch line under the
lock (top + 240 − band comparator), the band comparator with its counts, the observed band count and its class
(`travel` / `band+` / `dropped` / `fell-out` / `hidden` / `reset`), the first-row comparator with its counts.

## 6. Acceptance

Two blind instruments: the engine's record and Codex's reference, built from the same raw rows and the same
contract, joined by device counter. Agreement is counted per capture per field on the top, on S against the
reference's first-full-other-head row, on the band count under the lock, and on the comb; every disagreement is
decided on the raw rows and listed. The commercial tape's stable passage is the invariant test: the top constant,
the band comparator constant, the switch line moving only with the top. Every render is read back by machine on
every frame (bar positions, decisive picture shifts) before anyone looks at it. No work product stands in one
instrument alone.

## 7. Open measurements

- The shift gauge of rule 8: field 2's band one row longer than field 1's on the SP, EP and commercial tapes.
- The V-stabilize-off pass's flagged first lines (120 units): under the lock they hold; whether the top should be
  read through the flagging.
- S one row early where the partial line carries part of the other head's blanking (a partial line's left part
  still aligns with the row above; a full other-head row's does not).
- The reference's `first_full_other_head_line` exposed in few SP units: the SP's band rows carry their intruding
  run at the pedestal, not at the blank.
