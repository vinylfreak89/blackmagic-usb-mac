# per field of the TBC-off pass: colour ghost removed (seq2, the accepted colour step) | plus brightness ghosts removed
# (bright_deghost) with the whole-tape delays and the strengths of the field's own 8-field stretch.  Fields in a stretch
# without plain lines take strengths interpolated between the nearest measured stretches (held past the ends).
# UYVY 1448x240 per field on stdout; the 8-sample divider is white where the field's strengths were measured, grey where
# interpolated.  Per-field log (field, measured, LSQR iterations, RMS change in codes) to LOG.
import numpy as np, sys, os, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import seq2, bright_deghost as B
S, LOG = sys.argv[1], sys.argv[2]; DAMP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.125
NFR = int(sys.argv[4]) if len(sys.argv) > 4 else None
NR = 236; BL = 1.5; sh = np.load(S + '/tape_sh.npy'); NF = len(sh) if NFR is None else NFR
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(len(sh), NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(len(sh), NR, 360))
z = np.load(S + '/tape_chain.npz'); Ts = list(z['Ts']); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])))
if 'Tc' in z.files: ch['cp'] = dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c']))
st = np.load(S + '/strengths_8.npz'); T = st['T']; PER = int(st['PER']); F0 = st['f0']; G = st['G']; P0 = st['p0']
cen = F0 + (PER - 1) / 2
def strengths(f):
    k = np.searchsorted(F0, f, 'right') - 1
    if k >= 0 and f < F0[k] + PER: return G[k], P0[k], True
    if f <= cen[0]: return G[0], P0[0], False
    if f >= cen[-1]: return G[-1], P0[-1], False
    j = np.searchsorted(cen, f); a = (f - cen[j - 1]) / (cen[j] - cen[j - 1])
    return (1 - a) * G[j - 1] + a * G[j], (1 - a) * P0[j - 1] + a * P0[j], False
def uyvy(y, c):
    o = np.empty((240, 1440), np.uint8); o[:, 0::4] = 128; o[:, 2::4] = 128; o[:, 1::2] = 16
    o[2:238, 1::2] = np.clip(np.rint(y + BL), 0, 255); o[2:238, 0::4] = np.clip(np.rint(c.real + 128), 0, 255); o[2:238, 2::4] = np.clip(np.rint(c.imag + 128), 0, 255)
    return o
def one(f):
    y = np.asarray(Yy[f], float); c = np.asarray(Cc[f], complex)
    y2, c2 = seq2.process(y, c, sh[f], ch, Ts, float(z['D']), float(z['sig']), float(z['lam']), B=seq2.field_burst(c, ch, float(z['D'])))
    g, p0, meas = strengths(f)
    R, info = B.field((y - p0) / B.CODE, T, g, sh[f], damp=DAMP)
    y3 = R * B.CODE + p0; m = B.layout(NR, sh[f])[3]; y3[~m] = y2[~m]
    gap = np.tile(np.array([128, 235 if meas else 128], np.uint8), (240, 8))
    fr = np.concatenate([uyvy(y2, c2), gap, uyvy(y3, c2)], 1)
    return f, fr.tobytes(), meas, int(info[1]), float(np.sqrt(np.mean((y3 - y2)[m] ** 2)))
if __name__ == '__main__':
    log = open(LOG, 'w'); log.write('field,measured,iterations,rms_change_codes\n'); out = sys.stdout.buffer; n = 0
    with mp.get_context('fork').Pool(4) as pool:
        for f, b, meas, it, ch_ in pool.imap(one, range(NF), chunksize=2):
            assert f == n, (f, n); out.write(b); log.write('%d,%d,%d,%.2f\n' % (f, meas, it, ch_)); n += 1
            if n % 100 == 0: print('bright_render: %d fields' % n, file=sys.stderr, flush=True)
    log.close(); print('bright_render: %d fields written' % n, file=sys.stderr)
