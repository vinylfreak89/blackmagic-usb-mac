# Contract af58588 independent review

Scope: the complete 257-line contract at engine revision `af58588`, including the owner-only disagreement ruling added after `8141c7a`; this is a specification review against the harness's existing raw-row audits and references, with no code or reference rebuild.

## 1. My understanding

1. Every unit retains per-field observations of the recorded region, VBI signatures, picture top, switch and RF evidence, band extent, body shift, comb, lock state, and any reason its own position is Unknown.
2. Geometry is the line account: recorded VBI or black rows above the picture are balanced against switch-band and remaining rows below it through the clip, including changes whose other side lies outside the raster.
3. The visible picture top is the first recorded non-VBI row, while a hidden top must be inferred from the above/below account and confirmed by the settled comb rather than by new luma alone.
4. The switch line is the partial row carrying the RF peak or tear, `S` is the first row entirely from the other head, and source height counts from picture top inclusively to switch line exclusively.
5. The reliable picture bottom is the row before the switch, whereas `top + 239` is the distinct 240-line closure endpoint and can extend past the clip.
6. Band count begins with the partial top switch row, source height is fixed within a lock, and band count, first-recorded-row state, and visible tape-line-22 level are learned online rather than supplied per capture.
7. The three enumerated comparators use fixed eight-slot, increment-only running-mode arrays, with integer values, stable tie order, and a ninth distinct value replacing the least-counted entry.
8. Lock requires the Shuttle's regenerated timing, insert, and blank rows plus at least one geometry confirmation from comb or caption evidence.
9. Comb is settled on static picture once per lock, establishes inter-field registration and precedence, and thereafter confirms or contradicts a displacement derived from the line account without directly correcting the crop.
10. Before lock the crop remains at standard placement, while a locked crop takes 240 rows from `23 + d` and `286 + d`, using legal black for rows beyond the clip.
11. Non-snow damage preserves learned geometry but leaves the crop where it was only because the damaged unit supplies no measured reason to move, whereas snow or another lock-like loss resets both fields and all learned state immediately.
12. Every mechanical engine/comb or engine/reference disagreement is listed by the harness with one engine-positioned woven bwdif image and handed to the owner, who alone adjudicates it.

## 2. Unclear, undefined, or contradictory text

### Geometry and lock

| quoted contract text | finding |
|---|---|
| “Past the raster bounds neither can be seen; the account counts them by the change in the ones that can” | The initial baseline and explicit equation that converts the observable above/below changes into displacement `d` are still left to the open hidden-top measurement. |
| “A picture movement seen in both fields is content, not displacement” | This needs to say “body-content movement,” because matching changes in both fields' measured top and below-picture account would instead be physical raster displacement under the rest of the contract. |
| “every other signal confirms or contradicts and is recorded, never acted on alone” and “a caption may place the very first unit of a segment” | A caption that places the first unit acts on placement, so the geometry candidate that it confirms in that special case is not identified. |
| “captions” | The lock gate does not distinguish valid decoded caption bytes from the presence or shape of the regenerated insert, which matters because commercial counter 6372 has waveform-like rows while geometry is unmeasurable. |
| “with the Shuttle's regenerated rows present” | The exact pass condition is unstated for a null insert, a damaged timing pattern, or regenerated rows present in only one field. |
| “Comb ... settled once per lock” and lock exists after confirmation by “combing, captions, or both” | The text does not say whether a candidate comb can simultaneously acquire and settle lock or only a comb following caption-acquired lock can confirm it. |
| “on static picture” | The static-picture mask and measurable/unmeasurable decision are unspecified, while section 6 forbids inventing a window or unstated threshold. |
| “thereafter a disagreement is the arbiter of rule 9” and “no comb correction of the crop” | The intended distinction appears to be that comb chooses between geometry-supported placements but never originates an offset, yet the exact action when it contradicts every supported placement is unspecified. |
| “a signal-state relock or splice” | The event schema and whether reset occurs before or after the associated unit remain undefined. |
| “a vertical tear (cross-program or true)” | No raw-row or signal-state signature distinguishes a vertical tear from horizontal timing damage or other non-snow damage. |
| “snow-like signal” | No observable defines snow-like classification before the rule uses it to reset both fields. |
| “the first observed value leads” | The comparator admission rule does not say whether observations made before lock, during acquisition, or in a held/Unknown unit are counted. |

### Top, switch, band, and comparators

| quoted contract text | finding |
|---|---|
| “Picture top: the first picture row” and “It may be hidden by the Shuttle's overwrite blanking” | The mandatory record still needs distinct observed, inferred, and applied top values because an invisible first picture row cannot be a direct per-unit observation. |
| “confirmed when new luma ... appears at line 23 — every band's luma shifting about one row down” | This earlier wording remains although rule 9 says new luma alone is insufficient and section 9 says the unbuilt two-sided account plus settled comb is the actual rule. |
| “Switch line: the horizontal line carrying the peak, or where the tear crosses into the other field or falls off the edge” and “Height ... fixed within a source” | The arithmetic now defines the projected switch as `top + height`, but the mandatory record still has only one switch field and does not separate that projection from the raw observed partial line. |
| “Height ... fixed within a source” and “The comparators are: the band count, the state of the first recorded row ... and the level of the tape's line 22” | Height is not an enumerated comparator, and no other rule says which observation establishes its fixed value or how competing observed heights are resolved at lock. |
| “a height change for any other reason than the peak disappearing is reported” | Peak disappearance does not specify whether the switch observation becomes Unknown, is inferred from peak continuity, or is projected from the height comparator. |
| “Band: the switch lines” | The signature that terminates the last switch line when the band does not reach the clip is not defined. |
| “the band count under the lock” | The contract does not state whether clipped/censored switch rows inferred through closure enter the running comparator alongside directly visible band rows. |
| “The number of switch lines ... stays constant or decreases” and “the most frequent value is the comparator” | A band count above the current mode has no required classification, and the text does not say whether it is an error, a new challenger, or a geometry event. |
| “the picture bottom is the row above the switch line” and “top + 239 is the expected bottom” | The definitions now distinguish the meanings, but section 1 still calls both aspects of the active-picture geometry “bottom edge,” so record column names must preserve “reliable bottom” versus “closure endpoint.” |
| “the row's luma mean rounded to a unit” | The sample aperture over which that mean is taken is unstated, so two implementations can produce different integer comparator values from the same row. |
| “a ninth distinct value replaces the least-counted entry” | The replacement entry's starting count is only implicit, and the normative text does not explicitly say that an evicted value's historical count is discarded. |
| “the comparators with their counts and the runner-up's counts” | The representation when no runner-up exists or the current unit has no admitted observation is unspecified. |
| “Not applicable (no head switch on the source)” | No alternative reliable bottom-edge observation is defined for a source with no head switch. |

### Hold, crop, and output

| quoted contract text | finding |
|---|---|
| “A raster whose edges cannot be measured at all is Unknown, held and labelled” | Rule 6 now makes the intended split clear, but this older sentence should say that geometry is held, the crop is merely left, and the unit's position remains Unknown. |
| “old geometry invalid, back to zero” and “No zero re-anchoring” | “Back to zero” remains undefined and should be replaced by reset-to-unlocked to avoid resembling the prohibited coordinate re-anchor. |
| “boxed pictures are centred” | No measured definition identifies a box, its centre, or a true boxing change. |
| “field precedence is settled once per lock” | The contract implies comb supplies precedence but does not explicitly state the mapping or require a precedence value in the per-unit record. |

### Acceptance and owner adjudication

| quoted contract text | finding |
|---|---|
| “Every disagreement is decided on the raw rows by both agents” and “Neither agent adjudicates these” | These are directly contradictory, and the later owner ruling must replace the former sentence rather than coexist with it. |
| “every true disagreement” | “True” cannot be known before owner adjudication, so the harness needs a mechanical inclusion predicate that reports candidates without deciding them. |
| “the engine's crop against the settled comb, the two instruments against each other on a unit” | The contract does not say whether the defined one-row switch semantic gap, Unknown-versus-number cases, and unmeasurable combs are reportable disagreements or exclusions. |
| “one rendered frame ... deinterlaced with bwdif” | The required artifact lacks a specified field order, bwdif output parity/time, handling of unavailable crop rows, and deterministic filename mapping to counter and unit. |

### Deciding raw-row examples

- SP recording units 77–79, field 1: picture top stays L23 while the earliest unreliable row is L261, L259, L260; at unit 78 L258 is 86.505/35.583 and L259 is 51.759/42.515, while at unit 79 L259 is 89.139/37.349 and L260 is 50.380/44.699, so raw switch evidence and height-projected switch geometry require separate values.
- SP recording units 103–104, field 1: top and earliest switch remain L23/L259, but independently exposed `S` changes L260→L259; beginning the count at the partial row is invariant while beginning at `S` changes, confirming that the revised partial-row definition is necessary but leaving band termination/censoring to specify.
- SP recording unit 105, field 1: top changes L23→L25 and earliest switch L259→L262, with L23 carrying a caption, L24 at 4.219/2.978, L25 at 114.319/31.378, L261 at 96.428/36.515, and L262 at 29.202/43.077; the above count grows by two while raw switch evidence moves by three, making this the deciding unit for projected switch and peak-present height handling.
- Commercial-tape counters 6592–6593, both fields: both raw rasters remain spatially flat and unmeasurable at the externally known boundary, with field-1 L23 at 5.180/3.093 then 4.664/2.877 and field-2 L286 at 7.502/6.821 then 8.178/7.673; the revised rule sensibly keeps standard placement without claiming geometry until its regenerated-row and comb/caption gate passes.
- SP recording unit 87, field 2 versus commercial-tape counter 6672, field 2: SP L286 is 5.456/4.131 with picture beginning L287, while commercial L286 is 2.837/1.797 inside stable L286 picture geometry; the newly separated categorical state comparator resolves the old conceptual conflict, but the numeric line-22 mean still needs a common sample aperture.
- Commercial-tape counter 6372 has waveform-like rows at L21/L24/L26 in field 1 and L284/L287 in field 2 while both picture tops are unmeasurable, so caption validation cannot mean waveform presence alone if it may acquire lock.

### Numbers whose permitted origin is not stated

| quoted number | finding |
|---|---|
| “a 55-sample segment” | The segment-lag aperture has no cited standard or capture measurement and is not a memory capacity. |
| “units 300/301 and 43,737/43,738” | The fixture-A relock coordinates remain acceptance assertions without a cited measurement or annotation. |
| “snow units 43,686–43,736” | The snow endpoints remain acceptance assertions without a cited measurement or annotation. |
| “Every render (two captures × two fields per frame ...)” | The two captures remain unidentified and conflict with the four-capture reference scope. |
| “rows doubled” | This render scale is neither a named standard, a stated capture measurement, nor a memory capacity. |
| “flagged first lines (120 units)” | Section 9 still provides no census or source for 120. |
| “under half the brightness of the three rows below it” | The half/three-row gate is attributed to an owner ruling but does not belong to the preamble's allowed standard, capture-measurement, or memory-capacity classes. |
| “at least one confirmation” | This is attributed to the owner but is a decision count outside the preamble's three allowed numeric origins. |

The one-row `S`/partial relationship is now defined rather than an unexplained acceptance tolerance, the ninth value follows directly from the eight-slot memory capacity, and the newer one-frame/two-field image requirement has an explicit owner-ruling origin.

## 3. Turn-14 blocker resolution and build verdict

| turn-14 blocker | status in revision af58588 |
|---|---|
| Lock acquisition | **Resolved in substance:** regenerated timing/insert/blank rows plus comb or validated caption evidence form one gate, with only the exact caption/regenerated-row tests left to measurement. |
| `S` | **Resolved:** `S` is explicitly the first row entirely from the other head, with the switch in `S` or its partial predecessor. |
| Band comparator input | **Partly resolved:** it starts at the partial switch row, not `S`, but the last-band and censored-row admission rules remain unstated. |
| Observed versus projected switch | **Partly resolved:** exclusive height makes `top + height` unambiguous, but the record does not name raw and projected switch separately, select the fixed height at lock, or say which value survives peak disappearance. |
| Hold semantics | **Resolved:** learned geometry persists, the damaged unit's position is Unknown, and the crop is merely left because no measurement authorizes movement. |
| First-row comparator | **Resolved in substance:** categorical first-row state and rounded visible-line-22 level are now separate comparators, with only the luma sample aperture unspecified. |
| Height-change reset | **Unresolved by design:** section 9 still asks whether a peak-present height departure reports only or resets both fields. |

**Verdict: yes with the listed objections.**  The contract now supplies a sensible and mostly deterministic reference model, but implementation should not claim completion until the following points are resolved or represented explicitly as open states.

1. **Raw and projected switch coordinates must be separate:** SP units 77–79 and 105 field 1 prove that raw partial-line evidence can move independently of locked height.
2. **The fixed source height needs an acquisition rule:** unit 105 field 1 differs from unit 104 by two top rows and three raw switch rows, while the contract's exact comparator list excludes height.
3. **Band termination and censored admission must be normative:** SP units 103–105 field 1 otherwise permit different comparator streams from the same rows.
4. **Peak-present height handling must be measured before state transitions are final:** unit 105 field 1 is a deciding example, and section 9 intentionally leaves report-only versus reset open.
5. **The old both-agent adjudication sentence must be removed:** the later owner ruling controls, so the harness reports every mechanically qualifying candidate and the owner alone decides it.
6. **The disagreement frame recipe needs deterministic conventions:** until parity/time, unavailable rows, and filenames are fixed, two harness runs need not hand the owner the same bwdif evidence artifact.
7. **The 55-sample segment aperture must receive a permitted origin or be replaced by a standard/measured value:** otherwise an implementation would violate the contract's opening numeric rule.

## 4. Two measurements before implementation

1. Measure every peak-present height departure across both field-aligned SP passes and the commercial stable interval, recording top, raw partial switch, `S`, projected switch, peak row/x, visible and censored band rows, body/comb displacement, regenerated-row state, and following units, to decide report-only versus reset and lock down band admission.
2. Measure all 120 flagged V-stabilize-off fields against their aligned V-stabilize-on source fields, comparing L20–L26, the complete same-parity body, both field comb registrations, and every bottom-band row, to decide whether the top reads through flagging and to construct the hidden-top line account required by section 9.

## Conclusion

Revision `af58588` is sensible to build from once its explicitly open measurements are made: it now defines the core geometry, lock gate, `S`, height arithmetic, comparator domains, reset scope, damage behavior, crop, and owner-only review path, while the listed switch/band details and acceptance wording should be corrected before calling two blind outputs comparable.
