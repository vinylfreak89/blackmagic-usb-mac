# Known-answer test of a bridge (bridge.py + assemble.py): a capture bridged with a renumbered copy of itself must come out,
# unit for unit and audio block for audio block, exactly the capture, and the parser must see no hole or sequence gap.
# The copy (counters +100, transfer numbers moved on) stands in for a recapture whose numbering differs from the capture's;
# with the same content, any byte placed wrong at a seam, any counter not moved back, any packet out of its transfer shows.
# Also: a loss record inside the recapture's stretch stops the bridge by name.
# usage: test_bridge.py [capture.tpc]   (default: captures/tape1_flagging_30s.tpc in the repository)
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import bridge
from region import load, UNIT
from joined import Joined

def units_and_audio(path, piece=160 << 20):
    """{counter: sha1 of the whole unit}, {resync counter: sha1 of the audio records up to the next resync}"""
    U = {}; A = {}; size = os.path.getsize(path); at = 0; carry = None
    while at < size:
        R = load(path, at, min(piece + 2 * UNIT, size - at))
        for o, c, fm, ok in R.marks:
            if ok and fm == 0xe801 and o + UNIT <= len(R.v): U.setdefault(c, hashlib.sha1(bytes(R.v[o:o + UNIT])).hexdigest())
        rs = R.resyncs
        for (i, _, c), (j, _, _) in zip(rs, rs[1:]): A.setdefault(c, hashlib.sha1(R.arec[i:j].tobytes()).hexdigest())
        at += piece
    return U, A

def repacketize(src, dst):
    """src with every DATA packet split in two (video at half its bytes, audio at a whole record), packet indices counted
    afresh in each transfer: a recapture whose packets fall differently from the capture's"""
    with open(dst, 'wb') as g:
        cur = {}
        for pos, h, pay in bridge.walk(src, 0, os.path.getsize(src)):
            m, t, ep, pi, sq, st, rq, al = h
            if t != 0: g.write(bridge.H.pack(*h)); g.write(pay); continue
            cut = al // 2 if ep == 0x83 else (al // 48) * 24
            parts = [pay[:cut], pay[cut:]] if 0 < cut < al else [pay]
            if cur.get(ep, (None,))[0] != sq: cur[ep] = (sq, 0)
            for x in parts:
                g.write(bridge.H.pack(m, t, ep, cur[ep][1], sq, st, rq, len(x))); g.write(x); cur[ep] = (sq, cur[ep][1] + 1)

def main():
    T = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'captures', 'tape1_flagging_30s.tpc')
    W = tempfile.mkdtemp(prefix='bridge_test_')
    try:
        D = os.path.join(W, 'donor.tpc'); OUT = os.path.join(W, 'out.tpc'); OFF = 100
        J = Joined(dict(parts=[dict(path=T, size=os.path.getsize(T), counter_delta=OFF, seq_delta={'131': 5000, '132': 7000})], notes=[]))
        with open(D, 'wb') as f:
            J.seek(0)
            while True:
                b = J.read(64 << 20)
                if not b: break
                f.write(b)
        U0, A0 = units_and_audio(T); cs = sorted(U0); assert cs[-1] - cs[0] == len(cs) - 1, 'the test capture wraps or has a gap'
        uA, uB = cs[0] + 300, cs[0] + 600
        per = os.path.getsize(T) / len(cs)
        win = lambda path, u: (max(0, int((u - cs[0]) * per) - (48 << 20)), min(os.path.getsize(path), int((u - cs[0]) * per) + (48 << 20)))
        tA = bridge.seam(T, uA, *win(T, uA)); tB = bridge.seam(T, uB, *win(T, uB))
        dA = bridge.seam(D, uA + OFF, *win(D, uA)); dB = bridge.seam(D, uB + OFF, *win(D, uB))
        b = dict(kind='bridge', donor=D, tA=tA, dA=dA, dB=dB, tB=tB, file_from=min(tA['v'][0], tA['a'][0]), file_to=bridge.whole_transfer_after(T, tB),
                 counter_delta=-OFF, seq_start=bridge.seq_start(tA), units=[uA, uB - 1])
        m = bridge.measure(T, b)
        print('bridge: %d bytes in place of %d, counters moved: %d headers, %d resyncs, kv %d ka %d' % (m['bytes'], m['file_to'] - m['file_from'], m['headers'], m['resyncs'], m['kv'], m['ka']))
        assert m['headers'] == uB - uA, ('picture headers moved', m['headers'], uB - uA)
        assert m['resyncs'] == uB - uA, ('resyncs moved', m['resyncs'], uB - uA)
        os.makedirs(os.path.join(W, 'plan')); json.dump({'bridge-0': [m]}, open(os.path.join(W, 'plan', 'plan.json'), 'w'))
        r = subprocess.run([sys.executable, os.path.join(HERE, 'assemble.py'), T, OUT, os.path.join(W, 'plan')], cwd=HERE,
                           env=dict(os.environ, ASSEMBLY_JSON=os.path.join(W, 'assembly.json')), capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        A = json.load(open(os.path.join(W, 'assembly.json'))); assert A['bytes'] == os.path.getsize(OUT)
        U1, A1 = units_and_audio(OUT)
        assert U1 == U0, ('units differ', sorted(set(U0) ^ set(U1))[:5], [c for c in U0 if U1.get(c) != U0[c]][:5])
        assert A1 == A0, ('audio differs', [c for c in A0 if A1.get(c) != A0[c]][:5])
        print('units: all %d byte-identical to the capture; audio: all %d resync blocks identical' % (len(U0), len(A0)))
        rp = subprocess.run([os.path.join(REPO, 'src', 'frameserver', 'frameserver_replay'), OUT, os.path.join(W, 'log.csv'), '--offline', '--pool', '32'],
                            capture_output=True, text=True, env=dict(os.environ, FS_REGISTRATION_OFF='1', FS_HRETIME='0'))
        out = rp.stdout + rp.stderr
        mm = re.search(r'video obs (\d+) \| exact (\d+) short (\d+) hole (\d+) unframed (\d+)', out)
        assert mm, out[-1500:]
        r0 = subprocess.run([os.path.join(REPO, 'src', 'frameserver', 'frameserver_replay'), T, os.path.join(W, 'log0.csv'), '--offline', '--pool', '32'],
                            capture_output=True, text=True, env=dict(os.environ, FS_REGISTRATION_OFF='1', FS_HRETIME='0'))
        m0 = re.search(r'video obs (\d+) \| exact (\d+) short (\d+) hole (\d+) unframed (\d+)', r0.stdout + r0.stderr)
        print('replay: bridged %s | original %s' % (mm.group(0), m0.group(0)))
        assert int(mm.group(4)) == 0 and mm.group(2) == m0.group(2) and mm.group(3) == m0.group(3), 'the parser sees the bridge differently'
        # a loss record inside the recapture's stretch stops the bridge by name
        bad = os.path.join(W, 'donor_loss.tpc')        # the copy with a HostLoss record inserted mid-stretch
        mid = (dA['v'][0] + dB['v'][0]) // 2
        with open(D, 'rb') as f, open(bad, 'wb') as g:
            q = bridge.walk(D, 0, os.path.getsize(D)); done = False
            for pos, h, pay in q:
                if not done and pos >= mid:
                    g.write(bridge.H.pack(bridge.MAGIC, 1, 0x83, 0, 0, 0, 3, 46080)); done = True
                g.write(bridge.H.pack(*h)); g.write(pay)
        sh = 24                                   # the inserted record moves dB by its length
        bb = dict(b, donor=bad, dB=dict(dB, v=[dB['v'][0] + sh, dB['v'][1]], a=[dB['a'][0] + sh, dB['a'][1]]))
        try: bridge.measure(T, bb); raise AssertionError('a loss record inside the recapture\'s stretch was not refused')
        except ValueError as e: assert 'loss record' in str(e), e; print('refused: %s' % e)
        # a bridge planned one unit wrong: the moved counters do not run uA..uB-1 one each, refused by name
        try: bridge.measure(T, dict(b, units=[uA, uB])); raise AssertionError('a bridge planned one unit long was not refused')
        except ValueError as e: assert 'moved' in str(e), e; print('refused: %s' % e)
        # the first transfer number in the recapture's stretch: one past the seam transfer, or that transfer's own when the
        # seam packet began its transfer and is dropped whole
        sm = dict(v=[0, 0], a=[0, 0], v_seq=10, a_seq=20, v_pi=0, a_pi=5)
        assert bridge.seq_start(sm) == {'131': 10, '132': 21}, bridge.seq_start(sm)
        assert bridge.seq_start(dict(sm, v=[0, 7])) == {'131': 11, '132': 21}
        # a recapture whose packets fall differently: every packet split in two
        Dp = os.path.join(W, 'donor_split.tpc'); repacketize(D, Dp)
        dA2 = bridge.seam(Dp, uA + OFF, *win(Dp, uA)); dB2 = bridge.seam(Dp, uB + OFF, *win(Dp, uB))
        m2 = bridge.measure(T, dict(b, donor=Dp, dA=dA2, dB=dB2)); OUT2 = os.path.join(W, 'out2.tpc')
        os.remove(os.path.join(W, 'plan', 'plan.json')); json.dump({'bridge-0': [m2]}, open(os.path.join(W, 'plan', 'plan.json'), 'w'))
        r = subprocess.run([sys.executable, os.path.join(HERE, 'assemble.py'), T, OUT2, os.path.join(W, 'plan')], cwd=HERE,
                           env=dict(os.environ, ASSEMBLY_JSON=os.path.join(W, 'assembly2.json')), capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        U2, A2 = units_and_audio(OUT2)
        assert U2 == U0 and A2 == A0, 'a recapture split into other packets does not bridge to the capture exactly'
        r2 = subprocess.run([os.path.join(REPO, 'src', 'frameserver', 'frameserver_replay'), OUT2, os.path.join(W, 'log2.csv'), '--offline', '--pool', '32'],
                            capture_output=True, text=True, env=dict(os.environ, FS_REGISTRATION_OFF='1', FS_HRETIME='0'))
        m3 = re.search(r'video obs (\d+) \| exact (\d+) short (\d+) hole (\d+) unframed (\d+)', r2.stdout + r2.stderr)
        assert m3 and m3.group(0) == m0.group(0), ('replay of the split-packet bridge', m3 and m3.group(0), m0.group(0))
        print('split packets: %d bytes in place of %d; units, audio and replay identical to the capture' % (m2['bytes'], m2['file_to'] - m2['file_from']))
        print('BRIDGE TEST PASS')
    finally:
        shutil.rmtree(W)

if __name__ == '__main__':
    main()
