# Physics-derived edge detector, run as playback (each field judged only from earlier fields). Every choice traces to a
# measurement in the 2026-09-30 characterization; the ones that are not measured are listed in NOT_MEASURED.
import sys, os, json, struct, csv, numpy as np, time
sys.path.insert(0, os.path.dirname(__file__)); import playback as P
NOT_MEASURED = {'N_WIN': 'window length 30 frames', 'band': 'blanking band top = 99.9th pct of accepted samples 0-2',
                'guard': 'edge guard = 99th pct of line-to-line edge differences of accepted lines', 'band2': 'a band is >= 2 adjacent moved lines',
                'last8': 'last 8 lines out (owner)', 'right_half': 'fall beyond the window = still above half its level at 718 (the edge position is its halfway point)'}
N_WIN = 30; FR = [(19, 262), (282, 525)]
class Win:
    def __init__(s): s.f = []
    def add(s, x): s.f.append(x); s.f = s.f[-N_WIN:]
    def ok(s): return len(s.f) >= 3
    def stats(s):
        b = np.concatenate([x['b'] for x in s.f]); d = np.concatenate([x['d'] for x in s.f]); pr = [x['prof'] for x in s.f if x['prof'] is not None]
        if len(b) < 300 and hasattr(s, 'last'): return s.last
        B, top = float(np.median(b)), float(np.percentile(b, 99.9))
        g = float(np.percentile(np.abs(d), 99)) if len(d) > 200 else (s.last['g'] if hasattr(s, 'last') else 2.0)
        prof = np.median(np.array(pr), 0) if pr else None
        bump = float(prof[:max(3, int(np.argmax(prof > B + 0.5 * (prof.max() - B))) - 2)].max() - B) if prof is not None else 0.0
        s.last = dict(B=B, top=top, g=max(g, 0.5), bump=max(bump, top - B)); return s.last
def edges(Yl, st):
    B, top, bump = st['B'], st['top'], st['bump']; n = len(Yl)
    L = np.full(n, np.nan); R = np.full(n, np.nan); Ls = np.zeros(n, int); Rs = np.zeros(n, int)   # state: 0 edge, 1 none/beyond, 2 unknown
    lvlL = np.median(Yl[:, 40:80], 1) - B; lvlR = np.median(Yl[:, 640:680], 1) - B
    for i, y in enumerate(Yl):
        if (y[0:3] > top).all(): Ls[i] = 1
        elif lvlL[i] <= 2 * bump: Ls[i] = 2                    # step not taller than twice the blanking bump: bump could be the edge
        else:
            t = B + 0.5 * lvlL[i]; k = np.nonzero(y[:150] >= t)[0]
            if not len(k) or k[0] == 0: Ls[i] = 2
            else: k = k[0]; L[i] = k - 1 + (t - y[k - 1]) / (y[k] - y[k - 1])
        if lvlR[i] <= 2 * (top - B): Rs[i] = 2
        elif y[718] - B >= 0.5 * lvlR[i]: Rs[i] = 1
        else:
            t = B + 0.5 * lvlR[i]; k = np.nonzero(y[570:719] >= t)[0]
            if not len(k): Rs[i] = 2
            else: k = 570 + k[-1]; R[i] = k + (y[k] - t) / (y[k] - y[k + 1])
    return L, R, Ls, Rs
def judge(Y, tops, st, win_empty=False):
    res = {'torn': [False, False], 'lines': [[], []]}; acc_b, acc_d = [], []; prof = []
    for fi, (a, b) in enumerate(FR):
        t0 = int(tops[fi]) - 4 if tops[fi] >= 0 else a
        rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
        L, R, Ls, Rs = edges(Yl, st)
        both = (Ls == 0) & (Rs == 0)
        if both.sum() < 20: continue
        mL, mR = np.median(L[both]), np.median(R[both]); dl, dr = L - mL, R - mR; g = st['g']
        pushR = (Rs == 1) & (Ls == 0) & (dl > g)
        pushL = (Ls == 1) & ((Rs == 2) | ((Rs == 0) & (dr < -g)))
        shiftsq = (Ls == 0) & (Rs == 0) & (np.abs(dl) > g) & (np.abs(dr) > g)
        moved = pushR | pushL | shiftsq
        band = moved & (np.r_[False, moved[:-1]] | np.r_[moved[1:], False])
        if band.any():
            res['torn'][fi] = True; res['lines'][fi] = (rows[band] + 4).tolist(); lo, hi = np.nonzero(band)[0][[0, -1]]
            cut = np.zeros(len(rows), bool); cut[lo:hi + 1] = True
        else: cut = np.zeros(len(rows), bool)
        ok = both & ~cut & (np.abs(dl) <= g) & (np.abs(dr) <= g)
        acc_b.append(Yl[ok, 0:3].ravel())
        # line-to-line edge differences of adjacent measured, uncut lines (noise; a content run changes slowly line to line)
        adj = both[1:] & both[:-1] & ~cut[1:] & ~cut[:-1]
        acc_d.append(np.r_[np.diff(L)[adj], np.diff(R)[adj]])
        if ok.sum() > 20: prof.append(np.median(Yl[ok, 0:40], 0))
    fr = dict(b=np.concatenate(acc_b) if acc_b else np.zeros(0), d=np.concatenate(acc_d) if acc_d else np.zeros(0), prof=np.median(prof, 0) if prof else None)
    return res, fr
def warm_frame(Y):
    s = Y[19:516, 0:3].astype(float); p = np.percentile(s, 95)
    b = s[(s <= p).all(1)].ravel(); return dict(b=b, d=np.zeros(0), prof=np.median(Y[60:240, 0:40].astype(float), 0))
def play(frames, tops_of):
    """frames: iterable of (unit, Y) in playback order. tops_of(unit) -> (top1, top2) NTSC lines or -1."""
    W = Win(); out = {}
    for u, Y in frames:
        if not W.ok(): W.add(warm_frame(Y)); continue
        st = W.stats(); res, fr = judge(Y, tops_of(u), st); out[u] = res; W.add(fr)
    return out
