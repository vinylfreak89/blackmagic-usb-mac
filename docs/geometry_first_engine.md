# Geometry-first registration engine — design (2026-09-06 02:08 JST)

Branch `geometry-first`. Claude writes this engine; Codex writes the validation harness
(`docs/geometry_first_harness_brief.md`); neither reads the other's prior work. Per §14 the
design is derived below from two sources only — the owner's contract and the measured reference
raster — before any C is written. Every number is marked **raster** (derived from the measured
reference), **standard** (SMPTE RP-202 / CEA-608), or **default** (a tape-fitted value that must be
replaced or justified later). NTSC line numbers in prose; unit rows only in the tables.

## 1. The contract (owner, 2026-09-04/06, verbatim intent)

Geometry is the authority. Each field's active picture area — its top edge, bottom edge and
height — measured on every unit places the crop. Everything else (the tape's line 21, its black
line 22, static comb, any temporal witness) exists only to confirm that reading where geometry
alone cannot decide: (1) the head-switch region makes the bottom edge noisy and field-to-field
inconsistent; (2) geometry does not say which field's lines interleave on top — field precedence
is settled once per lock and held; (3) boxed pictures have their own geometry, centred in the
raster, and black level is not assumed constant. Tracking breaks only on a vertically torn
raster or a lost lock — both are one class: old geometry invalid, back to zero, re-acquire when
the lock returns. Horizontal tearing is not a geometry event. Dropout or RF noise that hides an
edge keeps the previous decision and re-evaluates when it clears. Line 22 never renders. The
output picture never moves except at a segment's initial lock and after such a re-acquisition.

## 2. The reference raster (measured 2026-09-05 on the locked no-source capture)

| unit rows | NTSC lines | content | source |
|---|---|---|---|
| 0–6, 261–269, 523–524 | 4–10, 265–273, 527–528 | padding, Y 16.0 / C 128.0 exactly | Shuttle |
| 7–15, 270–278 | 11–19, 274–282 | blanking, Y 1.4 ± 0.5 within a row, 0.01 unit to unit | Shuttle |
| 16, 279 | 20, 283 | timing pulse pattern | Shuttle |
| 17, 280 | 21, 284 | null CEA-608 insert (re-encodes what it decodes at the standard line) | Shuttle |
| 18, 281 | 22, 285 | blanking, Y 1.4 | Shuttle |
| 19–260, 282–522 | 23–264, 286–526 | pass-through: the source | tape/deck |

Consequences that the engine is built on:
- Nothing the tape carries above line 23 (286) reaches us. The tape's VBI becomes visible only
  when a displacement pushes it into the pass-through region: at displacement +2 the tape's
  line 21 appears on line 23; at +3 its line 20 appears on line 23 and its line 21 on 24; at +1
  its line 21 lands on the Shuttle's blanked line 22 and is invisible, while its black line 22
  appears on line 23 (measured: Y 4–7, above the 1.4 blanking, below any picture). At 0 the
  Shuttle re-encodes the tape's line 21 on its own insert.
- The picture's first RP-202 line is therefore the first pass-through row that is neither a
  VBI-type row (a 608 waveform, the tape's line 20 pattern, a black row) nor blanking. **Line 22
  never renders (standard):** if the first picture-carrying row sits directly under the tape's
  line-21 position, or directly under a black row that sits where line 22 would be, it is line 22
  and the crop starts one row lower.

## 3. Measurements, per unit, per field (all from the raw raster)

1. **Row luma profile** over the pass-through rows: mean and within-row std, at 640 samples per
   row. Blanking floor: 1.4 (**raster**). A row is *dark* if its mean ≤ floor + 8 (**default**: the
   tape's black line measures 4–7; a night scene at 10 is picture — the darkest picture row on
   fixture A; to be replaced by the field's own black level once boxing detection exists). A row
   is *picture* if it is not dark and not VBI-type.
2. **VBI-type rows:** a row that decodes as CEA-608 with valid parity (**standard**, my
   `cc608_decode.py` algorithm re-implemented in C: run-in by correlation at 1.986 µs cells,
   start bits 0,0,1, 16 LSB-first bits, odd parity per byte, amplitude gate 35 — **default**); a
   row with the timing-pattern signature of the Shuttle's line 20 (**raster**, by template match
   against the regenerated row 16); a run-in-only row (7 cycles, no start bits — the tape's line
   20 as seen at +3).
3. **Top edge:** the first pass-through row r such that r, r+1, r+2 are picture rows
   (**default**: three rows, so a single bright leak does not count). **Displacement top**:
   d_top = r − 19 (f1) / r − 282 (f2), then the line-22 correction of §2 if applicable.
4. **Tape's line 21 (when visible):** the unique parity-valid row off the insert ⇒ d_cap = row −
   17 (f1) / row − 280 (f2) (**standard**). Not an authority: a confirmation of d_top (it must equal
   d_top, or d_top + 1 when line 22 carries video in this recording).
5. **Tape's black line 22 (when visible):** the last dark row between the insert region and the
   top edge ⇒ d_gap = row − 18 (**raster**). Confirmation of d_top; also decides the line-22
   correction (a dark row directly above the top edge is the tape's line 22, so the top edge is
   already line 23).
6. **Bottom edge and height:** the last picture row before the padding, searched from the top
   edge downward; rows 257–260 / 519–522 are the head-switch band (**raster**: the four near-blank
   lines) and count as *uncertain*. Height = bottom − top + 1. Used only as a consistency check
   and for boxing detection, never for placement (owner: the bottom is noisy).
7. **Body continuity witness:** the vertical shift (−6..+6) of the field's picture body against
   the previous unit's same field, in two halves (upper/lower). Used only to (a) detect a
   splice/lost lock — one half still matches the previous unit while the other is a new picture
   (unit 300), or the two halves move by different amounts with the raster edges continuous —
   and (b) corroborate a one-line change of d_top when the caption and gap are both absent.
8. **Static comb between the two published crops:** once per lock, on the first units with
   ≥ 3% static detail (**default**), the relative shift (−3..+3) that minimises comb energy; this
   fixes FIELD PRECEDENCE (which field's picture line is above the other's). Thereafter a per-unit
   check only; disagreement is logged, never acted on per unit; a persistent disagreement (≥ 8
   units, **default**) with both edges stable flags the lock for re-acquisition.

## 4. Decision, per unit

For each field independently:
- If the top edge is measurable: d = d_top (with the line-22 correction). If a caption or gap is
  visible and disagrees with d_top by exactly the line-22 ambiguity, the recording's "line 22
  carries video" flag is set for the segment and d_top is corrected by it thereafter
  (**segment constant, learned once, boolean, not numeric**). Any other disagreement is logged
  (`VbiDisagrees`) and geometry wins.
- If the top edge is not measurable (torn, dark, snow): keep the previous d for this field
  (`EdgeHidden`), re-evaluate next unit. This is the owner's "keep the previous decision".
- If the body witness shows a splice or the classifier reports signal loss: mark the lock lost
  (`LockLost`), output the previous crop for this unit (nothing measurable), and on the next unit
  with a measurable top place fresh — the old d is not consulted (`Reacquired`, with the jump
  recorded). Field precedence is re-measured after every re-acquisition.
- Boxing: if height changes while top and bottom move symmetrically, the aperture is placed from
  the active area's centre (`Boxed`), not from the top edge (**owner**); until implemented, logged.

The output pair `(d1, d2)` is applied to the crops at rows 19+d1 / 282+d2, 240 lines each;
reading into the padding is legal black (**owner**). Sidecar: per field d, reason, top row,
bottom row, height, caption row, gap row, body shift per half, line-22 flag, lock state,
precedence, comb check — every decision with its evidence.

## 5. What this engine deliberately does not have

No zero re-anchoring, no learned numeric offsets, no evidence-voting hierarchy, no body-witness
veto of a measurable top, no persistent comb correction, no saved-geometry hold on absent
evidence, no top-reliability history. Each was measured to fit fixture A rather than the raster
(archaeology Part II). If one of them turns out to be needed, it comes back with a derivation.

## 6. Acceptance (Codex's harness, independently built)

Whole tape: crop starts on the picture's first RP-202 line by the oracle's reading (agree /
off-by-n / abstain per field); output moves only at units 300/301 and 43,737/43,738 (fixture A's
two relocks) and at real boxing changes; field precedence constant within a lock; no placement on
the snow/mute units 43,686–43,736; every hold named with its cause. Then the live-path watch copy
with the sidecar burned in, for the owner.

## 7. Revision from the raw panels (2026-09-06 05:30 JST, prototype `experiments/geometry_first_proto.py` at `be08bba`)

Every rule below replaced one in §3–§4 after a class panel (`experiments/class_panels.py`, raw rows of the units in
each decision class) contradicted the metric that had proposed it. Constants are labelled RASTER (measured on the
regenerated raster), STANDARD, or DEFAULT (fitted, to be replaced by a per-source measurement).

- **Rows are RECORDED or REGENERATED, decided against the unit's own blanking rows.** The Shuttle's regenerated rows
  (blanking, the two inserts, row 18) are chroma 128 exactly with sub-unit spread in every unit; every row that came
  through the analog decoder, black content included (luma 2–9), carries the decoder's chroma offset and noise
  (125–127). Thresholds are multiples of the blanking rows' own row-to-row spread (RASTER), never fixed levels. This
  makes the recorded region's first row measurable on black scenes and flat walls, where every luma-level test failed.
- **The top is the first recorded row that continues into the picture for two links** (row→row+1 and row+1→row+2,
  on 8-px horizontally smoothed rows, by correlation or by a difference at noise level). A VBI waveform (the tape's
  line-20 pulses, a parity-failed caption, the smeared XDS bar, the data line) never continues into the picture, but
  adjacent waveforms resemble EACH OTHER (measured: XDS bar vs run-in fragment, pulses vs caption), hence two links.
  Parity-valid captions are recognised as such (`cea608`); nothing else about a VBI row is assumed.
- **Recorded black above the picture is a BAND with two edges** (band start, picture start), reported as such; one
  raster cannot say whether it is the tape's blanking lines (field displaced by the band's height) or a black picture
  top. The caption decides when present (picture = caption+2, STANDARD); else the lock holds when it lies inside the
  band; else a single black row is read as the tape's black line 22 (fixture A's captions validated that 309/309,
  DEFAULT) and a deeper band as picture (golden rule: the recorded region is the picture until a gauge says otherwise).
- **Line 22 is never rendered (STANDARD RP-202).** A caption one row above the picture start marks that row as line
  22 whether it is black (gap) or attenuated video; only the video case sets the per-segment state used when no
  caption is visible. (A double count between the gap and video paths on the intro was the first panel-found bug.)
- **Field 2 without a gauge takes the relative static comb only among the admissible candidates of its black band.**
  A comb minimum cannot separate a displaced field from a source-side inter-field error; unconstrained it moved field
  2 to −1 at 05:00, below the recorded region, which is geometrically impossible.
- **The bottom is the last recorded row** (the deck's clip line: 262/525 on both fixtures, so height = 240 − d), no
  corridor of any width; the head-switch partial line under the last full picture line is reported with its split
  column and is picture. The commercial tape's picture runs to 262/525 and fixture A's to 260/522 plus the partial
  line: per source, measured per unit.
- **A flat raster holds.** Body median smoothed correlation 0.00 and row difference 0.1–0.3 (deck mute, pause, fade)
  against 0.90–0.95 / 1–11 on pictures (DEFAULT 0.3 / 1.0): no edge exists to measure.
- **Removed:** the three-consecutive-continuous-rows requirement (a content edge inside the first rows broke it),
  `bottom_uncertain` and the `hs` corridor constants, the luma-only `DARK` picture test, and the `runin`/`ccenv`/`bar`
  heuristics (the two-link rule and the regenerated/recorded split make them unnecessary).

Slice results at `be08bba` (applied pairs, units): 01:26 (1,0) 44 / (0,0) 30 / (2,0) 5; 05:00 (1,0) 373 / (0,0) 199 /
(2,0) 34; 35:00 (3,2) 357 / (2,2) 263; 37:01 (3,2) 244 / (2,2) 82; 45:00 (3,2) 614 / (2,2) 6; minute 43 (3,2) 306 of
319; commercial tape (0,0) 896 of 920 with every transition inside the first 47 units (rewind tail). The 35:00 +2/+3
alternation is the caption moving with the picture; the crop lands two lines under it every unit (panel-confirmed).
Not yet handled: snow and torn rasters are the signal-state layer's call (the frameserver's classifier), not
geometry's; the prototype only holds on flat rasters and torn top strips.

### 7a. Same day, later (07:50 JST, `e25f09b`), from the first harness comparison and its raw-row adjudication

- **A single black row directly above a picture-level row is the tape's black line 22, read every unit and never held
  through.** Codex's row means refuted my panel reading of the be08bba one-above class: line 23 flat black (luma 5,
  std 3–4) over a picture row at 102–164 is the +1 case, and a lock at 0 had been allowed to resolve it. The lock
  resolves a black band only when the rows under it are themselves dark (a black first picture line over a grey
  band, the commercial tape's dark scenes). DEFAULT picture level: blanking + 40.
- **A readable caption places the field when the picture edge is hidden** (398 of 404 whole-tape caption
  disagreements were EdgeHidden holds with a caption in view).
- **A field-2 parity row directly under a recorded waveform is the tape's line 285**, so the picture begins one row
  under it, not two (its 284 is the smeared bar above). The level-ratio version of this rule broke minute 43, where
  line 22 carries intermittent full-level video, and was replaced by the structural one.
- **The per-segment "line 22 carries video" state adds a line only when the row above the top is not a waveform or a
  torn row**; in the 34:39 damage slice a waveform above the picture had made it add a line to a top that was already
  the picture.
- **The relative comb only chooses among a black band's admissible candidates**; unconstrained it moved field 2 to
  −1 (below the recorded region) in 73 units at 05:00.
- **A flat raster holds** (body median smoothed correlation < 0.3 and row difference < 1.0: the deck's mute, a
  pause, a fade).
- **Ordinal = unwrapped device counter − first exact unit's counter**, the harness's numbering; a walker count sat five
  high (leading fragments) and was silently unjoinable.
- Adjudication panels carry the two candidate rows' luma mean/std in the label: an 8× panel of a dark row can look
  textured, and did.

### 7b. Review agenda for the next round (Codex's code-and-intent review of `5c3ffc3`, 2026-09-06 10:20 JST)

The prototype at `80a65af` is not accepted. Two whole-tape runs were scored against Codex's blind-built reference and
adjudicated on raw rows; the review then named the structural faults the rows confirm. Each item below carries the
ordinals that decide it (Codex is turning them into `experiments/geometry_oracle/reports/review_fixtures.csv` with a
`--fixtures` scorer flag):

1. Relative comb as a per-unit actuator bounces field 2 on an unchanged raster (66,422–66,424). Precedence settles once
   per lock on demonstrably static pixels; later checks report, never move.
2. No signal/relock input: snow at 43,686–43,736 gets placed; the body-half splice test false-fires (63,330–63,331).
   Explicit events: relock at 300 and 43,737; forbid the mute; report the near-repeats 43,696/43,702/43,707.
3. Bottom and height do not participate in the decision (top-only engine); active vs recorded bottom to be settled on
   the raw rows (fixture A ~260/522 active vs 262/525 recorded; commercial tape 262/525 both).
4. Damaged VBI rows accepted as picture (66,421; 63,053) — the standard run-in/start/cell 608 waveform test,
   independent of parity, replaces the fitted shape tests; hard-edged picture rows must survive it.
5. Captions override measurable geometry (62,713/62,717/62,723): geometry wins; a caption resolves the line-22 band
   or a hidden edge only, and disagreements are logged.
6. A lock inside a black band can preserve a wrong acquisition indefinitely (294–299, 420).
7. `line22_video` is a fitted state; derive the category from simultaneous caption plus complete geometry (63,506).
8. `recorded_mask` trusts nine blanking rows a torn strip could contaminate (no fixture exists yet).
9. One H-torn row or a flat body suppresses a measurable edge (62,322–62,326, 64,097).
10. Not fail-closed on a provenance error (partial sidecar kept). 11. `counter_extended` is wrapped; every row is
    labelled Complete/published regardless of signal state.

## 8. Contract v2 — the owner's model, written back (2026-09-06 21:08 JST, before any code)

One question per field per unit: **where does the picture start, and did it move since the last unit.** Everything
else is confirmation.

**Measured every unit, per field, from the raw raster and the unit's own regenerated rows**
1. The recorded region: first and last row that came through the analog decoder (chroma/luma against the unit's own
   blanking rows). The last recorded row is the deck's clip line, a per-source constant measured at lock, never assumed
   (262/525 on both fixtures).
2. The picture top: the first picture row inside the recorded region. Rows above it that are VBI (the tape's line 20
   data, its line 21 caption, its line 22 whatever it carries) are skipped. They are recognised by confirmation
   signals (parity, waveform shape) and by the fact that the picture body does not include them; they never move the
   crop on their own.
3. The picture body shift against the previous unit of the same field: the integer shift in −3..+3 that best matches
   the body (same-parity temporal correlation), with a decisiveness ratio; when not decisive the body abstains.
4. The bottom: every picture line has a left and a right active edge that sit within the field's own horizontal
   variance (timing is never perfect); the head-switch band is the lines whose edge falls outside that variance,
   left or right, on every VHS and on any source with a switch point. The last line whose edges are within the
   normal variance is the bottom. Recorded black under the picture on fixture A was a special case, not the rule.
5. The conserved quantity is the line ACCOUNT, not the height: visible picture lines + lines added above the picture
   + lines lost into the deck's blanking at the bottom = constant. Add X black lines at the top and the picture moved
   down X and is X shorter; remove X and it moved up X; this holds past the raster bounds; nothing deletes lines from
   the middle of a field except a vertical tear.

**Decision, per field per unit**
- No lock is claimed without confirmation: comb agreement between the fields, or clean, significant luma at the
  measured edge. Without it the picture stays at standard placement (23/286) and the sidecar says there was not
  enough to lock on. Once locked, with no signal loss since, tracking from the previous unit takes over.
- Body shift 0 and the account unchanged → the field did not move. The crop stays, whatever any classifier says
  about the top row.
- Body shifted by s, top moved by s, the account shows s lines added above (or lost below) → the field slipped by
  s. Move this field's crop by s to bring it back. The other field is untouched.
- The row directly above the picture that sometimes carries data and sometimes a faint copy of the line below is
  decided by geometry, never by classifying the row: if the bottom did not move, the top change is a garbage row
  from the signal chain and the field did not move; if the bottom moved too, the field shifted. The bottom is the
  tie-breaker.
- Both fields' bodies shifted together with no height change → picture content moved (a tilt). Ignore.
- Comb parity (the fields' relative placement) is established once per lock and is a confirmation from then on. It
  never moves a field by itself.
- Captions are confirmation. A caption may place the very first unit of a segment, when there is no previous field to
  compare against; a caption that disagrees with measured geometry is logged, geometry wins.
- Segment events (splice, signal loss, relock) come from the signal-state layer as explicit inputs. On one, the old
  geometry is invalid: back to standard placement (23/286) and re-acquire. Never inferred from a body-half heuristic.
- Damage that hides the edge (torn strip, dropout, noise band, flat raster) holds the last good geometry; when it
  clears, the new geometry is checked against the old and adjusted once.
- A raster whose edges cannot be measured at all is Unknown, held, and labelled; never a substituted number.

**No thresholds** except the decisiveness ratio of the shift measurement, stated with its measurement, and the
per-source constants (clip line, horizontal-edge variance, the line account, comb parity) measured at lock. Any
other number in the code is a defect. Tests are dumb and brute force: picture visible is the top, picture gone is the
bottom; black is the hard case and every not-sure class is worked through, never thresholded away.

**Output per field per unit:** applied d (crop start = 23 + d1 / 286 + d2), the body shift and its ratio, the top,
clip and height, the confirmations seen (caption line, comb), the reason. Scored against the harness's raw-confirmed
fixture rows before any whole-tape claim.

## 9. Measured 2026-09-07 (owner review of the reference renders + raw rows): the head switch is not picture geometry

Raw rows of the SP recording (`/private/tmp/hw-session/w_300s.tpc`, zoomed panels `zoom_SP_f1_u77-79.png`,
`zoom_SP_f2_u74-76.png`; per row: luma mean/std, left/right active edge, |difference to the row above| per third
against the body's own):
- **Field 1, units 77 → 78 → 79:** the picture's top stays at line 23 and lines 254–258 carry the same content in all
  three; the switch (the partial line, whose middle/right thirds depart) sits inside line 261, then 259, then 260,
  with the other head's pedestal rows under it. **Field 2, units 74 → 76:** top fixed at 286, switch inside 523,
  522, 524. The band moves by one or two lines unit to unit while the picture does not.
- **Commercial tape, units 551–1132:** the switch stays inside 260 / 522 in every measurable unit (its own recorder).
- **SP unit 439 → 440 → 451:** the whole field 1 moves up one line and back (top 24 → 23, switch 261 → 260, band with
  it): a rigid one-line displacement in which top and switch move together.
- A row of chroma noise can sit below the band (commercial pre-551 units, line 263: chroma std 3.08 against the
  0.5 blank); chroma alone therefore overstates the band bottom by one line there (owner observation, confirmed).
- Where the switch lands at or past the clip line no band is visible in that unit (owner: "certain fields have no
  detectable head switch").

Consequences (owner, 2026-09-07, amending §8): the head switch is a separate physical event (drum phase) whose
position relative to the picture jitters on this recording, so it is **not** a per-source constant to lock and **not**
a witness of the picture's vertical position by itself; the account "bottom moved by X ⇒ top moved by X" does not
hold across a switch move. The picture's position under lock is the top and the body; the picture's bottom is
`min(last picture line, switch line − 1)` measured per unit and legitimately moves when the switch cuts higher; the
review render carries two markers, the picture bottom (red) and the band bottom (yellow), both per unit. A recording
whose fields were recorded misregistered cannot be corrected by any frame TBC; only measuring the expected geometry
and every departure from it can, which is this engine's job. The v3 engine's switch lock (`geometry_v3_decide.py`)
is therefore correct only for sources whose switch is steady (the commercial tape) and is superseded for fixture A.

**Pairing phase is per capture, measured 2026-09-07 02:40 JST.** The owner re-captured the SP passage with
V-stabilize off (`/private/tmp/hw-session/sp_vstab_off_45s.tpc`, transport complete; slice `sp_vstab_off_slice.tpc`,
608 units, content-aligned to `w_300s.tpc`). Pooled field-body comparison at units 20/150/300/600: the new unit's
field-1 SLOT is the original's field 2 of the previous unit (MAD 2.6–3.0, against 7–12 for any other pairing) and its
field-2 slot is the original's field 1 of the same unit (2.4–2.8). The Shuttle grouped the same field sequence one
field later, so "field 1" and "field 2" name transport slots whose parity differs between these two captures of the
same tape. Every per-field constant (switch side and position, VBI lines, top origin) must be measured per capture on
the slot's own content, never carried by slot name from another capture; the review render's bottom row was
re-paired (this unit's field-2 slot beside the next unit's field-1 slot) to compare the same recorded fields.

**The field-1 displacement of the SP recording is made by the deck's line TBC, not carried by the tape — measured
2026-09-07 03:10 JST on the same recorded field in both passes.** Raw rows (`zoom_ON_f1_u20_200.png`,
`zoom_OFF_slot2_u20_200.png`, `zoom_OFF_slot2_u78_105.png`, `zoom_SP_f1_u105-107.png`):
- V-stabilize ON (fixture A, `w_300s`): unit 20 field 1 has the tape's black line 22 on line 23 (luma 1.6) and the
  picture from 24; unit 200 the same (5.5 / picture from 24); unit 105 has the tape's caption on 23, black on 24,
  picture from 25. The harness reference reads the top at 24 in 438 of 608 units and 25 in 48.
- V-stabilize OFF (`sp_vstab_off_slice`, same recorded field): the picture starts on its standard line in every one of
  the 608 units (reference: 0 top changes in either slot), with nothing of the tape's VBI visible above it; unit 105
  instead shows a severe horizontal tear over its first rows, which the ON pass shows as a clean, two-line-lower field.
- Bottom: OFF unit 20 carries picture content through line 524 with the other head's black run beginning at 525 and
  the rows before the switch horizontally skewed; ON unit 20 ends the picture at 260 with the partial switch line at
  261 and a pedestal row at 262. The field is one line lower and one line shorter with the TBC on.
Reading: the line TBC cannot time the torn rows at the top of field 1 and drops them, shifting the rest of the field
down by that count (one line in most units, two where the tear is worse) and clipping the bottom by as much; the
trigger (weak field-1 H-timing at the top, recording-borne, present on two decks) is on the tape, the vertical
displacement is the deck's. §11's "field-1 displacement is recording-borne" stands only for the trigger. The
head-switch position in the ON pass therefore moves with the dropped-line count, which is the "switch jitter" of §9.
Consequences: the raw pass is the geometric reference for what the tape holds; the ON pass is what a user of this
deck gets, and the engine's job on it is exactly the per-unit displacement the TBC introduced. A row-to-row
departure test reads the OFF pass's pre-switch skew as the switch (harness reference two lines early at units 20/200).

## 10. Contract v3 — the owner's model of 2026-09-07 03:09–03:35 JST (verbatim in
## `/private/tmp/hw-session/briefs/owner_verbatim_transcript.md`, extracted from the session transcript by script;
## Codex's independent read agreed on every point but one, its turn 4)

Per field per unit, measured from the unit's own regenerated rows with the same code on every capture:
1. **Blanking bounds** the geometry above and below; the picture is the rows between, and a field closes to its
   expected 240 lines (top + 239), whether or not all of them are visible in the Shuttle's raster.
2. **The reliable geometry is the top of the picture to the row before the head switch.** Measured at units 20,
   105 and 200: 237 rows in both the V-stabilize-on and -off passes, so the count survives the TBC.
3. **The head switch is one of: discontinuous horizontal skew, an RF peak in the luma, or both** (plus an AGC level
   mismatch where present). The peak carries the tear with it, so its horizontal position on the line is measured
   when present; it drifts slowly, never jumps from one side to the other; the TBC can smooth it away and render the
   partial line as picture, and then the band's row count is what survives. The head switch is optional (not every
   source is VHS): "not applicable" is distinct from "unmeasurable".
4. **The band is the unreliable part of the geometry**: how much of it is blanked by the switch versus the end of the
   picture is the number of band rows, and that number is confirmed by secondary signals (comb between the fields,
   VBI, captions), ideally more than one. The band count alone never moves anything.
5. **Raster clipping**: a whole field can mistime and fall out of the Shuttle's raster; cues present one frame and
   absent the next mean they shifted away, near-certain when the top shifts too. Open: the top stable with the band
   gone. Codex's audit: in the on pass every switch-past-clip transition (24) came with a top move; the owner has no
   model for the stable-top case; Codex disagrees that it is a field shift by itself; Claude's proposal is the
   per-field body shift against the previous unit compared between the two fields (a pan moves both, a field shift
   moves one) with the comb changing at the same unit.
Per-unit record (Codex's list, accepted): measured top with its VBI/caption/blanking evidence; expected bottom
top + 239 with clipping status; first switch row (skew, peak, AGC, or combination); last reliable row = switch − 1;
last visible picture-bearing band row; first blank row and raster limit; band length incl. censored rows; RF peak
row, x, strength, presence/disappearance and continuity from the preceding field; skew and AGC evidence;
comb/VBI/caption confirmations with observed / inferred / censored / unmeasurable / not-applicable status;
independent dp and switch displacement, never turning a missing observation into motion.
Measured row signatures (2026-09-07 04:00, verified units, both passes): picture rows match the row above at a
segment lag of 0–1 with mean |diff| 8–17; the first other-head row has median segment lag ≥ 10 and mean |diff|
35–80; the RF peak is a spike ≥ 4× the row's mean |diff| (105–160 raw) at the same sample in both passes on an
otherwise aligned row, with the next row torn from that sample on; the on pass ends the band with a flat pedestal
row (std < 1.1).

### 10.1 Engine measurement under contract v3 (experiments/switch_geometry.py, 2026-09-07 04:00–05:45 JST)

Per field of every unit, from the unit's own regenerated rows; the same code on every capture:
- **blank**: the field's blanking rows (lines 11–19 / 274–282): luma level and noise σ_b, chroma noise c_b.
- **recorded**: chroma noise > 2 c_b (measured gap: blank rows ≤ 1.48×, recorded ≥ 2.02×).
- **pedestal** (recorded black): the field's lowest flat recorded row above the blank (the other head's black in
  the band) when it has one, else the last pedestal seen on the source, else the blank.
- **top**: the first recorded row that begins a run of three picture rows — above the pedestal by more than 3 σ_b,
  textured (std ≥ 4 σ_b), not a CEA-608 waveform. Verified on the raw rows at SP units 4, 20, 75, 78, 86, 105, 106,
  200 (the tape's black line 22 at luma 4–8 and a damaged caption at 23 are skipped).
- **S**, the first row belonging entirely to the other head: the band is contiguous at the clip, so the scan runs
  upward from the last recorded row while a row is (a) time-shifted as a whole against the row above or the row two
  above — whole-row best lag ≥ 2 samples with SAD(best)/SAD(0) ≤ 0.90 over the two rows' common content span (the
  blind check's envelope: picture rows |lag| ≤ 1.2, r ≥ 0.94 on 71 full-content rows), or (b) torn — median segment
  lag and mean row difference both beyond the body rows' own maxima, or (c) a pedestal row, or (d) a leading blank
  run longer than the picture's own H-dip by 8 samples, or (e) without the H-dip (content at sample 0). The switch
  itself lies in S or S−1 (the partial line); S−1's evidence (a narrow spike on a flat background, its rank against
  the picture's own narrow specks, its whole-row lag/ratio) is recorded, never resolved by a threshold.
- **picture bottom** = top + 239 clipped at the last recorded row; **band** = S..last recorded; reliable = top..S−1.
Results: SP pass, verified units 20/78/105/106/200: S = 261/259/262/261/261 (field 1) and 523/523/522/522/523
(field 2) = the raw rows; blind subagent (own detector) on 15 sampled units: 13/15 + 2 definitional (field 1),
15/15 (field 2). Against Codex's contract-v3 reference (e6a5542/35e5979): top 608/608 and 604/608 (the four: line
286 at luma 3.8–6.0 is the tape's black line 22, engine 287 is right); S within one row of switch_first_line in
608/608 both fields. Stabilized render from the record: the bottom bar moves only where the top moves (67 = 67 and
8 = 8); residual picture shifts in the output 5 + 6 units, of which 75/76/79/102/105 are one field moving one line
under a clamped top (the body shift decisive in that field only) and the rest alternate fields at consecutive units
(content motion). A carried offset from the body alone moves the jump instead of removing it (tried, not adopted):
the resolution is the comb (§10.4), which Codex's harness now measures (turn 7: registration unchanged at all 63
measurable fixed-top switch moves on the SP pass).
Known limits: on the V-stabilize-off pass the picture carries rows as torn as the band's (a horizontal tear at lines
323–336 of unit 20) and the other head's rows settle to match each other, so the band is found only by contiguity,
the two-above test, the missing H-dip and the whole-row shift; S at the verified units 524/523/523/523/523 against
the rows' 523. Thresholds that remain constants: 2 samples / 0.90 (the blind check's envelope), 8 samples over the
H-dip, 3 σ_b above the pedestal, 4 σ_b for texture, 2 c_b for recorded — each stated with the measurement behind it.
Additions 06:30 JST: a dark recorded first band is picture and a lone dark row before a bright one is the tape's
black line 22 (the owner's round-4 ruling, re-established by Codex on the commercial rows: L23–L27 recorded at luma
4–10, L28 the bright onset); the top lies within the first four recorded rows (the tape's VBI can occupy at most lines
20–22 of the pass-through region) or the picture's top is unmeasurable (black top), never a brightness edge deeper in
the field; the picture bottom clips at the Shuttle's pass-through end (262/525, §2), because the chroma-recorded last
row falls short of it on dark units. Engine commit 632b110; Codex reference 82f177b. SP tops unchanged (8/8 verified
units); commercial dark-topped units 447/497/650/700/900 now 23.
**Comb at the residual units (Codex turn 9, 17ea6df).** At SP units 75, 79, 102, 105, where the engine's stabilized
output still moved because one field's body shifted decisively while its top held, the inter-field comb stays at
shift 0 (seven-shift energies minimal at 0 in units 74–80 and 101–106; unit 76 is a rigid −1 carried by both records;
unit 103 a genuine +1 with every coordinate fixed). The body moved and the weave did not: content motion. The crop must
not follow a body shift without a comb change; the clamped-top case of §10.5 is absent from the SP slice and, where
it occurs, shows as a comb change under a fixed top. EP pass: 458 measurable comb readings, all 0; 139 fixed-top
switch transitions, none changed the registration.

### 10.1.2 Engine rules added 2026-09-07 morning (commits 805434d … fb390d9), each from raw rows looked at first

- **The pedestal is the flat run contiguous with the clip.** A pedestal row (the other head's black) is flat AND at that
  level. A flat dark picture above the band is picture (EP counter 1913: lines 253–260 at luma 26, std 1–2, above the
  band's pedestal 13); a flat grey field has no pedestal of its own (commercial counter 6842). Before this, S ran up
  to line 250 through the flat picture.
- **A recorded row carries tape noise in chroma OR luma above the blank;** the Shuttle's padding (Y16/C128, zero
  variance in both) is excluded explicitly. A flat grey field with chroma noise only 1.7× the blank's (commercial
  counter 6842, luma 17–20 from line 23) is recorded.
- **Blanking inside the row is a band signature.** The other head's line carries its horizontal blanking interval —
  luma 1–2 at the blank's own noise — in the middle of the row (samples ~60–200), where a timed row never has one;
  its length is bounded by NTSC (64 samples = a sync pulse, 200 = more than any H blanking interval). Census
  against the harness reference (commercial, 920 units): band rows 834/954 (f1) and 1259/1323 (f2) carry one, the row
  before the switch 0/531 and 0/535, picture rows 0.4% and never within 4 rows of the switch. On the SP recording the
  intruding run sits at the pedestal (luma ~11) and no band row carries a blank-level run: the two captures show the
  same physics at two levels, and the engine keeps both tests. Codex's harness arrived at the same signature
  independently ("internal blank run x82–145 at Y1.391", turn 10).
- **VBI-type rows fail to correlate with the row below.** Adjacent picture lines correlate (measured r 0.87–0.99); the
  EP recording's smeared XDS bar (line 286), its run-in fragments (287) and its caption rows correlate at 0.01–0.36.
  The test applies only to rows with texture ≥ 4× the field's own noise (median std of adjacent-row differences /√2
  over the middle rows), so a dark band with texture at the noise (commercial lines 23–24, std 3–6 against noise 2)
  is left to the brightness rules. The bound 0.5 is a fitted default. Codex's harness uses a different signature
  (localized left-side structure, flat remainder, no continuation as a whole-width row) and reaches the same 288 in
  621/621 EP units; correlation is corroboration there, not the classifier.
- **A bright flat row is picture when the row below is flat too, VBI when the row below is textured.** The flat grey
  field (every row flat) is picture from line 23; the EP recording's isolated dim row before the picture (counter
  2066: line 25 at 18.1/2.7 before line 26 at 107/65; also 2303, 2410 — the harness's witnesses) is VBI.
- **The engine streams** (two rasters in memory) and flushes its record per unit. Whole-capture numbers for these
  rules: run C (0fc3461), recorded in the 2026-09-07 report.
- **The owner's commercial-tape rule as a test** (`experiments/stable_interval_check.py`, counter ≥ 6593): the top
  must be constant where measurable; S within one row of its mode. Codex's rows (turn 10) show the first-full-other-
  head row itself moving between 260 and 261 at counters 6645, 6688, 6714, 6738 with the top fixed at 23: the
  picture is stable, the switch position is not — the test's one-row allowance is physics, not tolerance.

### 10.1.3 Engine rules revised after run C (commit 992bf15, 2026-09-07 09:11 JST), each from rows looked at first

- **Every band test states its physical premise.** The whole-row lag is a time-base STEP only when the lag against the
  row two above equals the lag against the row above (a slanted picture feature doubles it: EP counter 1967, lines
  253–258, lag 3–5 one row up and 6–10 two rows up, had read as band); it needs texture on both rows (a flat row has
  no alignment: commercial counter 6657's flat grey rows read lag −16 at ratio 0.90 by chance); the leading run must
  sit at black (a flat picture row's own noise ended a picture-level run); the row-two-above pass carries no torn test
  (two rows apart the picture's own detail exceeds the body envelope: seven picture rows read as torn at counter 6907).
- **The field's noise is the median std of adjacent-SAMPLE differences /√2.** VHS luma is band-limited near 3 MHz, so
  adjacent samples at 13.5 MHz differ mostly by noise; adjacent-ROW differences carried the picture's vertical detail
  and read 12–15 on the SP recording against a tape noise near 5 (EP 1–4, commercial ≈ 1).
- **A VBI row is textured and uncorrelated with BOTH neighbours at its best horizontal lag (−24..24).** A torn
  picture row correlates with its neighbour at its lag (the V-stabilize-off pass's field tops read 287–289 or
  unmeasurable in 125 units under zero-lag correlation); a picture row at a horizontal edge correlates with one side
  (EP counter 2303, line 26 at 41.5/26.1: 0.00 below, 0.94 above). Rows torn beyond 24 samples (the raw pass's
  flagged first lines) still fail and are a listed residual; widening the search would carry the EP recording's
  run-in row (0.48 at ±24) over the 0.5 bound.
- **The black line 22 is SUB-BLACK, not merely dark.** On a tape with setup the tape's black line 22 sits below the
  tape's own black — the pedestal, the other head's black in the band (SP recording: 3–7 against 11.4) — which no
  picture row does; so a sub-black row before a row that is not sub-black is VBI and a run of sub-black rows is
  picture (the dark-band ruling). On a tape without setup (black at blanking: the commercial tape) the pedestal is
  the blank, nothing is sub-black and a dark first line is picture — commercial counter 6672 (lines 23–27 at 4–19)
  reads 23 again, as the harness's turn-8 rows ruled. The earlier 'bright = pedestal + 3σ_b' rule had read those lines
  as bright and the top wandered 23/24/25 on a stable picture. A level-free rule was tried in between and read the
  SP intro one row high in every unit (the black line 22 taken as picture); the two tapes differ exactly by setup.
- **A flat row before a textured row is VBI, before a flat row picture** (EP counter 2066: line 25 at 18/2.7 before
  107/65 → top 26; a flat grey field → 23).
- **Residual (per-unit undecidable, both instruments):** commercial counters 6641–6674 and 6802–6819, where the first
  picture line is a half-row transition (counter 6645: line 23 at 5.3/3.3, 24 at 15.3/9.0, 25 at 22.7/2.4) — the
  engine reads 25, the harness 24 'inferred'; the picture's constancy across the tape (line 23 grey at 6842) says 23.
