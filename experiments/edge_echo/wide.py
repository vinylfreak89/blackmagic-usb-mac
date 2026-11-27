# The echo described by K amounts per frame, read from the test bar against shapes learned ACROSS THE CAPTURE (the survey's
# test lines, 768 points 5 s apart), not from one passage: the first passage's two shapes missed where the echo sits 36 minutes
# later (README, "A second passage").  What the amounts do to a picture edge is read from the picture, as in harness.py, but
# from several passages at once, and one passage can be held out.
#   python3 wide.py build K SURVEY_tl.npy [VBI.npy ...]      -> wide.npz: the no-echo bar edge (refit4's) and K shapes of the bar's rise
#   python3 wide.py amounts VBI.npy OUT.npy                  -> per frame: reading, bar top, borrowed flag, K amounts
#   python3 wide.py calib OUT.npz TRACKS.npz=AMOUNTS.npy ... -> the K shapes as the picture's left edges show them, and taps for them;
#                                                               prints each passage's edge run back to no echo (they should agree)
#   python3 wide.py score NAME CAL.npz TRACKS.npz LUMA.npy AMOUNTS.npy [even]   -> harness.py's scores for the removal
#   python3 wide.py remove LUMA.npy AMOUNTS.npy CAL.npz OUT_removed.npy          -> a whole stretch (also OUT_read.npy for clip.py)
#   python3 wide.py tl CAL.npz VBI.npy                       -> the test line by part, amounts from the other field's line
import sys, numpy as np
import model as M, refit4 as F, harness as H
from aware import clean
np.set_printoptions(linewidth=250, precision=3, suppress=True)
TR = np.arange(-4, 81); T = H.T
def rises(v, lines):                    # bar rises of a (frames, lines, 720) array: (frames, len(lines), len(TR)), nan where no bar; also tops
    out = np.full((v.shape[0], len(lines), len(TR)), np.nan); tops = np.full((v.shape[0], len(lines)), np.nan)
    for k in range(v.shape[0]):
        for i, j in enumerate(lines):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, _ = F.rise(y, top, TR) if top >= 120 else (None, None)
            if r is not None: out[k, i] = r; tops[k, i] = top
        H.guard()
    return out, tops
def cmd_build(K, survey, *vbis):
    own = F.build(2, 75, 80, 1, verbose=False)['own']; R = [rises(np.load(survey, mmap_mode='r'), (0, 1))[0].reshape(-1, len(TR))] + [rises(np.load(f, mmap_mode='r'), (4, 12))[0].reshape(-1, len(TR)) for f in vbis]
    R = np.concatenate(R); R = R[~np.isnan(R[:, 0])]; U, s, Vt = np.linalg.svd(R - own, full_matrices=False); K = int(K)
    for i in range(K):                   # signs fixed so the amounts read the same way round on every build: first shape positive at the dip, others by their largest value
        Vt[i] *= np.sign(Vt[i][TR == 6][0]) if i == 0 else np.sign(Vt[i][np.argmax(np.abs(Vt[i]))])
    np.savez('wide.npz', own=own, V=Vt[:K]); print('%d bar rises; share of the departure from the no-echo edge carried by each shape: %s' % (len(R), (s ** 2 / (s ** 2).sum())[:K + 2]))
    for i in range(K): print('shape %d, t = -4..20: %s' % (i + 1, Vt[i][:25]))
def frame_amounts(vbif): return amounts_of(*rises(np.load(vbif, mmap_mode='r'), (4, 12)))
def amounts_of(r, tops):                # per frame: reading, bar top, 1 if borrowed from the nearest frame with a bar, the K amounts
    z = np.load('wide.npz'); own, V = z['own'], z['V']; n = len(r); out = np.full((n, 3 + len(V)), np.nan)
    for k in range(n):
        ok = ~np.isnan(r[k, :, 0])
        if ok.any(): rr = r[k, ok].mean(0); out[k] = np.r_[F.reading(rr, TR), tops[k, ok].mean(), 0, V @ (rr - own)]
    have = np.nonzero(~np.isnan(out[:, 0]))[0]
    for k in np.nonzero(np.isnan(out[:, 0]))[0]: out[k] = out[have[np.argmin(np.abs(have - k))]]; out[k, 2] = 1
    return out
def cmd_amounts(vbif, outf):
    A = frame_amounts(vbif); np.save(outf, A); print('%s: %d frames, borrowed %d; reading %.2f..%.2f; amounts 5%% / median / 95%%: %s' % (outf, len(A), int(A[:, 2].sum()), A[:, 0].min(), A[:, 0].max(), np.quantile(A[:, 3:], [.05, .5, .95], axis=0).T.round(2).tolist()))
def load(pairs):                        # several passages' tracks as one set: meta (track ids and frame numbers made distinct), profiles, amounts, passage number
    metas, caps, As, src = [], [], [], []; nf = nt = 0
    for i, pr in enumerate(pairs):
        tf, af = pr.split('='); z = np.load(tf); me = z['meta'].copy(); A = np.load(af); me[:, 0] += nt; me[:, 1] += nf
        metas.append(me); caps.append(z['prof']); As.append(A); src.append(np.full(len(me), i)); nf += len(A); nt += int(z['meta'][:, 0].max()) + 1
    return np.concatenate(metas), np.concatenate(caps).astype(float), np.concatenate(As), np.concatenate(src)
def cmd_calib(outf, *pairs, K0=1, K1=85, lam=0.1):     # lags from 1: the removal keeps the level (harness.remove_img has no lag 0)
    meta, cap, A, src = load(pairs); tid = meta[:, 0].astype(int); k = meta[:, 1].astype(int); a = A[k, 3:]; S = H.slopes(cap, tid, a); nk = S.shape[0]
    u, first = np.unique(tid, return_index=True); back = np.array([cap[tid == i].mean(0) - a[tid == i].mean(0) @ S for i in u]); own = np.median(back, 0); sel = (T <= 30) & (T % 2 == 0)
    print('t                                         ', T[sel])
    for i in range(nk): print('shape %d as the picture shows it            ' % (i + 1), S[i][sel])
    print('edge run back to no echo, all passages    ', own[sel])
    for i, pr in enumerate(pairs):
        s_ = src[first] == i; print('   %-38s' % pr.split('=')[0], np.median(back[s_], 0)[sel], ' (%d tracks; amounts in its edges, median: %s)' % (s_.sum(), np.median(a[src == i], 0).round(2)))
    ks = np.arange(K0, K1 + 1); D2 = np.diff(np.eye(len(ks)), 2, axis=0); Q = np.zeros((nk, K1 + 1)); ext = np.r_[np.zeros(K1 + 1), own]
    Am = np.stack([ext[K1 + 1 - kk: K1 + 1 - kk + len(T)] for kk in ks], 1)
    for i in range(nk):
        qs = np.linalg.solve(Am.T @ Am + lam * D2.T @ D2 + 1e-3 * np.eye(len(ks)), Am.T @ S[i]); Q[i, K0:] = qs
        print('shape %d: taps reproduce it to rms %.4f (shape rms %.4f); sum of taps %+.3f, at lag 0 %+.3f' % (i + 1, np.sqrt(((Am @ qs - S[i]) ** 2).mean()), np.sqrt((S[i] ** 2).mean()), qs.sum(), Q[i, 0]))
    np.savez(outf, Q=Q, S=S, own=own)
def taps(a, Q): return a @ Q
def removed(y, a, Q, white): return H.remove_img(y, taps(a, Q), white, lag=False, floor=True, cleaner=lambda v: clean(v, 220))
def cmd_score(name, calf, trackf, lumf, amf, even='0'):
    Q = np.load(calf)['Q']; z = np.load(trackf); meta, cap = z['meta'], z['prof']; A = np.load(amf); lum = np.load(lumf, mmap_mode='r'); k = meta[:, 1].astype(int)
    use = (k % 2 == 0) & ((meta[:, 0].astype(int) % 2 == 0) | (int(even) == 0)); meta, cap, k = meta[use], cap[use], k[use]; rem = np.zeros_like(cap)
    for f in np.unique(k):
        x = removed(lum[f].astype(float) - M.BL, A[f, 3:], Q, A[f, 1])
        for i in np.nonzero(k == f)[0]:
            _, _, r, p, c = meta[i]; rem[i] = np.interp(c + T, H.COLS, x[int(r)]) / p
        H.guard()
    H.report(name, meta, cap, rem, np.c_[A[:, 0], A[:, 3:5]])
def cmd_remove(lumf, amf, calf, outf):
    Q = np.load(calf)['Q']; A = np.load(amf); lum = np.load(lumf, mmap_mode='r'); lo = hi = 0; out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape)
    for f in range(lum.shape[0]):
        x = removed(lum[f].astype(float) - M.BL, A[f, 3:], Q, A[f, 1]) + M.BL; lo += int((x < 0).sum()); hi += int((x > 255).sum()); out[f] = np.clip(np.rint(x), 0, 255); H.guard()
    out.flush(); np.save(outf.replace('removed', 'read'), np.c_[A[:, 0], A[:, 3:5], A[:, 1], A[:, 2]]); print('%s: %d frames; samples cut off below 0: %d, above 255: %d' % (outf, lum.shape[0], lo, hi))
def cmd_tl(calf, vbif):
    Q = np.load(calf)['Q']; z = np.load('wide.npz'); own, V = z['own'], z['V']; X = np.arange(-450, 248); weak = []; v = np.load(vbif, mmap_mode='r'); res = {b: {'cap': [], 'rem': []} for b in H.BINS}
    for f in ('lo_vbi.npy', 'lo2_vbi.npy'):
        w = np.load(f, mmap_mode='r')
        for k in range(w.shape[0]):
            for j in (4, 12):
                y = w[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, TR) if top >= 120 else (None, None)
                if r is not None and F.reading(r, TR) < 0.12: weak.append(np.interp(c + X, H.COLS, y, left=np.nan, right=np.nan) / top)
    weak = np.nanmedian(weak, 0)
    for k in range(0, v.shape[0], 2):
        L = []
        for j in (4, 12):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, TR) if top >= 120 else (None, None); L.append(None if r is None else (y, top, r, c))
        if None in L: continue
        for src, dst in ((L[0], L[1]), (L[1], L[0])):
            g = F.reading(dst[2], TR); x = H.remove_img(dst[0][None], taps(V @ (src[2] - own), Q), dst[1], lag=False, floor=True)[0]
            for b in H.BINS:
                if b[0] <= g < b[1]: res[b]['cap'].append(np.interp(dst[3] + X, H.COLS, dst[0], left=np.nan, right=np.nan) / dst[1]); res[b]['rem'].append(np.interp(dst[3] + X, H.COLS, x, left=np.nan, right=np.nan) / dst[1])
    print('%s on %s: test line against the weak line, rms by part, captured -> removed' % (calf, vbif))
    for b in H.BINS:
        if len(res[b]['cap']) < 10: continue
        c = np.nanmedian(res[b]['cap'], 0); r = np.nanmedian(res[b]['rem'], 0); ok = c > 0.02; top = (X >= 30) & (X < 225); dt = (r - weak)[top]; dt = dt - np.polyval(np.polyfit(X[top], dt, 1), X[top])
        print('  reading %.2f-%.2f (%3d): ' % (*b, len(res[b]['cap'])) + ' | '.join('%s %.3f -> %.3f' % (n_, *[np.sqrt(np.nanmean((v_ - weak)[(X >= a_) & (X < b_) & ok] ** 2)) for v_ in (c, r)]) for n_, (a_, b_) in H.PARTS.items()) + ' | bar-top swing %.3f' % np.ptp(dt))
if __name__ == '__main__':
    {'build': cmd_build, 'amounts': cmd_amounts, 'calib': cmd_calib, 'score': cmd_score, 'remove': cmd_remove, 'tl': cmd_tl}[sys.argv[1]](*sys.argv[2:])
