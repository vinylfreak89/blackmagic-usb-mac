# The owner's model, plainly: ONE reflection per frame, three numbers (strength, phase, delay) read from that frame's test bar
# (reflect.py's form, reflect_score.py's per-frame fit; relative to the capture's weakest-echo state), removed at full strength.
# No picture edges, no leftover hole.  The division limit 0.01 with three passes and the gate are gate.py's; THIN=1 keeps thin
# features in the echo prediction.  Below 1.6 MHz only (above about 2 MHz the test line's echo does not carry to the picture).
#   FADE: where the reflection is as strong as the direct signal the cancelled band is gone from the recording and removal can
#   only add its own errors, so the removal is faded out: full while the strength is under FADE0, none from strength 1 on.
# Run from the scratch directory (reflect_fit.npy, barref.npz; PAR.npy = per-frame numbers from reflect_score.py):
#   python3 onerefl.py remove LUMA.npy PAR.npy OUT_full.npy OUT_fade.npy   -> the stretch removed at full strength, and with the fade
#   python3 onerefl.py frames LUMA.npy FULL.npy FADE.npy PAR.npy           -> raw yuv420p 720x1384 frames on stdout: captured / full / faded
#   python3 onerefl.py bystrength LUMA.npy PAR.npy [STEP]                  -> full strength: what is added where the capture is flat, and the
#                                                                             right border's ghost left on black, by measured strength
import sys, numpy as np
import gate as G, model as M, reflect as RF, reflect_cal as RC
np.set_printoptions(linewidth=250, precision=2, suppress=True)
FADE0 = 0.8; STRIP = 32
def kernel(par):                        # per frame: the reflection's response minus 1 on gate.py's frequencies, and its strength
    v = np.load(RF.FITF); Hr = RC.Hf(par, np.r_[1.0, 0.0, 0.0, v[0], v[1], v[2], v[3], v[4]])
    return (lambda f: np.interp(G.FR, RC.fr, Hr[f].real) + 1j * np.interp(G.FR, RC.fr, Hr[f].imag) - 1), np.hypot(par[:, 0], par[:, 1])
def full(y, q): x = G.remove_spec(y, q, eps=0.01); m, _ = G.gate(x - y); return y + m * (x - y)
def weight(s): return np.clip((1 - s) / (1 - FADE0), 0, 1)
def cmd_remove(lumf, parf, fullf, fadef):
    lum = np.load(lumf, mmap_mode='r'); qf, S = kernel(np.load(parf)); a = np.lib.format.open_memmap(fullf, mode='w+', dtype=np.uint8, shape=lum.shape); b = np.lib.format.open_memmap(fadef, mode='w+', dtype=np.uint8, shape=lum.shape)
    for f in range(lum.shape[0]):
        y = lum[f].astype(float) - M.BL; x = full(y, qf(f)); a[f] = np.clip(np.rint(x + M.BL), 0, 255); b[f] = np.clip(np.rint(y + weight(S[f]) * (x - y) + M.BL), 0, 255); G.H.guard()
    a.flush(); b.flush(); w = weight(S); print('%d frames; strength 5%% %.2f, median %.2f, 95%% %.2f; faded: full removal in %.0f%% of the frames, none in %.0f%%, part in the rest' % (len(S), *np.percentile(S, [5, 50, 95]), 100 * (w == 1).mean(), 100 * (w == 0).mean()))
def cmd_frames(lumf, fullf, fadef, parf):
    from PIL import Image, ImageDraw, ImageFont
    lum = np.load(lumf, mmap_mode='r'); a = np.load(fullf, mmap_mode='r'); b = np.load(fadef, mmap_mode='r'); S = np.hypot(*np.load(parf)[:, :2].T); font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20)
    grey = bytes([128]) * (720 * (1320 + 2 * STRIP) // 2)
    def weave(v): o = np.empty((440, 720), np.uint8); o[0::2] = v[:220]; o[1::2] = v[220:]; return o
    def strip(t): im = Image.new('L', (720, STRIP), 16); ImageDraw.Draw(im).text((8, 5), t, fill=200, font=font); return np.asarray(im)
    for k in range(lum.shape[0]):
        t = k * 1001 / 30000; sys.stdout.buffer.write(np.vstack([weave(lum[k]), strip('top: captured    middle: full strength    %4.1f s    reflection %.2f' % (t, S[k])), weave(a[k]), strip('bottom: removal faded out as the reflection nears 1.0 (now %d%%)' % round(100 * weight(S[k]))), weave(b[k])]).tobytes() + grey); G.H.guard()
def cmd_bystrength(lumf, parf, step='4'):
    from scipy.ndimage import maximum_filter1d, minimum_filter1d
    lum = np.load(lumf, mmap_mode='r'); qf, S = kernel(np.load(parf)); out = []
    def sm(v): return np.concatenate([G.box(G.box(v[r0:r1], 5, 1), 3, 0) for r0, r1 in ((0, 220), (220, v.shape[0]))])
    for f in range(0, lum.shape[0], int(step)):
        y = lum[f].astype(float) - M.BL; q = qf(f); x = full(y, q); s = sm(y); fl = maximum_filter1d((maximum_filter1d(s, 48, axis=1) - minimum_filter1d(s, 48, axis=1) < 3).astype(np.uint8), 48, axis=1) > 0; fl &= y > 4; fl[:, :30] = False; fl[:, 690:] = False
        c = G.border_ghost(y, y); out.append((S[f], np.sqrt((sm(x - y)[fl] ** 2).mean()) if fl.sum() > 2000 else np.nan, np.nan if c is None else c[4:].max(), np.nan if c is None else G.border_ghost(x, y)[4:].max(), np.abs(1 + q)[G.BAND].min())); G.H.guard()
    o = np.array(out); print('%s: %d frames; strength 5%% %.2f, median %.2f, 95%% %.2f' % (lumf, len(o), *np.percentile(S, [5, 50, 95])))
    print('strength   frames | added where the capture is flat, codes rms: median, worst tenth | right border ghost on black (62-minute layout only): captured -> left | picture left at the deepest point')
    for a, b in ((0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0), (1.0, 9)):
        k = (o[:, 0] >= a) & (o[:, 0] < b)
        if k.sum() >= 3: g = np.isfinite(o[k, 2]); print('  %.1f-%.1f   %3d   |  %.2f  %.2f | %s | %.3f' % (a, b, k.sum(), np.nanmedian(o[k, 1]) if np.isfinite(o[k, 1]).any() else np.nan, np.nanpercentile(o[k, 1], 90) if np.isfinite(o[k, 1]).any() else np.nan, '%.2f -> %.2f (%d frames)' % (np.median(o[k, 2][g]), np.median(o[k, 3][g]), g.sum()) if g.any() else '-', np.median(o[k, 4])))
if __name__ == '__main__':
    {'remove': cmd_remove, 'frames': cmd_frames, 'bystrength': cmd_bystrength}[sys.argv[1]](*sys.argv[2:])
