# Forward check, no inversion: does (weak line through the fitted system, cut at the floor) reproduce each captured line?
import sys, numpy as np
import sysid as S
np.set_printoptions(linewidth=240, precision=3, suppress=True)
recs, L, G = S.all_lines(); X, XV, VALID = S.X, S.XV, S.VALID; by = {}
for (f, (k, j, l, g, top)) in recs:
    if f == 'vbi_luma.npy': by.setdefault(k, {})[j] = (l, g)
pairs = [d for d in by.values() if len(d) == 2]; bins = [(0.3, 0.45), (0.45, 0.6), (0.6, 0.75), (0.75, 0.9)]
weak = np.nanmedian(L[G < 0.12], 0); D = S.design(weak); N = S.nuisance(weak); Lv = L[:, VALID]
fit = (XV >= -420) & (XV <= 225) & (weak[VALID] > S.FLOOR) & (np.nanpercentile(Lv, 2, axis=0) > S.FLOOR)
ok = ~np.isnan(Lv[:, fit]).any(1); U, s, Vt = np.linalg.svd((Lv - weak[VALID])[ok][:, fit], full_matrices=False)
parts = {k: (XV >= a) & (XV < b) for k, (a, b) in S.PARTS.items()}
for nsh in (2, 3, 4, 6):
    K = np.array([S.solve(D[fit], N[fit], Sh, 1e-2, 1.0) for Sh in Vt[:nsh]]); P = D @ K.T      # each kernel's effect on the weak line, all valid samples
    def amts(l):
        lv = l[VALID]; use = fit & (lv > S.FLOOR) & ~np.isnan(lv); A = np.c_[Vt[:nsh].T[use[fit]], N[use][:, :2]]; return np.linalg.lstsq(A, (lv - weak[VALID])[use], rcond=None)[0]
    for src in ('other field', 'same line'):
        res = {i: [] for i in range(4)}
        for d in pairs:
            lb, gb = d[12]; c = amts(d[4][0] if src == 'other field' else lb); pred = np.maximum(weak[VALID] + P @ c[:nsh], 0)
            for i, (lo, hi) in enumerate(bins):
                if lo <= gb < hi: res[i].append(lb[VALID] - pred)
        row = []
        for i in range(4):
            r = np.array(res[i]); med = np.nanmedian(r, 0); row.append(' '.join('%.3f/%.3f' % (np.sqrt(np.nanmean(med[m] ** 2)), np.sqrt(np.nanmean(r[:, m] ** 2))) for m in parts.values()))
        print('%d shapes, amounts from %-11s | pooled / per-field rms by part (%s):' % (nsh, src, ', '.join(parts))); print('     ' + '\n     '.join('%.2f-%.2f: %s' % (*bins[i], row[i]) for i in range(4)))
print('shares of shapes 1-6:', (s ** 2 / (s ** 2).sum())[:6])
