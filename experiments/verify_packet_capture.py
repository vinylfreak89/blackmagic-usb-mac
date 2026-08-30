#!/usr/bin/env python3
# verify_packet_capture.py <capture.tpc> [--split PREFIX]
# Verifier / de-multiplexer for capture_tagged_bench's tagged capture format (24-byte record headers).
# The format is contiguous — records are parsed in order, never scanned for; any magic
# mismatch is corruption and is reported with its byte offset.
#
# Reports per endpoint: payload bytes, packet counts, zero-length packets (scheduled-slot
# proof), submit-seq coverage (a seq gap = a transfer whose callback never delivered),
# callback-order inversions, HostLoss records, transfer errors.
# --split writes the concatenated payload per endpoint (video/audio raw streams).
import sys, struct

MAGIC = 0x31504143  # "CAP1"
TYPES = {0: "DATA", 1: "HostLoss", 2: "TransferError", 3: "SESSION", 4: "TICK"}

path = sys.argv[1]
split = None
if len(sys.argv) > 3 and sys.argv[2] == "--split":
    split = {0x83: open(sys.argv[3] + "_video.raw", "wb"),
             0x84: open(sys.argv[3] + "_audio.raw", "wb")}

st = {ep: dict(bytes=0, pkts=0, zero=0, short=0, seqs=set(), inversions=0,
               last_seq=-1, hostloss=0, lost_bytes=0, lost_pkts=0, xfererr=0)
      for ep in (0x83, 0x84)}
session = None
corrupt = ok = ticks = 0

with open(path, "rb") as f:
    off = 0
    while True:
        hdr = f.read(24)
        if len(hdr) < 24:
            if hdr: print(f"WARN: {len(hdr)} trailing bytes at {off}")
            break
        magic, typ, ep, pi, seq, status, req, alen = struct.unpack("<IBBHIIII", hdr)
        if magic != MAGIC:
            corrupt += 1
            print(f"CORRUPT: bad magic 0x{magic:08x} at offset {off}; aborting parse")
            break
        payload = f.read(alen) if typ in (0, 3) and alen else b""
        if typ in (0, 3) and len(payload) < alen:
            print(f"CORRUPT: truncated payload at offset {off}"); corrupt += 1; break
        if typ == 4:
            ticks += 1
        elif typ == 3:
            session = payload.decode("ascii", "replace")
        elif ep in st:
            s = st[ep]
            if typ == 0:
                s["bytes"] += alen; s["pkts"] += 1
                if alen == 0: s["zero"] += 1
                elif alen < req: s["short"] += 1
                s["seqs"].add(seq)
                if pi == 0:                       # order check at transfer granularity
                    if s["last_seq"] >= 0 and seq < s["last_seq"]: s["inversions"] += 1
                    s["last_seq"] = seq
                if split and alen: split[ep].write(payload)
            elif typ == 1:
                s["hostloss"] += 1; s["lost_pkts"] += req; s["lost_bytes"] += alen
            elif typ == 2:
                s["xfererr"] += 1
        ok += 1
        off += 24 + (len(payload) if typ in (0, 3) else 0)

print(f"records parsed: {ok}  corrupt: {corrupt}  ticks: {ticks}")
if session: print(f"session: {session}")
for ep in (0x83, 0x84):
    s = st[ep]; name = "video" if ep == 0x83 else "audio"
    gaps = 0
    if s["seqs"]:
        lo, hi = min(s["seqs"]), max(s["seqs"])
        gaps = (hi - lo + 1) - len(s["seqs"])     # transfers submitted but never delivered
    print(f"{name} 0x{ep:02x}: {s['bytes']:,} B in {s['pkts']:,} pkts "
          f"(zero-len {s['zero']:,}, short {s['short']:,}) | "
          f"seq span {len(s['seqs'])} used, GAPS={gaps} | inversions={s['inversions']} | "
          f"HostLoss recs={s['hostloss']} ({s['lost_pkts']} pkts / {s['lost_bytes']:,} B) | "
          f"xfererr={s['xfererr']}")
if split:
    for fh in split.values(): fh.close()
