# Bench experiments (no video source required)

Build (needs `brew install libusb`):
```
clang -O2 -Wall -o usb_descriptor_probe usb_descriptor_probe.c $(pkg-config --cflags --libs libusb-1.0)
clang -O2 -Wall -o iso_stream_smoke  iso_stream_smoke.c  $(pkg-config --cflags --libs libusb-1.0)
```

## usb_descriptor_probe — descriptor / endpoint map
Opens the Shuttle (VID 0x1EDB / PID 0xBD3B) from userspace, reads config-by-index.
**Verified result (M3 / macOS 26.6.1):** open + claim work with no root.
```
Config 1, bus-powered 224mA, Interface 0:
  alt0 idle
  alt1 (output): EP 0x01 OUT ISO (49152 B/interval) + bulk 0x05 OUT / 0x86 IN
  alt2 (input):  EP 0x83 IN ISO video (49152 B/interval, burst 11)
                 EP 0x84 IN ISO audio (2048 B/interval)
                 + bulk 0x05 OUT / 0x86 IN  (register/control channel)
```

## iso_stream_smoke — no-signal isochronous streaming
Runs the full capture init (alt1→alt2 reset, mode word `0x3f000000` = S-video+analog+8-bit,
latch `0x73c60001`) and streams iso on 0x83/0x84 for ~4s with **nothing connected**.
**Verified result: the Darwin iso path works.**
```
status(214/16) = 00 00 0c e0
video: 3851 transfers, 87.0 MB in ~4s, 0 iso errors, 0 xfer errors, ~174 Mbit/s
frame framing: marker 00 00 ff ff, then LE 16-bit frame counter (0x0001,0x0002,...)
               + format code 0x0800 (= NO SIGNAL, correct — nothing connected)
```

### Caveat: floating-input false-lock
With an analog input SELECTED but nothing connected, the decoder intermittently
false-locks on noise and emits an occasional bogus frame (seen: `0xe809`, `0xe801`
— PAL-family, and the value VARIES run to run). This is NOT capture. `iso_stream_smoke`'s
verdict therefore requires the signal format to be the **DOMINANT** format
(majority of frames), not just present — a couple of stray `0xe8xx` frames ≠ signal.
Never accept a frame boundary/format on the 4-byte magic alone.

### Signal go/no-go:
1. Connect deck **S-Video out → Shuttle S-Video in**;
   power the deck and **play a tape** (any NTSC source with motion).
2. `./iso_stream_smoke svideo`   (or just `./iso_stream_smoke`)
3. PASS = dominant format is an NTSC code (`0xe1xx`), verdict `SIGNAL LOCKED`.
   Then eyeball that pixels are changing (real image, not a stuck frame).
   Expected NTSC 8-bit code ≈ `0xe901`/`0xe101`-family.

## capture_render — repair an untagged capture_untagged_ring capture

`capture_untagged_ring.c` accidentally placed completed video (0x83) and audio (0x84)
transfers in one byte stream without endpoint tags. `capture_render.py`
recovers the two endpoint streams globally. It does not use a per-frame
zero-density maximum: audio callbacks can straddle video markers, so that
approach moves callback edges and causes horizontal wobble or green/magenta
UYVY bands.

The verified audio record phase is eight S24LE channels per 24-byte record:
channels 0/1 occupy bytes 0..5, and muted channels 2..7 occupy bytes 6..23.
`DeckLinkAudioResyncT` is a complete 24-byte record in the same phase. The
splitter tests all 24 phases, grows maximal record runs, and checks them against
the 11,520/11,616-byte callback grammar. Adjacent audio callbacks may merge;
their internal boundary is unknowable and unnecessary for endpoint recovery.

### `untagged_capture` transport caveat and capture_untagged_ring scheduling change

The recovered video remains intact through most of the run, then loses complete
24,576-byte payload quanta after counter 25026. Every deficit from there to the
last marker is divisible by 24,576. That is capture_untagged_ring's normal eight-iso-packet
video-transfer payload, not a 1,440-byte raster-line or 756,048-byte frame
quantum. Ring overflow was zero and video completion inversions were zero.

Static analysis found that the old `V_NPK=8`, `XFERS=6` arrangement queued only
about 6 ms of video time on Darwin. The libusb Darwin backend schedules iso
requests at explicit future USB frame numbers; once resubmission falls behind
the queued horizon, it resumes at the current frame plus a safety offset. No
request exists for the intervening time, so neither transfer status nor packet
status can report that hole. The old probe also silently skipped completed
zero-length packets.

capture_untagged_ring now queues 128 packets per transfer and eight video transfers, compacts
each transfer with one ring operation, and prints complete packet-length
histograms including zero lengths. This is an evidence-gathering fix, not yet a
hardware-verified archival container: the flat file still cannot describe the
location of a failed or unscheduled iso interval. Production capture must tag
endpoint, submission sequence, scheduled packet slot, status, requested/actual
length, host time, and payload.

Example archival extraction:

```sh
python3 experiments/capture_render.py capture.bin \
  --video-endpoint video-endpoint.bin \
  --audio-endpoint audio-8ch-with-resync.bin \
  --stereo-pcm audio-stereo.s24le \
  --video-480i complete-frames-720x480.uyvy \
  --audio-spans audio-spans.tsv \
  --sync-map audio-sync.csv \
  --video-map video-map.csv
```

The raw endpoint outputs preserve discontinuities. `--video-480i` contains
only complete 756,048-byte units and must not be muxed as one gapless CFR movie
across dropped/fragmented units. The CSV maps retain counters, endpoint offsets,
and audio sample positions for a timestamp-aware archival writer.

For a review MP4, select two e801 marker indices. This path restores a CFR
timeline from the shared counter, exposes damage with conspicuous legal-range
color bars, bobs with FFmpeg's field-aware `bwdif`, and trims audio at matching
`DeckLinkAudioResyncT` counters:

```sh
python3 experiments/capture_render.py capture.bin \
  --render review.mp4 \
  --render-marker-start 88 \
  --render-marker-end 762 \
  --render-crf 10
```

Invalid counter ranges are listed on stdout. The renderer never repeats or
blanks a damaged unit. For transfer-quantized capture_untagged_ring damage, it places surviving
bytes on the 24,576-byte grid: marker endpoints and uniquely mapped complete
hard-padding blocks are hard constraints; remaining ordered transfers use a
same-position temporal content score. Missing raster regions get synthetic
color bars. This is diagnostic recovery, not provenance: the CSV names
`PaddingAnchoredTemporalTransferGrid`, `AnchorlessTemporalTransferGrid`, and the
non-quantized fallback separately. Temporal matching is not authoritative on
fades or uniform fields, and tagged captures should place loss from packet
metadata instead. Raw endpoint and map outputs are unchanged.

The verified default for this capture is stored chronological field 1 mapped
to the top field. It constructs ordinary 720x480 TFF UYVY from full 240-line fields
(source field 1 lines 17..256 and a measured field 2 origin), then
`bwdif=mode=send_field:parity=tff` performs the half-line-aware 59.94p bob.
The credit roll is the disambiguator: the opposite mapping produces a strong
alternating vertical displacement, despite the usual expectation that NTSC SD
will be BFF. Use `--first-field bottom` only when motion in another capture
supports it. This avoids the vertical breathing produced by independently
scaling two 237-line field crops.

The fixture A also moves a field's **program-layer spatial registration**
inside an otherwise rigid 525-line transport raster. This is not a TFF/BFF
change and the fix never reorders fields. `--adaptive-registration` estimates
relative displacement from weave curvature and independent `(d1,d2)` from
learned per-field picture-band landmarks. It applies a change only when those
measurements converge, uses hysteresis, and reports `Unknown` rather than
inventing a common-mode anchor. Either field may move; neither is hardcoded as
the permanent reference. Record every decision and its evidence for review:

```sh
python3 experiments/capture_render.py capture.bin \
  --render corrected.mp4 \
  --render-marker-start 0 \
  --render-marker-end <last-marker> \
  --render-crf 12 \
  --adaptive-registration \
  --decision-log corrected-registration.csv
```

This remains a proof renderer, not the final live estimator. A production
frameserver should retain the same transport/VBI, same-parity temporal,
motion-masked weave, and hysteresis evidence and publish every selected offset
and confidence. Missing/short units break estimator continuity; the review
holds the last applied crop while rendering their surviving bytes and fill.

The renderer keeps the source at 720x480 by default and signals NTSC 4:3 with
SAR 8:9; it does not upscale. `--render-size` is opt-in for non-archival review
copies, and `--render-sar 1:1` is appropriate only after resizing to square
pixels.

If the first/last shared counters expose a small accumulated audio deficit, the
review renderer reports it and applies a bounded `atempo` correction to meet
the counter-timed video endpoint. Extracted PCM and archival maps are never
resampled or concealed.

Input remains memory-mapped. Full renders stream decoded units to a temporary
raw-video file while retaining one reference raster and one marker interval in
RAM; the frame index stores byte ranges, not multi-gigabyte image buffers.

## Tagged capture_tagged_bench (`.tpc`) render

The same tool accepts capture_tagged_bench's tagged capture container directly. It seek-walks
the 24-byte `CAP1` records, validates per-endpoint submission sequence, packet
index/status, `HostLoss`, and `TransferError`, and concatenates DATA payloads only in
memory-sized parser buffers. It never writes a raw video or endpoint split.
The first pass writes only compact two-channel S24LE PCM and indexes
`DeckLinkAudioResyncT`; the second pass streams one reconstructed 720x480 unit
at a time into FFmpeg. A missing resync metadata record is logged but does not
discard continuous PCM; timing anchors are found on an unwrapped 16-bit counter
rather than by assuming one resync row per video period.

```sh
python3 experiments/capture_render.py capture.tpc \
  --render review.mp4 \
  --scratch-dir <same-filesystem-tmp> \
  --render-crf 12 --render-preset veryfast \
  --adaptive-registration \
  --registration-library src/field_registration/libfieldreg.dylib \
  --registration-evidence dual \
  --deinterlacer none \
  --tagged-start-unit auto \
  --decision-log review_registration.csv
```

All growing encode, PCM, and sidecar files are staged outside File Provider
roots and moved into place only after close and validation. `--scratch-dir`
must be on the same filesystem as the destination; cross-device copy fallback
is deliberately refused. The default is a non-synced system temporary folder.

`--registration-library` selects the allocation-free production C estimator while
preserving the same decision-log contract. Production `dual` decisions require
coherent top and bottom geometry; scene cuts hold state without training the
landmark model, and a stale nonzero correction is released only after two
independent nominal-geometry/temporal votes. `top` remains a diagnostic port of
the original Python estimator. Picture-edge landmarks are decision evidence,
not crop coordinates: the renderer preserves VBI rows 17–18/280–281 and remaps
only the fixed 19–256/282–518 source envelope. It never shifts the complete
240-line crop. `--deinterlacer none` emits interlaced TFF video and leaves
deinterlacing downstream. For a 59.94p review copy, `--deinterlacer nnedi`
performs intra-field interpolation and therefore cannot blend across a scene
cut or across chronological fields. FFmpeg requires the external
`nnedi3_weights.bin`; pass it explicitly with `--nnedi-weights`. The expected
file is 13,574,928 bytes (upstream SHA-256
`27f382430435bb7613deb1c52f3c79c300c9869812cfe29079432a9c82251d42`).
The renderer does not bundle or silently download that model. `bwdif` remains
available for comparison, but its temporal/local decisions can be unstable on
noisy mixed-cadence tape. Deinterlacing is presentation-only and is not part of
the registration library or eventual CMIO capture path.

`--tagged-start-unit auto` counter-aligns presentation and audio to the first of
three consecutive exact transport/VBI-valid units. The three units are bounded
lookahead, not a capture-specific timestamp or counter. It does not remove
material from the source capture. `--tagged-limit-units N` is available for
bounded regression renders.

The MP4 and sidecar are first written to sibling partial files. FFmpeg must
decode the complete partial MP4 without an error before either destination is
atomically replaced.

The CAP1 transport may be byte-complete while the device's decoded-video
framing is not. Exactness is therefore measured independently from validated
`e801` header spacing and counter continuity. A short marker-delimited unit is
named `ShortDeviceUnit`, keeps its captured prefix at its observed byte
position, and receives diagnostic bars only for the undefined suffix; a
missing counter period is named `AbsentDeviceUnit`. Those states break
registration-estimator temporal continuity and remain explicit in the CSV.

## Live frameserver review render

Review copies used to judge the production registration path must come from
the frameserver itself, not from `capture_render.py`: the signal classifier's
segment/discontinuity actions are part of the live engine history. The live
recipe streams both raw outputs through FIFOs into separate bounded video and
audio encodes, then stream-copies them together; it never materializes the
roughly 65 GB UYVY endpoint:

```sh
experiments/render_live.sh capture.tpc /non-synced/review-output
```

The result is a 720x480, SAR 8:9, 60000/1001 NNEDI bob with AAC, its schema-5
frameserver sidecar, and a 720x580 overlay copy whose extra band leaves the
picture unobscured. `render_live_gate.py` requires every exact unit to have
been published, exactly two encoded frames per exact unit, and decodes a
checksum-protected machine strip at ten deterministic random units to compare
the burned ordinal, extended counter, and applied pair with the sidecar.
