# The patch on a capture whose audio transfers hold 128 packets, as capture_core has submitted them since 2026-10-16
# (ecd98dfb raised A_NPK from 80). The test captures are older (80 packets), so they never showed that the builder took
# 11520/11616 bytes (80 packets of 6 records, or 4 records more) as the only normal audio transfer: on a 128-packet capture
# every transfer looked unusual, each audio fill grew to the edges of the stretch read, and on 2026-11-22 13-11-20 (5:52) a
# fill of two one-unit gaps took 1.18 GB and the next clusters of the stretch failed ("windows of two clusters overlap").
#
#   repack   the fixture's audio regrouped into 128-packet transfers: the same packets in the same order, every video record
#            where it was, each new transfer written where its last packet arrived
#   two-glitches-128  two glitches 150 units apart on the repacked capture, the resync inside each a sample late (two intervals
#            of 1603 and 1600, as at 5:52, so each cluster has an audio gap and an audio window), one clip: both clusters filled,
#            every unit and sample equal to the source
#
# usage: test_capture_patch_npk128.py <capture.tpc (80-packet audio)> <scratch dir>
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from test_capture_patch_clips import glitch, move_resyncs, sidecar, clip, run_case, units
from test_capture_patch import H, MAGIC
from region import load

def repack_audio(src, dst, npk=128):
    """src with its audio data packets regrouped into transfers of npk: packet i of the audio stream becomes packet i % npk of
    transfer first_seq + i // npk, and each transfer's records are written together where its last packet stood (a partial
    last transfer at the end of the file). Every other record is kept where it was."""
    b = open(src, 'rb').read(); out = bytearray(); pend = []; n = 0; seq0 = None; p = 0
    while p + 24 <= len(b):
        m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p); assert m == MAGIC
        ln = 24 + (al if t in (0, 3) else 0)
        if ep == 0x84:
            assert t == 0, 'only data records on the audio endpoint are repacked'
            if seq0 is None: seq0 = seq
            r = bytearray(b[p:p + ln]); H.pack_into(r, 0, m, t, ep, n % npk, seq0 + n // npk, st, req, al); pend.append(bytes(r)); n += 1
            if n % npk == 0: out += b''.join(pend); pend = []
        else: out += b[p:p + ln]
        p += ln
    assert p == len(b)
    out += b''.join(pend); open(dst, 'wb').write(out)

def audio_packets(path):
    b = open(path, 'rb').read(); p = 0; pk = []; tx = {}
    while p + 24 <= len(b):
        m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p); ln = 24 + (al if t in (0, 3) else 0)
        if ep == 0x84 and t == 0: pk.append(bytes(b[p + 24:p + ln])); tx[seq] = tx.get(seq, 0) + 1
        p += ln
    return pk, tx

def main():
    src, S0 = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(S0): sys.exit('remove %s first' % S0)
    os.makedirs(S0); src128 = os.path.join(S0, 'src128.tpc')
    repack_audio(src, src128)
    a80, t80 = audio_packets(src); a128, t128 = audio_packets(src128)
    assert a80 == a128, 'the repacked audio packets differ from the source\'s'
    odd = {q: n for q, n in t128.items() if n != 128}
    assert not odd or list(odd) == [max(t128)], ('transfers of other sizes than 128 before the last', odd)
    assert max(t80.values()) == 80, ('the source is not an 80-packet capture', max(t80.values()))
    print('repack: %d audio packets, %d transfers of 80 -> %d of 128' % (len(a80), len(t80), len(t128)), flush=True)
    good, gL, gR = units(src128)
    nwhole = sum(1 for o, c, fm, ok in load(src128, 0, os.path.getsize(src128)).marks if ok and fm == 0xe801)
    S = os.path.join(S0, 'two-glitches-128'); os.makedirs(S); T = os.path.join(S, 'T.mov.raw.tpc'); T1 = os.path.join(S, 'one.tpc')
    b1 = glitch(src128, T1); b2 = glitch(T1, T, 0.5 + 150 / nwhole); os.remove(T1)
    move_resyncs(T, [b1[2], b2[2]], 1)               # each glitch's sound off the cadence by a sample (1603 then 1600), as at 5:52
    sidecar(T, os.path.join(S, 'T.mov.registration.csv'), S)
    run_case('two-glitches-128', S, T, [clip(src128, S, 'clipN')], good, gL, gR, dict(os.environ))
    print('npk128: all tests passed')

if __name__ == '__main__': main()
