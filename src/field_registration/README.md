# Registration engine

`field_registration` estimates independent signed integer line offsets `(d1,d2)` for
the two fields in one exact 756,048-byte `e801` unit. A positive offset means
that field extraction starts later in the 525-line transport raster. The
library does not deinterlace, read files, allocate, log, or own threads.

The caller owns one `field_registration` state per stream. Call
`fieldreg_discontinuity()` after unknown byte placement; it
clears temporal and pending-switch evidence without discarding learned band
modes. Every call returns the applied offsets, a named mode, confidence, and
the evidence needed for a sidecar decision log.

Call `fieldreg_begin_segment()` after acquisition/relock establishes a new
source segment. It clears the learned absolute band gauge as well as temporal
state. Do not call it for ordinary program edits. The signal-state layer owns
that distinction; registration geometry alone cannot prove whether a sustained
new edge baseline is a real plateau or a newly acquired source segment.

## Evidence and policy

The exact device padding at lines 0-6, 261-269, and 523-524 establishes the
transport ruler. VBI signatures validate the expected field origins. Neither
is treated as a program-picture displacement by itself.

Production dual-edge mode (`FIELDREG_EVIDENCE_DUAL_EDGE`, the default) learns the
stable top and bottom picture-edge modes for each field independently. A
single-unit correction is allowed when both edges report the same offset.
Top/bottom disagreement is `UnknownBandDisagreement`: the previous correction
is retained and the conflict is logged. A same-parity temporal cut gate prevents
scene changes from training the landmark model. Two consecutive nominal
top+bottom and temporal votes may release a stale nonzero correction, but
temporal or weave evidence can never create a nonzero correction. This is
important around fades, duplicate VBI-looking lines, and head-switch noise. The
weave score is relative evidence only; it cannot define the absolute anchor.

`FIELDREG_EVIDENCE_TOP_ONLY` reproduces the original Python estimator and is
retained only for golden-test compatibility. A valid line-21 payload is not an
absolute anchor: TBC/reslicing can duplicate a fully valid VBI line.

## Build and tests

```sh
make -C src/field_registration test
```

The streaming golden runner never splits a capture into endpoint files. For
tagged input it seek-walks the CAP1 records; for the legacy mixed capture it
uses the saved audio-span and marker indexes.

```sh
src/field_registration/tests/field_registration_golden \
  --packet-capture capture.tpc \
  --csv review_registration.csv \
  --start-unit 4 --model dual

src/field_registration/tests/field_registration_golden \
  --untagged-capture UNTAGGED_CAPTURE --audio-spans AUDIO_SPANS --marker-index MARKER_INDEX \
  --csv UNTAGGED_CAPTURE_DECISIONS --field-origin-census FIELD_ORIGIN_CENSUS \
  --model dual --output /tmp/field_registration-dual.csv
```

The runner reports Python-port parity separately from agreement with the
independent rigid-picture census. Matching the old decision log proves port
fidelity; it does not make every old decision physical truth.
`--start-unit` must match any deterministic device-arming interval omitted by
the decision CSV; it skips bounded source units without training the engine.

On an M3 host, the gated dual-edge model processed the 6,160 exact legacy
units at a 1.20 ms median and 1.31 ms p95 per 29.97-frame unit (about 27.7x
real time). On the 4,042 independently measurable census units it agreed on
4,039 (99.93%); the three disagreements are one-unit release-dwell lag, and all
3,851 explicit/confident decisions agree. These measurements are calibration
evidence from one capture, not hard-coded source assumptions.

The complete tagged-capture golden contains 86,300 bounded counter intervals:
86,293 exact units and seven startup shorts. Compatibility mode matches all
86,293 applied decisions and modes, all 56,441 explicit decisions, and every
logged diagnostic field. The same pass verified 46,075,614 CAP1 records with
no video sequence/packet gaps and no packet status errors. It reports 495,376
trailing video bytes after the final bounded interval rather than inventing an
extra frame.

In the final CMIO pathway, startup acquisition belongs to device arming. The
registration state is begun at the first stable source epoch; CMIO does not
publish diagnostic bars or short startup units. This is not capture-file
trimming—the normal recording client is expected to join an already-running
preview stream.
