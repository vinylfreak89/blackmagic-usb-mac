# A stretch in motion: captured over echo-removed, luma only.  Echo read per frame as two amounts from that frame's
# own test lines against the measured no-echo edge (refit3.py), removed as in panel3.py (five-line cleaning).
# Run from the scratch directory that holds run_luma.npy, vbi_luma.npy, family.npz, same_edges.npz:
#   python3 clip.py remove [N [LUMA.npy VBI.npy OUT_removed.npy]]   (N = 0: all frames; the first clip's model, superseded by
#                                `refit4.py remove`, which writes the same two files)
#                                -> clip_removed.npy (uint8, shape of run_luma.npy), clip_read.npy (reading, two amounts, bar top, borrowed)
#   python3 clip.py check        -> the steady-edge check and the 0.2-0.6 MHz line-to-line change on what the clip shows
#   python3 clip.py frames       -> raw yuv420p 720x912 frames on stdout (neutral colour): both fields woven (field 1 on top),
#                                   captured / label / removed; deinterlace downstream
import numpy as np, sys, resource
import model as M, refit3 as T, same_edge as E, same_refit as F
from aware import clean, bands
from stretch_check import remove_img
np.set_printoptions(linewidth=260, precision=2, suppress=True)
STRIP = 32
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def readings(vbif='vbi_luma.npy'):
    own, V, Q, _ = T.shapes(); v = np.load(vbif, mmap_mode='r'); n = v.shape[0]; tr = M.tr; R = np.full((n, 5), np.nan)
    for k in range(n):
        acc = []
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, _ = T.rise(y, top) if top >= 120 else (None, None)
            if r is not None: acc.append(np.r_[1 - r[(tr >= 5) & (tr <= 9)].min(), T.amounts(r, own, V), top])
        if acc: R[k, :4] = np.mean(acc, 0); R[k, 4] = 0
    have = np.nonzero(~np.isnan(R[:, 0]))[0]
    for k in np.nonzero(np.isnan(R[:, 0]))[0]:          # a frame with no bar reading borrows the nearest frame's
        R[k, :4] = R[have[np.argmin(np.abs(have - k))], :4]; R[k, 4] = 1
    return R, Q
def remove(n=None, lumf='run_luma.npy', vbif='vbi_luma.npy', outf='clip_removed.npy'):
    R, Q = readings(vbif); lum = np.load(lumf, mmap_mode='r'); n = n or lum.shape[0]
    out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=(n,) + lum.shape[1:]); lo = hi = 0
    for k in range(n):
        y = lum[k].astype(float) - M.BL; x = remove_img(y, R[k, 1] * Q[0] + R[k, 2] * Q[1], 1.0, R[k, 3], cleaner=lambda X: clean(X, 220)) + M.BL
        lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[k] = np.clip(np.rint(x), 0, 255); guard()
        if k % 100 == 99: print(k + 1, 'frames', file=sys.stderr, flush=True)
    out.flush(); np.save(outf.replace('removed', 'read'), R[:n])
    print(f'frames {n}, borrowed a reading {int(R[:n, 4].sum())}; reading {R[:n, 0].min():.2f}..{R[:n, 0].max():.2f} (median {np.median(R[:n, 0]):.2f}); samples cut off below 0: {lo}, above 255: {hi}')
def check():
    lum = np.load('run_luma.npy', mmap_mode='r'); rem = np.load('clip_removed.npy', mmap_mode='r'); R = np.load('clip_read.npy'); n = rem.shape[0]
    meta, cap, d, w, tid2, dk, keep = F.classes(); kk = meta[:, 1].astype(int); sel = np.isin(tid2, keep[1] + keep[-1]) & (kk < n); mt = (E.t >= 2) & (E.t <= 24)
    cols = np.arange(720); out = np.zeros((len(meta), len(E.t)), np.float32)
    for f in np.unique(kk[sel]):
        x = rem[f].astype(float) - M.BL
        for i in np.nonzero(sel & (kk == f))[0]:
            _, _, r, p, s, a = meta[i]; out[i] = (np.interp(p + E.t, cols, x[int(r)]) - a) / s
    g = np.r_[R[:, 0], np.zeros(max(0, kk.max() + 1 - n))][kk]
    print('steady picture edges, what still follows the strength (rms t=2..24):')
    for name, R_ in (('captured', cap), ('clip', out)):
        res = []
        for sg in (1, -1):
            ids = [i for i in keep[sg] if (kk[tid2 == i] < n).all()]; sl, _, se, _ = E.pooled(R_, g, tid2, ids); res.append((np.sqrt((sl[mt] ** 2).mean()), np.sqrt((se[mt] ** 2).mean()), len(ids)))
        print('  %-9s rises %.3f (+-%.3f, %d edges), falls %.3f (+-%.3f, %d edges)' % ((name,) + res[0] + res[1]))
    b = np.array([[bands(lum[k].astype(float), 220), bands(rem[k].astype(float), 220)] for k in range(0, n, 15)])
    print('line-to-line change mid-frame, codes, bands 0-0.2 / 0.2-0.6 / 0.6-1.5 / 1.5-4 MHz (median of %d frames):' % len(b))
    print('  captured', np.median(b[:, 0], 0)); print('  clip    ', np.median(b[:, 1], 0))
def frames():
    from PIL import Image, ImageDraw, ImageFont
    lum = np.load('run_luma.npy', mmap_mode='r'); rem = np.load('clip_removed.npy', mmap_mode='r'); R = np.load('clip_read.npy'); font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20)
    grey = bytes([128]) * (720 * (880 + STRIP) // 2)        # neutral colour planes: the frames are yuv420p, luma codes as captured
    def weave(a): o = np.empty((440, 720), np.uint8); o[0::2] = a[:220]; o[1::2] = a[220:]; return o
    for k in range(rem.shape[0]):
        im = Image.new('L', (720, STRIP), 16); ImageDraw.Draw(im).text((8, 5), 'above: captured      below: echo removed      %4.1f s      echo reading %.2f' % (k * 1001 / 30000, R[k, 0]), fill=200, font=font)
        sys.stdout.buffer.write(np.vstack([weave(lum[k]), np.asarray(im), weave(rem[k])]).tobytes() + grey); guard()
if __name__ == '__main__':
    {'remove': lambda: remove(int(sys.argv[2]) or None if len(sys.argv) > 2 else None, *sys.argv[3:6]), 'check': check, 'frames': frames}[sys.argv[1]]()
