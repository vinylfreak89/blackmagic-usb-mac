# Current-unit signal gate and the 27:18 loss

The premise is rule 5: non-program units do not run registration. Rule 5b
resets geometry on snow-like loss, not on a deck mute. Upstream source state
must not be settled by downstream applied crops. This repair changes those
ownership/lifecycle seams; it does not change picture-edge measurement.

## Deciding tests

- `registration_output_cannot_mutate_signal_state` failed at unit 5 with the
  old feedback API. Both feedback APIs and the settled-phase members are
  removed. Source confirmation and geometry confirmation are now separate.
  Review found that its conditional compilation made the post-fix version
  vacuous: neither history reached the classifier. That runtime test and its
  feature macro are now removed. `retired_registration_api_absent` instead
  requires references to both retired names to fail compilation, checks that
  neither is exported by the actual object, and tests all four checks with
  reintroduced declarations/definitions. No surviving API accepts registration
  output, so there is no meaningful two-downstream-histories runtime test.
- `registration_gate_test.py` failed on the first grey unit, counter 12.
  It exercises the real parser, classifier, engine and publisher: 29 exact
  synthetic units, nine mute units held at the previous nonzero crop, and
  initial acquisition held at standard placement. Publisher metadata is
  checked separately from the registration record.
- `signal_loss_2718_test.py` failed 32 assertions before the classifier
  repair. The fixed paced replay processes/publishes 449 exact units out of
  451 observations, with zero pool/ring/surface drops. Whole-tape index is
  extended device counter minus 4511, not observation ordinal.

| Whole-tape indices | Result |
|---|---|
| 49105–49112 | 8 Incoherent / Unknown; no registration |
| 49113–49117 | 5 SubBlackMuteLike / Muted, preserved |
| 49118–49125 | 8 SnowLike / Reacquiring, each marked lock-like loss |
| 49126–49136 | 11 carried-forward SubBlackMuteLike labels, preserved |
| 49105–49166 | 62 SignalGateHold rows at the preceding published (0,0) |

Exactly one begin-segment action occurs in that 62-unit interval, at 49118.
The replay has two in total: initial acquisition and the snow edge. Mute and
the return from it do not repeatedly reset the engine. Source Present returns
at 49167. The separate synthetic gate test proves holding a nonzero crop;
this raw passage's preceding crop happens to be zero.

## Measurement and limits

`coherence_probe.c` measures the real parser's eligible rasters, independently
recomputing the classifier's diagnostic statistics. It uses the existing
classifier's sampled body: raw rows 20–256 / 282–518 and every fourth luma
sample. Adjacent-row Pearson correlation is taken separately for each field
and reduced by its median; temporal Pearson correlation compares that same
field with its preceding eligible unit. Neither is the other instrument's
pooled row-correlation number. Means/offsets are fitted out by Pearson's
definition. The median row sigma is compared with the full measured luma
range of that field's regenerated blanking rows 7–15 / 270–278.

Representative independent measurements, spatial / temporal correlation:

| Unit | Field 1 | Field 2 |
|---|---:|---:|
| 49104, preceding program | .946 / .975 | .950 / .978 |
| 49105, wreck onset | .751 / .700 | .295 / .419 |
| 49117, last sub-black | −.007 / .929 | .006 / .831 |
| 49118, first snow | −.004 / .767 | .006 / .655 |
| 49122, one temporally repeated field | −.001 / .9997 | .008 / .343 |
| 49125, fields in different stages | .014 / .213 | .511 / .127 |

The new numeric limits are explicitly empirical, not standards: snow requires
row correlation below .1 and temporal correlation below .8 in at least one
field, plus median row sigma above its blanking range. The measured snow row
correlations were −.020..+.038, while normal-program controls had a minimum
.699. The temporal boundary lies between .767 in the first snow field and
.831 in the preceding sub-black field. Wreck onset uses the measured joint
spatial <.5 / temporal <.8 departure. Once triggered, it blocks otherwise
ProgramLike successors until both fields recover temporally (>=.8) or
spatially (>=.9), or an actual mute is identified. The wreck's both-field
spatial minimum never exceeded .887; returned program was >=.934. A source
still has to satisfy its existing acquisition confirmation. A mute ends the
disrupted-picture episode, not the loss epoch.

These are bounded measurements, not proof of universal separation. An
unseen low-coherence legitimate source remains a possible false positive;
unmeasurable temporal evidence can delay detection. One field is sufficient
to block the unit: the fields enter/leave the noise stage at different times,
and a temporarily repeated field must not hide the other's noise.

Two variants were rejected during control testing. Row range alone admitted
low-amplitude black dither as snow; using median row sigma against the field's
whole blanking range rejects it. Keeping a disruption latch through an
identified mute delayed a clean commercial fade by two program units; the
mute now ends that episode. Safety evidence is separate from appearance
hysteresis, so detecting snow does not rewrite the subsequent sub-black label.
`snow_loss_and_mute_lifecycle` tests low-amplitude noise, the dither negative
control, one loss reset, and no reset on mute/program return.

## Control captures

| Input | Eligible measurements | Appearance/source changes vs pre-fix |
|---|---:|---:|
| composite_program_30s.tpc | 919 | 10, all before counter 6593 |
| w_2100s.tpc (EP) | 621 | 0 |
| w_300s.tpc (SP) | 608 | 0 |
| sp_vstab_off_slice.tpc | 608 | 0 |

The commercial stable interval, counter >=6593, has zero changed labels.
Its earlier changes are one Incoherent at 6275 and nine SnowLike at
6277, 6321, 6330, 6333, 6336, 6337, 6356, 6358 and 6360. They belong to
the documented rewind interval, not the stable-program control; these ten
individual events have not been separately adjudicated as tear versus snow.

The diagnostic aborts on CAP1 HostLoss/TransferError/status errors and parser
packet-provenance flags. It reports device counter discontinuities, invalidates
temporal comparison, and excludes ineligible units. On the commercial input,
counter 6043 is Complete but ineligible with counter-discontinuity flag 16;
6250 is Short with the same flag. Thus 919 here is an eligible-classifier
count, not a claim that the earlier 920 exact-marker census was wrong.
An initial assertion rejecting all parser flags aborted on these rows; it
was corrected to distinguish counter continuity from packet-byte provenance.

## Reproduction and cost

Build `make -C src/signal_state test test-asan` and
`make -C src/frameserver frameserver_replay test-registration-gate test`.
The latter needs IOSurface access. Then run
`python3 src/frameserver/tests/signal_loss_2718_test.py CAPTURE NEW_SCRATCH_DIR`.
The output directory must not already exist. Replay is paced and bounded by
a 180-second subprocess timeout. No program bytes are in the repository.

The probe builds with `cc -O3 -std=c11 -Wall -Wextra -Werror
src/signal_state/tests/coherence_probe.c src/signal_state/signal_state.c
src/unit_parser/unit_parser.c -lm -o /private/tmp/v10-coherence-probe`.
It takes a CAP1 input and emits scalar measurements to stdout. An optional
scratch directory exports the named diagnostic rows for visual inspection.

Final classifier-only synthetic test: median .306 ms, p95 .326 ms.
Active-path synthetic worker (10,000 units; 9,996 registration calls,
four acquisition gates): engine 2.398 / 2.522 ms median/p95, complete
classifier/engine/publisher worker 2.738 / 3.093 ms. A worker test on the
engine-only rule-1 fixture was mostly gated and is not an active-path cost;
the benchmark now prints invocation counts to prevent that misreading.
Final rule-1 golden: 2.458 / 2.580 ms; rule 3: .444 / .476;
rule 4: .442 / .459. All pass the focused 10-ms checks.

This is not a blanket budget pass: an earlier 10,000-unit run on the broad
retired-v9 fixture measured engine 4.853 / 24.293 ms median/p95. That engine
tail exceeds the budget and remains a performance finding. The tests above
do not erase it. No full-tape performance or new registration acceptance is
claimed by this classifier repair.
