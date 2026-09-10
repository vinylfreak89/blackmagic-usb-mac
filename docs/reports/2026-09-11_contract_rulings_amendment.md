# Contract amendment: held registration, coherence and gated input

Inputs: harness `6484b4d9ea57ce682ca97303f9136840fb3dd2ca` and
`0f6e3efe05771b24b8e08bb19867e9cc08936af9`, plus the peer's dispatched owner quotations and latest stop on
duplicate absence/reset repairs. The requested merges are `a3965b1` and `677d963`. Contract baseline blob:
`6696fd56dea669cfa0796783c4492ba49f9c5bb7`. This is a contract/documentation change, not an engine or harness
implementation, source measurement, render, or capture verdict.

## What changed, and what did not

The B2 disposition paragraph is replaced in place: BOTH no recordable head switch AND no other recordable valid
picture exclude registration. Unresolved optional switch evidence with valid picture does not meet the gate.
The gated unit supplies timing/identity/status, not a registration decision, newly set registration level, or
temporal decision witness. Unknown is not rewritten as measured absence. Transport-unavailable samples remain
transport damage, not proof of a physically invalid signal. Warm-up can still acquire qualified references on
recordable evidence; the level-setting prohibition is not generalized to every reason registration is inactive.

The during-invalid R3 disposition is stated, and its old broad question is replaced by the existing recovery-only
question. Rule 13 already answers its own explicit full-reset cases and is unchanged. There is one remaining
recognized owner marker, not a claim that all recovery policy was newly settled.

Rule 8 records valid source VBI at candidate registration as interleave evidence, acquired once and held without
mandatory combing. A retained comb adjustment is not a current reading and a caption-only lock does not fabricate
a comb calibration. Source lock, Comb and the old settled-comb model wording are amended to agree with that phase
distinction. The plain-comb definition catches up with the already implemented mask removal; implementation
status claims that still described unconditional comb calls and mandatory-switch acquisition are removed.

Rule 2 and its dependent displacement/model clauses now require coherent geometry tracking and hold BOTH lock
and placement on unilateral motion. An unobservable counterpart is not stationary, a raw content threshold is
not an identified source landmark, and the rule does not make switch measurements mandatory. Identified tape VBI
has source identity and observed position; it is not confined to the first delivered row. Rule 11 retains the
positive full-window seed and first-confirmed geometry. The malformed 8a/12 question is withdrawn from the queue;
no exception is added and rules 8a–8d/12 are byte-for-byte unchanged.

The existing Source-measured levels definition now names the MEAN of qualified SOURCE blanking, each line at its
own interval. A mean of device rows is not the same reference. No new absence test or reset/reacquisition rule
is added. The Head switch definition and the existing region-versus-landmark absence wording are retained under
the latest do-not-redo instruction; this does not independently qualify an RF detector.

Crop, rule 7, the model's blanket line-22 statement, and §8's render composition are amended together. Measured
displacement and surviving identified source VBI license tape 20–22 replacing the device's versions on the proper
486 output lines. At d=0 there is no surviving tape VBI to substitute. Lost picture renders black, and the later
real-picture tape-line-22 exception is explicit for the 480 picture. The first six output lines must remain
vertically stable. The input-survival paragraph previously cited as :451 is unchanged; the repair is to output
composition, not to the physical input claim.

## Checks and their limits

`git diff --check` passes. Separate baseline-versus-working-copy comparisons pass for rules 8a–8d, rule 12,
rule 13, the Head switch definition, and the input VBI-survival paragraph. The symlink `AGENTS.md -> CLAUDE.md`
remains intact. No engine, harness executable, instrument, capture or generated render is changed.

Manual decision-case audit of the TEXT, not a test of implemented behaviour: the unrecordable-evidence gate
fires only when both evidence categories are unrecordable. Either category being recordable avoids that
particular gate but does not itself satisfy geometry, independent confirmation or other validity requirements.
That distinction covers a switch with no usable picture, valid picture without a switch, both available, and
neither available. A retained nonzero crop is not mislabeled as an observed zero or as a newly applied correction
on an excluded unit. Existing warm-up reference acquisition is not prohibited.

`python3 experiments/owner_queue_check.py` exits 0:

```text
contract markers found: 1
queue anchors: 1

Every contract owner-marker has a queue row, and every queue anchor still lands on one.
NOT proof that no question is elsewhere -- see the docstring.
```

`python3 experiments/definition_sweep.py` exits 0: 43 definition-form terms, zero duplicates IN THAT FORM.
This does not establish absence of semantic overloading or definitions in running prose.

Two checks fail because their fixtures require the questions just answered. They are not reported green, nor
is obsolete text restored to satisfy them. These are harness follow-up changes, not edits made in this batch.

`python3 experiments/superseded_check.py` exits 1; relevant output verbatim (including its inconsistent success
summary before the missing-replacement failure):

```text
subjects checked: 17
replacement present, no bare withdrawn form: 17

  ** REPLACEMENT ABSENT: the owner's question about absence -- expected 'the DISPOSITION when absence cannot be established, not whether it can'
```

That expected unresolved-question wording has been replaced by the owner's answered disposition. The predicate
must follow the new obligation without weakening its old historical negative control.

`python3 experiments/owner_queue_check.py --selftest` exits 1, verbatim:

```text
SELFTEST
  negative control (live tree): expect clean ... PASS
  positive 1 (a marker with no queue row): expect FAIL ... FAIL
  positive 2 (an anchor that no longer lands): expect FAIL ... FAIL
  positive 3 (a new marker, never mirrored): expect FAIL ... PASS
  positive 4 (two rows for one marker): expect FAIL ... PASS
SELFTEST FAILED
```

Controls 1/2 hardcode the removed caption-only question and their replacements now do nothing. The live anchor
check, new-marker control and duplicate-anchor control still pass. Updating the controls to mutate an actual
recognized live marker/anchor avoids tying coverage to one unresolved question's permanent existence.

## Implementation observations, not promises

The current engine already retains `comb_zero_candidate` after comb calibration and skips maintained-lock
evaluation. That variable does not demonstrate a caption-only interleave implementation: it is assigned in
`comb_confirm`, not by the caption path. Likewise `blank_mean` is per-call rather than a persistent level
accumulator, but its input rows are device rows 7–16 / 270–279, including the timing row. Computing a mean does
not implement the source-reference requirement. The existing top-only placement defect and the new input-gate
state/record obligations still need their engine changes and tests. This amendment does not claim otherwise.

Both requested merges initially failed on overlapping documentation. Exact failures:

```text
CONFLICT (content): Merge conflict in docs/v10_pending.md
Automatic merge failed; fix conflicts and then commit the result.
```

```text
CONFLICT (content): Merge conflict in CLAUDE.md
Automatic merge failed; fix conflicts and then commit the result.
```

The completed resolutions preserve the Part 2C withdrawal, the separate variance caveat, the owner's dark-peak
closure, and the verified current-code correction that `LockBroken` has no live assignment.
