#!/usr/bin/env python3
"""Known-answer tests of trim_render.py on a synthetic master shaped like the renders (ProRes 422 704x480 at 60000/1001,
PCM S24 48 kHz in .mov): five 180-frame scenes, so scene changes at frames 180, 360, 540 and 720, and audio whose every
sample is identifiable. Each copy's frames and audio are compared in full with the master's."""
import math, os, shutil, subprocess, sys, tempfile
from fractions import Fraction
HERE = os.path.dirname(os.path.abspath(__file__)); TOOL = os.path.join(HERE, 'trim_render.py')
FD = Fraction(1001, 60000); SPF = 48000 * FD
NS = math.ceil(900 * SPF) - 2900                               # audio ends 2900 samples before the last frame, as a render's does
edge = lambda f: min(NS, math.ceil(f * SPF))

d = tempfile.mkdtemp(); M = os.path.join(d, 'master.mov')
scenes = ['testsrc2=s=704x480:r=60000/1001', 'smptebars=s=704x480:r=60000/1001', 'mandelbrot=s=704x480:r=60000/1001',
          'testsrc=s=704x480:r=60000/1001', 'color=c=0x2050c0:s=704x480:r=60000/1001']
inputs = sum((['-f', 'lavfi', '-i', s] for s in scenes), [])
fc = ''.join('[%d:v]trim=end_frame=180,setpts=PTS-STARTPTS,format=yuv422p10le[v%d];' % (i, i) for i in range(5)) + ''.join('[v%d]' % i for i in range(5)) + 'concat=n=5:v=1:a=0[v]'
subprocess.run(['ffmpeg', '-v', 'error', *inputs, '-f', 'lavfi', '-i', "aevalsrc='0.4*sin(2*PI*440*t)+0.3*(mod(n,977)/977-0.5)|0.4*sin(2*PI*660*t)':s=48000",
                '-filter_complex', fc, '-map', '[v]', '-map', '5:a', '-c:v', 'prores_ks', '-profile:v', '2', '-c:a', 'pcm_s24le',
                '-af', 'atrim=end_sample=%d' % NS, '-y', M], check=True)

def run(*a):
    r = subprocess.run([sys.executable, TOOL, M, *a], capture_output=True, text=True); return r.returncode, r.stdout + r.stderr
def frames(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_packets', '-show_data_hash', 'sha256', '-show_entries', 'packet=data_hash', '-of', 'csv=p=0', p], capture_output=True, text=True, check=True)
    return r.stdout.split()
def audio(p):
    return subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:a', '-f', 's24le', '-'], capture_output=True, check=True).stdout
MF, MA = frames(M), audio(M)
assert len(MF) == 900 and len(MA) == NS * 6, (len(MF), len(MA))
def expect(name, keep):
    out = os.path.join(d, name + '.mov'); F, A = frames(out), audio(out)
    assert F == sum((MF[a:b] for a, b in keep), []), (name, len(F))
    assert A == b''.join(MA[edge(a) * 6:edge(b) * 6] for a, b in keep), (name, len(A), sum(edge(b) - edge(a) for a, b in keep) * 6)

# 1. a cut moves to the nearest scene changes: 4.0 s -> frame 180 (3.003 s), 7.5 s -> frame 360 (6.006 s)
rc, out = run('cut1', '--cut', '0:04-0:07.5')
assert rc == 0 and 'scene change' in out, out
expect('cut1', [(0, 180), (360, 900)])
# 2. two cuts, one running to the end; master untouched
before = os.stat(M)
rc, out = run('cut2', '--cut', '2.9-6.1', '--cut', '11.9-14.5')
assert rc == 0 and 'the end' in out, out
expect('cut2', [(0, 180), (360, 720)])
assert os.stat(M).st_mtime == before.st_mtime and os.stat(M).st_size == before.st_size
# 3. --keep with --exact: frame-exact at the given times (2 s = frame 120, 5 s = frame 300), off a scene change
rc, out = run('keep1', '--keep', '0:02-0:05', '--exact')
assert rc == 0, out
expect('keep1', [(120, 300)])
# 4. no scene change within the window: the time stays (4.5 s = frame 270, 4.6 s ~ frame 276)
rc, out = run('keep2', '--keep', '4.5-4.6', '--window', '0.5')
assert rc == 0 and 'no scene change within 0.5 s' in out, out
expect('keep2', [(270, 276)])
# 5. refusals: the master's own name, an existing copy, a folder in the name, both kinds of span
for args, why in ((['master', '--cut', '1-2'], "master's own name"), (['cut1', '--cut', '1-2'], 'exists'),
                  (['sub/x', '--cut', '1-2'], 'no folders'), (['y', '--cut', '1-2', '--keep', '3-4'], 'one kind')):
    rc, out = run(*args); assert rc == 2 and why in out, (args, out)
# 6. a span whose ends move to the same scene change is refused
rc, out = run('empty', '--cut', '2.9-3.2'); assert rc == 2 and 'empty after moving' in out, out
# 7. --dry-run writes nothing
rc, out = run('dry', '--cut', '4-7', '--dry-run'); assert rc == 0 and 'nothing written' in out and not os.path.exists(os.path.join(d, 'dry.mov')), out
assert not [n for n in os.listdir(d) if n.startswith('.')], os.listdir(d)
shutil.rmtree(d)
print('trim_render: all tests passed')
