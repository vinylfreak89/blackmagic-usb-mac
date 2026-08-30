#!/usr/bin/env python3
"""Generate a synthetic Tagged USB Packet Capture (.tpc) with known totals.

The capture core's tests need a well-formed tagged stream whose per-endpoint
byte and packet counts are known independently of the code under test. Real
captures are large and machine-specific; this generator produces an equivalent
stream deterministically from a seed, so the tests are self-contained.

Record layout (24-byte header, little-endian) + payload:
    u32 magic 'CAP1' | u8 type | u8 endpoint | u16 pkt_index
    u32 submit_seq   | u32 status | u32 req_len | u32 actual_len
Types: 0 DATA (payload = actual_len bytes), 1 HostLoss, 2 TransferError,
       3 SESSION (payload = text), 4 TICK (status = elapsed ms).

Usage:
    gen_packet_capture.py --out fixture.tpc --expect fixture.expect \
        [--video-transfers 200] [--audio-transfers 300] [--seed 1] \
        [--short-every N] [--hostloss-at K]

The .expect file holds four integers: video_bytes video_packets audio_bytes
audio_packets — the truth the tests compare against.
"""
import argparse, random, struct, sys

MAGIC = 0x31504143
V_EP, A_EP = 0x83, 0x84
V_PKT, V_NPK = 15360, 128     # video: 128 packets of up to 15,360 B per transfer
A_PKT, A_NPK = 0xC0, 80       # audio: 80 packets of up to 192 B per transfer
UNIT_MARKER = b"\x00\x00\xff\xff"


def rec(typ, ep, pi, seq, status, req, actual, payload=b""):
    return struct.pack("<IBBHIIII", MAGIC, typ, ep, pi, seq, status, req, actual) + payload


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect", required=True)
    ap.add_argument("--video-transfers", type=int, default=200)
    ap.add_argument("--audio-transfers", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--short-every", type=int, default=0,
                    help="every Nth video packet is short (device-short behaviour); 0 = none")
    ap.add_argument("--hostloss-at", type=int, default=0,
                    help="emit one HostLoss record after this many video transfers; 0 = none")
    a = ap.parse_args()
    rng = random.Random(a.seed)

    vb = vp = ab = apk = 0
    counter = 0
    with open(a.out, "wb") as f:
        note = f"gen_packet_capture seed={a.seed} v={a.video_transfers} a={a.audio_transfers}".encode()
        f.write(rec(3, 0, 0, 0, 0, 0, len(note), note))
        vi = ai = 0
        vseq = aseq = 0
        # interleave transfers roughly as the bus does (video ~16 ms, audio ~10 ms)
        while vi < a.video_transfers or ai < a.audio_transfers:
            do_video = vi < a.video_transfers and (ai >= a.audio_transfers or (vi * 10) <= (ai * 16))
            if do_video:
                for pi in range(V_NPK):
                    n = V_PKT
                    if a.short_every and (vp + 1) % a.short_every == 0:
                        n = V_PKT - 496
                    payload = bytearray(rng.randbytes(n))
                    # sprinkle a plausible unit marker + counter so unit parsers see structure
                    if pi == 0:
                        payload[0:4] = UNIT_MARKER
                        payload[4:8] = struct.pack("<HH", counter & 0xFFFF, 0xE801)
                        counter += 1
                    f.write(rec(0, V_EP, pi, vseq, 0, V_PKT, n, bytes(payload)))
                    vb += n; vp += 1
                vseq += 1; vi += 1
                if a.hostloss_at and vi == a.hostloss_at:
                    f.write(rec(1, V_EP, 0, vseq, 0, 3, 3 * V_PKT))
                if vi % 60 == 0:
                    f.write(rec(4, 0, 0, 0, vi * 16, 0, 0))
            else:
                for pi in range(A_NPK):
                    n = A_PKT if rng.random() < 0.6 else 144
                    payload = bytes(rng.randbytes(n))
                    f.write(rec(0, A_EP, pi, aseq, 0, A_PKT, n, payload))
                    ab += n; apk += 1
                aseq += 1; ai += 1
    with open(a.expect, "w") as e:
        e.write(f"{vb} {vp} {ab} {apk}\n")
    print(f"wrote {a.out}: video {vb} B / {vp} pkts, audio {ab} B / {apk} pkts -> {a.expect}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
