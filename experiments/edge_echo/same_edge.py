# Same edge, different echo strength.  An edge of the picture that stays put for many frames (lettering, a logo, a
# still shot) is the same content each time, while the echo strength (read from the test line) drifts.  Regressing
# its response on echo strength WITHIN each such edge splits it into the edge's own shape and the part that follows
# the echo, with the picture content cancelled out.  Done on the captured lines and on the lines after removal:
#   if the model's echo is right for picture edges, the part that follows the echo is ~0 after removal;
#   whatever overshoot is left and does not follow the echo is the edge's own.
# usage: python3 same_edge.py find [LUMA.npy VBI.npy OUT.npz]  (default: run_luma / vbi_luma -> same_edges.npz)      python3 same_edge.py fit
import numpy as np, sys, resource
import model as M, stretch_check as S
np.set_printoptions(linewidth=260, precision=2, suppress=True)
t = np.arange(-5, 30)
def guard():
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2e9: sys.exit('memory over 2 GB, stopping')
def find(lumf='run_luma.npy', vbif='vbi_luma.npy', outf='same_edges.npz'):
    v = np.load(vbif, mmap_mode='r')[:, 12]; Rb, _, Tb, idx = M.edges(v); gb = M.gauge(Rb); q, _ = M.taps(*M.split(Rb, gb))
    d = np.interp(np.arange(v.shape[0]), idx, gb); w = np.interp(np.arange(v.shape[0]), idx, Tb)      # frames without a reading borrow from neighbours
    lum = np.load(lumf, mmap_mode='r'); cols = np.arange(720)
    meta, cap, aft = [], [], []; open_ = {}; ntid = 0
    for k in range(lum.shape[0]):
        y = lum[k].astype(float) - M.BL; x = S.remove_img(y, q, d[k], w[k]); dd = y[:, 3:] - y[:, :-3]
        rr, cc = np.nonzero(np.abs(dd[:, 40:640]) > 35); cc = cc + 41
        for r, c in zip(rr, cc):
            row = y[r]; g = dd[r]
            if abs(g[c]) < np.abs(g[c-2:c+3]).max(): continue
            lo = row[c-14:c-3]; hi = row[c+26:c+37]
            if lo.std() > 4 or hi.std() > 5: continue
            a, b = lo.mean(), hi.mean(); s = b - a
            if abs(s) < 40 or np.sign(s) != np.sign(g[c]): continue
            nn = (row[c-10:c+30] - a) / s; i = np.argmax(nn[4:] >= 0.5)
            if i == 0: continue
            p = c - 10 + 4 + i - 1 + (0.5 - nn[4+i-1]) / (nn[4+i] - nn[4+i-1])
            tid = -1
            for o in open_.get(r, ()):                                   # the same edge in an earlier frame?
                if k - o[1] <= 3 and k != o[1] and abs(p - o[2]) < 0.6 and np.sign(s) == np.sign(o[3]) and abs(s - o[3]) < 0.2 * abs(s) and abs(a - o[4]) < 10:
                    tid = o[0]; o[1:] = [k, p, s, a]; break
            if tid < 0:
                tid = ntid; ntid += 1; open_.setdefault(r, []).append([tid, k, p, s, a])
            meta.append((tid, k, r, p, s, a)); cap.append((np.interp(p + t, cols, row) - a) / s); aft.append((np.interp(p + t, cols, x[r]) - a) / s)
        if k % 50 == 0:
            guard(); print(k, len(meta), flush=True)
            for r in list(open_): open_[r] = [o for o in open_[r] if k - o[1] <= 3]
    np.savez(outf, meta=np.array(meta), cap=np.array(cap, np.float32), aft=np.array(aft, np.float32), d=d, w=w, q=q)
def pooled(R, dk, tid, keep):
    # within-edge regression: remove each edge's own mean response and mean depth, then one common slope
    Sxy = np.zeros(R.shape[1]); Sxx = 0.0; per = []
    for i in keep:
        m = tid == i; x = dk[m] - dk[m].mean(); y = R[m] - R[m].mean(0); Sxy += x @ y; Sxx += x @ x; per.append((x @ y, x @ x, R[m].mean(0), dk[m].mean(), m.sum()))
    slope = Sxy / Sxx
    own = np.sum([(mr - slope * md) * n for _, _, mr, md, n in per], 0) / sum(p[4] for p in per)      # the edge at no echo
    rng = np.random.default_rng(1); bs = []
    for _ in range(200):                                                 # how sure: resample whole edges
        j = rng.integers(0, len(per), len(per)); bs.append(sum(per[i][0] for i in j) / sum(per[i][1] for i in j))
    return slope, own, np.std(bs, 0), Sxx
def fit():
    z = np.load('same_edges.npz'); meta, cap, aft, d, w, q = z['meta'], z['cap'], z['aft'], z['d'], z['w'], z['q']
    tid = meta[:, 0].astype(int); k = meta[:, 1].astype(int); s = meta[:, 4]; a = meta[:, 5]; dk = d[k]; wk = w[k]
    dark = np.minimum(a, a + s) / wk                                      # the edge's darker side, as a share of white
    ids, cnt = np.unique(tid, return_counts=True); print('edge sightings', len(tid), ' distinct edges', len(ids), ' seen in 12+ frames', (cnt >= 12).sum())
    # drop sightings where something else is in the window (before the edge or after the echo has ended)
    ok = np.ones(len(tid), bool)
    for i in ids[cnt >= 12]:
        m = np.nonzero(tid == i)[0]; med = np.median(cap[m], 0); bad = (np.abs(cap[m] - med)[:, (t <= -3) | (t >= 25)].max(1) > 0.12); ok[m[bad]] = False
    tid2 = np.where(ok, tid, -1)
    for kind, sg in (('rise', 1), ('fall', -1)):
        for name, lo_, hi_ in (('darker side below 0.15 of white', -1, 0.15), ('darker side 0.15-0.6 of white', 0.15, 0.6)):
            keep = []
            for i in ids[cnt >= 12]:
                m = tid2 == i
                if m.sum() < 12 or np.sign(s[m][0]) != sg or dk[m].std() < 0.03: continue
                if not (lo_ <= np.median(dark[m]) < hi_): continue
                keep.append(i)
            if len(keep) < 8: print(f'\n{kind}, {name}: only {len(keep)} edges, skipped'); continue
            n = sum((tid2 == i).sum() for i in keep); span = np.median([np.ptp(dk[tid2 == i]) for i in keep])
            sc, oc, ec, _ = pooled(cap, dk, tid2, keep); sa, oa, ea, _ = pooled(aft, dk, tid2, keep)
            pred = np.array([sum(q[j] * (oc[i - j] if i - j >= 0 else 0.0) for j in range(1, len(q))) for i in range(len(t))])
            m = (t >= 2) & (t <= 24)
            print(f'\n{kind}, {name}: {len(keep)} edges, {n} sightings, median step {np.median(np.abs(s[np.isin(tid2, keep)])):.0f} codes, echo depth moves {span:.2f} within an edge (median)')
            print('  t                          ', t[3:30])
            print('  own edge, captured         ', oc[3:30])
            print('  own edge, after removal    ', oa[3:30])
            print('  follows echo, captured     ', sc[3:30])
            print('     +- (resampled edges)    ', ec[3:30])
            print('  follows echo, model says   ', pred[3:30])
            # the test bar's rise through the SAME frames and the same within-edge regression (bar's own time axis is t=-4..27)
            v = np.load('vbi_luma.npy', mmap_mode='r')[:, 12]; Rb, _, _, idx = M.edges(v); gb = M.gauge(Rb); pos = {int(f): j for j, f in enumerate(idx)}
            rows, dks, tids = [], [], []
            for i in keep:
                for f in k[tid2 == i]:
                    if int(f) in pos: rows.append(Rb[pos[int(f)]]); dks.append(gb[pos[int(f)]]); tids.append(i)
            sb, ob, eb, _ = pooled(np.array(rows), np.array(dks), np.array(tids), [i for i in keep if tids.count(i) >= 8])
            print('  test bar, same frames (t-1) ', sb[0:27]); print('     +-                      ', eb[0:27]); print('  test bar own edge (t-1)    ', ob[0:27])
            print('  follows echo, after removal', sa[3:30])
            print('     +-                      ', ea[3:30])
            print(f'  size of the part that follows the echo, t=2..24 (rms): captured {np.sqrt((sc[m] ** 2).mean()):.3f}, after {np.sqrt((sa[m] ** 2).mean()):.3f}, uncertainty {np.sqrt((ea[m] ** 2).mean()):.3f}; model vs captured mismatch {np.sqrt(((pred - sc)[m] ** 2).mean()):.3f}')
def ka():
    # Known answer: made-up edges, each with its own overshoot, echo of known taps scaled by a drifting depth, noise.
    # The edges' own overshoot is made LARGER where the depth is larger, the content confound a pooled-by-block
    # check cannot tell from echo.  The within-edge slope must return the true echo and the true own edge anyway.
    rng = np.random.default_rng(0); q = np.zeros(28); q[2:14] = [-.1, -.3, -.8, -1.1, -1.0, -.8, -.6, -.4, -.3, -.2, -.1, -.05]
    nE = 60; R, dk, tid, owns, echos = [], [], [], [], []
    for i in range(nE):
        base = 0.35 + 0.4 * i / nE; n = 40; dd = base + 0.08 * np.sin(np.arange(n) / 7 + i) + 0.01 * rng.standard_normal(n)
        over = 0.1 + 0.6 * (base - 0.35)                                 # own overshoot grows with the mean depth
        own = 1 / (1 + np.exp(-(t + 0.0) * 1.6)) + over * np.exp(-((t - 4) / 2.5) ** 2) * (t > 0)
        echo = np.array([sum(q[j] * (own[k - j] if k - j >= 0 else 0.0) for j in range(1, 28)) for k in range(len(t))])
        R.append(own + dd[:, None] * echo + 0.03 * rng.standard_normal((n, len(t)))); dk.append(dd); tid.append(np.full(n, i)); owns.append(own); echos.append(echo)
    R = np.concatenate(R); dk = np.concatenate(dk); tid = np.concatenate(tid)
    slope, own, se, _ = pooled(R, dk, tid, list(range(nE))); m = (t >= 2) & (t <= 24)
    naive = np.linalg.lstsq(np.c_[np.ones(len(dk)), dk], R, rcond=None)[0][1]            # one regression over everything
    print('true echo part (mean)   ', np.mean(echos, 0)[3:30]); print('within-edge slope       ', slope[3:30]); print('one regression over all ', naive[3:30])
    print('rms error t=2..24: within-edge %.3f, one regression over all %.3f; own edge error %.3f' % (np.sqrt(((slope - np.mean(echos, 0))[m] ** 2).mean()), np.sqrt(((naive - np.mean(echos, 0))[m] ** 2).mean()), np.sqrt(((own - np.mean(owns, 0))[m] ** 2).mean())))
if __name__ == '__main__':
    {'find': find, 'fit': fit, 'ka': ka}[sys.argv[1]](*sys.argv[2:])
