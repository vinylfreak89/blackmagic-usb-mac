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

## Lifecycle and statistics

The lifecycle is `open -> start -> stop -> close`. A successful start means the complete device
fleet is submitted. `stop` is idempotent and drains callbacks; `on_end` fires exactly once.
Statistics are authoritative after stop. `control_records_dropped > 0` or
`control_loss_markers == 1` means the archive cannot claim complete control provenance even when
all DATA bytes balance.
