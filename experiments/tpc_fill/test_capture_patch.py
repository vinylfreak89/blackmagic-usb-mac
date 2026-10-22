#!/usr/bin/env python3
"""Known-answer test of capture_patch.py on a real capture.  usage: test_capture_patch.py SOURCE.tpc SCRATCH_DIR

From SOURCE (any byte-complete capture of 30 s or more with sound) it makes, in SCRATCH_DIR:
  target   SOURCE with a host loss punched in at about 15 s, shaped like the 2026-10-19 one: about 0.13 s of packets on both
           endpoints never read, the transfers either side of the hole cut short, sequence numbers continuous, and a HostLoss
           record per endpoint; plus its sidecar from a replay (registration and H-retiming off, as plain_render runs)
  donor A  SOURCE with every device counter raised by 1000 (pairing same, FILL_OFF 1000)
  donor B  SOURCE re-paired one field later by repair.py (pairing shifted, FILL_OFF 0)
and checks, for each donor: `run` verifies; every patched unit and every audio sample of the hole equals SOURCE's; `swap`
puts the result under the target's names with the original dates. Nothing outside SCRATCH_DIR is written."""
import hashlib, json, os, shutil, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from tpc import walk
H = struct.Struct('<IBBHIIII'); MAGIC = 0x31504143; UNIT = 756048; SYNC = b'DeckLinkAudioResyncT'

def records(b):
    p = 0
    while p + 24 <= len(b):
        m, t, ep, pi, seq, st, req, al = H.unpack_from(b, p)
        assert m == MAGIC, p
        n = 24 + (al if t in (0, 3) else 0); yield p, n, (t, ep, pi, seq, st, req, al); p += n

def punch(src, dst, at_frac=0.5, lose_video_pkts=736):
    """drop every record from a video transfer's 70th packet up to a later video transfer's 78th, both endpoints"""
    b = open(src, 'rb').read(); recs = list(records(b))
    isv = lambda r: r[0] == 0 and r[1] == 0x83
    k0 = int(len(recs) * at_frac)
    while not (isv(recs[k0][2]) and recs[k0][2][2] == 69): k0 += 1
    k1 = k0; lost_v = 0
    while not (lost_v >= lose_video_pkts and isv(recs[k1][2]) and recs[k1][2][2] == 77):
        lost_v += isv(recs[k1][2]); k1 += 1
    # what is left keeps its order; each endpoint's transfers are renumbered consecutively in order of appearance and
    # each transfer's packets re-indexed from 0, so the two cut transfers stay whole-numbered and no sequence number is missing
    out = bytearray(); newseq = {}; last = {}; npk = {}; lost = {0x83: 0, 0x84: 0}
    for i, (p, n, r) in enumerate(recs):
        t, ep, pi, seq, st, req, al = r
        if i == k1:
            for e in (0x83, 0x84): out += H.pack(MAGIC, 1, e, 65533, last[e][1], 0, lost[e], 0)
        if t == 0 and k0 <= i < k1: lost[ep] += 1; continue
        rec = bytearray(b[p:p + n])
        if t == 0:
            if ep not in last or last[ep][0] != seq: last[ep] = (seq, last[ep][1] + 1 if ep in last else seq); npk[ep] = 0
            struct.pack_into('<HI', rec, 6, npk[ep], last[ep][1]); npk[ep] += 1
        out += rec
    open(dst, 'wb').write(out); return lost

def raise_counters(src, dst, by):
    """every unit marker's counter and every resync's counter + by, in place in the packet payloads"""
    b = bytearray(open(src, 'rb').read())
    for ep, pat, off in ((0x83, b'\x00\x00\xff\xff', 4), (0x84, SYNC, len(SYNC))):
        pos = []; stream = bytearray()                        # stream offset -> file offset, per payload byte run
        for p, n, r in records(b):
            if r[0] == 0 and r[1] == ep: pos.append((len(stream), p + 24, r[6])); stream += b[p + 24:p + 24 + r[6]]
        import bisect
        starts = [s for s, _, _ in pos]
        def put(so, val):
            k = bisect.bisect_right(starts, so) - 1; s, fo, ln = pos[k]; b[fo + so - s] = val
        j = stream.find(pat)
        while j >= 0:
            ok = ep == 0x84 or stream[j + 6:j + 8] == b'\x01\xe8'
            if ok:
                c = (stream[j + off] | stream[j + off + 1] << 8) + by
                put(j + off, c & 255); put(j + off + 1, (c >> 8) & 255)
            j = stream.find(pat, j + 4)
    open(dst, 'wb').write(b)

def units(path, skip_row7=False):
    """counter -> sha256 of the unit's payload, and the audio samples, from a capture. skip_row7: storage row 7 left out, which
    a shifted-pairing fill takes from the nearest intact target unit (the re-paired donor has no source for it; synth.py)"""
    sys.path.insert(0, HERE); from region import load
    R = load(path, 0, os.path.getsize(path))
    def h(o):
        b = bytearray(R.v[o:o + UNIT])
        if skip_row7: b[48 + 7 * 1440:48 + 8 * 1440] = bytes(1440)
        return hashlib.sha256(b).hexdigest()
    u = {c: h(o) for o, c, fm, ok in R.marks if ok and fm == 0xe801}
    Lc, Rc = R.pcm(); return u, Lc, Rc

def main():
    src, S = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(S): sys.exit('remove %s first' % S)
    os.makedirs(S)
    T = os.path.join(S, 'T.mov.raw.tpc'); lost = punch(src, T); print('punched: packets lost %s' % {hex(k): v for k, v in lost.items()})
    r = subprocess.run(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), T, os.path.join(S, 'T.mov'), os.path.join(S, 'tr')],
                       env=dict(os.environ, PLAIN_RENDER_DECISION_LOG=os.path.join(S, 'T.mov.registration.csv')), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    print('target sidecar made; replay:', [l for l in r.stdout.splitlines() if 'hole' in l][:2])
    shutil.rmtree(os.path.join(S, 'tr'))
    t0 = os.stat(T); t0c = os.stat(os.path.join(S, 'T.mov.registration.csv'))
    good, gL, gR = units(src); good7 = units(src, True)[0]
    DA = os.path.join(S, 'donorA.tpc'); raise_counters(src, DA, 1000)
    DB = os.path.join(S, 'donorB.tpc')
    r = subprocess.run([sys.executable, 'repair.py', src, DB, '--local'], cwd=HERE, capture_output=True, text=True); assert r.returncode == 0, r.stderr[-2000:]
    keep = {n: open(os.path.join(S, n), 'rb').read() for n in ('T.mov.raw.tpc', 'T.mov.registration.csv')}
    for label, D, want in (('A', DA, ('same', 1000)), ('B', DB, ('shifted', 0))):
        for n, data in keep.items(): open(os.path.join(S, n), 'wb').write(data)
        for n in ('T.mov.raw.tpc', 'T.mov.registration.csv'): os.utime(os.path.join(S, n), ns=(t0.st_atime_ns, t0.st_mtime_ns))
        for n in ('T patched.mov.raw.tpc', 'T patched.mov'):
            if os.path.exists(os.path.join(S, n)): os.remove(os.path.join(S, n))
        W = os.path.join(S, 'work' + label)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'run', T, D, '--at', '0:15', '--work', W], capture_output=True, text=True)
        print(r.stdout[-3000:]); assert r.returncode == 0, r.stderr[-3000:]
        res = json.load(open(os.path.join(W, 'result.json')))
        assert (res['pairing'], res['fill_off']) == want, (res['pairing'], res['fill_off'], want)
        shifted = res['pairing'] == 'shifted'
        got, pL, pR = units(res['patched']['tpc'], shifted); ref = good7 if shifted else good
        filled = [c for a, b in res['spans'] for c in range(a, b + 1)]
        bad = [c for c in filled if got.get(c % 65536) != ref.get(c % 65536)]
        assert all(got.get(c) == ref.get(c) for c in ref if c not in {x % 65536 for x in filled}), 'units outside the patch changed'

        assert filled and not bad, ('patched units differ from the source', bad[:5])
        n = min(len(pL), len(gL)); assert len(pL) == len(gL) and (pL[:n] == gL[:n]).all() and (pR[:n] == gR[:n]).all(), 'patched audio differs from the source'
        print('donor %s: pairing %s FILL_OFF %d; units %s%s and all %d audio samples equal the source, every other unit unchanged' % (
            label, res['pairing'], res['fill_off'], filled, ' (but for storage row 7)' if shifted else '', len(pL)))
        r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'swap', W], capture_output=True, text=True)
        print(r.stdout[-1500:]); assert r.returncode == 0, r.stderr[-2000:]
        s1 = os.stat(T); assert s1.st_mtime_ns == t0.st_mtime_ns and s1.st_size == res['bytes'], 'swap: capture size/date'
        assert hashlib.sha256(open(os.path.join(S, 'T.mov.registration.csv'), 'rb').read()).hexdigest() == res['sidecar_sha256']
        assert not os.path.exists(res['patched']['tpc']) and os.path.exists(os.path.join(S, 'T.mov')), 'swap: names'
        r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'swap', W], capture_output=True, text=True)
        assert r.returncode != 0 and 'swapped' in r.stdout, 'a second swap must be refused'
    shutil.rmtree(S); print('capture_patch: all tests passed')

if __name__ == '__main__': main()
