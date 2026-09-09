# Analysis / publication / logging ownership

The owner asked for video analysis to consume available work without waiting
for publication or logging, with event-driven wakeups. Analysis remains ordered;
this change does not parallelize stateful registration or change its measurements.

## Boundaries

    capture backend -> delivery/parser -> input pool/ring -> analysis
                                                        |-> output pool/FIFO -> publication
                                                        |-> binary log FIFO -> log writer
    publication -------------------------------------------> completion in reserved log slot

Publication and logging are two additional workers. Audio already had an
independent consumer. The four frameserver workers now sleep on persistent
kqueue user events, only when their queue/predicate cannot progress. Notifications
are coalesced hints; release/acquire queue state is authoritative. Enqueue between
the final empty check and sleep leaves a pending event, not a lost condvar signal.
The libusb event owner and capture-core delivery implementation are unchanged;
this does **not** claim that every wait elsewhere in the capture stack was migrated.

`process_item` owns classification, registration and `last_decided_d1/d2`.
Every exact unit gets an immutable crop tuple. A signal-gated unit gets analysis's
last decided tuple, including when the corresponding delivery failed. Publication
success/failure neither changes that tuple nor clears the engine's temporal
witness. Input loss and signal-state actions still reach analysis in order.
The comb's saved raster is therefore the previous analyzed raster at its own
decided crop, not the last frame a consumer happened to accept. No comb algorithm
or signal-state rule was changed.

Publication copies from an independent preallocated raw-unit pool. Analysis's
input slot is freed immediately after this bounded copy/enqueue (or a counted
output-queue rejection), before any IOSurface operation or callback. A blocked
consumer cannot retain an input slot. The output slot is retained until its
callback returns. Surface ownership beyond the callback continues to follow the
existing IOSurface use-count API.

Analysis submits binary log snapshots, not CSV strings. Each reserves a log
sequence; a queued publication carries that sequence plus epoch and ordinal.
Completion verifies those identities and stores an atomic outcome in the reserved
slot. The logger cannot free/reuse a pending slot. It writes in analysis order,
only after the outcome exists; it never guesses `published=1` at enqueue time.
No decision or outcome from a newer epoch is substituted for an older one.

This bounded join has an explicit consequence: a publisher that never returns
prevents finalization of its row and later rows. It does **not** block analysis;
eventually the log queue can overflow and that file becomes incomplete. It does
not promise an endlessly complete log behind an endlessly blocked sink.

## Capacities and pressure

Defaults are **memory capacities**, not signal-derived constants:

| Queue | Capacity | Allocated payload/record storage |
|---|---:|---:|
| Publication | 16 units | 16 × (756,048 raw bytes + 48 metadata bytes) = 12,097,536 bytes |
| Log join/writer | 128 records | 128 × 800 = 102,400 bytes on this build |

Sixteen output slots match the existing default input-pool unit capacity, while
remaining physically separate. The log capacity matches the existing default
observation-ring item capacity. Both are configurable (`publication_queue_units`,
`log_queue_items`); neither is asserted to cover every disk/consumer stall.
At 29.97 units/s sixteen slots represent about 0.534 s, and 128 records about
4.27 s if every observation is a normal unit. The added raw copy is 22.66 MB/s
at realtime. These are arithmetic, not measured latency guarantees.

Output-full drops the new delivery request, records `PublicationQueueFull` and
increments `publication_queue_drops` (also included in `publisher_dropped`).
Input/analysis proceeds. Surface exhaustion and publisher rejection are distinct
outcomes (`PublisherFull`, `PublisherError`).

Log-full drops that record, increments `log_queue_drops` and the attached file's
error count. `fs_log_stop` returns -1; `log_last_file_errors` stays nonzero after
close. Existing OBS sidecar publication consequently refuses to promote it as
complete. Replay reports the counts and exits nonzero for log loss/write/close
failure. Record loss is not hidden by a successful shutdown or the next clean
file. Exact missing-record ranges are not reconstructed by this queue; the file
is explicitly incomplete.

## Log boundaries and shutdown

Attachment enables admission atomically. Each snapshot retains its file identity.
Detach disables admission, waits for in-flight admissions, then waits for the
captured queue boundary to drain before flushing/closing. Only the control caller
waits; neither analysis nor publication takes the log-control mutex. File writes
and CSV formatting run on the log worker. Open/flush/close can block their control
caller without blocking analysis.

Stop ends capture and drains analysis, publication, log and audio. `on_end` fires
once all four workers are terminal, with no subsequent media callbacks; `fs_stop`
then flushes/closes the file and exposes its final error verdict. Startup failure
releases and joins whatever workers were created. No event handle, payload pool
or pending log slot is destroyed while a worker can use it.

A callback or filesystem operation that never returns can still prevent a
complete drain. Arbitrary callback threads are not forcibly cancelled or freed
underneath. Analysis isolation does not claim cancellable consumer code.

Schema **18** appends `epoch`; existing ordinal/counter and decision columns
remain. The `published` bit is the actual completed publication outcome.
`applied_d1/d2` name the immutable chosen crop even for an undelivered unit.
The terminal ring-loss row now uses the same serializer as normal observations,
including the comb diagnostics and the epoch of the first lost observation.

## Deciding tests

- `daa2f1c`: barrier-controlled `enqueue_between_empty_check_and_sleep` failed
  on the old trylock/condvar implementation with `wait result 60` (ETIMEDOUT).
  With kqueue it passes with result 0. This is not an inference from inspection.
- `c4e9e4d`: `publisher_does_not_block_analysis` and
  `logger_does_not_block_analysis` each failed with zero units analyzed while
  the sink was blocked. Both now pass with **119/119** exact units processed.
  The old fixture comment incorrectly said 120 exact; a direct parser replay
  measures 119 exact and one trailing unframed observation. Tests now use the
  parser's eligible-ingress count rather than the comment.
- `gate_holds_analysis_decision_after_delivery_failure`: before, crop **1**;
  after, crop **2**, the actual last analysis decision. The second delivery is
  deliberately failed; the third unit is gated.
- A blocked publisher's retained raw slab is checksummed before/after input
  reuse. Its 16 output slots are retained and excess deliveries are counted.
- `log_queue_overflow_is_incomplete`: a two-record queue loses **118** records
  under a forced writer stall, continues video and returns an incomplete-file
  verdict. The default 128-record queue retains this finite test without loss.
- `make test` includes the new wakeup/isolation tests plus existing audio,
  IOSurface publication, drain, failed-start, concurrent-stop, log-rotation and
  write-failure tests. Input-pressure tests now stall analysis itself; a stalled
  downstream consumer is no longer a valid way to force input-pool exhaustion.
  Stall tests require video to continue. CSV loss accounting looks up the named
  column rather than incorrectly treating the final column as ring loss.
- ASan/UBSan queue tests and the forced two-slot input-ring suite pass.
  TSan queue tests pass. Its first isolation run expired the five-second parser
  watchdog, verbatim:

      Assertion failed: (atomic_load(&f->producer_done) && target>0), function main, file output_isolation_test.c, line 68.
      make: *** [test-queue-tsan] Abort trap: 6

  The instrumented 90-MB parser now has a 60-second test watchdog (180-second
  process alarm), not a pipeline delay or performance threshold. No TSan race
  diagnostic was emitted in the passing rerun.
- `test-registration-gate` passes: nine non-program units are unmeasured and
  the first mute unit holds the prior analysis crop.
- The final sandboxed rerun stopped before queue testing, verbatim:

      Assertion failed: (!fs_open(&f,&cfg)), function main, file output_isolation_test.c, line 68.
      make: *** [test-output-isolation] Abort trap: 6

  The same native test rerun with macOS system access passed. This records an
  open failure, not an established cause or a pre-existing platform defect.

These tests use synthetic bytes, not captured program content. Both consumer
stall tests and the failed-delivery test exercise the actual frameserver paths
with deterministic classification/registration/publication boundary doubles.

## Commercial replay and cost

`tests/queue_bench` times the actual analysis worker around `process_item`,
including output copying and enqueues. The publisher and log writer run normally.
The original `captures/composite_program_30s.tpc` was used, not a mid-transfer
slice. No other capture was processed.

Paced at 16,000 us per replay transfer, ring 512 MB, input pool 32:
**919 exact, 919 published, zero input-pool, input-ring, publication or log drops;
zero log errors**. High-water: input 3, output 1, log 1. Record: 930 rows, all
schema 18, epoch 1, no malformed rows. Crops, appearance, registration eligibility,
comb check and parity match the preceding commercial record in **every row**.

| Timed worker calls | Count | Median ms | p95 ms |
|---|---:|---:|---:|
| All exact units, including gates | 919 | 2.308 | 15.111 |
| Units invoking registration | 452 | 9.428 | 18.227 |

p95 is sorted index floor(0.95 × (N−1)); median averages the middle pair for
even N. This is an O2 worker-path measurement, not the earlier O3 standalone
engine probe, and is not evidence of a speedup. The 10-ms target is still exceeded;
optimization remains deferred by the owner. The unchanged comb remains ambiguous
on this capture; queue correctness does not mean geometry acceptance.

Scratch record: `/private/tmp/v10-queue-commercial.4Qzf9U/registration.csv`.
SHA-256: `834834b5b38a9144ae9de5e58d7d8723bfaa8025d06d16d06ecfd3a4d162a501`.
