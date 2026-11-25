# Scoring a removal IN THE PICTURE (the left picture edge of every line, a step out of blanking) and on every part of the
# test line, as the two reviews of 2026-11-25 asked.  No large arrays are written: removals run frame by frame.
#
#   python3 harness.py tracks                      -> tracks.npz: left edges that stay put 12+ frames (captured profiles, t = -2..92)
#   python3 harness.py score NAME [key=value ...]  -> scores one removal variant (see `variant`); keeps NAME.npz (removed profiles)
#   python3 harness.py tl NAME [key=value ...]     -> test line by part, amounts from the other field's line
#   python3 harness.py remove LUMA VBI OUT_removed.npy [key=value ...]   -> a whole stretch removed (also OUT_read.npy)
#   python3 harness.py ka [NOISE]                  -> known answer for the whole method on made-up captures of the weak passage
#   python3 harness.py calib [K0 K1 LAM HALF OUT TRACKS.npz ...]   -> calib.npz (or OUT), from one or several passages' tracks: the two echo shapes as the picture's left edges show them, and taps for them
# Variant keys: lag=0|1 (the lag near blanking), floor=0|1 (samples at the floor left as captured), g1=, g2= (gains on the
# two shapes), g2z= (zero added to amount 2), shift= (taps moved by this many samples), eps=, iters=, step=N (every Nth frame),
# calib=1 (taps from calib.npz instead of the bar's), even=1 (score even-numbered tracks only);
# lum=, vbi=, tracks= name another passage's files for score and tl (default: the first passage's); cal= another calibration file
#
# Scores (all from edges that stay put, so picture content cancels):
#   slope1, slope2 : what the edge's profile still does per unit of amount 1 / amount 2 (joint regression inside each track),
#                    rms over +2..+24 (the dip) and +26..+90 (the bands).  Both zero = the removal takes off exactly what moves.
#   band           : pooled (removed - captured) over +22..+92 with its line taken out, swing by reading, as share and in codes
#   fill           : level at +6..+8 after removal against the level at +60..+90, median and 5-95% over frames, by reading
import numpy as np, sys, resource
import model as M, refit4 as F
from aware import clean
np.set_printoptions(linewidth=240, precision=3, suppress=True)
T = np.arange(-2, 93); COLS = np.arange(720); NF = 1024; BINS = [(0.30, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 0.90)]
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def cross(v, lev):
    i = np.argmax(v >= lev); return None if i == 0 else i - 1 + (lev - v[i - 1]) / (v[i] - v[i - 1])
def left_edges(y):                     # rows with a clean step out of blanking into a flat stretch: (row, step height, crossing)
    out = []
    for r in range(y.shape[0]):
        a = y[r, 70:105]; p = a.mean()
        if p > 40 and a.std() < 0.06 * p and abs(y[r, 40:70].mean() / p - 1) < 0.05:
            c = cross(y[r, :30], 0.5 * p)
            if c is not None and 3 < c < 14: out.append((r, p, c))
    return out
def remove_img(Y, q, white, lag=True, floor=False, cleaner=None, eps=0.01, iters=3, a_dark=0.4, g_dark=0.8):
    # floor=True: the capture cut off whatever the echo pushed below blanking.  A sample at the floor is either blanking (nothing to
    # do) or picture whose dip was cut off (its captured value is too high by an unknown amount).  Which one is decided by the
    # prediction: if the estimate plus its predicted echo is below the floor, the sample was cut off; its true value is taken to be
    # that prediction, and the picture there is the estimate carried by its neighbours (the five-line cleaning), not blanking.
    q = np.r_[0, q[1:]]; H = 1 + np.fft.rfft(q, NF); n = Y.shape[1]; fl = Y <= 0.5 if floor else None
    X = np.fft.irfft(np.fft.rfft(Y, NF, axis=1) * np.conj(H) / (np.abs(H) ** 2 + eps), NF, axis=1)[:, :n]
    for it in range(iters):
        Xc = cleaner(X) if cleaner else X
        E = np.fft.irfft(np.fft.rfft(Xc, NF, axis=1) * np.fft.rfft(q, NF), NF, axis=1)[:, :n]
        if lag:
            lev = np.clip(np.c_[np.zeros(len(Xc)), Xc[:, :-1]] / white, 0, 1); out = np.zeros_like(E); es = np.zeros(E.shape[0])
            for k in range(n):
                a = a_dark + (1 - a_dark) * lev[:, k]; es += a * (E[:, k] - es); out[:, k] = (g_dark + (1 - g_dark) * lev[:, k]) * es
            E = out
        X = (np.where(fl, np.minimum(Xc + E, Y), Y) if floor else Y) - E
    return X
def shifted(q, s):                     # taps moved later by s samples (linear interpolation)
    if not s: return q
    k = np.arange(len(q)); return np.interp(k - s, k, q, left=0, right=0)
def variant(kv):
    d = dict(lag=1, floor=0, g1=1.0, g2=1.0, g2z=0.0, shift=0.0, eps=0.01, iters=3, step=2, calib=0, even=0, lum='run_luma.npy', vbi='vbi_luma.npy', tracks='tracks.npz', cal='calib.npz')
    d.update({k: v if k in ('lum', 'vbi', 'tracks', 'cal') else float(v) for k, v in (a.split('=') for a in kv)}); return d
def taps(R, m, d):
    Q = np.load(d.get('cal', 'calib.npz'))['Q'] if d.get('calib') else m['Q']       # calib=1: taps read from the picture's own left edges (see cmd_calib)
    return shifted(d['g1'] * R[1] * Q[0] + d['g2'] * (R[2] + d['g2z']) * Q[1], d['shift'])
def fit_calib(meta, cap, R, K0=1, K1=85, lam=0.1, verbose=True):
    # The echo's two shapes as the PICTURE shows them: slope of the left edge's profile on the two amounts inside each steady track
    # (content cancels), then taps that make those shapes out of the edge itself.  The amounts still come from the test bar.
    cap = cap.astype(float); tid = meta[:, 0].astype(int); k = meta[:, 1].astype(int); A = R[k, 1:3]; S = slopes(cap, tid, A); u = np.unique(tid)
    own = np.median([cap[tid == i].mean(0) - A[tid == i].mean(0) @ S for i in u], 0)      # each track run back to no echo; used only as the edge the taps act on
    ks = np.arange(K0, K1 + 1); D2 = np.diff(np.eye(len(ks)), 2, axis=0); Q = np.zeros((2, K1 + 1)); src = np.r_[np.zeros(K1 + 1), own]   # blanking before the edge
    Am = np.stack([src[K1 + 1 - kk: K1 + 1 - kk + len(T)] for kk in ks], 1)
    for i in range(2):
        qs = np.linalg.solve(Am.T @ Am + lam * D2.T @ D2 + 1e-3 * np.eye(len(ks)), Am.T @ S[i]); Q[i, K0:] = qs
        if verbose: print('shape %d as the picture shows it, t=2..30 step 2: %s' % (i + 1, S[i][(T >= 2) & (T <= 30) & (T % 2 == 0)])); print('   taps reproduce it to rms %.4f (shape rms %.4f); sum of taps %.3f' % (np.sqrt(((Am @ qs - S[i]) ** 2).mean()), np.sqrt((S[i] ** 2).mean()), qs.sum()))
    if verbose: print('the edge with the echo run back to nothing, t=-2..30 step 2:', own[(T <= 30) & (T % 2 == 0)])
    return Q, S, own
def cmd_calib(K0='1', K1='85', lam='0.1', half='0', out='calib.npz', *trackfiles):   # half=1: tracks with odd ids only, so the even ones can check it
    metas, caps, Rs = [], [], []; nf = nt = 0                                    # several track files: one calibration over all of them
    for f in trackfiles or ('tracks.npz',):
        z = np.load(f); me = z['meta'].copy(); me[:, 0] = z['meta'][:, 0] + nt; me[:, 1] += nf
        if int(half): s_ = z['meta'][:, 0].astype(int) % 2 == 1
        else: s_ = np.ones(len(me), bool)
        metas.append(me[s_]); caps.append(z['prof'][s_]); Rs.append(z['R']); nf += len(z['R']); nt += int(z['meta'][:, 0].max()) + 1
    Q, S, own = fit_calib(np.concatenate(metas), np.concatenate(caps), np.concatenate(Rs), int(K0), int(K1), float(lam)); np.savez(out, Q=Q, S=S, own=own, K0=int(K0), K1=int(K1))
def make_tracks(lum, n=None):          # left edges that stay put (same row, step within 5%) for 12+ frames
    cur = {}; recs = []; tid = 0
    for k in range(n or lum.shape[0]):
        y = lum[k].astype(float) - M.BL
        for r, p, c in left_edges(y):
            t0 = cur.get(r)
            if t0 and t0[2] == k - 1 and abs(p / t0[1] - 1) < 0.05: i = t0[0]
            else: tid += 1; i = tid
            cur[r] = (i, p, k); recs.append((i, k, r, p, c, np.interp(c + T, COLS, y[r]) / p))
        guard()
    ids = np.array([x[0] for x in recs]); u, cnt = np.unique(ids, return_counts=True); keep = np.isin(ids, u[cnt >= 12])
    return np.array([x[:5] for x in recs])[keep], np.array([x[5] for x in recs], np.float32)[keep]
def cmd_tracks(lumf='run_luma.npy', vbif='vbi_luma.npy', outf='tracks.npz'):
    m = F.build(2, 75, 80, 1, verbose=False); R = F.per_frame(vbif, m); meta, prof = make_tracks(np.load(lumf, mmap_mode='r'))
    np.savez(outf, meta=meta, prof=prof, R=R); print('%s: %d edges in %d tracks of 12+ frames, frames %d' % (outf, len(meta), len(np.unique(meta[:, 0])), len(np.unique(meta[:, 1]))))
def slopes(prof, tid, A):              # joint slope on the columns of A inside each track
    P = prof.astype(float).copy(); A = A.astype(float).copy()
    for i in np.unique(tid):
        s = tid == i; P[s] -= P[s].mean(0); A[s] -= A[s].mean(0)
    return np.linalg.lstsq(A, P, rcond=None)[0]
def report(name, meta, cap, rem, R):
    tid = meta[:, 0].astype(int); k = meta[:, 1].astype(int); p = meta[:, 3]; g = R[k, 0]; A = R[k, 1:3]; near = (T >= 2) & (T <= 24); far = (T >= 26) & (T <= 90)
    rms = lambda v, mk: np.sqrt((v[mk] ** 2).mean())
    Sc = slopes(cap, tid, A); Sr = slopes(rem, tid, A); Gc = slopes(cap, tid, g[:, None])[0]; Gr = slopes(rem, tid, g[:, None])[0]
    print('%s: %d edges, %d tracks' % (name, len(tid), len(np.unique(tid))))
    print('  per unit of reading   : captured dip %.3f band %.3f | removed dip %.3f band %.3f' % (rms(Gc, near), rms(Gc, far), rms(Gr, near), rms(Gr, far)))
    print('  per unit of amount 1  : captured dip %.3f band %.3f | removed dip %.3f band %.3f' % (rms(Sc[0], near), rms(Sc[0], far), rms(Sr[0], near), rms(Sr[0], far)))
    print('  per unit of amount 2  : captured dip %.3f band %.3f | removed dip %.3f band %.3f' % (rms(Sc[1], near), rms(Sc[1], far), rms(Sr[1], near), rms(Sr[1], far)))
    tt = (T >= 2) & (T <= 30) & (T % 2 == 0); print('  t                               ', T[tt])
    for lab, v in (('amount 1: captured', Sc[0]), ('amount 1: left after removal', Sr[0]), ('amount 2: captured', Sc[1]), ('amount 2: left after removal', Sr[1])): print('  %-32s' % lab, v[tt])
    seg = (T >= 22) & (T <= 92); rows = []
    for lo, hi in BINS:
        s = (g >= lo) & (g < hi)
        if s.sum() < 50: continue
        d = np.median(rem[s] - cap[s], 0)[seg]; d = d - np.polyval(np.polyfit(T[seg], d, 1), T[seg]); fr = np.unique(k[s])
        fill = np.array([np.median(rem[s & (k == f)][:, (T >= 6) & (T <= 8)].mean(1) - rem[s & (k == f)][:, (T >= 60) & (T <= 90)].mean(1)) for f in fr if (s & (k == f)).sum() >= 8])
        low = np.median(rem[s], 0); lowest = (low[(T >= 3) & (T <= 24)] - low[(T >= 60) & (T <= 90)].mean()).min()
        rows.append('  reading %.2f-%.2f (%5d edges): band swing %.3f of the step, %4.1f codes | level at the dip against the far level: median %+.3f, 5-95%% %+.3f..%+.3f | lowest point +3..+24: %+.3f'
                    % (lo, hi, s.sum(), np.ptp(d), np.ptp(d) * np.median(p[s]), np.median(fill), *np.quantile(fill, [.05, .95]), lowest))
    print('\n'.join(rows))
def cmd_score(name, *kv):
    d = variant(kv); z = np.load(d['tracks']); meta, cap, R = z['meta'], z['prof'], z['R']; m = F.build(2, 75, 80, 1, verbose=False); lum = np.load(d['lum'], mmap_mode='r')
    k = meta[:, 1].astype(int); use = (k % int(d['step']) == 0) & ((meta[:, 0].astype(int) % 2 == 0) | (d['even'] == 0)); meta, cap = meta[use], cap[use]; k = k[use]; rem = np.zeros_like(cap)   # even=1: even track ids only
    for f in np.unique(k):
        y = lum[f].astype(float) - M.BL; x = remove_img(y, taps(R[f], m, d), R[f, 3], lag=bool(d['lag']), floor=bool(d['floor']), cleaner=lambda v: clean(v, 220), eps=d['eps'], iters=int(d['iters']))
        for i in np.nonzero(k == f)[0]:
            _, _, r, p, c = meta[i]; rem[i] = np.interp(c + T, COLS, x[int(r)]) / p
        guard()
    np.savez(name + '.npz', rem=rem, use=use); report(name + ' ' + ' '.join(kv), meta, cap, rem, R)
def cmd_remove(lumf, vbif, outf, *kv):                 # a whole stretch, for clip.py check / frames and the left-edge scripts
    d = variant(kv); m = F.build(2, 75, 80, 1, verbose=False); R = F.per_frame(vbif, m); lum = np.load(lumf, mmap_mode='r'); lo = hi = 0
    out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape)
    for f in range(lum.shape[0]):
        x = remove_img(lum[f].astype(float) - M.BL, taps(R[f], m, d), R[f, 3], lag=bool(d['lag']), floor=bool(d['floor']), cleaner=lambda v: clean(v, 220), eps=d['eps'], iters=int(d['iters'])) + M.BL
        lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[f] = np.clip(np.rint(x), 0, 255); guard()
    out.flush(); np.save(outf.replace('removed', 'read'), R); print('%s: %d frames; samples cut off below 0: %d, above 255: %d' % (outf, lum.shape[0], lo, hi))
def cmd_ka(noise='1'):
    # Known answer for the whole method.  The weak passage's frames are taken as the clean picture; a made-up echo system (not built
    # from any taps above, with content at lag 0 the taps cannot hold) is put on them with the strong passage's sequence of amounts,
    # cut at the floor and rounded.  Then: tracks -> shapes -> taps from the made-up capture, amounts as a test bar would give them
    # (noise=1: with a field's reading noise), removal, error against the clean frames.
    rng = np.random.default_rng(5); lo = np.load('lo_luma.npy', mmap_mode='r'); n = lo.shape[0]; Rs = np.load('clip_read.npy')[:n]; t = np.arange(90)
    g1 = -np.exp(-0.5 * ((t - 6.5) / 2.3) ** 2) + 0.5 * np.exp(-0.5 * ((t - 14) / 5.5) ** 2) + 0.06 * np.exp(-0.5 * ((t - 38) / 12.0) ** 2); g1 -= g1.mean(); g1 *= 0.42 / np.abs(np.cumsum(g1)).max()
    g2 = -(t - 2.5) * np.exp(-0.5 * ((t - 2.5) / 1.2) ** 2); g2 -= g2.mean(); g2 *= 0.5 / np.abs(np.cumsum(g2)).max(); pq = np.c_[-Rs[:, 1], Rs[:, 2]]
    ka = np.lib.format.open_memmap('ka_luma.npy', mode='w+', dtype=np.uint8, shape=lo.shape)
    for k in range(n):
        x = lo[k].astype(float) - M.BL; H = 1 + np.fft.rfft(pq[k, 0] * g1 + pq[k, 1] * g2, NF)
        ka[k] = np.clip(np.rint(np.fft.irfft(np.fft.rfft(x, NF, axis=1) * H, NF, axis=1)[:, :720] + M.BL), 0, 255); guard()
    ka.flush(); R = np.c_[0.5 * pq[:, 0], -pq[:, 0], pq[:, 1], np.full(n, 235.0), np.zeros(n)]; Rn = R.copy()
    if int(noise): Rn[:, 1] += rng.normal(0, 0.03, n); Rn[:, 2] += rng.normal(0, 0.05, n)
    meta, cap = make_tracks(ka); Q, S, own = fit_calib(meta, cap, Rn, verbose=False); print('known answer: %d edges in %d tracks; amounts with noise: %s' % (len(meta), len(np.unique(meta[:, 0])), bool(int(noise))))
    k_ = meta[:, 1].astype(int); res = {}; prof = {'captured': cap.astype(float), 'removed': np.zeros(cap.shape), 'true system': np.zeros(cap.shape), 'clean': np.zeros(cap.shape)}; inner = np.s_[:, 30:690]
    for f in range(0, n, 3):
        x = lo[f].astype(float) - M.BL; y = ka[f].astype(float) - M.BL; fl = y[inner] <= 0.5
        xr = remove_img(y, Rn[f, 1] * Q[0] + Rn[f, 2] * Q[1], 235.0, lag=False, floor=True, cleaner=lambda v: clean(v, 220))
        xo = remove_img(y, np.r_[0, (pq[f, 0] * g1 + pq[f, 1] * g2)[1:]], 235.0, lag=False, floor=True, cleaner=lambda v: clean(v, 220))
        b = int(np.digitize(R[f, 0], [0.3, 0.4, 0.55])); res.setdefault(b, []).append([np.mean((v[inner] - x[inner])[~fl] ** 2) for v in (y, xr, xo)])
        for i in np.nonzero(k_ == f)[0]:
            _, _, r, p, c = meta[i]
            for nm, v in (('removed', xr), ('true system', xo), ('clean', x)): prof[nm][i] = np.interp(c + T, COLS, v[int(r)]) / p
    print('  strength (dip share) | frames | error against the clean frames, codes rms: captured / removed / removed with the true system (lags 1+)')
    for b in sorted(res): print('  %-20s | %4d   | %5.2f / %5.2f / %5.2f' % (['< 0.3', '0.3-0.4', '0.4-0.55', '> 0.55'][b], len(res[b]), *np.sqrt(np.mean(res[b], 0))))
    use = k_ % 3 == 0; seg = (T >= 22) & (T <= 92); g = R[k_, 0]; pp = meta[:, 3]
    for lo_, hi_ in ((0.2, 0.3), (0.3, 0.4), (0.4, 0.55), (0.55, 0.9)):
        s_ = use & (g >= lo_) & (g < hi_)
        if s_.sum() < 50: continue
        row = []
        for nm in ('captured', 'removed', 'true system'):
            d = np.median(prof[nm][s_] - prof['clean'][s_], 0); dd = d[seg] - np.polyval(np.polyfit(T[seg], d[seg], 1), T[seg]); row.append('%s: dip region rms %.3f, band swing %.3f (%.1f codes)' % (nm, np.sqrt((d[(T >= 2) & (T <= 24)] ** 2).mean()), np.ptp(dd), np.ptp(dd) * np.median(pp[s_])))
        print('  left edge against the clean edge, strength %.2f-%.2f (%d edges): ' % (lo_, hi_, s_.sum()) + ' | '.join(row))
    import os; os.remove('ka_luma.npy')
PARTS = {'staircase': (-420, -172), 'after its fall': (-172, -118), '2T pulse': (-118, -84), '12.5T pulse': (-84, -25), 'bar rise': (-25, 30), 'bar top': (30, 225)}
def cmd_tl(name, *kv):
    d = variant(kv); m = F.build(2, 75, 80, 1, verbose=False); tr = m['tr']; X = np.arange(-450, 248); weak = []; v = np.load(d['vbi'], mmap_mode='r'); res = {b: {'cap': [], 'rem': [], 'fl': []} for b in BINS}
    for f in ('lo_vbi.npy', 'lo2_vbi.npy'):
        w = np.load(f, mmap_mode='r')
        for k in range(w.shape[0]):
            for j in (4, 12):
                y = w[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, tr) if top >= 120 else (None, None)
                if r is not None and F.reading(r, tr) < 0.12: weak.append(np.interp(c + X, COLS, y, left=np.nan, right=np.nan) / top)
    weak = np.nanmedian(weak, 0)
    for k in range(0, v.shape[0], int(d['step'])):
        L = []
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, tr) if top >= 120 else (None, None); L.append(None if r is None else (y, top, r, c))
        if None in L: continue
        for src, dst in ((L[0], L[1]), (L[1], L[0])):
            a = F.amounts(src[2], m); g = F.reading(dst[2], tr); Rk = np.r_[g, a, dst[1]]
            x = remove_img(dst[0][None], taps(Rk, m, d), dst[1], lag=bool(d['lag']), floor=bool(d['floor']), eps=d['eps'], iters=int(d['iters']))[0]
            for b in BINS:
                if b[0] <= g < b[1]: res[b]['cap'].append(np.interp(dst[3] + X, COLS, dst[0], left=np.nan, right=np.nan) / dst[1]); res[b]['rem'].append(np.interp(dst[3] + X, COLS, x, left=np.nan, right=np.nan) / dst[1])
    print('%s %s: test line against the weak line, rms by part, captured -> removed (samples at the floor in the captured line left out)' % (name, ' '.join(kv)))
    for b in BINS:
        if len(res[b]['cap']) < 10: continue
        c = np.nanmedian(res[b]['cap'], 0); r = np.nanmedian(res[b]['rem'], 0); ok = c > 0.02; top = (X >= 30) & (X < 225); dt = (r - weak)[top]; dt = dt - np.polyval(np.polyfit(X[top], dt, 1), X[top])
        print('  reading %.2f-%.2f (%3d): ' % (*b, len(res[b]['cap'])) + ' | '.join('%s %.3f -> %.3f' % (n_, *[np.sqrt(np.nanmean((v_ - weak)[(X >= a_) & (X < b_) & ok] ** 2)) for v_ in (c, r)]) for n_, (a_, b_) in PARTS.items()) + ' | bar-top swing %.3f' % np.ptp(dt))
if __name__ == '__main__':
    {'tracks': cmd_tracks, 'score': cmd_score, 'tl': cmd_tl, 'calib': cmd_calib, 'remove': cmd_remove, 'ka': cmd_ka}[sys.argv[1]](*sys.argv[2:])
