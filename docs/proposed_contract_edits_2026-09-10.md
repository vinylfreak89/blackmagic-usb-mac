# Proposed contract changes — 2026-09-10

**For approval. Nothing here is in `docs/geometry_first_engine.md` and no code has been written to
it.** This is a single statement of what each rule says after the day's rulings, in the contract's own
order. Where a rule needs an instrument that does not exist yet, that is a fact about the code and is
tracked in `docs/v10_pending.md`, not a qualification on the rule.

---

## Section 2 — what the captures show

### The head switch is the unstable timing region

"Head-switch region" names the affected region where the other field's horizontal timing intrudes
into this field.

> "I'M DEFINING THE HEAD SWITCH AS basically where the other fields horizontal timing gets into the
> wrong field. that is not technically 'the head switch'. the head switch is the RF peak/half line.
> whereas I'm basically just defining it as the unstable timing region"

The partial line and the RF peak are possible landmarks within or at its boundary. Their absence does
not establish absence of the region. This does not broaden to any unstable timing: ordinary horizontal
tearing and departure-and-return keep their existing distinctions, and a region-based definition does
not remove the need to identify timing evidence rather than merely dark content.

### A line-TBC-corrected pass is not a switch-free source

> "just because a partial line isn't there, as in the TBC captures, that doesn't mean there is no head
> switch. the horizontal skew at the bottom of the frame is evidence of a head switch."

The absence of a partial line is not the absence of a switch, and the skew below the picture is
positive evidence of one. The head switch remains optional as a category — "not applicable" stays
distinct from "unmeasurable" — but no capture in this project is known to be switch-free.

---

## Section 3 — definitions

### Source lock

**A lock is valid geometry, which may include a switch, plus the comb or captions.**

> "it should be comb OR caption. valid geometry which may include a switch plus comb or captions,
> ideally both"

Both is preferred. This is rule 4's independence requirement stated concretely: geometry and the comb
are two independent observations; geometry and captions are two; all three is better.

**The head switch is an input to the geometry, not one of the confirmations.**

> "right because the head switch participates in the geometry decision. I've been considering it one of
> the 3 but its not really"

Head-switch evidence used to establish geometry cannot be counted again as an independent confirmation
of that geometry. A source lock therefore does not require head-switch evidence, and acquiring one
without it does not manufacture a switch count: an unmeasured count stays Unknown and every
count-dependent deduction stays unavailable with it.

**A caption that confirms a lock is the tape's own, off the insert, with sound VBI semantics.**

> "locking on comb plus captions does not require a head switch if the caption lock followed proper VBI
> semtantics. ie, it was not over top of the shuttles 20,21,22 and line 22 was properly blanked, and
> line 21 carried the proper caption data, not some weird skew."

The caption qualifies when it is outside the Shuttle's overwritten lines 20-22, the tape's following
line 22 is properly blanked, and line 21 carries proper caption data rather than a skew artefact.

**Decoded caption data at the regenerated insert supplies no geometry or confirmation evidence.**

> "no the regenerated insert shouldn't count as anything"
>
> "but whether they can decode captions, that could mean the real captions are anywhere from 20,21,22
> so that should say nothing about geometry"

A successful decode at the insert does not locate the tape's caption line and contributes no geometry
evidence, no corroboration and no tiebreak. Its bytes may be recorded as observations; recording them
is not using them as confirmation.

**A head switch present in one field and absent in the other is a broken source.**

> "a head switch can't be in only one field... again ... PHYSICS. a source with a head switch (or signs
> of one) in only one field is garbage. fail open. do nothing (or hold if you already acquired a lock)"

Positive evidence that the region exists in one field and is absent in the other prevents correction:
with no lock, make no corrective placement; with a lock, hold the placement already applied, which
neither resets nor reacquires it. A measured region in one field and Unknown in the other is one
measurement and one abstention — it does not establish this asymmetry.

### The comb

Comb measurement and picture-preserving alignment selection occur during acquisition and
reacquisition.

> "no it does not override rule 9. that is the lock, either initial or reacquisition. when a source is
> locked, then its geometry is known, comb should not need to run and field geometry shifting obviously
> is going to move the same way comb detection works. so comb should not be an all the time running
> thing."

Under a maintained lock the comb is not measured, and transient combing alone does not initiate an
adjustment. Where an alignment is selected, the preference is to shift the combed field down rather
than move its partner up — unless that fails to resolve the comb — the governing aim being to preserve
observed picture.

> "If combing happens, it should shift the combed field down not its partner up, unless that won't
> resolve the comb"; "you prefer the one that doesn't lose picture"

A confirmation disagreement is recorded explicitly. A rejected candidate does not authorize acquisition
or move the rendered placement. During acquisition or reacquisition, alternative alignments may be
evaluated under the picture-preserving preference; an alternative is applied only after it satisfies
the lock requirements.

### The box

A box must be **bounded**. A structureless band at one end only is not a box: that is full picture.

> "no it doesn't need to open up to a full picture. it can open up to whatever is on the screen. but it
> must be bounded. only one side of the picture isn't a box thats full picture."

Failure to detect a second bound is not positive evidence that only one exists; that stays Unknown.
"Full picture" does not by itself establish displacement or authorize a lock.

The box's extent is measured while the picture is well exposed and is then held. A fade shows as the
picture's overall level falling while the band edges stay put in the rows that still read, and it never
invalidates anything: a band edge that appears to move because the picture dimmed is exposure-dependent
detectability, not a release. A band edge moving while the level is steady does release the geometry.

Picture positively established within the held bounds also invalidates the box. Replacement geometry is
then measured — it opens to whatever is on the screen, not necessarily to full picture and possibly to
another box; invalidating the old box does not itself establish its replacement.

The box includes its bars. Where a head-switch region is present, the box's lower outer boundary must
meet it without an intervening source-blanking interval: "if the box doesn't touch the head switch, then
its not valid geometry. simple. basically if there's a blanking interval that sits between the box and
the head switch thats garbage." A demonstrated intervening interval prevents a new acquisition; an
unresolved boundary does not establish contact. This contact requirement does not make head-switch
evidence mandatory on a genuinely switch-free source, and failure to measure a switch does not establish
that the source is switch-free.

### Levels, and what blanking means

Levels are measured per source, at runtime.

> "do not take numbers that are in the programs own measured thing as gospel. once again, NO MAGIC
> NUMBERS. measure things per source. there is obviously going to be a source measured levels section."
>
> "not measure it as a static to put in a file. measure it when a source is first acquired."

The engine establishes, for the source in front of it, what blanking is, what black is, and where
generated fill sits. No contract value, header constant or calibration file carries them. Source
blanking, source black and device-generated fill stay separately identified: their measured levels may
coincide on a given source without their roles becoming interchangeable.

The blanking reference is established from qualified blanking intervals on the current source's good
picture lines, and supplies both level and variability.

> "the CORRECT thing to do is find the blanking on the good lines of picture, thats your blanking
> interval the head switch needs to be measured inside of... we aren't following a source standard. we
> are following SOURCES WE ARE CORRECTING."

Nominal standard timing does not establish it and device-generated fill never establishes it. The same
reference serves the head switch's horizontal extent and the black of the invalid-raster test below.

What is measured against that reference is departure from it in either direction: "It should be measuring
where the blanking is overwritten. So if the blanking extends past its expected horizontal extent or the
picture extends past its expected horizontal extent, that's the head switch." The expected extent is the
source's own, remeasured after the transition events below, never the nominal figure.

### Warm-up

Before the required source references are qualified, registration and corrective placement are
inactive. Observation and reference acquisition continue.

> "the engine can't run on a fresh source until it 'warms up' which means on capture 1, the loss like
> noise bars during the fade, the entire engine can't run. that is accepted and expected."

This is intended behaviour at capture start and after every full engine reset. Following reassessment,
any required reference that is no longer qualified must be reacquired before registration resumes.
Elapsed time alone does not complete warm-up, and completing it does not itself supply geometry
confirmation or a lock.

### Lock-like loss, and the invalid class

Lock-like loss is snow-like signal, a vertical tear, and a signal-state relock or splice. It resets the
geometry and the engine continues.

**The invalid class is separate.** A raster in it is not valid NTSC: the engine does not register and
does not correct. Two conditions put a raster there.

**The regenerated rows absent.**

> "if they are gone, then the picture is truly unlocked, not lock like loss. it is not a valid NSTC
> picture. period"

Their presence is evidence the decoder has sync, and serves device-state monitoring; it contributes
nothing to geometry. Their absence must be positively established — a failed caption decode is not
absence, and samples unavailable through transport damage are not absence.

**A trailing black run of more than 24 lines with no unstable-timing region in it.**

> "if there are more than 24 lines of black with no head switch, just pure fucking black at the end, its
> an invalid raster. straight up"
>
> "its blanking. they need to figure out what blanking means. deck blanking, chroma, etc, I simply do
> not care."

The condition is a conjunction: **more than 24 qualifying terminal lines, AND positively established
absence of the unstable-timing region within them.** Unknown switch evidence does not satisfy that
absence. The black is measured against the source's own blanking reference above. His rationale for the
number: "the 24 has nothing to do with what the fuck is delivered. it has to do with 262.5 + 24 = 23.5,
ie PICTURE." Either field meeting the condition disables the registration engine: "if EITHER field does
that, then the registration engine should not operate."

Legitimate picture meeting the condition also disables correction, and that cost is accepted: "that
means that a letterboxed picture might fail open on a truly noiseless source which is whatever."

---

## Section 4 — rules

### Rule 1 — geometry proposes, confirmation locks

> "Geometry is a guess not a lock. A comb safe and/or caption safe/VBI ... result or adjustment make it
> into a lock. Only after lock does it move the rendered frame's location."

Geometry supplies a candidate; independent confirmation licenses acquisition; unconfirmed candidates do
not move the output. A source that never locks holds its picture unmoved, which is correct: "rather
fail closed than fail open."

### Rule 4 — independence

A lock is acquired on two or more independent observations, at least one of which is geometry. Evidence
used to establish the geometry cannot also serve as the confirmation of that geometry.

### Rule 9 — the locked state

Under a maintained lock the engine tracks geometry and does not measure the comb. A settled comb is not
re-measured at a moved crop.

### Re-measurement

Mute, fade, and actual picture appearing within previously established letterbox-like bounds trigger
reassessment of the source reference and the affected geometry.

> "not just a transition event, mute or fade. if the boxed geometry becomes invalid, then it should
> reset as well. mute fade, or actual picture appearing in the letterbox-like area bounds"

During a fade, committed geometry is held while observation continues to establish the transition and
its completion — "geometry (including the box) can't change during a fade. that must be a hold" — and
remeasurement follows completion: "IF IT CHANGES which really can only happen after some type of
transition event (mute or fade), remeasure." Post-transition remeasurement does not itself establish a
geometry change.

Positively established box invalidation releases the affected geometry and its lock; replacement
geometry requires acquisition. Evidence dependent on invalidated geometry cannot support acquisition
without renewed qualification. A positively established change of geometry resets the lock,
including a change between boxed and full-picture geometry. Ordinary displacement tracked under a
maintained geometry is not itself such a change.

### Full reset

> "its not just that it resets the lock. it should reset everything. losing those lines means the entire
> registration engine should reset as if the capture is brand new"
>
> "it resets the registration engine full stop (obviously keeping its unit counts but any derived locks,
> timings, etc)"
>
> "if they get `0x0800` or lose the regenerated lines, they go get it again"

`0x0800`, or positively established absence of the regenerated rows, resets the registration engine full
stop. Everything the engine has derived is discarded — locks, timings, geometry, source references,
confirmation state and temporal witnesses. The transport unit counts are not derived and survive.
Retained storage must be inaccessible as evidence until freshly populated. The source references are
acquired again from the source, as at the start of a capture.
