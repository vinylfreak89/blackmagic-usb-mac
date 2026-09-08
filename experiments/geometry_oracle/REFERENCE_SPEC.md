# The v10 reference: what each column is, and the raw-row measurement behind it

HANDBACK §7 step 1 requires the reference to be re-derived from the contract, with "every column's raw-row
derivation stated". This is that statement. It is written BEFORE the code so the code can be checked against it,
and it is the harness's half of the two-instrument acceptance (contract §8): the engine's record and this
reference are implemented independently from the same contract and the same raw rows, and are never fused.

## Why this is not the old builder

`build_reference.py` (165 KB, 130 field columns, frozen at `552ad2f`) is the geometry-first experiment's builder.
The owner's ruling of 2026-09-07 20:10 carries its raw-row MEASUREMENTS into the contract's section 2 and leaves
its engine, its later reference semantics and its fitted constants behind. Its column set is also its own
diagnosis: three columns per quantity (observation, status, evidence) for 40 quantities is what an instrument
looks like when nobody can say what it is measuring. Contract §5 names about a dozen things. This starts from
those, and reaches into the old file only for a specific measurement technique, re-derived and cited when it does.

## The unit of the record

One row per device counter per field. Field is 1 or 2. Rows are the Shuttle's unit rows in the CSV and NTSC lines
in every report and message (CLAUDE.md: NTSC line = unit row + 4). Every measured quantity carries its own
measurability class, never a substituted number:

- `observed` — measured on this unit's raw rows.
- `unmeasurable` — the measurement was attempted and its own precondition failed. The reason is named.
- `not_applicable` — the quantity does not exist for this source (contract rule 10: distinct from unmeasurable;
  e.g. a source with no head switch).

A column that is not `observed` carries no number at all. A provenance failure (an unpublished unit, a duplicate
counter, a short or unframed unit reaching a fixed-raster measurement) fails closed and the whole row is void
(contract §5: "Provenance errors fail closed").

## The columns

### 1. The recorded region
`recorded_first`, `recorded_last`, `recorded_class`.

Contract §3: a recorded row came through the analog decoder and is told from the Shuttle's regenerated rows by
the decoder's chroma noise — regenerated ≤ 1.48× the blanking rows' noise, recorded ≥ 2.02×, the test at its
lower bound — or by luma above the blank. Padding is neither.

Raw-row measurement: per row, the standard deviation of the chroma bytes (even offsets) and the mean of the luma
bytes (odd offsets). The reference for both is this unit's own regenerated blanking rows (7–15 / 270–278), never
a constant. A row is recorded when its chroma noise is at least 2.02× the blanking rows' chroma noise, or its
luma mean is above the blanking mean by more than the blanking rows' own spread. `unmeasurable` when the
regenerated blanking rows are absent, which contract §3 makes a lock-like-loss observation in its own right.

### 2. The picture top and the VBI rows above it
`picture_top`, `top_class`, `vbi_rows`, `vbi_signatures`.

Contract §3: a VBI row is a recorded row carrying a vertical-interval WAVEFORM, recognised by signature — the
CEA-608 waveform, the run-in burst without data, the tape's line-20 timing pattern, the smeared XDS bar. A
picture row is a recorded row that is not a VBI row. The picture top is the first picture row, and nothing else:
"the first picture row is the first picture row" (owner).

Raw-row measurement: walk down from the first recorded row, classify each row by signature, and stop at the
first row that matches none. Each VBI row is recorded with the signature that caught it, so a wrong exclusion is
visible rather than silent. The four signatures are measured tests on the row's own waveform, and each is
specified in section 4 below. `unmeasurable` when the recorded region is unmeasurable, or when a row matches
more than one signature (the owner's ruling: an ambiguous vertical-interval reading is not a reference).

The top may be hidden by the Shuttle's overwrite blanking (contract §3). The reference does NOT guess in that
case: it records the top as `unmeasurable` with reason `hidden_by_insert`, and the position is left to the line
account, which is column 6. New luma at the top alone never moves anything (owner, 15:11).

### 3. The caption line
`caption_line`, `caption_bytes`, `caption_class`.

Contract §3 and CLAUDE.md §11: the tape's line 21 is the CEA-608 waveform decoded with parity. Only lines OFF
the Shuttle's regenerated 21/284 are evidence, because the device re-encodes at 21/284 and its bytes are its own
decision about where line 21 was, never a measurement of ours.

Raw-row measurement: decode every recorded line of the field as CEA-608 — run-in phase by correlation, start
bits, sixteen data bits at 1.986 µs cells, odd parity per byte — gated at run-in amplitude 35 (the measured
separation: real captions 52–60, chance picture hits 15–22). `observed` when exactly one line off the insert
decodes; `unmeasurable` when more than one does (contract, owner's ruling: multiple line-21-like rows mean the
timing is too unstable to use); `not_applicable` when none does, which is the ordinary case for a source with
no caption service and for field 2 of both fixture-A recordings.

This is a CONFIRMATION, not the gauge (contract rule 1: geometry is the authority). It is recorded so that a
disagreement with geometry is visible and reportable, which is what rule 1 requires.

### 4. The switch line and the signatures that carried it
`switch_line`, `switch_signatures`, `switch_class`, `S`, `S_class`.

Contract §3: the head switch is discontinuous horizontal skew, an RF peak, or both, plus an AGC mismatch where
present. The switch line is the top switch line, the partial line. With the peak absent it is the first
measurable horizontal-skew discontinuity scanning down from the picture; else S, the first full other-head row,
when that is exposed. That one row is the travel.

Raw-row measurement: the per-row horizontal-phase profile (section 5). The switch line is the first row whose
later part departs from the row above while its earlier part does not — a partial row. S is the first row whose
whole profile has departed. Both carry the signatures that produced them so the reading is auditable.

⚠️ This is the column most likely to be wrong (owner: the band is "probably the thing that's most likely to be
wrong"), and it is the one the acceptance counts. It is also regime-dependent: on a source whose line TBC has
replaced the band's picture there is no timing to read and the band is found by the absence of picture instead
(contract §2). The two regimes are told apart per source and never from one field, and NOT by the RF peak, whose
sensitivity is about 3% (CLAUDE.md §11).

### 5. The RF peak
`rf_line`, `rf_x`, `rf_class`.

Contract §5 asks for the peak's line and its position along the line when present. Contract §2: the peak is a
spike at least four times the row's mean absolute difference at the same sample in both. `not_applicable` when
absent, which is the common case and says nothing about the source.

### 6. The span, the picture rows, the band count, and the closure
`span`, `picture_rows`, `band_extent`, `band_count`, `clip_line`, `closure`, `closure_class`.

Contract rule 3: the line account is conserved; the picture bottom is the row above the switch line; lines past
the clip are lost. Contract rule 2: the source's switch-line count is fixed, the top switch line is the only
variable one, and with the picture lower by d the band's extent is the count minus d.

Raw-row measurement: the picture bottom is the row above the switch line, taken from column 4 — never a luma or
recorded-black rule, which contract §3 records as falsified on the commercial capture. The band's extent is the
rows from the switch line to the clip. The clip line is the last recorded row, measured per source and never
assumed from the raster: it is line 262/525 on the commercial tape against 260/522 on fixture A (CLAUDE.md §11).
The closure is the conservation equation: lines added at the top equal lines lost below the clip. It is reported
as its residual, so that a failure is a number rather than a boolean.

### 7. The lock's switch-line count
`lock_count`, `lock_count_source`.

Contract rule 4: taken at the confirmed unit and kept until a reset, never re-learned; a unit that disagrees with
it is reported. The reference records the count it is holding and the unit that seeded it, so an engine that
re-learns is caught by comparison rather than by inspection.

### 8. The line-22 level comparator
`line22_level`, `line22_comparator`, `line22_count`, `line22_runner_up`.

Contract rule 4, the owner's mechanism of 12:52 and 12:55: a running count in a fixed array of eight slots;
counts never decrement; the most frequent value is the comparator and is replaced by a value whose count passes
it. Contract §3: the tape's black line 22 is located by the line account as the row below the located line 21,
and the comparator confirms that identity but never establishes the row by itself.

The reference records the comparator, its count and the runner-up's count, because contract §5 asks for exactly
that and because a comparator one count from being replaced is a different state from one that is settled.

### 9. The lock state, and every hold or reset with its cause
`lock_state`, `event`, `event_cause`.

Contract rules 5, 5b and 6. Every hold and every reset carries the cause that produced it, from the contract's
own vocabulary: a lock-like loss (snow-like signal or a vertical tear) resets everything, both fields at once;
damage that is neither holds with the previous geometry and the unit's position recorded Unknown; a transport
hole or short unit is damage, not a loss; a unit carrying a horizontal timing error other than its own head
switch may not be the confirmed unit.

### 10. The confirmations
`comb_shift`, `comb_class`, `body_shift`, `body_class`.

Contract rule 9: the comb confirms or vetoes; it never proposes a move. It is measured at the reference's OWN
placement, so that the acceptance question — does the picture land registered where this instrument put it — is
answerable without the engine. The body shift is recorded only when it was used.

## The four VBI signatures, stated as measurements

Each is a test on the row's own waveform against this unit's own blanking, with no typed level:

1. **CEA-608 waveform** — seven-cycle run-in at the standard phase, start bit, sixteen data cells at 1.986 µs,
   odd parity per byte. Amplitude gate 35 against the blanking, from the measured separation above.
2. **Run-in burst without data** — the run-in present and in phase, no start bit and no data. Measured on the EP
   recording as a vertical duplicate of the run-in, horizontally in phase (CLAUDE.md §11).
3. **The tape's line-20 timing pattern** — the same pattern as the Shuttle's regenerated line 20: a bright pulse
   at the far left and a wide pulse at about 80% of the line.
4. **The smeared XDS bar** — the frozen constant of CLAUDE.md §11: row mean < 95, a 48-bin luma profile whose
   bins 20–47 are all ≤ 40, and a run of at least six consecutive bins > 60 within bins 0–19. Its signature is
   its LEFT half only, which is the correction from the round-3 audit: the bar's right half can carry picture
   bleed, and demanding a quiet right half made the exclusion fail exactly where it was needed.

## The horizontal-phase profile, stated as a measurement

Every timing column above rests on one measurement, and it is the one the owner rejected a brightness rule in
favour of. Per row: register the row against the row above by exhaustive signed horizontal search over all 720
luma samples, split into a fixed set of apertures, fitting gain and offset per aperture first so that a dark row
and a bright row carrying the same timing give the same answer. Keep every aperture's signed lag and residual,
never their median: the sign and the left-versus-right split are the evidence, and a partial switch row is
exactly the case where only one side departs.

At the confirmed acquisition unit the ordinary picture rows define the source's own distribution of those lags,
and that distribution is saved with the lock and dies with it (contract §3, per source never fixed). A row is
Unknown rather than thresholded where its lag or its boundary is not unique, and a perfectly flat row carries no
phase information at all, so it is Unknown by construction and the conserved account handles the field.

The absolute alternative, from the standards, is recorded in the contract §2 and is not yet decided between:
an NTSC line is 858 samples at 13.5 MHz with 720 delivered, and horizontal blanking is 147 samples, so every
correctly timed line carries about nine samples of its own blanking inside the delivered window. Locating that
blanking measures a row's timing absolutely, with no reference to the row above. Codex's qualifier stands: the
standards guarantee the overlap, not that those samples are distinguishable from black picture.
