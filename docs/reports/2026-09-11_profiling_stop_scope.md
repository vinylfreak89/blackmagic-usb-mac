# The profiling stop — what can be measured today, and what cannot

The owner's gate, set before the contract work began and never lifted: **the entire live engine
profiled, numbers only, no optimisation.** This establishes what that can mean today. It contains no
optimisation and proposes none.

## The finding that decides the shape of this work

**Every timing instrument in this project lives in a `tests/` directory. The live path has none.**

| file | `clock_gettime` / `mach_absolute_time` |
|---|---|
| `frameserver/frameserver.c` | **0** |
| `frameserver/frameserver_replay.c` | **0** |
| `frameserver/frame_publisher.c` | **0** |
| `frameserver/audio_publisher.c` | **0** |
| `unit_parser/unit_parser.c` | **0** |
| `capture_core/capture_core.c` | 6 — a ms helper, a condvar timedwait, and loop pacing; **none is per-stage profiling** |

Everything that times anything is a test binary: `frameserver/tests/worker_bench.c`,
`tests/queue_bench.c`, and the `field_registration/tests/*` probes.

**So "profile the entire live engine" cannot be satisfied by running anything that exists.** The live
engine is not instrumented. Every ms/unit figure on record was produced by a test harness or by an
ad-hoc instrumented build that is not in the tree.

## What the recorded numbers actually measure

§11b's budget is "the whole frameserver worker path (classifier + registration + assembly + publish,
excluding I/O) ≤ 10 ms on the reference M3 P-core, single-threaded". The instrument behind it is
`worker_bench`, which links exactly:

`worker_bench.c` + `frame_publisher.c` + `signal_state.c` + `field_registration.c` + `cea608.c`

**It therefore excludes** the unit parser, the capture core, the audio publisher, the output and log
queues, and `frameserver.c`'s own orchestration — i.e. most of what "the live engine" contains.

⚠️ **And it runs on 194 units looped ~51 times.** The fixture `registration_v9.raw` is 146,673,312
bytes = **194 units, 6.5 s of tape**; the bench takes 10,000 samples from it. Registration cost is
content-dependent (comb searches, caption decodes, switch measurement), so this measures **the cost
distribution of those 194 units**, not of a tape. A p95 from a 51-times-repeated 6.5-second loop is not
a p95 over the acceptance captures.

⚠️ **Figures quoted from elsewhere are not reproducible from the tree.** CLAUDE.md records
"analysis-worker registration calls median/p95 9.428/18.227 ms (O2, includes copy/enqueue, excludes
independent sinks)" and similar; the instrumentation that produced them is not present, so those
numbers cannot be re-derived or checked today.

## What the gate therefore requires, stated as work and not begun

1. **Per-stage timing in the live path**, off the USB callback, recording rather than printing — parser,
   classifier, registration, assembly, publish, audio, and the queue handoffs — so a stage's cost is
   attributable rather than inferred from a bench that omits it.
2. **Run over real material**: the four acceptance captures, each end to end, rather than a looped
   fixture, so the distribution is a tape's.
3. **Numbers only.** The owner's words. No threshold is to be tuned, no stage reordered, nothing made
   faster as part of this. Anything found slow is reported and left.

## Two things measured while establishing the above

**1. The budget's own regression gate is not exercising the stage the budget is about.**
`make bench` on the current tree:

```
BENCH-SAMPLES 10000  registration_calls 0  gated 10000
```

**Registration ran on none of the 10,000 samples.** `signal_state_classify` returns
`normal_picture == false` for every unit of `registration_v9.raw`, so the worker loop takes the gated
branch every time. The `WORKER-BENCH` figure it then prints is the cost of **classifier + publish with
the engine skipped** — it is not a measurement of the path §11b's 10 ms applies to, and it cannot fail
that budget however slow registration becomes. This is load-independent and reproducible.

**WHY it closes, measured directly** (a standalone probe running only `signal_state_classify` over the
fixture, sharing no code with the bench):

```
units 194 | appearance PROGRAM_LIKE 0 | source PRESENT 0 | normal_picture 0
unit 0: appearance = SIGNAL_APPEARANCE_UNKNOWN (0)
```

**It is the APPEARANCE that fails, not the source hysteresis.** The classifier calls the fixture
programme-like on **none** of its 194 units — every one is `SIGNAL_APPEARANCE_UNKNOWN` — so
`stable_source` can never reach `PRESENT` and `normal_picture` can never be true. No number of units
and no warm-up changes that; the gate cannot open on this fixture.

That is consistent with what `registration_v9.raw` is: a fixture built to exercise the REGISTRATION
engine's geometry, not to look like programme to a classifier that was written later.

⚠️ CLAUDE.md records "9,996 of 10,000 units actually invoking registration" for a synthetic worker.
**That was not this fixture**, and **whether this bench ever exercised registration is NOT established
here** — only that it cannot now, and why.

**2. No timing taken on this machine is comparable to §11b's budget, and no recorded figure states its
load.** §11b specifies "the reference M3 P-core, single-threaded". Measured during this work, the host
was running Chrome at 105% CPU, WindowServer at 41%, the Claude app at 37% and a trading platform at
36%, with a 1-minute load average of 6.75. **Every ms/unit figure in the project's record was taken on
this host under conditions nobody wrote down.** A timing without its load is not reproducible, and the
budget it is compared against assumes a quiet core.

**3. `fieldreg_process` alone measures ~21 ms median and ~47 ms p95 here, reproducibly — and that is
far above every figure in the record.** Two runs, `FIELDREG-BENCH` (the engine called unconditionally,
10,000 samples):

| run | load before | median | p95 | load after |
|---|---|---:|---:|---|
| 1 | 6.75 | 20.797 ms | 46.778 ms | — |
| 2 | 5.99 | 20.992 ms | 47.851 ms | 4.84 |

⚠️ **Two corrections to my own readings of this, in order.** First I dismissed the figure as host load.
Then, seeing the medians agree to within **0.9%**, I argued that "across different load" was evidence
against contention-domination. **That second inference is also wrong, and a third session's independent
sample during run 2 is why**: load 4.51 with Chrome at 97%, WindowServer 39%, a trading platform at 29%
— **the same applications as run 1**. The load AVERAGES differed (6.75 against 5.99) but the contention
PROFILE did not, and the average includes `worker_bench` itself at ~99% of a core.

So the agreement shows the measurement is **stable under this contention profile**; it does NOT show
the figure is independent of it. Capturing load either side records the contention, it does not remove
it. The honest statement is narrower than either of my two: **reproducible on this host with these
applications running, cause not established, and a quiet-host run is still the discriminator** — not a
formality but the only thing that separates the three candidates below.

Against the record — 1.35 ms and ~1.4 ms (rounds 8 and 10), 4.853/24.293 ms (the retired v9 engine,
already called over budget), 9.617/16.603 ms (native classifier+engine) — 21 ms median is far above
all of them. Three candidates and this document settles none: the engine is slower than when those
were taken; `FIELDREG-BENCH` measures something the other figures did not; or a quiet core would
produce a different number.

⚠️ **If it survives a quiet machine, one consequence is immediate: 47 ms p95 exceeds the 33.37 ms unit
period**, so at p95 the engine alone would not keep up with realtime, before the parser, classifier,
publisher, audio path and queues are counted. **That is a conditional, not a claim** — the quiet-host
measurement has not been taken, and taking it needs a machine not running Chrome and a trading
platform.

⚠️ **Nothing above is a measurement of the live engine.** It is a statement of what the existing
measurement covers, what it does not, and what conditions any number here would need to carry.
