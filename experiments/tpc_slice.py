#!/usr/bin/env python3
"""Cut a record-aligned slice out of a tagged packet capture (.tpc / CAP1).

The parser tolerates arbitrary endpoint edges (a leading video fragment and a
trailing one are reported, never silently merged), so a slice only has to start
and end on CAP1 record boundaries. Records are located by seeking to the byte
offset and walking forward to the first position where a run of consecutive
records validates; the slice is prefixed with a SESSION note naming its origin.

    tpc_slice.py whole.cap6 out.tpc --start-bytes 14800000000 --video-bytes 2300000000
"""
from __future__ import annotations
import argparse, struct, sys
MAGIC = 0x31504143
HDR = struct.Struct("<IBBHIIII")           # magic, kind, endpoint, pkt_index, seq, status, req, actual
KINDS = {0: "DATA", 1: "HOSTLOSS", 2: "XFERERR", 3: "SESSION", 4: "TICK"}
ENDPOINTS = {0x00, 0x83, 0x84}
MAX_REQ = 65536

def valid_header(b: bytes) -> bool:
    if len(b) < HDR.size: return False
    magic, kind, ep, _pi, _seq, _st, req, alen = HDR.unpack_from(b)
    return magic == MAGIC and kind in KINDS and ep in ENDPOINTS and req <= MAX_REQ and alen <= max(req, 4096)

def find_boundary(f, offset: int, depth: int = 16) -> int:
    """First byte >= offset at which `depth` consecutive records validate."""
    f.seek(offset); buf = f.read(2 * 1024 * 1024)
    pos = 0
    while True:
        i = buf.find(b"CAP1", pos)
        if i < 0: raise SystemExit("no record boundary within 2 MB of the requested offset")
        p, ok = i, 0
        while ok < depth and p + HDR.size <= len(buf) and valid_header(buf[p:p + HDR.size]):
            p += HDR.size + HDR.unpack_from(buf, p)[7]; ok += 1
        if ok == depth: return offset + i
        pos = i + 1

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--start-bytes", type=int, required=True, help="approximate byte offset to start at (aligned forward to a whole TRANSFER)")
    ap.add_argument("--video-bytes", type=int, required=True, help="stop after at least this many video (0x83) payload bytes")
    a = ap.parse_args()
    with open(a.src, "rb") as f, open(a.dst, "wb") as o:
        start = find_boundary(f, a.start_bytes)
        # A record boundary is not enough: a transfer is a GROUP of packets and its members carry
        # pkt_index 0,1,2,... A slice beginning mid-transfer starts at a non-zero pkt_index, and the
        # reader rejects that as packet-index errors rather than reading it (measured 2026-09-09:
        # all four acceptance slices failed provenance with exactly 3 such errors at their leading
        # edge, so every one of them was cut mid-transfer). Walk forward to the first video record
        # whose pkt_index is 0, so the slice begins on a whole transfer.
        f.seek(start); scanned = 0
        while scanned < 4000:
            here = f.tell(); h = f.read(HDR.size)
            if len(h) < HDR.size or not valid_header(h):
                f.seek(start); break                       # leave it where it was; the reader will complain
            kind, ep, pkt, _, _, _, alen = HDR.unpack(h)[1:8]
            if kind == 0 and ep == 0x83 and pkt == 0:
                start = here; break
            f.seek(here + HDR.size + alen); scanned += 1
        f.seek(start)
        note = f"tpc_slice of {a.src} from byte {start}".encode()
        o.write(HDR.pack(MAGIC, 3, 0, 0, 0, 0, len(note), len(note)) + note)
        f.seek(start); video = records = 0; end = start
        # Both ends must land on a whole transfer, not just the start: stopping mid-transfer leaves a
        # trailing partial group and the reader rejects it the same way (measured 2026-09-09 — fixing
        # only the leading edge took the error count from 3 to 1). So once enough video has been
        # taken, keep going until the NEXT video record would begin a new transfer.
        enough = False
        while True:
            here = f.tell(); h = f.read(HDR.size)
            if len(h) < HDR.size: break
            if not valid_header(h): raise SystemExit(f"record chain broke at byte {end}")
            kind, ep, pkt = HDR.unpack(h)[1], HDR.unpack(h)[2], HDR.unpack(h)[3]
            alen = HDR.unpack(h)[7]
            if enough and kind == 0 and ep == 0x83 and pkt == 0:
                f.seek(here); break
            payload = f.read(alen)
            o.write(h + payload); records += 1; end += HDR.size + alen
            if kind == 0 and ep == 0x83:
                video += alen
                if video >= a.video_bytes: enough = True
    print(f"wrote {a.dst}: bytes {start}..{end} of {a.src}, {records} records, {video} video payload bytes")

if __name__ == "__main__":
    main()
