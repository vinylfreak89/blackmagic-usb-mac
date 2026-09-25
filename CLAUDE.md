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
- **Validation fixture A** (the test tape behind every measurement in this doc): consumer T-120
  VHS carrying two off-air recordings made ~1998 on two unknown consumer VCRs, remainder virgin.
  Segment 1: SP, weak indoor-antenna source, recording-time horizontal flagging, field-1
  registration plateaus on playback. Segment 2: EP, rooftop-antenna source, clean H-timing,
  pause-edit discontinuities (program missing at recording time). Both segments: audio on the
  linear track only. Chosen because a pipeline that survives it survives ordinary tapes.
  Target corpus: ordinary consumer VHS. Minimize plays as a courtesy to the tape, but nothing in
  the corpus is so fragile that a capture cannot be re-run (owner, 2026-09-03; an earlier
  "one-shot, one capture per tape" framing here was invented, not a requirement).

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
- **Licensing position:** the position is unusually
  clean with one wrinkle. **Clean:** no BMD SDK was used and no BMD EULA was ever accepted (BMD
  never shipped macOS software for this device — the project's founding premise), so no contract
  restricts the RE; no firmware is touched or redistributed; nothing circumvents a protection
  measure (the protocol is unencrypted); interoperability RE of this kind is the classically
  protected case. Name the device nominatively only (compatibility), never implying endorsement.
  **The wrinkle:** this was not a formal clean-room — the author read bmusb's GPL source directly
  while writing our code. Nothing was copied or translated (all code here is original, and the
  protocol facts — constants, endpoints, request numbers — are facts), but the two-team spec-wall
  defense doesn't exist. Cheapest resolutions if publishing: license our code **GPLv2+** (any
  derivation question becomes moot by compliance) with a NOTICE crediting bmusb for protocol
  discovery; or, for a permissive license, accept the (small) residual derivation argument and
  document the protocol as a standalone facts file. Not legal advice; decide at publication time.
- **License:** GPLv2+ with a NOTICE crediting bmusb for protocol discovery.

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
the next marker**; short units archived separately, never fed to the fixed-raster renderer.
The later byte-complete tagged capture establishes that the device itself emits short units
(census below). Callback arrival order still needs separate verification; framing alone does
not establish submission order.

**QUALIFIED by `capture_untagged_ring` (ring buffer + writer thread):**
- ✅ The writer no longer blocks the libusb callback; the 5-min run reported zero ring overflow
  and zero observed video submission-order inversions.
- ❗ **That run was not full-rate or lossless.** Loss starts at counter 24983 / 209.4 s; after
  counter 25026, every video deficit is an
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

### capture_tagged_bench — tagged capture bench

Implements requirement 7: **single libusb event thread → SPSC
byte ring (default 256 MB ≈ 11 s, atomic head/tail, lock-free data path; condvar only for
sleep/wake with a 100 ms liveness backstop) → writer thread**; shared state in C11 atomics;
transfers cancelled on shutdown. **Every iso packet** gets a 24-byte record —
`{magic 'CAP1', type DATA/HostLoss/TransferError/SESSION, endpoint, pkt_index, submit_seq, libusb
status, req_len, actual_len}` + payload — **including zero-length packets**, so scheduled-slot
accounting is complete: a missing USB frame appears as a per-endpoint **seq GAP** in the tag
stream, provable rather than inferred. **Ring overflow → explicit in-stream `HostLoss` record**
(lost pkts + bytes), never silent. `verify_packet_capture.py` verifies/de-multiplexes (per-endpoint bytes,
zero-len/short counts, seq gaps, inversions, HostLoss, split to raw streams); the format
round-trips a synthetic stream exactly, including a deliberately-missing seq detected as a gap.
Deep queue retained (`V_NPK=128`, `XFERS=8`). Overhead ≈ 0.2% (24 B per 15,360 B video packet).

**Collapse mechanism, measured from the untagged capture:** the delivered-video fraction does not
drift — it sits on razor-flat plateaus at exactly **40.0%** (~35 s) then **20.0%** (~15 s), i.e.
steps of **1/5**. That is the signature of Darwin's miss-the-horizon behaviour (a resubmission
landing past the horizon is scheduled at *current + 4* frames ⇒ a transfer delivers 1 ms in every
5 ⇒ **20% duty per live transfer**), compounded by **fleet attrition**: old capture_untagged_ring *freed* a
transfer when resubmission failed, so capacity stepped 2×20% → 1×20% → **0** (permanent video
death at ctr 26651) while audio — whose transfers each queue 10 ms, a 10× deeper horizon — never
missed a sample. Both defects are addressed: the deep queue gives ~20× horizon margin, and capture_tagged_bench
**never silently shrinks the fleet** — a failed resubmit is retried from the event loop, logged
loudly, and written to the capture as a tagged `TransferError` record (`pkt_index=0xFFFF`), with fleet
size reported at shutdown. The flat-rational-plateau shape also argues **against** gradual
USB-vs-host clock drift, which would produce a slope, not steps.

**Interior losses proven; the "multi-frame interleave" is a renderer artifact:** a hard-padding
ruler census across all 733 damaged intervals (2,543 padding blocks) finds **1,786 of 1,810
inter-block spacings compacted below one frame period** — the losses are *interior* to the
interval, not a missing tail; 19 spacings exceed a frame period (0.7%, consistent with the padding
block itself being lost), and none show duplication or non-monotonic content. So the visible
mixing of multiple frames in one raster in the damage-review encode is the documented
**prefix-placement assumption compacting interior losses** — not evidence of USB reordering or
clock desync. Reordering among *delivered* transfers measured **0 inversions** across the whole
capture; ordering of the *missing* slots is unobservable in an untagged capture — capture_tagged_bench's
per-packet `submit_seq`/`pkt_index` makes it directly measurable on the next hardware run, which
is the definitive test.

**Pre-collapse drops are phase-locked at ~1 Hz:** even the "healthy" region
carried 130 damaged intervals (~2.1% of units), mostly single-quantum (24,576 B) — and **81 of 127
(64%) land in just two 100 ms phase bins (.7 s and .9 s) of a 1-second cycle** (uniform ≈ 13/bin).
A periodic host task was stalling the default-priority event thread past the old ~6 ms horizon
twice a second; the terminal collapse was this chronic disease going terminal. **Not
deck-correlated** (0.50 drops/s within ±3 s of deck events vs 0.65 elsewhere — an earlier
impression that bursts followed the splice failed this test). capture_tagged_bench countermeasures: threads at
`QOS_CLASS_USER_INITIATED`, the 128 ms horizon, and 1 Hz `TICK` records (type 4, elapsed-ms) so
any residual stall is datable against wall clock.

**Deck full-frame freezes: measured ZERO.** The hypothesis "the TBC never freezes full
frames" converted to measurement: inter-frame MAD on subsampled luma over 4,916 consecutive
program pairs vs the deck-blank static reference (the chain's true frozen-image noise floor,
MAD 0.65–0.76). **Minimum program-pair MAD = 1.53 — 2× the static ceiling; zero program pairs at
or below it.** A TBC freeze would replay a stored frame and land at the static floor; none did.
(Held animation cels explain the ~1.5–2.5 tail: identical cels through two passes of tape noise.)
Within the delivered data there is also no garbage raster — damage is pure absence plus the two
known signal-borne faults (field-1 registration, line-21 H/chroma), never TBC-generated
corruption.

**48-minute tagged capture of fixture A (69.7 GB): provably byte-complete.**
Sustained 181 Mbit/s through a USB 3 hub: **46,075,614 records, zero corrupt;
video 65.247 GB in 23,036,416 packets across 179,972 transfers with seq GAPS = 0; audio 3.319 GB,
287,954 transfers, GAPS = 0; HostLoss 0, transfer errors 0, zero-length packets 0, resubmit
failures 0, fleet 8/8 + 8/8 end to end, ring high-water 3 MB of 256.** Every scheduled USB slot
across the entire tape was requested, delivered, and recorded — the first capture in this project
whose completeness is proven from its own tag stream rather than inferred. The 2,877 tick records
bound any event-loop stall below ~1.04 s (tick jitter max 38 ms, within the 100 ms loop
granularity — ticks cannot resolve stalls below that; the dispositive continuity proof is
GAPS = 0). Analyses stream the file by seek-walking records; a raw endpoint split is never
materialized. Transport completeness does not establish picture quality or source geometry.

**Whole-tape unit census:** USB byte-complete does not mean decoder-unit-exact. Across
86,300 counter periods, the video endpoint contains **86,293 exact 756,048-byte marker
intervals, seven device-short units, zero absent counters and zero counter discontinuities**.
The shorts are counters 4507=371,568 B,
4508=13,008 B, 4509=371,568 B, 4510=371,568 B, 4515=755,824 B, 4520=755,824 B, and
4701=755,824 B. CAP1 packet provenance establishes that these shorts are device-framed, not
host loss; this closes the question of whether the Shuttle can itself emit short units.
Arbitrary endpoint edges add a 1,652,048-byte leading
fragment and 495,376-byte trailing fragment outside the marker-delimited census.

The audio endpoint is also transport-complete, but device audio samples and resync metadata
have localized deficits (audio census below). Unwrap counters and look anchors up by value,
not audio-row ordinal. Review apertures, renderer and deinterlacer policy are in §7.

**NTSC-M setup: preserved in the measured black-card sample (2026-09-09).**
**The measured 0 IRE reference is code ≈ 1.5, not 16**, established three
independent ways: the vertical-interval lines carry a device-WRITTEN dithered constant 1.375 (identical in all five
captures, spread 0.0007; its lag-1 autocorrelation of −0.33 is the high-pass signature of dither, so it is written
rather than digitised); each picture line's own horizontal blanking reads 1.459–1.53; and the relay-muted composite
units, whose active area goes through the same decode path, read 1.533. Against that zero, 7.5 IRE lands near code
18, and it is there. Measured on 95 units of a full-frame black card on the commercial tape, using each line's OWN
blanking as its 0 IRE reference (the classical black-minus-porch measurement, needing no device constant): blanking
mean 1.459 and finished by code 7; picture black beginning at code 12, peaking at 17–18, mean 17.699; **a separation
of 16.22 codes against those same lines' blanking and 16.32 against the vertical interval, which is 7.45 IRE at
BT.601's 219 codes per 100 IRE — NTSC-M setup is 7.5.** It is a jump, not a slope: codes 8–11 carry about five
samples per million, and the skirt below code 15 is the black's own noise (0.0296% observed in codes 3–12 against
0.0506% predicted by a Gaussian at the measured mean and sd), not a ramp into blanking. No clipping at black either:
16.4% at code 16, 24.8% at 17, 24.4% at 18, a smooth distribution with tails ~10× heavier than Gaussian, where a
clamp would make them lighter. Nothing at code 0 or 255 in any capture.
**What IS truncated is sub-black.** With 0 IRE at ≈ 1.5 there is half a code below blanking, so every excursion
under 0 IRE is lost at the floor: the composite capture has 2.576% of samples at code 1 against 0.352% at code 3, a
ratio of 7.3, traced to composite edge undershoot at sharp white text. With black at 16 those would survive to −7
IRE. The black level is not squashed; sub-black content is.
**Attribution is not separated by these measurements:** within one tape, one deck and one S-Video input, black
sits at ≈ 9 in the SP passage, floor-crushed at 2,100 s, and ≈ 24 at 2,700 s — a range as wide as the pedestal
itself. The Shuttle's generated line-21 insert measures 119 codes above blanking on both inputs
(117 on the EP captures), but 125–126 with no input. That establishes an insert-level comparison,
not an isolated measurement of how its analogue decoder treats source black. The
device's no-signal output sits at exactly the captures' blanking level (1.3749 against 1.3750–1.3756).
The upstream recording chain, deck playback processing and Shuttle decoder are not separately
identified by a tape measurement; fixture A's level variation is not a calibrated decoder test.
**No level correction** (owner, September 9): "we don't need to match studio levels LOL. this
is consumer grade VHS tape." His bar is no unwanted clipping or level fix, with the tape appearing
as intended. He accepted the recording VCR's AGC as the explanation for fixture A's variation
and closed the question without further measurement; that attribution is not an isolated-stage
measurement. Nothing in the delivery path remaps levels. The Y16/C128 hard-padding ruler remains
valid but says nothing about programme black; source-level measurements use the source reference,
not an assumed Y16 black point.

**Deterministic replay (`experiments/libusb_replay_shim.c`):** link the unmodified
capture code against the mock instead of `-lusb-1.0` and it replays a `.tpc` through the REAL
callback/ring/writer machinery as if the device were streaming. Proven: 2.83 GB of the actual
whole-tape capture round-tripped **byte-identically** (SHA-256, both endpoints, zero gaps), and
fault injection exercised the paths healthy hardware never fires — a swallowed transfer produced
the mandatory seq GAP in the output accounting, and an injected submit failure exercised the
no-fleet-shrink retry (`failures=1 recovered=1`, gaps 0) for the first time ever. `REPLAY_PACE_US`
paces delivery (16 ms/video transfer ≈ realtime) for clock/A-V-sync/live-path development; the
device timebase is fully reconstructable from the iso cadence + audio resync counters, and replay
can inject synthetic clock skew (off-nominal pacing) that real hardware cannot be commanded to
produce. Not recorded, hence not replayable: original host-jitter finer than the 1 Hz ticks
(a per-transfer host timestamp is the obvious v2 format extension if ever needed) and control-
transfer responses (mock stubs them). An accidental bonus test: unpaced replay outruns the
writer and the ring overflow machinery emitted exact HostLoss records — the honesty path works
under overload.

**capture_tagged_bench hardware smoke test:** 30 s at 179 Mbit/s through a USB 3 hub with
**zero submit-seq gaps on both endpoints** (complete scheduled-slot continuity, the claim capture_untagged_ring
could never make), 0 iso errors, 0 inversions, 0 HostLoss, ring high-water 0. 471k records, 0
corrupt. Shutdown cancellations are now accounted separately from
errors, and fleet size is reported from before cancellation.

**Untagged damage reconstruction:** marker endpoints and uniquely placeable hard-padding
blocks are hard position evidence. Temporal matching between those anchors failed known-answer
tests on fades/uniform grey; such placements are diagnostic, not byte-position-authoritative.
Tagged captures use packet provenance instead of this rescue path.

**Design decisions:**
- **Correction-decision log:** record per-unit registration decisions, their evidence and
  unavailable measurements in an optional sidecar. This supports later audit/repair; it does
  not authorize a particular estimator or lookahead on the live path.
- **Review-encode damage policy:** never blank or repeat. Render corruption **as-is** (surviving
  bytes at their positions); genuinely absent bytes get an unmistakable standard-NTSC-style
  no-signal fill, documented, with the placement assumption stated for untagged captures. Purpose:
  drop *patterns* must stay visible and inspectable.

**Writer output rule:** no encoder or capture writer may create or grow its working file
inside a cloud-synced (File Provider) root, even under a hidden or `.partial` name — a dataless
placeholder or an in-flight sync corrupts a growing file. Growing TPC, MP4, PCM, and decision-log files live in a non-synced scratch
directory. After the writer closes and validation succeeds, publish with one same-filesystem
atomic rename. For a multi-gigabyte media file never fall back to copy+delete; a small FINISHED
file (a sidecar CSV) may be published to another filesystem by a staged, fsynced, read-back-verified
copy followed by an exclusive rename, then deletion of the scratch copy (owner, 2026-09-04: a
recording may live on a cloud volume such as a LucidLink filespace). Filesystem identity is checked
before work begins and selects the path. An unfinished capture remains in scratch for diagnosis/recovery.
The destination above describes final publication only, not the writer's working directory.

**Archival re-registration does NOT require a full-raster master (owner decision, 2026-09-03).**
The normal recorder records the corrected 480i as an ordinary downstream consumer; a 525-line
FFV1 master in the service was proposed and rejected as an extreme-edge-case tax. A whole-line
re-registration of a 480i recording lacks the 1–3 raster lines outside the crop; those lines sit
in the head-switching / line-21 region, so the accepted archival repair is an edge-duplicated or
estimated whole-line shift, recorded in the sidecar as a substitution. Where lossless repair is
actually wanted, a `.tpc` of that segment (explicit debug sink; requires replaying the segment)
is patched into the recording. The live-path requirement is that the sidecar carries per-unit
applied field placements, the observations that produced them and the interval label, so an
offline pass can locate and re-shift affected units.

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

**Field order: TFF in the tested capture** — stored chronological field 1 → **top** field.
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
heads disengaged, the tested deck configuration retains output: a **grey mute screen with
OSD and a running tape counter**.
Consequences:
- **`0x0800` never occurs anywhere in this capture** (0 hits in 5.57 GB); no green pseudo-frames,
  no ~30.13 Hz cadence. Format stayed `0xe801` and the rate stayed **29.97003 fps exactly**
  throughout that window. Stopping the tape was not a no-input test; the later disconnected-input
  measurement is recorded below.
- The blank raster is **near-neutral grey, NOT green** (Y 120.6 ±0.1, U 129.9, V 127.3).
- Two runs of **exactly 19 frames** bracket the blank period with **luma Y 1–2** and chroma
  pinned at 128, near the measured blanking floor rather than Y16 programme black. The working
  explanation was the deck's output relay muting to 0 V.

**Deck mute observations (including the later tagged virgin-tape measurement):**

| Deck state | S-Video output |
|---|---|
| Non-playback transport mode (stop, rewind, FF) | grey mute + OSD |
| Playing, servo locked | program |
| Playing, unlocked — **transient** (relock windows) | snow, ~0.7–2.3 s, re-timed into valid `0xe801` units |
| Playing **virgin tape** (no CTL, no RF), steady state | **NOT grey mute — MEASURED 2026-09-03 (`captures/virgin_transition.tpc`, 45 s, byte-complete):** the deck outputs **sub-blanking black (Y ≈ 1.5–2, chroma 128) with sparse white dropout streaks and a noise band at the bottom of the raster**, all in locked `0xe801` units; the OSD (if enabled) is composited over it. The earlier "grey mute" came from a **deck setting** (a mute/back-screen mode the owner has since switched off); with it off the deck passes its raw no-RF output. So the grey rows in this table describe that setting, not the deck's only behaviour — one more reason states are defined by signal properties, never by deck (design rule below). Deck-specific tell for the inference layer: with OSD display set to off, this deck still composites its OSD when playback is fully unlocked (no control track) — an OSD appearing over a sub-blanking raster is strong no-RF evidence on this family, usable by the deck-mute score, never as a state definition. The end-of-recording transient was short (~0.5 s: flat → sub-black → 2 snow-like units → black), not the 1.7–2.3 s snow relock seen after splices — a virgin section has no CTL to chase. |

So snow is only the *acquisition transient*; the deck's steady-state answer to unlocked playback is
its mute screen — or, with the mute setting off, its dropout compensator's output. **Likely mechanism
(interpretation, 2026-09-03, from the virgin-transition render):** a plain VCR shows snow because its
FM demodulator turns head/tape noise into luma; this deck shows sub-blanking black with sparse white
specks because the dropout compensator's RF-envelope detector marks every no-RF line as a dropout
and clamps it to blanking, and only momentary envelope excursions above threshold demodulate as
bright bursts. The ~7 s before that (frame TBC holding/repeating every other frame) is the erased
tail of the recording where control-track pulses are present but failing. Other decks fill the same
regenerated raster with snow, blue or black — the classifier labels appearance, never the fill. ("The rest of the tape is snow" describes the tape's magnetic content — what this
deck *shows* for that content is mute.)

**⚠️ 17.7% of complete units are structurally perfect non-picture** (1,093 of 6,160: 1,017 deck
blank, 38 snow, 38 sub-blanking black). Every one is a full 756,048-byte `0xe801` unit with a
monotonic counter — **in-band indistinguishable from good video.** Relock after the splice took
51 frames (1.70 s) and after the restart 69 frames (2.30 s), emitting complete well-formed units
of pure snow the whole time. This is the hard number behind "format classification is not a
quality guarantee": **in-band framing cannot establish signal state** (see also the dead-end header
result in §9 — and note the `214/16` status register is still un-probed across states).

**→ Signal-state classification is therefore a real design problem. Do NOT reduce it to one
`signal_valid` boolean.** Three separate layers, each recorded:

1. **Transport state** — exact unit / partial unit / packet hole / absent video / counter discontinuity.
2. **Raster appearance** — program-like / snow-like / deck-grey / sub-blanking mute / device
   no-signal / flat-ambiguous.
3. **Source-state inference** — present / reacquiring / deck-muted / no input / **unknown**, with
   confidence.

**`SubBlackMuteLike` on a degenerating passage is NOT a mislabel** (owner, 2026-09-09): "the label sub mute black
like is not a miss. that is actually what the picture looks like before it degenerates into snow." Measured at 27:18 on fixture A (unit
index = device counter − 4511), the sequence through a signal stop is **programme → wrecked → sub-black →
snow-like → deck grey mute → programme**, with these boundaries:

| units | time | mean | std | adjacent-row corr | temporal corr | stage |
|---|---|---|---|---|---|---|
| 49095–49104 | 27:18.14–.44 | 60–62 | 48–51 | 0.89 | 0.98 | programme |
| 49105–49112 | 27:18.47–.70 | 17–72, swinging | 31–92 | 0.56–0.77 | −0.17 to +0.26 | wrecked |
| 49113–49117 | 27:18.74–.87 | 8–16 | 6–29 | 0.93–0.98 | — | sub-black |
| 49118–49125 | 27:18.90–27:19.14 | 17→41 | 31→48 | 0.62 → 0.18 | 0.77 → 0.21 | snow-like |
| 49126–49163 | 27:19.17–27:20.41 | 117 | 16 | 0.75 | 0.998 | deck grey mute |

The sub-black stage is a real appearance, not a level error to fix. The historical classifier
also called torn and snow-like units programme or mute, and retained a sub-black label onto
grey mute. Those are separate classifier observations, not evidence of a registration state.

**Whole-tape signal-state audit — historical results, September 9, over all 86,293 units
(independent instrument joined to that revision's classifier log).** These are observations and
failure cases, not the current classifier's score or a replacement specification. **The tape carries three
genuine non-programme events totalling 10.9 seconds**, every one confirmed on the raw 525-line raster — the tape
start (units 0–214: deck grey mute with OSD, then a completely black raster, then relock snow), the boundary
between the two recordings (43,678–43,729, one torn unit then snow then grey mute), and 27:18 (49,105–49,163, nine
violently torn rasters then black, snow, grey mute). The deck's grey-mute fingerprint (mean 115–125, σ 14–18,
temporal r > 0.99 in both fields) matches 228 units in six runs and **every one lies inside those three events**.
A ~99-run flat list reconstructed to the same shape is **96% ordinary programme**: 54 runs vertically coherent
throughout, 21 carrying saturated chroma, 15 fade bottoms. Five 9-unit sequences at units 45719/48115/48642/49560/
57488 have matching statistics in matching order and a large coherent saturated U plane where relock snow carries
no chroma at all: recorded content, not noise.
**In this audit, `SnowLike` fired only twice** (43,693–43,694), both on real snow; no programme
was labelled snow. The other observed errors were:

- **The tested `SnowLike` rule lacked temporal and vertical-coherence terms** (`luma_sigma > 35 && spatial_gradient_energy > 30 && program_extent_fraction > 0.50`). Torn rasters retaining high sigma/gradient read as programme, including the 27:18 event and tape-start relock units 196–212. At 49,106/49,109/49,112 adjacent-row correlation remained 0.95–0.97 while temporal correlation was ≈ 0: vertical coherence alone did not distinguish those torn rasters, while the temporal measurement separated these examples.
- **The appearance latch is asymmetric.** The logged appearance is `stable_appearance`; `SubBlackMuteLike` (like `DeviceNoSignal0800`) installs with NO confirmation while leaving it needs three consecutive identical observations. At 49,126–49,136 it therefore persisted 11 units (0.37 s) onto a raster measuring mean 117–118 — the deck grey mute — with confidence 1.00 and nothing in the raster changing at the switch. This is the "sub-black label on grey" the owner saw.
- **`NeutralGrayMuteLike`'s rule tests uniformity, not greyness**, so 253 units of near-black programme (mean 15–38, against the deck's actual grey mute at 117) carry a label and a `Muted` source that assert a deck mute. 122 false positives in all, none of them snow.

**Replay caveat found by the same audit:** unpaced replay overflowed its ring without a failing exit code. On
`fulltape.cap6` it produced 20,933 holes and only 991 exact units, then **exited 0**: the 256 MB capture ring
overflows against a reader going at ~1 GB/s, its HostLoss becomes parser holes, and the tool prints no
capture-level loss counter. Re-run at `--pace-us 8000` (2× realtime) it is 86,293 exact, 0 holes, 0 drops, ring
high-water 0. Use `--pace-us 8000` for a whole-tape replay, or a ring larger than the file for a slice; never
trust an unpaced whole-tape run's exit code.

**Commercial-capture opening** (owner, September 9): the examined source begins with near-blank
output and sparse white specks before picture arrives, consistent with the deck playing tape
without usable RF rather than a flat relay mute. The owner accepted leaving its initial
mute-labelled interval unregistered: "It's the tape coming in... You are trying to do the
impossible which is register the difference between the first fade from black on tape and real
picture. That should stay unregistered." This source-specific decision does not make every
near-black programme interval a mute. Capture-1 selection and field-arrival details are in §7.

Useful features: exact hard-padding runs + VBI-signature confidence; active-area luma/chroma mean,
robust variance, percentiles; fraction of neutral-chroma and sub-black pixels; spatial gradient
energy and adjacent-line correlation; same-field temporal correlation; a **snow score** (high
broadband variance + low spatial/temporal coherence); a **deck-mute score** (persistent neutral
grey + recognizable OSD regions); exact/near-exact frame fingerprints for repeat detection; audio
RMS/mute state as supporting evidence; and **audio resync counters as the expected video-slot clock
when video is absent**. Run these through a **temporally hysteretic state machine that is allowed
to answer `Unknown`**.
⚠️ **"Snow-like" does not prove relock** — a recording can legitimately *contain* broadcast snow.
Preserve and publish it by default; live concealment is a separate, user-selected policy.
⚠️ **Post-TBC content analysis cannot always separate recorded snow from playback-relock noise.**
Recorded tuner snow (real helical tracks + CTL, noise content) and virgin-tape/no-RF playback are
*magnetically* very different, but a TBC deck re-times both into perfectly locked output rasters —
`0xe801` asserts only that the **output raster** is locked, never that the recorded source had
valid sync. So: **label observations, don't claim unknowable provenance** — appearance labels
(program-like / snow-like / neutral-grey-mute / sub-black-mute / no-transport / unknown) plus a
*separate* contextual inference (e.g. `LikelyRelock`) built from surrounding cuts, OSD, audio,
duration, transport history.
⚠️ **Generalize by property, never by this deck (design rule).** Every state above was measured
through ONE deck (a JVC D-VHS with a TBC that launders everything into a valid raster). Other
sources will behave differently: a TBC-less VCR can emit genuinely unlocked signal (and the
Shuttle's response to unlocked video is not established by the no-input test below); mute screens vary per deck
(grey here, blue elsewhere, black, OSD or none); relock transients differ. Define every classifier
state by its **observable signal properties** (luma/chroma statistics, coherence, temporal
behaviour), not by "what the HM-DHX2 does" — deck-specific knowledge may *inform* an inference
layer, never define a state.

**Device NO-INPUT behaviour — MEASURED (2026-09-03, `captures/shuttle_no_input_45s.tpc`, 1.13 GB,
45 s S-Video with the deck powered off; transport byte-complete: 743,727 records, GAPS 0,
HostLoss 0, errors 0).** The Shuttle with nothing on its input does NOT sit in one state:
- **`0x0800` finally observed** (1,089 marker units): pseudo-frames of the full **756,048-byte
  525-line unit size**, monotonic counter, ~30 Hz. First 5 units at startup, then the last ~28 s.
  Content (second capture, `captures/deck_hdmi_mode_output_drop_30s.tpc`, deck output dropped by its HDMI
  mode engaging — a deck-side cable pull, transport byte-complete): a **flat synthetic raster,
  Y ≈ 12 ± 4, chroma bytes far from neutral (U ≈ 188 or 76, V ≈ 0 — renders deep blue in a naive
  UYVY decode; bmusb called it green), no hard-padding ruler, consecutive units not
  byte-identical.** When the deck's output returned, the Shuttle relocked to `0xe801` (no-RF
  sub-blanking black, padding ruler back) with a counter jump 4961 → 5162: a second epoch instance.
  ⚠️ This is *absence of input*, not unlocked video — the unlocked-input experiment is still owed.
- **`0xe809` — the PAL-family code — for ~15 s (444 units)** with the decoder free-running: units
  alternate **436,368 B and 463,728 B = 48-byte header + 303 and 322 lines × 1,440 B**
  (303 + 322 = 625). So in the PAL family the device emits **one field per unit with unequal
  line counts**, not one 625-line frame. This is device framing observed from the device itself,
  but from a free-running decoder, not a PAL signal — it promotes the P6 PAL framing from
  hypothesis to "measured shape, unverified against real PAL content".
- **`0xe801` for ~2 s at startup (66 units)** classified sub-black mute / a few program-like:
  the decoder's initial guess before it gave up; 34 exact units, 28 device-short.
- **A counter epoch restart** at the `0xe809`→`0x0800` transition (raw 534 → 329): §8 property 5
  (never extend the 16-bit counter across an ambiguous restart) has its first real instance.
- **Iso packets shrink to ~2,848 B** (every packet "short" vs the 15,360 B request) while the byte
  rate stays ≈22.6 MB/s: packet length is a scheduling artefact, never a unit-validity signal.
- Parser + classifier handled all of it without a fixed-raster consumer ever seeing a wrong-size
  unit (other-format units kept out, `DeviceNoSignal0800` appearance, `NoInput` source).
- ⚠️ Lesson: an **unpaced `frameserver_replay` overflowed the 256 MB capture ring** on this file
  (byte-at-a-time parser slower than disk) and the resulting holes were *replay* host loss, not
  capture loss — visible only via the verifier, because `frameserver_replay` did not print
  capture-level HostLoss. Replay with `--ring-mb` ≥ file size or `--pace-us 16000`; the tool must
  surface capture-core loss (fix queued).

**Classifier v0 on the virgin-tape capture — three real-data defects, FIXED (main `f2f445e`, mutual
review, two rounds): robust luma/chroma medians and a 15×15-tile program-extent measure; a
sub-blanking neutral raster (median Y ≤ 12) is `SubBlackMuteLike` by veto regardless of streak or
OSD edges; a localized static overlay over a flat raster cannot imply program; asymmetric
hysteresis (5 units to enter program/reacquiring, 3 mute/no-input, 2 ambiguous); `unsettled`
settles from the phase actually applied on the forward-only path; and a **host-side shed (PoolFull,
ring drop) is absence of evidence, never a source transition** — the frameserver tells the
classifier via `signal_context`, which holds every inferred state and clears only temporal raster
history (a parser hole still resets). Paced replay of the capture: OSD-over-black span
Program/Present 786→0 rows, tail flapping 148/227→0, unsettled 1,396→53 of 1,396, begin_segment 3;
5-minute registration action check 0 differences in 9,097 units. Original findings:** (1) sub-blanking
black with sparse dropout streaks flapped between `SubBlackMuteLike` and `ProgramLike` every ~2
units for 7 s — gradient energy from the streaks passes the program test; a raster whose luma sits
below blanking must veto `ProgramLike` outright. (2) The deck's OSD over black-with-noise classified
as `ProgramLike`/`Present` for 26 s (the OSD text supplies edges): the planned deck-mute score with
OSD-region awareness is needed, and `Present` must not be inferred from overlay content alone.
(3) `unsettled` stayed 1 for every unit of two clean 45 s captures (1,385/1,385 and 1,387/1,387):
the unsettled interval never closes on the live path. Transport/parser were flawless on both
captures (GAPS 0, HostLoss 0, errors 0).

**Hardening pass (2026-09-03, main `f75dccf`) — an external static review of `capture_core` and
`frameserver`, verified independently by both agents, then three mutual review rounds under the
§14 rule.** Of the 15 external findings, 11 were confirmed, 2 refuted by measurement (Apple
`aligned_alloc` sizes are multiples of alignment by the C object model; the classifier already
guards NULL payloads), 2 partial. The whole-system read added defects the diff could not show:
holes/short/unframed discontinuities never reached the registration engine; loss stats were
pending-since-flush, not cumulative; a full data ring could suppress the report of its own
overflow; an initial submit failure silently shrank the fleet; recorded transfer errors were not
replayed; two stale-snapshot drain races at termination. **Fixed, each with a deciding test
(barrier-controlled races, fault-injecting shim, small-ring build, falsified against the old
code):** joined lifecycle state machines in both libraries (elected stopper, callback-thread
refusal, failed-start rollback, no `on_end` for a session that never started); start succeeds only
after the full 8+8 fleet is submitted; permanent resubmit failure ends the session after a
configurable deadline (`CC_END_TRANSFER_FAILED`); coalesced, non-truncating, cumulative HostLoss;
a control-record reserve plus a **one-time in-stream "control truth lost" marker** (`XFERERR`,
pkt_index `0xFFFE`, status `UINT32_MAX`) — **default: mark once and continue (§8 property 7);
`fail_stop_on_control_loss` opts into termination**; pool-full sheds bytes but never the
observation (`drop_reason=PoolFull`); ring-full loss is attached to the first retained post-gap
row with a reserved `RingFullTail` slot so every missing range is chronologically locatable
(sidecar schema 2, `schema_version` column); publisher exhaustion named; exact conservation
`published + PoolFull + PublisherFull == exact_units` and `exact_units + eligible ring drops ==
eligible_observations`; every transfer freed at stop (`transfers_allocated == transfers_freed`);
init checks alt1/alt2/mode/latch/input; the CLI names end reasons and the SESSION note now carries
input, mode word, ring size, fleet and loss policy. **Deferred, named OPEN, not implied complete:**
submission-order reconstruction (API now promises callback-completion order + tags until the
inversion mock exists); live stats are after-stop-authoritative; the sidecar's full raw-evidence
columns; audio serving.

**The hard-padding ruler is Shuttle-side digital fill — measured September 3.**
All coordinates in this paragraph are **zero-based storage rows**, not NTSC line numbers
(convert with §7's rule). The 18 padding rows (0–6, 261–269, 523–524) are exactly Y16/C128
with zero variance in the examined `0xe801` units, including 34 with no deck connected and
300 with the deck on an unconnected input. Content beyond row 260 in field 1 or 522 in field 2
cannot be recovered from those padding rows; reading them returns device fill.
The four near-blank rows below each field (257–260, 519–522) were not hard padding:
Y ≈ 1.4 ± 0.5 with no input, but averaging Y31 ± 29 on the programme tape.
A 3,000-unit average found picture at rows 20–256 / 282–518, VBI signatures at 17/19 and
280, about ten decoded-blanking rows above and four near-blank rows below, then padding.
Those are population observations, **not output-aperture definitions or fixed picture bounds**.

**Whole-tape audio timing — measured September 3 over all 86,302 resync intervals,
with transport byte-complete:** 51,773 intervals of 1602 samples
and 34,522 of 1601 — a steady-state mean of **exactly 1601.6 samples per unit, i.e. the audio
sample clock is locked to the video unit clock with no measurable rate offset.** The entire
5,557-sample deficit sits in **seven intervals**: five at capture start (counters 4506–4510:
1272/787/28/787/787 samples — the same units the device emitted short on the video endpoint, a
device startup hiccup), one at **1021.5 s** (counter 35119: 1579 samples, 23 short) and one at
**2066.2 s** (absent `DeckLinkAudioResyncT` record 894→896, sample index 99,177,246:
2020 samples over two units, ~1,183 short). The two mid-tape events are **audio-endpoint-only
device events**: video units remained exact, with no coincident cut/relock/mute identified in
the audit. Transport completeness does not imply the device supplied every expected audio sample.
**Consequences:** global tempo correction is not justified by these localized deficits; an A/V
adapter must apply the audio publisher's **correlation residual only where it steps** (a
discontinuity event: advance audio time by the lost samples once, flagged) and never resample
continuously; video timestamps come from the unit counter and audio from the sample count, which
agree exactly between events. The earlier ≈36 ppm/`atempo` interpretation and periodic
video-repeat proposal were withdrawn: these measurements show localized discontinuities, not
a steady clock-rate mismatch.

**✅ Audio is a viable continuity master** (validates §9's approach): 8,991 resync records,
counter `18706 → 27696`, **every step exactly +1, zero exceptions** — across the splice, the stop,
the rewind, the relock, and 35 s in which the video endpoint delivered **zero bytes**. Spacing
alternates 1601/1602 samples. **Corrected figure:** three anomalous intervals occur at *startup*
only (`18708→18709` = 870, `18709→18710` = 784, `18710→18711` = 1589 samples); from counter
**18711** onward, 8,985 intervals average **1601.600334** against the ideal 1601.6 — a residual of
**+3 samples total**, i.e. essentially perfect. (An earlier "271 samples / 5.6 ms drift" figure
was wrong — it folded the startup anomalies into the slope.) Audio mute runs also independently
locate every deck event. ⚠️ Caveats: no 16-bit wrap occurred (27,696 < 65,536) so **wrap handling
remains untested**, and **counter continuity does not prove audio-payload completeness** — the
startup intervals are proof that the two are separate claims.

**Untagged transport collapse:** the delivered fraction falls 99%→60%→~40%→~19%, and the video endpoint delivers **zero bytes from ctr
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

## 7. Registration: current question, sources and accumulated evidence

This section keeps the useful evidence and the short history, not a prescribed
replacement algorithm. Measurements below belong to the named material and
instrument; they are not rules for every tape. Main's implemented behavior and
the later v10 experiments are distinguished in §11.

### The question we are trying to answer

The owner's September 14 description: find the data-like lines, where real
picture begins, and the blanking lines between them. Waveform recognition is
being pursued because it may supply a stable top-of-picture landmark. Automatic
measurement matters; asking a person for each crop or shift leaves that question
unanswered.

The current top pattern being investigated is line 21's caption in both fields,
then line 22's caption/waveform/blanking, then picture. At the bottom, the owner
is looking for a fully blanked line bounding the picture, with the head-switch
region included in the geometry. These name signal objects, not a fixed set of
storage rows to inspect.

The physical idea is that a reliable top and bottom gauge should move together
when picture position changes: extra blank space below for an upward shift,
above for a downward shift. An isolated content-edge change is not the same
observation. This is the owner's current line of investigation, not evidence
that the existing gauges already implement it correctly. Field order and
relative alignment also need to be established to produce a coherent weave.

The September 14 pause is for understanding the accumulation of complexity.
This rewrite does not authorize another detector or select a new model.

### Coordinates and layers

Use **NTSC line numbers when talking to the owner**, not storage rows.
For this raster, NTSC line = zero-based storage row + 4 in both fields:
field-2 rows 279/280/282 are lines 283/284/286.

- **Storage row:** zero-based row in a delivered raster.
- **Raster line:** NTSC numbering used in a particular report; field-relative
  numbering and whole-frame numbering must not be mixed.
- **Source line:** the line carried by the source, which can land at a different
  raster position after displacement.
- **Temporal order:** which field happened first; distinct from spatial parity
  and from which fields the device grouped into a transport unit.

The measured NTSC unit contains 525 rows of 720 UYVY samples after its 48-byte
header (§6). Main's 480i aperture begins at storage rows 19/282, labelled NTSC
23/286. Early tools instead called 17/280 their origins because they included
the insert region. A number from one convention is not a crop in the other.
The 480-line output has 240 selected rows per field; that does not establish
which source rows were delivered or where their boundaries lie.

A row is a time sweep. In the recorded timing model, 720 delivered samples cover
about 53.33 µs of a 63.56 µs line; the full line is 858 samples at 13.5 MHz.
The omitted 138 samples matter for censoring. An unobserved switch instant is
not an entirely unobserved blanking interval: the nominal 10.9 µs blanking
interval is about 147 samples, wider than that omitted region. These numbers
constrained an earlier synthetic example; they do not locate an actual switch.

**Colour burst:** the normal burst (5.300–7.814 µs after 0H) ends before
the delivered window starts (122 samples / 9.037 µs). The relocated-blanking
probe also found no recoverable burst, while recovering injected controls.
That is the measured limit of this raster/probe, not a result about raw RF.
See `experiments/burst_probe.py` and `experiments/switch_cohort/BURST_RESULT.md`.

Keep source picture, deck output/OSD, device inserts and hard padding separate.
Hard padding is a transport ruler, not the source's black or blanking reference.
Comb can constrain relative alignment without establishing both absolute
positions. Neither a stable crop nor agreement between related estimators
establishes that the physical landmarks were identified.

### Capture inventory — keep this even if the experiments are retired

“Fixture A” means the off-air SP/EP test tape described in §2. “Capture 1” in the
later four-capture work means the commercial tape, not fixture A. The whole-tape
file is a separate, longer input, not a fifth independent source.

| Input | Material and reason it matters | Recorded location / provenance |
|---|---|---|
| Capture 1 | Commercial tape, composite input, recorded with V-stabilize/line TBC off. Opening rewind/acquisition, a dark boxed card and brighter programme exercise different visibility and level regimes. A comparison source distinct from the two off-air recordings. | `captures/composite_program_30s.tpc`, captured 2026-09-03. |
| Capture 2 | EP part of fixture A. Different recording conditions, data-like top lines, sometimes no blank row between data and picture; tests whether an SP-derived gauge generalizes. | `/private/tmp/hw-session/w_2100s_aligned.tpc`, sliced from `captures/fulltape.cap6`, byte start `50811787037`. |
| Capture 3 | SP part of fixture A, V-stabilize on. Contains the field-position problem, weak recorded timing and the corrected head-switch-region appearance. | `/private/tmp/hw-session/w_300s_aligned.tpc`, sliced from the same whole tape, byte start `7260251349`. |
| Capture 4 | Another SP pass with V-stabilize off. Exposes stronger horizontal timing disturbance near the switch and a different transport pairing; not a frame-aligned A/B of capture 3. | `captures/sp_vstab_off_aligned.tpc` (SHA-256 `d6fbd509…`), cut at byte `118907896` from `sp_vstab_off_45s.tpc`, captured 2026-09-07. That original no longer exists, so this is the only copy. An older cut, defective and a strict subset of this one, was deleted on 2026-09-16. |
| Whole tape | Approximately 48 minutes / 69.7 GB, both off-air recordings plus transitions and non-picture intervals. Its wider variation found failures missed by the short selections. | `captures/fulltape.cap6`; older notes/tools also use `whole_tape.tpc`. Verify identity rather than assuming an alias. Historical replay: 86,293 exact units; short/other observations are accounted separately (§6). |

The aligned scratch slices were re-cut on September 9 after the slicer was
found to align to CAP1 records but not complete transfers. Their previous
provenance failures were slicing artifacts. `experiments/tpc_slice.py` on the
v10 branch records that repair. Preserve input hashes, cut lengths and transfer
alignment when reproducing a selection; the starts above are navigation aids,
not complete manifests. These paths were inventoried, not re-opened for this
rewrite. Scratch may disappear. Captures 2 and 3 can be re-cut from the whole tape; capture 4 cannot,
so keep its `captures/` copies (a new one needs another pass on the deck). No new tape run is authorized by this inventory.

**Captures 3 and 4 pair their fields one field apart** (measured 2026-09-16 on the current cuts).
The owner saw it first in a side-by-side render: "one of the 3 [corrected by the owner: "one of the 4"]
panels was changing at a different time.. and I'd expect 2 to do that, not 1... and I'd expect it to
match both units".
- The cuts start one unit apart in content: capture 4 unit u lines up with capture 3 unit u−1.
- Across 63 sampled units, capture 4's slot 1 best matches capture 3's unit u−2 slot 2, and its slot 2
  matches capture 3's unit u−1 slot 1, each in 56 of 63 units with a clear margin.
- At all five scene changes checked (capture 3 units 48, 128, 169, 297 and 522), capture 4's two slots
  switch in the same unit, while capture 3's slot 2 switches one unit before its slot 1. The panel out
  of step is capture 3's.
- If the source's cuts fall on frame boundaries (usual for edited video, not guaranteed for
  film-originated material), capture 4 pairs fields as the source did and capture 3 is the offset pass.
  That is the reverse of the earlier assumption. It does not settle which pass puts each field on
  its correct spatial row.
- An earlier six-unit check (2026-09-06, old cuts) pointed the same way but was reported selectively.

Some v10 harness runs used `--repair` on capture 4. Every comparison must say whether it uses raw
slots or repaired pairing, and which unit offset; field-number joins can otherwise compare different
times. This observation does not say every TFF/BFF problem has this cause.

Capture 1's later tests often select counters **≥6667**. That was the chosen
registration interval, not the first sample of picture: the recorded arrival
is between the fields of counter 6610, followed by a dark/fading opening.
Older “stable from 6593” statements and all-unit results are different
selections. Keep startup in its own accounting rather than making it vanish.

Useful whole-tape slices recorded with `tpc_slice.py`:

| Passage | Start byte / requested video bytes | Use |
|---|---|---|
| Start / unit-300 splice | `0 / 320000000` | Initial acquisition and a recorded tear. |
| 27:18 signal stop | `39439481630 / 340000000` | Programme → damaged/sub-black → snow-like → grey mute → return. |
| Recording boundary | `35000331301 / 260000000` | Distinguish transition behavior from ordinary picture movement. |

The late-tape region near minute 43 is also important: intermittent picture on
nominally blank top lines and long intervals without a usable caption exposed
one-line ambiguity. See the main v9 history for the exact selections.

The original five-minute untagged capture is an additional historical diagnostic,
not one of these four. It contains useful OSD/registration observations but also
host scheduling losses described in §6. Do not use its readable-unit count as
complete transport coverage.

### Source observations worth carrying forward

**Why the source descriptions matter.** SP and EP are different recordings,
not interchangeable speed labels on the same signal. The commercial card and
bright programme are also different regimes within one capture. The comparison
passes differ in deck processing and pairing. Keeping these distinctions
prevents a reference learned on one selection from quietly becoming “the tape.”

**Picture displacement versus device raster.** In the early five-minute
capture, hard padding and the insert spacing remained rigid while the SP
picture moved in one- and two-line plateaus, predominantly in field 1. The raw OSD
stayed put while the picture behind it moved. Correcting the picture then
moved the OSD in the corrected render, which briefly led to the opposite
interpretation. This is useful evidence about layers on those events, not a
permanent instruction to hold field 2 fixed or to rule out pairing errors on
other captures.

**Deck setting.** The later A/B identified `Vスタビライズ` as the relevant line-TBC
switch on this deck. The old recommendation “TBC on, V-stabilize off” treated
them as independent controls and should not guide a new session. Record the
actual setting with each input. Off-setting material exposes peaks and
horizontal disturbances that the on-setting pass often replaces or suppresses;
which source geometry remains observable depends on that processing.

**On/off comparison.** The recorded affected-row selections found 768 flat
rows among 1,076 with the corrector on, against none in the off selection.
Using a separate absolute horizontal-displacement criterion of ≥6 samples,
the counts were 11 on versus 1,957 off. The timing difference is substantial,
not categorical. These are different selections/statistics; 768 is not 100%
of 1,076, and horizontal sample displacement is not vertical registration
`d`. The captures were not frame-aligned, so these results do not establish
what happened to the same instant in both passes. Detailed measurements and
instrument names remain in the September 9 notes and v10 reports.

**Black and blanking.** The measured levels in §6 are retained. In particular,
95 units of a commercial full-frame black card gave picture mean **17.699**
against those lines' own blanking mean **1.459** (difference about 16.2 codes).
Other selected dark/band runs approached blanking; that does not establish
source-wide clipping of black picture. The earlier “same dither” claim was not
established by equal means and standard deviations. Later texture comparisons
also had selection and adjacency defects, so neither universal identity nor a
universal texture separator follows. Distinguish the hard-padding code 16,
device fill near 1.4, and the source's qualified blanking before using a level.

**Device inserts versus tape captions.** Lines 20/283 carry the Shuttle's
pulse/timing insert; 21/284 carry its re-encoded CEA-608 waveform, not the tape's
original waveform. They are placed relative to detected sync and can disappear
when sync is lost (seen at whole-tape play-start mute and with no input).
The slicer re-encodes decoded bytes, otherwise emitting nulls while the insert
is present. Identical bytes produced repeatable waveforms; displaced raw tape
captions were noisier and higher-amplitude in the examined recordings.
Fixture A demonstrated re-encoding despite a rigid **+1** picture displacement;
raw captions at +2/+3 instead accompanied null inserts. These observations do
not establish a symmetric slicer range. Insert bytes therefore do not locate
the tape's line 21 or prove zero displacement. Source: the v9 VBI measurements
in `c91a10b:CLAUDE.md`, §11; broader history in `docs/registration_archaeology.md`.

**Line 22.** The September 13 correction identifies the examined line-22
blanking as deck output, not an unconditional Shuttle-written constant.
Its luma followed deck grey mute (about 123.6), while the device's lines 20/21
kept their insert patterns. This is why the older “everything above line 23 is
overwritten” statement was reconsidered. Keep the measured configuration and
line coordinates attached; a tape's line 22 wandering into picture is a source
object, not a command to inspect fixed raster line 22.

**Output apertures** (owner, September 4; 486 origin corrected September 9):
720×480 is the clean aperture beginning at NTSC 23/286. The alternate
720×486 mode retains the insert/caption region: lines 20–262 / 283–525.
For 486 rendering, the tape's real lines 20–22 replace the Shuttle's where
measured displacement exposes them; at d=0 there is no exposed tape material
to substitute (owner, September 10; clarification recorded in the v10 contract).

**Top-of-picture observations, September 14.** The transcript's raw-row work
distinguished the following cases; these are examples, not exhaustive labels:

- Capture 1: the examined programme had picture at nominal 23/286, after the
  insert region and blank line 22/285. The boxed card was different: at counters
  6700/6731/6760, line 23 carried signal to about sample 320 then blanking;
  line 286 was blank throughout. Do not transfer the programme's top to the card.
- Capture 2: data-like lines around 23/24 and 286/287, sometimes immediately
  adjacent to picture; a blank separator is not always present.
- Capture 3: examples of a caption at 23 with a flat low-level row below it.
- Capture 4: examples of a caption at 286 over a row that begins dark and
  becomes picture partway through its sweep.

The mixed/pedestal line called “capture 2 line 286” remained a disputed label
during the waveform experiments. Do not silently make an old score file its
definition. The useful observation is the actual waveform/picture relationship,
including whether the intervening line is blank, flat source content, mixed,
or not yet identified.

**Boxed card.** Capture 1 contains a dark boxed card whose visible content
extent changed with exposure. At counter 6700 a census read content around
54–236 in field 1 with corresponding field-2 content. The supposed ~23-line
“gap to switch” was largely the lower box bar: the instrument had measured
the content interior and called it the box. Keep the distinction between a
box and its content, and exposure-dependent visibility and motion. Neither
that count nor the window-forced bottom was a measured box boundary.

**Half line.** On two grey-mute events, 205 units showed one additional
partly filled row in field 1. Its fill fraction was about 0.4257, close to
the 0.4264 predicted from a 429-sample half line and the delivered aperture.
This was a useful observation on full-field fill, not a continuous order
detector: the necessary fill was not present in the four programme selections,
including the pairing-anomalous capture. The whole tape retains the mute
examples; a classifier's “grey” label alone did not select them reliably.

**Head-switch endpoints.** Earlier work used T for a partial/disturbed row and
S for a first fully displaced row/bound. Definitions and coordinate conventions
changed between instruments. A bright excursion, the start of a low-level run,
and a measured timing boundary are not automatically the same instant.
Several disagreements were one-row classes; some were field-coordinate bugs.
Keep the traces and keyed comparisons, rather than inheriting a universal
T=S or T=S−1 rule. Likewise, the stored “RF peak sensitivity” figures were
counts from particular excursion detectors, not a general limit on what
information the capture contains.

Dark peaks were visually apparent but the tried statistics did not separate
them from dark picture; the owner accepted them going undetected on September 11.

### What was tried — short history, not a blacklist

| Approach | What the work contributed | What limited that version / lesson |
|---|---|---|
| Best-weave / origin search | Demonstrated useful relative alignment evidence. | Early reports assigned the difference to one field's absolute origin without an independent anchor. Flat/moving material complicated interpretation. |
| Dual-edge and rolling-mode models | Exposed whole-line plateaus and gave an initial C implementation. | Brightness changed apparent edges; a 120-unit mode delayed transitions. A stable estimate was not necessarily a correctly placed picture. |
| Buffered trajectory / lookback | Explored how to bridge missing evidence and isolate publication. | Caller state and backdating created or extended plateaus. Forward-only live output and offline repair were different requirements. |
| Authority-first and relative-only variants | Separated observed positions from held output and relative evidence. | Field assignment and absolute placement still needed evidence; correcting weave alone could move the wrong field. |
| Bottom-edge model | Used a physically motivated lower landmark. | Some versions improved relative comb scores while losing caption agreement; bottom visibility and clipping mattered. |
| v9 captions + geometry + body/comb | Main contains these paths; captions supplied useful absolute gauges and comb helped relative alignment. | A caption may be absent or not CEA-608; line-22 data and dark top rows caused ambiguity. Integrating content motion drifted in one experiment; that is not a theorem against temporal evidence. |
| Geometry-first / v10 rewrite | Made line accounts, partial rows, source references and censoring explicit. | Engine, reference and contract sometimes described different quantities. Much effort went into reconciling them; the branch's existence is not evidence of a validated replacement. |
| Plain versus masked comb | Compared a simpler energy with a motion-qualified measurement. | A coherent-pan synthetic could give a confident wrong result; masks also removed usable evidence. Capture behavior and constructed counterexamples answer different questions. |
| Peak / blank-run / extent references | Made actual horizontal transitions and run positions inspectable. | Padding was once used as the blanking level; total duration missed translations; fixed windows preselected locations; absence of a hit was confused with no event. These findings concern those implementations. |
| Texture/dither comparison | Asked whether blanking could be identified independently of darkness. | Sample selection altered adjacency and populations; relocated intervals did not reproduce the proposed signature. A valid source-local texture witness remains an empirical question. |
| September 13–14 waveform walker | Examined pulse ramps, ringing, symmetry and data/picture adjacency. | Histogram/label shortcuts and fitted residual clauses accumulated. A clean short-capture score did not transfer to the whole tape. |

The waveform work grew from a two-level temporal-shape description into
13 tests with roughly 20 numbers/settings. Successive limits were often
selected from a “true” set produced by another thresholded detector. Including
the previously excluded line 286 changed that set substantially. A top scan
then reached nominal 0/0 on the short captures while sharing a wrong label
with its scorer; the whole tape exposed weaker captions, ghosting and content
false positives. The durable lesson is to retain the intended observation
and identify changes to its meaning, not to prohibit waveform recognition,
symmetry, thresholds or another entire family of methods.

### Where to find the experiments

These are navigation pointers, not required dependencies of a replacement.
Main includes `experiments/capture_render.py`, `cc608_decode.py`, the unit
reader/verifier, and the v9 registration tests. Its archaeology records the
early origin, trajectory and body/comb work.

On the v10 branch, the relevant experiments include
`box_census.py` / `box_vs_switch.py` (box versus content bounds),
`rf_peak_census.py` (excursion census; later keyed comparisons are in the reports),
`source_reference.py` (horizontal transition and level reference),
`blanking_extent.py` / `level_attribution.py` (extent observable and reference
attribution), `switch_fixtures.py` (known-answer/censoring cases), and
`dither_compare.py` (the withdrawn texture comparison). These names are under
`experiments/`; their diagnostic/withdrawal status is part of their history.
`src/field_registration/tests/` also carries the v10 switch, run-timing and
plain/static-comb reports. Retiring an implementation need not discard a useful
known-answer input, but its truth and scope need to survive with it.

The September 13–14 waveform work used the committed
`experiments/alternation_walker.py` and `alternation_census.py`, plus scratch
`wf/` instruments such as `rule3.py`, `rule4.py`, `symmetry.py`,
`score.py`, `top_scan*.py` and `tape_scan.py`. The scoring file was itself
part of the label problem. Scratch outputs are not a durable reproducibility
record; retain the useful traces/inputs deliberately if that work is retired,
rather than assuming their filenames will remain available.

### Evidence and review practice for this work

Use the source inventory and compare the same counter, field, pairing and row
convention. Keep the measured position, applied crop, retained lock and missing
measurement distinct. Identify the input and code behind a render; changing
the producer without refreshing its decision log once made a new render show
old decisions.

**Deinterlacer rule** (owner, September 4): NNEDI3 is the diagnostic lens;
it reconstructs from one field, so cannot introduce cross-field combing.
Motion-adaptive methods such as yadif/bwdif/estdif can weave misregistered
fields and add presentation artifacts; bwdif/estdif produced apparent false
field inversions on fixture A. Yadif is the intended end presentation, with
“no combing under yadif” the presentation-level acceptance test, not proof of
absolute placement. Keep raw fields/row traces available; NNEDI3 also
interpolates, and neither renderer is registration ground truth.

**Review-render producer:** amend `experiments/review_render.py` on
v10-harness rather than rebuilding it (owner, September 11). It draws the
720×486 colour output with metrics below, translucent field-coloured box/bar
overlays (purple on overlap), and box/head-switch ticks in the margins.
The inspected producer draws one output panel; it does not currently add a
side-by-side 525-line raster. Its overlays and decision log are instrument
outputs, not independent evidence that registration worked.

References and synthetic fixtures are instruments too. Their labels, calibration
selection, endpoint availability and scoring rules need checking. A conditional
synthetic establishes behavior within its stated model, not prevalence on tape.
When a test or reference changes, rerun the affected comparison rather than
carrying forward its old count.

Detailed older steps are already in `docs/registration_archaeology.md`,
`docs/registration_v9_plan.md`, `LEARNINGS.md` and the main registration
README/tests. Later v10 reports and `docs/geometry_first_engine.md` preserve
that experiment's definitions and disputes; consult them for a specific
question, not as an automatic list of instructions for a new attempt.
The branch and report pointers here preserve provenance, not a commitment
to keep the v10 implementation.

## 8. Architecture (independently agreed by two analyses)

**Production persistence decision: the tagged capture sink is debug-only.** A normal installed
capture does **not** write a raw USB/tag stream or a hidden/partial TPC alongside the user's
recording. The TPC sink remains available behind an explicit diagnostic flag for development,
hardware fault isolation, and deterministic fixture creation. The live core must still account
for every scheduled packet and propagate named loss/error state; disabling raw persistence does
not permit silent gaps. The normal downstream recorder writes the chosen standard media master
plus timing/registration decisions. TPC files used while developing that path are transient and
may be deleted after the resulting master is fully decoded, QC'd, hashed, and backed up.

**Core principle:** *Account for what crossed the USB bus before interpretation. Describe what's
known separately from the pixels. Infer registration reversibly while the raw unit is buffered.
Conceal only in disposable live output; persist raw transport only in explicit debug mode.*

**Non-negotiable properties:**
1. **Transport truth before interpretation** — account for every iso packet's endpoint, submit
   seq, status, requested/actual length, and host time before decoding. A failed packet is an
   explicit **hole**; never concatenate around it. Persist those tags and bytes only when the
   explicit debug/TPC sink is enabled.
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
8. **Debug transport storage, when enabled, is append-only and crash-recoverable** — payload
   once in chunked files; observation records reference byte spans; per-chunk checksums, a
   journal, and a manifest (sw rev, libusb ver, descriptors, USB topology, mode word, control
   transactions). This is not a normal side effect of recording through CMIO.
9. **Deterministic replay** — the parser also consumes a saved transport log offline, so packet
   loss / split markers / short fields / wraps / relocks are testable without tape.
10. **Acquisition/live isolation** — OBS, a CMIO extension, or the standard-media recorder is a
    downstream consumer, fed over **IOSurface-backed shared frames** (CoreVideo's zero-copy
    surface) / XPC; its crash or slowness must never endanger acquisition. The optional debug
    TPC sink follows the same bounded-consumer rule.

**Threads:** control/session thread (owns lifecycle, serializes transitions) · exactly **one
libusb event thread** (services events only) · per-endpoint ingest/parser queues · optional
debug transport writer · timeline/correlation worker · optional parity/cadence analyzer ·
optional live/recorder adapters.
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

The source-geometry question and capture inventory are in §7. Keep spatial
placement, temporal order and transport pairing distinct. Earlier versions of
this section proposed HMM/Viterbi order inference; that was an experimental
proposal, not an established requirement for the current problem.

**TODO — live field-parity detection (owner, 2026-09-16):** "we need to figure out some live
detection engine for field parity since our tests at the moment says it can't be guaranteed to be
either TFF or BFF". What the tests show so far: fixture A measured TFF against the usual NTSC
expectation (§6), and captures 3 and 4 (two passes of the same tape) pair their fields one field apart
(§7, measured). No method has been chosen yet.

The early header census found 6,160 complete headers identical apart from their
16-bit counter. This did not provide a per-field order/lock flag, but it also
did not rule out every hardware status source. Preserve the header and consult
the actual status-register experiments in §6 before declaring telemetry absent.
Decoded YCbCr is not raw sync-tip waveform input.

**A/V sync:** keep exact audio sample counts + cumulative ordinal; extend `tc16` only within an
epoch (record every wrap decision); match non-destructively within a bounded reorder window; fit
a robust relation between audio sample position and video, tracking both offset and slope/drift.
At 48 kHz / 29.97 fps the average is **1601.6 samples/unit** — record what the device supplied,
don't force 1601/1602. Separate **physical cadence** from **content cadence** (telecine).

**⚠️ Owner correction (2026-09-03): there is NO first-class "archival master".** This project is
an *anyone-can-use* capture path for the Shuttle, and the Shuttle itself is not archival grade.
**The frameserver is an SDK.** It publishes registration-corrected 480i frames and PCM blocks,
each with provenance and timestamps, through a C callback API; what a consumer does with them is
the consumer's business. No codec, container or file format is part of the frameserver's
contract. The sinks this project ships are the OBS source plugin and later the CMIO camera; a
recorder is just another sink, and a *reference* recorder sink writing ProRes 422 HQ 720×480i
with field-order and 8:9 aspect metadata and nothing baked in (no deinterlacing, scaling or level
remap) is a sensible default for a **master-quality** capture that survives future digital
clean-up — but anyone can build a different sink. "Lossless" is not a goal and is not meaningful
past the ADC on an analog source. The tpc sink stays debug-only. The paragraph below is retained
as the design of an *optional* lossless sink, not the product.

**Optional lossless recording mode (not the product):** a playable lossless file, produced
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

**Backlog: optional horizontal-damage concealment (owner, 2026-09-09).**
The owner proposed borrowing a damaged row from the other field, with
intra-field interpolation when the result combs. The proposed option belongs
in the frameserver before weaving; repaired rows are marked, all consumers
receive the selected output, and unchanged transport is retained only when
debug TPC capture is enabled. Whole-field comb was accepted as a conservative
substitute for a per-row test in that discussion. The prerequisite was
substantial measured real-time headroom after registration works. This remains
a separate presentation feature, not evidence of source geometry and not an
instruction to build it during the present reset. Recheck cost and the intended
output before implementing; the previous timing figures were specific runs.

## 10. Delivery: OBS virtual camera

**End state: a device every app's picker sees as a standard capture device.** Every design choice below serves that sentence — a normal camera in every
app's picker, no companion apps, no special client code, knobs in CMIO properties.

A CMIO **camera is video-only** — audio needs a separate CoreAudio device, OR deliver via a
native **OBS source plugin** (carries video+audio together; the pragmatic path for the OBS goal).
Either way, **do not put USB ownership inside the CMIO extension** (Apple's camera-extension
design assumes a signed system extension, app-group IPC, `/Applications` install, admin approval).
A sandboxed GUI/extension needs entitlement `com.apple.security.device.usb`. Long-term shape:
one USB capture service → {archival writer, OBS source (V+A), CMIO video ext + linked CoreAudio}.

**Packaging / adapter model:** the command-line probes,
TPC renderer, and replay tools are development/forensic infrastructure, not
the shipping interaction model. The normal installation is kextless: a signed
application bundle installs/manages the CMIO camera extension (and linked
CoreAudio endpoint), after which ordinary clients select the Shuttle as a
standard capture device. Keep `capture_core` + `field_registration` behind an
adapter-neutral C callback API. CMIO is the primary compatibility adapter, but
if real clients hide required controls or mishandle 480i, add a native OBS
source plugin and/or first-party capture UI against that same API. Those are
thin consumers, not alternate USB implementations: one service owns the
device, acquisition remains byte-accountable, and expensive deinterlacing or
encoding stays on bounded downstream workers rather than the USB/event path.
This is a preserved contingency, not a requirement to ship a custom capture
GUI in the first release.

**Control surface (final):** three tiers, each on the most standard
rail available. (1) **Mode selection = advertised FORMATS** in every app's native picker — the
raw/corrected split ("v-sync"/registration correction) is a device stream/property choice;
**both remain `720×480i`**. The device does not bake in bob or cadence decisions—OBS/ffmpeg/post
deinterlaces if desired. (2) **CMIO custom properties** carry the
long tail of device-global knobs. (3) **A real configurator app** — polished SwiftUI, "the
typical Mac way," Desktop-Video-Setup-class — owns logging, diagnostics, decision-log viewing,
and property editing. **This is a PUBLISHED app end-state**, so build quality, signing/
notarization, and the license (GPLv2+) are product requirements, not
afterthoughts. (Supersedes the earlier no-companion stance — the industry pattern won.)

*(superseded, kept for context)* **Control surface (earlier): EVERYTHING lives in CMIO.** All configuration —
registration correction on/off, concealment policy, logging on/off, archival-stream behaviour —
is exposed as **CMIO custom properties** on the virtual device(s); device-**global** scope is
fine (per-app scoping explicitly not needed). Whether the archival stream is corrected and
whether logs are kept are the **user's decisions through those properties**, not structural
guards — the software's job is honest defaults and honest labelling, not preventing the user
from configuring their own pipeline. No second control plane (companion-app/XPC) for settings.
(This overrides a two-surface recommendation and an "archival never property-controllable"
guard.) Client identity via `CMIOExtensionClient` may inform diagnostics; multiple published
virtual devices/streams remain available as a presentation choice, not as a settings mechanism.

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

**BUILD PLAN:**
- **P1 `capture_core`** — C library productizing capture_tagged_bench: device backend + replay backend
  (libusb_replay_shim heritage) behind one callback API; tagged transport sink; atomics/QoS/fleet
  discipline as library invariants. Tested by byte-identical replay round-trips.
- ✅ **P1 capture core landed.** `src/capture_core/` provides the device and replay
  backends, tagged sink, and adversarial/sanitizer tests. The early integration
  found a ring-publication race and unreported termination loss, with deciding
  tests. Transport details and later fixes remain in §6 and the component docs.
- **P2 registration — implemented baseline, research still open.**
  Remote `main` was verified at
  `b15b459596e0ea20c15d042835116e2b111587ea` for this rewrite.
  It contains the v9-family allocation-free C engine, CEA-608 decoder, geometric
  envelope/lock, bounded previous-unit body witness and relative comb correction.
  `src/field_registration/README.md`, headers and tests describe that revision;
  their cutoffs and precedence are implementation choices, not new requirements.
  `src/frameserver/` already contains assembly, PCM publication and logging;
  `src/obs_plugin/` already contains a working replay-capable adapter.
- **What main improved, and what its results mean.** The early C port reproduced
  the offline model on the 86,293 exact whole-tape units. Later versions recovered
  caption-anchored positions and reduced the then-defined relative comb errors.
  The round-10 report recorded 165 such errors against round 8's 1,052, with no
  unexplained disagreements against its usable parity readings. This comparison
  has an instrument-defined population, including abstentions; it is useful
  history, not a claim of universal correct placement or today's score.
  The minute-43 case motivated a bounded relative correction rather than
  accumulating body-motion shifts. Startup, clipped boundaries, absent captions,
  dark rows and source transitions remain important when judging a replacement.
- **What the v10 branches tried.** They rewrote registration around explicit
  geometry, source-local references, head-switch measurements and confirmation.
  Later work simplified comb energy, changed when it ran, and removed a
  switch-measurable prerequisite from that path. **Capture 1 did not achieve a
  valid lock; the reported first lock is withdrawn.** Comb agreement occurred
  only at 6268–6269 (rewind) and 6810–6811 (fade onset). At 6811 the best two
  energies were nearly tied, 4.704/4.711; the flag was held without rechecking
  and restored at 6882, with applied offsets (0,0). See
  `docs/registration_archaeology.md`, Part III, corrected in `a0890c3`.
  A provisional output record was also once reused after the engine changed.
  These failures concern the evidence and implementation, not a verdict on
  whether the physical approach can work.
- **Integration work must be assessed separately.** v10 also changed
  `signal_state` and `frameserver`: registration feedback could affect the
  source-layer settlement claim, a gate/fixture combination could skip engine
  work in a worker benchmark, and queue/output-isolation repairs were pursued.
  Main's worker benchmark calls registration; the later skip finding is not
  automatically a main defect. Likewise, main still has its own registration
  feedback path. Check each change against its revision before carrying it
  forward or discarding it with the engine experiment.
- **Current status.** The owner expects much of v10 may go away; no retirement
  or replacement algorithm is decided by this document. Main is the comparison
  baseline, not an oracle. Keep the four captures and whole tape in §7, the
  implementation-independent observations and reproducible regression cases.
  Short accounts of approaches and limitations are in §7; round-by-round
  patches, score tables and historical policy are in the archaeology and tests.
- **Useful existing checks (not run for this rewrite):**
  `make -C src/field_registration test`,
  `make -C src/frameserver test`, and
  `make -C src/frameserver bench`.
  They check their specified fixtures and paths; a passing suite is not a
  substitute for identifying the physical signal. Preserve transport/replay
  checks when registration changes, and report both placement and abstention
  rather than using the lock count alone.

- ✅ **P3 landed (parser, classifier, frameserver assembly).**
  `src/unit_parser/` (provenance-aware, allocation-free; split markers, device-short units kept
  out of fixed-raster consumers, holes derived from tags never content, counter wrap, audio
  resync correlation), `src/signal_state/` (property-based three-layer classifier v0 with an
  explicit unsettled-interval signal and the registration actions; ~0.61 ms/unit), and
  `src/frameserver/` (capture core → parser → classifier → engine → IOSurface publisher →
  decision log, fixed pool + SPSC handoff, low-latency live policy). **Whole-tape validation at
  2× realtime:** 86,305 observations = 86,293 exact + 7 short + 4 unframed + 1 `0x0800`, 0 holes,
  0 drops, 86,293 frames published, pool high-water 2/64; the live applied phases differ from the
  archival log in exactly the 147 rows (five plateau onsets) that forward-only publication implies.
  Earlier lookback experiments and the forward-only/live distinction are
  summarized in §7; `TRAJECTORY.md` retains the historical optional offline
  design. They are not a request to add a FIFO to the current live path.
- **P3 frameserver (original plan)** — unit parser + signal-state classifier v0 (three-layer model, §6) +
  registration engine → interlaced UYVY IOSurface publisher + decision log + standard-media
  recorder skeleton; TPC/raw packet persistence is an explicit debug option only. **No
  deinterlacer in C or on the real-time device path**; ffmpeg/OBS/post owns that presentation
  decision.
  Both components test via replay.
- ✅ **P3 audio path landed (main `da39beb`, four mutual review rounds).** `src/frameserver/
  audio_publisher.{h,c}`: every PCM record the parser emits reaches a media sink as bounded blocks
  cut at each `DeckLinkAudioResyncT` record. **Audio is the master clock:** a contiguous run is
  placed on the video timebase ONCE at its first resync (counter c → c·1001/30000 s) and every
  later frame is exactly 1/48000 s after the previous, in one rational (den 240000: a unit is 8008
  ticks, a frame 5), so block boundaries never carry the ±0.6-sample gaps that re-anchoring at
  1601/1602-frame units would create; each later resync yields a signed **correlation residual**
  (video time − audio time), reported on the block and in stats as the measured audio/video clock
  offset, never applied — on the whole tape the residual is flat (±3 ticks of quantization) except
  at the seven device events in §6, where it steps. Holes/unframed/epoch changes end the run (next block flagged, unanchored
  until the next resync — ordinal continuity cannot locate missing bytes in physical time);
  counter jumps and parser-flagged discontinuities flag `COUNTER_GAP` with the PCM untouched.
  The user's sink sits behind a **bounded preallocated queue and a dedicated audio worker** (never
  the video worker, never the delivery thread): a slow consumer causes explicit, counted, flagged
  downstream drops, never upstream HostLoss (§8 properties 7/10); `on_end` fires only after BOTH
  workers drain; stop/close are refused from any callback thread. For audio-as-master consumers a
  seqlock correlation table (resync counter → audio-clock pts) stamps every published video frame
  with its unit's audio-clock time (`fp_frame.audio_pts_known/num`). Invariants asserted after
  every run: frames published == PCM records; delivered + dropped == published. Real 45 s capture:
  2,228,913 PCM records → 2,228,913 frames in 1,393 blocks, 0 dropped, 1,385/1,385 frames stamped
  at device pace. **Open for P4a:** the adapter's policy when `audio_pts_known == 0` (bounded
  one-frame hold or a marked nominal-time fallback; zero is never a timestamp); S24LE→S32/float
  conversion belongs in the adapter; a full PCM digest test after the queue is a follow-up.
- **P4a native OBS source plugin FIRST (owner decision, 2026-09-03).** OBS is the initial
  target; the CMIO extension needs a paid Apple team even for personal use (system-extension
  entitlement; developer mode does not waive signing), and the owner wants a **ProRes capture
  end to end through OBS before paying for a certificate**. The plugin is a thin consumer of the
  same C API (async video source, 480i UYVY frames + 48 kHz audio; OBS owns deinterlacing and
  the ProRes encode). First iteration may link the frameserver in-process; the API boundary stays
  the service's callback API so the CMIO extension later consumes the same thing. Spike report:
  `src/obs_plugin/PLUGIN_SPIKE.md`. Decisions taken from it: **build route A** for the dev loop (plain
  Makefile against OBS.app's own `libobs.framework` + matching headers; no CMake, ad-hoc signature,
  no Apple account — OBS 32.2.2 has no sandbox and disables library validation), obs-plugintemplate
  only when publishing; **audio-as-master timestamps** — video frame timestamps derive from the
  audio sample ordinal at the unit's resync anchor (the audio publisher exposes `anchor_counter_ext`
  and `sample_ordinal`) — **superseded the same day by the resync-interval census (§6): the audio
  clock has no rate offset, so video timestamps come from the unit counter, audio from the sample
  count, and the adapter applies the correlation residual only where it steps (three events on the
  whole tape)**; libusb statically linked
  (`libusb-1.0.a`); one session per process, a second source instance is refused
  (`OBS_SOURCE_DO_NOT_DUPLICATE`); Color Format P216 / Rec.601 / limited for the ProRes record, and
  a synthetic Y=1 / Y=250 clamp test before any OBS file is trusted. **The OBS ProRes is a
  presentation copy** (progressive RGB composite, square pixels, no field metadata); a 1:1-pixel
  720×480 file with 8:9 aspect metadata is a recorder sink's job (§9).
  **✅ First live OBS test (2026-09-03, `src/obs_plugin/`, replay of fixture A inside OBS 32.2.2):**
  the plugin loads, the source publishes, and the frameserver accounting inside OBS was 0 drops,
  0 holes on every session. Two problems, both fixed and measured: (1) constant audio dropouts —
  the replay's fixed sleep per transfer added the parser's work to each period (a "realtime"
  replay ran **28% slow**, 59.65 s for 46.58 s of device time) and starved libobs's mixer;
  deadline-based pacing brought it to 46.96 s and the dropouts stopped; (2) libobs keeps audio
  timing independent of video only when the source is **decoupled AND unbuffered** (read from
  `obs-source.c`), so the plugin sets both — the shared device clock is the sync. Known and
  accepted: OBS shows 720×480 square-pixel (stretched) until the scene item's transform is set to
  640×480 — 640×480 (not 720×540) because it leaves the 480 scan lines untouched and VHS
  horizontal resolution (~240 TVL) is oversampled at 720 anyway; the source defaults to Yadif 2x
  TFF; OBS owns deinterlacing (Yadif is the intended end presentation once registration works;
  deinterlacer rule, §7).
  **Recording-aligned sidecar (2026-09-04):** the frameserver gained runtime decision-log
  attach/detach (`fs_log_start`/`fs_log_stop`: exclusive open, checked writes with
  `log_write_errors`/`log_close_errors`, `fs_log_stop` reports a file with any failed row as
  incomplete; a stall-hook test proves a hung sidecar write sheds video downstream with exact
  range accounting, never acquisition). The plugin subscribes to OBS's recording-started/stopped
  events and writes `<recording>.registration.csv` per recording: grown in a per-uid 0700 scratch
  directory, published by `renamex_np(RENAME_EXCL)` on the same filesystem or by a staged,
  fsynced, byte-verified copy plus exclusive rename on another (`publish_copy.c`, fault-injected
  tests for every post-create step; "published" = the destination filesystem acknowledged the
  bytes, cache-visible on a write-back cloud volume), never truncating or replacing an existing
  sidecar, never published if incomplete; on a mid-recording source restart the log is closed by
  `fs_stop` after the workers drain, so no delivered unit is ever unlogged. Publication runs on
  a persistent per-source thread with a job queue (OBS frontend event callbacks execute on the UI
  thread — `OBSStudioAPI::on_event` is a synchronous loop called from `OBSBasic` — so a callback
  only enqueues), drained at destroy, never inline. The recording's file name comes from
  `obs_frontend_get_last_recording()` (set at recording start); `obs_frontend_get_current_record_output_path()`
  is the configured directory, not the file — the first live test produced nameless sidecars.
  Scope decision: one sidecar per press of the record button, named after the recording's first
  file (OBS's automatic file split emits no frontend event; per-split rotation via the output's
  `file_changed` signal is a follow-up); standard and advanced file recorders supported, an FFmpeg
  output to a URL gets none, auto-remux keeps the pre-remux name. The publisher is a bounded,
  tested queue (`publish_queue.{c,h}`) with final-name reservation. Alignment is within
  one unit (the counter of the last frame delivered before the event is logged; exact alignment
  needs an in-band frame counter). OPEN: a `.tpc` tee from inside the plugin (needs a
  runtime-attachable tagged sink in the capture core); a log writer thread if storage stalls are
  ever observed; the plugin's live-device path has never been exercised inside OBS.
- **P4b CMIO extension (Swift)** — after P4a and the Apple team exist: standard device, two
  advertised formats (raw 480i, corrected 480i), sink-stream consumer, custom properties.
  Deinterlacing belongs to OBS/ffmpeg/post.
  Includes a signing/notarization/dev-mode
  investigation SPIKE first (published-app requirement; no boot-security changes). Spike report:
  `src/cmio/PACKAGING_SPIKE.md` — first hard blocker is a paid Apple Developer Program team
  (pay + identity check, no software review; only DriverKit entitlements need Apple approval and
  the design avoids them). Real-device test target after synthetic validation: the commercial SP
  tape behind `captures/composite_program_30s.tpc`, captured over S-Video.
- **P5 configurator app (SwiftUI)** — status, logging, decision-log viewer, property editor.
- **P6 (far future) every device mode** — PAL 576i, component, composite, HDMI, 720p, 1080i/p,
  10-bit v210. A public driver cannot stay S-Video/NTSC-only. Measured state: all NTSC geometry
  (unit bytes, line bytes, 525 lines, field starts 17/280, padding-ruler lines, 240-line field)
  sits behind named constants in `unit_parser`, `field_registration`, `signal_state` and
  `frame_publisher`; the parser already keys on the `0xe8xx` family and the classifier is
  property-based. The change is one seam: a runtime format descriptor selected by format code.
  Exact Shuttle PAL framing is a HYPOTHESIS (bmusb: `0xe109` family, 720×576, second field at
  335) until a real PAL `.tpc` exists — a 30 s `shuttle-capture` from any PAL user is the fixture,
  which is the tpc sink's real job. Full-raster lossless captures found online (vhs-decode outputs
  carry the 625-line raster with VBI) can drive the descriptor plumbing synthetically but cannot
  prove device framing. HD bus bandwidth (~1.3 Gbit/s at 1080i v210) is unmeasured on this host.
- **Next hardware session — owed experiments (all ≤30 s tagged captures via `shuttle-capture`,
  no long plays; poll status register `214/16` at 1 Hz throughout each):**
  1. ~~**True no-signal path**~~ — **DONE 2026-09-03** (two captures, see the no-input paragraph in
     §6): deck absent/off and deck output dropped by its HDMI mode both yield `0x0800`. Expect the never-observed `0x0800` format code and whatever pseudo-frames /
     cadence the device emits (bmusb: green, ~30.13 Hz) — the only device state no capture has
     ever triggered, and the one that cannot be synthesized because its content is unknown.
  2. ~~**Unlocked input** via the deck's tuner on a dead channel~~ — **DONE 2026-09-03, negative
     result (`captures/deck_ext_input_nosource_30s.tpc`):** with the deck on an unconnected
     external input and then on a dead tuner channel, its output is **locked `0xe801` sub-blanking
     black (Y ≈ 2 ± 5, chroma 128, padding ruler intact), no OSD**. This deck regenerates sync in
     every mode; it cannot produce unlocked video. Genuinely unlocked baseband needs a TBC-less
     deck or camcorder (still owed; the Shuttle's unlocked-input behaviour remains unexercised).
  3. ~~**Virgin-tape mute row**~~ — **DONE 2026-09-03**, row corrected (raw no-RF black, not grey).
     Original plan: start a few
     seconds before a recording ends and run ~30 s into a virgin section, so the acquisition
     transient (snow) and the settled deck mute are in one file. Verifies "snow is only the
     acquisition transient".
  4. ~~**Composite fixture (P6)**~~ — **DONE 2026-09-03 (`captures/composite_program_30s.tpc`,
     700 MB, byte-complete):** mode word `0x3d000000` selects the composite decoder; framing is
     identical to S-Video (`0xe801`, 756,048-byte units, padding ruler at the same 18 lines),
     real colour program decoded. Taken over an audio-grade RCA lead (not 75 Ω), so it proves the
     path and the framing, **not** chroma quality — the S-Video-vs-composite chroma A/B still needs
     a proper 75 Ω cable and the same passage on both inputs.
  5. **V-stabilize comparison:** the later work identified this as the deck's
     line-TBC switch and recorded both settings. The source inventory, pairing
     caveat and on/off observations are in §7. Earlier independent “TBC on /
     V-stabilize off” prescriptions should not be read as two available controls.
     The already-recorded off-setting pass is a useful comparison; a new hardware
     session is not required just because an old plan offered one.
  No over-the-air analog exists in Japan since 2011/2012 (cable digi-ana ended 2015), and dead-air
  tapes through this deck yield TBC-locked snow identical to the relock windows already captured.
- Throughout: **all testing via deterministic replay** (whole_tape.tpc + untagged_capture + libusb_replay_shim +
  census ground truths); hardware only for final validation passes.
   **Steps 5–6 are built by replaying a captured file through a virtual device — no deck, no tape,
   no live signal** (see §6). Only steps 1–4 need the hardware; everything downstream is
   deterministic replay, so the archival writer and the CMIO/OBS path can be developed and
   regression-tested against recorded damage (program cut, deck-blank/relock, short units) at will.

**Analog input choice:** default **S-Video** (VHS/S-VHS is natively Y/C → most direct, least
transformed tap). **A/B vs component** early: component moves chroma demodulation off the
Shuttle and onto the deck, and this best-in-class deck may decode better — the *only* axis on
which component can win (both are 480i; field/interlace handling is identical). Compare on a
saturated, motion-heavy passage (chroma noise, color bleed, edge cleanliness).

## 11b. Real-time budget and CPU minimum (owner requirement, 2026-09-03)

Registration will keep getting more capable; it must stay real-time, and the project publishes a
CPU minimum rather than assuming M-class silicon. Rules:

- **Budget.** One unit period is 33.37 ms. The per-unit cost of the whole frameserver worker path
  (classifier + registration + assembly + publish, excluding I/O) must stay **≤ 10 ms on the
  reference M3 P-core, single-threaded** — ~30% of the period — so a core three times slower still
  keeps up. Anything beyond that needs a measured justification and a design that sheds work
  before it sheds frames (§8 property 7).
- **Measured today (M3):** registration 1.47 ms median / 1.57 ms p95 per unit; classifier
  ~0.65 ms; publish/copy well under 1 ms; whole worker ≈ 2.5 ms/unit. Any new evidence path (e.g.
  a static-region comb search) is costed against this table before it lands.
- **Enforcement.** Every engine or classifier change reports ms/unit (median, p95) from the golden
  runs in its commit; a `bench` target over a fixed 10,000-unit fixture is the regression gate.
  Allocation-free and SIMD-friendly code (NEON now, SSE/AVX2 when ported) is the norm on this path.
- **Published minimum (provisional, from measurement + a 3× scalar-throughput margin):** any Apple
  M-series; on x86, a 2017-or-later quad-core with AVX2 at ≥ 3 GHz for the full pipeline at 480i.
  A 2015-class dual-core i3 is explicitly NOT supported. Revised when an Intel build exists and is
  measured; never restated from extrapolation once real numbers exist.
- HD modes (P6) multiply the raster by 4–6×; their budget is a separate measurement, not this one.

## 12. Fallback if analog needs host-side decoder config

If exp 1 streams but stays `0x0800` on analog select, host-side analog init is missing. **Don't
disassemble** — **USB-sniff** the old Windows **Blackmagic Desktop Video** driver (USBPcap/
Wireshark) capturing analog, and replay the control transfers. Caveat: a Win11-**ARM** VM on the
M3 can't load BMD's x64 **kernel** driver → this generally needs **real x86 Windows** hardware.

## 13. Prior art & references

- **bmusb** (protocol ref, GPLv2+): `https://sources.debian.org/src/bmusb/0.7.8-2/` — Nageru.
- **vhs-decode / ld-decode**: useful prior work on per-field metadata and software
  TBC, but the raw RF/CVBS input differs from the already-decoded raster here.
  Treat it as related research, not an existing solution to our registration
  task. `https://github.com/oyvindln/vhs-decode/wiki/JSON-metadata-format`
- **GStreamer** interlace vocabulary (`DISCONT/RESYNC/CORRUPTED/GAP`, one-field-per-buffer).
- **V4L2/videobuf2 + em28xx**: `SEQ_TB/SEQ_BT/ALTERNATE`, damaged buffers as errors,
  `NO_SIGNAL/NO_H_LOCK/LOCKED`. (Old drivers trust the hw field marker — less provenance than we need.)
- **DeckLink SDK** input model: stream-time / hw-ref arrival / validity flags
  (`bmdFrameHasNoInputSource`) / format-change (`bmdVideoInputFieldDominanceChanged`) / timecode.
- **FFmpeg / presentation tools:** `idet`, `fieldmatch`, bob and other
  deinterlacers were useful comparisons but answer different questions about
  order, cadence or presentation. Some review renders introduced apparent field
  inversions; compare raw fields before attributing that artifact to the capture.
  NNEDI3 was used for review presentation, not as registration ground truth.
  `fieldmatch` is content-cadence tooling; it must not “repair” physical field
  records. FFmpeg's `decklink_dec.cpp` is the multi-PTS-source reference for A/V.
- **OBS decklink**: live-adapter reference only.

## 14. Working notes — retain lessons, not every round

- **Mutual code-and-intent review is the coding style of this project (owner rule, 2026-09-03).**
  Every change by one agent (Claude or Codex) is reviewed by the other before it is considered
  done, and the review covers **intent as well as code**: the reviewer must be able to state the
  decision-making behind any part it does not understand, and must ask rather than assume. Review
  the change **in the context of the whole system, never the changeset alone** — a diff-only
  review dangerously misses side effects on other modules, invariants, and the design decisions
  recorded in this file. Iterate until both agents converge. A mismatch is resolved by a
  **deterministic test** that decides it; if it is genuinely an interpretation question, end the
  turn and bring it to the owner instead of picking a side. Token cost is accepted.
  **Both agents implement, both review** (owner, same day): review is not one agent judging
  and the other coding. Each agent fixes the findings it owns as commits with deciding tests,
  and the other reviews that *implementation* — the code, not only the decision — before merge.
  If one agent is mid-review of the other's branch, let that review finish before pushing more
  commits under it; then swap roles on the next round.

- **Keep evidence separate from policy.** Before another registration change,
  state what the owner asked to observe and how the proposed measurement bears
  on it. A fitted rule may be an experiment; it is not an owner ruling. When a
  counterexample appears, check the interpretation and instrument before
  absorbing it into another clause.
- **Source context belongs with the result.** The capture inventory in §7 is
  retained because input, recording, deck setting, exposure and pairing changed
  what was observable. These are useful distinctions, not permanent conditions
  for recognizing an entire class of tape.
- **Truth and tests also need scrutiny.** Keep the scorer's labels and selection
  identifiable. An old label cache, mismatched field coordinates or a default
  argument change altered results in the waveform work. Known-answer synthetic
  cases helped find instrument defects; they do not establish source prevalence.
  A crash, missing input, expected assertion failure and pass are distinct.
- **Waveform scores must distinguish device inserts from source-carried data.**
  A pooled score can mostly measure the easier Shuttle waveforms: the first v11
  two-band temporal-walk sample recognized inserts while missing the source
  examples. This limits that baseline, not waveform recognition as a method.
  Keep visual labels separate from detector decisions and report each population.
- **Scope negative conclusions.** “This instrument did not establish it on these
  rows” preserves a finding without claiming no method can do so. The same
  applies to positive results: state the measured population, not “solved.”
  Record what changed and its remaining uncertainty; avoid carrying a withdrawn
  interpretation forward inside a confident summary.
- **Experiment commitments (owner, 2026-09-19).** Before a test meant to decide
  something, the agent appends an entry to its own ledger (`docs/experiments_claude.md`,
  `docs/experiments_codex.md`) and commits it: the question in the owner's words; the
  premise, the claim about the signal that must be true, stated apart from the method;
  the simplest method; the falsifier; the material it is judged on. Amendments are
  appended, never edited in, and state before they are built their physical reason,
  what they should improve and what they must not break. "Multiple amendments are
  allowed but amendments should create progress in a forward direction. If adding new
  parts is not pushing closer to the solution, or if amendments introduce regressions,
  that's when I should be stopped and queried." A falsifier appearing is the result:
  report the premise refuted; a different premise is a new entry. Every report answers
  its entry: verdict on the premise (held / refuted / unknown), what the data did, the
  population with abstentions, each amendment and whether it moved forward, what is not
  understood, the raw rows it rests on. Raw-row labels are preferred; another
  instrument's output is named and never treated as truth. A positive claim is checked
  on material not used to build it where such material exists. The other agent reviews
  reports against entries; the owner is queried on a stalled or regressing amendment or
  an unresolved disagreement. The ledger holds commitments and verdicts only; results
  stay in scratch. It moves out of the repo in one commit if the owner prefers.
- **Search the owner's words before escalating** (standing instruction,
  2026-09-11). A question goes to the owner when those words do not answer it,
  or the agents cannot converge on their application. Relayed quotations and
  the relaying agent's gloss are different evidence. Do not ask the owner to
  select a physical fact that the measurements have not established.
- **Artifacts and review:** inspect the actual producing code, input and output,
  including commit-message claims. A new render with an old decision log is
  still an old measurement. A review of a proposed repair is not a review of
  the resulting diff. Keep detailed reports at their own paths rather than
  expanding this section after every exchange.
- **Capture startup honesty:** allocate delivery storage synchronously in `cc_start`,
  before launching workers, so failed startup cannot report success or emit `on_end`.
  Capture-core/frameserver callback refusal uses thread-local session ownership,
  never joined worker IDs (which the OS may reuse).
  Deadline mechanisms: `src/test_supervisor.h` and `src/tool_deadline.h`.
  Concurrent tests establish overlap/pressure and control windows by event handshakes;
  deadlines only fail missing events, never supply evidence that a window occurred.
  Inner pipeline-test deadlines measure lack of progress; the external supervisor
  separately bounds total runtime. Release admission gates after the last required boundary.
  Asserted CPU-cost gates use the measured thread's CPU time, not wall time;
  host scheduling delays belong to liveness measurements, not CPU-cost regressions.
- **v11 engine integration:** `docs/geometry_engine.md` describes the explicit
  frameserver selection, unit-keyed decisions and reversed-pair boundary handling.
  Keep a requested crop distinct from unavailable raster rows: silently clamping
  the whole crop makes the applied-decision log disagree with the published pixels.
  Owner-directed cleanup removed the near-blank and overrun vetoes, interpreted
  top substitution and their early-comb path; they are not dormant controls.
  Entry 33 replaces the d5c9f08 top search with a first single-line Pearson-rise
  measurement (strict >0.45), followed by an independent symmetric +/-5 discard
  per field. The C raw scan matched all 172,586 whole-tape edges before removal
  of the old guards. Controls are GE_WAVE_BAR and GE_WAVE_CLAMP; old GE_TOP_*
  commands are refused. Schema 21 distinguishes unit-owned raw top/step/status
  from frame-owned accepted census and publication sources. An absent/discarded
  top is not a guessed measurement; existing placement fallback is labelled.
  Bottom edges, profiles and blanking are unchanged on all 86,293 units.
  History retains discarded experiments; census identity is not render approval.
  Aperture arithmetic uses published offsets: 480i starts at 23+d1 / 286+d2
  for 240 lines; the 486-line review starts three lines earlier with the same
  endpoints. Measured field-1 first is not generally 23+d1 because comb changes
  d1. A census restriction is not a final-crop guarantee. Equal comb winners
  estimate relative alignment, not absolute common-mode motion. A late-top gate
  that abstains on early tops cannot validate an earlier-biased rule's quality.
  Optional audit logging never changes decisions or triggered-comb scheduling.
  Report published-unit counts separately from woven-frame counts. Reversed
  pairing flushes its final unit with f2_unused=1 and no frame_top_unit; its
  field 1 already belongs to the preceding frame. A missing boundary frame key
  is not an interior frame loss. Validate frame sequence and both source-unit
  placements by encoded-strip readback, not by equating MP4 frames to units.
  Review runs must retire the previous renders.status before publication and
  write a validated replacement naming the actual engine/renderer producer
  commits. scripts/geometry_review_status.py provides --begin and completion
  checks, including artifact hashes and explicit boundary-unit accounting.
  Entry-34 rejection preflight stopped before promotion: its C state path changed
  exactly the requested 26 frames, but independent whole-aperture roughness rose
  on three. Two remain worse in the interior-only check; the original scorer's
  aperture is unresolved. See the Codex ledger and /private/tmp/comb-reject.HLom5S.
  The owner's two-sided-floor amendment then passed: 21 supported target
  placements improve full-aperture roughness, five unsupported proposals hold
  the previous published pair, and no extra/decided-frame placement changes.
  Entry-34 rejection is separate from selection: default GE_COMB_REJECT=2,
  an enclosed contiguous <=1.5*minimum floor, both outside rises >=1.5.
  Schema 22 records proposal ratio, refusal/discard, floor and rises without
  changing census or audit-only decisions. Discard means geometry only, not
  image loss/repetition. Some improvements propagate without a fresh refusal.
  Evidence: /private/tmp/comb-basin.KlFmop; docs/geometry_engine.md defines the
  log and zero-energy/out-of-range conventions. Renderer approval remains the
  owner's decision after the four numeric-gated review captures.
  Later hold instructions stopped that render run before publication. The
  superseded one-field prototype changed 31 frames against an exactly-five
  gate. Its four-edge/known-motion replacement performs 32 direct interventions
  and changes 56 frames against the reported 20 onsets. It delays cap1's (5,5)
  placement from 6667 to 6670 (nothing/nothing); it does not eliminate it.
  Neither prototype is promoted. The owner withdrew both hold rules after the
  four-edge falsifier and authorized basin-only 3a87891 review renders for
  captures 1–4. Keep the prototypes and findings in scratch/history; do not
  change the waveform instrument in that work.
  The remaining cap1 6667 placement is knowingly unchanged, not fixed by the
  basin rule. Review publication still requires encoded-strip validation and
  a fresh renders.status identifying the actual producing commits.
  That basin-only review publication completed: all four MP4/sidecar pairs
  passed full encoded-strip readback and source-unit placement joins, with
  zero differences. geometry_renders/renders.status is READY with engine and
  renderer 3a87891; visual acceptance is pending. Prior files are recoverable
  under /private/tmp/comb-basin.KlFmop/replaced-reviews. That run rendered only
  the four captures. The later whole-tape authorization has its own scale gate:
  rejection strictly below 5% and discards below 2% of paired frame rows.
  Its zero-drop paced replay passed (329/86,289 rejections, 14 discards).
  Whole-tape encoding/validation is separate from census identity and from
  owner visual acceptance; evidence is /private/tmp/basin-fulltape.f19Ygq.
  That full-tape review is now published as captures/fulltape_render.mp4 and
  its registration sidecar: 86,296 encoded frames, zero strip/source-placement
  differences, hashes verified across same-filesystem publication. The status
  in captures/ names engine/renderer 3a87891 and leaves visual acceptance pending.
  Entry-36 preflight has not promoted the vote: its reference joins reversed
  field-1 level fills to the wrong unit and treats DISCARDED as ABSTAIN. Its
  persistent vote window also needs reconciliation with the engine's reset
  contract. See the Codex ledger and /private/tmp/vote-entry36.aBbP7d/REPORT.md;
  engine, renderer and review artifacts remain unchanged pending that review.
- `AGENTS.md` is a symlink to `CLAUDE.md`; edit `CLAUDE.md` only.
  Follow the active turn's shared-checkout/lock instructions, preserve others'
  edits and stage explicit owned paths. Commit owned work with the required
  co-author trailer; review and push under the agreed workflow.
- **Keep results out of git (owner, 2026-09-16).** Experiment results, per-round reports,
  image panels and data tables stay in scratch outside the repository; a durable finding
  goes into an existing document in a few lines. `scripts/git-hooks/artifact_guard.py`, run
  by the pre-commit and pre-push hooks (`git config core.hooksPath scripts/git-hooks`),
  refuses them. An exception is the owner's decision and goes into `.artifact-allowlist` in a
  commit of its own. Never bypass the hooks with `--no-verify`.
- Preserve the project's privacy convention: capture identifiers and engineering
  observations, not programme titles, on-screen identities or private tape details.
- Superseded early assumptions: "not a driver / no RE"; bulk (not isochronous)
  transfers; the 1080p-throughput concern (SD analog is ~166–242 Mbit/s — trivial
  for SuperSpeed).

Historical details remain in `LEARNINGS.md`,
`docs/registration_archaeology.md`, component docs/tests and the reports
for the relevant branch. Read them when the question calls for them; they are
not a mandatory accumulated algorithm or an instruction to repeat every
experiment. Source facts needed to navigate the current work are retained in
§7. Nothing in this rewrite removes the underlying history.
