# The A->B row offset along the tape, from hard cuts in both live sidecars (rigid-SAD spikes): for each cut in A, the B row is A row + 34
# or 35 (whichever has a matching cut with the same field pattern); isolated single-cut flips are dropped; the offset holds until the
# next cut. Output: ab_offset.npy, one int per A sidecar row. render_ab.py adds the config's b_counter_shift to turn A counters into B counters.
# usage: extract.py <A sidecar> A_live.npz ; extract.py <B sidecar> B_live.npz ; make_offset.py
import numpy as np
Al = np.load('A_live.npz'); Bl = np.load('B_live.npz')
va = np.nan_to_num(Al['v'][:, :2].astype(float)); vb = np.nan_to_num(Bl['v'][:, :2].astype(float))
def cuts(v):
    s = v.max(1); med = np.median(s); mad = np.median(abs(s - med)) + 1e-9; zz = (s - med) / mad
    return [i for i in range(2, len(s) - 2) if zz[i] > 40 and s[i] >= s[i - 1] and s[i] >= s[i + 1] and s[i] > 3 * max(s[i - 2], s[i + 2])]
ca = cuts(va); cb = set(cuts(vb)); pts = []
for i in ca:
    ds = [d for d in (34, 35) if (i + d) in cb and tuple(va[i] > 0.5 * va[i].max()) == tuple(vb[i + d] > 0.5 * vb[i + d].max())]
    if len(ds) == 1: pts.append((i, ds[0]))
clean = [p for k, p in enumerate(pts) if 0 < k < len(pts) - 1 and not (pts[k - 1][1] == pts[k + 1][1] != p[1])]
off = np.full(len(va), 34)
for (i0, d0), (i1, d1) in zip(clean, clean[1:] + [(len(off), clean[-1][1])]): off[i0:i1] = d0
off[:clean[0][0]] = clean[0][1]
np.save('ab_offset.npy', off)
print('cuts A %d, B %d, matched %d, kept %d; offset 34 on %d rows, 35 on %d rows' % (len(ca), len(cb), len(pts), len(clean), int((off == 34).sum()), int((off == 35).sum())))
