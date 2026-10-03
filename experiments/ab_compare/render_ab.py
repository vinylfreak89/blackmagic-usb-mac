# 2x2 review render of one window: top = H-timing + registration ON, bottom = both OFF; left = A, right = B.
# A is the master (its timeline and audio); B's frame for A counter c is B counter c + shift + off[row] (shift from the config). Each panel is the
# frameserver's own published frame (frameserver_replay --dump-uyvy), keyed by the unit counter in its --dump-log.
import numpy as np, subprocess, os, sys, csv, json
from PIL import Image, ImageDraw, ImageFont
import os as _os
REPLAY = _os.environ.get('REPLAY', 'frameserver_replay')      # a frameserver_replay with --start-offset, --limit-units, --dump-uyvy, --dump-log, --dump-pcm
CFG = json.load(open(_os.environ['AB_CONFIG']))      # capture-specific values live outside git (see README)
AF, BF, OUTDIR = CFG['a_path'], CFG['b_path'], CFG['out_dir']
W, H = 720, 480; FR = W * H * 2; FPS = 30000 / 1001
off = np.load(_os.environ.get('AB_OFFSET', 'ab_offset.npy'))      # make_offset.py
A_BYTES, A_UNITS, A_C0 = CFG['a_bytes'], CFG['a_units'], CFG['a_first_unit']      # A_C0: first complete unit counter in A's raw file
A_ROW0 = CFG['a_row0_counter']                                                  # A's sidecar row 0 is this counter
B_BYTES, B_LOST, B_UNITS = CFG['b_bytes'], CFG['b_lost_bytes'], CFG['b_units']
B_FIRST, B_C0, SHIFT = CFG['b_first_unit'], CFG['b_c0'], CFG['b_counter_shift']  # B counter for A counter c = c + SHIFT + off[row]
B_HOLES = [tuple(h) for h in CFG['b_holes']]                                    # (B recording seconds, units lost in B's raw file)
def ts(s):
    p = [float(x) for x in s.split(':')]; return p[-1] + 60 * p[-2] + (3600 * p[0] if len(p) == 3 else 0)
def a_offset(ctr): return int((ctr - A_C0) * A_BYTES / A_UNITS)
def b_offset(ctr):
    bpu = (B_BYTES + B_LOST) / B_UNITS; u = ctr - B_FIRST; t = (ctr - B_C0) / FPS
    lost = sum(n for s, n in B_HOLES if s < t) * bpu
    return max(0, int(u * bpu - lost))
def replay(path, start_ctr, units, on, tag, work):
    env = dict(os.environ); env.pop('FS_REGISTRATION_OFF', None); env.pop('FS_HRETIME', None)
    if on: env['FS_HRETIME'] = '1'
    else: env['FS_REGISTRATION_OFF'] = '1'
    off_b = a_offset(start_ctr) if path == AF else b_offset(start_ctr)
    base = os.path.join(work, tag)
    cmd = [REPLAY, path, '--start-offset', str(off_b), '--pace-us', '1000', '--limit-units', str(units),
           '--dump-uyvy', base + '.uyvy', '--dump-log', base + '.log'] + (['--dump-pcm', base + '.pcm'] if tag == 'A_off' else [])
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    frames = []; audio = []
    for row in csv.reader(open(base + '.log')):
        if row[0] == 'V': frames.append((int(row[1]) % 65536, int(row[2]), int(row[3])))
        elif row[0] == 'A': audio.append((int(row[2]), int(row[3]), int(row[4])))
    mm = np.memmap(base + '.uyvy', np.uint8, 'r') if frames else None
    assert mm is None or len(mm) == FR * len(frames), (tag, len(mm), len(frames))
    return {c % 65536: k for k, (c, _, _) in enumerate(frames)}, frames, audio, mm, r.stdout[-400:]
def font(size):
    for f in ('/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Monaco.ttf'):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()
F = font(15)
def label_block(lines):
    img = Image.new('L', (W, 22 * len(lines) + 6), 0); d = ImageDraw.Draw(img)
    for i, t in enumerate(lines): d.text((6, 3 + 22 * i), t, fill=255, font=F)
    return np.array(img)
def burn(panel, lines):
    """white text on a black box in the panel's top-left, written into UYVY luma (chroma neutral)."""
    m = label_block(lines); h, w = m.shape; ww = min(w, 420)
    p = panel.reshape(H, W, 2)
    p[:h, :ww, 1] = np.where(m[:, :ww] > 128, 235, 16); p[:h, :ww, 0] = 128
    return panel
def gray(msg):
    p = np.zeros((H, W, 2), np.uint8); p[..., 0] = 128; p[..., 1] = 60
    return burn(p.reshape(-1), [msg])
def tstr(ctr, c0): s = (ctr - c0) / FPS; return '%d:%02d:%05.2f' % (s // 3600, (s // 60) % 60, s % 60)
def render(idx, a, b):
    t0, t1 = ts(a) - 10, ts(b) + 10
    r0, r1 = int(t0 * FPS), int(t1 * FPS)                    # A live-sidecar rows == A counter - A_ROW0
    warm = 600
    c_start = A_ROW0 + r0 - warm; units = (r1 - r0) + warm + 60
    work = _os.path.join(_os.environ.get('WORK', '/private/tmp/abrender'), 'w%02d' % idx); os.makedirs(work, exist_ok=True)
    offs = off[np.clip(np.arange(r0 - warm, r1 + 60), 0, len(off) - 1)]
    b_start = c_start + SHIFT + int(offs.min()) - 300
    P = {}
    for tag, path, cs, n, on in (('A_on', AF, c_start, units, 1), ('A_off', AF, c_start, units, 0),
                                ('B_on', BF, b_start, units + 600, 1), ('B_off', BF, b_start, units + 600, 0)):
        P[tag] = replay(path, cs, n, on, tag, work)
    # audio for the output: A_off's PCM, cut from the first output frame's pts
    amap, frames, audio, _, _ = P['A_off']
    first = A_ROW0 + r0; ci = amap.get(first % 65536)
    assert ci is not None, 'first output frame missing from A_off'
    vpts = frames[ci][1] / frames[ci][2]
    cum = 0; start_sample = None
    for pts_num, den, n in audio:
        bs = pts_num / den
        if bs <= vpts < bs + n / 48000: start_sample = cum + int(round((vpts - bs) * 48000)); break
        cum += n
    assert start_sample is not None
    nout = r1 - r0; nsamp = int(round(nout / FPS * 48000))
    pcm = open(os.path.join(work, 'A_off.pcm'), 'rb').read()[start_sample * 6:(start_sample + nsamp) * 6]
    open(os.path.join(work, 'out.s24le'), 'wb').write(pcm)
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, '%02d_%s-%s.mov' % (idx, a.replace(':', '.'), b.replace(':', '.')))
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'uyvy422', '-s', '1440x960', '-r', '30000/1001', '-i', '-',
                           '-f', 's24le', '-ar', '48000', '-ac', '2', '-i', os.path.join(work, 'out.s24le'),
                           '-filter:v', 'setfield=tff,yadif=mode=send_field:parity=tff,setsar=8/9', '-c:v', 'prores_videotoolbox', '-profile:v', '2',
                           '-c:a', 'pcm_s24le', '-shortest', out], stdin=subprocess.PIPE)
    missing = {k: 0 for k in P}
    for r in range(r0, r1):
        ca = (A_ROW0 + r) % 65536; cb = (A_ROW0 + r + SHIFT + int(off[min(r, len(off) - 1)])) % 65536
        row = []
        for tag, ctr, cap in (('A_on', ca, 'A'), ('B_on', cb, 'B'), ('A_off', ca, 'A'), ('B_off', cb, 'B')):
            m, fr, _, mm, _ = P[tag]; k = m.get(ctr)
            mode = 'H-timing+reg ON' if tag.endswith('on') else 'both OFF'
            if k is None: missing[tag] += 1; row.append(gray('%s %s: no frame for counter %d' % (cap, mode, ctr)).reshape(H, W * 2)); continue
            panel = np.array(mm[k * FR:(k + 1) * FR])
            c0 = A_ROW0 if cap == 'A' else B_C0
            ext = A_ROW0 + r if cap == 'A' else A_ROW0 + r + SHIFT + int(off[min(r, len(off) - 1)])
            row.append(burn(panel, ['%s  %s' % (cap, mode), 'unit %d  %s' % (ext, tstr(ext, c0))]).reshape(H, W * 2))
        top = np.concatenate([row[0], row[1]], 1); bot = np.concatenate([row[2], row[3]], 1)
        ff.stdin.write(np.concatenate([top, bot], 0).tobytes())
    ff.stdin.close(); rc = ff.wait()
    for tag in P: os.remove(os.path.join(work, tag + '.uyvy'))
    print('window %02d %s-%s -> %s  rc %d  frames %d  missing %s' % (idx, a, b, out, rc, nout, missing), flush=True)
if __name__ == '__main__':
    wins = CFG['windows'] if len(sys.argv) < 2 else [w for w in CFG['windows'] if w[0] in {int(x) for x in sys.argv[1].split(',')}]
    for idx, a, b in wins: render(idx, a, b)
