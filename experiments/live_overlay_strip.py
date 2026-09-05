#!/usr/bin/env python3
"""Machine-readable identity strip shared by the live overlay and its gate."""
from __future__ import annotations

import struct

SYNC = 0xD3
CELL_WIDTH = 7
STRIP_X = 24
STRIP_HEIGHT = 6
_BODY = struct.Struct(">BIIbb")
PAYLOAD_BYTES = _BODY.size + 1
STRIP_WIDTH = PAYLOAD_BYTES * 8 * CELL_WIDTH


def payload(ordinal: int, counter_extended: int, d1: int, d2: int) -> bytes:
    body = _BODY.pack(SYNC, ordinal, counter_extended, d1, d2)
    checksum = 0
    for value in body:
        checksum ^= value
    return body + bytes((checksum,))


def bits(encoded: bytes):
    for value in encoded:
        for shift in range(7, -1, -1):
            yield (value >> shift) & 1


def draw(draw_context, y: int, encoded: bytes) -> None:
    for index, bit in enumerate(bits(encoded)):
        x0 = STRIP_X + index * CELL_WIDTH
        level = 240 if bit else 16
        draw_context.rectangle(
            (x0, y, x0 + CELL_WIDTH - 1, y + STRIP_HEIGHT - 1),
            fill=(level, level, level),
        )


def decode_gray(raw: bytes, stride: int = STRIP_WIDTH) -> tuple[int, int, int, int]:
    if len(raw) != stride * STRIP_HEIGHT:
        raise ValueError(f"strip is {len(raw)} bytes, expected {stride * STRIP_HEIGHT}")
    values = []
    for index in range(PAYLOAD_BYTES * 8):
        x0 = index * CELL_WIDTH
        total = 0
        for y in range(STRIP_HEIGHT):
            total += sum(raw[y * stride + x0:y * stride + x0 + CELL_WIDTH])
        values.append(1 if total >= 128 * CELL_WIDTH * STRIP_HEIGHT else 0)
    decoded = bytearray()
    for index in range(0, len(values), 8):
        value = 0
        for bit in values[index:index + 8]:
            value = (value << 1) | bit
        decoded.append(value)
    checksum = 0
    for value in decoded[:-1]:
        checksum ^= value
    if decoded[0] != SYNC or checksum != decoded[-1]:
        raise ValueError("strip sync/checksum mismatch")
    _sync, ordinal, counter, d1, d2 = _BODY.unpack(decoded[:-1])
    return ordinal, counter, d1, d2
