# Capture core

`capture_core` exposes the live Shuttle and deterministic `.tpc` replay through one callback
API. Acquisition owns the USB event thread; an internal delivery thread invokes callbacks. Ring
pressure is represented as loss rather than hidden by blocking the event loop.

## `.tpc` records

Every record begins with the packed 24-byte little-endian header
`<IBBHIIII>`: magic `CAP1`, type, endpoint, packet index, submission sequence, status, requested
length, and actual length. Only `DATA` and `SESSION` carry `actual_len` payload bytes.

Types are `DATA=0`, `HostLoss=1`, `TransferError=2`, `SESSION=3`, and `TICK=4`. Two reserved
`TransferError` packet indices refine its meaning:

- `0xffff`: submission or resubmission failed; `status` is the positive libusb error number.
- `0xfffe` with `status=UINT32_MAX`: **control truth was lost** because even the metadata reserve
  was exhausted. The producer emits this terminal cleanliness marker at most once. It is not a
  USB transfer error and a verifier must report it separately.

The default after control-truth loss is to continue capturing while permanently marking the run
not clean. Set `cc_config.fail_stop_on_control_loss` to end with `CC_END_INTERNAL_ERROR` after the
same marker; the CLI exposes it as a trailing `--fail-stop-control-loss` option. By contrast, a
transfer that cannot be resubmitted before
`resubmit_deadline_ms` ends the whole session: its future USB slots provably cannot be scheduled,
so continuing only the other endpoint would manufacture a misleading capture.

`HostLoss` is aggregate accounting. Very large adjacent loss may span multiple records; consumers
sum `req_len` packets and `actual_len` bytes. A byte count larger than 32 bits is emitted as
multiple records.

The CLI's leading `SESSION` note records the selected input, exact mode word, ring size, and
configured transfer fleet (or identifies replay and its source path). It is provenance text, not
a parser contract.

## USB stacks

`cc_config.usb_backend` picks the device's USB stack; the CLI takes a trailing `--iousbhost`.

- **libusb** (the default). libusb's Darwin backend chooses each read's bus frame. A late
  resubmission is moved past frames it never reads, and nothing records them. capture_core infers
  them from completion timing (the unread-slot model) and writes `CC_PI_UNSCHEDULED` /
  `CC_PI_UNSCHEDULED_LATE` HostLoss with an estimated count.
- **IOUSBHost** (`capture_iousbhost.m`, only in builds with `-DCC_WITH_IOUSBHOST`; the CLI has it).
  Each endpoint's reads are queued at consecutive explicit frame numbers, from one serial
  user-interactive dispatch queue with no real-time policy. A read lying wholly in the past is
  refused by macOS; it is queued 8 frames ahead and the exact number of frames between goes out as
  `CC_PI_UNSCHEDULED` just before its data. A read only partly in the past is accepted, and its
  past packets fail with `kIOReturnIsoTooOld`. They stay DATA records with that status, which the
  parser flags, and they are counted in the unread-slot statistics with a HOST LOSS line. No
  `_LATE` records. Completions are held back until `cc_start` succeeds, so a failed start hands
  nothing over. Another refusal is retried every millisecond until `resubmit_deadline_ms`. Each
  attempt goes out as a `0xffff` TransferError, then the session ends, as with libusb. Device
  removal notices come on IOUSBHost's own queue and are moved onto the completion queue. Opens as
  a normal user with no entitlement, and refuses endpoints whose bInterval is not 1. Packet
  statuses are IOReturn values here, libusb ones there; the SESSION note names the backend.
  `make test-iousbhost` runs three tests under TSan. The unmodified backend against a fake
  IOUSBHost (`ih_fake_iousbhost.m`: a real-time bus clock, the refusal and too-old rules measured
  here, every packet carrying its microframe number), checking that each microframe is accounted
  for exactly once through stalls, requeues landing exactly 1, 8, 14 and 20 frames late,
  refusals, an unplug, the start gate and a stop during a stalled callback. The same, end to
  end through capture_core (the delivered packet stream and its HostLoss records). And
  capture_core's side against a scripted mock of the `ih_*` interface
  (`capture_iousbhost_mock.c`). The fake does not model interrupt coalescing, packet errors
  other than too old, short packets, or how a real unplug fails the transfers in flight.

Measured on hardware, 2026-10-17 (M3, bars), by holding the completion queue (`shuttle-capture-hold`):

- Held 490 to 505 ms, the next read started 1 to 15 frames in the past and was accepted with
  8 to 120 video packets past due. Held 510 ms and longer, it lay wholly in the past and was
  refused. A shared start frame once left audio's first read 6 frames late at start-up, so each
  endpoint now takes its own.
- Held 0.51, 0.52, 0.53, 0.8, 1.5 and 3 s, every gap was reported once per endpoint at the
  transfer it precedes (26 to 2,526 frames), with seq gaps 0. The kernel's completion time of each
  transfer's last packet put the same frame counts in the gaps to within 0.03 frames. Gap-free
  transfers stepped within 0.035 ms of schedule, over 3 minutes too. The session reports both
  (`IOUSBHost bus check`).
- The stream content does not resolve a gap to the frame. Audio samples missing around those
  gaps came to −0.17, +0.20 and +1.15 frames off the count, and video bytes to about −1.5. The
  device's own buffering sits between the bus and the data.
- macOS fails as too old the frame after the one the bus is in, as well: with the bus at a
  read's first frame, its first two frames failed. Each past-due count is checked against the
  bus frames read before and after the enqueue, allowing for that, and holds of 490 to 505 ms
  (24 to 120 packets) all fell inside. The session names any transfer whose count does not.
- Every transfer was deallocated by the time the device closed; close reports any that are not.
- Not exercised on hardware: an unplug during capture, and a refusal other than lateness (both
  are in the fake-device test).

## Lifecycle and statistics

The lifecycle is `open -> start -> stop -> close`. A successful start means the complete device
fleet is submitted. `stop` is idempotent and drains callbacks; `on_end` fires exactly once.
Statistics are authoritative after stop. `control_records_dropped > 0` or
`control_loss_markers == 1` means the archive cannot claim complete control provenance even when
all DATA bytes balance.

Callback-thread refusal uses a thread-local owning-session marker, set through the final
callback and cleared on thread exit. Joined worker IDs are never used to identify callers;
they may already have been reused by another thread. Tests deliberately alias those IDs to
an external caller and check that stop/close still succeed.
