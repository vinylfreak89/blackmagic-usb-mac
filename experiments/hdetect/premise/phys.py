# Physics-derived edge detector, run as playback (each field judged only from earlier fields). Every choice traces to a
# measurement in the 2026-09-30 characterization; the ones that are not measured are listed in NOT_MEASURED.
import sys, os, json, struct, csv, numpy as np, time
sys.path.insert(0, os.path.dirname(__file__)); import playback as P
NOT_MEASURED = {'edge_ref_min': 'per-edge reference needs >= 20 measured lines of that edge (the old both-edge count)','avg3': 'sliding average length 3 = the blanking samples a fixture A line provides','N_WIN': 'window length 30 frames', 'band': 'blanking band top = 99.9th pct of accepted samples 0-2',
                'guard': 'edge guard = 99th pct of line-to-line edge differences of accepted lines', 'band2': 'a band is >= 2 adjacent moved lines',
                'last8': 'last 8 lines out (owner)', 'right_half': 'fall beyond the window = still above half its level at 718 (the edge position is its halfway point)',
                'rspec': 'fall-beyond counts as evidence only if the 99th pct of the window normal lines level-at-718 ratio is below one half'}
N_WIN = 30; FR = [(19, 262), (282, 525)]
class Win:
    def __init__(s): s.f = []
    def add(s, x): s.f.append(x); s.f = s.f[-N_WIN:]
    def ok(s): return len(s.f) >= 3
    def stats(s):
        b = np.concatenate([x['b'] for x in s.f]); d = np.concatenate([x['d'] for x in s.f]); pr = [x['prof'] for x in s.f if x['prof'] is not None]
        if len(b) < 300 and hasattr(s, 'last'): return s.last
        b3 = np.concatenate([x['b3'] for x in s.f]) if all('b3' in x for x in s.f) else b
        # change v4: the band is the 3-sample average's band - the walk tests a sliding 3-sample average, not single samples
        B, top = float(np.median(b)), float(np.percentile(b3, 99.9))
        g = float(np.percentile(np.abs(d), 99)) if len(d) > 200 else (s.last['g'] if hasattr(s, 'last') else 2.0)
        prof = np.median(np.array(pr), 0) if pr else None
        bump = float(prof[:max(3, int(np.argmax(prof > B + 0.5 * (prof.max() - B))) - 2)].max() - B) if prof is not None else 0.0
        r7 = np.concatenate([x['r718'] for x in s.f]) if all('r718' in x for x in s.f) else np.zeros(0)
        # change: the right end can show a push only where this source's normal falls finish inside the window
        rspec = bool(len(r7) > 200 and np.percentile(r7, 99) < 0.5) if len(r7) > 200 else (s.last['rspec'] if hasattr(s, 'last') else False)
        s.last = dict(B=B, top=top, g=max(g, 0.5), bump=max(bump, top - B), rspec=rspec); return s.last
def edges(Yl, st):
    """Each edge against its OWN step (C1): left = the steepest rise within 15 samples after the line leaves the blanking
    run that starts at sample 0, halfway between blanking and the level just after it; right = the mirror, from where the
    line enters the blanking run before sample 719 (719 is an attenuated sample, not blanking). An edge whose own step is
    not taller than twice the blanking bump (left) or twice the band (right) is unmeasurable (dark picture)."""
    B, top, bump = st['B'], st['top'], st['bump']; n = len(Yl)
    L = np.full(n, np.nan); R = np.full(n, np.nan); Ls = np.zeros(n, int); Rs = np.zeros(n, int); lvR = np.full(n, np.nan)
    for i, y in enumerate(Yl):
        # left
        m3 = np.convolve(y, np.ones(3) / 3, 'valid')   # m3[k] = mean(y[k:k+3])
        if m3[0] > top: Ls[i] = 1
        else:
            k = 0
            while k < 150 and m3[k] <= top: k += 1
            if k >= 150: Ls[i] = 2
            else:
                seg = np.diff(y[max(0, k - 1):k + 16]); j = max(0, k - 1) + int(np.argmax(seg))
                lvl = np.median(y[j + 4:j + 11]) - B
                if lvl <= 2 * bump: Ls[i] = 2
                else:
                    t = B + 0.5 * lvl; hit = [x for x in range(max(1, k - 1), min(719, j + 8)) if y[x - 1] < t <= y[x]]
                    if hit: x = hit[0]; L[i] = x - 1 + (t - y[x - 1]) / (y[x] - y[x - 1])
                    else: Ls[i] = 2
        # right
        k = 718
        while k > 570 and m3[k - 2] <= top: k -= 1
        if k <= 570: Rs[i] = 2; continue
        lo = max(0, k - 15); seg = np.diff(y[lo:k + 2]); j = lo + int(np.argmin(seg))
        lvl = np.median(y[max(0, j - 10):max(1, j - 3)]) - B; lvR[i] = lvl
        if lvl <= 2 * (top - B): Rs[i] = 2; continue
        t = B + 0.5 * lvl
        if y[718] - B >= 0.5 * lvl: Rs[i] = 1; continue
        hit = [x for x in range(min(717, k + 1), max(0, j - 8), -1) if y[x] >= t > y[x + 1]]
        if hit: x = hit[0]; R[i] = x + (y[x] - t) / (y[x] - y[x + 1])
        else: Rs[i] = 2
    edges.lvR = lvR
    return L, R, Ls, Rs
def judge(Y, tops, st, win_empty=False):
    res = {'torn': [False, False], 'lines': [[], []]}; acc_b, acc_d, acc_b3 = [], [], []; prof = []; acc_r = []
    for fi, (a, b) in enumerate(FR):
        t0 = int(tops[fi]) - 4 if tops[fi] >= 0 else a
        rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
        L, R, Ls, Rs = edges(Yl, st)
        both = (Ls == 0) & (Rs == 0)
        # change v5: each edge's reference from the lines where THAT edge is measured (a black scene can leave the left
        # unmeasurable while the right is measured on every line); window statistics keep their old both-edge gate
        mL = np.median(L[Ls == 0]) if (Ls == 0).sum() >= 20 else np.nan; mR = np.median(R[Rs == 0]) if (Rs == 0).sum() >= 20 else np.nan
        if np.isnan(mL) and np.isnan(mR): continue
        dl, dr = L - mL, R - mR; g = st['g']
        pushR = (Rs == 1) & (Ls == 0) & (dl > g) & st['rspec']
        pushL = (Ls == 1) & ((Rs == 2) | ((Rs == 0) & (dr < -g)))
        shiftsq = (Ls == 0) & (Rs == 0) & (np.abs(dl) > g) & (np.abs(dr) > g)
        moved = pushR | pushL | shiftsq
        band = moved & (np.r_[False, moved[:-1]] | np.r_[moved[1:], False])
        if band.any():
            res['torn'][fi] = True; res['lines'][fi] = (rows[band] + 4).tolist(); lo, hi = np.nonzero(band)[0][[0, -1]]
            cut = np.zeros(len(rows), bool); cut[lo:hi + 1] = True
        else: cut = np.zeros(len(rows), bool)
        if both.sum() < 20: continue   # statistics: same fields as before the per-edge reference
        ok = both & ~cut & (np.abs(dl) <= g) & (np.abs(dr) <= g)
        acc_b.append(Yl[ok, 0:3].ravel()); acc_b3.append(Yl[ok, 0:3].mean(1))
        lvR = edges.lvR; nl = (Ls == 0) & ~cut & (np.abs(dl) <= g) & np.isfinite(lvR) & (lvR > 2 * (st['top'] - st['B']))
        acc_r.append((Yl[nl, 718] - st['B']) / lvR[nl])
        # line-to-line edge differences of adjacent measured, uncut lines (noise; a content run changes slowly line to line)
        adj = both[1:] & both[:-1] & ~cut[1:] & ~cut[:-1]
        acc_d.append(np.r_[np.diff(L)[adj], np.diff(R)[adj]])
        if ok.sum() > 20: prof.append(np.median(Yl[ok, 0:40], 0))
    fr = dict(b3=np.concatenate(acc_b3) if acc_b3 else np.zeros(0), b=np.concatenate(acc_b) if acc_b else np.zeros(0), d=np.concatenate(acc_d) if acc_d else np.zeros(0), prof=np.median(prof, 0) if prof else None, r718=np.concatenate(acc_r) if acc_r else np.zeros(0))
    return res, fr
def warm_frame(Y):
    s = Y[19:516, 0:3].astype(float); p = np.percentile(s, 95)
    keep = s[(s <= p).all(1)]; b = keep.ravel(); return dict(b3=keep.mean(1), b=b, d=np.zeros(0), prof=np.median(Y[60:240, 0:40].astype(float), 0), r718=np.zeros(0))
def play(frames, tops_of):
    """frames: iterable of (unit, Y) in playback order. tops_of(unit) -> (top1, top2) NTSC lines or -1."""
    W = Win(); out = {}
    for u, Y in frames:
        if not W.ok(): W.add(warm_frame(Y)); continue
        st = W.stats(); res, fr = judge(Y, tops_of(u), st); out[u] = res; W.add(fr)
    return out
