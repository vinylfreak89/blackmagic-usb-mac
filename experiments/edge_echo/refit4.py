# refit3.py's two-shape echo, read over a longer stretch after the bar's rise.  refit3 looked at +0..+24 samples and
# fitted taps for lags 2..27; the echo's tail runs on to about +60 and comes back to nothing, so those taps had a net
# sum and the removal shifted the level of everything after a bright edge.  Here: shapes over 0..T1, taps K0..K1.
#   python3 refit4.py tl [K0 K1 T1 RECENTRE]                         test line by part: amounts from line 18, removal scored on line 281
#   python3 refit4.py remove LUMA.npy VBI.npy OUT_removed.npy [K0 K1 T1 RECENTRE]   (as clip.py remove: OUT_removed.npy, OUT_read.npy)
# RECENTRE 1 (default): shape 2's zero is set from the weak-echo fields; 0: left where the lowest-reading fields put it.
import numpy as np, sys, resource
import model as M
from aware import clean
from stretch_check import remove_img
np.set_printoptions(linewidth=240, precision=3, suppress=True)
COLS = np.arange(720); X = np.arange(-450, 248)
PARTS = {'staircase': (-420, -172), 'after its fall': (-172, -118), '2T pulse': (-118, -84), '12.5T pulse': (-84, -25), 'bar rise': (-25, 30), 'bar top': (30, 225)}
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def rise(y, top, tr):
    c1 = M.cr(y, 0.5 * top, 440, 540, False)
    if c1 is None or y[int(c1) - 12:int(c1) - 3].max() > 0.15 * top: return None, None
    return np.interp(c1 + tr, COLS, y) / top, c1
def reading(r, tr): return 1 - r[(tr >= 5) & (tr <= 9)].min()
def build(K0=2, K1=75, T1=80, recentre=1, lam=0.1, verbose=True):
    tr = np.arange(-4, T1 + 1); R = []; g = []
    for f in ('vbi_luma.npy', 'lo_vbi.npy', 'lo2_vbi.npy'):
        v = np.load(f, mmap_mode='r')
        for k in range(v.shape[0]):
            for j in (4, 12):
                y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, _ = rise(y, top, tr) if top >= 120 else (None, None)
                if r is not None: R.append(r); g.append(reading(r, tr))
    R = np.array(R); g = np.array(g); own = np.median(R[g < 0.1], 0); m = tr >= 0; U, s, Vt = np.linalg.svd((R - own)[:, m], full_matrices=False)
    V = np.zeros((2, len(tr))); V[:, m] = Vt[:2]; ks = np.arange(K0, K1 + 1); D2 = np.diff(np.eye(len(ks)), 2, axis=0); Q = []; fits = []
    for v_ in V:
        A = np.zeros((len(tr), len(ks)))
        for j, kk in enumerate(ks): A[kk:, j] = own[:len(tr) - kk]
        qs = np.linalg.solve(A.T @ A + lam * D2.T @ D2 + 1e-3 * np.eye(len(ks)), A.T @ v_); q = np.zeros(K1 + 1); q[K0:] = qs; Q.append(q); fits.append(np.sqrt(((A @ qs - v_) ** 2).mean()))
    # The weak-echo edge was picked as the fields with the lowest reading, and the reading itself moves with shape 2 (which moves
    # within seconds), so that pick sits off to one side along shape 2.  A constant shape-2 amount was then removed from every field
    # as if it were echo: a fixed false echo, plain to see when the real one is weak.  Zero for shape 2 = where its amount heads as
    # shape 1's amount goes to nothing, read from the fields with readings 0.1 to 0.6.
    A = (R - own) @ V.T; bins = [(x, x + 0.1) for x in (0.1, 0.2, 0.3, 0.4, 0.5)]; med = np.array([np.median(A[(g >= lo) & (g < hi)], 0) for lo, hi in bins])
    c = np.polyfit(med[:, 0], med[:, 1], 1); off = c[1] if recentre else 0.0; own = own + off * V[1]     # a line through the medians: single fields' two amounts share noise
    if verbose: print('shape-2 amount where shape 1 goes to nothing: %.3f (slope %.3f; medians of amounts 1 / 2 by reading 0.1-0.2 ... 0.5-0.6: %s / %s)%s' % (c[1], c[0], med[:, 0], med[:, 1], '' if recentre else '  NOT applied'))
    if verbose: print('fields %d; shapes carry %s; taps reproduce them to rms %.3f / %.3f; sum of taps %.3f / %.3f; own edge at +30/+50/+70: %s' % (len(g), (s ** 2 / (s ** 2).sum())[:3], *fits, Q[0].sum(), Q[1].sum(), own[np.isin(tr, (30, 50, 70))]))
    return dict(tr=tr, own=own, V=V, Q=Q)
def amounts(r, m): return m['V'] @ (r - m['own'])
def per_frame(vbif, m):                # per frame: reading, two amounts, bar top (mean of its two test lines), borrowed flag
    v = np.load(vbif, mmap_mode='r'); n = v.shape[0]; R = np.full((n, 5), np.nan)
    for k in range(n):
        acc = []
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, _ = rise(y, top, m['tr']) if top >= 120 else (None, None)
            if r is not None: acc.append(np.r_[reading(r, m['tr']), amounts(r, m), top])
        if acc: R[k, :4] = np.mean(acc, 0); R[k, 4] = 0
    have = np.nonzero(~np.isnan(R[:, 0]))[0]
    for k in np.nonzero(np.isnan(R[:, 0]))[0]: R[k, :4] = R[have[np.argmin(np.abs(have - k))], :4]; R[k, 4] = 1
    return R
def cmd_tl(*a):
    m = build(*map(int, a)); v = np.load('vbi_luma.npy', mmap_mode='r'); weak = []; res = {i: {'captured': [], 'removed': []} for i in range(4)}; bins = [(0.3, 0.45), (0.45, 0.6), (0.6, 0.75), (0.75, 0.9)]
    for f in ('lo_vbi.npy', 'lo2_vbi.npy'):
        w = np.load(f, mmap_mode='r')
        for k in range(w.shape[0]):
            for j in (4, 12):
                y = w[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = rise(y, top, m['tr']) if top >= 120 else (None, None)
                if r is not None and reading(r, m['tr']) < 0.12: weak.append(np.interp(c + X, COLS, y, left=np.nan, right=np.nan) / top)
    weak = np.nanmedian(weak, 0)
    for k in range(v.shape[0]):
        ya = v[k, 4].astype(float) - M.BL; yb = v[k, 12].astype(float) - M.BL; ta = np.median(ya[560:680]); tb = np.median(yb[560:680])
        if min(ta, tb) < 120: continue
        ra, _ = rise(ya, ta, m['tr']); rb, cb = rise(yb, tb, m['tr'])
        if ra is None or rb is None: continue
        a = amounts(ra, m); gb = reading(rb, m['tr']); x = M.remove(yb, a[0] * m['Q'][0] + a[1] * m['Q'][1], 1.0, tb, 0.4, 0.8)
        for i, (lo, hi) in enumerate(bins):
            if lo <= gb < hi: res[i]['captured'].append(np.interp(cb + X, COLS, yb, left=np.nan, right=np.nan) / tb); res[i]['removed'].append(np.interp(cb + X, COLS, x, left=np.nan, right=np.nan) / tb)
    print('line 281 against the weak line, amounts read from line 18 of the same frame; rms by part of the line: captured -> removed')
    for i, (lo, hi) in enumerate(bins):
        d = {n: np.nanmedian(res[i][n], 0) - weak for n in res[i]}
        print('  reading %.2f-%.2f (%3d fields): ' % (lo, hi, len(res[i]['captured'])) + ' | '.join('%s %.3f -> %.3f' % (n, *[np.sqrt(np.nanmean(d[w_][(X >= a_) & (X < b_)] ** 2)) for w_ in ('captured', 'removed')]) for n, (a_, b_) in PARTS.items())
              + ' | bar top mean shift %+.3f' % np.nanmean(d['removed'][(X >= 60) & (X < 225)]))
def cmd_remove(lumf, vbif, outf, *a):
    m = build(*map(int, a)); R = per_frame(vbif, m); lum = np.load(lumf, mmap_mode='r'); n = lum.shape[0]
    out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape); lo = hi = 0
    for k in range(n):
        x = remove_img(lum[k].astype(float) - M.BL, R[k, 1] * m['Q'][0] + R[k, 2] * m['Q'][1], 1.0, R[k, 3], cleaner=lambda v: clean(v, 220)) + M.BL
        lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[k] = np.clip(np.rint(x), 0, 255); guard()
    out.flush(); np.save(outf.replace('removed', 'read'), R)
    print(f'{outf}: frames {n}, borrowed a reading {int(R[:, 4].sum())}; reading {R[:, 0].min():.2f}..{R[:, 0].max():.2f}; samples cut off below 0: {lo}, above 255: {hi}')
if __name__ == '__main__':
    {'tl': cmd_tl, 'remove': cmd_remove}[sys.argv[1]](*sys.argv[2:])
