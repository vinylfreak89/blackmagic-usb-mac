# Unit parser

`unit_parser` is the allocation-free framing layer between `capture_core` and
media consumers. Caller-owned storage is allocated once using
`unit_parser_size()`/`unit_parser_alignment()`; packet processing performs no
allocation, I/O, locking, or thread creation. Callbacks are synchronous and
observation pointers are valid only until that callback returns.

The parser consumes `capture_core` callbacks in their documented per-endpoint
submission order. It independently checks `(submit_seq,pkt_index)` continuity,
records packet status, and accepts explicit `HostLoss`/transfer-error events.
Transport truth never comes from pixel or audio content.

## Video contract

The parser recognizes marker candidates even when `00 00 ff ff` is split
between packets, then validates the following header before accepting a unit
boundary. It extends the 16-bit counter monotonically within an explicit epoch.

A fixed-raster consumer may accept a unit only when all of these are true:

```
kind == UNIT_VIDEO_E801
transport == UNIT_TRANSPORT_COMPLETE
byte_count == 756048
payload_bytes == 756000
fixed_raster_eligible == true
```

Device-short units are emitted as `UNIT_TRANSPORT_SHORT` for archival and
logging, never padded or read through the next marker. Explicit host loss,
packet gaps, packet status, or transfer errors produce `UNIT_TRANSPORT_HOLE`.
Leading/trailing bytes without validated framing are `UNFRAMED` observations.

## Audio contract

Audio is parsed as 24-byte wire records after phase lock. Ordinary records
emit the two active S24LE channels and a cumulative stereo-sample ordinal.
`DeckLinkAudioResyncT` records emit the shared 16-bit counter and its epoch
extension without incrementing the sample ordinal. Correlation is reported;
the parser never pairs and drops an orphan video or audio observation.
