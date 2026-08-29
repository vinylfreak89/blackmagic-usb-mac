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

---

## Claude — misdiagnoses

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
