# Blackmagic Intensity Shuttle (USB 3.0) — userspace analog capture on macOS

A kext-free capture path for the Intensity Shuttle USB 3.0 on Apple-silicon macOS, built for
lossless, honest archival of interlaced standard-definition analog video (S-Video/composite/
component) with audio. Blackmagic never shipped macOS software for this device; the USB protocol
was reimplemented in userspace over libusb from published protocol facts (see `NOTICE`) and
re-verified on hardware.

The project is developed by two AI coding agents under a human owner, and the repository is the
record of that work: the design doc, the experiments, the wrong turns and their post-mortems are
all in the history on purpose. Read `LEARNINGS.md` first if you want the method; read `CLAUDE.md`
(the living design doc — `AGENTS.md` is a symlink to it) for the design and the measured facts.

## What exists

| component | what it is |
|---|---|
| `src/capture_core/` | The capture core as a C library: one callback API over two backends — the live device (libusb isochronous streaming) and replay of a recorded `.tpc` stream — plus a `.tpc` sink. `shuttle-capture` is the CLI. |
| `src/field_registration/` | Allocation-free C engine that measures and corrects per-field vertical program-layer displacement inside the device's fixed 525-line raster. |
| `experiments/` | The bench programs in the order they were needed: USB descriptor probe, isochronous stream smoke test, the naive capture that lost packets, the untagged ring-buffer capture, the tagged capture bench, the libusb replay shim (deterministic replay + fault injection), the packet-capture verifier/reader, and the renderer that turns captures into review video. |
| `CLAUDE.md` | Design doc: protocol, architecture, measured device behaviour, signal-state model, field-registration physics, delivery plan. |
| `LEARNINGS.md` | Diagnostic post-mortems — method, not chronology. |

## The `.tpc` container

Tagged USB Packet Capture: a sequence of 24-byte records (`CAP1` magic) — one per isochronous
packet, plus explicit host-loss, transfer-error, session and heartbeat records — followed by the
packet payload. Every scheduled USB slot is accounted for, so a missing packet is provable from the
tag stream rather than inferred from content. `experiments/verify_packet_capture.py` checks a file;
`experiments/packet_capture_reader.py` streams one.

`TransferError` packet index `0xffff` denotes a submit failure. Index `0xfffe` with status
`UINT32_MAX` is the terminal **control-truth-lost** marker: the metadata reserve was exhausted,
the file is permanently not clean, and capture continues by default. See
[`src/capture_core/README.md`](src/capture_core/README.md) for the complete record policy.

## Build and test (no hardware needed)

Requirements: Apple clang, `libusb` 1.0 (Homebrew), Python 3, `ffmpeg` for rendering.

```bash
make -C src/capture_core test          # generates a synthetic .tpc fixture, runs the suite
make -C src/capture_core test-tsan     # same under ThreadSanitizer
make -C src/capture_core test-asan     # same under ASan + UBSan
make -C src/field_registration test    # unit tests + the synthetic-truth golden (tests/TRUTH.md)
```

`make -C src/capture_core check CAPTURE=<file.tpc>` replays a real capture through the library and
verifies the accounting against the file's own totals.

## Reproducing the experiments

Everything downstream of acquisition runs from a recorded `.tpc` file; only acquisition itself
needs the Shuttle. With a Shuttle and any NTSC S-Video source:

```bash
clang -O2 -o experiments/usb_descriptor_probe experiments/usb_descriptor_probe.c $(pkg-config --cflags --libs libusb-1.0)
./experiments/usb_descriptor_probe                       # endpoint map, no source needed
make -C src/capture_core shuttle-capture
./src/capture_core/shuttle-capture svideo 30 capture.tpc # 30 s tagged capture
python3 experiments/verify_packet_capture.py capture.tpc # zero gaps, zero loss expected
python3 experiments/capture_render.py capture.tpc --render out.mp4
```

The history is the experiment log: each commit says what was tried or found. Measurements quoted
in the design doc were taken on the author's own test tape (characterized in `CLAUDE.md` §2) and are
recorded results, not test assertions; the tests assert only what synthetic fixtures can prove.

## Status

Acquisition is proven byte-complete (a 48-minute capture with zero unrequested USB slots, zero
host loss). The registration engine matches its offline model on the author's fixtures. The live
frameserver, CMIO camera extension and configurator app are the remaining phases; see `CLAUDE.md`
§11.

## License

GPLv2 or later — see `LICENSE` and `NOTICE`.
