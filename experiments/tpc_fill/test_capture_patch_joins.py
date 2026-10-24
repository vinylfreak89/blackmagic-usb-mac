#!/usr/bin/env python3
"""Known-answer test of capture_patch.py on a capture split at a Shuttle disconnect.  usage: test_capture_patch_joins.py SOURCE.tpc SCRATCH_DIR

From SOURCE (a byte-complete capture of 30 s or more with sound) it makes, in SCRATCH_DIR, a target shaped like the 2026-10-23
disconnects: T.mov.raw.tpc is SOURCE up to a video transfer near the middle, then HostLoss records for what was not read;
T.mov.raw.part2.tpc starts on a later video transfer (about 0.25 s lost) with a SESSION note of its own, the Shuttle's counter
restarted near 15 and transfer numbers restarted at 6, as a reset leaves them. Each part's live sidecar comes from its own
replay, and a stand-in OBS log names both parts' sessions, so the clock check runs as on a real capture. The donor is SOURCE
with every counter raised by 1000. `run --join DONOR` must verify; every unit of the patched capture must equal SOURCE's unit
of the same counter, every audio sample must equal SOURCE's; `swap` must leave one capture and one sidecar, part 2 gone.
With SCRATCH_DIR on the JuiceFS share, the render must have read the assembler's stream and the write proof must be complete."""
import hashlib, json, os, shutil, struct, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from test_capture_patch import records, raise_counters, units, H, MAGIC, SYNC
import joined

def split(src, p1, p2, at_frac=0.5, lose_video_pkts=2000):
    b = open(src, 'rb').read(); recs = list(records(b)); isv = lambda r: r[0] == 0 and r[1] == 0x83
    k0 = int(len(recs) * at_frac)
    while not (isv(recs[k0][2]) and recs[k0][2][2] == 0): k0 += 1
    k1 = k0; lost = {0x83: 0, 0x84: 0}
    while not (lost[0x83] >= lose_video_pkts and isv(recs[k1][2]) and recs[k1][2][2] == 0):
        r = recs[k1][2]
        if r[0] == 0: lost[r[1]] += 1
        k1 += 1
    last = {}
    for p, n, r in recs[:k0]:
        if r[0] in (0, 1, 2): last[r[1]] = r[3]
    out1 = bytearray(b[:recs[k0][0]])
    for e in (0x83, 0x84): out1 += H.pack(MAGIC, 1, e, 65533, last[e] + 1, 0, lost[e], 0)
    open(p1, 'wb').write(out1)
    # part 2: the rest, renumbered as a reset leaves it, with the leading partial audio transfer re-indexed from packet 0
    part = bytearray(b[recs[k1][0]:]); base = recs[k1][0]; seq0 = {}; first_seq = {}; npk = {}
    for p, n, r in recs[k1:]:
        t, ep, pi, seq = r[0], r[1], r[2], r[3]
        if t in (0, 1, 2):
            first_seq.setdefault(ep, seq); new = seq - first_seq[ep] + 6
            if t == 0:
                if seq0.get(ep) != seq: seq0[ep] = seq; npk[ep] = 0
                struct.pack_into('<H', part, p - base + 6, npk[ep]); npk[ep] += 1
            struct.pack_into('<I', part, p - base + 8, new)
    # counters, by an independent method: the whole video stream searched at once
    import bisect
    vpay = [(p - base + 24, r[6]) for p, n, r in recs[k1:] if r[0] == 0 and r[1] == 0x83]
    vs = b''.join(bytes(part[a:a + n]) for a, n in vpay); starts = []; acc = 0
    for a, n in vpay: starts.append(acc); acc += n
    fpos = lambda i: vpay[bisect.bisect_right(starts, i) - 1][0] + i - starts[bisect.bisect_right(starts, i) - 1]
    heads = []; j = vs.find(b'\x00\x00\xff\xff')
    while j >= 0:
        if j + 48 <= len(vs) and vs[j + 7] == 0xe8 and vs[j + 8:j + 48] == bytes(40): heads.append(j)
        j = vs.find(b'\x00\x00\xff\xff', j + 1)
    K = ((vs[heads[0] + 4] | vs[heads[0] + 5] << 8) - 15) % 65536
    for h in heads:
        c = ((vs[h + 4] | vs[h + 5] << 8) - K) % 65536; part[fpos(h + 4)] = c & 0xff; part[fpos(h + 5)] = c >> 8
    for p, n, r in recs[k1:]:
        if r[0] == 0 and r[1] == 0x84:
            d0 = p - base + 24
            for i in range(d0, d0 + r[6], 24):
                if bytes(part[i:i + 20]) == SYNC:
                    c = ((part[i + 20] | part[i + 21] << 8) - K) % 65536; part[i + 20] = c & 0xff; part[i + 21] = c >> 8
    # part 2's TICKs restart at its own session start, as a reset makes them: its session begins where part 1's slots end
    tick, nv = None, 0
    for p, n, r in recs[:k1]:
        if r[0] == 4: tick, nv = r[4], 0
        elif r[0] == 0 and r[1] == 0x83: nv += 1
    t_cut = tick + nv * 0.125                                 # ms of the original session at part 2's first record
    for p, n, r in recs[k1:]:
        if r[0] == 4: struct.pack_into('<I', part, p - base + 12, int(round(r[4] - t_cut)))
    open(p2, 'wb').write(joined.note_record('shuttle-source tee v1 usb=iousbhost input=svideo setup=on mode=0x3c000000 part=2 recording=T.mov') + part)
    return lost, K, t_cut / 1000          # t_cut: seconds into the original session where part 2 begins (the disconnect)

def wait_free(paths, cap_s=600):
    """until no program, and on the share no JuiceMount write handle (pooled until 2 min idle), holds any of paths"""
    from capture_patch import busy
    import time
    t0 = time.time()
    while busy(paths):
        assert time.time() - t0 < cap_s, ('still in use after %d s' % cap_s, busy(paths))
        time.sleep(10)

def stand_in_log(logs, T, P2, t_cut):
    """an OBS log with a session per part, as a reconnect makes them: the disconnect, and part 2's session start, at t_cut s
    into part 1's session (the tick clock the join is checked on)"""
    os.makedirs(logs); at = lambda t: '10:%02d:%06.3f' % (t // 60, t % 60)
    with open(os.path.join(logs, '2026-10-23 10-00-00.txt'), 'w') as f:
        f.write('%s: [shuttle-source] started (device), registration OFF (nominal placement), H-retiming off\n' % at(0))
        f.write('%s: [shuttle-source] raw .tpc started: %s — local spill x\n' % (at(0.5), T))
        f.write('%s: [shuttle-source] the Shuttle disconnected (USB connection lost): picture blanked; reconnecting when it comes back\n' % at(t_cut))
        f.write('%s: [shuttle-source] started (device), registration OFF (nominal placement), H-retiming off\n' % at(t_cut))
        f.write('%s: [shuttle-source] raw .tpc started: %s — local spill x\n' % (at(t_cut + 0.1), P2))

def main():
    src, S = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if os.path.exists(S): sys.exit('remove %s first' % S)
    os.makedirs(S)
    # work folders hold FIFOs, which the share cannot: local, as the dashboard keeps them
    L = tempfile.mkdtemp(prefix='cpj-') if os.path.realpath(S).startswith('/Volumes/zpool/') else S
    T, P2 = os.path.join(S, 'T.mov.raw.tpc'), os.path.join(S, 'T.mov.raw.part2.tpc')
    lost, K, t_cut = split(src, T, P2); print('split: packets lost %s; part 2 counters moved by %d' % ({hex(k): v for k, v in lost.items()}, -K))
    for tp, csv in ((T, 'T.mov.registration.csv'), (P2, 'T.mov.registration.part2.csv')):
        r = subprocess.run(['/bin/bash', os.path.join(REPO, 'scripts/plain_render/plain_render.sh'), tp, tp + '.check.mov', os.path.join(L, 'tr')],
                           env=dict(os.environ, PLAIN_RENDER_DECISION_LOG=os.path.join(S, csv)), capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
        os.remove(tp + '.check.mov'); shutil.rmtree(os.path.join(L, 'tr'))
    logs = os.path.join(L, 'obs-logs'); stand_in_log(logs, T, P2, t_cut)
    good, gL, gR = units(src)
    DA = os.path.join(S, 'donorA.tpc'); raise_counters(src, DA, 1000)
    W = os.path.join(L, 'work'); env = dict(os.environ, CAPTURE_PATCH_OBS_LOGS=logs)
    wait_free([T, P2, DA])                                   # the patch tool refuses a capture still being written
    r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'run', T, '--work', W, '--join', DA], capture_output=True, text=True, env=env)
    print(r.stdout[-4000:]); assert r.returncode == 0, r.stderr[-3000:]
    res = json.load(open(os.path.join(W, 'result.json')))
    # a second run with the same inputs reuses every finished step instead of redoing it (here it then stops at the read-back,
    # whose outputs exist): the stage keys survive their JSON round trip
    r2 = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'run', T, '--work', W, '--join', DA], capture_output=True, text=True, env=env)
    for st in ('join-1', 'first-line', 'plan', 'assemble'):
        assert '%s: done in an earlier run, reused' % st in r2.stdout, (st, r2.stdout[-1500:])
    if os.path.realpath(S).startswith('/Volumes/zpool/'):       # on the share: one pass, the render read the assembler's stream
        A = json.load(open(os.path.join(W, 'assemble.json')))['result']; wp = A.get('write_proof') or {}
        assert A.get('rendered') and wp.get('complete') and not wp.get('downloaded_blocks'), ('not the one-pass path, or no proof', A)
        assert not os.path.exists(os.path.join(W, 'checked_read.json')), 'the patched capture was read back'
        print('one pass: rendered from the assembler\'s stream; write proof %d objects, %d downloaded' % (wp['objects'], wp['downloaded_blocks']))
    j = res['joins']['parts'][1]; print('join: counter delta %d, transfers %s' % (j['counter_delta'], j['seq_delta']))
    assert j['counter_delta'] == K, (j['counter_delta'], K)
    got, pL, pR = units(res['patched']['tpc'])
    filled = {c % 65536 for a, b in res['spans'] for c in range(a, b + 1)}
    assert filled, 'nothing was filled'
    bad = [c for c in good if got.get(c) != good[c]]
    assert not bad, ('units differ from the source', bad[:8], len(bad))
    assert len(pL) == len(gL) and (pL == gL).all() and (pR == gR).all(), 'audio differs from the source (%d vs %d samples)' % (len(pL), len(gL))
    print('joined and patched: all %d units and %d audio samples equal the source; filled %d units' % (len(good), len(pL), len(filled)))
    wait_free([res['patched']['tpc'], res['patched']['mov']])
    r = subprocess.run([sys.executable, os.path.join(HERE, 'capture_patch.py'), 'swap', W], capture_output=True, text=True)
    print(r.stdout[-1500:]); assert r.returncode == 0, r.stderr[-2000:]
    assert not os.path.exists(P2) and not os.path.exists(os.path.join(S, 'T.mov.registration.part2.csv')), 'swap left part 2'
    assert os.path.getsize(T) == res['bytes'] and os.path.exists(os.path.join(S, 'T.mov')), 'swap: names'
    shutil.rmtree(S)
    if L != S: shutil.rmtree(L)
    print('capture_patch joins: all tests passed')

if __name__ == '__main__': main()
