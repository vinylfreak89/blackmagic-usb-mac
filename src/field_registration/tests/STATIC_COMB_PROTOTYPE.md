# Quarantined static-comb prototype — not production

`static_comb_prototype.patch` preserves the experimental engine diff against
`796f6d09491174628f2a71ed1b426ccf57ee11a0`. The baseline source blob is
`e48c77035fd8e9e859d6b3e3d7464a9c7292d3fc`. No production target applies it.
The production source is restored byte-for-byte; acquisition, top measurement
and box classification are unchanged. Do not promote this patch before the
box observation and its exclusion of gap-separated switch evidence exist.

## Why this is quarantined

Rule 8 uses two different quantities: box bars are recorded picture rows in
the conserved line account, but the lower structureless bar separates visible
structured content from the switch. That is the gap which excludes switch
measurement. Darkness alone does not establish a box. Claude's counter-6668
audit shows both switch flags true at the prototype's first acquisition; the
card's content ends at 236 and the switch is below its lower band. We agree
that this evidence is excluded, and the resulting lock is not sanctioned.
The prototype changes neither acquisition site: improving confirmation exposes
the missing box classification rather than resolving it.

An EARLIER version (absolute energy-interval comparison) was replayed: 367/508
registerable units decisive, 365 agreeing, first lock counter 6668, eleven
nonzero field-2 applications. This is a regression, not capture acceptance.
That run's analysis median/p95: 2.722/12.172 ms over 919 exact units;
10.7945/12.629 ms over 452 registration calls. Zero input/publication/log drops.
These are not timings or a census of the final patch: the final paired-energy
correction has NOT had a whole-capture replay. None was run during quarantine.

## Attempted instrument and limits

Eight-pixel sums feed positive-product comb energy. Static evidence is retained:
each vertical strip's current/previous vertical curvature must correlate most
strongly at zero against every cyclic phase permutation, strictly and positively.
This removes constant/linear ramps and tests stationary structure without a
generated-blanking tolerance or a typed minimum surviving-block count. It is
an experimental certificate, not proof against every motion pattern.

The comb tests a local neighbourhood (unsettled -1..+2, settled precedence +/-1),
using identical supported pixels for each candidate and both times. The winner
must beat alternatives separately at BOTH times. Comparing absolute energy
intervals across times incorrectly rejected counter 739 despite zero winning
at each time; paired contrasts fix that control without a margin threshold.

Final patch: synthetic static detail, coherent pan, accidental matches and ramp
controls 6/6; cached raw controls 7/7 (6687/6690/6700 -> 0; 13653 -> -1;
13972/739 -> 0; 333 -> +1). Raw control bounds are the normal 240 picture rows,
not the production switch detector's bounds. These controls do not validate
acquisition or box geometry. The wider existing comb suite is 17/19:

    FAIL: remote minimum is searched
    FAIL: periodic aliases do not calibrate

The local test does not establish remote uniqueness. Those assertions were not
changed to manufacture a pass. Production baseline remains COMB 19/19 and
UNLOCKED-PLACEMENT 24/24; the deliberately failing-first STATIC-COMB is 2/6:

    FAIL: real_picture_fluctuation_does_not_discard_static_detail
    FAIL: real_picture_fluctuation_does_not_discard_static_detail
    FAIL: real_picture_fluctuation_does_not_discard_static_detail
    FAIL: two_accidental_blocks_cannot_license_a_pan

## Isolated reproduction (no capture replay)

From the repository root, with the baseline source blob above (check with
`git hash-object src/field_registration/field_registration.c`):

```sh
probe_dir=$(mktemp -d /private/tmp/comb-quarantine.XXXXXX)
mkdir "$probe_dir/tests"
cp src/field_registration/field_registration.c src/field_registration/field_registration.h src/field_registration/cea608.c src/field_registration/cea608.h "$probe_dir/"
cp src/field_registration/tests/static_comb_test.c "$probe_dir/tests/"
patch -d "$probe_dir" -p3 < src/field_registration/tests/static_comb_prototype.patch
clang -O3 -std=c11 -Wall -Wextra -Werror "$probe_dir/tests/static_comb_test.c" "$probe_dir/cea608.c" -lm -o "$probe_dir/static_comb_test"
"$probe_dir/static_comb_test"
```

For existing provenance-checked caches from `static_mask_probe.py`, pack the
seven previous/current pairs into scratch (exclusive creation; never committed):

```sh
python3 src/field_registration/tests/pack_static_comb_controls.py /private/tmp/v10-static-mask "$probe_dir/controls.raw"
"$probe_dir/static_comb_test" "$probe_dir/controls.raw"
```

Quarantine verification used the already packed scratch controls, not a new
capture read. Temporary patched source was checked against the preserved
prototype; production test and queue-bench binaries were rebuilt from baseline
so they do not silently retain the experimental implementation.
