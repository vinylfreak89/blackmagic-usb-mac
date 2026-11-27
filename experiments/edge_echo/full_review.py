# One-off, whole capture: what the table (full_table.py) says before any picture is rendered from it.
#   python3 full_review.py TABLE.npz [MEASDIR P2_VBI.npy P2_CTR.npy P2_TAPS.npz P2_PAR.npy OUT_PREFIX]
# Prints, by stretches of the capture: the reflection's strength, the frames where nothing is removed (trade, no test bar), how
# much the picture's own edges had to say, how deep the cancelled band is, and every run of frames at strength 1.0 or more.
# With the approved 62-minute stretch's arrays: finds that stretch in the table by its unit counters, checks that the measuring
# pass read the same test-signal rows, compares the whole-capture taps and weights with the approved ones, and writes the
# stretch's rows as OUT_PREFIX_taps.npz / _par.npy (gate.py remove's inputs) for the regression check.
import sys, numpy as np
import gate as G
np.set_printoptions(linewidth=250, precision=3, suppress=True)
t = np.load(sys.argv[1]); Q, w, S, A, cnt, pw, wb = t['Q'], t['w'], t['S'], t['A'], t['cnt'], t['pw'], t['wbar']; n = len(w); sec = np.arange(n) * 1001 / 30000.0
ctr = t['ctr']; d = np.diff(ctr) % 65536; print('%d units (%.1f min); counter steps not 1: %d %s' % (n, sec[-1] / 60, int((d != 1).sum()), [(int(i), int(x)) for i, x in zip(np.nonzero(d != 1)[0][:12], d[d != 1][:12])]))
hmin = np.array([np.abs(1 + G.spec(Q[k]))[G.BAND].min() for k in range(0, n, 10)]); dq = np.abs(np.diff(Q, axis=0)).max(1)
print('taps: change from one frame to the next (largest tap): median %.4f, 99.9%% %.4f, largest %.4f; picture left at the deepest point of the cancelled band: 5%% %.3f, median %.3f, 95%% %.3f' % (np.median(dq), np.percentile(dq, 99.9), dq.max(), *np.percentile(hmin, [5, 50, 95])))
print('minutes   strength 5%/median/95%   at 1.0+   removal: none  part   no bar   left edges per frame (median)   weight of the picture\'s correction (median)   deepest point (median)')
step = 4 * 60
for a in np.arange(0, sec[-1], step):
    k = (sec >= a) & (sec < a + step); kk = np.nonzero(k)[0]
    print('  %2d-%2d    %.2f  %.2f  %.2f      %5d        %5d  %5d   %5d     %4d                             %.2f                                        %.3f' % (a / 60, min(a + step, sec[-1]) / 60, *np.percentile(S[k], [5, 50, 95]), int((S[k] >= 1).sum()), int((w[k] == 0).sum()), int(((w[k] > 0) & (w[k] < 1)).sum()), int(A[k, 2].sum()), np.median(cnt[k]), np.median(pw[k]), np.median(hmin[kk[0] // 10:kk[-1] // 10 + 1])))
hot = S >= 1.0; edges = np.diff(np.r_[0, hot.astype(int), 0]); st = np.nonzero(edges == 1)[0]; en = np.nonzero(edges == -1)[0]; ln = en - st
print('runs at strength 1.0 or more: %d (frames in them %d); lasting 1 frame: %d, 2-5: %d, 6-30: %d, longer: %d' % (len(st), int(hot.sum()), int((ln == 1).sum()), int(((ln >= 2) & (ln <= 5)).sum()), int(((ln >= 6) & (ln <= 30)).sum()), int((ln > 30).sum())))
for a, l in list(zip(st, ln))[:60]: print('   %2d:%05.2f  %4d frames, largest strength %.2f' % (sec[a] // 60, sec[a] % 60, l, S[a:a + l].max()))
off = w == 0; e2 = np.diff(np.r_[0, off.astype(int), 0]); s2 = np.nonzero(e2 == 1)[0]; l2 = np.nonzero(e2 == -1)[0] - s2
print('stretches with no removal: %d, in all %.1f s (%.2f%% of the capture); removal in part: %.1f s; no test bar nearby: %.1f s' % (len(s2), off.sum() * 1001 / 30000, 100 * off.mean(), ((w > 0) & (w < 1)).sum() * 1001 / 30000, (wb == 0).sum() * 1001 / 30000))
if len(sys.argv) > 2:
    measdir, vbif, ctrf, tapf, parf, outp = sys.argv[2:8]; pc = np.load(ctrf); m = len(pc); cand = np.nonzero(ctr == pc[0])[0]; hit = [c for c in cand if c + m <= n and np.array_equal(ctr[c:c + m], pc)]
    print('the approved stretch (unit counters %d..%d): found at table rows %s' % (pc[0], pc[-1], hit))
    v = np.load(measdir + '/vbi.npy', mmap_mode='r'); pv = np.load(vbif, mmap_mode='r'); same = [c for c in hit if np.array_equal(v[c:c + m], pv)]; c = same[0]; print('   test-signal rows identical to the experiment\'s: rows %d..%d (%d:%04.1f into the capture)' % (c, c + m - 1, sec[c] // 60, sec[c] % 60))
    g = np.load(tapf); par = np.load(parf); S0 = np.hypot(par[:, 0], par[:, 1]); w0 = G.trade_weight(S0); q0, q1 = g['Q'], Q[c:c + m]
    print('   strength: largest difference %.4f; frames at 1.0+: approved %d, whole capture %d; weights: largest difference %.3f, frames that differ by more than 0.01: %d' % (np.abs(S[c:c + m] - S0).max(), int((S0 >= 1).sum()), int((S[c:c + m] >= 1).sum()), np.abs(w[c:c + m] - w0).max(), int((np.abs(w[c:c + m] - w0) > 0.01).sum())))
    dd = q1 - q0; print('   taps, whole capture against approved: rms difference %.4f (rms of the taps %.4f), largest %.4f; per frame the largest tap difference: median %.4f, 95%% %.4f' % (np.sqrt((dd ** 2).mean()), np.sqrt((q0 ** 2).mean()), np.abs(dd).max(), np.median(np.abs(dd).max(1)), np.percentile(np.abs(dd).max(1), 95)))
    h0 = np.array([np.abs(1 + G.spec(q))[G.BAND].min() for q in q0[::5]]); h1 = np.array([np.abs(1 + G.spec(q))[G.BAND].min() for q in q1[::5]]); print('   deepest point of the cancelled band: approved median %.3f, whole capture median %.3f; largest difference %.3f' % (np.median(h0), np.median(h1), np.abs(h1 - h0).max()))
    np.savez(outp + '_taps.npz', Q=q1, direct=t['pw'][c:c + m] > 0.5, weight=t['pw'][c:c + m]); np.save(outp + '_par.npy', t['par'][c:c + m]); np.save(outp + '_am.npy', A[c:c + m]); print('   written: %s_taps.npz, _par.npy, _am.npy' % outp)
