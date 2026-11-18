#!/usr/bin/env python3
"""Known-answer test of tpc_play.  usage: test_tpc_play.py TPC_PLAY FRAMESERVER_REPLAY SOURCE.tpc

1. probe: the span is a whole number of units and its first counter is the file's.
2. play from the start, read as fast as possible: every frame and sample equals frameserver_replay's dump with the same
   settings (the plain render's), in order; the sound may lack only the leading blocks before the first resync (not on
   the timeline yet, as in OBS); frame times never go back; frame units count up from 0.
3. the same, with the reader pausing 3 s twice (it stops reading, as a paused player does): the same frames and sound,
   nothing dropped (the frameserver waits).
4. a seek: play from unit 400 of the span: the first frame lands within 15 units of it (the start is a byte estimate,
   as for the OBS seek bar: a player asks for a little earlier and drops frames before its target), its unit index
   agrees with its counter, and every frame from there equals the frame of that counter played from the start.
5. the reader closing early ends the helper promptly (exit 0, within 10 s)."""
import json, os, struct, subprocess, sys, tempfile, time
import numpy as np

W, H = 720, 480; VB = W * H * 2

def records(stream, pause_at=()):
    """(type, header fields, payload) from a tpc_play stdout, pausing `pause_at` seconds after given frame counts"""
    frames = 0; pauses = list(pause_at)
    while True:
        h = stream.read(8)
        if len(h) < 8: return
        t, n = struct.unpack('<II', h); p = stream.read(n); assert len(p) == n, 'short record'
        if t == 1:
            frames += 1
            if pauses and frames == pauses[0][0]: time.sleep(pauses.pop(0)[1])
        yield t, p

def play(tp, src, extra=(), pause_at=()):
    pr = subprocess.Popen([tp, 'play', src] + list(extra), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    vids, auds, end = [], [], None
    for t, p in records(pr.stdout, pause_at):
        if t == 1:
            ticks, cext, unit = struct.unpack_from('<QQQ', p); tr, d1, d2, est = struct.unpack_from('<Bbbb', p, 24)
            vids.append(dict(ticks=ticks, counter=cext, unit=unit, transport=tr, est=est, px=p[32:]))
        elif t == 2:
            ticks, nf, fl = struct.unpack_from('<QII', p); auds.append(np.frombuffer(p[16:], '<f4').reshape(-1, 2))
        elif t == 3: end = json.loads(p)
    err = pr.stderr.read().decode(); rc = pr.wait()
    assert rc == 0, (rc, err[-2000:])
    return vids, (np.concatenate(auds) if auds else np.zeros((0, 2), '<f4')), end

def main():
    tp, rp, src = (os.path.abspath(a) for a in sys.argv[1:4])
    span = json.loads(subprocess.run([tp, 'probe', src], capture_output=True, text=True, check=True).stdout)
    assert span['units'] > 400 and span['first16'] == span['first_counter'], span
    print('probe:', span)
    d = tempfile.mkdtemp(prefix='tpc_play_test_')
    try:
        env = dict(os.environ, FS_REGISTRATION_OFF='1', FS_HRETIME='0', FS_SHOW_PARTIAL='1', FS_REPAIR='1')
        r = subprocess.run([rp, src, '--offline', '--pool', '32', '--dump-uyvy', d + '/v.uyvy', '--dump-pcm', d + '/a.s24'],
                           env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        dv = np.fromfile(d + '/v.uyvy', np.uint8).reshape(-1, VB)
        a = np.fromfile(d + '/a.s24', np.uint8).reshape(-1, 6)
        s24 = lambda b: ((b[:, 0].astype(np.int32) | b[:, 1].astype(np.int32) << 8 | b[:, 2].astype(np.int32) << 16) << 8) >> 8
        da = np.stack([s24(a[:, 0:3]), s24(a[:, 3:6])], 1)
        span_args = ['--units', str(span['units']), '--first16', str(span['first16'])]

        def check_whole(label, vids, au, end):
            assert len(vids) == len(dv), (label, 'frames', len(vids), len(dv))
            bad = [i for i, v in enumerate(vids) if v['px'] != dv[i].tobytes()]
            assert not bad, (label, 'frames differ from the replay dump', bad[:5])
            got = np.round(au.astype(np.float64) * (1 << 23)).astype(np.int64)
            k = len(da) - len(got)
            assert 0 <= k < 3300, (label, 'sound length', len(got), len(da))
            assert np.array_equal(got, da[k:]), (label, 'sound differs from the replay dump')
            ts = [v['ticks'] for v in vids]
            assert all(b > a for a, b in zip(ts, ts[1:])), (label, 'frame times go back')
            us = [v['unit'] for v in vids if v['transport'] != 1]
            assert us[0] <= 2 and all(b >= a for a, b in zip(us, us[1:])), (label, 'unit indexes', us[:5])
            assert end and end['reason'] == 'eof' and end['audio_dropped_frames'] == 0, (label, end)
            print('%s: %d frames and %d samples equal the replay dump (%d leading samples before the first resync), %s' % (
                label, len(vids), len(got), k, end))

        check_whole('whole', *play(tp, src, span_args))
        t0 = time.time(); res = play(tp, src, span_args, pause_at=[(100, 3), (500, 3)])
        assert time.time() - t0 >= 6
        check_whole('paused', *res)

        vids, au, end = play(tp, src, span_args + ['--start-unit', '400'])
        first = next(v for v in vids if v['transport'] != 1)
        assert abs(first['unit'] - 400) <= 15, ('seek landed at', first['unit'])
        assert (first['counter'] - span['first16']) % 65536 == first['unit'] % 65536, first
        whole = play(tp, src, span_args)[0]; by_c = {v['counter'] % 65536: v['px'] for v in whole}
        bad = [v['counter'] for v in vids if v['px'] != by_c.get(v['counter'] % 65536)]
        assert not bad, ('seek: frames differ from the same counters played from the start', bad[:5])
        print('seek: first frame unit %d (asked 400), %d frames equal the same counters played from the start' % (first['unit'], len(vids)))

        pr = subprocess.Popen([tp, 'play', src] + span_args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        pr.stdout.read(8 + 32 + VB); pr.stdout.close(); t0 = time.time(); rc = pr.wait(timeout=10)
        assert rc == 0, rc
        print('reader closed: the helper ended in %.2f s' % (time.time() - t0))
        print('tpc_play: all tests passed')
    finally:
        for f in os.listdir(d): os.remove(os.path.join(d, f))
        os.rmdir(d)

main()
