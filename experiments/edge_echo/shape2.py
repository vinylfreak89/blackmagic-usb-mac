# What is the fast-moving second shape?  If it is echo, both test lines of a frame (16.7 ms apart) should agree on it and the picture's dip
# should move with it.  If it belongs to the test line (timing at the top of the field), it should follow the line's own position instead.
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import model as M, refit4 as F
np.set_printoptions(linewidth=220, precision=3, suppress=True)
m = F.build(2, 75, 80, 1, verbose=False); tr = m['tr']; cols = np.arange(720)
def lines(vf):
    v = np.load(vf, mmap_mode='r'); n = v.shape[0]; out = np.full((n, 2, 6), np.nan)       # reading, a1, a2, bar column, bar width, top
    for k in range(n):
        for i, j in enumerate((4, 12)):
            y = v[k, j].astype(float) - M.BL; top = np.median(y[560:680])
            if top < 120: continue
            r, c = F.rise(y, top, tr)
            if r is None: continue
            cf = M.cr(y, 0.5 * top, 660, 719, True); a = F.amounts(r, m); out[k, i] = [F.reading(r, tr), a[0], a[1], c, (cf - c) if cf else np.nan, top]
    return out
def cc(x, y):
    ok = np.isfinite(x) & np.isfinite(y); return np.corrcoef(x[ok], y[ok])[0, 1] if ok.sum() > 20 else np.nan
for name, vf, tkf in (('strong passage', 'vbi_luma.npy', 'run_track.npy'), ('weak passage', 'lo_vbi.npy', None)):
    L = lines(vf); g, a1, a2, c, w = [L[..., i] for i in range(5)]
    p = np.polyfit(a1[np.isfinite(a1)], a2[np.isfinite(a1)], 2); f2 = a2 - np.polyval(p, a1)       # the part of amount 2 not tied to amount 1
    print('== %s: amount 2 spread %.3f; left after a smooth curve of amount 1: %.3f' % (name, np.nanstd(a2), np.nanstd(f2)))
    print('   the two test lines of one frame agree on:  reading %.3f   amount 1 %.3f   amount 2 %.3f   fast part of amount 2 %.3f   (correlations)' % (cc(g[:, 0], g[:, 1]), cc(a1[:, 0], a1[:, 1]), cc(a2[:, 0], a2[:, 1]), cc(f2[:, 0], f2[:, 1])))
    print('   same line, next frame:                      reading %.3f   amount 1 %.3f   amount 2 %.3f   fast part of amount 2 %.3f' % (cc(g[:-1, 0], g[1:, 0]), cc(a1[:-1, 0], a1[1:, 0]), cc(a2[:-1, 0], a2[1:, 0]), cc(f2[:-1, 0], f2[1:, 0])))
    for lagf in (5, 15, 30): print('   same line, %2d frames on:                    fast part of amount 2 %.3f' % (lagf, cc(f2[:-lagf, 0], f2[lagf:, 0])))
    print('   fast part of amount 2 against the test line\'s own column %.3f, bar width %.3f, column early by more than 1 sample: mean %.3f (n %d) against %.3f' % (cc(f2.ravel(), c.ravel()), cc(f2.ravel(), w.ravel()), np.nanmean(f2[c < np.nanmedian(c) - 1]), int((c < np.nanmedian(c) - 1).sum()), np.nanmean(f2[c >= np.nanmedian(c) - 1])))
    print('   amount 1 against column %.3f; reading against column %.3f' % (cc(a1.ravel(), c.ravel()), cc(g.ravel(), c.ravel())))
    if tkf:
        tk = np.load(tkf); dip, place = tk[..., 0], tk[..., 1]        # left picture edge: dip depth and place per frame, field, quarter
        for fld in (0, 1):
            pl = np.nanmedian(place[:, fld], 1); dp = np.nanmedian(dip[:, fld], 1); pp = np.polyfit(dp[np.isfinite(dp) & np.isfinite(pl)], pl[np.isfinite(dp) & np.isfinite(pl)], 2); plr = pl - np.polyval(pp, dp)
            print('   field %d: picture dip place against amount 2 of its own test line %.3f; place with its trend in depth taken out against the fast part of amount 2 %.3f; picture dip depth against reading %.3f' % (fld + 1, cc(pl, a2[:, fld]), cc(plr, f2[:, fld]), cc(dp, g[:, fld])))
            print('            picture dip place: spread %.2f samples, left after its trend in depth %.2f; same field next frame agree %.3f' % (np.nanstd(pl), np.nanstd(plr), cc(plr[:-1], plr[1:])))
