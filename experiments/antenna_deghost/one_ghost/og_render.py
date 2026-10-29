# per field of the TBC-off pass: colour ghost removed (seq2, the accepted colour step) | plus the one strong brightness
# echo removed (og_remove) with the whole-tape delay and its strength measured per stretch (og_tape_measure).
# A stretch's strength is used only if it stands clear of the instrument's floor (fixed before the tape was measured:
# |g| > 3 x the largest null-delay estimate and |g| > 4 x its bootstrap spread); otherwise that stretch counts as no echo.
# Per field the complex strength is interpolated linearly between stretch centres (held past the ends).
# UYVY 1448x240 per field on stdout; the 8-sample divider is white where the field's echo is removed, grey where not.
import numpy as np, sys, os, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/../an'); sys.path.insert(0, HERE + '/../an/er')
import seq2, og_remove as RM
S, LOG, PER = sys.argv[1], sys.argv[2], int(sys.argv[3])
F0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0; F1 = int(sys.argv[5]) if len(sys.argv) > 5 else None   # fields F0..F1-1
NR = 236; BL = 1.5; sh = np.load(S + '/tape_sh.npy'); F1 = len(sh) if F1 is None else F1
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(len(sh), NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(len(sh), NR, 360))
z = np.load(S + '/tape_chain.npz'); Ts = list(z['Ts']); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])))
if 'Tc' in z.files: ch['cp'] = dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c']))
st = np.load(S + '/og_strengths_%d.npz' % PER); T = float(st['T'])
use = (np.abs(st['g']) > 3 * st['null_max']) & (np.abs(st['g']) > 4 * st['sd'])
G = np.where(use, st['g'], 0); cen = (st['f0'] + st['f1'] - 1) / 2
def strength(f): return np.interp(f, cen, G.real) + 1j * np.interp(f, cen, G.imag)
def fillmask(f):
    m = np.zeros((NR, 720), bool)
    for r, c in enumerate(sh[f]):
        if c > 0: m[r, :int(np.ceil(c)) + 1] = True
        elif c < 0: m[r, 720 - int(np.ceil(-c)) - 1:] = True
    return m
def uyvy(y, c):
    o = np.empty((240, 1440), np.uint8); o[:, 0::4] = 128; o[:, 2::4] = 128; o[:, 1::2] = 16
    o[2:238, 1::2] = np.clip(np.rint(y + BL), 0, 255); o[2:238, 0::4] = np.clip(np.rint(c.real + 128), 0, 255); o[2:238, 2::4] = np.clip(np.rint(c.imag + 128), 0, 255)
    return o
def one(f):
    y = np.asarray(Yy[f], float); c = np.asarray(Cc[f], complex)
    y2, c2 = seq2.process(y, c, sh[f], ch, Ts, float(z['D']), float(z['sig']), float(z['lam']), B=seq2.field_burst(c, ch, float(z['D'])))
    g = strength(f); fl = fillmask(f)
    y3 = RM.remove(y2, fl, T, g) if abs(g) > 0 else y2.copy()
    gap = np.tile(np.array([128, 235 if abs(g) > 0 else 128], np.uint8), (240, 8))
    fr = np.concatenate([uyvy(y2, c2), gap, uyvy(y3, c2)], 1)
    return f, fr.tobytes(), g, float(np.sqrt(np.mean((y3 - y2)[~fl] ** 2)))
if __name__ == '__main__':
    log = open(LOG, 'w'); log.write('field,g_abs,g_deg,rms_change_codes\n'); out = sys.stdout.buffer; n = 0
    print('delay %.3f; stretches used %d of %d' % (T, use.sum(), len(use)), file=sys.stderr, flush=True)
    with mp.get_context('fork').Pool(4) as pool:
        for f, b, g, ch_ in pool.imap(one, range(F0, F1), chunksize=2):
            assert f == F0 + n, (f, F0 + n); out.write(b); log.write('%d,%.4f,%.1f,%.2f\n' % (f, abs(g), np.degrees(np.angle(g)), ch_)); n += 1
            if n % 200 == 0: print('og_render: %d fields' % n, file=sys.stderr, flush=True)
    log.close(); print('og_render: %d fields written' % n, file=sys.stderr)
