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
lines from the middle of a field except a vertical tear. The line account decides: content moving while the bands above and below the picture are unchanged is not a
displacement, and the bands changing in both fields by the same amount is a displacement of both fields, each
closing its own account (owner, 2026-09-07 15:11: "my original definition of geometry, ie, the number of top bands vs
bottom bands shifting is the correct answer"); new lines of luma appearing at the top alone never mean the picture moved, unless that shift causes a
comb disagreement on the settled comb. No lock is claimed without at least one confirmation that the geometry is
correct — combing, captions, or both; without it the picture stays at standard placement (23/286) and the record
says there was not enough to lock on. The row directly above the picture that sometimes carries data and sometimes
a faint copy of the line below is decided by geometry, never by classifying the row: if the bands below did not
change, the field did not move. Captions are confirmation; a caption may confirm the very first unit of a segment when it
agrees with geometry; a caption that disagrees with measured geometry is logged, geometry wins. Segment events (splice, signal loss, relock)
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
cues present one frame and absent the next mean they shifted away, near-certain when the top shifts too (owner, 03:34:41).

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

> [2026-09-07 20:56, asked whether the 12:52 comparator ruling applied to the switch-line count:] no. the comparator
> was at line 22. you extended it to the head switch (wrongly) on your own

> [2026-09-09, after the live-path audit found placements of +30 and +101 lines on muted rasters:] okay obviously
> you need to completely turn off registration in anything other than normal picture and that should solve most of
> the detection issues. detecting the vertical tear should be equally obvious. in a vertical tear, horizontal timing
> goes completely out the window. any field with horizontal timing that skews mid frame and then becomes stable
> again is a vertical tear by nature. this would cover signal, VBI, etc coming back into the picture.

> [2026-09-07 21:34, on what confirms a first lock:] combing captions or both. significant clean picture was a
> fuck up on my part. because of the shuttle's own raster hiding potentially the first few lines. and "captions"
> that sit on the raster's line 21 have to be assumed they could be from 20, 21, or 22 LOL, so only if it agrees
> with the comb on one of those 3, but comb should be retested in that case

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

- **The delivered window is narrower than the line but wider than the active picture, and that is what makes
  horizontal timing readable at all** (standards, with the measurement that follows). An NTSC line is 858 samples at
  13.5 MHz and the device delivers 720 (BT.601 / SMPTE 259M); the analogue horizontal blanking interval is 10.9 µs =
  147 samples (SMPTE 170M). Since 147 > 858 − 720 = 138, a correctly timed line ALWAYS shows about 9 samples of
  blanking inside the window, split between its two ends and nowhere else. Displace the line's timing and that
  blanking moves with it: one end loses its blanking, the other gains it, and at full displacement the whole
  147-sample interval sits inside the window. So locating a row's blanking IS measuring its timing, with no reference
  to what the picture is doing — which is why an "active edge" (where content begins) is not a timing edge, and why
  horizontal and vertical geometry are one problem rather than two. Measured on the commercial capture (2026-09-09,
  independent instrument): the head-switch band's rows are displaced about 160 samples, the whole blanking interval
  inside the window; reading the bottom this way puts it on one row in 496 of 526 measured field-1 units (99.4%
  within one row) and 443 of 504 field-2 units, flags no picture row, and refuses the rewind (337 of 338 units before
  counter 6593 unmeasurable).
- **Black picture content in this source is clipped to exactly the blanking level, with the same dither** (mean 1.40
  against 1.39, standard deviation 0.49 against 0.49, measured inside content runs and band runs). No level test and
  no texture test can separate content from blanking here; only geometry can.
- **A field's horizontal timing is not uniform down the field**, so its variance is measured over a local window of
  rows, never whole-field: the top rows of each field (lines 23–34) carry end levels of median 4.6–6.6 and p95 52–63
  above blanking against median 0.6 and p95 7.6 just above the head switch — the flagging of a VHS field's first
  lines. Judged whole-field, those top rows hide the band.
- Nothing the tape carries above line 23 (286) reaches us except the re-encoded bytes on the insert. The tape's own
  VBI becomes visible only when the field is displaced downward: at +1 its black line 22 appears on line 23 (luma
  4–7 on fixture A), at +2 its line 21 on 23, at +3 its line 20 on 23 and its line 21 on 24.
- The Shuttle re-encodes the insert from a caption it slices within one line of the standard line: measured on
  fixture A, 91 units of the first 13,000 carry decoded caption bytes at line 21 with no parity-valid raw caption
  anywhere in the field and a rigid +1 picture (top and bottom together, 24/261 against a 23/260 lock), while in
  1,300+ units whose raw caption sits at 23 or 24 (+2, +3) the insert carried nulls every time (CLAUDE.md §11). So
  the window reaches ±1 and not ±2; the −1 side (the tape's line 21 on raster line 20) is its symmetric case, not
  separately measured.
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
  ≤ 1.48×, recorded ≥ 2.02×, the test at its lower bound), or luma above the blank; padding is neither. The Shuttle's regenerated blanking rows (7–15 / 270–278) are the
  reference when present; tape signal cannot reach them; their absence is a lock-like-loss observation.
- **Pedestal**: the tape's black — the other head's black rows at the bottom of the band.
- **VBI row**: a recorded row carrying a vertical-interval WAVEFORM, recognised by signature: the CEA-608 waveform
  (standard), the run-in burst without data (standard), the tape's line-20 timing pattern (the same pattern as the
  Shuttle's regenerated line 20), the smeared XDS bar (measured on the EP recording). "Line 22" in this document is
  the TAPE's line 22 wherever it lands in the raster (line 23 at +1); the Shuttle's own line 22 (row 18) is regenerated
  blanking and only ever a regenerated-row-presence check. The tape's line 22 is one line below the tape's line 21; it
  carries a specific level or sometimes faint picture (owner, 13:29). The tape's black line 22 is located by the line
  account as the row below the located line 21; its running level comparator (the owner's 12:52 mechanism) confirms
  that identity but never establishes the row by itself. When no line 21 is located, the band-above rows are what
  the account requires — count − extent — and the level comparator confirms which of them is line 22; a first-row
  reading that the account does not require never moves anything. The row directly above the picture that carries data or a
  faint copy is decided by the account (the bands below), never by classifying the row (owner, 2026-09-06). The former
  "grey line 22 under half the brightness of the three rows below" rule was a typed brightness test (Claude's round-3
  audit finding, CLAUDE.md §11, not an owner ruling) and is dropped: the comparator supersedes it.
- **Picture row**: a recorded row that is not a VBI row. **Picture top**: the first picture row (owner: "the first
  picture row is the first picture row"). It may be hidden by the Shuttle's overwrite blanking: if the Shuttle's
  insert decodes captions on line 21, the real line 21 is somewhere between lines 20 and 22; a bottom band that does
  not extend to the end of the frame, or a mostly black head-switch area, is suspect that the top landed in the
  Shuttle's blanking (owner, 13:29); the hidden top is read from the account (definition of d: the band's extent
  against the count, blank rows under the band) and confirmed by the comb — new luma alone never means the picture
  moved (owner, 15:11).
- **Per source, never fixed** (owner, 2026-09-09: "this should always be derived per source. ABSOLUTELY not a fixed
  thing and the reason should be obvious. horizontal timing and levels will be a PER RECORDING thing. any vertical
  tear or signal loss like completely invalidates this registration and it will need to be rebuilt"). The field's
  horizontal-timing variance (its source-derived horizontal-phase distribution — NOT the spread of its rows'
  active edges, which is where content begins and moves with brightness; falsified on the commercial capture,
  2026-09-09) and its level references (the blanking level and
  noise, the pedestal, the tape's line-22 level) are measured from the source itself and belong to the current lock.
  No sample position and no luma level is ever typed in or carried from another recording; the numbers quoted in
  section 2 are measurements on these captures, never test points. A lock-like loss (rule 5b) discards them with the
  lock, and they are rebuilt from the units after re-acquisition — nothing derived under the old lock survives it.
- **Vertical tear**: a field whose horizontal timing departs mid-field and then becomes stable again (owner,
  2026-09-09: "in a vertical tear, horizontal timing goes completely out the window. any field with horizontal
  timing that skews mid frame and then becomes stable again is a vertical tear by nature. this would cover signal,
  VBI, etc coming back into the picture"). It is read from the same per-row horizontal-phase profile as the head
  switch and is told apart by WHERE the departure ends: the head-switch band's departure begins near the bottom and
  persists to the clip, while a tear's departure returns to the field's own stable phase and picture continues below
  it. A vertical tear is a lock-like loss (rule 5b). **The bare definition is not sufficient and carries three
  qualifiers, each measured** (2026-09-09, independent instrument on fixture A's opening 416 units): applied
  literally it fires 1,038 times, so a departure is a tear only when it (a) returns to the field's stable timing,
  (b) is at least three rows long, and (c) has stable readable rows above it — without (c) the field's first lines,
  which carry VHS flagging up to 231 samples over 4–6 rows, "return" trivially because the whole field lies below
  them, and that class alone is 23 of 27 candidates in settled programme; rule 5's normal-picture gate removes the
  rest, which are snow during relock. With the three, the signature fires once in 198 settled units and it is the
  splice. Two limits stated with it: the displacement is known only modulo one line (a late shift and an early one
  differing by a whole line are the same arrangement of samples), and a dark picture edge of a few tens of samples
  cannot be separated from a displacement of the same size when the row's other end shows nothing either.
- **The head-switch band's horizontal displacement is a per-source property, and on a TBC'd source it is absent.**
  Measured 2026-09-09 on the last 14 lines of all 396 settled fields of fixture A's opening (the deck's line TBC on):
  |displacement| median 1–2 samples, p95 ≤ 5, and ZERO rows at ≥ 20, against 23 such rows in the same fields' middles.
  The deck clips its picture and leaves flat rows at luma ≈ 12 with no transition at all, whose timing is
  unreadable — the TBC has re-timed the band away. On the commercial capture the same instrument measures band rows
  displaced about 160 samples. So the band is found by displacement on one source and by unreadable flatness on
  another, which is why the reference is per source and why "not applicable" is distinct from "unmeasurable".
- **Head switch**: discontinuous horizontal skew, an RF peak, or both, plus an AGC mismatch where present (owner,
  2026-09-07 morning); the other head's blanking intruding into the row and the pedestal rows are what the captures
  show (section 2). **Switch line** (the top switch line): the horizontal line carrying the peak, the partial line;
  it keeps being the switch line when the peak moves into the other field or disappears off the edge, even if it
  then holds a fully stable line of picture (owner, afternoon). With the peak absent it is the first measurable
  horizontal-skew discontinuity scanning down from the picture: the partial row whose later part departs from the
  row above, else S when the first full other-head row is exposed; that one row is the travel. If neither is
  measurable, the unit's switch line is Unknown and the lock's count is not substituted as an observation. How each
  instrument measures the discontinuity is its own, stated per column (harness) and per golden (engine).
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
  or blank rows lie under them; counted per field. **Switch-line count**: the field's number of head-switch lines, taken
  at the confirmed unit and kept for the lock (never re-learned; owner, 20:56), measured per unit as the band's
  extent + d (the lines past the clip are the offset's); a unit whose measurement differs from the lock's count is
  reported (rule 2). Worked with three lines: offset 0, picture 23–259, band 260–262 (3 + 0); offset +1, picture 24–260,
  band 261–262, one line past the clip (2 + 1); offset −1, picture from line 22 (overwritten), band 259–262 with a
  blank row at its bottom (4 − 1). **Picture rows** = 240 − switch-line count, the
  source's constant under the lock (237 when the lock's confirmed switch-line count is 3; owner 15:22 "237 real picture line + 3
  head switch lines = 0 offset", and 16:03 "I agree with that interpretation" to "237 is 240 minus the source's
  switch-line count"). **Span** from line 23 to the row before the switch line = picture rows + d = 240 − the band's
  extent. Per unit the two readings of d — the bands above the picture, and count − extent — must agree ("most
  important is agreement"). The owner's "say to 235" figures are illustrative; the ruling is the count, the partial
  line counted as a switch line ("not 238"). **Bands above the picture**: the recorded rows between line 23
  and the picture top that are not the Shuttle's. **Bands below**: the band's extent. **Clip line**: the last row
  the deck delivers (262/525 on every capture seen), measured per source as the last recorded row's constant, never
  typed in. It is not the picture bottom, which is the row above the switch line (rule 3).
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
  count; an engineering choice the owner left to the agents, 13:29: "Number I will leave up to you. 8 sounds fine.
  Equal counts do not change ordering."). The comparator, per field: the level of the tape's line 22 where it is
  visible (an integer, the row's luma mean rounded to a unit). The switch-line count is not a comparator (owner,
  20:56).
- **Source lock**: exists only after at least one confirmation that the geometry is correct — combing, captions, or
  both, and nothing else (owner, 13:29 and 21:34: "combing captions or both. significant clean picture was a fuck
  up on my part. because of the shuttle's own raster hiding potentially the first few lines" — his earlier
  "significant non-dirty luma" is withdrawn, because the Shuttle's blanking can hide the picture's first lines) — at a
  unit whose switch line and band are measurable, so that the lock's count is taken there and never substituted; a
  unit that confirms only the top does not make a lock. A caption confirms the very first unit of a segment when it
  agrees with the geometry (the lock's confirmation); it never places a unit against measurable geometry (owner,
  2026-09-04 21:26: "assuming the picture itself ALSO MOVES THE SAME AMOUNT"). **A caption on the insert** (bytes
  decoded on the raster's line 21 / 284) does not say where the tape's line 21 was: the Shuttle slices within one
  line (section 2), so the tape's row could be 20, 21 or 22 — d ∈ {−1, 0, +1}. It confirms only when the comb,
  re-measured for that unit at the three candidate placements, agrees with exactly one of them (owner, 21:34: "so
  only if it agrees with the comb on one of those 3, but comb should be retested in that case"); otherwise it
  confirms nothing. A caption whose row lies in the pass-through region (line 23 or below) is the tape's own line 21
  and gives d = its line − 21 directly. **Regenerated-row presence** (the
  Shuttle's timing pattern and insert on lines 20/21 and 283/284, line 22/285 blank) is required decoder evidence,
  not a lock: the rewind passage carries the regenerated rows (measured) and has no source-lock confirmation, so it
  stays unlocked — the owner's 12:39 "no stable VBI = no stable lock" as this document states it. **Lock-like loss**:
  snow-like signal, a vertical tear (cross-program or true), a signal-state relock or splice, the Shuttle's regenerated
  rows absent; a unit event, both fields. A transport hole or short unit (a counter discontinuity) is damage under
  rule 6, not a lock-like loss.
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
  At an acquisition whose only caption is on the insert the comb is re-measured for that unit at each of the three
  candidate placements (owner, 21:34) and confirms only if exactly one of them weaves without a relative shift. The
  comb constrains the two fields' relative registration only, so where both fields are ambiguous by the same amount
  it cannot decide and there is no lock.
- **Body shift**: the vertical shift of a field's picture body against the previous unit of the same field, over
  whatever range is required (never a fixed one); a maybe, not an authority.
- **Comparator order**: the first observed value leads; a replacement enters at the bottom; equal counts do not change
  the ordering.

## 4. Rules (the owner's, from section 1; the engine implements, the harness checks)

1. Geometry is the authority; every other signal confirms or contradicts and is recorded, never acted on alone.
2. The head switch's position moves with the picture; the source's switch-line count is fixed; the top switch line
   is the only variable one (the area of travel); the visible switch lines below it stay constant or decrease by the
   offset; a count change (visible + d against the lock's count) for any other reason than the peak disappearing is
   reported loudly; the lock's count is kept (not re-learned) and the position goes on being read from the bands
   above the picture where the top is visible; where the top is hidden and the account cannot close, the unit's
   position is Unknown (rule 6) — it is not a reset, since only snow-like signal or a vertical tear is a lost lock
   (owner, 04:29, and 15:11 "previous geometry (not position) holds through the damage"; both agents at extreme
   confidence, 2026-09-07 15:50 and 21:12).
3. The line account is conserved; the picture bottom is the row above the switch line; lines past the clip are lost.
4. The lock's constant, the switch-line count, is taken at the confirmed unit and kept until a reset, never
   re-learned; a unit that disagrees with it is reported (rule 2). The level of the tape's line 22 is a comparator by
   running count in a fixed array of eight slots; counts never decrement; the most frequent value is the comparator
   and is replaced by a value whose count passes it (owner, 12:52, 12:55, 20:56). No magic numbers, no per-source
   constants typed in.
5. **Registration runs only on normal picture.** Where the signal-state layer does not report program, the engine
   measures nothing and places nothing: no displacement is computed, none is applied, the crop stays where it was,
   and the record says why (owner, 2026-09-09: "you need to completely turn off registration in anything other than
   normal picture"). Mute, snow, no-signal, device-no-signal and unframed rasters are not inputs to geometry.
5b. A loss of source lock or a lock-like loss (the owner's "change of geometry", 2026-09-07 afternoon) resets
   everything immediately, both fields at once (there is no snow in one field only); an ordinary measured
   displacement is tracking, not a change of geometry; a transport hole or short unit is damage (rule 6), not a
   loss; without regenerated-row presence and a confirmation there is no lock and no geometry is claimed.
6. Damage that is not snow-like and not a vertical tear (cross-program or true) is continuing program: the previous
   geometry — the lock's switch-line count, the line-22 level comparator and the lock — holds through it; the unit's own position is recorded Unknown, the crop
   is left where it was because nothing measurable says to move it (not a claim that the position held), and the
   position is re-measured when the edge returns. Horizontal tearing
   is not a geometry event. Snow-like signal or a vertical tear is a lost lock: everything resets, both fields at once.
   **A unit carrying a horizontal timing error other than its own head switch may not be the confirmed unit**: it
   holds, and the lock's constants are taken from a clean unit (owner, 2026-09-09: "other horizontal timing error
   should result in a hold rather than a lock"). Holding through such damage is the rule above; this is its other
   half, that damage may not seed the geometry either.
7. The tape's line 22 never renders: a source whose own line 22 carries picture keeps its origin at 23 and that line
   is dropped; at a negative offset the render's first line is whatever the Shuttle put at 23 + d — its blank at −1,
   its caption insert at −2 (owner, 16:16–16:18: "if the shuttle overwrote it, tough noogies"). Rows past the clip
   render as legal black in the output (owner, 2026-09-03), whatever the raster carries there.
8. The output picture never moves except at a segment's initial lock and after a re-acquisition; field precedence
   (which field's line sits between the other's) is settled once per lock by the comb; a boxed picture's bars are recorded picture rows inside the 240 and change nothing in the account, and the box is
   rendered where the account puts it, centred as the source centred it (owner, 2026-09-05: "letterboxing or any
   weirdboxing creates its own geometry and that can EASILY be centered in the raster"; no acceptance capture carries
   a boxed picture, so the class is not exercised);
   black level is never assumed. Snow-like signal, splices and relocks are delivered by the signal-state layer; the
   engine reads the raster only.
9. Blank lines under the picture could indicate that the field sits high and need confirmation against the comb
   (owner); the band's extent alone never moves anything; new luma at the top alone never moves anything either. The
   offset is read every unit from the bands above the picture, or, with the top at line 23, from the band's extent
   against the switch-line count (definition of d); the settled comb confirms or vetoes it — it never proposes a
   move; the geometry's reading is applied either way, and a veto is a true disagreement recorded and reported to
   the owner (section 8), never a silent hold or a change of the crop; most important is agreement (owner).
   Black rows under the band that the deck's TBC makes are band rows (they define no bottom, rule 3), constant for a
   field and inside the count; a change against it is the evidence, confirmed by the comb. After a displacement is applied the settled comb stands and
   must agree again at the moved crop. A field partly out of the raster is a displacement of that field, tracked and
   confirmed; a field with no measurable picture while the other field's picture continues is a hidden edge (rule
   6; measured on fixture A at 24:17, one field black); snow-like signal is a unit event of the signal-state layer,
   both fields (owner, 15:11: "why would there be snow in one field but not the other"). Switch
   lines past the clip are counted by the account: the count is fixed for a field, so with the picture lower by d
   the band's extent is the count minus d. (The line-account interpretations here were resolved by both agents at 15:50 —
   interpretation_resolution_a80c7e6.md, whose running-comparator reading of the switch-line count is overruled by
   the owner's 20:56 ruling — and re-settled on the current text at 21:12 and 21:21.)
10. Not applicable (no head switch on the source) is distinct from unmeasurable.

## 5. Measured every unit, per field (what the record must carry)

The recorded region; the picture top with the VBI rows above it and their signatures; the caption line when
visible; the switch line and the signatures that carried it; the RF peak's line and position along the line when
present; the span, the picture rows and the band count; the lock's switch-line count; the line-22 level comparator with its
counts and the runner-up's; the lock
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
either agent — it is reported to the owner as below. "Output" below means the stabilized visible picture the owner watches, not the crop-origin metadata. Invariants: on
the commercial tape from counter 6593, the top constant, the lock's switch-line count constant, the switch line moving only
with the top within the partial line's one-row travel; on fixture A, output moves only at its two relocks (units 300/301 and 43,737/43,738) and at real boxing
changes, no placement on the snow units 43,686–43,736, field precedence constant within a lock. Every render (two
captures × two fields per frame, rows doubled, red = picture top and bottom, yellow = the band bottom) is read back
by machine on every frame — bar positions and decisive picture shifts — before anyone looks at it. The owner's
watch copy is the live path's output with its record burned in. No work product stands in one instrument alone.

**Final outputs** (owner, 2026-09-07 21:4x): "for final outputs, the 720x486 overlay plus the raster that shows the
picture shift. the one with the running line and number at the bottom, rendered as bwdiff, not nnedi3", and "plus
all the decision information ... the last type of output this thread was last producing, tweaked slightly". So the
deliverable review copy of a capture is one frame per unit carrying: the 720×486 output as placed (CLAUDE.md §11's alternate
mode: lines 21–263 and 283–525, 243 lines per field; against the 480-line crop that is lines 21–22 above and 263
below in field 1, and 283–285 above in field 2 — the 486 raster is asymmetric — so what landed on the caption and
VBI rows is visible); the 525-line raster beside it, showing where the picture sits in the raster; and BELOW the
picture, never over it, the metrics band of `experiments/overlay_sidecar.py` — the per-field statistics on the left
(reason colour-coded, gauge with its line and decoded bytes, geometry d, raw top and bottom, lock state with the
source-lock provenance, the lock's fixed switch-line count, the measured clip line, the conservation equation) and on the right a graph of the applied shift across the
surrounding ±90 units with a line at zero and guides at ±2, swept by a red vertical RUNNING LINE at the current unit
(the owner's "the one with the running line and number at the bottom", identified 2026-09-09); the band's first line
carries the unit, the counter, the unit state, the applied pair and comb_safe. What the graph traces (owner, 2026-09-09):
BOTH fields' applied shifts, d1 and d2, not d1 alone; and the head-switch band's two edges per field — its top (the
switch line) and its bottom (the last band row) — drawn so both edges are visible in one element, absent where the
band is not measurable and omitted where the source has none ("not applicable" is distinct from unmeasurable,
rule 10). The band is "probably the thing that's most likely to be wrong" (owner). The picture top is deliberately
NOT traced: it must land on line 23 (286), so a jump is obvious on the picture itself, and the 720×486 render shows
lines 20, 21 and 22 anyway (owner). The plotted quantity is the applied displacement, zero meaning the standard
origin, so the absolute position is 23 + d (286 + d) — the same information shifted by a constant.

The band also carries the per-source quantities the placement rests on, so a wrong one is visible where it is used:
per field, the derived horizontal-phase distribution of the source and the row's own phase measured against it, and
the level references (blanking level and noise, pedestal, the tape's line-22 level with its
comparator count). Owner, 2026-09-09: "more good statistics to add to the bottom output, along with luma levels.
basically that running output should be as detailed as possible while still being sensible to read" — detail is
bounded by legibility, and anything that does not change a decision stays out.

**Alignment.** The band is aligned to the picture by construction ONLY when the video holds exactly one frame per
sidecar row from the first row, and the tool refuses anything else. The existing guard in `overlay_sidecar.py` tests
two frames per row because it was written for the bobbed 59.94p render; at one frame per unit it becomes one. This
matters: a keyframe-cut excerpt once silently offset every label by 12 units (25 extra frames, measured 2026-09-05)
and misled a whole review, which is why the review copy is produced over the entire capture and never from an
excerpt (CLAUDE.md §11, review-copy rules).

Deinterlaced with **bwdif in `send_frame` mode**, one frame per unit, 29.97p — never NNEDI3 (owner, 2026-09-08:
"the problem with nnedi3 is it doesn't just show jumps cleanly. it shows field doubling so the comb pattern during
playback is structurally impossible. it just renders as blur"). NNEDI3 builds each frame from one field, so the two
fields never share a frame and an inter-field error cannot appear as comb at all; the comb pattern is the legible
signal. A weaver decides motion by comparing fields of the SAME PARITY across time, so on static picture a
misregistered field shows no motion, the filter weaves, and the error combs at full strength; where the picture
really moves the test fires and interpolates, which is intended to suppress ordinary motion comb — an intention, not
a guarantee: its motion decision can fail, and the machine read-back stays authoritative. Both filters also run a
spatial check that can override the temporal decision and smooth a comb; bwdif has no switch for it and yadif does
(`mode=send_frame_nospatial`), which is the named fallback if a known one-line error ever renders as smoothing
rather than combing. The filter's job is to make an error obvious to the owner's eye; it is never the measurement,
which stays the settled comb on the placed crops and the machine read-back of every frame before anyone looks.
(Recorded so it is not relitigated: the 2026-09-04 "estdif made the OSD look stationary" episode is NOT evidence
against a weaver. The owner re-checked the raw full-raster render the same evening and confirmed the opposite — the
OSD in the OUTPUT RASTER is stationary, the picture behind it moves, and what had looked like a moving OSD was the
CORRECTED render, where the OSD must move by exactly the applied displacement because the crop window shifts to hold
the picture still. That is an acceptance check, not a fault: OSD displacement in a corrected output equals the
applied d. CLAUDE.md §7 carries the finding and LEARNINGS the lesson.)

Owner, verbatim (2026-09-07 15:15): "any true disagreement (such as comb not matching) should be reported loudly for
me to examine unit by unit in the test harness (Codex's job). please present a single frame rendered (and shifted)
bwdif image in that case." [The harness was Codex's at 15:15 and is Claude's since 20:10.] So every true disagreement — the engine's crop against the settled comb, the two
instruments against each other on a unit — is reported by the harness (Claude produces the report and the frames)
and handed to the owner, who examines them one by one: per unit, one rendered frame — the two fields' 240-row crops
as the engine placed them, woven into a 720×480 frame, deinterlaced with bwdif (one frame per unit, top field first),
labelled with the unit, its counter, both crop origins and the comb's reading. Neither agent adjudicates these.

## 9. Open

Nothing is open.

Closed 2026-09-09 (the owner): "the running line" is the red playhead sweeping the applied-shift graph in the
`overlay_sidecar.py` band under the picture, not a marker on the raster, and the graph must trace both fields. The
cadence is one frame per unit, 29.97, top field first, which follows from bwdif in `send_frame` mode.

Closed 2026-09-07 21:34 (the owner): a first lock is confirmed by combing, captions or both, and nothing else; the
earlier "significant non-dirty luma" is withdrawn (the Shuttle's blanking can hide the picture's first lines), and a
caption on the insert is ambiguous over d ∈ {−1, 0, +1} and confirms only with the comb re-measured (Source lock,
Comb).

Closed 2026-09-07 21:12 (both agents): the V-stabilize-off pass's flagged first lines are recorded, non-VBI rows and
therefore picture; the top is read through the flagging; the horizontal error is not the engine's (owner: "Horizontal
tearing is not a geometry event"; 13:29 "The first picture row is the first picture row").
