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
timeline from the shared counter, repeats the prior good image for damaged or
missing counter slots, bobs with FFmpeg's field-aware `bwdif`, and trims audio
at matching `DeckLinkAudioResyncT` counters:

```sh
python3 experiments/capture_render.py capture.bin \
  --render review.mp4 \
  --render-marker-start 88 \
  --render-marker-end 762
```

Repeats are preview concealment only and are listed on stdout. The verified
default for this capture is stored chronological field 1 mapped to the top
field. It constructs ordinary 720x480 TFF UYVY from full 240-line fields
(source lines 17..256 and 280..519), then
`bwdif=mode=send_field:parity=tff` performs the half-line-aware 59.94p bob.
The credit roll is the disambiguator: the opposite mapping produces a strong
alternating vertical displacement, despite the usual expectation that NTSC SD
will be BFF. Use `--first-field bottom` only when motion in another capture
supports it. This avoids the vertical breathing produced by independently
scaling two 237-line field crops.
