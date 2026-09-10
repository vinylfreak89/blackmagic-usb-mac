# Proposed contract edits — 2026-09-10

**Status: PROPOSED. Nothing here is in `docs/geometry_first_engine.md` and no code has been written
to any of it.** Drafted on the owner's instruction ("have them draft I will approve"), agreed in
wording between Claude and Codex, and awaiting his approval. Where the two agents could not agree, or
where a decision is his, that is marked in place rather than resolved.

Each draft supersedes text the owner himself authored on an earlier date. That is why they are
proposed rather than landed: two agents agreeing on a measurement is not the same as two agents
rewriting his ruling.

---

## Draft 1 — §2: the switch-free example is void

> The head switch is optional (not every source is VHS): "not applicable" is distinct from
> "unmeasurable", and a lock must never be conditioned on one. ⚠️ **The example this document gave
> for a switch-free source is WITHDRAWN by the owner, 2026-09-10**: a line-TBC-corrected pass is not
> one. "just because a partial line isn't there, as in the TBC captures, that doesn't mean there is
> no head switch. the horizontal skew at the bottom of the frame is evidence of a head switch." So
> the absence of a partial line is not the absence of a switch, and the skew below the picture is
> positive evidence OF one.
>
> No genuinely switch-free real-source fixture has been established in the current acceptance
> inventory. Initial regression coverage can be synthetic; real-source qualification remains
> unestablished.

## Draft 2 — §3: the switch requirement is keyed to the confirmation route

> **The switch line and band are required by the CONFIRMATION ROUTE, not by the source's geometry
> category** (owner, 2026-09-10, superseding the condition recorded here on 2026-09-09).
>
> A source lock does not require head-switch evidence. Acquiring a lock without it does not
> manufacture a switch count: an unmeasured count stays Unknown, and every count-dependent deduction
> stays unavailable with it.
>
> The owner permits acquisition without head-switch evidence through comb-plus-caption confirmation
> when the tape's own off-insert caption follows these VBI semantics: it is outside the Shuttle's
> overwritten lines 20-22, carries proper caption data rather than a skew artefact, and the tape's
> following line 22 is properly blanked.
>
> **The regenerated insert supplies no evidence** (owner, 2026-09-10: "no the regenerated insert
> shouldn't count as anything"). Comb plus a caption ON the insert does not acquire a lock.

## Draft 3 — the comb's phase, and rule 9's withdrawn clauses

In the Comb definition:

> Comb measurement and picture-preserving alignment selection occur during acquisition and
> reacquisition. During a maintained lock, geometry tracking does not rerun the comb, and transient
> combing alone does not initiate an adjustment.
>
> Where an alignment is selected, the preference is to shift the combed field down rather than move
> its partner up — unless that fails to resolve the comb — the governing aim being to preserve
> observed picture (owner, 2026-09-10).
>
> A confirmation disagreement is recorded explicitly. A rejected candidate does not authorize
> acquisition or move the rendered placement. During acquisition or reacquisition, alternative
> alignments may be evaluated under the picture-preserving preference; an alternative is applied only
> after it satisfies the lock requirements.

Rule 9 references that definition and describes maintained-lock geometry tracking only. Withdrawn
from rule 9: "the settled comb confirms or vetoes it" as a locked-state obligation, and "After a
displacement is applied the settled comb stands and must agree again at the moved crop."

Removed from the Source lock definition and the Comb definition: the caption-on-insert confirmation
procedure and its d ∈ {−1, 0, +1} candidate mechanism, both of which took the regenerated insert as
input. This removes the insert-derived candidate mechanism, not every independently justified comb
neighbourhood.

## Draft 4 — the invalid-raster test

> **The invalid-raster test (owner, 2026-09-10).** "if there are more than 24 lines of black with no
> head switch, just pure fucking black at the end, its an invalid raster. straight up". His rationale
> for the limit: "the 24 has nothing to do with what the fuck is delivered. it has to do with
> 262.5 + 24 = 23.5, ie PICTURE." Scope: "if EITHER field does that, then the registration engine
> should not operate" — it fails open and corrects nothing.
>
> The **no-head-switch** clause is what keeps a healthy field from tripping: black at the end
> containing the switch region is the normal case; black at the end containing nothing is a dead
> raster.
>
> He has declined to arbitrate which kind of black counts — "deck blanking, chroma, etc, I simply do
> not care" — and accepts the false positives: a legitimately dark picture or a box's bar meeting the
> condition may disable correction.

⚠️ **The policy above is settled; the DETECTOR is not, and no threshold is proposed.** Still requiring
agreement and his approval: qualification of the black reference; how the terminal run is measured;
whether generated lines and the half-line contribute to the run's length; and the treatment of Unknown
switch evidence. A fixed level bound was proposed by Claude and rejected by Codex; none is agreed.
Black is defined against the source's own measured levels (Draft 5), never against a table of values
observed on these captures.

## Draft 5 — source-measured levels, and the blanking reference

> Expected blanking extent is learned from qualified good picture lines of the current source, not
> imposed from nominal standard timing. It is remeasured after the specified transition events. How
> those lines and their reference are qualified remains gated pending agreement.
>
> **Levels are measured per source** (owner, 2026-09-10: "do not take numbers that are in the programs
> own measured thing as gospel. once again, NO MAGIC NUMBERS. measure things per source. there is
> obviously going to be a source measured levels section."). The engine establishes, for the source in
> front of it, what blanking is, what black is and where generated fill sits.
>
> ⚠️ Source blanking, source black and device-generated fill remain SEPARATELY IDENTIFIED. Their
> measured levels may coincide on a given source without their roles becoming interchangeable, and a
> per-source number can still be wrong if the samples it was estimated from were misidentified.

## Draft 6 — the head switch is a geometry input, and the both-fields rule is validity

> ⚠️ **The head switch is NOT one of the confirmations — it is an input to the geometry decision**
> (owner, 2026-09-10): "right because the head switch participates in the geometry decision. I've been
> considering it one of the 3 but its not really". So "The second may be the comb or the head switch",
> recorded from his 2026-09-09T16:40:11Z message, is superseded. **The two confirmations are the comb
> and captions/VBI, and a lock is geometry plus at least one of them.**
>
> Rule 4's independence requirement remains unchanged. Head-switch evidence used to establish geometry
> cannot be counted again as an independent confirmation. Requiring head-switch evidence at every
> acquisition is a separate defect: it makes an optional geometry input mandatory.
>
> **Both fields, as a VALIDITY rule** (owner, 2026-09-10): "a head switch can't be in only one
> field... PHYSICS. a source with a head switch (or signs of one) in only one field is garbage. fail
> open. do nothing (or hold if you already acquired a lock)". Positive evidence that the region exists
> in one field and is absent in the other prevents correction: without an acquired lock, make no
> corrective placement; with an acquired lock, hold the previously applied placement, which neither
> resets nor reacquires it. **A measured region in one field and Unknown in the other does not
> establish this asymmetry.**

⚠️ Recorded as his validity policy. Neither agent claims an instrument has been demonstrated for
positive absence.

## Draft 7 — what "head switch" names

> "Head-switch region" names the affected region where the other field's horizontal timing intrudes
> into this field (owner, 2026-09-10: "I'M DEFINING THE HEAD SWITCH AS basically where the other
> fields horizontal timing gets into the wrong field... I'm basically just defining it as the unstable
> timing region"). The partial line and the RF peak are possible landmarks within or at its boundary;
> their absence does not establish absence of the region.
>
> This does not broaden to any unstable timing: ordinary horizontal tearing and departure-and-return
> keep their existing distinctions, and a region-based definition does not remove the need to identify
> timing evidence rather than merely dark content.

---

## Open for the owner

1. **Device-state scope of the regenerated rows.** May regenerated-row presence or absence still
   inform device-state monitoring and the existing lock-like-loss policy, while contributing nothing
   to geometry or acquisition confirmation? His "shouldn't count as anything" answered a question
   about the caption route; the rows' presence is also the engine's evidence that the DEVICE has sync,
   and its absence is a lock-like loss the signal-state work depends on. Neither agent would resolve
   this without him.
2. **Approval of Drafts 1–7**, and of the deferred items staying deferred.

## Deferred measurement work, named rather than assumed

- Draft 4's detector, per the four qualifications above.
- Draft 5's qualification of good picture lines and of per-source level estimation.
- A synthetic fixture for a genuinely switch-free source; no acceptance capture provides one.
- **A lead, not a result:** the harness identifies a switch line in 1,013 of 1,013 registerable
  field-readings of capture 1 (validated against an instrument sharing no code with it), while the
  engine's export has S in 484 of 1,016. Whether Draft 7's region definition permits an additional
  SOUND region observation in that gap is worth measuring. It is not established that the engine's
  abstentions are wrong: it declines for a stated reason, and of its 264 `no_disjoint` readings, 255
  fail at candidate formation, of which 210 have the blank-level run starting at sample 0, 19 at
  samples 1–2 and 26 interior. The census validated S, which is POSITION, and explicitly not the
  partial-line identification nor that the run is physically relocated blanking rather than clipped
  black content.
