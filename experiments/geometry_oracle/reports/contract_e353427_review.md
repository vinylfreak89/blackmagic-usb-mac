# Contract e353427 independent review

Scope: the complete 217-line contract at engine revision `e353427`, read against the harness's existing raw-row audits and reference records; this is a specification review only, with no reference or code change.

## 1. My understanding

1. Each transport slot is measured in its own NTSC line coordinates, and a recorded row is distinguished from a Shuttle-regenerated row by decoder noise rather than by nominal position alone.
2. The picture top is the first recorded row that is picture after VBI rows have been excluded by their waveform signatures, including a dark first picture row when the locked geometry says it belongs to the picture.
3. The per-unit evidence record keeps the observed picture top, switch evidence, peak row and horizontal position, band extent, body shift, comb, captions, lock state, holds, and resets instead of collapsing them into one coordinate.
4. The reliable picture ends immediately before the switch line, while the expected active-picture extent still closes 240 lines from the top and may continue through a visible or clipped switch band.
5. A source's top-to-switch height and band count are learned online as running modal comparators, not supplied as capture-specific constants.
6. Each comparator uses eight fixed slots whose counts only rise, whose entries reorder only when their counts rise, and whose current value changes only when another count passes it.
7. Geometry is acquired only after an independent confirmation and is then held for that source and field precedence until a defined lock-like loss.
8. A counter discontinuity, signal-state relock or splice, vertical tear, or loss of regenerated rows invalidates the old source lock and resets its learned state immediately.
9. A temporarily hidden edge produces an explicitly labelled hold rather than a fabricated observation, whereas a genuinely unmeasurable raster carries no measured coordinate.
10. Head-switch evidence can be absent or not applicable, and neither state is equivalent to having observed a switch row.
11. The live crop follows the locked geometry so that the stabilized output picture remains stationary except at first acquisition, reacquisition, or a real boxing change.

## 2. Unclear, undefined, or contradictory text

### Geometry, confirmation, and lock

| quoted contract text | finding |
|---|---|
| “Everything else ... exists only to confirm that reading where geometry alone cannot decide” and “every other signal confirms or contradicts and is recorded, never acted on alone” | This conflicts with “a caption may place the very first unit” and with source lock being created by combing or captions, because those secondary signals necessarily affect a decision in those cases. |
| “No lock is claimed without confirmation (comb agreement between the fields, or clean, significant luma at the measured edge)” | This acquisition set conflicts with the definition “combing, captions, or both,” which omits edge luma and requires no VBI. |
| “Source lock: exists only after at least one confirmation ... combing, captions, or both” and “without a stable VBI there is no lock” | These statements disagree over whether comb alone can acquire lock and whether captions specifically, any stable VBI, or neither is mandatory. |
| “without it the picture stays at standard placement (23/286) and the record says there was not enough to lock on” and “without a stable VBI there is no lock and no geometry is claimed” | The document does not say whether standard placement is an applied crop with an unclaimed coordinate, a claimed provisional coordinate, or merely an output fallback outside the geometry record. |
| “Each field's active picture area — its top edge, bottom edge and height — measured on every unit” and “The conserved quantity is the line account, not the height” | Active-picture height, visible height, and the separately defined top-to-switch `Height` are three different quantities but share the word “height.” |
| “A raster whose edges cannot be measured at all is Unknown, held and labelled, never a substituted number” | The sentence does not separate the raw measurement (`Unknown`), the retained lock state, and the coordinate actually applied to the crop, so “held” and “never a substituted number” appear contradictory in a single field. |
| “No saved-geometry hold on absent evidence” and “Dropout or RF noise that hides an edge keeps the previous decision” | The boundary between forbidden absent-evidence memory and required hidden-edge memory is undefined. |
| “old geometry invalid, back to zero” and “No zero re-anchoring” | “Zero” is undefined and reads as a forbidden zero re-anchor unless it means only clearing an internal correction state. |
| “A change of geometry ... resets everything immediately” | The scope of “everything” is undefined, including whether one field's event resets both fields, precedence, both comparators, and source identity. |
| “Dropout or RF noise that hides an edge keeps the previous decision” and “the Shuttle's regenerated rows absent” is a lock-like loss | Absence of regenerated rows can also hide an edge, so the contract needs an observable rule distinguishing a hold from an immediate reset. |
| “stable VBI” | Stability has no defined observable, running-count state, or acquisition condition, and the deliberate absence of windows and unstated thresholds prevents an implementation from inventing one. |
| “clean, significant luma at the measured edge” | “Clean” and “significant” have no stated capture measurement or standard and therefore cannot be converted into a permitted test. |
| “a vertically torn raster” and “Horizontal tearing is not a geometry event” | No measured signature distinguishes a vertical tear from horizontal timing damage that changes down the raster. |
| “Segment events ... come from the signal-state layer as explicit inputs” | The event schema, field timing, and whether a reported splice resets before or after the associated unit are undefined. |
| “within a source” | “Source” has no operational boundary beyond the partly undefined lock-like-loss list, so comparator ownership across a continuous capture is not fully specified. |

### Top, switch, band, and line account

| quoted contract text | finding |
|---|---|
| “Picture top: the first picture row” and “It may be hidden by the Shuttle's overwrite blanking” | A hidden row cannot be measured as the first picture row in that unit, so the record needs separate observed, inferred, and applied tops and a rule for deriving the latter two. |
| “if the Shuttle's insert decodes captions on line 21, the real line 21 is somewhere between lines 20 and 22” | The relationship between a regenerated fixed-position insert and the inaccessible source-row position is not defined strongly enough to locate the hidden picture top. |
| “a bottom band that does not extend to the end of the frame ... is suspect that the top landed in the Shuttle's blanking” and “the band count alone never moves anything” | The band is simultaneously proposed as hidden-top evidence and forbidden from moving geometry, with no required second confirmation named for that case. |
| “confirmed when new luma that is neither blanking nor darkened picture appears at line 23 — every band's luma shifting about one row down” | The correspondence test for “every band's luma” and the distinction between darkened picture and black-line VBI are undefined and explicitly remain open in section 9. |
| “The head switch's position moves with the picture; its height is fixed; the top switch line alone travels by one row” | With a fixed picture top, a one-row switch-line travel changes top-to-switch height, so an observed travelling partial line must be separated from a locked switch line for all three clauses to coexist. |
| “The head switch band should not move” and “The head switch's position moves with the picture” | The first statement can mean invariant band height, while the second means absolute raster position, but the document does not say so at the point where it quotes the apparently absolute rule. |
| “The number of switch lines below the top line either stays constant or decreases” and “the most frequent value is the comparator” | The contract does not define how a value greater than the running mode is classified or whether the intended source quantity is a modal count or a maximum count. |
| “Band: the switch lines, counted from the top switch line including the partial line” | It is unclear whether censored rows past the clip are included in the observation fed to the comparator or only in closure bookkeeping. |
| “the band count under the lock” | The exact comparator input is undefined when the partial switch row, the first fully other-head row, and the last visible band row are different. |
| “S against the reference's first-full-other-head row ... and against its earliest switch-band row” | `S` and “first-full-other-head row” are used by acceptance but are not defined anywhere in this revision's definitions or mandatory record. |
| “the picture bottom is the row above the switch line” and “top + 239 is the expected bottom” | These are respectively the last reliable pre-switch row and the expected active-picture bottom, so calling both “picture bottom” leaves the crop and acceptance column semantics ambiguous. |
| “visible picture lines + lines added above the picture + lines lost into the deck's blanking at the bottom = constant” | The account does not state where picture-bearing switch-band rows belong or how a censored partial line is counted. |
| “the head switch is optional” | For a non-head-switch source, the contract supplies no alternate observed bottom-edge rule even though per-unit bottom geometry is mandatory. |

### Comparator, crop, and record semantics

| quoted contract text | finding |
|---|---|
| “Its level is a comparator by running count” | A row mean or level is not a discrete repeatable value without a stated quantization, while classifying a categorical first-row state would be a different comparator. |
| “a new value uses a free slot or replaces the least-counted slot when full” | The initial count of a new or replacement entry and the victim chosen among equally least-counted entries are not stated. |
| “equal counts do not change the ordering” | Initial ordering and the position assigned to a replacement are undefined, so two conforming fixed arrays can expose different comparators after the same observations. |
| “field precedence is settled once per lock and held” | Neither the measurement that settles precedence nor a required precedence field in the per-unit record is specified. |
| “boxed pictures are centred” | No raster statistic defines the box, its centre, or when a boxing change is real rather than picture content. |
| “The output picture never moves” | This must mean the picture is stationary after the crop offset moves, but the text never explicitly distinguishes output-picture motion from crop-coordinate motion. |
| “Provenance errors fail closed” | The failed state and its required output behaviour are not defined. |

### Deciding raw-row examples for the ambiguities

- SP recording units 77–79, field 1: the measured top stays L23 while the earliest unreliable row is L261, L259, L260; unit 78 has L258 at 86.505/35.583 and L259 at 51.759/42.515, while unit 79 has L259 at 89.139/37.349 and L260 at 50.380/44.699, so “fixed height” cannot directly mean the raw earliest-unreliable observation.
- SP recording units 103–104, field 1: top and earliest switch stay L23/L259, but the independently exposed first-full row changes L260→L259; counting L259 through the L262 clip gives four rows in both units, while counting the first-full row gives three then four, so the comparator's input materially changes the result.
- SP recording unit 105, field 1: top moves L23→L25 while the earliest switch moves L259→L262, with L23 carrying a caption, L24 at 4.219/2.978, L25 at 114.319/31.378, L261 at 96.428/36.515, and L262 at 29.202/43.077; this is the concrete case in which picture displacement and observed switch displacement differ and a single “height” cannot explain both without partial/censored state.
- Commercial-tape counters 6592–6593, both fields: both are spatially flat and the reference has no measurable top or switch in either unit, with field-1 L23 at 5.180/3.093 then 4.664/2.877 and field-2 L286 at 7.502/6.821 then 8.178/7.673, so the externally known stable-interval boundary cannot itself be derived from those raw rows.
- SP recording unit 87, field 2 versus commercial-tape counter 6672, field 2: SP L286 is 5.456/4.131 with picture beginning L287, whereas commercial L286 is 2.837/1.797 yet belongs to the stable picture geometry; a comparator over raw “level” cannot distinguish those cases without a defined state and contextual evidence.
- SP recording, V-stabilize off, units 20 and 200, field 2: L285 is overwritten blank at 1.380/0.485 and 1.392/0.488, and pulling the field down one raises comb energy, so a hidden-top rule cannot simply recover one more row whenever the lower band is longer.

### Numbers whose permitted origin is not stated

| quoted number | finding |
|---|---|
| “within the one-row partial ambiguity” | Section 8 does not identify a standard or a capture measurement establishing this acceptance tolerance or define which two row meanings it spans. |
| “units 300/301 and 43,737/43,738” | The fixture-A relock unit numbers are asserted as acceptance truth without stating the measurement or annotation from which they came. |
| “snow units 43,686–43,736” | The snow interval is asserted without stating the measurement or annotation that established its endpoints. |
| “Every render (two captures × two fields per frame ...)” | The two captures are not identified and the count conflicts with the four-capture scope used by the surrounding reference work. |
| “flagged first lines (120 units)” | Section 9 gives no census or source for the count of 120. |
| “under half the brightness of the three rows below it” | The document attributes this half/three-row gate to an owner ruling, but it is neither a stated capture measurement, a named standard, nor a memory capacity as required by the preamble. |
| “at least one confirmation” | The count is attributed to the owner but is likewise a decision threshold outside the preamble's stated numeric categories. |

All other operational numbers in the contract are either mapped to NTSC/CEA-608, explicitly labelled capture measurements, direct arithmetic from the 240-line field, or the owner-approved eight-slot memory capacity.

## 3. Build verdict and objections

**Verdict: no, not yet as an authoritative reference.**  The physical model is sensible, and the evidence record can be scaffolded from it, but the current text permits different correct outputs from the same raw rows in the following blocking cases.

1. **Lock acquisition is not a single rule:** edge luma, comb, captions, and stable VBI appear in three incompatible requirement sets, and counters 6592–6593 show why this matters because neither raw raster uniquely places the externally known boundary.
2. **The band comparator has no unique observation:** SP units 103–104 field 1 yield an invariant four rows from the earliest switch but three→four from the first-full row, so the choice changes the learned comparator and travel classification.
3. **Observed switch travel is conflated with locked height:** SP units 77–79 field 1 keep L23 fixed while raw switch evidence moves L261→L259→L260, so the record needs distinct observed-switch and height-projected-switch values plus a rule selecting the crop authority.
4. **Unknown, hold, and applied crop are conflated:** the specification simultaneously forbids substituted coordinates, requires a previous decision to be held, and says absent evidence has no saved-geometry hold, so it cannot state what coordinate is applied during an edge-hidden unit.
5. **The first-row comparator's value domain is missing:** the SP-unit-87/commercial-counter-6672 field-2 pair shows that similar low luma can be VBI in one locked geometry and picture in another, while a continuously valued luma mean cannot be counted without forbidden quantization.
6. **The lock-loss transition remains deliberately undecided:** section 9 asks whether a peak-present height change merely reports or resets, yet this choice controls whether all comparator state survives the unit.

## 4. Two measurements before implementation

1. Audit every peak-present top-to-switch-height departure across both aligned SP passes and the commercial stable interval, recording the peak row/x, earliest unreliable row, first-full row, top/body/comb displacement, regenerated VBI state, and the following units, to decide whether each departure is partial-line travel or a lock-loss reset.
2. On all 120 flagged V-stabilize-off fields and their aligned V-stabilize-on partners, compare L20–L26, the same-parity body, both field comb registrations, the bottom line account, and the luma correspondence of every visible band row, to decide both whether the flagged first line is picture and what observable confirms a top hidden under L23/L286.

## Conclusion

The contract has the right governing idea—preserve the measured evidence, learn bounded source state online, and stabilize only geometry—but its current lock, switch/band, and hold semantics are not yet deterministic enough for two blind implementations to be expected to agree.
