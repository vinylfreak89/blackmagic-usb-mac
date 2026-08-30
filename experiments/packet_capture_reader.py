#!/usr/bin/env python3
"""Streaming verifier/dispatcher for capture_tagged_bench's tagged capture format."""

from __future__ import annotations

import mmap
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

TPC_MAGIC = 0x31504143
TPC_HEADER = struct.Struct("<IBBHIIII")
TPC_DATA = 0
TPC_HostLoss = 1
TPC_TransferError = 2
TPC_SESSION = 3
TPC_TICK = 4
VIDEO_ENDPOINT = 0x83
AUDIO_ENDPOINT = 0x84

PayloadCallback = Callable[[bytes], None]


@dataclass
class EndpointStats:
    endpoint: int
    packets_per_transfer: int
    records: int = 0
    payload_bytes: int = 0
    zero_length: int = 0
    short_payload: int = 0
    transfers: int = 0
    sequence_gaps: int = 0
    inversions: int = 0
    packet_index_errors: int = 0
    status_errors: int = 0
    hostloss_records: int = 0
    hostloss_packets: int = 0
    hostloss_bytes: int = 0
    transfer_errors: int = 0
    first_sequence: int | None = None
    last_sequence: int | None = None
    _current_sequence: int | None = field(default=None, repr=False)
    _next_packet_index: int = field(default=0, repr=False)

    def observe_data(
        self,
        packet_index: int,
        sequence: int,
        status: int,
        requested: int,
        actual: int,
    ) -> None:
        if self._current_sequence is None:
            if packet_index != 0:
                self.packet_index_errors += 1
            self._current_sequence = sequence
            self._next_packet_index = 0
            self.first_sequence = sequence
            self.transfers = 1
        elif sequence != self._current_sequence:
            if self._next_packet_index != self.packets_per_transfer:
                self.packet_index_errors += 1
            if packet_index != 0:
                self.packet_index_errors += 1
            delta = sequence - self._current_sequence
            if delta <= 0:
                self.inversions += 1
            elif delta > 1:
                self.sequence_gaps += delta - 1
            self._current_sequence = sequence
            self._next_packet_index = 0
            self.transfers += 1
        if packet_index != self._next_packet_index:
            self.packet_index_errors += 1
        self._next_packet_index = packet_index + 1
        self.last_sequence = sequence
        self.records += 1
        self.payload_bytes += actual
        if status:
            self.status_errors += 1
        if actual == 0:
            self.zero_length += 1
        elif actual < requested:
            # Iso req_len is slot capacity; a short payload is not by itself an
            # error. Endpoint framing/counters decide continuity downstream.
            self.short_payload += 1
        if actual > requested:
            raise ValueError(
                f"endpoint 0x{self.endpoint:02x} actual_len {actual} "
                f"exceeds req_len {requested}"
            )

    def finish(self) -> None:
        if (
            self._current_sequence is not None
            and self._next_packet_index != self.packets_per_transfer
        ):
            self.packet_index_errors += 1


@dataclass
class TaggedStats:
    file_bytes: int
    records: int = 0
    ticks: int = 0
    session: str = ""
    video: EndpointStats = field(
        default_factory=lambda: EndpointStats(VIDEO_ENDPOINT, 128)
    )
    audio: EndpointStats = field(
        default_factory=lambda: EndpointStats(AUDIO_ENDPOINT, 80)
    )

    def endpoint(self, value: int) -> EndpointStats | None:
        if value == VIDEO_ENDPOINT:
            return self.video
        if value == AUDIO_ENDPOINT:
            return self.audio
        return None

    def assert_lossless(self) -> None:
        problems = []
        for endpoint in (self.video, self.audio):
            label = f"0x{endpoint.endpoint:02x}"
            for name, value in (
                ("sequence gaps", endpoint.sequence_gaps),
                ("completion inversions", endpoint.inversions),
                ("packet-index errors", endpoint.packet_index_errors),
                ("packet status errors", endpoint.status_errors),
                ("HostLoss records", endpoint.hostloss_records),
                ("TransferError records", endpoint.transfer_errors),
            ):
                if value:
                    problems.append(f"{label} {name}={value}")
        if problems:
            raise RuntimeError("tpc provenance validation failed: " + "; ".join(problems))


def walk_tagged(
    path: str | Path,
    *,
    on_video: PayloadCallback | None = None,
    on_audio: PayloadCallback | None = None,
    progress: bool = True,
) -> TaggedStats:
    """Seek-walk one tpc file and dispatch DATA payloads without splitting it."""
    path = Path(path)
    size = path.stat().st_size
    stats = TaggedStats(size)
    next_progress = 5 << 30
    last_tick = -1
    with path.open("rb") as capture:
        mm = mmap.mmap(capture.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            offset = 0
            while offset < size:
                if size - offset < TPC_HEADER.size:
                    raise RuntimeError(
                        f"tpc truncated header: {size-offset} bytes at {offset}"
                    )
                (
                    magic,
                    record_type,
                    endpoint_value,
                    packet_index,
                    sequence,
                    status,
                    requested,
                    actual,
                ) = TPC_HEADER.unpack_from(mm, offset)
                if magic != TPC_MAGIC:
                    raise RuntimeError(
                        f"tpc bad magic 0x{magic:08x} at byte {offset}"
                    )
                payload_start = offset + TPC_HEADER.size
                payload_length = actual if record_type in (TPC_DATA, TPC_SESSION) else 0
                payload_end = payload_start + payload_length
                if payload_end > size:
                    raise RuntimeError(
                        f"tpc truncated payload at byte {offset}: "
                        f"need {payload_length}, have {size-payload_start}"
                    )

                endpoint = stats.endpoint(endpoint_value)
                if record_type == TPC_DATA:
                    if endpoint is None:
                        raise RuntimeError(
                            f"tpc DATA has unknown endpoint 0x{endpoint_value:02x} "
                            f"at byte {offset}"
                        )
                    endpoint.observe_data(
                        packet_index, sequence, status, requested, actual
                    )
                    if actual:
                        callback = (
                            on_video if endpoint_value == VIDEO_ENDPOINT else on_audio
                        )
                        if callback is not None:
                            callback(mm[payload_start:payload_end])
                elif record_type == TPC_HostLoss:
                    if endpoint is None:
                        raise RuntimeError(
                            f"tpc HostLoss has unknown endpoint 0x{endpoint_value:02x}"
                        )
                    endpoint.hostloss_records += 1
                    endpoint.hostloss_packets += requested
                    endpoint.hostloss_bytes += actual
                elif record_type == TPC_TransferError:
                    if endpoint is None:
                        raise RuntimeError(
                            f"tpc TransferError has unknown endpoint 0x{endpoint_value:02x}"
                        )
                    endpoint.transfer_errors += 1
                elif record_type == TPC_SESSION:
                    stats.session = mm[payload_start:payload_end].decode(
                        "ascii", "replace"
                    )
                elif record_type == TPC_TICK:
                    if status < last_tick:
                        raise RuntimeError(
                            f"tpc non-monotonic TICK {status} after {last_tick} "
                            f"at byte {offset}"
                        )
                    last_tick = status
                    stats.ticks += 1
                else:
                    raise RuntimeError(
                        f"tpc unknown record type {record_type} at byte {offset}"
                    )
                stats.records += 1
                offset = payload_end
                if progress and offset >= next_progress:
                    print(
                        f"tpc pass: {offset/(1<<30):.1f}/{size/(1<<30):.1f} GiB, "
                        f"{stats.records:,} records",
                        file=sys.stderr,
                        flush=True,
                    )
                    next_progress += 5 << 30
            if offset != size:
                raise RuntimeError(f"tpc parse ended at {offset}, file size {size}")
        finally:
            mm.close()
    stats.video.finish()
    stats.audio.finish()
    stats.assert_lossless()
    return stats


def format_tagged_stats(stats: TaggedStats) -> str:
    lines = [
        f"tpc records={stats.records:,}; ticks={stats.ticks:,}; "
        f"session={stats.session!r}"
    ]
    for endpoint, name in ((stats.video, "video"), (stats.audio, "audio")):
        lines.append(
            f"{name} 0x{endpoint.endpoint:02x}: {endpoint.payload_bytes:,} B; "
            f"packets={endpoint.records:,}; transfers={endpoint.transfers:,}; "
            f"zero={endpoint.zero_length:,}; short={endpoint.short_payload:,}; "
            f"seq_gaps={endpoint.sequence_gaps}; inversions={endpoint.inversions}; "
            f"packet_index_errors={endpoint.packet_index_errors}; "
            f"status_errors={endpoint.status_errors}; "
            f"HostLoss={endpoint.hostloss_records}; TransferError={endpoint.transfer_errors}"
        )
    return "\n".join(lines)
