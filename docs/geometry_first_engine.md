# Geometry-first registration engine — the contract

The single current contract for the registration engine and its validation harness, edited in place. Claude writes
the engine (`experiments/switch_geometry.py`), Codex the harness (`experiments/geometry_oracle/`, branch
`geometry-first-harness`); neither reads the other's code. Line numbers are NTSC lines; unit row r is line r+4 (rows past line 525 are the
Shuttle's, named by the same mapping).
Every number is a standard (NTSC, SMPTE RP-202, CEA-608), a measurement on the captures (stated with its value), a
memory capacity, a measurement aperture named as such, a test point inside a measured gap (stated with the gap), or
a fitted default labelled as such; any other number in the code is a defect. "Variation" and "spread" are the
standard deviation of a row's samples 40–680.

## 1. The owner's rules, verbatim

**Intent (2026-09-04/06).** Geometry is the authority. Each field's active picture area — its top edge, bottom edge
and height — measured on every unit places the crop. Everything else (the tape's line 21, its black line 22, static
comb, any temporal witness) exists only to confirm that reading where geometry alone cannot decide: (1) the
head-switch region makes the bottom edge noisy and field-to-field inconsistent; (2) geometry does not say which
field's lines interleave on top — field precedence is settled once per lock and held; (3) boxed pictures have their
own geometry, centred in the raster, and black level is not assumed constant. Tracking breaks only on a vertically
torn raster or a lost lock — both are one class: old geometry invalid, back to zero, re-acquire when the lock
returns. Horizontal tearing is not a geometry event. Dropout or RF noise that hides an edge keeps the previous
decision and re-evaluates when it clears. The tape's line 22 never renders. The output picture never moves except at a
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
render the partial line as picture, and then the band's row count (the switch-line count) is what survives. The head switch is optional (not
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
> dynamic memory allocation (in the real C engine). [And:] Why are you ever decrementing counts. [And, on the
> array's size:] Number I will leave up to you. 8 sounds fine. Equal counts do not change ordering.

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
> letterboxing and such the picture should be centered). [Read with 16:20: the tape's VBI never renders; the
> Shuttle's regenerated rows stand in at negative d.] If the full picture starts at 23 and goes say to 235 only
> and then head switch from 236–238 then full geometry is 237 lines, not 238 lines, not 240.


## 2. What the captures show (measured)

| unit rows | NTSC lines | content | origin |
|---|---|---|---|
| 0–6, 261–269, 523–524 | 4–10, 265–273, 527–528 | padding, Y 16.0 / C 128.0 exactly | Shuttle |
| 7–15, 270–278 | 11–19, 274–282 | blanking, Y 1.4 ± 0.5 | Shuttle |
| 16, 279 | 20, 283 | timing pulse pattern, std 40–54 when present | Shuttle, when its decoder has sync |
| 17, 280 | 21, 284 | CEA-608 insert: the tape's bytes when its line 21 lies within one line of the standard line (measured 2026-09-05), else nulls | Shuttle, when its decoder has sync |
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
  picture top to the row before the switch line are the same in both passes (237 at units 20, 105, 200).
- The commercial tape's picture is stable from counter 6593 onward (before it the tape is rewinding); its pedestal
  measures 9–11, the same as fixture A's 11.4 (both tapes have setup); its head switch sits on line 260 or 261 in
  every measurable unit, and with the peak present the rows from the top to the row before the switch row are 238 in 31 of 36
  field-1 units and 237 in 48 of 59 field-2 units.
- Field 2's band is one row longer than field 1's on the SP, EP and commercial tapes (SP, TBC off: field 1 two rows
  in 427 of 606 units, field 2 three or four rows in 597 of 608).

## 3. Definitions

- **Recorded row**: a pass-through row that came through the analog decoder, told from the Shuttle's regenerated
  rows by the decoder's noise: chroma noise above twice the blanking rows' (the measured gap of section 2, regenerated
  ≤ 1.48×, recorded ≥ 2.02×, the test point inside the measured gap at 2.0), or luma above the blanking rows' level by
  more than twice their noise (0.5, section 2; the same factor, an aperture); padding is neither. A raster whose
  edges cannot be measured at all is Unknown (held, labelled); edges measured but inconsistent are the loud reports
  of rules 2 and 9 (held, reported) — two labels, one action. **Apertures used by
  the tests**: "present" for the Shuttle's timing pattern and insert is the row's variation above 20, an aperture
  inside the measured gap (40–54 present, 0.5 absent, section 2); "blank" is the blanking level (1.4) within the blanking rows' noise; "flat" is a
  row's variation within that noise for a regenerated or TBC-made row, and within twice the field's own noise
  (defined under the comb) for a recorded row — the tape's line 22 on the SP recording reads luma 3–5 with a
  within-row spread of 3–4 in 434 of 608 units, uncorrelated with the picture row below (0.02), measured
  2026-09-07; the line-22 level match uses the same twice-the-noise window; "static" pixels are unchanged against the previous unit within the field's own
  noise (defined under the comb), "detailed" ones differ from the row below by more than it; a "dark scene" is dark
  rows (not above the pedestal by more than the blanking rows' noise) under a dark row.
- **Pedestal**: the tape's black — the other head's black rows at the bottom of the band; measured per unit as the
  level of the flat rows above the blanking level contiguous with the clip, carried from the last unit that had
  them (on a source without setup, or before any unit had them, it is the blanking level; a lock-like loss
  empties it with everything else). At d = 0 the tape's
  line 22 is behind the Shuttle's, so the level comparator is fed only where the caption is raw.
- **VBI row**: a recorded row carrying a vertical-interval signal, recognised by signature: the CEA-608 waveform
  (standard), the run-in burst without data (standard: the clock-frequency amplitude over three cycles at the
  decoder's gate, 35, a test point inside the measured gap — captions 52–60, chance picture hits 15–22 — with the
  row flat beyond it), the tape's
  line-20 timing pattern (correlation at least 0.8 with the Shuttle's regenerated line 20, an aperture), the smeared
  XDS bar (the one per-source signature: its envelope measured on the EP recording, the test frozen 2026-09-04 as
  fitted defaults, labelled:
  48-bin luma profile, row mean under 95, bins 20–47 at most 40, a run of at least six bins over 60 within bins
  0–19; the tape's line 284, so it places field 2 as a caption places field 1 — d = its row − 284 — and confirms its
  lock the same way: it is that field's caption line), the tape's line
  22 by
  position (the row below a raw parity-valid caption line or below the XDS bar — never the Shuttle's insert: one
  line below its line 21, whatever it carries),
  the tape's black line 22 (a
  flat row at the level its line 21 has placed before: the level comparator is fed only by the row below a decoded
  caption or below the XDS bar), the tape's grey line 22 (a flat row under half the brightness of the three rows
  below it, owner ruling 2026-09-05, those rows being picture — above the pedestal by more than the blanking rows'
  noise; read on the run of dark flat rows at the top, at most three — the tape's lines 20–22 — against the three
  picture rows under the run, so the tape's blank line 21 and black line 22 without caption service are both VBI;
  a dark row over dark rows is a dark scene: on the commercial tape lines 23–25 read 4.0/5.8/12.4 through one
  177-unit scene and line 23 tracks line 24 across units with correlation 1.00, measured 2026-09-07). The
  signatures are read on the rows above the picture only, from line 23 down; the picture top is the first row
  they do not claim; a bottom letterbox bar never meets them. Per unit the order is: recorded rows, the
  signatures and the top, the body rows below the top, S from the bottom up, the clip reading, then the account.
  "Line 22" in this document is the TAPE's line 22 wherever it lands in the raster (line 23 at +1); the Shuttle's own
  line 22 (row 18) is regenerated blanking and is only ever a stable-VBI check. The tape's line 22 is one line below the tape's line 21; it carries a specific level or
  sometimes faint picture (owner). Its level is a comparator by running count (owner: "derived and stabilized"), not a constant.
- **Picture row**: a recorded row that is not a VBI row by signature. **Picture top**: the first picture row (owner:
  "the first picture row is the first picture row"), read by signature every unit (the **signature top**). Two rows
  the signatures cannot settle are settled by the account (the model: "decided by geometry, never by classifying the
  row"): the row directly above the picture, which sometimes carries data and sometimes a faint copy of the line
  below — if the switch line did not move, the field did not move, and the top stays at the switch line minus the
  picture lines (rule 9) in either direction — the row reading as picture then not, or not then picture — while the
  signature reading is recorded (with a caption placing the field that row is its line 22 by position and never
  picture); and a top hidden in the Shuttle's regenerated rows (the signature top reads 23 while the
  account says the picture sits higher; the insert carries the tape's bytes when its line 21 lies within one line
  of 21, measured 2026-09-05, so decoded bytes on the insert say only that) — the top is 23 + d from the account,
  confirmed by the comb (rule 9).
- **The account**: the comparison, per field per unit, of the two edge readings (signature top, switch-line reading)
  with the geometry's expectation and the segment's constants (rule 9); its reading is d, its crop 23 + d. A
  **segment** runs from the capture's first unit or a lock-like loss to the next lock-like loss; its seed is the
  first unit with both edges readable (on a source without a head switch, rule 10, the top alone, its H := clip −
  (23 + d) + 1 and c := 0) and the regenerated rows present; H, c and d are per field; after Unknown or
  held units the expectation is the last applied decision. The rules name fields by origin — the 23-field and the 286-field;
  the capture's pairing input (the harness's per-capture measurement, section 2) says which transport slots of
  which units form a frame (on the V-stabilize-off capture, slot 2 of a unit with slot 1 of the next: a frame woven
  from two units), and the record names each field by its slot; the rules' line numbers are the origin's (a
  286-field in slot 1 is still the 286-field). The switch-line reading that seeds H is the reading as defined (the
  partial line where it departs, else S); a seed unit read the other way seeds H one off for the segment, which the
  comb reports. Every line number in the rules has its field-2 analogue (23 → 286, 22 →
  285, 21 → 284, 20 → 283, the clip 262 → 525). The output weaves each field at its own crop,
  one locked and one at standard placement included. A seed
  whose H is high by one (the row above read as picture on the first unit) has no correction without a raw caption
  (at |d| = 1 the caption is overwritten, the insert's bytes confirm either d, the comb cannot see a shared offset):
  it stands until a caption or a lock-like loss, and a segment whose units mostly read the row above the picture
  against its seed is a seed suspect the harness reports (section 7). A shared −1 (both tops hidden, the caption
  inside the Shuttle's window) is unresolvable by any instrument named here and stays at the seed's reading,
  reported the same way.
- **Head switch**: discontinuous horizontal skew, an RF peak, or both, plus an AGC mismatch where present (owner,
  2026-09-07 morning); the other head's blanking intruding into the row and the pedestal rows are what the captures
  show (section 2). **Switch line** (the top switch line): the horizontal line carrying the peak, the partial line;
  it keeps being the switch line when the peak moves into the other field or disappears off the edge, even if it
  then holds a fully stable line of picture (owner, afternoon) — the account keeps that identity (the switch line
  sits H rows below the picture top); the per-unit **reading** of it, with the peak absent, is S, the first row
  entirely the other head, or the partial line above S where that row's later part departs (its segment lags in the
  right part of the row exceed the body's maxima while its left part aligns); a reading one row from the identity
  is the travel. The RF peak per unit: a narrow spike on a flat background above the field's own narrow specks (the
  body's maximum). "Not applicable" (rule 10) per unit: no switch signature and the picture contiguous with the
  clip.
  **Switch lines / the band**: the head-switch lines counted from the top switch line down, the partial line
  included (owner); the black rows the deck's TBC makes of them are band rows, not picture. Measured, TBC off against on on the same recorded fields
  (2026-09-07, one census; section 2's row is another over the same passes): with the deck's line TBC off the SP's
  field 1 shows 2 switch lines in 434 of 597 units and field 2 shows 3 in 335 of 577, the band running to the clip in 576 of 577; with the TBC on, 1–2 switch lines remain and one
  (field 1) or two (field 2) of them have become flat black rows, so the TBC clears switch lines into black, one more
  in field 2; the peak shows in 31 of 597 and 5 of 577 units with the TBC off and in 1–2 of 606 with it on. The
  commercial tape shows 2 (field 1, 422 of 582) and 3 (field 2, 507 of 576) switch lines with no black under them.
- **The source's constants** (owner, 15:40: "237 real picture lines + 3 head switch lines = 0 offset"; "the height
  counts should be both head switching and non head switching"). **Picture lines** H: the rows from the picture's
  first line to the row before the switch line (the reliable geometry); a constant of the segment (owner: "its
  height should be fixed"), seeded on the seed unit and re-seeded only by a raw caption (rule 9) or a comb-confirmed
  hidden-top move (the seed's correction: H := switch line − (23 + d) with the confirmed d) — never learned by count: a row above the picture reading as picture or as VBI never moves it (the model: "if the bands
  below did not change, the field did not move"), nor does the switch-line reading's travel (the owner: the peak
  disappearing "should maintain that as the head switch line"). On flat content, where the comb reads nothing, a
  hidden-top move stays held and recorded until the comb can read. **Switch-line count** c: the head-switch lines from
  the top switch line down, the partial line included (owner: the switch lines below the top switch line "stay
  constant or decrease", the top one "the only variable one" — its reading travels by a row); the flat rows the deck's TBC makes of them sit at
  the pedestal (9–11 on both tapes, section 2) and are switch lines; rows at the blanking level (1.4) under the band
  are not. A constant of the segment (rule 2: "the source's switch-line count is fixed"), seeded on the first unit
  as the visible switch lines plus the lines lost past the clip (top + 239 − clip when positive); each unit's
  reading (the same sum) is checked against it — the owner: the visible ones "stay constant or decrease"; fewer is
  the peak gone or the TBC's clearing, recorded; one more is the travel; more than that is reported loudly (rule
  2). c moves nothing. H
  is the owner's "full geometry" ("237 lines, not 238, not 240" — the quote's line numbers do not add up; read as the
  picture lines: the partial line is a
  switch line, not a picture line; the blank rows under the band are neither); the deck delivers 240 lines (23–262) per field,
  which H, c and the blank rows under the band fill (at d > 0 with the lines lost past the clip); on a source without
  setup the pedestal is the blanking level and c reads the timed rows only. Letterbox bars are recorded rows at the pedestal: a top bar is
  picture (inside H); a bottom bar contiguous with the band reads as band rows; the crop (240 rows from 23 + d) is
  unaffected either way. **Band's extent**: the rows from the top switch line to the clip, inclusive — the visible switch lines and the
  blank rows under them; per field. **Blank rows under the band**: the rows at the blanking level between the
  band's last switch line and the clip once the clip comparator leads — on the seed, to the Shuttle's padding (exact
  Y16/C128 rows, section 2), so the near-blank remainder of lines 263–264 then counts and its candidates are put
  to the comb, which rejects them; they arise from a field sitting high (its band's lines above the clip leave the
  tape's rows after the band visible) or from a source whose band ends above the clip; the comb tells which where the offset is not shared by both
  fields. **Bands above the picture**: the rows from line 23 up to, not including, the
  picture's first line, whatever they carry (the Shuttle's own rows end at 22): d = top − 23 when the top is
  visible; none when it is hidden (d then from V − H). **Bands below**: the band's extent. **Clip line**: the
  last row the deck delivers (262/525 on every capture seen), measured per source as a comparator of the last row
  whose luma passes the recorded-row test (chroma noise alone reaches 263–264, section 2) less the offset where the
  field sits high (at d −1 that row is 261; at d ≥ 0 the raster's clip bounds the field and the reading is raw),
  never typed in; the comparator is the clip, not the unit's reading. For a source whose band ends above the deck's
  clip it reads the band's end, and the closure then counts the blank rows as lost — a record entry, no crop effect.
- **Offset d** (signed; positive when the picture sits lower in the raster). At offset d the whole stack — H picture
  lines, c switch lines, blank rows — sits d lines lower; rows above line 23 are hidden by the Shuttle's regenerated
  rows, rows past the clip are lost (owner). Read per unit: with the signature top below 23, d = the bands above the
  picture; with the signature top at 23, the visible picture lines V = switch line − 23 = H + d, so d = V − H,
  confirmed by the comb (rule 9). (V + the band's extent is the rows from 23 to the clip in every unit; the information is the
  observations V and extent against the constants H and c.) Worked with H 237, c 3, clip 262: d 0 — picture 23–259, switch lines 260–262, nothing under;
  d +1 — picture 24–260, switch lines 261–262, one switch line lost past the clip (the visible count fell by d, rule
  2; c 3 is the owner's example, field 1 of the SP measures 2, section 2); d −1 — the picture's first line at 22, overwritten, picture 23–258 visible (V 236), switch lines 259–261, row
  262 at the blanking level (not a switch line). **Seed**: on the seed unit (the segment's first unit with both edges readable and the regenerated rows present;
  units before it are Unknown, at standard placement, feeding nothing) the comparators are empty; d is read from
  that unit alone — the caption's d when the unit carries one, else the bands above the picture, else 0
  with the signature top at 23 (owner, 15:40: "0 offset (basis assumption of geometry requiring confirmation)") — and
  H := switch line − (23 + d), c := the visible switch lines plus the lines lost past the clip; with the top at 23 and
  blank rows under the band, the
  hidden-top candidates d = −1 down to −(those rows) are put to the comb, which may confirm one — zero at the candidate, not at
  the held crop (rule 9; owner, 15:40); no lock until a confirmation
  (the record and rule 9
  use the account's crop from the seed on; the output stays at standard placement until the lock, then moves to it).
  A seed with the top hidden seeds H low by |d|; one with the row above the picture read as picture
  seeds H high by one; the comb corrects the first (the hidden-top candidates), a raw caption the second (rule 9);
  nothing else does — the seed is the geometry until a caption or a lock-like loss. On the seed unit the clip is
  the unit's own reading (the last row above blanking) until the comparator has a leader. The level and clip
  comparators are fed from the seed on, lock or not; a lock-like loss empties everything.
- **Closure**: a field is 240 lines; the lines past the clip — top + 239 − clip when positive — are lost (owner) and
  recorded. **Picture bottom**: the row above the switch line (the model's "picture gone is the bottom": the reliable
  geometry ends there; the band lies between it and the blanking the owner named as the lower bound).
- **S**: the first row belonging entirely to the other head — read from the bottom of the field upward as the top
  of the run of rows whose horizontal alignment to the row above (segment lag), row difference, missing horizontal
  blanking dip (the blank run at the row's start where the horizontal blanking interval ends, which every picture
  row carries), intruded blanking run, or flatness at the pedestal exceeds the maxima of the field's own body rows
  (the rows 20 to 200 below the picture top, an aperture; the field's own variance, never a typed level); the
  switch lies in S or the partial line above it. **Segment lag**: the horizontal lag, in samples, at which a short
  segment of a row best matches the row above (55-sample segments, lags −24 to +24: apertures). **Provenance error**: a capture whose
  packet accounting (the capture reader's, an input) is not complete at a unit; the engine emits no record from it
  on to the end of the capture (fail closed).
- **Displacement**: d.
- **Comparator**: the value seen most often since the last reset, held in a fixed array of eight slots (owner: "8
  sounds fine"); equal counts do not change the ordering (owner); a ninth distinct value takes the slot of the
  least-counted entry — the owner's "fixed number": a value that falls out of the eight drops out and the array
  shifts (the owner's "fixed number" is the array's size, "falls below" is falling out of it: "why are you ever
  decrementing counts"; among equal least counts the last slot goes); the evicted entry is forgotten, no live count ever decrements, and a returning value is a
  new entry. When another value's count passes the leader's it becomes the comparator (owner), reported. The
  comparators, per field: the level of the tape's line 22 where its line 21 has placed it (the line-22 signature's
  reference) and the clip line (integers: rows, the row's luma mean rounded to a unit). Neither moves the crop.
- **Source lock**: claimed only after at least one confirmation that the geometry is correct — combing, captions, or
  both (owner) — with the Shuttle's regenerated rows present (**stable VBI**, the owner's term: the timing pattern
  and the insert on lines 20/21 (283/284) present — their variation above 20, an aperture inside the measured gap 0.5 to 40 —
  and line 22 (285) blank in the unit — a lock slip of the Shuttle's decoder puts the insert one line low; the
  rewind passage carries
  the rows and no confirmation, so it has no lock). A lock confirmed by the comb alone is a lock at
  the account's reading — the comb cannot see an offset both fields share; a caption is the only absolute
  confirmation — and the record names which confirmed it. Decoded non-null bytes on the Shuttle's insert with no raw caption
  anywhere in the field confirm the account's d when |d| ≤ 1 (the tape's line 21 is then inside the Shuttle's
  window and overwritten; measured 2026-09-05) — a windowed confirmation, the owner's "captions" read to include the
  Shuttle's decode, labelled a choice; at |d| ≥ 2 the raw caption is the confirmation. The lock is per
  field: a caption
  confirms its field, a decisive comb zero confirms both fields' relative placement; each field's output leaves standard
  placement at its own lock. **Lock-like loss**: snow-like signal, a vertical tear (cross-program or true), a signal-state
  relock or splice (the owner's list), and a counter discontinuity (the capture's own epoch rule, not the owner's);
  a unit event, both fields. A unit failing the stable-VBI check (a decoder lock slip) is a hold (rule 6). The Shuttle's regenerated rows absent
  (its decoder without sync: a mute, a dropout) is a signal-state fact and a hold (rule 6), never a gauge and not by
  itself a loss.
- **Crop**: line 23 (286) is always the output's top line (owner); the crop takes the picture's first line to it, so
  its origin in the raster is 23 + d (286 + d) for every sign of d: the render's line 23 is the source's real line
  23 wherever it landed, and whatever the Shuttle put there is what is rendered — its blank at −1, its caption
  insert at −2, its timing line at −3 (owner, 16:20). A source whose own line 22 carries picture keeps its origin at
  23 and that line is dropped ("VBI never rendered").
  Extra black at the bottom is acceptable; rows past the clip read as legal black (owner, 2026-09-03); a boxed
  picture's bars are picture rows at the pedestal, inside H, so the crop keeps the box as broadcast (owner:
  "centred"); before a lock, standard placement. **Displacement sign**: positive is lower in the raster.
- **Comb**: the relative vertical shift between the two fields' crops that minimises the comb energy of their weave on
  static, detailed picture (pixels unchanged against the previous unit within the field's own noise — the median
  over the picture body, lines 63–222 / 326–485, of the standard deviation of adjacent-sample differences over √2
  (one sample's noise from a difference of two) — with vertical detail above it; the comb energy is the mean absolute second difference along the weave after an
  8-sample horizontal low-pass; shifts −3 to +3, an aperture covering every displacement measured; apertures), measured at the account's crops at the capture's field precedence (an input from the
  capture's pairing measurement, not a constant); a reading is decisive when the best shift's energy is at most
  0.8 of the runner-up's — a fitted default, labelled: fitted on fixture A against caption truth, where a decisive
  reading is wrong in about 1 unit in 500; a decisive zero confirms the relative placement (a
  lock of both fields, source lock); "agrees" is a decisive zero, "disagrees" a decisive nonzero, "reads nothing"
  an undecisive reading. The **settled comb**
  is that zero reading, re-measured at the account's crops every unit; before a lock there is none, and the cases of
  rule 9 that consult it apply under a lock only — the seed's hidden-top candidates and the lock's own confirmation
  use the comb's reading at the account's and candidate crops. The comb is measured at the account's crops
  (23 + d per field, lock or not; the output before a lock is at standard placement) and, per field with a hidden-top
  or row-above reading, at that one candidate crop. The comb never proposes a crop and moves no field: it decides
  only between the account's own readings — the account's decision (a move or a still unit) stands whether the comb
  reads zero, nothing, or disagrees (a decisive disagreement is reported, section 7); a hidden-top reading is a
  candidate, not a decision, applied only when the comb reads zero at the candidate (a move shared by both fields reads zero at both placements and stays held, recorded, until a caption
  places the field: the caption is the only absolute confirmation); a held row-above reading becomes a move when
  the comb disagrees at the held crop and agrees at the moved one (the owner's exception; H is unchanged and the
  switch-line reading, now one row from its identity, is the travel until it follows — for good, if H was seeded
  one high, until a caption); a move the account applied
  is not undone when the comb disagrees — geometry is the authority (rule 1) and the disagreement is reported to
  the owner (section 7). **Field precedence** (which field's line sits between the other's): the transport order,
  the 23-field's line above the 286-field's, always (by origin); what is measured per capture is the pairing —
  which slots of which units form a frame — by the same-field temporal match between the slots (section 2, MAD:
  the V-stabilize-off capture pairs slot 2 of a unit with slot 1 of the next; measured 2026-09-07: with the 286
  slot woven on top the comb read a correct interleave on that pass as a one-line shift and held a field one line
  high in 379 units), applied at each lock. A reading of +s means the 286-field's crop sits s rows high of the
  interleave (or the 23-field's s rows low); never
  inferred from the comb, which cannot tell a swapped precedence from a one-line displacement. On a unit without
  static detail the comb reads nothing, the geometry is applied (to the account; the output follows only under a
  lock) and the unit is marked unconfirmed. A source whose line 22 carries picture and shows no caption seeds H one
  high at +1 and reads as still; the comb's decisive disagreement at the account's crops is then reported every
  unit, no lock is claimed, and the output stays at standard placement (the tape's line 22 rendered, since nothing
  identifies it) until a caption or a lock-like loss — the honest outcome, for the owner's examination.
- **Body shift**: the vertical shift of a field's picture body against the previous unit of the same field, over
  whatever range is required (never a fixed one); a maybe (owner), not used by the engine.

## 4. Rules (the owner's, from section 1; the engine implements, the harness checks)

1. Geometry is the authority; every other signal confirms or contradicts and is recorded, never acted on alone (a
   caption placing a segment's first unit confirms the seed measured on that unit — the model).
2. The head switch's position moves with the picture; the source's switch-line count is fixed; the top switch line
   is the only variable one (the area of travel); the visible switch lines below it stay constant or decrease by the
   offset; per unit, a one-row change of the switch line alone is the travel (the partial line, the peak's drift)
   and is recorded; a change of the switch-line reading of more than one row against the top's move, or a count
   beyond c + 1, is reported loudly (the top's own readings are rule 9's: the rows above the picture, the field's
   move) and the geometry is held — unless the comb confirms it as a
   hidden-top move (rule 9's pinned-top case; owner: "needs to be confirmed against the comb"), then it is reported
   loudly and applied. None of these readings is a "change of geometry" in the owner's sense (rule 5): only
   a lock-like loss (definition: snow-like signal, a vertical tear, a counter discontinuity, a relock or splice from
   the signal-state layer) is a lost lock (owner, section 1, on damage; both agents at extreme confidence,
   2026-09-07 15:50).
3. The line account is conserved; the picture bottom (picture gone) is the row above the switch line; lines past the
   clip are lost.
4. H and c are the segment's constants from the seed (owner: fixed); the level of the tape's line 22 and the clip
   are comparators by running count in fixed arrays (the owner's ruling on the level); counts never decrement; the most frequent value is the
   comparator and is replaced by a value whose count passes it; no magic numbers, no per-source constants typed in.
5. A change of geometry — a lock-like loss (the owner's "loss of source lock or lock like loss") — resets everything immediately, both fields at
   once (there is no snow in one field only; a single field with no picture is not snow — rule 6); without a stable
   VBI (the Shuttle's regenerated rows) no new lock is claimed and no geometry is read — the unit's position is
   Unknown (rule 6); an existing lock holds through their absence.
6. Damage that is not snow-like and not a vertical tear (cross-program or true) is continuing program: the previous
   geometry — the comparators and the lock — holds through it; the unit's own position is recorded Unknown, the crop
   is left where it was because nothing measurable says to move it (not a claim that the position held), and the
   position is re-measured when the edge returns. Horizontal tearing
   is not a geometry event. Snow-like signal or a vertical tear is a lost lock: everything resets, both fields at once.
7. The tape's line 22 never renders, wherever it lands (it is identified by its line 21 or its signatures; a row
   nothing identifies is picture; a row the account holds as picture under rule 9's row-above case renders, its
   signature recorded — the model: "decided by geometry, never by classifying the row"). Rows past the clip render as legal black in the output
   (owner, 2026-09-03), whatever the raster carries there. At negative d the raster rows the Shuttle regenerated
   stand in for the hidden lines (owner, 16:20; definition of the crop).
8. The output picture — the picture's content on the render; the crop origin 23 + d moves with every applied d so
   that the content does not — never moves except at a segment's initial lock, after a re-acquisition, and at the
   corrections of the initial lock's seed (rule 9: a caption re-seed, a comb-confirmed hidden-top move, the
   row-above exception — each reported loudly whenever it happens) — and returns to standard placement at a
   lock-like loss (rule 5); this list is the one list — a rule-9 move keeps the content still by construction and
   is not on it; field precedence (which field's line
   sits between the other's) is settled once per lock from the capture's pairing (definition of the comb) and held;
   boxed pictures are kept as broadcast; black level is never assumed. Snow-like signal, vertical tears (an
   appearance class of that layer), splices and relocks are delivered by the signal-state layer and packet accounting
   by the capture reader; the engine reads the raster only.
9. The account decides, per field per unit, from the field's edges — the signature top and the switch-line reading
   (never the picture's content: a content movement seen in both fields moves neither edge, the model) — against
   the geometry's expectation — the previous decision (never a recorded, unapplied reading): top 23 + d, switch line
   23 + d + H — and the comparators; "moved" is each edge's reading minus its expectation (Δtop, Δswitch), so travel
   never accumulates. The cases are tested in this order; the first that fits decides (the owner's rules of
   section 1):
   - Δtop = Δswitch = 0: still; nothing applied; the comb's reading at the crop recorded (a decisive disagreement is
     a true disagreement, section 7);
   - Δtop = Δswitch ≠ 0: the field moved (rule 2, the switch line follows the picture); d changes by that amount; the
     settled comb must agree at the moved crop — a disagreement is reported as a true disagreement (section 7), the
     move stands (rule 1);
   - the signature top at 23 with the expectation at 23 or hidden above it (23 + d ≤ 23; the top pinned: it cannot show a move above 23,
     so Δtop is censored — an upper bound on the top's move when the expectation is 23, no reading at all when the
     top is already hidden) and Δswitch < Δtop (or, with the top hidden, Δswitch ≠ 0; Δswitch = 0 there is still):
     the switch line's move is the field's candidate — d would change by Δswitch (definition of d: d = V − H) —
     applied — up, or with the top hidden in either direction — only when the comb reads zero at that placement
     and not at the held one
     (definition of the comb; owner: blank lines under the picture "could be indicative … needs to be confirmed
     against the comb"), then reported loudly (rule 2); the band's extent alone never moves anything; unconfirmed,
     the geometry is held and the reading recorded as travel when it is one row, reported loudly when more (rule
     2);
   - Δswitch = 0, Δtop ≠ 0: the row above the picture — the field did not move (the model); the top stays at
     switch line − H; unless the settled comb disagrees at the held crop and agrees at the moved one (owner: "unless
     the line shift down of new luma causes a comb disagreement on the settled comb"), then it moved;
   - Δtop ≠ 0, Δswitch ≠ 0 and Δswitch = Δtop ± 1: the field moved by Δtop (the top is the reliable edge, the band the
     unreliable one — owner) with one row of the reading's travel, recorded;
   - Δtop = 0, Δswitch = ±1: travel, recorded (rule 2; a one-row upward reading with the top at 23 reaches this
     through the hidden-top case unconfirmed); |Δswitch| > 1: reported loudly, held;
   - no switch-line reading with the expected switch row reading as picture, or expected past the clip: the band
     has left the raster past the clip (or the source has none — rule 10, whose bottom is the clip and c is 0, and
     whose only edge is the top);
     Δtop > 0: the field moved by Δtop (the reliable edge), the lost lines recorded (closure), the comb agreeing
     where it can read; Δtop = 0: still; Δtop < 0 with a band gone from a source that has one: reported loudly,
     held (a band cannot vanish upward); on a source without a head switch the top's move is the field's in either
     direction (a bottom letterbox bar there reads as its band; the crop is unaffected);
   - anything else (different amounts): reported loudly, held (rule 2).
   A caption reads d = its row − 21 (284), compared with the account's d after the unit's case: on the seed, and
   before any lock, it places the unit (re-seeding the geometry from it); under a lock confirmed by the insert's bytes or the comb alone (both windowed or relative) a raw
   caption is the absolute reading and re-seeds the geometry once — the segment's first raw caption (d, H, c from
   that unit; reported, rule 8), the lock becoming caption-confirmed so that later caption jitter is logged — that
   re-seed is where the tape's line 22 is identified as the row below the caption (owner, 16:20: real picture there
   "should get dropped") and the picture as starting on the next row; under a caption-confirmed lock (which keeps that
   status when the caption stops) it confirms when it equals the account's d, and any disagreement is logged and
   reported (section 7) — geometry wins (the
   model; the caption line itself moves for a single unit on fixture A, measured: 2,023 one-unit flips); without a
   caption the rows' identity is their signatures'. Two fields whose edges both move are both
   displaced (the model's "content" is the picture's body, which moves no edge). New luma at the top alone never
   moves anything (owner); most important is agreement (owner). A field partly out
   of the raster is a displacement of that field, tracked and confirmed; a field with no picture at all in a unit has
   shifted out of the raster or dropped out (owner, morning) and nothing places it: a hidden edge (rule 6), the other
   field continuing. Switch lines past the clip are the account's: with the picture lower by d the visible count is
   c − d once the blank rows under the band are used up.
10. Not applicable (no head switch on the source) is distinct from unmeasurable.

## 5. Measured every unit, per field (what the record must carry)

The recorded region; the picture top with the VBI rows above it and their signatures; the caption line when
visible; the switch line and the signatures that carried it; the RF peak's line and position along the line when
present; the picture lines and the visible switch lines; the comparators with their counts and the runner-up's counts; the lock
state and every hold or reset with its cause; the caption and the comb (the engine's own, for its lock) as
confirmations. Provenance errors fail closed.

## 6. The engine deliberately does not have

No zero re-anchoring, no learned numeric offsets, no evidence-voting hierarchy, no body-witness veto of a measurable
top, no comb correction of the crop (the comb decides only between the account's own readings, definition of the
comb), no position claimed through damage (the geometry holds, the position is Unknown),
no top-reliability history, no windows, no thresholds that are not a stated measurement or a labelled fitted default. Each was measured to fit fixture A rather than the raster.

## 7. Acceptance

Seed suspects (segments whose units mostly read the row above the picture against their seed) are listed with
their counts. Two blind instruments, the engine's record and Codex's reference, from the same raw rows and this contract, joined
by device counter. Counted per capture per field: the top; S against the reference's first-full-other-head row
(exact where the reference exposes one) and against its earliest switch-band row (within the one-row partial
ambiguity); the picture lines and switch lines against the segment's constants; the comb on the engine's crops. A disagreement between the two instruments
about what a row IS (a measurement error in one of them) is decided on the raw rows by both agents and listed with
its rows; a true disagreement about the geometry (the comb not matching the placed crops) is not adjudicated by
either agent — it is reported to the owner as below. Invariants: on the
commercial tape from counter 6593, the top constant, the switch-line count constant, the switch line moving only
with the top within the partial line's one-row travel; on fixture A, the rendered picture moves only at its two relocks
(units 300/301 and 43,737/43,738: the play-start mute as a signal-state relock, and the owner's program split) and at the moves rule 8 allows (each reported; a boxing change is content the
read-back sees as a move), no placement on the snow units 43,686–43,736, field precedence
constant within a lock. Every render (two
captures × two fields per frame, rows doubled, red = picture top and bottom, yellow = the band bottom) is read back
by machine on every frame — bar positions and decisive picture shifts — before anyone looks at it. The owner's
watch copy is the live path's output with its record burned in. No work product stands in one instrument alone.

Owner, verbatim (2026-09-07 15:15): "any true disagreement (such as comb not matching) should be reported loudly for
me to examine unit by unit in the test harness (Codex's job). please present a single frame rendered (and shifted)
bwdif image in that case." So every true disagreement — the engine's crop against the settled comb, the two
instruments against each other on a unit — is reported by the harness (Codex produces the report and the frames)
and handed to the owner, who examines them one by one: per unit, one rendered frame — the two fields' 240-row crops
as the engine placed them, woven into a 720×480 frame, deinterlaced with bwdif (one frame per unit, top field first),
labelled with the unit, its counter, both crop origins and the comb's reading. Neither agent adjudicates these.

## 8. Open

1. The V-stabilize-off pass's flagged first lines (120 units): the top is read through the flagging — a flagged row
   is a recorded picture row and horizontal tearing is not a geometry event (rule 6); the harness counts those units.
