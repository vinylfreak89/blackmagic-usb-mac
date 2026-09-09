# Box classification: first candidate falsified, not implemented

This is an engine-side diagnostic, not harness code or a production change.
It tests whether a scale-relative partition of row spread plus two edge-anchored
bands is sufficient to observe a box. It is not sufficient. No threshold is
adjusted to make its census match the reference.

## Attempt and deciding negative

`box_partition_probe.py` measures each row's variance in the central aperture
after omitting one nominal horizontal-blanking duration from each end. It fits
two log-variance classes by least within-class squared error. The low class
must reach BOTH field edges, with a majority of high-class rows between them.
The two classes, aperture and majority requirement are experimental choices,
not owner rules. A scale-relative cut does not establish structurelessness.

Constructed controls have 240 rows. A box has noise-only edge bands and
structured rows 30..209. Its gain-quarter copy has the same classification
and extent (floating-point scaling before quantization, not a claim about an
8-bit fade). A one-ended band is rejected. But adding deterministic texture
to EVERY edge row of that box still produces `box=true`: its edge variance is
44.893920, middle variance 703.809760, and the fitted cut is 177.754828. The
edge rows are not structureless; their structure is merely weaker. This
negative fails, and the diagnostic intentionally returns exit status 1.

Thus neither gain invariance nor two end-anchored low-spread runs licenses a
box classification. An observer must distinguish structurelessness from lower
contrast, rather than treating the weaker of two fitted classes as a band.

## Same-source check

The strict CAP1 walker reads 919 exact units of the original commercial capture;
508 have counter >=6667. Candidate counts are f1=255, f2=380, both=254.
These are candidate outputs, NOT true-box counts or an accepted comparison.
The harness's 159-unit report has not been joined to this diagnostic by counter.

Counter 6668 is an additional concrete failure. The card is boxed, but f1 is
rejected because its final row (NTSC 262) has variance 57.791157 against the
field-derived cut 43.789389. The head-switch area contaminates the field-edge
test. Anchoring at the delivered edge does not by itself identify the box's
lower band in the presence of terminal damage. F2 is called boxed. Using this
observation as an exemption would therefore leave forbidden switch evidence
in f1 at the very unit whose acquisition we need to prevent.

At 6700 both fields are candidates, with proposed content bounds 55..236 and
318..498. At 6704 and 6705 those candidate bounds also agree, despite the old
raw-top reader's three-line disagreement. This is useful but does not outweigh
the two falsifications. These extents are not used for placement or centring.

## Status and reproduction

No production box classifier, conditional-acquisition bypass, extent hold,
geometry reset, picture-top change or comb promotion has landed. The remaining
implementation requirement is an independently validated observation of
structureless edge bands, including a terminal head-switch region, followed by
the specified fade hold and geometry-class reset. This is a measurement/design
failure of this candidate, not a request to change the owner's contract.

From the repository root:

```sh
probe_dir=$(mktemp -d /private/tmp/box-partition.XXXXXX)
python3 src/field_registration/tests/box_partition_probe.py --output "$probe_dir/result.json" --capture /Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc
```

Expected exit 1: `negative_rejected` is false. Omitting `--capture` runs only
the constructed controls. Output is scratch scalar measurements, never an
archived program raster. The original run is
`/private/tmp/box-partition.BobWW7/result.json`.

The production baseline replay first failed under the sandbox:

    Assertion failed: (!fs_open(&f,&c)), function main, file queue_bench.c, line 32.

That failure is reported as observed, not called pre-existing. The subsequent
authorized replay with host access completed: 930 observations, 919 exact and
published, zero input/publication/log drops. Nonzero applied d1: 0; nonzero
applied d2: 0; geometry_lock_known: 0 throughout. No first lock. The eleven
moves remain absent, but this is the unchanged production baseline, not a
successful box-classification change. Worker median/p95 2.693/14.092 ms over
919 exact units, 10.872/16.192 ms over 452 registration calls. Sidecar:
`/private/tmp/box-baseline.mma1ZB/registration.csv`. Host-access success alone
does not establish the cause of the initial open failure.
