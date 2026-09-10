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

⚠️ CLAUDE.md records an earlier run of this same bench with "9,996 of 10,000 units actually invoking
registration". It is now 0. **Whether that is a regression, a fixture change or a configuration
difference is NOT established here** — only that the gate now closes on every unit of this fixture.

**2. No timing taken on this machine is comparable to §11b's budget, and no recorded figure states its
load.** §11b specifies "the reference M3 P-core, single-threaded". Measured during this work, the host
was running Chrome at 105% CPU, WindowServer at 41%, the Claude app at 37% and a trading platform at
36%, with a 1-minute load average of 6.75. **Every ms/unit figure in the project's record was taken on
this host under conditions nobody wrote down.** A timing without its load is not reproducible, and the
budget it is compared against assumes a quiet core.

⚠️ **The first `FIELDREG-BENCH` reading of this session — 20.797 ms median, 46.778 ms p95 for
`fieldreg_process` alone — was taken under that load and is NOT reported as an engine figure.** It is
far above every number in the record (1.35 ms, ~1.4 ms, 4.853/24.293 ms, 9.617/16.603 ms), and the
honest reading is that it measures the host, not the engine.

⚠️ **Nothing above is a measurement of the live engine.** It is a statement of what the existing
measurement covers, what it does not, and what conditions any number here would need to carry.
