# Review of six relayed owner rulings and the temporal interpretation

Input: harness commit `86b9fcc`, merged before review. The quotations are in
`docs/v10_pending.md`, introduced at `f9fc385`. The temporal-line correction
was also received directly from the owner. Other quoted rulings are treated
as relayed owner statements; the relay's interpretation is not a ruling.

This review agrees to the bounded substantive repairs below, not to an
unseen resulting diff. No contract clause or detector is changed here.

## R1: agree, with the existing evidence qualifications

The affirmative answer explicitly permits a qualified switch in contact
with boxed geometry to contribute to d through the line account. The box's
own bar is not a categorical prohibition on that use. This resolves the
specific choice between displacement use and contact-test-only use.

Amend 8c's categorical gap/measurability wording, not merely a question
marker. Keep a genuine disqualifying gap distinct from the box's own bar;
contact and switch observations still require their own evidence. Permission
to contribute to d is not permission to turn every change of the switch
boundary into picture displacement. The temporal qualification separating
independent switch motion from displacement, Unknown handling, acquisition
requirements, and held-versus-current distinction remain operative.

The older 8d explanation must not continue to impose a bar-based prohibition
on d after this repair. Preserve its quotation as history, with its current
scope unambiguous. The owner-queue finding 6/CR-10 can close on this answer.

## R2: agree to repair the definition and its exclusion

A head-switch region may consist of one affected line, including a partial
line or an identified head-switch RF peak. No separate fully other-head row
or minimum multi-line band is required to make that a valid head switch.
Repair both the Head switch definition and the invalid-class wording that
excludes "a peak or a partial line". The existence of either valid landmark
can defeat a claim that the region is absent.

Keep identification separate from naming: an arbitrary bright excursion
does not become a head-switch RF peak by being called one. This distinction
must not reinstate a requirement for a fully switched successor or a visible
spatial tear. The owner expressly permits the one-line case.

## R2b: agree to the comparison and location rules, not a detector sign-off

The relevant comparison is the line's own horizontal blanking and picture
timing: whether they occupy their expected times in the scan. It is not a
requirement that the other head expose a complete relocated blanking interval.
The error's location at the bottom before the deck/device/other blanking
distinguishes the head-switch region from ordinary horizontal tearing elsewhere.
Calling an error ordinary tearing does not make it harmless; rule 6's separate
restriction on acquiring from other horizontal timing damage still applies.

Positive normal timing is not equivalent to failure of a displaced-interval
detector. Unreadable, ambiguous or censored timing remains Unknown and does
not satisfy the invalid-raster condition's required positive absence.

`own_blanking_census.py` is a proposed observation, not the owner's rule made
automatically conclusive. Its documented ordinary-row false positive matters.
Its reference-row selection, run statistic and empirical envelope still need
qualification; learning them within a unit does not establish identity by
itself. This review inspected its stated method, not a fresh raw-data census.

The comparison policy is clear enough to replace the obsolete B2 framing.
It does not authorize routing uncertainty on otherwise valid video into the
invalid-signal class.

## R3: the gate is clear; the lifecycle gloss is not agreed

The common established instruction is that the registration engine must not
operate on a positively established invalid-NTSC signal. This is not ordinary
uncertainty, and it is not the fade's hold-and-reassess procedure.

However, "the engine does not run" does not logically settle what happens
when valid video returns. Nor does it by itself cancel the owner's preceding
"the whole lock gets reset" and "it starts from scratch". The queue's claim
that there is no retain-versus-discard question because nothing runs is the
relay's architectural inference. A gate can be implemented with retained
storage, inaccessible old state, or a fresh instance; its name selects none
of those policies. In particular, invoking rule 5 would import that rule's
explicit held-crop disposition, which has not been established for this case.

Do not land the assertion that recovery needs no lifecycle decision, and do
not silently turn this into either automatic reuse or rule 13's full reset.
Resolve the quoted instruction in plain words with the owner:

> Once the bad signal ends and good video returns, does "starts from scratch"
> still apply—must it find a new lock before correcting the picture again?

This asks which instruction remains operative; it does not ask the owner to
choose a list of internal variables to clear.

## R6: rendering is actionable; the comb phase is not newly specified

The rendering instructions establish the following substantive changes:

- Positively established missing picture is represented as black, even when
  the selected input positions contain regenerated insert data or padding.
  Correct alignment can be used when preserving every picture line is impossible.
- The compliant 486 output places the proper lines 20–22 above the corrected
  picture; a displaced crop must not drag those service rows through missing
  picture positions and present them as recovered picture.
- The narrow exception permits the source's line 22 to render when displaced
  below the normal line-22 position and positively identified as real picture,
  not caption garbage. If used, it is the top of the 480 picture. This is not
  permission to render every displaced VBI row or arbitrary unidentified data.

These are replacements to the Crop definition, rule 7, and the 486 output
description, including their overlapping assertions that whatever the Shuttle
put in a missing-picture position renders unchanged or that source line 22
never renders. The universal line-23 crop formula needs its render exception
stated without silently redefining the measured displacement. The archival
raster and raw 525-line diagnostic must remain distinct from the composed
compliant output. This does not authorize fabricating caption payloads.

The opening "the comb is only to maintain the lock" is not a safe basis for
an execution-phase change. Existing explicit owner wording says the comb runs
at initial acquisition/reacquisition, not while the lock is maintained. The
new sentence also speaks of combing being the only way "to lock", so it may
describe the comb's purpose rather than reverse that schedule. Neither reading
should be smuggled into a rewrite. The quote supports accepting necessary
picture loss for valid alignment; it does not explicitly answer whether fresh
comb evaluation is required for a qualified displacement update under a lock.

Land the rendering repair separately. Do not mark the scheduling/tracking
question answered from this phrase alone. First recover any fuller antecedent
in the relay; if it does not settle the meaning, ask:

> After the picture is locked, should the comb run again, or only when finding
> the lock initially or finding it again?

## R45: recover the referenced answer before replacing operative text

"Answered by you I think" and "same" acknowledge earlier answers; they do not
contain replacement rules. The earlier answer and the question it answered
need to be attached explicitly. R6 supplies substantive rendering directions,
but neither those directions nor the queue's closure label specifies the
caption-only field-interleave case in rule 8.

That question separates physical field/time identity, crop interleave and the
comb's calibrated zero. Earlier VBI rules governing caption qualification and
displacement do not automatically specify all three. Do not restore the
withdrawn "precedence follows from placed geometry" clause by implication,
or make the comb compulsory after agreeing to comb OR captions.

This is first a missing-reference task for the agents, not a reason to ask the
owner the whole question again. Until the actual operative earlier answer is
present, the blanket assertion that the contract alone is stale is unverified.

## Temporal correction: accepted; the measure-zero deduction is not

Treat the line as a time interval and reconstruct acquisition chronology.
Do not treat a displayed row as an instantaneous object. But this does not
establish an instantaneous point model for every measured effect, an event-time
distribution, or an equivalence between a full analog scan and a delivered row.

Using the contract's own nominal timing, 720 samples at 13.5 MHz cover
53.333 microseconds; a full 858-sample line covers 63.556 microseconds. The
unobserved portion is 138 samples, or 10.222 microseconds per line. It is a
time interval, not a measure-zero boundary. A transition in that interval can
leave a delivered row wholly after the event without exposing its partial
predecessor. Underlying physical transition time, first observable affected
line, and the first fully other-head delivered row are distinct quantities.

For an ideal point transition and fully observed complete scans, the proposed
T/S relation can describe which scan contains the event and which follows it.
The engine has neither that full observation nor a justified uniform phase
distribution. Phase-locked or discretely sampled events also cannot be assigned
continuous-uniform probabilities by assumption. Thus "T=S is measure-zero"
cannot be used to prefer S-1 or to eliminate independently established T=S.

The late-crossing explanation of the six is a testable hypothesis, not a
deduction from S or terminal-run length. Its landmark times must be measured
independently; a missing partial predicate cannot supply those times.

## Three narrower statistical qualifications

The failed pre/post correlation control falsifies that **test's ability to
distinguish the rows**, not the proposition that either real spike is RF.
Similarly, abs-then-sign selection can miss positive excursions, but with
false positives unqualified, 241 is not a proved lower bound on genuine RF
events. It is a count under a stated selection procedure.

Adding roughly 150 equal-valued samples does not generally raise a row's
median or MAD. Low blanking can lower the median; an exactly constant majority
can leave MAD zero. A lower observed score on selected displaced-interval rows
may be reported as such, but universal anticorrelation does not follow from
the interval's length and uniformity alone.

## Verification and repository state

`owner_queue_check.py` reports three markers and three anchors. This confirms
pointer consistency, not whether the recorded answers determine replacement
rules. No new capture measurements were run. The contract is unchanged by
this review. Merge and review commits are local; no push was attempted in this
turn, pending the owner's requested push-permission question.
