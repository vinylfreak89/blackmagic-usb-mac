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
  Target corpus: irreplaceable one-shot consumer VHS — minimize plays; one tagged capture per
  tape once the pipeline is proven, so nothing ever needs a re-run.

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
GAPS = 0). Deck-health substitute test condition 1 (zero scheduled USB holes) is **met**; the
remaining conditions (fixed geometry, no field-1 plateaus, line-phase stability, no repeats,
audio continuity) await the content passes. Analyses stream the file by
seek-walking records; a raw endpoint split is never materialized.

**Whole-tape render/content pass:** two bounded passes over the tagged capture (compact stereo
PCM only; no endpoint/video split) produced a review MP4 plus a registration decision log. Both passes
reproduced the 46,075,614-record CAP1 census exactly; a complete decode of the result returned
zero errors. Output: 720×480, SAR 8:9/DAR 4:3, 60000/1001, 172,600 frames, stereo 48 kHz,
2879.543333 s, 4,420,351,820 B. **USB byte-complete does not mean decoder-unit-exact:** the video
endpoint contains 86,293 exact 756,048-byte marker intervals, seven short device-emitted units,
zero absent counters, and zero counter errors. The shorts are counters 4507=371,568 B,
4508=13,008 B, 4509=371,568 B, 4510=371,568 B, 4515=755,824 B, 4520=755,824 B, and
4701=755,824 B. They retain their observed prefix and use conspicuous fill only for the undefined
suffix; CAP1 proves they are not host loss. Arbitrary endpoint edges add a 1,652,048-byte leading
fragment and 495,376-byte trailing fragment outside the marker-delimited census.

Audio is continuous, but audio resync *metadata* is not perfectly dense: one
`DeckLinkAudioResyncT` record is absent at 894→896 (sample index 99,177,246). CAP1 audio sequence
is still complete and no PCM is discarded. The renderer therefore unwraps counter values and
looks anchors up by value rather than treating audio-row ordinal as frame time. The selected A/V
window had 138,212,854 samples for a counter-timed expectation of 138,218,080 (5,226-sample /
108.9 ms deficit over 48 min); the review copy applies `atempo=0.999962190185`. Raw extraction
does not conceal or resample this.

⚠️ **Do not call every registration-render decision a measured deck plateau.** The generalized
one-pass estimator selected `(d1,d2)` counts `(0,0)=63,476`, `(1,0)=19,265`, `(2,0)=2,315`,
`(3,0)=1,244`, with 2,165 maximal nonzero constant runs; 1,282 of those runs are only 1–3 units.
The raw decision log is an auditable correction trace, not by itself deck-health ground truth.
Using an explicitly diagnostic summary rule (bridge zero gaps shorter than 10 s), selections form
nine high-level clusters: 15.215–975.641 s (chronic +1/+2), 990.089–999.532, 1017.516–1018.251,
1046.312–1047.446, 1127.760–1128.427, 1459.458–1461.293, 1880.011–1882.814 (+2),
2669.600–2704.569 (+1), and 2837.201–2879.543 (+2/+3). An independent field-origin census or
visual/raw-field check must decide which are physical registration events versus estimator chatter,
especially fades, flat fields, mute/snow, and the 720 one-unit selections. Thus the earlier
deck-health condition “no field-1 plateaus” is not met by renderer selections, but deck health is
not falsified by those selections alone.

**Full-tape render + census:** review MP4 720×480 SAR 8:9 (4:3), TFF bob 59.94p, CRF 12, stereo AAC; full `-xerror` decode clean;
video and audio both exactly 2879.543 s. Unit census over **86,300 counter periods: 86,293 exact
756,048-B units, 0 absent counters, 0 counter discontinuities — and SEVEN device-short units**
(ctr 4507–4510, 4515, 4520, 4701; surviving prefixes rendered, bars only on undefined suffixes).
With transport provably gapless, those shorts are **device-framed: the Shuttle itself occasionally
emits a short unit.** That closes §6's old open question (a) — capture_60s's short tc-5839 unit was
device behaviour, not host loss — and vindicates the strict-extractor policy. Audio: PCM
continuous; one absent resync record (894→896, zero samples lost); cumulative device-vs-nominal
clock offset **5,226 samples / 48 min ≈ 36 ppm** (atempo 0.999962 in the watch copy only).
Registration: the corrector chose nonzero field-1 offsets in 2,165 runs, but **1,282 lasted 1–3
units — estimator chatter, explicitly NOT deck-health evidence**; after bridging, nine candidate
regions remain (largest 15.2–975.6 s and 2837 s–end), pending raw-field/visual confirmation.
Deck-health conditions 2–6 therefore stay OPEN pending that inspection.

**NTSC-M setup: no preserved pedestal in this capture.** Fade-bottom/black frames in fixture A measure **median Y ≈ 12–17** with
sub-black excursions — with p95 ≈ 22–24 these frames **cannot represent ordinary 7.5 IRE setup
(expected Y ≈ 16 + 219×0.075 ≈ 32)**. That is the supportable claim; the measurement does NOT
establish where setup vanished, nor that "US black became Y12" (8 frames is thin; dark program
content can legitimately contain superblack/crushed fades). **THREE unapportioned stages, not
two:** the 1998 broadcast→cable→VCR chain, the DHX2's playback processing, and **the Shuttle's
own analog decoder** — a Y16 result from any test downstream of tape cannot separate the last
two. The commercial-tape capture is a worthwhile *real-world* test (pro duplication makes setup
plausible, not guaranteed), but the **decisive test is a calibrated NTSC generator into the
Shuttle directly, with and without setup** — that isolates the Shuttle; then the deck with a
known signal. Method upgrades for the next pass: gate on low spatial variance + neutral chroma +
unimodal luma histogram (not just p95); report the histogram mode (median biases on detail);
measure setup as **black-minus-same-line-porch** (that difference IS setup); require the black
peak to settle across contiguous frames. **Renderer implications (adopted):** the Y16/C128
hard-padding ruler stays valid (device-generated, says nothing about program black); classifiers
and registration landmarks must treat program black as **relative/adaptive, never assume Y16**;
any future presentation-side setup removal is an affine remap from measured black/white — and the
archival stream is never touched.

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

**Damage-review rerender:** the obsolete whole-interval prefix placement is replaced
by a 24,576-byte transfer-grid reconstruction. Marker endpoints plus **1,890 uniquely placeable
complete hard-padding blocks** constrain the grid; ordered transfers in the remaining spans use a
same-position temporal content cost. All **5,225,562,336** captured video bytes in the rendered
counter range are represented exactly once; **781,239,024** absent bytes are conspicuous synthetic
color bars. Of 7,945 units, 6,160 are exact, 1,781 partial, and 4 wholly absent. Two damaged
intervals have no complete padding anchor; three false/inconsistent padding-like runs are rejected.
The three startup fragments and truncated final interval are not individually 24,576-quantized and
use a separately named padding-bracketed fallback. **Do not overclaim this reconstruction:** a
synthetic-drop test falsified temporal matching as byte-position-authoritative on fades/uniform
gray. Only marker/padding anchors are hard evidence; every other slot choice is labelled diagnostic
in the decision CSV. Tagged capture_tagged_bench data must use packet provenance instead of this rescue path.

**Design decisions:**
- **Correction-decision log:** the real-time corrector MAY rely on band modes without a stable
  video anchor **provided** every per-unit decision `{d1, d2 or Unknown, mode, confidence}` is
  logged in real time to an optional sidecar — corrections are real-time in the driver; the log
  is the post-fixup escape hatch, not lookahead.
- **Review-encode damage policy:** never blank or repeat. Render corruption **as-is** (surviving
  bytes at their positions); genuinely absent bytes get an unmistakable standard-NTSC-style
  no-signal fill, documented, with the placement assumption stated for untagged captures. Purpose:
  drop *patterns* must stay visible and inspectable.

**Writer output rule:** no encoder or capture writer may create or grow its working file
inside a cloud-synced (File Provider) root, even under a hidden or `.partial` name — a dataless
placeholder or an in-flight sync corrupts a growing file. Growing TPC, MP4, PCM, and decision-log files live in a non-synced scratch
directory. After the writer closes and validation succeeds, publish with one same-filesystem
atomic rename; never fall back to copy+delete. Scratch and destination filesystem identity is
checked before work begins. An unfinished capture remains in scratch for diagnosis/recovery.
The destination above describes final publication only, not the writer's working directory.

**Archival re-registration does NOT require a full-raster master (owner decision, 2026-09-03).**
The normal recorder records the corrected 480i as an ordinary downstream consumer; a 525-line
FFV1 master in the service was proposed and rejected as an extreme-edge-case tax. A whole-line
re-registration of a 480i recording lacks the 1–3 raster lines outside the crop; those lines sit
in the head-switching / line-21 region, so the accepted archival repair is an edge-duplicated or
estimated whole-line shift, recorded in the sidecar as a substitution. Where lossless repair is
actually wanted, a `.tpc` of that segment (explicit debug sink; requires replaying the segment)
is patched into the recording. Expected consumer need for either path is ~0.1%. The one live-path
requirement this imposes: the sidecar carries per-unit applied `(d1,d2)`, the observation that
produced it, and the interval label, so an offline pass can locate and re-shift affected units.

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

**Deck mute policy (measured; the virgin-tape row is visually observed, not USB-verified):**
| Deck state | S-Video output |
|---|---|
| Non-playback transport mode (stop, rewind, FF) | grey mute + OSD |
| Playing, servo locked | program |
| Playing, unlocked — **transient** (relock windows) | snow, ~0.7–2.3 s, re-timed into valid `0xe801` units |
| Playing **virgin tape** (no CTL, no RF), steady state | **NOT grey mute — MEASURED 2026-09-03 (`captures/virgin_transition.tpc`, 45 s, byte-complete):** the deck outputs **sub-blanking black (Y ≈ 1.5–2, chroma 128) with sparse white dropout streaks and a noise band at the bottom of the raster**, all in locked `0xe801` units; the OSD (if enabled) is composited over it. The earlier "grey mute" came from a **deck setting** (a mute/back-screen mode the owner has since switched off); with it off the deck passes its raw no-RF output. So the grey rows in this table describe that setting, not the deck's only behaviour — one more reason states are defined by signal properties, never by deck (design rule below). Deck-specific tell for the inference layer: with OSD display set to off, this deck still composites its OSD when playback is fully unlocked (no control track) — an OSD appearing over a sub-blanking raster is strong no-RF evidence on this family, usable by the deck-mute score, never as a state definition. The end-of-recording transient was short (~0.5 s: flat → sub-black → 2 snow-like units → black), not the 1.7–2.3 s snow relock seen after splices — a virgin section has no CTL to chase. |

So snow is only the *acquisition transient*; the deck's steady-state answer to unlocked playback is
its mute screen. ("The rest of the tape is snow" describes the tape's magnetic content — what this
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
Shuttle's real `0x0800` path, still unexercised, will finally fire); mute screens vary per deck
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

**Classifier v0 on the virgin-tape capture — three real-data defects (queued):** (1) sub-blanking
black with sparse dropout streaks flapped between `SubBlackMuteLike` and `ProgramLike` every ~2
units for 7 s — gradient energy from the streaks passes the program test; a raster whose luma sits
below blanking must veto `ProgramLike` outright. (2) The deck's OSD over black-with-noise classified
as `ProgramLike`/`Present` for 26 s (the OSD text supplies edges): the planned deck-mute score with
OSD-region awareness is needed, and `Present` must not be inferred from overlay content alone.
(3) `unsettled` stayed 1 for every unit of two clean 45 s captures (1,385/1,385 and 1,387/1,387):
the unsettled interval never closes on the live path. Transport/parser were flawless on both
captures (GAPS 0, HostLoss 0, errors 0).

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
The visible "flip"/registration jump is a **spatial vertical registration error measured in whole
raster lines** — **not** temporal order, **not** pairing phase, **not** cadence.

> **⚠️ CORRECTED (full-capture census, 6,160 intact units).**
> The first version of this section said *"field 2's start line drifts across 274–285."* **That is
> false.** Measured against three independent anchors:
> - **The transport raster is rigid.** `f1_origin=17` (99.35%), `f2_origin=280` (99.25%), spacing
>   **263** (99.27%), and **100% of consecutive frame pairs are unchanged** on both fields.
> - **What actually moves is FIELD 1's PICTURE, translating down 1–2 whole lines** — field 2's
>   picture translated **0 lines in 4,042 of 4,042** rigidly-measurable units. The whole frame
>   never shifts together. So the varying quantity is the **inter-field spacing**, and field 1 is
>   the field that slides.
> - **It is episodic, not chronic:** confirmed translations occur only in counters 24533–25025
>   (~16 s), as bursts of multi-frame plateaus (median 4 frames, max 44) that return to nominal
>   in between.
> - **The "274–285 wander" was estimator noise.** Comb/weave scoring **can only ever constrain
>   f2−f1**, never an absolute origin (shifting both fields together leaves the weave intact).
>   42% of its off-263 picks had a median relative margin of **0.027** vs **0.587** for confident
>   picks. **Never report a best-weave candidate as an observed physical VSYNC location.**
>
> **Anchors that broke the tie** (use these, not comb, for geometry): the device inserts a
> **hard-padding ruler** — `Y==16 & C==128`, zero variance — at lines **0–6, 261–269, 523–524**
> (byte-identical in 6,159/6,160 units); decoded analog blanking sits at Y≈1.4; and each field
> carries a **2-line VBI signature**, with **field 2's a line-for-line replica of field 1's,
> offset exactly 263**.
>
> Two traps that produce wrong numbers: dark picture content moving only a field's *top* edge
> (check the bottom edge too — it stayed put), and a **flat bright field** (counters 23335–24380)
> flooding the normally-blank lines past any threshold while spacing stays 263.

Consequences, all large:

- **The fix is pure spatial line selection**, and its **direction matters**. Correct by holding
  **field 2 fixed at 280** and moving **field 1's crop**: nominal `17/280`, field-1 displaced +1 →
  `18/280`, +2 → `19/280`. ⚠️ Holding field 1 at 17 and pulling field 2 to `279`/`278` yields a
  mathematically identical *weave* but is **backwards** — it makes the stable field chase the
  displaced one, so absolute program placement jumps. (An earlier `17/278` example here was wrong.)
  Describe the phenomenon as **field-1 program-layer displacement within a fixed raster, with
  bottom clipping** — not an unconstrained whole-picture translation. Because nothing is reordered,
  the correction **cannot disturb cadence or A/V sync** — a whole class of feared damage does not
  apply. Naming should follow the physics: measure *inter-field registration*, not "field 2 origin";
  keep the observed transport starts `17/280` immutable; record the chosen correction **separately
  from the observation**.
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

#### Where the fault lives — the OSD is the witness

The deck's **OSD stays coherent at nominal raster coordinates while the program picture is
displaced**, and correcting the whole field repairs the program picture but **tears the OSD**.
Two layers with *different* registration is decisive: had the Shuttle misdetected output VSYNC it
would have shifted program **and** OSD together, and could not have produced the split. So the
fault sits in the **deck's program-video path, upstream of its OSD compositor** — the deck emits a
**stable regenerated raster** and places the program layer at the wrong line inside it. Consistent
with the census (rigid transport raster, moving picture content).

This also explains the CRT question: a CRT locks to the **stable regenerated sync — which never
moves** — and simply draws displaced content, hidden by overscan and spot size. It only rolls or
jumps if actual output VSYNC moves, and here it doesn't. *(Corrections to earlier reasoning:
classical CRT **vertical** sweep is a **triggered relaxation oscillator** — the flywheel/AFC lives
on **horizontal**, so "vertical flywheel averaging" was wrong. And **flagging is not the analog
form of this error**: flagging is horizontal line-time error, a separate failure mode that may
merely share an upstream trigger.)*

**Still unresolved — tape vs deck.** Not settled by this capture: the census cannot separate "the
deck delivered field 1 one line late" from "the Shuttle sliced field 1 one line differently", and
the OSD evidence rules the Shuttle out as *primary* without identifying whether the trigger is
recorded tape timing, control-track/servo trouble, deck misadjustment, or simply this deck
family's policy for a legal-but-ugly signal. **Cheapest decisive test:** play the same passage on
a **known-good older analog S-VHS deck** through the same Shuttle and settings — same displacement
at the same tape location ⇒ tape/recorded-timing origin; clean registration ⇒ the D-VHS deck's
servo/digital processing. (Gold standard would be a two-channel scope on S-Video Y plus the deck's
head-switch/PG test point, but the second-deck A/B is cheaper and answers the practical question.)

**General registration model (replaces the field-2-origin model in the proof renderer):** per unit,
estimate a **signed integer program-layer offset per field, or `Unknown`** —
`{transport field starts (observed) · d1 · d2 · relative = d2−d1}` — searching candidate **pairs**
`(d1, d2)` over configurable bounds, corrected crops `17+d1`/`280+d2` for this format, **no field
permanently designated the anchor**. Hard padding + VBI give the transport ruler but cannot see
program-layer displacement; comb constrains only `d2−d1` (common-mode-blind); **absolute** offsets
need same-parity temporal registration, active-picture landmarks, or a learned stable segment —
and when those are insufficient (flat fields, snow, cuts) the estimator publishes `Unknown` or
relative-only rather than arbitrarily anchoring a field. The segment model *learns* which field
(if either) is stable, normal placement, plausible offset range, and transition/hysteresis costs.
This capture resolves as `d1∈{0,+1,+2}, d2=0` — **test data, not policy**. Labels, stricter form:
observation layer stores `UniformField` + measured `{Y,U,V, variance, chroma_distance,
temporal_coherence}`; `LikelyMute` and friends live **only** in the inference layer; `0x0800` is
stored as a device observation, not a universal no-signal description.

**Second-deck A/B deferred**; the narrower question is only *"is the deck itself going bad?"*. **Substitute test:** capture a
**known-good tape with the fixed deeper-queue probe** — ideally **both SP and EP material, once
cold and once warmed** — and validate: zero scheduled USB holes · fixed hard-padding/VBI geometry ·
no field-1 registration plateaus · stable horizontal line phase · no unexplained repeats or missing
fields · continuous audio delivery. This doubles as the hardware verification of the queue fix.

**Deck-health read (evidence favours a healthy deck, with caveats):** ~99.3% of the capture is
geometrically rigid, the confirmed registration fault is localized and plateau-like, the output
raster and OSD compositor stay rigid throughout, and two D-VHS decks have shown the same broad
behaviour → a **tape-triggered edge case or deck-family policy**, not this unit dying. ⚠️ Do not
over-claim: "a degrading deck would show *pervasive continuous* instability" is **too strong** — a
marginal deck can misbehave only when warm, only in EP, or only on badly damaged control-track
sections. And a rigid *output* raster proves the deck's **regenerated raster** is stable; it does
**not** directly prove the mechanical servo is healthy. A clean known-good-tape run is strong
evidence of health, but cannot prove this deck handles every damaged tape as well as another design
would.

**Deck policy for archival (revised — the earlier "TBC off" advice was backwards):** software
corrects **discrete vertical registration only**; it does **not** fix within-line time-base error,
top flagging, chroma phase, or H-sync damage. TBC-off would keep the registration problem *and*
add flagging. Default: **TBC on, `Vスタビライズ` off** — test V-stabilize *separately*, since JVC's
own manual says it corrects vertical picture shaking and should be returned to off afterwards,
which implies a second vertical-concealment path that may help presentation while destroying
chronology. Move off TBC-on only when an A/B proves it preserves materially better information,
judged on **unique-field fingerprints, repeats, H-line phase, vertical origin and signal loss —
not appearance**. And "don't replace the deck" was too categorical: a different deck can have
better tracking, tape path, sync separator or a less destructive TBC policy, so a second known-good
S-VHS deck is worth having as an **archival tool, not a spare** — different decks win on different
pathological tapes.

**Architecture consequence (supersedes "archival writer + preview" framing in §8–§10):** the final
shape is a **normal live frameserver**, not an archival writer with a preview bolted on:
`USB capture → frame parser → field-origin correction → 59.94p frame surfaces + 48 kHz audio →
CMIO/OBS`. **Recording becomes an optional downstream consumer, exactly like OBS** — it must not
control acquisition or correction. Per transport unit: archive the untouched 525-line unit
only when explicit debug transport capture is enabled; otherwise retain it in bounded pipeline
storage, detect origins on a separate thread, select the corrected windows, publish 480i or
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

**Don't treat the 16-bit timecode as a field counter** (it's once per transport unit, not per
field). **Segment** on signal-loss/relock, USB/parser gap, format-code change, counter
discontinuity, or strong pairing-phase-change evidence. Within a segment, weigh evidence in
order: (1) **device/header** — ❌ **DEAD END, measured:** across all 6,160 complete
units the 48-byte header is **byte-identical except the 16-bit counter** (`00 00 ff ff | cc cc |
01 e8` + 40 zero bytes). **No lock flag, no field-marker bit, no status.** Stop hunting *in the
header*. ⚠️ But an empty header does **not** prove content analysis is the only possible telemetry:
the **status register `214/index 16` has never been polled across states** and must be sampled
over program / snow / deck-grey / a real cable-pull before hardware telemetry is written off.
Preserve the header anyway (cheap, and it proves the
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
- **P2 registration engine in C** — the (d1,d2) per-field model ported from
  capture_render.py, same anchors (padding ruler, VBI, temporal registration), hysteresis,
  `Unknown`. Golden-tested against `field_origin_census.tsv` and the
  whole_tape decision log; must match the offline estimator's confident decisions and stay within
  the 16.68 ms/field budget in C.
- ✅ **P1 + initial P2 landed (P2 estimator superseded below).** `src/capture_core/` (capture core as a library: device +
  replay backends behind one callback API, tpc sink, adversarial suite green under plain/TSAN/
  ASan+UBSan; two real bugs caught pre-consumer — a ring publication race, and unconfessed loss
  at termination when the ring is full). `src/field_registration/`: allocation-free dual-edge
  estimator — full-tape golden **86,293/86,293 units and 56,441/56,441 confident decisions**
  matching the offline model, untagged_capture census 4,042/4,042 applied offsets correct, all 320 (+1)
  and 66 (+2) events corrected, **1.29 ms median per unit (~25.8× realtime)**, 185 KB state.
  **Integration contract:** the signal-state layer MUST call `fieldreg_begin_segment()` after
  acquisition/relock (registration cannot distinguish a long real displacement from a new source
  segment); plain byte discontinuities use `fieldreg_discontinuity()` and keep the learned
  gauge. Note: on the end credits the production dual-edge model stabilizes at (-1,0) where the
  old sidecar chattered +2/+3 — promising, pending visual confirmation. CMIO startup guidance
  from P2: suppress samples during Arming; start the device timeline at the first stable A/V
  epoch; no synthetic startup frames.
- **P2 trajectory correction (supersedes the 120-unit rolling-mode policy above):**
  the rolling majority was proven to manufacture delayed plateaus. Production now uses a
  caller-owned bounded FIFO (30-unit confirmation, 36-unit hard horizon). Strong per-unit
  absolute geometry and the stable fallback trajectory are separate: a coherent top+bottom
  `(d1,d2)` candidate may correct a buffered unit even if it lasts only one frame, but an
  opposite same-parity **differential** motion measurement vetoes it. The differential cancels
  coherent picture/credit motion and prevents a source-carried edge or overlay phase from moving
  the whole field against the dominant picture asset. Hysteresis changes only the fallback for
  abstaining units. Cuts/global-luma steps make the current unit abstain because the measured
  envelope is source-carried. Between observations, presentation
  holds the last accepted per-unit phase instead of snapping to an older baseline; the sidecar
  names this `HeldLastObservation`. A settled fallback is backdated only onto buffered
  abstentions. At the horizon, the caller flushes the already-held buffered trajectory,
  labels abstentions `HeldUnresolvedHorizon`, logs `trajectory_reset`, and starts fresh—never
  rewrite the buffer to raw around isolated observations, and never drop/repeat a unit.
  Reset invalidates the learned lock but preserves the last actually presented phase (which may
  differ from the locked baseline); following abstentions cannot create an unobserved snap while
  the engine reacquires.
  Neither field is a permanent anchor; `(0,1) -> (1,0)` is legal. Integration is off the USB hot
  path via preallocated lock-free SPSC pointer handoffs; `field_registration` itself allocates nothing.
  **Six-minute production-path proof:** 10,800 units through C registration +
  bounded FIFO + `estdif` produced 54 finalized offset transitions (only five 1–3-unit runs),
  zero known-observation/applied mismatches, and zero backdates over known observations. A caught
  caller bug had rewritten buffered abstentions to raw at every hard-horizon reset, manufacturing
  144 transitions/70 short runs; preserving the already-held trajectory reduced it to the numbers
  above. untagged_capture golden: 3,784/4,042 overall census agreement, **3,499/3,499 confident**, with all
  258 disagreements conservative under-corrections and no opposite correction; median 2.58 ms/unit
  on M3 (~7.7% of one core). The lower overall agreement than the old edge-only result is deliberate:
  differential dominant-picture motion may veto a rigid envelope edge on a multi-phase raster.
  Targeted late-tape checks also close the specific delayed-plateau regression: a 7,300-unit
  tail/credits window finalized three transitions and zero 1--3-unit runs; a 4,500-unit window
  around a known one-unit registration event at 36:40 stayed `(0,0)` for 4,499 units and applied one directly observed
  one-unit `(1,0)`, rather than holding a new phase to tape end. Both checks had zero
  known-observation/application mismatches and zero backdating over observed units. This does
  not claim one global field offset can reconcile the tape's spatially incompatible layers.
  **Algorithm v4 horizon fix:** a full v3 sidecar audit found that 936/948 applied
  transitions began on a matching current-unit observation and six were deliberate backdated
  locks, but two `RawAwaitingLock` transitions snapped to `(0,0)` after reset with no observation.
  Reset now invalidates confidence while preserving the last actually presented phase, not just
  the last locked baseline. A synthetic divergent-baseline/presentation reset test proves the
  contract; local untagged_capture remains 3,784/4,042 overall and 3,499/3,499 confident. The full v4 golden processed all
  86,293 exact units at 2.532 ms median (13.2x realtime), matched 50,042/50,042 confident v3
  evidence decisions, and observed 464 hard resets with **zero reset-induced phase changes**.
  The five transitions without a same-unit observation were all explicit 30--32-unit convergence
  commits with backdates, never reset snaps. The pass accounted for all 46,075,614 CAP1 records
  and 23,036,416 video DATA records with zero sequence/packet gaps and zero status errors.
  The renderer refuses dataless (File Provider placeholder) inputs rather than triggering a
  multi-gigabyte cloud fetch.
- ✅ **P2 authority-first v6 (supersedes the live FIFO/backtracking policy above).**
  Reconciled raw-field evidence showed that the dominant whole-tape failure was evidence
  authority, not missing lookahead: a local two-of-three band majority overruled an agreeing
  coherent full-width envelope and relative phase. The production live engine is now
  **forward-only with zero presentation FIFO**. A coherent full-width envelope plus relative
  consensus is authoritative; coherent top+bottom motion in at least two broad bands plus
  same-parity temporal corroboration follows physical per-unit jitter immediately. A stable raw
  edge anchor prevents delta integration from walking the crop, and delta authority is bounded
  to one line around an independently established absolute gauge. Other fixes split structural
  transport validity from content availability, treat a search-floor top edge as censored and
  permit a corroborated bottom-only absolute candidate, compare common-mode *displacement*
  against `(absolute-prior)`, and prevent a lone positive observation from latching through later
  abstentions. The optional endpoint-constrained retroactive pass remains recording-side only and
  is gated on real-tape evidence that a coherent positive observation was wrong.

  Public two-truth golden: physical raster **1,017/1,017** (v4: 858/1,017), trajectory oracle
  **1,130/1,140** (v4: 962/1,140); its ten differences intentionally ask archival hindsight to
  override the live raster. All physical field/common-mode/multiphase unit-rate FOLLOW classes,
  false/secondary-edge HOLD classes, upward `-2` classes, blank-with-padding, and the 124-unit
  stale-latch class pass. Full-tape strict coherent-envelope disagreement fell from
  **10,547/55,329 to 1,021/55,329**; one-field coherent transitions followed rose from 850/4,128
  to 2,939/4,128. At 35:00--40:00, follow/hold changed from 0/1,066 to 594/438. Full-pass M3 C
  timing was 1.466 ms median / 1.569 ms p95 per unit; state is 188,320 bytes, allocation-free.
  Human sign-off remains required: these are observable-consistency metrics, not proof that every
  content-derived edge is physical truth. Integer vertical registration does not correct
  sub-line, horizontal/line-time, flagging, or skew errors.
  **Owner visual sign-off (2026-09-03, full forward-only NNEDI watch copy of fixture A):** a
  large improvement over the validated v4 engine; judged representative of what a digitally
  captured VHS tape should look like. Of the jumps that remain, nearly every one in the SP
  recording brings *new* lines into the picture (unique luma and chroma, not a shifted copy of
  lines already present) — dispositive that they are recorded-signal instability, not raster
  position, and therefore outside any integer registration engine. The EP recording additionally
  shows line-21 content bleeding into the active picture, forbidden on a compliant broadcast —
  consistent with a generational copy at the source and/or EP-mode playback; also not a raster
  fault. Conclusion: not every jump is fixed, and the ones that remain are not registration.
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
  **Lookback investigation (two independent arms, reconciled and superseded for live use):** the
  old caller backdated only abstaining rows and could not revise positive provisional evidence;
  the lone frame-8169 `(0,1)` then latched for 104 units. V6 fixes the latch forward and follows
  coherent physical evidence immediately. `TRAJECTORY.md` retains the optional archival-side
  endpoint-constrained design, but no caller FIFO/backtracking belongs in the CMIO live path.
- **P3 frameserver (original plan)** — unit parser + signal-state classifier v0 (three-layer model, §6) +
  registration engine → interlaced UYVY IOSurface publisher + decision log + standard-media
  recorder skeleton; TPC/raw packet persistence is an explicit debug option only. **No
  deinterlacer in C or on the real-time device path**; ffmpeg/OBS/post owns that presentation
  decision.
  Both components test via replay.
- **P4 CMIO extension (Swift)** — standard device, two advertised formats (raw 480i, corrected
  480i), IOSurface/XPC consumer, custom properties. Deinterlacing belongs to OBS/ffmpeg/post.
  Includes a signing/notarization/dev-mode
  investigation SPIKE first (published-app requirement; no boot-security changes).
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
  4. **Composite fixture (P6):** ~30 s of program via composite (mode word `0x3d000000`) — the
     first composite `.tpc`, and the chroma-decoding A/B against S-Video on the same passage.
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
- `AGENTS.md` is a symlink to `CLAUDE.md`; edit `CLAUDE.md` only.
- Superseded early assumptions: "not a driver / no RE"; bulk (not isochronous) transfers; the
  1080p-throughput concern (SD analog is ~166–242 Mbit/s — trivial for SuperSpeed).
