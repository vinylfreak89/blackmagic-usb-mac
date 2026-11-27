# Does colour need anything?  The 62-minute stretch's colour (p2_uv.npy: frames x 440 x (U, V) x 360) against the echo's strength
# from the test bar (reflect_score.py's three numbers).  Three questions:
#   steady  : a part of the layout that keeps its hue (the blue glow under the picture box; it sweeps, so its size is compared at
#             the same point of the sweep): hue and size by strength
#   edges   : the picture box's borders as colour edges, along the row's own colour direction: a dip or bump after the edge?
#   place   : the right border as a colour edge against the same border in luma, within scenes (so a change of scene does not count):
#             does the colour edge move against the luma edge as the strength changes?
# Run from the scratch directory:   python3 chroma_check.py
import numpy as np
np.set_printoptions(linewidth=250, precision=2, suppress=True)
lum = np.load('p2_luma.npy', mmap_mode='r'); uv = np.load('p2_uv.npy', mmap_mode='r'); par = np.load('reflect_par_p2.npy'); S = np.hypot(par[:, 0], par[:, 1]); ROWS = list(range(15, 170)) + list(range(235, 390))
r = np.array([[(uv[f, 188:214, 0, 12:70].astype(float) - 128).mean(), (uv[f, 188:214, 1, 12:70].astype(float) - 128).mean()] for f in range(900)]); C = np.hypot(r[:, 0], r[:, 1]); hue = np.degrees(np.arctan2(r[:, 1], r[:, 0]))
print('steady colour (blue glow, where its size is over 12):')
for a, b in ((0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0), (1.0, 1.3)):
    s = (S >= a) & (S < b) & (C > 12)
    if s.sum() >= 10: print('   strength %.1f-%.1f (%3d frames): hue %.1f deg' % (a, b, s.sum(), np.median(hue[s])))
pk = [f for f in range(20, 880) if C[f] == C[f - 20:f + 21].max() and C[f] > 30]; print('   peaks of its sweep: ' + ', '.join('frame %d size %.1f at strength %.2f' % (f, C[f], S[f]) for f in pk))
def along(f, r_, ins, seg):
    U = uv[f, r_, 0].astype(float) - 128; V = uv[f, r_, 1].astype(float) - 128; u0, v0 = U[ins].mean(), V[ins].mean(); c0 = np.hypot(u0, v0)
    if c0 < 18 or np.hypot(U[ins] - u0, V[ins] - v0).max() > 0.2 * c0: return None
    return np.r_[(U[seg] * u0 + V[seg] * v0) / c0 ** 2, (-U[seg] * v0 + V[seg] * u0) / c0 ** 2]
print('colour edges at the picture box, level along the colour\'s own direction (1 = inside the picture), every 2nd chroma sample; largest turn of hue at the edge')
for lab, ins, seg, n in (('left border, rising ', slice(14, 26), slice(0, 26), 26), ('right border, falling', slice(205, 217), slice(213, 243), 30)):
    acc = {}
    for f in range(300, 560, 2):
        p = [x for x in (along(f, r_, ins, seg) for r_ in ROWS) if x is not None]
        if len(p) >= 12: acc.setdefault(0 if S[f] < 0.85 else (1 if S[f] < 0.95 else 2), []).append(np.median(p, 0))
    for b, name in ((0, 'under 0.85'), (1, '0.85-0.95'), (2, '0.95 and over')):
        if b in acc and len(acc[b]) >= 5: m = np.median(acc[b], 0); print('   %s, strength %-13s (%3d frames): %s | %.2f' % (lab, name, len(acc[b]), np.round(m[:n:2], 2), np.abs(m[n:]).max()))
def cpos(f):
    P = [x[:35] for x in (along(f, r_, slice(205, 217), slice(210, 245)) for r_ in ROWS) if x is not None]
    if len(P) < 12: return np.nan, np.nan
    m = np.median(P, 0); i = np.arange(210, 245); x = lambda lev: np.interp(lev, m[5:30][::-1], i[5:30][::-1]); return 2 * x(0.5), 2 * (x(0.1) - x(0.9))
def lpos(f):
    pos = []
    for r_ in ROWS:
        v = lum[f, r_, 435:475].astype(float); a, b = np.median(v[:6]), np.median(v[-6:])
        if a - b < 40: continue
        lev = 0.5 * (a + b); i = np.argmax(v <= lev)
        if 0 < i < 39: pos.append(435 + i - 1 + (lev - v[i - 1]) / (v[i] - v[i - 1]))
    return np.median(pos) if len(pos) >= 20 else np.nan
fr = np.arange(300, 560); D = np.array([list(cpos(f)) + [lpos(f)] for f in fr]); ok = ~np.isnan(D).any(1); mot = np.array([np.abs(lum[f, 20:160:4, 20:440:4].astype(float) - lum[f - 1, 20:160:4, 20:440:4].astype(float)).mean() for f in fr]); cut = np.cumsum(mot > 3 * np.median(mot)); x = []; yd = []; yl = []; wd = []
for c in np.unique(cut[ok]):
    s = ok & (cut == c)
    if s.sum() >= 12 and np.ptp(S[fr][s]) >= 0.03: x += list(S[fr][s] - S[fr][s].mean()); yd += list((D[s, 0] - D[s, 2]) - (D[s, 0] - D[s, 2]).mean()); yl += list(D[s, 2] - D[s, 2].mean()); wd.append(np.median(D[s, 1]))
x = np.array(x); sl = lambda y: np.polyfit(x, np.array(y), 1)[0]; se = lambda y: np.std(np.array(y) - sl(y) * x) / (np.std(x) * np.sqrt(len(x)))
print('place, within scenes (%d frames): per 0.1 of strength the colour edge moves %+.2f +- %.2f luma samples against the luma edge (the luma edge itself %+.2f +- %.2f); the colour edge is %.0f-%.0f luma samples wide (10-90%%)' % (len(x), 0.1 * sl(yd), 0.1 * se(yd), 0.1 * sl(yl), 0.1 * se(yl), min(wd), max(wd)))
