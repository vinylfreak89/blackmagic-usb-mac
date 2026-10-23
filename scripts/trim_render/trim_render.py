#!/usr/bin/env python3
"""trim_render.py MASTER.mov NAME (--cut FROM-TO ... | --keep FROM-TO ...) [--window S] [--threshold X] [--exact] [--dry-run]

An edited copy of a master render, for uploading: the master with some stretches cut out (--cut), or only some stretches
kept (--keep). Times are H:MM:SS(.s) or MM:SS(.s) in the master. Each time moves to the nearest scene change within
--window seconds (default 5) of it (the master's start and end count as one), found by ffmpeg's scene score (--threshold, default 0.3); a time with no scene change
that near stays where it is, and the plan says so. --exact uses the times as given (to the nearest frame).

The copy is NAME.mov beside the master. The master and its capture are only read, never renamed, replaced or removed:
NAME.mov cannot be a capture's or sidecar's name, the master's own name is refused, and so is any NAME.mov that exists.

Cuts are frame-exact and sample-exact. Every ProRes frame in a master is a whole picture, so the kept video is copied
packet for packet; the audio is stored in 1024-sample packets, so it is decoded and written again as the same PCM samples
(a lossless rewrite), cut at the first sample at or after each frame boundary. The master is read once, one kept stretch at a time
(one reader per file on the JuiceFS share), and the copy is written once: each stretch goes through a FIFO into the
single ffmpeg that writes the copy. Before the copy takes its name it is checked: its frame and sample counts from its
own index, and at every seam the first frames and audio of each stretch against the master's own bytes and samples.
--dry-run prints the plan (where each time moved) and writes nothing.
"""
import json, math, os, re, shutil, signal, subprocess, sys, tempfile, time
from fractions import Fraction

SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')
SR = 48000

def say(m): print(time.strftime('%H:%M:%S ') + m, flush=True)
def die(m): print('REFUSE: ' + m, flush=True); sys.exit(2)
def truth(p):
    """where a file is checked: on the share, JuiceMount's own directory (the Mac's view can lag)"""
    p = os.path.realpath(p)
    return FUSE + p[len(SHARE):] if p.startswith(SHARE + '/') and os.path.isdir(FUSE) else p

def parse_time(s):
    parts = s.split(':')
    if not 1 <= len(parts) <= 3: raise ValueError(s)
    t = Fraction(0)
    for x in parts: t = t * 60 + Fraction(x)
    return t

def parse_span(s):
    m = re.fullmatch(r'\s*([0-9:.]+)\s*-\s*([0-9:.]+)\s*', s)
    if not m: die('a span is FROM-TO, e.g. 1:02:10-1:05:00: %r' % s)
    a, b = parse_time(m.group(1)), parse_time(m.group(2))
    if b <= a: die('a span ends before it starts: %r' % s)
    return a, b

def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=index,codec_type,codec_name,r_frame_rate,time_base,nb_frames,sample_rate,channels,start_pts',
                        '-of', 'json', path], capture_output=True, text=True)
    if r.returncode != 0: die('ffprobe could not read %s: %s' % (path, r.stderr.strip()[-300:]))
    st = json.loads(r.stdout)['streams']
    v = [s for s in st if s['codec_type'] == 'video']; a = [s for s in st if s['codec_type'] == 'audio']
    if len(v) != 1 or len(a) != 1: die('%s: expected one video and one audio track, found %d and %d' % (path, len(v), len(a)))
    return v[0], a[0]

def scene_changes(master, t0, t1, threshold):
    """frame times (seconds, Fraction-free float) in [t0, t1) whose scene score passes threshold, with their scores"""
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', '%.6f' % t0, '-to', '%.6f' % t1, '-copyts', '-i', master,
                        '-map', '0:v', '-vf', "select='gt(scene,%s)',metadata=print:file=-" % threshold, '-f', 'null', '-'],
                       capture_output=True, text=True)
    if r.returncode != 0: die('scene detection failed near %.1f s: %s' % (t0, r.stderr.strip()[-300:]))
    out = []; t = None
    for line in r.stdout.splitlines():
        m = re.search(r'pts_time:([0-9.]+)', line)
        if m: t = float(m.group(1)); continue
        m = re.search(r'lavfi\.scene_score=([0-9.]+)', line)
        if m and t is not None: out.append((t, float(m.group(1)))); t = None
    return out

def hms(frames, fd):
    s = float(frames * fd); h = int(s // 3600); m = int(s % 3600 // 60)
    return '%d:%02d:%06.3f' % (h, m, s - h * 3600 - m * 60)

def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0].startswith('-') or a[1].startswith('-'): print(__doc__.split('\n')[0]); sys.exit(2)
    master, name = a[0], a[1]; rest = a[2:]
    cuts, keeps, window, threshold, exact, dry = [], [], 5.0, '0.3', False, False
    i = 0
    while i < len(rest):
        k = rest[i]
        if k in ('--cut', '--keep') and i + 1 < len(rest): (cuts if k == '--cut' else keeps).append(parse_span(rest[i + 1])); i += 2
        elif k == '--window' and i + 1 < len(rest): window = float(rest[i + 1]); i += 2
        elif k == '--threshold' and i + 1 < len(rest): threshold = rest[i + 1]; i += 2
        elif k == '--exact': exact = True; i += 1
        elif k == '--dry-run': dry = True; i += 1
        else: die('unknown argument %r' % k)
    if bool(cuts) == bool(keeps): die('give --cut spans or --keep spans (one kind)')
    if not os.path.isfile(master) or not master.endswith('.mov'): die('the master must be an existing .mov render: %s' % master)
    if '/' in name or name.endswith('.mov') or not name.strip(): die('NAME is the new file name without .mov, no folders: %r' % name)
    out = os.path.join(os.path.dirname(os.path.abspath(master)), name + '.mov')
    mbase = os.path.basename(master)[:-4]
    if name == mbase: die('NAME %r is the master\'s own name' % name)
    if os.path.exists(out) or os.path.exists(truth(out)): die('%s exists; pick another name' % out)

    v, au = probe(master)
    if v['codec_name'] != 'prores': die('the master\'s video is %s, not ProRes: frames are not all whole pictures' % v['codec_name'])
    if au['codec_name'] != 'pcm_s24le' or int(au['sample_rate']) != SR: die('the master\'s audio is %s at %s Hz, not 48 kHz PCM S24' % (au['codec_name'], au['sample_rate']))
    fd = 1 / Fraction(v['r_frame_rate'])                     # seconds per frame (1001/60000)
    nframes = int(v['nb_frames']); spf = SR * fd              # samples per frame, 800.8
    nsamples = int(au['nb_frames'])                           # a master's audio ends a little before its last frame
    vstart = int(v['start_pts']) * Fraction(v['time_base']); astart = int(au['start_pts'])   # audio time base is 1/48000
    if Fraction(au['time_base']) != Fraction(1, SR): die('the master\'s audio time base is %s, not 1/%d' % (au['time_base'], SR))
    if vstart or astart: die('the master\'s streams start at %s s / sample %d, not 0 (renders start at 0; seeks here assume it)' % (vstart, astart))
    say('master %s: %d frames (%s), %s fps, %s audio samples' % (master, nframes, hms(nframes, fd), v['r_frame_rate'], au['nb_frames']))

    def snap(t):
        """the frame a time moves to: the nearest scene change within the window, else the nearest frame"""
        f0 = min(nframes, max(0, round(t / fd)))
        if exact: return f0, 'as given'
        lo, hi = max(Fraction(0), t - Fraction(window)), min(nframes * fd, t + Fraction(window))
        sc = [] if lo >= hi else [(round((Fraction(tt) - vstart) / fd), 'scene change', sco) for tt, sco in scene_changes(master, float(vstart + lo), float(vstart + hi), threshold)] if lo < hi else []
        sc += [(f, what, None) for f, what in ((0, 'the start'), (nframes, 'the end')) if abs((f - f0) * fd) <= window]
        if not sc: return f0, 'no scene change within %g s: as given' % window
        f, what, score = min(sc, key=lambda x: abs(x[0] - f0))
        f = min(nframes, max(0, f))
        return f, '%s %+.2f s away%s' % (what, float((f - f0) * fd), ' (score %.2f)' % score if score is not None else '')

    spans = []
    for x, y in (cuts or keeps):
        fa, wa = snap(x); fb, wb = snap(y)
        say('%s %s-%s -> frames %d-%d (%s-%s): start %s; end %s' % ('cut' if cuts else 'keep', hms(round(x / fd), fd), hms(round(y / fd), fd), fa, fb, hms(fa, fd), hms(fb, fd), wa, wb))
        if fb <= fa: die('the span %s-%s is empty after moving to scene changes' % (hms(round(x / fd), fd), hms(round(y / fd), fd)))
        spans.append((fa, fb))
    spans.sort()
    for (a0, b0), (a1, b1) in zip(spans, spans[1:]):
        if a1 < b0: die('two spans overlap after moving to scene changes: %s-%s and %s-%s' % (hms(a0, fd), hms(b0, fd), hms(a1, fd), hms(b1, fd)))
    if cuts:
        keep, at = [], 0
        for fa, fb in spans:
            if fa > at: keep.append((at, fa))
            at = fb
        if at < nframes: keep.append((at, nframes))
    else: keep = spans
    keep = [(fa, fb) for fa, fb in keep if fb > fa]
    if not keep: die('nothing would be left')
    # each frame boundary's sample: the first at or after it on the audio's own timeline, clamped to the audio's length
    edge = lambda f: min(nsamples, max(0, math.ceil((vstart + f * fd) * SR) - astart))
    samples = [(edge(fa), edge(fb)) for fa, fb in keep]
    total_f = sum(fb - fa for fa, fb in keep); total_s = sum(sb - sa for sa, sb in samples)
    for (fa, fb), (sa, sb) in zip(keep, samples): say('  keep frames %d-%d (%s-%s, %s), samples %d-%d' % (fa, fb, hms(fa, fd), hms(fb, fd), hms(fb - fa, fd), sa, sb))
    say('the copy: %d frames (%s), %d samples' % (total_f, hms(total_f, fd), total_s))
    if dry: say('dry run: nothing written'); return

    # the copy grows under a name of this run's own (plain_render's partials are .NAME.partial.mov), created exclusively
    part = os.path.join(os.path.dirname(out), '.%s.trim-%d.partial.mov' % (name, os.getpid()))
    os.close(os.open(part, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)); made = True
    work = tempfile.mkdtemp(prefix='trim_render.')
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))   # a stop cleans up like Ctrl-C
    try:
        fifos = []
        with open(os.path.join(work, 'list.txt'), 'w') as f:
            f.write('ffconcat version 1.0\n')
            for i, (fa, fb) in enumerate(keep):
                p = os.path.join(work, 'seg%03d.nut' % i); os.mkfifo(p); fifos.append(p)
                f.write("file '%s'\nduration %.9f\n" % (p, float((fb - fa) * fd)))
        mux = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(work, 'list.txt'),
                                '-map', '0:v', '-map', '0:a', '-c', 'copy', '-f', 'mov', '-y', part], stderr=open(os.path.join(work, 'mux.log'), 'w'))
        for i, ((fa, fb), (sa, sb)) in enumerate(zip(keep, samples)):
            if mux.poll() is not None: die('writing the copy stopped early: %s' % open(os.path.join(work, 'mux.log')).read()[-400:])
            start = vstart + fa * fd
            # seek just past the frame's own timestamp without sample-accurate trimming: the copied video starts at that
            # frame (every frame is whole) and the audio decodes from the packet before it; the master's timestamps are
            # kept, so the audio is cut by absolute sample number and the video by its own timestamps (packets from the
            # stretch's end on are dropped). A frame limit instead ended short stretches before their audio was through.
            end_pts = int((vstart + fb * fd) / Fraction(v['time_base']))
            cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-noaccurate_seek', '-copyts', '-ss', '%.9f' % (float(start) + 1e-6),
                   '-to', '%.6f' % float(vstart + fb * fd + 2), '-i', master,
                   '-map', '0:v', '-map', '0:a', '-c:v', 'copy', '-bsf:v', 'noise=drop=gte(pts\\,%d)' % end_pts,
                   '-af', 'atrim=start_pts=%d:end_pts=%d' % (astart + sa, astart + sb), '-c:a', 'pcm_s24le', '-f', 'nut', '-y', fifos[i]]
            say('stretch %d/%d: %s-%s' % (i + 1, len(keep), hms(fa, fd), hms(fb, fd)))
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                mux.kill(); mux.wait(); die('reading the stretch %s-%s failed: %s' % (hms(fa, fd), hms(fb, fd), r.stderr.strip()[-400:]))
        if mux.wait() != 0: die('writing the copy failed: %s' % open(os.path.join(work, 'mux.log')).read()[-400:])
        check(master, part, keep, samples, fd, vstart, astart, total_f, total_s)
        size = os.path.getsize(part); ino = os.stat(truth(part)).st_ino
        t = os.stat(truth(part))
        if t.st_size != size: die('the copy is %d bytes in JuiceMount\'s view, %d in the Mac\'s' % (t.st_size, size))
        if os.path.exists(out) or os.path.exists(truth(out)): die('%s appeared while the copy was being written; nothing was renamed' % out)
        os.rename(part, out); made = False                      # the name is checked just before; rename replaces nothing else
        t = os.stat(truth(out))
        if t.st_size != size or t.st_ino != ino: print('WARNING: %s is %d bytes, inode %d; the copy checked was %d bytes, inode %d' % (out, t.st_size, t.st_ino, size, ino), flush=True); sys.exit(1)
        ad = os.path.join(os.path.dirname(part), '._' + os.path.basename(part))
        try: os.unlink(ad)                                      # the share leaves the old name's ._ entry after a rename
        except OSError: pass
        say('DONE %s (%.2f GB); the master is untouched' % (out, size / 1e9))
    except BaseException:
        if made and os.path.exists(part): os.remove(part)         # only the file this run created
        raise
    finally: shutil.rmtree(work, ignore_errors=True)

def pcm(path, k, n):
    """samples [k, k + n) of a file's audio by absolute sample number (its own timeline, time base 1/48000), as raw S24LE"""
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-noaccurate_seek', '-copyts', '-ss', '%.9f' % max(0, k / SR - 0.1), '-i', path,
                        '-map', '0:a', '-af', 'atrim=start_pts=%d:end_pts=%d' % (k, k + n), '-c:a', 'pcm_s24le', '-f', 's24le', '-'], capture_output=True)
    if r.returncode != 0 or len(r.stdout) != n * 6: die('could not read samples %d-%d of %s (%d bytes)' % (k, k + n, path, len(r.stdout)))
    return r.stdout

def frame_hash(path, t):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-read_intervals', '%.9f%%+#1' % t, '-show_packets', '-show_data_hash', 'sha256',
                        '-show_entries', 'packet=pts,data_hash', '-of', 'json', path], capture_output=True, text=True)
    pk = json.loads(r.stdout).get('packets', []) if r.returncode == 0 else []
    if not pk or 'data_hash' not in pk[0]: die('could not read the frame at %.3f s of %s' % (t, path))
    return pk[0]['data_hash']

def check(master, part, keep, samples, fd, vstart, astart, total_f, total_s):
    v, au = probe(part); cv = int(v['start_pts']) * Fraction(v['time_base']); ca = int(au['start_pts'])
    if int(v['nb_frames']) != total_f: die('the copy has %s frames, expected %d' % (v['nb_frames'], total_f))
    if int(au['nb_frames']) != total_s: die('the copy has %s audio samples, expected %d' % (au['nb_frames'], total_s))
    say('check: %d frames and %d samples, as planned' % (total_f, total_s))
    at_f = 0; at_s = 0; n = 4800
    for (fa, fb), (sa, sb) in zip(keep, samples):
        # the stretch's first frame and first 0.1 s of audio, and its last 0.1 s, must be the master's own
        if frame_hash(part, float(cv + at_f * fd) + 1e-6) != frame_hash(master, float(vstart + fa * fd) + 1e-6): die('the frame at %s of the copy is not the master\'s frame %d' % (hms(at_f, fd), fa))
        m = min(n, sb - sa)
        if pcm(part, ca + at_s, m) != pcm(master, astart + sa, m): die('the audio at %s of the copy is not the master\'s from sample %d' % (hms(at_f, fd), sa))
        if pcm(part, ca + at_s + sb - sa - m, m) != pcm(master, astart + sb - m, m): die('the audio before %s of the copy is not the master\'s up to sample %d' % (hms(at_f + fb - fa, fd), sb))
        at_f += fb - fa; at_s += sb - sa
    say('check: every stretch starts with the master\'s frame and starts and ends with the master\'s samples')

if __name__ == '__main__': main()
