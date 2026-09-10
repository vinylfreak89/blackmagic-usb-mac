# Frozen independent contract review

Reviewed file: `/tmp/contract-review.lcdyuA/contract.md`, all 1,017 lines.

Source SHA-256: `62ba541cf019ab561ce9a55037d00e9df24ec489fd83bd138521b71b42f79597`.

This is an internal-coherence review, not a pass/fail decision and not a review of implementation or physical correctness. All cited evidence comes from the supplied file. References below are to its numbered lines. No referenced repository document, code, transcript, git data, or web source was opened. The source document was not edited.

Isolation limitation: automatically supplied conversation context included extensive repository instructions and project measurements for `/private/tmp/blackmagic-v10`, plus environment and skill metadata. I therefore cannot claim a context-free blind review. I did not manually read those instructions from another file, and have not used their claims as evidence for any finding here. This review was derived without seeking or receiving another reviewer's findings.

Severity means consequence if two implementations follow the competing readings: High affects placement, loss accounting, or core mathematical validity; Medium affects a decision, validation scope, or an operative rule; Low is a narrower scope/documentation inconsistency. A missing identification method is not treated as evidence that identification is impossible.

## Findings

### CR-01 — High — The operative coordinate/provenance table was not migrated with the coordinate rule

Evidence:

- Lines 7–10: “both fields' pictures are lines 23-262”; old field-2 numbering “is withdrawn.”
- Lines 180–186: each block contains “240 picture (23-262)”; field 1 alone has an extra written `262.5` row, and the following row is field 2's written line 1.
- Lines 318–325: the measured table still labels field 2 with `274–282`, `283`, `284`, `285`, and `286–526`; it calls unit rows `19–260, 282–522` “pass-through from the tape and deck.”
- Lines 631–632 and 935–938 retain operative crop formulas/ranges using `286` and `283–525`.

The problem is more than old display labels. Using the document's own row mapping at lines 8–9, 240 picture rows occupy unit rows 19–258 and 282–521. The block description makes rows 259 and 260 written rows, and puts the next field-1 written line 1 at row 522. The table includes all three in its source/pass-through range. An implementation taking the table as provenance truth can therefore classify written rows as source data. Explicitly historical examples may retain old labels, but the table and live crop definitions are not marked historical. This is a direct internal conflict; the warning about unconverted code at lines 25–28 does not identify the table itself as obsolete.

### CR-02 — Medium — An implementation gate remains after the declaration that those gates were removed

Evidence:

- Lines 87–92: procedural authorization gates and another agreement round before classification code “are REMOVED”; “nothing should be gated.”
- Lines 173–174: a correction is owed from the owner and “nothing is implemented against this ruling until it lands.”

These are conflicting workflow instructions within the same dated section. The latter is expressly an implementation prohibition, not an Unknown measurement outcome or an evidence qualification. A possible reconciliation is that the removal applies only to the earlier cutoff study and not to this particular ruling. The broad wording does not state that exception, so an implementer cannot tell whether to proceed with the head-catch rule or defer it. This finding does not treat the separate acceptance order at lines 138–139 as automatically repealed.

### CR-03 — High — Accepted head-catch movement is incompatible with the unqualified count equations and acceptance invariants

Evidence:

- Lines 150–155 and 162–172: temporally sound movement by a line or two is neither a hold nor a geometry change; output does not move; observed counts of 2 or 4 should hold at the established 3.
- Lines 515–526: `d = switch-line count − band's extent`; the two readings of `d` “must agree.”
- Lines 673–680: the switch position moves with the picture, and other count changes are reported.
- Lines 792–793: the switch-line count may expand when the partial was absent initially, “accepted rather than a fault.”
- Lines 923–925: the switch line “moves only with the top and only within the partial line's one-row travel.”

For the newly accepted event, the picture top can remain fixed while the first affected row and observed extent change. Substituting that changed extent into the unqualified equation changes `d`, exactly what the new rule forbids. The one-row invariant also excludes a literal two-row event allowed above. A raw measured boundary/count and a normalized geometry boundary/count could reconcile these requirements, but the definitions and record fields do not establish those distinct quantities or specify which feeds the equation and invariant. The missing temporal margin is an additional specification need, not proof that temporal qualification is impossible. Severity is High because the competing readings either move a picture that must remain still or reject an explicitly accepted event.

### CR-04 — Medium — The TBC definition simultaneously preserves and removes displacement

Evidence:

- Line 468: “it removes the PICTURE, not the displacement.”
- Lines 474–476: “Corrector on: the displacement is gone and so is the picture”; no side-versus-side step is found.
- Lines 479–486: visible skew is “not a timing skew,” and those rows “cannot be identified from timing at all”; identification instead uses absence of picture.

The heading and its explanatory bullets directly disagree about the same corrected state. The bullets may mean observable displacement is gone while some underlying timing displacement survives, but the document does not make that distinction or provide evidence for it. A reader following the heading will expect a timing measurement that the body explicitly says is unavailable. The heading should either describe the body's measured result or explicitly name a different quantity; this review does not adjudicate the physical claim.

### CR-05 — Medium — The recorded-row definition promotes a fixture threshold that the per-source rule forbids as a test point

Evidence:

- Lines 392–395: a recorded row is detected by chroma noise “above twice the blanking rows'”; “the 2.0x test sits inside that observed gap.”
- Lines 400–407: levels are established at runtime for the current source, not carried by a contract value or calibration file.
- Lines 444–453: the horizontal timing and level references are per recording; “the numbers quoted in section 2 are measurements on these captures, never test points.”

The definition explicitly makes a test point out of the section-2 observed separation. Scaling by current blanking noise makes the ratio relative, but does not make its cutoff a newly measured separation for the current source. A permissible reconciliation would be an expressly qualified universal ratio, or a source-derived boundary whose example happened to be 2.0. Neither is what the present definition says. This is an operative policy conflict; it does not establish that 2.0 is physically wrong on the measured captures.

### CR-06 — High — Provenance errors suppress records, while damage and rendering require a record at that unit

Evidence:

- Lines 535–537: incomplete packet accounting at a unit is a provenance error; “the engine emits no record for it.”
- Lines 705–709: a transport hole or short unit is damage, and “the unit's own position is recorded Unknown.”
- Lines 876–884: the per-unit record carries lock state and every hold/reset and its cause.
- Lines 966–971: alignment requires exactly one video frame per sidecar row from the first row; an earlier silent label offset motivates refusal of any other alignment.

A transport hole falls under both the no-record instruction and the Unknown-damage-record instruction. If its video frame remains but its sidecar row is omitted, the alignment requirement is also broken. A separate transport layer could supply a keyed placeholder record, or the renderer could omit both frame and sidecar entry while preserving explicit counter gaps, but neither interface is specified here. The issue is not that damaged content must be measured: it is that “no measurement” and “no unit record” have different consequences, and the contract currently directs both. This affects the integrity of the audit and review alignment.

### CR-07 — High — The line-account identity silently fixes a clip line that the definition says is measured per source

Evidence:

- Lines 516–517: band extent runs from the top switch line to the clip, inclusive.
- Lines 525–531: span is from line 23 to the row before the switch line, and equals `240 − band's extent`; the clip is the deck's last delivered row, “measured per source ... never typed in.”
- Lines 532–533: closure is 240 lines, while rows past the clip are lost.

Let `S` be the top switch line and `C` the measured clip. The definitions give `span = S − 23` and `extent = C − S + 1`, hence `span + extent = C − 22`. The asserted identity `span = 240 − extent` therefore requires `C = 262`. No condition on these equations states that every source's measured clip must be 262, and the definitions explicitly distinguish actual delivery from lost rows. For any other clip, either a virtual missing-tail term or a different extent definition is required. This is a conditional algebraic inconsistency, not a claim that the measured fixtures have a non-262 clip. Its severity comes from using the account as displacement authority across sources.

### CR-08 — Medium — Reference rebuilding is ordered after reacquisition even though reacquisition requires those references

Evidence:

- Lines 417–423: before required source references are qualified, registration and corrective placement are inactive; observation/reference acquisition continue.
- Lines 444–453: timing and level references belong to the current lock, are discarded by a lock-like loss, and “are rebuilt from the units after re-acquisition.”
- Lines 668–672 and 682–685: geometry plus independent confirmation licenses acquisition; only a lock moves the rendered placement.

Read literally, source-lock reacquisition must precede rebuilding references that warm-up requires before registration can resume. The document already provides the components for a coherent order—observe, rebuild references, propose geometry, confirm, acquire—but the “after re-acquisition” wording reverses the first and last stages. If that occurrence means signal reacquisition rather than source-lock acquisition, the dependency can be reconciled by naming it. This is a lifecycle-order ambiguity, not proof that reference acquisition is impossible, and not an assertion that every geometry reset must be a full-engine reset.

### CR-09 — Medium — Per-unit comb validation is not scoped against the explicit acquisition-only comb rule

Evidence:

- Lines 640–655: comb measurement occurs only during acquisition/reacquisition; under maintained lock it “does not run at all” and the record says `COMB NOT EVALUATED`.
- Lines 830–836: the obligation for the settled comb to agree again at a moved crop is explicitly withdrawn.
- Lines 876–883: the section is “Measured every unit, per field” and includes the engine's comb confirmation.
- Lines 916–925 and 983–998: acceptance checks comb on engine crops, the settled comb is an authoritative measurement, and a crop-versus-comb disagreement gets a per-unit comb-labelled frame.

There is no necessary contradiction if the engine records `NOT EVALUATED` under lock and an independent harness performs additional retrospective comb measurements. But the acceptance language does not clearly assign that exception to the harness, distinguish a historical settled value from a fresh reading, or state how locked units with no engine comb value are compared. Implementers can reasonably produce different validation coverage or accidentally reintroduce the withdrawn running engine check. This is a scope/interface omission rather than evidence that a comb cannot be measured independently.

### CR-10 — Medium — The box/bar gap history leaves the operative switch-measurability predicate ambiguous

Evidence:

- Lines 754–765: the box includes its bars, and only an intervening source-blanking interval defeats contact with the switch.
- Lines 770–777: a switch separated from picture by a gap “is not measured”; darkness/absence of content is not a gap; a boxed source's switch is measured like any other.
- Lines 805–810, under the “History — superseded wordings” heading at line 796: the old answer that card-to-switch rows count as a gap still “establishes why those rows separate CONTENT from the switch for the purpose of measuring the switch against picture.”

The history paragraph continues to assign measurement significance to the content-to-switch separation that the operative paragraph says must not make a boxed source unmeasurable. A coherent reading is available: box contact concerns its outer edge, while bars can hide a lift-off landmark without disabling all other switch measurements. The text does not state that reconciliation, and “not measured at all” versus “for the purpose of measuring” invites a different reading that disables the boxed switch again. The finding is a misleading history/operative boundary, not a claim that dark bars and source blanking are inherently inseparable.

### CR-11 — Medium — The definition of a picture row includes rows that the switch definition explicitly excludes

Evidence:

- Lines 392–398: recorded rows are source/pass-through rows identified through decoder noise or luma.
- Lines 424–436: VBI rows carry specified vertical-interval waveforms; tape line 22 is separately located through the account.
- Line 437: “Picture row: a recorded row that is not a VBI row.”
- Lines 501–502: the deck's TBC-created black switch rows “are band rows, not picture.”
- Lines 351–353 and 681: the partial switch row is also excluded from picture; the picture bottom is the preceding row.

Source-derived head-switch rows need not carry any of the defined VBI signatures, so the broad picture-row definition includes them while the switch definition excludes them. Geometry can impose an ordering that resolves the classification, but that ordering or exclusion must be part of the definition to avoid two valid-looking row censuses. This matters particularly when a detector uses “first picture row” or counts picture rows before establishing the switch bounds. It is a definitional conflict, not an argument that every recorded non-VBI row must be visibly useful content.

### CR-12 — Medium — “Picture within the held bounds” can invalidate the very box that contains ordinary picture

Evidence:

- Lines 734–742: box geometry is held, but “Picture positively established WITHIN the held bounds also invalidates the box.”
- Lines 743–755: bars are recorded picture rows inside the 240; “The box INCLUDES ITS BARS”; bounds are outer box bounds, not just content bounds.
- Lines 857–865: remeasurement is triggered by actual picture appearing in “previously established letterbox-like bounds” or “letterbox-like area bounds.”

If “held bounds” means the box's stated outer bounds, normal existing content lies within them and would invalidate any valid box. The likely intended trigger is newly established content inside a region previously identified as a bar, not content anywhere inside the box. The narrower phrase in rule 12 supports that reconciliation, but rule 8a neither names that subregion nor states the novelty condition. This is a consequential bounds-definition ambiguity, not an assertion that boxes cannot be held or remeasured.

### CR-13 — Low — The blanket prohibition on windows contradicts the required local timing window

Evidence:

- Lines 347–350: timing variance is measured “over a local window of rows, never whole-field.”
- Lines 534–536: a segment has a measurement aperture, explicitly distinguished from a decision constant.
- Lines 888–891: the engine has “no windows.”

A plausible intended prohibition is on arbitrary temporal smoothing or historical decision windows, while allowing spatial measurement apertures. The prohibition does not say that. This is a narrow scope inconsistency that can be fixed by naming the prohibited kind of window; it does not justify abandoning the explicit local timing measurement.

## Qualifications and resolved tensions not counted as findings

- The file explicitly acknowledges the missing timing-identification method at lines 115–123 and protects unresolved cases with `Unknown` at lines 46–49 and 94–113. That is unfinished method qualification, not a logical impossibility or a license to use position alone as identity.
- An observed switch in one field and `Unknown` in the other does not prove a broken source: lines 566–572 explicitly require positive absence. I found no contradiction merely from optional switch evidence and this bilateral-validity rule.
- General source lock uses geometry plus comb or qualified captions, not head switch as an independent second observation (lines 546–556). Earlier head-switch-confirmation wording at lines 209–216 is redirected to that definition; its presence as explicitly superseded history is not by itself another contradiction.
- Regenerated-row absence and lock-like loss have expressly different reset scope in lines 702–713 and 867–874. Those scopes are not automatically inconsistent merely because both discard geometry. CR-08 concerns rebuilding order, not an inferred requirement to collapse the reset classes.
- Holding committed geometry through a fade is compatible with observing the fade and remeasuring after it completes (lines 857–866). Remeasurement need not itself change geometry.
- The general ban on rendering the tape's own line 22 need not contradict the 486-line review output displaying device-generated inserts; the document distinguishes tape and generated rows. I have not counted those different outputs as a conflict.
- The compositor and filter claims have not been checked against code, standards, or external documentation. The file itself qualifies visibility guarantees at lines 979–984, so I have not inferred an unconditional guarantee of visible comb from the surrounding explanation.

## Aggregate

13 findings: 4 High (CR-01, CR-03, CR-06, CR-07), 8 Medium (CR-02, CR-04, CR-05, CR-08, CR-09, CR-10, CR-11, CR-12), and 1 Low (CR-13). No Critical finding.

This artifact freezes the complete review before any findings are reported outside it. No source edits or tracked-file changes were made.
