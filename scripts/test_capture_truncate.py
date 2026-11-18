#!/usr/bin/env python3
"""Tests capture_truncate.py on a synthetic capture, through the real replay. No captured media is required.

The capture: 400 unit periods, audio and video packets interleaved as the device sends them (each endpoint's packets placed
by their share of their own stream). Periods 0-199 are picture units 0-199; periods 200-211 are no-signal (0x0800) units with
their own numbering (900-911), the audio running on; periods 212-399 are picture units 212-399. Each period carries one audio
resync and 1602,1601,1602,1601,1602... samples. Its 'live' sidecar is its own replay, as plain_render's.

Checked: the unit kept last is the last picture unit whose audio time (samples from the first published unit, counted from
the generator, not from the sidecar) is at or before TIME; the shortened capture is a prefix of the original; its replay
is the new sidecar byte for byte; a dry run, a TIME past the last picture unit, a file held open and a split capture
change nothing; a TIME inside the no-signal stretch keeps everything to the last picture unit before it. A live sidecar
written with H-retiming on, or registration on, is cut so that a replay of the cut capture with those settings is the new
sidecar byte for byte; one with reversed pairing is cut that way or refused, never given a row of another setting. A
failure between the two cuts, or after them, is reported as FAILED AFTER CUTTING with the files' state and dates put back,
and running the same TIME again finishes the job exactly as an uninterrupted cut.
    test_capture_truncate.py [path/to/frameserver_replay]   (default: src/frameserver/frameserver_replay)"""
import hashlib, importlib.util, os, shutil, subprocess, sys, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixture', root / 'src/unit_parser/tests/gen_unit_parser_capture.py')
fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)
binary = Path(sys.argv[1] if len(sys.argv) > 1 else root / 'src/frameserver/frameserver_replay').resolve()
TOOL = root / 'scripts/capture_truncate.py'
ENV = {'FS_REGISTRATION_OFF': '1', 'FS_HRETIME': '0', 'FS_SHOW_PARTIAL': '1', 'FS_REPAIR': '1', 'PATH': '/usr/bin:/bin'}
N, NS0, NS1 = 400, 200, 212
SAMPLES = [1602 if p % 5 in (0, 2, 4) else 1601 for p in range(N)]
START = [sum(SAMPLES[:p]) for p in range(N + 1)]
RASTER = bytes((128, 16)) * ((fx.UNIT_BYTES - fx.HEADER_BYTES) // 2)

def header(counter, fmt):
    return b'\x00\x00\xff\xff' + counter.to_bytes(2, 'little') + fmt.to_bytes(2, 'little') + bytes(40)

def write_capture(path):
    video = [header(p, 0xe801) if not NS0 <= p < NS1 else header(900 + p - NS0, 0x0800) for p in range(N)]
    vstream = b''.join(h + RASTER for h in video) + header(N, 0xe801)[:8]
    astream = b''.join(fx.resync(p) + b''.join(fx.pcm(START[p] + i) for i in range(SAMPLES[p])) for p in range(N))
    recs = []                                         # (time in periods, endpoint, payload)
    for ep, stream, size, per in ((fx.VIDEO, vstream, 15360, fx.UNIT_BYTES), (fx.AUDIO, astream, 2048, len(astream) / N)):
        for o in range(0, len(stream), size): recs.append(((o + size) / per, ep, stream[o:o + size]))
    recs.sort(key=lambda r: (r[0], r[1]))
    seq = {fx.VIDEO: 0, fx.AUDIO: 0}
    with open(path, 'wb') as out:
        for _, ep, payload in recs:
            out.write(fx.record(fx.DATA, ep, 0, seq[ep], 0, len(payload) if ep == fx.AUDIO else 15360, payload)); seq[ep] += 1

def replay(cap, dlog, env=ENV, extra=()):
    r = subprocess.run([str(binary), str(cap), str(dlog), '--offline', '--pool', '32', *extra], env=env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, (r.stdout[-1500:], r.stderr[-1500:])

def rows(csvp):
    import csv
    return list(csv.DictReader(l for l in open(csvp, newline='') if not l.startswith('#')))

def truncate(tpc, *args, fail=None):
    env = dict(os.environ, **({'CAPTURE_TRUNCATE_TEST_FAIL': fail} if fail else {}))
    return subprocess.run([sys.executable, str(TOOL), str(tpc)] + list(args), capture_output=True, text=True, timeout=1800, env=env)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

with tempfile.TemporaryDirectory(prefix='truncate-test-', dir='/private/tmp') as d:
    d = Path(d); orig = d / 'orig.tpc'; ocsv = d / 'orig.csv'
    write_capture(orig); replay(orig, ocsv)
    R = rows(ocsv); pub = [r for r in R if r['published'] == '1']
    u0 = int(pub[0]['counter_extended'])                  # the first published unit: time zero
    def fresh(name):
        t = d / (name + '.mov.raw.tpc'); c = d / (name + '.mov.registration.csv')
        shutil.copyfile(orig, t); shutil.copyfile(ocsv, c); return t, c
    def expect(T):
        """the last picture unit whose audio time is at or before T, from the generator's own sample counts"""
        lim = START[u0] + T * 48000
        return max(p for p in range(N) if not NS0 <= p < NS1 and START[p] <= lim and any(int(r['counter_extended'] or -1) == p for r in pub))

    # a cut at 5.000 s
    t, c = fresh('a'); s0, c0 = sha(t), sha(c)
    r = truncate(t, '--at', '0:05.000', '--dry-run')
    assert r.returncode == 0 and 'dry run, nothing changed' in r.stdout, r.stdout + r.stderr
    assert sha(t) == s0 and sha(c) == c0, 'a dry run changed a file'
    r = truncate(t, '--at', '0:05.000')
    assert r.returncode == 0 and 'TRUNCATED' in r.stdout, r.stdout + r.stderr
    got = [x for x in rows(c) if x['published'] == '1'][-1]
    assert int(got['counter_extended']) == expect(5), (got['counter_extended'], expect(5))
    assert hashlib.sha256(orig.read_bytes()[:t.stat().st_size]).hexdigest() == sha(t), 'the shortened capture is not a prefix of the original'
    replay(t, d / 'a.re.csv')
    assert (d / 'a.re.csv').read_bytes() == c.read_bytes(), 'the shortened capture\'s replay is not the new sidecar'
    assert rows(c)[-1]['drop_reason'] == 'Unframed', rows(c)[-1]

    # a cut inside the no-signal stretch keeps everything to the last picture unit before it
    T = (START[NS0 + 5] - START[u0]) / 48000
    t, c = fresh('b')
    r = truncate(t, '--at', '%.4f' % T)
    assert r.returncode == 0, r.stdout + r.stderr
    got = [x for x in rows(c) if x['published'] == '1'][-1]
    assert int(got['counter_extended']) == NS0 - 1 == expect(T), (got['counter_extended'], expect(T))
    replay(t, d / 'b.re.csv')
    assert (d / 'b.re.csv').read_bytes() == c.read_bytes(), 'the shortened capture\'s replay is not the new sidecar (no-signal)'

    # a cut after the stretch: picture counters jumped there, the audio clock did not
    T = (START[300] - START[u0]) / 48000 + 0.001
    t, c = fresh('e')
    r = truncate(t, '--at', '%.4f' % T)
    assert r.returncode == 0, r.stdout + r.stderr
    got = [x for x in rows(c) if x['published'] == '1'][-1]
    assert int(got['counter_extended']) == 300 == expect(T), got['counter_extended']
    replay(t, d / 'e.re.csv')
    assert (d / 'e.re.csv').read_bytes() == c.read_bytes(), 'the shortened capture\'s replay is not the new sidecar (after the stretch)'

    # past the last picture unit: only what follows that unit's confirmation goes, no picture
    t, c = fresh('g'); last = (START[N - 1] - START[u0]) / 48000
    r = truncate(t, '--at', '%.3f' % (last + 1))
    assert r.returncode == 0 and '0:00:00.000 of timed picture removed' in r.stdout and [x for x in rows(c) if x['published'] == '1'][-1]['counter_extended'] == str(N - 1), r.stdout
    r = truncate(t, '--at', '%.3f' % (last + 1))
    assert r.returncode == 0 and 'already ends' in r.stdout, r.stdout
    t, c = fresh('h'); s1, c1 = sha(t), sha(c)
    r = truncate(t, '--at', '1:00:00')                     # a typo past the end: refused, not a trim
    assert r.returncode == 2 and 'past the recording\'s end' in r.stdout and sha(t) == s1 and sha(c) == c1, r.stdout
    # refusals change nothing
    t, c = fresh('c'); s0, c0 = sha(t), sha(c)
    with open(c, 'rb'):
        hold = subprocess.Popen(['/bin/sleep', '60'], stdin=open(c, 'rb'))
        try: r = truncate(t, '--at', '5')
        finally: hold.kill(); hold.wait()
    assert r.returncode == 2 and 'in use' in r.stdout, r.stdout
    (d / 'c.mov.raw.part2.tpc').write_bytes(b'')
    r = truncate(t, '--at', '5')
    assert r.returncode == 2 and 'split into parts' in r.stdout, r.stdout
    assert sha(t) == s0 and sha(c) == c0, 'a refusal changed a file'
    os.remove(d / 'c.mov.raw.part2.tpc')
    r = truncate(t, '--at', '5:xx')
    assert r.returncode == 2 and 'TIME is' in r.stdout, r.stdout
    r = truncate(t, '--at', '1.5')
    assert r.returncode == 2 and 'too near the start' in r.stdout and 'reading' not in r.stdout, r.stdout
    os.chmod(c, 0o444)
    r = truncate(t, '--at', '5')
    assert r.returncode == 2 and 'not writable' in r.stdout, r.stdout
    os.chmod(c, 0o644)
    assert sha(t) == s0 and sha(c) == c0, 'a refusal changed a file'

    # live sidecars written with other settings: cut to what a replay with those settings writes, or refused untouched
    for name, env, extra in (('hretime', dict(ENV, FS_HRETIME='1'), ()),
                             ('registration', dict({k: v for k, v in ENV.items() if k != 'FS_REGISTRATION_OFF'}, FS_REPAIR='0'), ()),
                             ('reversed', ENV, ('--pair-next',))):
        t = d / (name + '.mov.raw.tpc'); c = d / (name + '.mov.registration.csv')
        shutil.copyfile(orig, t); replay(t, c, env, extra); s0, c0 = sha(t), sha(c)
        r = truncate(t, '--at', '0:05.000')
        if r.returncode == 2 and 'other settings' in r.stdout:
            assert sha(t) == s0 and sha(c) == c0, name + ': a refusal changed a file'
            print('  %s: refused (%s)' % (name, r.stdout.strip().splitlines()[-1].split('REFUSED (nothing changed): ')[-1])); continue
        assert r.returncode == 0, (name, r.stdout + r.stderr)
        replay(t, d / (name + '.re.csv'), env, extra)
        assert (d / (name + '.re.csv')).read_bytes() == c.read_bytes(), name + ': the cut capture\'s replay with its settings is not the new sidecar'
        print('  %s: cut, its replay with those settings is the new sidecar' % name)

    # a failure between the cuts, or after both: named, dates back, and the same TIME again finishes the job
    ref, refc = d / 'a.mov.raw.tpc', d / 'a.mov.registration.csv'          # the uninterrupted cut at 5.000 s above
    for where, state in (('between', 'the capture is cut, the sidecar is not'), ('after', 'both files are cut'),
                         ('stop-between', 'the capture is cut, the sidecar is not'), ('stop-after', 'both files are cut'),
                         ('badbytes', 'both files are cut')):
        t, c = fresh('f' + where); old = 1_000_000_000
        for x in (t, c): os.utime(x, (old, old))
        r = truncate(t, '--at', '0:05.000', fail=where)
        assert r.returncode == 1 and 'FAILED AFTER CUTTING' in r.stdout and state in r.stdout and 'nothing changed' not in r.stdout, (where, r.stdout)
        assert ('stopped' in r.stdout) == where.startswith('stop'), (where, r.stdout)
        assert ('Do not run it again' in r.stdout) == (where == 'badbytes'), (where, r.stdout)
        assert all(int(x.stat().st_mtime) == old for x in (t, c)), 'dates not put back after a failure'
        r = truncate(t, '--at', '0:05.000')
        assert r.returncode == 0 and ('TRUNCATED' in r.stdout or 'CHECKED, already ends there' in r.stdout), (where, r.stdout)
        assert sha(t) == sha(ref) and sha(c) == sha(refc), where + ': finishing after a failure differs from an uninterrupted cut'
        assert all(int(x.stat().st_mtime) == old for x in (t, c)), 'dates not the originals after finishing'
print('capture_truncate: all tests passed')
