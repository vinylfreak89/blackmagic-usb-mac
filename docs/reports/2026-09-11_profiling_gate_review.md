# Profiling gate review

Reviewed the source at `698c11ae7202dca2166afee25d815ae5738ea033` and the peer's
`b9d1f7e` commit record. This is an inspection and fixture diagnostic, not a new timing
run or an implementation change. The peer reports the following timing observations:

```text
BENCH-SAMPLES 10000 registration_calls 0 gated 10000 checksum 50025288
WORKER-BENCH median 0.315 ms p95 0.328 ms
load 5.99: FIELDREG-BENCH median 20.992 ms p95 47.851 ms
load 3.12: FIELDREG-BENCH median 1.690 ms p95 2.073 ms
```

## What the benchmark does

`src/frameserver/tests/worker_bench.c` has two loops. The direct engine loop calls
`fieldreg_process` 10,000 times. The worker-like loop calls it only when
`sr.normal_picture` is true. Thus zero registration calls makes WORKER-BENCH blind
to registration cost, not the entire executable engine-free. The direct loop still
reports registration cost on this synthetic workload.

There is a separate enforcement defect: neither loop's timing is compared against
10 ms, and zero registration calls does not cause failure. Successful processing and
publication return exit status zero irrespective of elapsed time. `make bench` is
not an automated budget gate even if its fixture starts invoking registration.

The worker-like loop does not call the current production worker. It directly calls
classifier, engine and publisher, whereas `frameserver.c:process_item` also performs
audio-clock lookup, log-record assembly/enqueue, output-copy/enqueue and ownership
handoff, with publication on a separate thread. The benchmark therefore cannot be
called the whole current worker path merely by fixing its input. The existing
`tests/queue_bench.c` hooks the actual analysis worker and reports registered units
separately, but excludes independent publication sinks, has a 4096-sample capacity,
and is not itself the complete 10,000-unit budget gate either.

## Why this fixture never opens the classifier gate

The local `registration_v9.raw` contains 194 units; worker_bench unconditionally omits
the last one and cycles the remaining 193. Measuring the exact padding predicate
used by `signal_state.c` on every selected unit gives:

```text
fixture_units 194 bench_used_units 193 padding_fraction_range 0.0 0.0 below_0.98 193
```

The predicate counts UYVY sample pairs equal to chroma 128 / luma 16 in storage rows
0..6, 261..269 and 523..524. `classify_appearance` immediately returns Unknown when
the fraction is below 0.98. The fixture generator initializes rows with luma 2 and
does not construct this device padding. Other synthetic content may overwrite those
positions, but no selected unit satisfies even one padding sample in this fixture.
This is an input-model mismatch, not evidence the real capture lacks programme.
`registration_gate_test.py` already explicitly supplies padding for its own synthetic
fixture; do not weaken the classifier to make this benchmark pass.

Reproduction of the fixture diagnostic (read-only):

```sh
python3 -c 'import numpy as np; from pathlib import Path; p=Path("src/field_registration/tests/registration_v9.raw"); rows=list(range(7))+list(range(261,270))+[523,524]; a=np.memmap(p,dtype=np.uint8,mode="r").reshape(-1,756048); r=a[:,48:].reshape(-1,525,720,2)[:,rows]; fractions=((r[:,:,:,0]==128)&(r[:,:,:,1]==16)).mean(axis=(1,2)); print("fixture_units",len(a),"bench_used_units",len(a)-1,"padding_fraction_range",fractions[:-1].min(),fractions[:-1].max(),"below_0.98",int((fractions[:-1]<.98).sum()))'
```

## Fixture and instrumentation recommendation, not implemented

Use a versioned, hashed chronological capture-1 slice spanning source acquisition,
the first lock and maintained-lock card/programme material. The already analysed
counter >=6667 passage is a candidate; establish its exact eligibility/registration
and lock-phase counts with the current code instead of borrowing stale counts or
forcing a ProgramLike label. Keep startup/gated units visible in the population.

For the fixed 10,000 observations, define deterministic replay epochs/repetition
boundaries and reset state explicitly at those boundaries. Do not concatenate a
short slice as though the tape had moved continuously, or silently omit its final
unit using the synthetic fixture's special-case rule. Freeze counter/epoch metadata,
fixture hash, expected calls, publication counts and acquisition/maintained-lock
coverage. A gate must reject missing expected work, not merely print the count.

Report whole-path and phase-specific costs so cheap gated or maintained-lock units
cannot hide expensive acquisition. Retain a separate gated-path control. Instrument
the real paths through assembly and publication, excluding I/O as required by §11b;
state separate stage service times and end-to-end latency rather than adding stage
p95s. Add actual budget enforcement and a deliberate timing-regression control.
This review does not choose an unstated percentile interpretation of the budget.

## What the paired timing observations establish

The lower run puts direct-engine median and p95 below 10 ms on that fixture in that
run. It is useful evidence against treating 20.992 ms as a reproducible baseline
engine cost. It does not establish the whole-path budget, a CPU minimum, or every
acquisition/reacquisition case. The older record includes separate above-budget
tails; a new median does not retire their workloads without a matched comparison.

The timer is CLOCK_MONOTONIC elapsed time, not thread CPU time. The high/low difference
is consistent with contention, but two load-average observations do not establish
"from load alone". Core placement, scheduling, frequency/thermal state and background
activity are not isolated by load average. worker_bench does not explicitly request
the production worker's USER_INITIATED QoS, nor establish execution on a P-core.

Record binary/compiler flags and fixture hashes, phase mix, host load before/after,
power/thermal context where observable, repeated elapsed and CPU-time measurements,
and deadline exceedances. Do not kill owner applications. Host-induced elapsed
overruns still matter to live service under that load, even if they are not intrinsic
compute cost. Publish bounded observations, not an extrapolated minimum or a causal
claim the experiment did not isolate.

No bench implementation, classifier, engine or contract is changed in this review.
