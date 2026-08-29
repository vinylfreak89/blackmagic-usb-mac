# Blackmagic Intensity Shuttle (USB 3.0) — analog capture on Apple Silicon

Design doc and measured facts for the Intensity Shuttle USB 3.0 userspace capture path.

---

## 1. Goal

Get a **clean, faithful, lossless interlaced ANALOG standard-definition capture** off a
Blackmagic **Intensity Shuttle USB 3.0** on an Apple-Silicon **M3** Mac — video **+ audio +
correct A/V sync** — for **VHS archival**. End-state: expose it so **OBS** (and ideally any
app) can use it. Fix field order / deinterlacing **in software downstream**, never bake it in
at capture.

Primary signal path: **JVC D-VHS deck (best-in-class analog S-VHS/VHS playback) → S-Video →
Shuttle analog in → Mac.** (S-Video is the default tap; component is an early A/B — see §11.)

## 2. Requirements

- **Analog is the primary path, NOT HDMI.** The deck's TBC/frame-synchronizer does unwanted
  processing on its HDMI out (see §7). HDMI capture is only a *diagnostic reference* (§9, exp 3).
- Prefer **no boot-security changes** (no disabling SIP / kext allowance). The chosen approach
  needs none.
- Capture must be **lossless and honest**: record what happened, mark damage, never conceal in
  the archival record.
- **OBS virtual camera** is the delivery end-state.

## 3. Hardware & environment (VERIFIED on the machine)

| Fact | Value |
|---|---|
| Device | "Intensity Shuttle", VID `0x1EDB` (Blackmagic), PID `0xBD3B` |
| USB | USB 3.0, negotiated **SuperSpeed 5 Gbps** (`ioreg` UsbLinkSpeed=5000000000) |
| Class | Vendor-specific `0xFF/0xFF/0xFF` → **no OS driver binds; nothing claims it** |
| Host | Apple **M3**, macOS **26.6.1** (arm64), SIP **enabled** |
| Access | Openable from userspace via **libusb** (no kext, no entitlement, no root for a CLI) |
| Toolchain | `libusb 1.0.30` (Homebrew, exactly the version to use), Apple clang 21, ffmpeg 9 |
| Enumerate | `system_profiler SPUSBHostDataType` (NOT `SPUSBDataType` — returns empty on this macOS); `ioreg -p IOUSB -l -w 0` is the scriptable source of truth |
| Topology | Direct attach and one USB 3 hub both sustained the SD rate (181 Mbit/s) with zero scheduled-slot gaps; hub reserved-bandwidth behaviour at HD rates is unmeasured |

Blackmagic never shipped a macOS driver for the USB3 Shuttle (the Mac product was Thunderbolt),
so there is no vendor kext to fight — this is *why* userspace is tractable.

## 4. Approach & the central decision

**Native userspace libusb capture core. `bmusb` is a PROTOCOL REFERENCE ONLY — not a port.**

- Userspace libusb avoids kexts, DriverKit dext entitlements, and boot-security changes.
- **`bmusb`** (Steinar H. Gunderson, GPLv2+, Linux, libusb) reverse-engineered the device
  protocol. We take its **observed constants and hypotheses**, not its code structure, error
  policy, or "authoritative" semantics. Its silent-corruption architecture (skips iso packets
  without marking frames corrupt; pairs A/V by timecode and **drops the orphan / emits blank**;
  global-default libusb context) is **disqualifying for archival**.
- **GPL note:** copying bmusb code makes a derivative GPLv2+. We reimplement its *ideas*
  (protocol facts are not copyrightable). Fine for personal use; matters if ever distributed.

## 5. Device protocol (from bmusb 0.7.8 — RE-VERIFY empirically in §9 exp 1)

Reference source: `https://sources.debian.org/data/main/b/bmusb/0.7.8-2/bmusb.cpp`.

**Init (active path):** `libusb_claim_interface(0)` → `set_alt(0, 1)` (alt 1 = output) →
`set_alt(0, 2)` (alt 2 = input). Switching alternates **resets** the card, so alt1→alt2 doubles
as reset+select-input. Then send the mode word (req 215) → the index-24 latch → start iso IN.
`release_interface(0)` on teardown. (Alt 3/4 = lower-bandwidth variants; a second
`claim_interface(3)` and a 1→2→1 dance exist only under `#if 0`.)

**Mode word** — vendor control OUT, `request=215, value=0, index=0`, 4 bytes big-endian:
```
mode = 0x09000000 | video_input | audio_input   (| 0x20000000 for 8-bit; omit for 10-bit v210)
```
| Selector | Values |
|---|---|
| video_input | HDMI/SDI `0x00000000`, Component `0x02000000`, Composite `0x04000000`, **S-video `0x06000000`** |
| audio_input | Embedded `0x00000000`, **Analog `0x10000000`** |
| pixel | 8-bit YCbCr (UYVY) sets `0x20000000`; 10-bit v210 is default |

→ **S-video + analog audio + 8-bit = `0x3F000000`** (wire `3f 00 00 00`). This is the first
experiment's mode word. Then latch: req 215, index 24, `0x73c60001`.

**Streaming:** async **isochronous** IN on `0x84` = **audio**, the other IN (`0x83` per bmusb) =
**video**. (bmusb uses iso, NOT bulk — matters a lot for the Darwin backend.)

**Status:** vendor control IN `request=214`; index 16 = signal/mode status
(first byte ~`0x39` stable 576p, `0x2d` stable 720p, `0x20` no-signal).

**Video formats** (16-bit code): NTSC 480i `0xe101` family → 720×480 interlaced,
`second_field_start=280`, 30000/1001; PAL 576i `0xe109` family → 720×576, 335, 25/1;
**no-signal `0x0800`** → green pseudo-frames ~30.13 Hz. SD is delivered with the **full
525/625-line raster** via extra top/bottom lines.

**Audio:** 8-channel **24-bit** raw; **sample rate is NOT signaled — it's guessed** from
sample-count vs frame-rate (32000/44100/48000). **Observed on hardware (§6):** 24-byte records,
only **2 channels active** (bytes `[0:6]`, the other 6 always zero), and a
**`DeckLinkAudioResyncT`** record once per video frame carrying the **shared 16-bit counter** —
which is what makes A/V sync (and untagged de-interleaving) exact.

**Frame boundaries:** a sync marker in the stream (bmusb: `00 00 ff ff`). Only 4 bytes → **can
occur inside UYVY/v210 content**; validate by expected position + plausible following header +
length, and handle a marker **split across iso packets**.

**A/V pairing:** each queued video/audio unit carries a **16-bit `timecode`** (wraps). bmusb
matches them and discards the orphan — **we must NOT do this** (§8).

**Firmware:** none uploaded; device is already on its main PID. Requests 192/219/222/223/224 are
firmware-upgrade — stay away.

## 6. Status — confirmed / qualified / open

**CONFIRMED on hardware (M3 / macOS 26.6.1; `experiments/`):**
- ✅ Userspace `libusb` open + `claim_interface(0)` — no root, no entitlement.
- ✅ Real endpoint map (usb_descriptor_probe): IF0 **alt2** = iso IN **`0x83` video** (49152 B/interval,
  burst 11) + **`0x84` audio** (2048) + bulk `0x05`/`0x86`; **alt1** = output.
- ✅ Full init: `alt1→alt2` reset, mode word (`0x3f000000` S-video / `0x3b000000` component),
  latch `0x73c60001`, status `214/16`.
- ✅ **ANALOG CAPTURE WORKS — existential unknown RESOLVED.** Real color **NTSC 480i** captured
  via **S-Video** and **visually confirmed** (bob-deinterlaced to a clean frame). Source deck:
  JVC HM-DHX2. Deck requirements: use a rear OUTPUT jack (the front AV block is input-only), and
  HDMI output mode must be off so the deck outputs 480i (in HD/progressive output modes the SD
  analog outputs are blanked → black-with-sync capture).
- ✅ Isochronous **throughput** proven: sustained SD at ~**181 Mbit/s decimal** (≈173 Mib/s) —
  NOT "174 Mbit/s". CPU/bandwidth are non-issues.

**QUALIFIED / CORRECTED:**
- Bob-deinterlace vs the deck's HDMI: *on the tested tape segments*, field-rate bob from analog
  avoided the deck-HDMI deinterlace artifacts and looked cleaner. **Comparative, not universal.**
- The 16-bit value after the marker **increments per marker-delimited transport unit (incl.
  short/fragmented units)**; it is **NOT** established as a video-frame timecode. (Earlier "tc16
  frame counter" was wrong.)
- **Rewind frames are NOT "valid."** During rewind the Shuttle **keeps reporting the NTSC format
  and emits structurally-framed but severely degraded/noisy raster.** Format classification is
  **not** a quality guarantee. (So "the device lies about lock" was also wrong.)
- The 60 s / 1.3 GB run = **"sustained capture completed," NOT "clean"** — until packet-error
  counters, short-write checks, and submission-order instrumentation exist.

**RESOLVED — the intermittent frame "tear":** a frame-by-frame decode traced it
to a **renderer bug — not the signal, not the player**: the extractor accepted a **short
755552-byte unit** (tc 5839, 496 B short of 756048) and **read 756000 B anyway, spilling 496 B
across the next marker** → horizontal raster slip = the green splice. **Fix:** strict extractor
invariant — `format==0xe801` **and** `gap==756048` **and** `payload==756000`, **never read past
the next marker**; short units archived separately, never fed to the fixed-raster renderer. Two
narrower issues stay OPEN: (a) *why* that unit was short; (b) whether Darwin/libusb callbacks ever
arrive out of submission order.

**QUALIFIED by `capture_untagged_ring` (ring buffer + writer thread):**
- ✅ The writer no longer blocks the libusb callback; the 5-min run reported zero ring overflow
  and zero observed video submission-order inversions.
- ❗ **That run was not full-rate or lossless.** After counter 25026, every video deficit is an
  exact multiple of **24,576 bytes**, the normal payload of one old capture_untagged_ring video transfer. Static
  analysis shows `V_NPK=8`, `XFERS=6` queued only ~6 ms of Darwin video schedule. Darwin assigns
  explicit future USB frame numbers and jumps forward when resubmission misses that horizon; an
  unscheduled interval has no callback and cannot increment transfer/packet error counters.
- ❗ The old callback also silently ignored completed packets with `actual_length == 0`, so
  "0 iso-packet errors" did not establish continuity. capture_untagged_ring now queues ~128 ms, uses one ring
  operation per transfer, and reports packet-length histograms. Hardware verification remains.

**OPEN / NOT retired:**
- ❗ **Silent host-loss holes.** On ring-full, `capture_untagged_ring` drops the payload and only counts bytes —
  **no marker in the stream**, so a gap is indistinguishable from contiguous data downstream.
  Violates §8 property 1/6. Fixed by the tagged format (requirement 7).
- ❗ **Unscheduled Darwin iso holes.** A shallow submitted-transfer horizon can expire without
  producing any transfer record. The production format must identify scheduled packet slots,
  not merely callback and submission order.
- ❗ **Non-atomic shared state in `capture_untagged_ring`:** `inflight`, `v_bytes`, `v_submit` are plain globals
  mutated from callbacks; `g_stop`/`g_done` are `volatile`, not atomics. Bench-adequate, not
  core-adequate.

**Confirmed probe defects → capture-core requirements (fix before trusting captures):**
1. **No disk I/O in the iso callback** — swap/enqueue buffer + resubmit immediately; a ring buffer
   + dedicated **writer thread** does the writing.
2. **Per-endpoint submission sequence** — tag each submission monotonically and reconstruct byte
   order by **submission** seq, not callback order (clean gaps + monotonic counter do NOT rule out
   two equal chunks swapping inside one marker interval).
3. **Count/act on errors** — don't silently skip non-COMPLETED iso packets; check every `fwrite`
   return; log packet status/lengths.
4. **Handle a marker split across two iso packets.**
5. **Cancel outstanding transfers on shutdown.**
6. **Strict extractor invariant** (above); archive short/fragmented units separately.
7. **Tag every chunk on the wire-to-disk path** — `{endpoint, submit_seq, length}` header per
   payload, plus an explicit **`HostLoss` record** on overflow. Untagged output forces the reader
   to *infer* stream identity from content; tagging makes de-interleaving exact instead of
   inferential and makes holes explicit. (Improvement, not a rescue — see the recovery result
   below: untagged captures are NOT stranded.)

### Untagged video+audio mix is RECOVERABLE (proven with `capture_render.py`)

`capture_untagged_ring` submits both endpoints, so completed video (0x83) and audio (0x84) transfers land in one
flat file **with no endpoint tag**, in completion order. This was accidental — and it turns out to
be a genuine **A/V** capture, not a corrupt one. Full-file result: **6,160 video units, every one
exactly 756,048 B**; **26,487 audio spans, 0 counter discontinuities**; renders correctly.

It works because both streams are strongly self-describing **and the format self-validates**:
- **Audio record = 24 B**: 8ch × 24-bit where only **2 channels are active (bytes `[0:6]`)**, so
  **bytes `[6:24]` are always zero**. An 18-of-24 zero pattern repeating *in phase* effectively
  does not occur in UYVY video, and the test holds for loud *or* silent audio.
- **`DeckLinkAudioResyncT`** appears **once per video frame** (8,991 over 300 s) as a complete
  24-byte record in the same phase, carrying **the same 16-bit counter as video** → A/V sync comes
  from a shared counter, never from interleave position.
- **The validator:** remove exactly the right bytes and consecutive `0xe801` markers land at
  **exactly 756,048**. Any mis-cut shows as an off-by-N gap. This is a hard property, not a
  heuristic — it caught every bad extractor (off by 120 B, then 1–4 B, each → whole-frame UYVY
  phase shift = green/magenta or an "hsync-off" raster slip).
- **Do NOT de-interleave per-frame by zero-density maximum.** Audio callbacks **straddle video
  markers** (the first audio block in a frame span is a partial), so per-frame heuristics move
  callback edges → horizontal wobble + leaked-audio bands. It must be a **global** pass.

Genuinely unrecoverable (and none of it caused by the missing tags): merged adjacent audio
callbacks' internal boundary (irrelevant — samples stay contiguous, resync records re-anchor
timing), and anything already dropped at capture time (overflow / failed iso packets / **the
unscheduled Darwin holes above**).

⚠️ **"Recoverable" ≠ "complete."** `untagged_capture` itself is missing data — after counter 25026 every
video deficit is an exact multiple of 24,576 B (unscheduled transfer slots, §6 open items), and
those positions were **never recorded**, so no decoder can restore them byte-exactly. De-interleave
recovers *what crossed the bus*; it cannot recover what the host never asked for. Do not read the
"6,160 units, all exactly 756,048 B" result as evidence the capture was lossless — the units that
*survive* are exact, which is a different claim.

**Field order: TFF, verified empirically** — stored chronological field 1 → **top** field, built as
720×480 from source lines 17..256 and 280..519, bobbed with `bwdif=mode=send_field:parity=tff`.
The credit roll is the disambiguator: TFF gives **0.0345 px** mean motion alternation vs **0.759 px
(±1.7 px excursions)** for BFF. Note this **contradicts the usual NTSC-SD-is-BFF expectation** —
trust the measurement, and re-measure per capture rather than assuming.

**Pipeline work does NOT need the deck.** Everything downstream of acquisition — §9 archival
writer, §10 CMIO/OBS delivery — is developed by **replaying a captured file through a virtual
device**. This makes the whole downstream pipeline deterministic, testable without tape, and
exercisable against recorded damage (program cut, deck-blank/relock, short units) on demand. It is
§8 property 9 (deterministic replay) promoted to the primary development workflow.

### Signal-state timeline — measured over the full 5-min capture

**❌ The "no-signal rewind" never happened — the assumption was wrong.** With the tape stopped and
heads disengaged, the deck does **not** drop its output: it emits its own **grey mute screen with
the Japanese OSD and a running tape counter** (visibly `0:23:58 → 0:25:24 → 0:03:31 → -0:00:13`).
Consequences:
- **`0x0800` never occurs anywhere in this capture** (0 hits in 5.57 GB); no green pseudo-frames,
  no ~30.13 Hz cadence. Format stayed `0xe801` and the rate stayed **29.97003 fps exactly**
  throughout the "dead" window. **Device true-no-signal behaviour is UNTESTED** — to exercise it,
  disconnect the S-Video cable or power the deck off; stopping the tape is not sufficient.
- The blank raster is **near-neutral grey, NOT green** (Y 120.6 ±0.1, U 129.9, V 127.3).
- Two runs of **exactly 19 frames** bracket the blank period with **sub-blanking luma (Y 1–2,
  below the 16 black level)** and chroma pinned at 128 — not a legal digitized picture, most
  likely the deck's output relay muting to 0 V.

**⚠️ 17.7% of complete units are structurally perfect non-picture** (1,093 of 6,160: 1,017 deck
blank, 38 snow, 38 sub-blanking black). Every one is a full 756,048-byte `0xe801` unit with a
monotonic counter — **in-band indistinguishable from good video.** Relock after the splice took
51 frames (1.70 s) and after the restart 69 frames (2.30 s), emitting complete well-formed units
of pure snow the whole time. This is the hard number behind "format classification is not a
quality guarantee": **only content analysis can establish signal state** (see also the dead-end
header result in §9).

**✅ Audio is a viable continuity master** (validates §9's approach): 8,991 resync records,
counter `18706 → 27696`, **every step exactly +1, zero exceptions** — across the splice, the stop,
the rewind, the relock, and 35 s in which the video endpoint delivered **zero bytes**. Spacing
alternates 1601/1602 samples (1601.5998 mean in clean segments vs the ideal 1601.6); total drift
**271 samples ≈ 5.6 ms over 5 minutes**. Audio mute runs also independently locate every deck
event. ⚠️ No 16-bit wrap occurred (27,696 < 65,536), so **wrap handling remains untested**.

**Transport collapse is worse and earlier than recorded:** loss begins at **ctr 24983 / t 209.4**
(not ctr 25026), ramps 99%→60%→~40%→~19%, and the video endpoint delivers **zero bytes from ctr
26651 / t 265.1 to the end** — 1,046 counters, ~794 MB never requested — while audio continued
untouched (consistent with the high-rate endpoint suffering far more from the shallow queue, not
proven). **Everything after t≈209 is excluded from source conclusions.** 730 of 733 short units are
short by an exact multiple of **24,576 B = half the 49,152 B/interval iso packet**.

**Correction to an earlier belief:** the false `00 00 ff ff` markers are **not** in pixel data —
all 6,345 false hits lie **inside audio spans** (quiet negative S24 samples at record boundaries);
**zero** occurred in the video raster in this capture. Grid-lock validation is still right, but the
stated reason ("the magic occurs inside UYVY content") was wrong for this material.
- Provenance test for the open questions: log per completed batch {endpoint, submit seq, callback
  seq, transfer status, per-packet status/req/actual len, payload}; reconstruct submission vs
  callback order to distinguish reordering / device-short-unit / host-loss / writer-failure /
  pre-host corruption. (Do NOT drop to 1 transfer in flight — it changes scheduling and proves
  nothing.)

## 7. The core problem: unstable field parity on degraded sources

Field "**flipping**" is **not source-stable** — it drifts within and across tapes, so **no
single global BFF/TFF flag can fix it.** Precise terms (keep them distinct):

- **Spatial parity** — top/even vs bottom/odd raster phase.
- **Temporal order** — which field occurred first.
- **Pairing phase** — which two fields the Shuttle grouped into one transport unit.

### ✅ ANSWERED — it is a **spatial field-ORIGIN slip**, not a temporal/order problem

**The central question of this project is resolved, and the earlier framing below was wrong.**
The visible "flip"/registration jump is **the second field's start line drifting** within the
525-line transport unit — observed candidates **274–285** instead of the canonical **280** — so
the raster is sliced at the wrong offset. It is **not** temporal order, **not** pairing phase, and
**not** cadence. Consequences, all large:

- **The fix is pure spatial line selection**: detect the per-frame field origins, extract the
  correct 240 lines per field (e.g. `17/278`). Because nothing is reordered, the correction
  **cannot disturb cadence or A/V sync** — a whole class of feared damage simply does not apply.
- **No dynamic TFF/BFF, no cadence matching, no field reordering.** Ordering stays chronological.
  (This retires the §9 worry about Viterbi-scored temporal hypotheses for the *common* case.)
- **Real-time feasible:** the 12-candidate origin search ran at **6.84 ms/decision in unoptimized
  Python/NumPy** against a **16.68 ms** field budget (and a decision is usually needed only once
  per 33.37 ms transport unit). C/NEON/Accelerate leaves ample headroom.
- **It belongs in the frameserver stage, NOT the USB callback**, and costs ≲1 field of latency.
- Detection must not rely on comb-scoring alone (motion can fool it). Production detector:
  VBI/active-line boundary cues + same-parity temporal registration + motion-masked comb scoring
  + a small discrete offset search + **hysteresis** (keep the previous origin when ambiguous).
- ⚠️ Also observed: a *localized* H-sync/chroma-phase disturbance at the top active lines of
  field 2 (line ~21) — **distinct** from the whole-field origin slip, present in the raw fields and
  on the deck's own HDMI/TV output. So a single event can combine whole-field registration
  displacement **and** a within-field H-sync/chroma fault. Don't model it as one phenomenon.

**Architecture consequence (supersedes "archival writer + preview" framing in §8–§10):** the final
shape is a **normal live frameserver**, not an archival writer with a preview bolted on:
`USB capture → frame parser → field-origin correction → 59.94p frame surfaces + 48 kHz audio →
CMIO/OBS`. **Recording becomes an optional downstream consumer, exactly like OBS** — it must not
control acquisition or correction. Per transport unit: archive the untouched 525-line unit
immediately, detect origins on a separate thread, select the corrected windows, publish 480i or
independent 59.94p spatial bob with monotonic PTS, and **record chosen origins + confidence as
metadata**. Audio samples are never touched, preserving the A/V clock correlation. Raw transport
logging stays an optional diagnostic mode, not the defining architecture.

---

*Superseded framing (kept for context — the mechanism guess below was not what the data showed):*

The visible flip is often a **temporal-order or pairing-phase** change while spatial parity is
normal. Likely mechanism (from the observed *freeze → vertical jump* on the deck's HDMI output): the
deck's **fixed-clock HDMI frame-synchronizer** reacting to control-track/line-timing
instability — it repeats a field to hold its clock, reacquires field phase, resumes with the
opposite pairing/registration. A **~240-line (NTSC)** jump ⇒ whole-field/pairing slip; a
**~½-scanline** jump ⇒ field-1/2 vertical-phase reinterpretation. **This can happen while signal
state stays "Locked"** — so segment boundaries must NOT depend only on signal-loss/`0x0800`/
timecode.

**Caveat that the torture test (§9 exp 3) must settle:** the Shuttle is itself an analog
**decoder + frame assembler**, not a raw sampler; its firmware may do its *own* concealment
(freeze/repeat/crop/resample) when sync gets ugly, which would be baked into the USB raster and
unrecoverable. Intact-but-mis-grouped fields are repairable; lost/duplicated/truncated/mixed
fields are not.

## 8. Architecture (independently agreed by two analyses)

**Core principle:** *Save what crossed the USB bus as immutable truth. Describe what's known as
separate, versioned interpretation. Infer field chronology reversibly. Conceal only in
disposable live output.*

**Non-negotiable properties:**
1. **Transport truth before interpretation** — record every iso packet's endpoint, submit seq,
   status, requested/actual length, host time, bytes. A failed packet is an explicit **hole**;
   never concatenate around it.
2. **Multidimensional validity** — not one `valid` bool. Separate axes: Transport (complete/gap/
   error/overrun), Framing (plausible/short/long/unframed), Signal (locked/no-signal/relocking/
   unknown), Cadence (normal/suspected repeat-drop-mispair/unknown), Interpretation confidence.
3. **Immutable observations, revisable interpretations** — raw units & field slots never change;
   parity/order/pairing/cadence are versioned annotations; manual fixes are another annotation
   layer, not destructive edits.
4. **Independent video & audio** — store every unit and every audio block; create correlation
   records. An unmatched block is a kept observation, never dropped.
5. **Epoch-based monotonic state** — every reset/reopen/alt-reset/ambiguous-counter-restart =
   new `session_epoch`; host sequence numbers monotonic; never extend the 16-bit device counter
   across an epoch just because the arithmetic fits.
6. **Structured, named discontinuities** — machine-readable records with affected ranges
   (`VideoIsoPacketLoss`, `FrameShort`, `SignalLost`, `RelockStarted`, `CounterJump`,
   `AudioOrphan`, `HostWriterOverrun`, `FieldPhaseDiscontinuity`, `PairingBoundaryShift`, …),
   not console prose.
7. **Bounded queues, honest overflow** — iso can't be backpressured. Under pressure shed parity
   analysis / preview / OBS first; if the acquisition pool exhausts, emit a host-loss marker
   immediately. Default: continue but mark the run "not clean"; offer fail-stop as an option.
8. **Append-only, crash-recoverable storage** — payload once in chunked files; observation
   records reference byte spans; per-chunk checksums, a journal, and a manifest (sw rev, libusb
   ver, descriptors, USB topology, mode word, control transactions).
9. **Deterministic replay** — the parser also consumes a saved transport log offline, so packet
   loss / split markers / short fields / wraps / relocks are testable without tape.
10. **Acquisition/live isolation** — OBS or a CMIO extension is a *disposable* downstream
    consumer, fed over **IOSurface-backed shared frames** (CoreVideo's zero-copy surface) / XPC;
    its crash or slowness must never endanger the archival writer.

**Threads:** control/session thread (owns lifecycle, serializes transitions) · exactly **one
libusb event thread** (services events only) · per-endpoint ingest/parser queues · append-only
writer · timeline/correlation worker · optional parity/cadence analyzer · optional live adapter.
**Lifecycle:** `Detached → Opened → Claimed → ResetViaAlt1 → InputAlt2 → ModeSet → Latched →
Streaming` (+ `SourceRelocking / Stopping / DeviceLost / Fault`). **Source lock state is distinct
from USB session state** (a tape dropout ≠ the USB device needs resetting).

**macOS specifics:** threads at `QOS_CLASS_USER_INITIATED` (no Mach real-time until measured);
the iso callback must not allocate, parse, write, format logs, or wait on consumer locks —
snapshot result + packet descriptors, swap a free slab, assign seq, resubmit immediately, enqueue
an immutable batch. **Sequence at submission time.** Single explicit `libusb_context`; check
active configuration before `set_configuration`; on shutdown stop resubmission then cancel each
endpoint as a group (Darwin cancels all transfers on an endpoint together); avoid concurrent
open/close/hotplug/teardown (Darwin backend concurrency bugs); one-arg `pthread_setname_np`.

**Data model (conceptual):** `IsoBatch{session, epoch, endpoint, submit_seq, callback_seq,
submitted_at, completed_at, transfer_status, packets[], bytes}` · `PacketResult{index,
requested_len, actual_len, status, slab_offset}` · `VideoUnitObservation{id, epoch,
boundary_before/after, header_before/after, tc16?, format_code?, payload, expected/received_bytes,
integrity, slot[2]?}` · `FieldSlot{id, parent, slot(0/1 transport fact), wire_ordinal, lines,
payload, integrity, fingerprint}` · `FieldAnnotation{field, analyzer_version, spatial_parity,
temporal_rank, pairing, confidence, evidence}` (separate from the slot) · `DiscontinuityEvent{id,
epoch, kind, cause_domain, severity, affected_range, evidence}` · `AudioBlockObservation{id,
epoch, header, tc16?, cumulative_sample_ordinal, sample_frames, format, payload, integrity}`.
**Time domains:** transport order · device token time (raw 16-bit + cautiously-extended) · host
monotonic (diagnostic only) · derived media time (with confidence). Host completion time is NOT
capture PTS.

## 9. Parity detection & A/V sync

**Don't treat the 16-bit timecode as a field counter** (it's once per transport unit, not per
field). **Segment** on signal-loss/relock, USB/parser gap, format-code change, counter
discontinuity, or strong pairing-phase-change evidence. Within a segment, weigh evidence in
order: (1) **device/header** — ❌ **DEAD END, measured:** across all 6,160 complete
units the 48-byte header is **byte-identical except the 16-bit counter** (`00 00 ff ff | cc cc |
01 e8` + 40 zero bytes). **No lock flag, no field-marker bit, no status.** Stop hunting; content
analysis is the only route to signal state. Preserve the header anyway (cheap, and it proves the
negative);
(2) **VBI/raster geometry** — the full 525/625 raster may carry line-21/VITC (but decoded YCbCr
has no sync-tip waveform, so RF-style tricks are out); (3) **motion/cadence** — split slots, bob
each, score chronological hypotheses over a **window** with an **HMM/Viterbi** (strong transition
penalties, relax at relock) — never frame-by-frame flipping; (4) **audio/counters** — locate
discontinuities, not top/bottom. **The estimator must be allowed to say `Unknown`** — a confident
wrong flip is worse than an unresolved annotation.

**A/V sync:** keep exact audio sample counts + cumulative ordinal; extend `tc16` only within an
epoch (record every wrap decision); match non-destructively within a bounded reorder window; fit
a robust relation between audio sample position and video, tracking both offset and slope/drift.
At 48 kHz / 29.97 fps the average is **1601.6 samples/unit** — record what the device supplied,
don't force 1601/1602. Separate **physical cadence** from **content cadence** (telecine).

**Archival master (the primary deliverable):** a **playable lossless master**, produced
*semi-live* — resolve **deterministic** field ordering with a short lookahead (unpair/reorder/
re-pair across transport boundaries; Viterbi + hysteresis settle within a few frames), then encode
straight into it. Still preserve every unit/orphan/partial/gap and bracket unknown intervals;
never silently blank/dup/drop/resample/force-CFR.
- **Gold standard: FFV1 in Matroska** — lossless, open, **per-slice CRC** (bit-rot detectable),
  interlace-preserving, 8/10-bit 4:2:2. Recipe `ffv1 -coder 1 -context 1 -g 1 -slices 16
  -slicecrc 1`, both fields woven, correct field-order tag. This file *is* the archive, not a
  derivative.
- Lighter real-time alt: **UT Video** (8-bit only, no CRC). **HuffYUV** works but is superseded.
- **MPEG-2 / H.264 = access copies (derivatives), never the master** (they're lossy).
- **Ambiguous spans** (Unknown parity / relock / cadence break): the live encoder can't commit
  safely → flag the span in a sidecar and keep a **transient raw safety net** (≥ flagged spans) to
  re-resolve and patch the master without re-running tape; delete after QC.
- **Bandwidth is a non-issue at SD:** lossless 4:2:2 ≈ 11–30 MB/s, real-time on an M3-class CPU
  (no GPU needed). Note: base M3 parts lack the ProRes hardware engine, and
  VideoToolbox can't do lossless YUV anyway — hardware offload is only relevant to *lossy*
  H.264/HEVC access copies, not the master. **Live policy:** bounded jitter buffer; valid
audio as continuity master; **bob at field rate (59.94p/50p)**; conceal only in the live
derivative; shed the live consumer before it threatens acquisition.

## 10. Delivery: OBS virtual camera

A CMIO **camera is video-only** — audio needs a separate CoreAudio device, OR deliver via a
native **OBS source plugin** (carries video+audio together; the pragmatic path for the OBS goal).
Either way, **do not put USB ownership inside the CMIO extension** (Apple's camera-extension
design assumes a signed system extension, app-group IPC, `/Applications` install, admin approval).
A sandboxed GUI/extension needs entitlement `com.apple.security.device.usb`. Long-term shape:
one USB capture service → {archival writer, OBS source (V+A), CMIO video ext + linked CoreAudio}.

**Where CoreVideo fits (and why not at capture):** at the delivery boundary, a resolved
presentable frame is materialized as a **CoreVideo `CVPixelBuffer`** — IOSurface-backed
(`kCVPixelFormatType_422YpCbCr8` = `2vuy` for 8-bit UYVY, `422YpCbCr10` = `v210` for 10-bit),
carrying field order via `kCVImageBufferFieldCountKey`/`kCVImageBufferFieldDetailKey` — which
CMIO/CoreMedia wrap as a `CMSampleBuffer`, and which IOSurface hands zero-copy to OBS/GPU/
VideoToolbox. CoreVideo is **deliberately absent from the capture core (§8)**: it's a
decoded-image/pipeline abstraction (fixed geometry & pixel format) that cannot represent
transport holes, short units, field-sequential *unpaired* slots, "unknown parity", or provenance
— using it at capture would bake in the very interpretation §8 defers. Right currency at the
delivery edge; wrong one at acquisition.

## 11. Milestones / experiment plan

1. ✅ **DONE** — **Native probe** (direct-attached, 8-bit S-video, mode `0x3F000000`):
   open/claim/alt-reset/mode/latch/stream. Real NTSC 480i captured and visually confirmed;
   sustained 5-min capture with 0 loss (§6). **Existential go/no-go: PASSED.**
2. **A/B field fixture**: source with a marker on field 1 vs field 2 + synced audio click, with
   hard signal cuts — pins slot order, spatial-parity mapping, boundary/trailer semantics, V↔A
   counter relationship, loss/relock behavior. Do this *before* torture-tape inference.
3. **Simultaneous HDMI + analog torture test** on the degraded test tapes, aligned by audio —
   locates where the damage happens (deck HDMI pipeline vs Shuttle frontend vs baked-in line
   timing). Answers the original "why field-flipping" question.
4. **Capture core** (§8) → 5. **Archival writer** (§9) → 6. **OBS/CMIO live path** (§10).
   **Steps 5–6 are built by replaying a captured file through a virtual device — no deck, no tape,
   no live signal** (see §6). Only steps 1–4 need the hardware; everything downstream is
   deterministic replay, so the archival writer and the CMIO/OBS path can be developed and
   regression-tested against recorded damage (program cut, deck-blank/relock, short units) at will.

**Analog input choice:** default **S-Video** (VHS/S-VHS is natively Y/C → most direct, least
transformed tap). **A/B vs component** early: component moves chroma demodulation off the
Shuttle and onto the deck, and this best-in-class deck may decode better — the *only* axis on
which component can win (both are 480i; field/interlace handling is identical). Compare on a
saturated, motion-heavy passage (chroma noise, color bleed, edge cleanliness).

## 12. Fallback if analog needs host-side decoder config

If exp 1 streams but stays `0x0800` on analog select, host-side analog init is missing. **Don't
disassemble** — **USB-sniff** the old Windows **Blackmagic Desktop Video** driver (USBPcap/
Wireshark) capturing analog, and replay the control transfers. Caveat: a Win11-**ARM** VM on the
M3 can't load BMD's x64 **kernel** driver → this generally needs **real x86 Windows** hardware.

## 13. Prior art & references

- **bmusb** (protocol ref, GPLv2+): `https://sources.debian.org/src/bmusb/0.7.8-2/` — Nageru.
- **vhs-decode / ld-decode** (closest metadata-model fit, GPLv3): per-field seq#/first-field/
  sync-confidence/phase-ID/fault-flags + raw-plus-sidecar. Borrow the *model*, not its
  duplicate/drop compensation; its best algos need RF sync the Shuttle already decoded away.
  `https://github.com/oyvindln/vhs-decode/wiki/JSON-metadata-format`
- **GStreamer** interlace vocabulary (`DISCONT/RESYNC/CORRUPTED/GAP`, one-field-per-buffer).
- **V4L2/videobuf2 + em28xx**: `SEQ_TB/SEQ_BT/ALTERNATE`, damaged buffers as errors,
  `NO_SIGNAL/NO_H_LOCK/LOCKED`. (Old drivers trust the hw field marker — less provenance than we need.)
- **DeckLink SDK** input model: stream-time / hw-ref arrival / validity flags
  (`bmdFrameHasNoInputSource`) / format-change (`bmdVideoInputFieldDominanceChanged`) / timecode.
- **FFmpeg**: `idet` (motion TFF/BFF/undetermined, ~1.04 threshold, 4-frame vote) as the parity
  baseline **applied between fields**; `bwdif` for the live bob; **`fieldmatch` is content-cadence
  tooling, NOT acquisition truth** (harmful if allowed to "repair" physical field records).
  `decklink_dec.cpp` for the multi-PTS-source matrix.
- **OBS decklink**: live-adapter reference only.

## 14. Working notes

- `AGENTS.md` is a symlink to `CLAUDE.md`; edit `CLAUDE.md` only.
- Superseded early assumptions: "not a driver / no RE"; bulk (not isochronous) transfers; the
  1080p-throughput concern (SD analog is ~166–242 Mbit/s — trivial for SuperSpeed).
