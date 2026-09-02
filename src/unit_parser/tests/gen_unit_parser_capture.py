#!/usr/bin/env python3
"""Generate a deterministic tagged packet stream for unit_parser tests."""

from __future__ import annotations

import argparse
import random
import struct
from pathlib import Path

MAGIC = 0x31504143
DATA, HOSTLOSS, XFERERR, SESSION = 0, 1, 2, 3
VIDEO, AUDIO = 0x83, 0x84
UNIT_BYTES, HEADER_BYTES = 756_048, 48
AUDIO_SYNC = b"DeckLinkAudioResyncT"


def record(kind: int, endpoint: int, packet_index: int, sequence: int,
           status: int, requested: int, payload: bytes = b"") -> bytes:
    return struct.pack("<IBBHIIII", MAGIC, kind, endpoint, packet_index,
                       sequence, status, requested, len(payload)) + payload


def unit(counter: int, size: int = UNIT_BYTES) -> bytes:
    if size < HEADER_BYTES:
        raise ValueError("unit too small")
    header = b"\x00\x00\xff\xff" + struct.pack("<HH", counter, 0xE801) + bytes(40)
    raster = bytearray(bytes((128, 16)) * ((size - HEADER_BYTES) // 2))
    if len(raster) < size - HEADER_BYTES:
        raster.append(128)
    return header + bytes(raster[:size - HEADER_BYTES])


def resync(counter: int) -> bytes:
    return AUDIO_SYNC + struct.pack("<HH", counter, 0x6E65)


def pcm(sample: int) -> bytes:
    left = (sample & 0xFFFFFF).to_bytes(3, "little")
    right = ((-sample) & 0xFFFFFF).to_bytes(3, "little")
    return left + right + bytes(18)


def packetize(stream: bytes, endpoint: int, rng: random.Random,
              first_sequence: int = 0) -> list[bytes]:
    result: list[bytes] = []
    offset = 0
    sequence = first_sequence
    while offset < len(stream):
        size = min(len(stream) - offset, rng.randint(37, 4093))
        payload = stream[offset:offset + size]
        result.append(record(DATA, endpoint, 0, sequence, 0, size, payload))
        sequence += 1
        offset += size
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rng = random.Random(0x55504A31)

    # The first marker begins two bytes before a packet boundary. Counter 0 is
    # explicitly damaged by both a HostLoss record and a submission-seq gap.
    leading = b"XYZ"
    video_units = [
        unit(65534),
        unit(65535, UNIT_BYTES - 224),
        unit(0),
        unit(1),
    ]
    video_packets: list[bytes] = []
    video_packets.append(record(DATA, VIDEO, 0, 0, 0, 5,
                                leading + video_units[0][:2]))
    video_stream = b"".join(video_units)[2:] + unit(2)[:100]
    packetized = packetize(video_stream, VIDEO, rng, first_sequence=1)
    # Insert explicit loss while counter 0 is being accumulated and also skip
    # one submission sequence. Payload order remains otherwise exact.
    insertion = len(packetized) // 2
    video_packets.extend(packetized[:insertion])
    video_packets.append(record(HOSTLOSS, VIDEO, 0, 0, 0, 4096))
    for item in packetized[insertion:]:
        fields = list(struct.unpack("<IBBHIIII", item[:24]))
        fields[4] += 1
        video_packets.append(struct.pack("<IBBHIIII", *fields) + item[24:])

    audio_stream = b"abcde" + resync(65535)
    audio_stream += b"".join(pcm(i) for i in range(17))
    audio_stream += resync(0)
    audio_stream += b"".join(pcm(100 + i) for i in range(19))
    audio_packets = packetize(audio_stream, AUDIO, rng)
    # Force a realignment test after an explicit audio hole.
    audio_packets.append(record(HOSTLOSS, AUDIO, 0, 0, 0, 192))
    audio_packets.extend(packetize(b"junk" + resync(1) + pcm(999), AUDIO, rng,
                                   first_sequence=len(audio_packets) + 1))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as out:
        note = b"unit_parser synthetic truth"
        out.write(record(SESSION, 0, 0, 0, 0, len(note), note))
        # Endpoint ordering is the contract; cross-endpoint interleave is not.
        for item in video_packets:
            out.write(item)
        for item in audio_packets:
            out.write(item)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
