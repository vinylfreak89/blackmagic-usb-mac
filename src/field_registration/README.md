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
source segment. It clears temporal history, pending decisions, and diagnostic
band histograms. It does **not** redefine zero: offsets are always absolute in
the device's transport-raster coordinates. Do not call it for ordinary program
edits. The signal-state layer owns that distinction; registration geometry
alone cannot prove whether a sustained new edge baseline is a real plateau or
a newly acquired source segment.

## Evidence and policy

The exact device padding at lines 0-6, 261-269, and 523-524 establishes the
transport ruler. VBI signatures validate the expected field origins. Neither
is treated as a program-picture displacement by itself.

Production mode (`FIELDREG_EVIDENCE_MOTION_PHASE`, the default) estimates
relative field phase from low-pass luma in three broad horizontal bands. For
each band it measures same-parity vertical motion, subtracts half that motion
from the direct inter-field weave displacement, and records the resulting phase
vote. This is necessary for scrolling credits: an uncorrected weave search
mistakes four lines/frame of source motion for about two lines of registration.

Two agreeing bands normally define the per-unit vote. If spatial layers carry
different real phases, a uniquely and coherently vertically moving broad band
may win instead; raw temporal energy cannot win because VHS dot crawl is noisy
but is not coherent integer translation in both parity histories. A 120-unit
rolling mode provides the state trajectory and hysteresis. Fades, cuts, weak
correlation, search-boundary-clipped motion, and unresolved spatial disagreement
abstain and hold the last baseline. A best motion estimate at `-6` or `+6` is
censored evidence—the source may have moved farther—and is never converted into
a registration correction.

Top/bottom picture edges are still measured independently in all three bands,
but their fast transient result is **diagnostic only**. A full-tape audit showed
that allowing this path to modify state manufactured thousands of transitions
from changing content apertures, overlays, and dot crawl. Such evidence is
logged as `UnknownEdgeTransient`; only the rolling motion-compensated phase may
move the applied mapping. This deliberately gives up live correction of some
real one-frame jumps. The sidecar preserves those candidates for post, while
the live path avoids silently creating much more damage than it repairs.

`FIELDREG_EVIDENCE_DUAL_EDGE` retains the absolute top/bottom estimator for
diagnostics and controlled material. It measures each field against nominal
envelopes `19..256` and `282..518`; it is not the general production default.

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
  --start-unit 4 --model phase

src/field_registration/tests/field_registration_golden \
  --untagged-capture UNTAGGED_CAPTURE --audio-spans AUDIO_SPANS --marker-index MARKER_INDEX \
  --csv UNTAGGED_CAPTURE_DECISIONS --field-origin-census FIELD_ORIGIN_CENSUS \
  --model phase --output /tmp/field_registration-phase.csv
```

The runner reports Python-port parity separately from agreement with the
independent rigid-picture census. Matching the old decision log proves port
fidelity; it does not make every old decision physical truth.
`--start-unit` must match any deterministic device-arming interval omitted by
the decision CSV; it skips bounded source units without training the engine.

On an M3 host, motion-phase mode processed the 6,160 exact legacy units
at about 2.5 ms median per 29.97-frame unit (about 13x real time, roughly 7.5%
of one core). Against the 4,042 independently measurable untagged_capture census rows,
the slow live mapping agreed on 3,908 (96.68%). It intentionally held the
baseline through brief edge-only events rather than applying them; among rows
where it emitted an explicit decision, agreement was about 99.6%. These are
limited calibration measurements, not a claim that untagged_capture or any rendered
video is perfect. The census has no truth label for spatially incompatible
source layers.

The 86,293-unit full-tape audit applied 48 baseline transitions: 42,767 units
at `(0,0)`, 43,030 at `(1,0)`, and 496 at `(2,0)`. Rejecting clipped temporal
motion removed two spurious negative-offset episodes. The audit logged 5,353
fast edge-transient candidates without applying any of them. Those counts are
an algorithm trace, not physical ground truth; the late recording really does
contain spatially incompatible layers, so no global `(d1,d2)` can make every
pixel region agree.

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
