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

**THE BLACK REFERENCE — decided between both agents, 2026-09-10.** He named it in the sentence that
poses the test: "**its blanking.**" The black here IS blanking, and ruling 6 already says where
blanking comes from — "find the blanking on the good lines of picture, thats your blanking interval".
Agreed wording:

> The terminal-run test uses the source-blanking reference established from qualified blanking
> intervals on the current source's good picture lines. That reference supplies both level and
> variability; nominal levels and device-generated fill do not establish it. Qualification of matching
> lines, run length and switch evidence remains separately gated.

Two qualifications keep its justification honest. Reusing ruling 6's reference does not mean the
measurement exists — that interval-identification method is itself unfinished. And the owner's
"truly noiseless" qualifier SUPPORTS this reading without proving it: a noisy bar can share blanking's
mean and digitized blanking has its own variability, so the discrimination depends on the eventual
matching test rather than on the mean, and no claim is made that ordinary noisy bars necessarily
reject.

⚠️ **Still gated, and no threshold is proposed:** how a line is matched to that reference; how the
run's ends are found; whether generated lines and the half-line contribute to its length; and the
treatment of Unknown switch evidence. A fixed level bound was proposed by Claude and rejected by
Codex; none is agreed. **The test is inactive until the reference is acquired, and a field that
cannot be tested is neither valid nor invalid on this basis** — which matters because the reference
is re-acquired from scratch after a reset (Draft 10).

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
>
> **Acquired live, never recorded as a constant** (owner, 2026-09-10): "not measure it as a static to
> put in a file. measure it when a source is first acquired." The levels are acquired at first
> acquisition of a source at runtime. No contract value, header constant or calibration file carries
> them.
>
> **Two re-measurement triggers, with different scope, which are not to be collapsed:**
> 1. a transition event (mute or fade) — re-measure the blanking interval; the lock and the rest
>    survive. Maintenance.
> 2. `0x0800`, or the regenerated rows absent — full engine reset (Draft 10); the levels are void and
>    re-acquired with everything else. A new capture.

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


---

# Round 2 — Drafts 8 to 10

## Draft 8 — the invalid class, distinct from lock-like loss

> **Two conditions put a raster in the INVALID class rather than the degraded one.** In the invalid
> class the engine does not register and does not correct — it fails open. This is NOT lock-like loss,
> which resets the geometry under rule 5b and continues.
>
> 1. A trailing black run of more than 24 lines containing no unstable-timing region (Draft 4).
>    Consequence: this unit is not usable.
> 2. The Shuttle's regenerated rows absent (owner, 2026-09-10): "if they are gone, then the picture is
>    truly unlocked, not lock like loss. it is not a valid NSTC picture. period". Consequence: the
>    above, AND a full engine reset (Draft 10) — everything the engine believes is void.
>
> Remove "the Shuttle's regenerated rows absent" from the Lock-like loss list in §3. Snow-like signal,
> a vertical tear, and a signal-state relock or splice stay lock-like loss.

⚠️ **This cannot be implemented from `insert_present`.** That flag currently means a successful
parity-valid DECODE at the insert (`field_registration.c:379`), not independent detection that the
generated row exists. A failed decode is not absence, and unavailable samples from transport damage
must never become positive evidence of absence. The engine has no detector for these rows existing;
it is a thing to build.

## Draft 9 — the insert's bytes count for nothing

> Successful regenerated-insert decoding does not locate the tape's caption line and contributes no
> geometry evidence, corroboration or tiebreak (owner, 2026-09-10: "whether they can decode captions,
> that could mean the real captions are anywhere from 20,21,22 so that should say nothing about
> geometry"). A tape-derived caption qualifies only through the agreed raw-caption and VBI checks.

Code consequence, code-derived rather than replay-verified: removing `caption_confirmation`'s
insert-bytes branch changes its result from AMBIGUOUS to NOT_APPLICABLE. The acquisition control flow
accepts only AGREES, so this alone does not change that gate's outcome; it changes the recorded
confirmation label, which has a logging consumer.

⚠️ Open gap, not an endorsement: `caption_confirmation` compares an off-insert candidate's
displacement against geometry but does not establish the properly blanked following tape line 22, so
"off-insert" alone does not certify the complete gauge under the new VBI semantics.

## Draft 10 — full reset on positively established absence

> Positively established absence of the required regenerated rows invalidates the entire registration
> state. All learned geometry, applied-offset state, confirmation state, temporal witnesses and
> source-derived references are reset to fresh-acquisition semantics. Caller configuration is
> preserved; diagnostic identifiers remain monotonic. Retained scratch storage must be inaccessible as
> evidence until freshly populated. Any future source-level references belong explicitly in this
> reset's scope.

Owner: "its not just that it resets the lock. it should reset everything. losing those lines means the
entire registration engine should reset as if the capture is brand new", and "if they get `0x0800` or
lose the regenerated lines, they go get it again".

**Measured against the code.** `0x0800` today produces a `begin_segment`, not a full reset: the
classifier's `lock_like_loss` includes the no-signal appearance (`signal_state.c:525-526`), which
raises `SIGNAL_ACTION_REGISTRATION_BEGIN_SEGMENT`, which the frameserver dispatches to
`fieldreg_begin_segment` (`frameserver.c:536`). The regenerated-rows-absent condition has no
implementation at all.

⚠️ **A claimed "gap of three arrays" is withdrawn.** `fieldreg_begin_segment` invalidates the temporal
witness, and the comb reads retained history only behind `previous_luma_valid`, replacing the luma
history and all three crop arrays before setting that flag true again — so the old contents are not
presently reachable as evidence. The requirement is therefore stated as reachability
("inaccessible as evidence until freshly populated"), not as byte-for-byte initialization. The real
implementation gap is detecting genuine absence and invoking the reset on it.

Also owed at that site: `v10_reset_field`'s comment still carries the superseded rule that a lock
requires "a unit whose switch line and band are measurable", now wrong twice over (Drafts 2 and 6).
