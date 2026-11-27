# Regression check of a rendered 62-minute stretch against the capture and against a reference render (the sixth clip's removal):
# every defect fixed on the way must stay fixed.  Layout constants are this stretch's (picture box border at col 455, caption card
# from col 470, the wall after the left border at frames 420-446, the last title card from frame 650).
#   python3 regress.py LUMA.npy NEW_removed.npy REF_removed.npy NEW_TAPS.npz REF_TAPS.npz PAR.npy [REF_MEAN]
#   REF_MEAN: the reference used a flat mean of this many frames of its taps (5 for the sixth clip); the new taps are used as they are.
import sys, numpy as np
import gate as G, harness as H
from scipy.ndimage import maximum_filter1d, minimum_filter1d
np.set_printoptions(linewidth=250, precision=2, suppress=True)
lumf, newf, reff, tnew, tref, parf = sys.argv[1:7]; rm = int(sys.argv[7]) if len(sys.argv) > 7 else 5
lum = np.load(lumf, mmap_mode='r'); N = np.load(newf, mmap_mode='r'); R = np.load(reff, mmap_mode='r'); S = np.hypot(*np.load(parf)[:, :2].T); w = G.trade_weight(S); on = w == 1; fl_ = lambda a, f: a[f].astype(float)
def line(lab, cap, ref, new, note=''): print('  %-66s captured %-12s reference %-12s new %-12s %s' % (lab, cap, ref, new, note))
print('removal: none in %d frames, part in %d, on in %d' % ((w == 0).sum(), ((w > 0) & (w < 1)).sum(), on.sum()))
# 1. the diagonal 393 kHz bands and anything else added on flat picture
def sm(v): return np.concatenate([G.box(G.box(v[a:b], 5, 1), 3, 0) for a, b in ((0, 220), (220, v.shape[0]))])
t393 = {'c': [], 'r': [], 'n': []}; add = {'r': [], 'n': []}
n96 = np.arange(96); DT = lambda v: v - np.polyval(np.polyfit(n96, v, 2), n96); EX = np.exp(-2j * np.pi * 0.393 / 13.5 * n96) * np.hanning(96) / np.hanning(96).sum() * 2
for f in range(0, 900, 9):
    if not on[f]: continue
    y = fl_(lum, f); s = sm(y); flat = maximum_filter1d((maximum_filter1d(s, 48, axis=1) - minimum_filter1d(s, 48, axis=1) < 3).astype(np.uint8), 48, axis=1) > 0; flat &= y > 6; flat[:, :30] = False; flat[:, 690:] = False
    for k, a in (('r', R), ('n', N)): add[k].append(np.abs(sm(fl_(a, f) - y)[flat]))
    for r in range(4, 436, 3):                       # 96-sample stretches of bright, flat picture (detrended spread under 2 codes): the 393 kHz tone's amplitude
        for c in range(40, 680 - 96, 48):
            seg = y[r, c:c + 96]
            if seg.mean() > 30 and DT(seg).std() < 2.0:
                for k, a in (('c', lum), ('r', R), ('n', N)): t393[k].append(abs((DT(fl_(a, f)[r, c:c + 96]) * EX).sum()))
print('flat picture (frames with the removal on)')
line('393 kHz amplitude in flat stretches, codes (rms of %d)' % len(t393['c']), *['%.2f' % np.sqrt(np.mean(np.array(t393[k]) ** 2)) for k in 'crn'])
ar, an = np.concatenate(add['r']), np.concatenate(add['n']); line('added where the capture is flat, codes rms | 1 sample in 1000', '-', '%.3f | %.1f' % (np.sqrt((ar ** 2).mean()), np.percentile(ar, 99.9)), '%.3f | %.1f' % (np.sqrt((an ** 2).mean()), np.percentile(an, 99.9)))
ml = lambda a: np.mean([abs((fl_(a, f) - fl_(lum, f)).mean()) for f in range(0, 900, 15)]); line('mean level of a frame moved by, codes', '-', '%.3f' % ml(R), '%.3f' % ml(N))
# 2. moving vertical bands
det = lambda v: v - np.polyval(np.polyfit(np.arange(len(v)), v, 2), np.arange(len(v))); wl = lambda a: [np.sqrt((det(fl_(a, f)[20:60, 32:112].mean(0)) ** 2).mean()) for f in range(420, 447, 2)]
print('moving vertical bands'); line('wall after the left border, 14-15 s, ripple codes rms: median | worst', '%.1f | %.1f' % (np.median(wl(lum)), np.max(wl(lum))), '%.1f | %.1f' % (np.median(wl(R)), np.max(wl(R))), '%.1f | %.1f' % (np.median(wl(N)), np.max(wl(N))))
ch = lambda a, r, cut: np.median(np.sqrt((np.diff(np.array([cut(fl_(a, f)) for f in r]), axis=0) ** 2).mean(1))); card = lambda y: y[20:200, 470:700].mean(0); title = lambda y: y[55:115, 30:450].mean(0)
for lab, r in (('still caption card, change frame to frame, 10.0-20.7 s', range(300, 620)), ('still caption card, 21.7-25.4 s (last title card)', range(650, 760))): line(lab, '%.2f' % ch(lum, r, card), '%.2f' % ch(R, r, card), '%.2f' % ch(N, r, card))
line('title lettering rows, same down the rows, change frame to frame, 21.7-25.4 s', '%.2f' % ch(lum, range(650, 760), title), '%.2f' % ch(R, range(650, 760), title), '%.2f' % ch(N, range(650, 760), title))
# 3. rising picture edges: ghost removal, level after the edge, ripple far after the edge
z = np.load('p2_tracks.npz'); meta, cap = z['meta'], z['prof'].astype(float); k = meta[:, 1].astype(int); use = (k % 2 == 0) & (meta[:, 2].astype(int) % 2 == 1); meta, cap, k = meta[use], cap[use], k[use]; T = H.T; rr = np.zeros_like(cap); rn = np.zeros_like(cap)
for f in np.unique(k):
    xa = fl_(R, f) - 1.5; xb = fl_(N, f) - 1.5
    for i in np.nonzero(k == f)[0]: _, _, r, p_, c = meta[i]; rr[i] = np.interp(c + T, H.COLS, xa[int(r)]) / p_; rn[i] = np.interp(c + T, H.COLS, xb[int(r)]) / p_
seg = (T >= 22) & (T <= 92); rip = lambda v: np.ptp(v[seg] - np.polyval(np.polyfit(T[seg], v[seg], 1), T[seg])); Sk = S[k]; t6, t8, t40, t60 = [np.nonzero(T == t)[0][0] for t in (6, 8, 40, 60)]
print('rising picture edges (frames with the removal on): level at +6 / +8 (the ghost\'s dip; 1.0 = none), at +40 / +60 (level after the edge), ripple +22..+92')
for a_, b_ in ((0, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)):
    s = (Sk >= a_) & (Sk < b_) & on[k]
    if s.sum() < 150: continue
    f_ = lambda P: (lambda m: '%.2f/%.2f %.2f/%.2f %.3f' % (m[t6], m[t8], m[t40], m[t60], rip(m)))(np.median(P[s], 0)); line('reflection strength %.1f-%.1f (%d edges)' % (a_, b_, s.sum()), f_(cap), f_(rr), f_(rn))
# 4. around the moment the paths trade places; smoothness in time
same = [f for f in range(900) if np.array_equal(N[f], lum[f])]; print('around the trade: new render identical to the capture in frames %d-%d (%d frames); reference: %d frames' % (min(same), max(same), len(same), sum(np.array_equal(R[f], lum[f]) for f in range(500, 660))))
Qn = np.load(tnew)['Q']; Qr = np.load(tref)['Q']; Qr = np.array([Qr[max(0, f - rm // 2):f + rm // 2 + 1].mean(0) for f in range(len(Qr))]); dq = lambda Q: np.sqrt((np.diff(Q[:, 1:30], axis=0) ** 2).sum(1))
print('smooth in time'); line('echo taps as used, change from one frame to the next: median | largest', '-', '%.4f | %.3f' % (np.median(dq(Qr)), dq(Qr).max()), '%.4f | %.3f' % (np.median(dq(Qn)), dq(Qn).max()))
line('amount applied around the trade, largest change in one frame (0..1)', '-', '-', '%.3f' % np.abs(np.diff(w)).max())
