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

The library remains allocation-free and retains no input pointer. Production
integration keeps USB capture on its own hot path: a preallocated lock-free SPSC
descriptor ring hands raw units to a registration worker, and another bounded
SPSC ring carries finalized pointers onward. The caller-owned delayed FIFO is
preallocated to `fieldreg_buffer_units()` entries; Python's `deque` in the
offline renderer is only a test harness for the same ownership contract.

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
but is not coherent integer translation in both parity histories. A bounded
contiguous candidate trajectory replaces the former 120-unit trailing mode.
The defaults require 30 supporting observations inside a 30-unit (about one
second) confirmation span, with a hard 36-unit presentation-buffer horizon.
Contradictory geometry replaces the candidate immediately, so votes from a
finished jump cannot trigger a delayed correction.

Top/bottom picture edges remain source-carried evidence, not a transport
oracle. Before an edge vote can move the whole field, the engine compares the
same-parity motion of both fields. It uses their **difference**, not either
absolute motion: coherent camera/credit motion cancels, while a change in
field registration remains. An opposite differential minimum vetoes the edge
vote even when two bands agree. This is essential for mixed rasters in which a
program layer and an overlay carry different vertical phases.

Fades, cuts, correlated whole-picture luma steps, weak correlation, and
search-boundary-clipped motion make the temporal estimator abstain. Unresolved
spatial disagreement also abstains unless the coherently moving asset breaks
the tie. A best motion estimate at `-6` or `+6` is censored evidence—the source
may have moved farther—and is never converted into a registration correction.
The state trajectory and the
individual unit mapping are deliberately separate. A strong absolute
observation is applied to that buffered unit immediately, even when it lasts
for only one unit; it does not have to survive a one-second dwell. The dwell
changes only the stable fallback used by units whose geometry abstains. When
that fallback settles, `decision_backdate` applies it only to still-buffered
abstaining units at the candidate onset. This changes crop selection, not
pixels, and permits transitions such as `(0,1) -> (1,0)` without treating
either field as a permanent anchor.

An abstaining unit holds the last accepted per-unit phase rather than snapping
back to an older fallback. That distinction removed a renderer-created
one-unit notch between otherwise coherent observations. The sidecar calls this
`HeldLastObservation`; convergence/backdating or an explicit trajectory reset
is required to replace it.

If geometry remains unresolved beyond `maximum_buffered_units`, the result sets
`trajectory_reset`. The caller flushes the trajectory already assigned to the
buffer, marks its abstaining units `HeldUnresolvedHorizon`, and reacquires a
fresh stable fallback. It must not rewrite those abstentions to `(0,0)` around
isolated observations—that creates raw/corrected crop chatter at the exact
point where evidence is weakest. No video unit may be dropped or repeated. The
sidecar presentation policy therefore
distinguishes `CorrectedObserved`, `CorrectedLocked`, `CorrectedBackdated`,
`HeldLastObservation`, `RawAwaitingLock`, and `HeldUnresolvedHorizon`; a visible
jump can be attributed to an observed correction versus honest raw
pass-through without inference.

Top/bottom picture edges are measured independently in all three bands. Two
bands agreeing on both fields form an absolute candidate. If real
spatial layers disagree, the uniquely coherent moving broad band wins;
otherwise the detector abstains. The full-width top+bottom pair is accepted
when the bands do not contradict it, or when their motion-compensated relative
phase directly corroborates it, and only when differential temporal evidence
does not contradict the proposed move. A local fast-edge delta remains diagnostic
because changing apertures, overlays, and dot crawl can move one band without
moving the field. Relative phase may continue a fallback candidate whose
absolute gauge is already established, but it may not invent a new absolute
pair by itself.

Cuts and correlated global-luma steps make the current unit abstain even when
its content-derived envelope appears coherent. A scene transition can change
that envelope without moving raster phase. Short real registration events away
from a cut remain correctable through independent band, relative-phase, or
same-parity corroboration.

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
at 2.58 ms median per 29.97-frame unit (12.9x real time, about 7.7% of one
core). Against all 4,042 independently measurable untagged_capture census rows, the
engine agreed on **3,784/4,042 (93.62%)** and on **all 3,499/3,499 confident
decisions**. All 258 remaining disagreements are conservative under-corrections:
192 census `(1,0)` rows held `(0,0)`, 52 census `(2,0)` rows held `(1,0)`, and
14 census `(2,0)` rows held `(0,0)`. None applied an opposite correction. That
delta from the older 98.81% result is deliberate: a rigid source-envelope edge
is not necessarily the dominant picture phase, and the new differential-motion
veto rejects it when those observables conflict. This is a bounded calibration
result, not a claim that untagged_capture or any rendered video is perfect. The census
has no truth label for spatially incompatible source layers.

The six-minute production-path proof from the 48-minute fixture-A capture processed 10,800
presented units (10,797 exact plus three device-short units) through the C
engine, the 36-unit caller FIFO, `estdif`, and x264. The finalized sidecar has
54 applied transitions, only five runs of 1–3 units, and zero cases where a
known per-unit observation was rendered at another offset. Backdating
overwrote zero known observations. Before the horizon-flush fix, the same
evidence produced 144 transitions and 70 short runs because the Python caller
rewrote abstentions to raw `(0,0)` around isolated observations; that was a
renderer policy bug, not detector evidence.

Two targeted algorithm-v3 presentation checks cover the previously reported
late-tape failures.  A 7,300-unit tail/credits window finalized only three
offset transitions, no 1--3-unit runs, no known-observation/application
mismatches, and no backdating over an observed unit.  A 4,500-unit window
around a known one-unit registration event at 36:40 held `(0,0)` for 4,499 units and applied one
directly observed one-unit `(1,0)` correction; it did not turn that event into
a delayed or permanent plateau.  These are policy/visual regression checks,
not claims that the spatially incompatible source layers can be made globally
coherent by one field offset.

The 86,293-unit full-tape **algorithm-v2 audit (superseded)** applied 48 baseline transitions: 42,767 units
at `(0,0)`, 43,030 at `(1,0)`, and 496 at `(2,0)`. Rejecting clipped temporal
motion removed two spurious negative-offset episodes. The audit logged 5,353
fast edge-transient candidates without applying any of them. Those counts are
an algorithm trace, not physical ground truth; the late recording really does
contain spatially incompatible layers, so no global `(d1,d2)` can make every
pixel region agree.

Algorithm v3 intentionally does not reproduce that superseded trajectory:
applied parity is 50,686/86,293 (58.74%) and old explicit-decision parity is
48,088/72,547 (66.29%). The 713 cases where both versions emit different
explicit decisions are 650 old `(1,0)` -> v3 `(0,0)`, 62 old `(0,0)` -> v3
`(1,0)`, and one old `(2,0)` -> v3 `(1,0)`. All occur in stable fallback
states, not as opposite current-unit observations. This is an investigated
algorithm change, not a failed C port: algorithm v2's trailing mode was proven
to manufacture/retain plateaus, while v3 is independently clean on all 3,499
confident untagged_capture census decisions. Full-tape v3's raw C trace applies `(0,0)`
to 75,729 units, `(1,0)` to 10,271, `(2,0)` to 180, and `(0,1)` to 113; the
caller FIFO subsequently backdates/holds a subset as documented above.

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
