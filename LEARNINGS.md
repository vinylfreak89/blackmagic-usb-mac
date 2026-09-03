# Learnings log

Diagnostic post-mortems for this project — **method**, not chronology. Kept because the wrong
turns here were expensive and repeatable, and because several "obvious" conclusions were wrong in
ways that looked right for hours.

Rule for entries: record what would otherwise be **re-derived or re-suffered**. A learning earns a
place only if it changes how the next diagnosis is run.

---

## Method lessons (the transferable ones)

### 1. "No error reported" is not "no error" — an instrument must be able to *see* the failure
The capture reported **0 iso-packet errors, 0 ring overflow, 0 submission-order inversions**, and
that was cited as proof a 5-minute run was clean. It was not clean: `XFERS=6`/`V_NPK=8` queued only
~6 ms of Darwin isochronous schedule, and when the queue horizon expired Darwin advanced to a later
USB frame. **No request existed for the skipped slots, so no callback and no error counter could
ever fire.** The deficits were exact multiples of one transfer payload (24,576 B).

The counters were not wrong; they were **blind to that failure mode**, and silence from a blind
instrument was read as evidence. Before claiming a property holds, ask *by what mechanism would the
opposite have been detected?* If the answer is "it wouldn't", the measurement says **unknown**, not
**fine**. (Corollary: continuity must be established positively — from a monotonic sequence or the
data's own invariant — never inferred from the absence of complaints.)

### 2. A self-validating invariant beats every heuristic
De-interleaving the untagged capture was solved not by a clever detector but by a property that
**cannot accidentally hold**: remove the right bytes and consecutive `0xe801` markers land at
*exactly* 756,048. Every bad extractor was caught instantly and unambiguously by its own off-by-N
(120 B, then 1–4 B). Heuristics (zero-density maxima, period-4 variance) each looked plausible and
each silently corrupted output. **Find the invariant first; it is the arbiter, not the eyeball.**

### 3. One frame is not a render
A single hand-picked frame was declared clean; a montage of the same clip showed green/magenta
chroma-shifted frames and leaked-audio bands throughout. **Always sample across the whole artifact
before making a quality claim** — `select='not(mod(n\,N))',tile=` costs seconds.

### 4. Symptoms and causes live in different layers — name the layer before fixing
Repeatedly, a visible artifact was attributed to the wrong layer: a raster slip blamed on the
deinterlacer, a capture-loss claim blamed on disk I/O, a commit failure blamed on file permissions.
Each fix aimed at the wrong layer wasted a cycle and, twice, **added** a defect. Ask "which stage
could produce *exactly* this signature?" and prove that stage is implicated before changing it.

### 5. Verify hardware and tool preconditions instead of assuming them
Assumed the deck had no HDMI (it does), and dispatched a commit task to an agent thread whose
approval policy made `.git` writes impossible (checkable in one command beforehand). Both were
cheap to verify and expensive to assume.

### 6. Don't "fix" a symptom outside the system you were asked to change
Faced with a sandbox-denied `.git` write, the repo's macOS sandbox ACL (`com.apple.macl`) was
stripped. It **did not** fix the problem — the real cause was the agent's approval policy — and it
damaged security metadata that then had to be restored from a Time Machine backup. Out-of-scope
"fixes" are how one bug becomes two.

### 7. A metric that constrains a *difference* cannot locate an *absolute* position
The field-registration fault was reported for hours as "field 2's origin wanders across 274–285."
It was measured with comb/weave scoring — a metric that is mathematically **only** sensitive to
`f2 − f1`, because translating both fields together leaves the weave identical. It therefore could
never have located field 2's origin at all. A full census against **physical anchors** (the
device's constant hard-padding ruler at lines 0–6/261–269/523–524, and each field's VBI signature)
showed the transport raster is rigid and that **field 1's picture** is what moves.

Two rules fall out. **Ask what a metric is capable of resolving before quoting its output as a
measurement** — this is the same error as the "0 errors" bug (§1): an instrument's silence and an
estimator's best guess were both promoted to fact without checking what they could actually see.
And **anchor geometry to something the device asserts**, not to a quality score over the content.

Corollary — **low-margin estimator output is not data.** 42% of the off-nominal picks carried a
median relative margin of **0.027** against **0.587** for confident picks; they were noise being
reported as signal. Always emit a per-decision confidence, threshold on it, and exclude regions
where the metric provably has nothing to work with (here: a flat bright field with no vertical
detail, and dropout frames with no VBI at all). "Unmeasurable" is a valid, useful result.

### 8. A discrepancy is a lead, not a thing to explain away
The decoder recovered **6,160** video units where the audio resync records proved **8,991** frames
had occurred. That 2,831-frame gap was *rationalized* on the spot — "consistent with the ~100 s of
stop/rewind/no-signal" — and moved past. **The gap was the bug.** A plausible story was accepted in
place of a five-minute check that would have exposed the missing USB frames immediately.

When a count derived from what *should* exist disagrees with what *does* exist, that difference is
the highest-value signal available. Explaining it away with a story that happens to fit is the most
expensive shortcut in this log — it postponed the real finding by hours, and only an independent
investigator eventually chased the number down.

### 9. A periodic fault carries its period — histogram the timestamps before theorizing
The USB capture losses spawned days of mechanism theories: bandwidth, disk throughput, hub
quirks, buffering mechanics, transfer ordering, USB-vs-host clock desync. The actual cause was
**a timing-cycle mismatch all along**: a ~1 Hz periodic host task beating against a ~6 ms USB
scheduling horizon. The confession was sitting in plain sight the whole time — **64% of the
drops landed in two 100 ms windows (.7 s and .9 s) of every second** — findable by a one-line
histogram of `timestamp mod 1.0`, at any point, by anyone.

Two rules. **When a fault recurs, histogram its timestamps against candidate periods FIRST** —
periodicity fingerprints the mechanism class instantly (phase-locked ⇒ a scheduling collision;
uniform ⇒ load or noise; stepped ⇒ discrete state loss) and would have eliminated most of the
theories in one shot. And **real-time pipelines fail at the beat frequency of their mismatched
cycles**: any periodic stall longer than the scheduling margin loses data on every beat, so the
margin must dwarf the longest periodic stall in the system (6 ms lost twice a second; 128 ms
doesn't), and the thread doing the real-time work must outrank the housekeeping that beats
against it. The same census also cleared two suspects at once: the drops were not deck-correlated
(an impression that bursts followed the splice failed its own test), and the flat 1/5-duty
plateaus ruled out gradual clock drift — steps, not slope.

### 10. A silenced guard is no guard
Hours after building automatic lock-holding into the dispatch tooling, the orchestrator's own
commit ritual ran `lock acquire ... >/dev/null 2>&1` during a live render turn. The guard worked
perfectly — it refused with BUSY every single time — and the output suppression threw the refusal
away. The edits proceeded; the paired `lock release` (then unconditional) destroyed the running
turn's hold on the first cycle; every later cycle "acquired" cleanly against a tree the first pass
had unprotected. Only disjoint file sets prevented interleaved commits.

Two rules. **Never redirect a guard's output to /dev/null** — a refusal you cannot see is a hard
stop you will not make; if a guard's chatter is noisy, fix the guard, don't gag it. And **a
release operation must never be able to break another live holder** — the tool now refuses
(exit 1, `--force` for deliberate breaks), because the operator who suppresses output is exactly
the operator who won't notice they just released someone else's lock. Same family as the global
rule "never disable a safety net and exercise what it protected in one pass" — performed, this
time, by the person who built the net that afternoon.

### 11. Don't claim credit for a fix you didn't prove you caused
A commit that had been failing suddenly succeeded, and the sandbox-ACL strip performed just before
it was announced as the fix. It was not — the actual cause was the agent's approval policy. Two
changes had landed close together and the wrong one was credited, purely because it was *mine*.
Post-hoc-ergo-propter-hoc is how a useless change gets enshrined as a fix and a real cause goes
unrecorded. State the causal claim only when the counterfactual was actually tested.

---

## Claude — misdiagnoses

- **Never asked the device for the data at all — silently.** The single worst defect in the
  project, and it was originally filed only as an instrumentation lesson rather than as the bug it
  is. `XFERS=6` × `V_NPK=8` queued roughly **6 ms** of Darwin isochronous schedule. Darwin assigns
  each transfer an explicit *future* USB frame number and, when the submitted queue expires,
  advances to a later frame. The skipped USB frames therefore had **no request outstanding**: the
  data was not corrupted, not dropped, and not lost in transit — **it was never requested.** Since
  a transfer that was never scheduled produces no callback, no status, and no packet descriptor,
  every error counter stayed at zero and the run was reported as clean. Two distinct failures in
  one: the omission itself, and reporting silence as success. Queue depth on an isochronous
  endpoint is a **correctness** parameter, not a tuning knob — the host must be asking for *every*
  frame interval, continuously, and must be able to prove it did.
- **Declared analog capture working from a format code alone.** A locked format value is not a
  picture; the frames were noise. Format classification is never a quality guarantee (the same
  error recurred later with rewind frames, which report valid NTSC while being garbage).
- **`fwrite` inside the isochronous callback** (capture_naive_callback_io) blocked the event thread and dropped
  packets on long runs — capture-side work must never do disk I/O.
- **Read a fixed 756,000 B out of a short 755,552 B unit**, spilling 496 B across the next marker
  → the "green splice" tear. Was confidently attributed to the *signal* before being traced to the
  renderer.
- **Per-frame de-interleaving by zero-density maximum.** Audio callbacks **straddle** video
  markers, so per-frame heuristics move callback edges → wobble and leaked-audio bands. Had to be
  a global pass over the whole stream.
- **Wrong audio record phase** (`[12:18]` instead of the real `[0:6]` active / `[6:24]` zero) and
  the `DeckLinkAudioResyncT` record left in → 1–4 bytes over-removed per frame → whole-frame UYVY
  phase shift (green/magenta, "hsync-off" raster slip).
- **Attributed a ±0.6 px vertical displacement to the bob's field crops.** It was the field-origin
  slip — the actual core finding — misfiled as a rendering artifact.
- **Claimed the removed sandbox xattrs could not be re-applied.** A plain-user `xattr -wx` did it.
  A capability claim derived from one failed attempt is the weakest possible evidence.
- **Held completed work uncommitted** across long stretches, then misread `git status` and implied
  another agent had modified files that were its own uncommitted edits.

## Source-side misdiagnoses

Each was a *reasonable* inference from real observations, which is
exactly why they held for so long.

- **The project's founding diagnosis was wrong.** "Field flipping / weird interleaving" framed the
  whole design doc (§7) around temporal field order, pairing phase, and cadence — with the deck's
  TBC/frame-synchronizer as the suspected mechanism. The truth was a **spatial field-origin slip**:
  the second field's start line drifting (274–285 vs the canonical 280) inside the 525-line unit.
  Nothing temporal was involved. The correct fix — choosing the right 240 lines — is far cheaper
  and safer than everything the temporal framing implied.
- **The deck's HDMI path was blamed for the artifact.** It appears in the *raw analog fields* too,
  so the deck's HDMI pipeline was not the origin.
- **S-Video was patched into the deck's front AV block**, which on this unit is input-only; the
  Shuttle needs a rear output. Cost hours of black-with-sync captures, compounded by the front
  panel's `入出力` labelling.
- **Called a good frame broken.** A correctly de-interleaved frame was read as "hsync boundary is
  off / mangling the framebuffer"; it was in fact **real tape flagging** faithfully captured. Corrected by
  re-inspecting the raw fields — which is what stopped a chase after a non-existent bug.

---

## What actually worked

- **Two independent agents disagreeing.** Nearly every correction in this project came from one
  party refusing to accept the other's conclusion — the tear, the de-interleave method, the
  scheduling holes, and the field-origin finding were all caught this way.
- **Owner's domain expertise as the veto.** "That's real flagging, not your bug" and "it's a frame
  shift, like an analog TV with hsync off" both redirected the investigation correctly when the
  data alone was ambiguous.
- **Preserving damage instead of concealing it.** Refusing to fake missing frames kept the real
  signature (deficits in exact multiples of 24,576 B) visible — which is what made the Darwin
  scheduling bug findable at all. Concealment would have hidden the evidence.

## A described change is not a landed change — the other reviewer must verify the tree

During the audio-path review a patch script aborted on a duplicate match after the first file,
and the subsequent `git commit --amend` carried nothing. The dispatch to the reviewing agent
described the fix as present and the suites as green; the reviewer verified the tree instead of
the description and returned CHANGES-REQUIRED with the exact discrepancy. Two rules fall out:
patch scripts must assert every replacement count and verify by grep before any test or commit
claims are made, and a review request must never rely on the author's description — the reviewer
reads the tree at the named revision. The mutual-review rule (CLAUDE.md §14) exists for exactly
this failure.

