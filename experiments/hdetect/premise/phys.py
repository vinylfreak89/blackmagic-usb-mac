# Physics-derived edge detector, run as playback (each field judged only from earlier fields). Every choice traces to a
# measurement in the 2026-09-30 characterization; the ones that are not measured are listed in NOT_MEASURED.
import sys, os, json, struct, csv, numpy as np, time
sys.path.insert(0, os.path.dirname(__file__)); import playback as P
NOT_MEASURED = {'level_fit': 'level reference fitted only with >= 20 lines within g of the flat median spanning >= 20 codes (p10-p90); else flat median','edge_ref_min': 'per-edge reference needs >= 20 measured lines of that edge (the old both-edge count)','avg3': 'sliding average length 3 = the blanking samples a fixture A line provides','N_WIN': 'window length 30 frames', 'band': 'blanking band top = 99.9th pct of accepted samples 0-2',
                'guard': 'edge guard = 99th pct of line-to-line edge differences of accepted lines', 'band2': 'a band is >= 2 adjacent moved lines',
                'switch': 'judged region ends above the measured head-switch line (see switch_line); held when unmeasured; field unjudged before any measurement', 'right_half': 'fall beyond the window = still above half its level at 718 (the edge position is its halfway point)',
                'rspec': 'fall-beyond counts as evidence only if the 99th pct of the window normal lines level-at-718 ratio is below one half'}
FIT = []; N_WIN = 30; FR = [(19, 262), (282, 525)]
class Win:
    def __init__(s): s.f = []; s.sw = [None, None]; s.sw_held = [0, 0]   # head-switch line per field (held when unmeasured)
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
        s.last = dict(B=B, top=top, g=max(g, 0.5), bump=max(bump, top - B), rspec=rspec, sw=s.sw, sw_held=s.sw_held); return s.last
def edges(Yl, st):
    """Each edge against its OWN step (C1): left = the steepest rise within 15 samples after the line leaves the blanking
    run that starts at sample 0, halfway between blanking and the level just after it; right = the mirror, from where the
    line enters the blanking run before sample 719 (719 is an attenuated sample, not blanking). An edge whose own step is
    not taller than twice the blanking bump (left) or twice the band (right) is unmeasurable (dark picture)."""
    B, top, bump = st['B'], st['top'], st['bump']; n = len(Yl)
    L = np.full(n, np.nan); R = np.full(n, np.nan); Ls = np.zeros(n, int); Rs = np.zeros(n, int); lvR = np.full(n, np.nan); lvL = np.full(n, np.nan); kL = np.full(n, np.nan)
    for i, y in enumerate(Yl):
        # left
        m3 = np.convolve(y, np.ones(3) / 3, 'valid')   # m3[k] = mean(y[k:k+3])
        if m3[0] > top: Ls[i] = 1
        else:
            k = 0
            while k < 150 and m3[k] <= top: k += 1
            if k >= 150: Ls[i] = 2
            else:
                kL[i] = k   # where the line leaves the blanking band (first 3-sample mean above it)
                seg = np.diff(y[max(0, k - 1):k + 16]); j = max(0, k - 1) + int(np.argmax(seg))
                lvl = np.median(y[j + 4:j + 11]) - B; lvL[i] = lvl
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
    edges.lvR = lvR; edges.lvL = lvL; edges.kL = kL
    return L, R, Ls, Rs
SWR = [(19, 263), (282, 525)]   # whole field incl. trailing rows; device padding is found by content, not position
def switch_line(Y, fr_, r0, st):
    # Head switch = start of the run, ending at the field's last non-padding row, of lines departing from the field's reference
    # beyond the guard (picture at sample 0, a measured edge beyond g, or a fall past the window on sources whose normal falls end
    # inside it), near-blank lines allowed inside the run; the run starts on a departed line. Padding = luma constant across the
    # row. Edges measured with no search limit (edges_full, generated from edges). Measured 2026-09-30, scratchpad switch2b.
    from edges_full import edges_full
    a, b = fr_; last = b - 1
    while last > a and Y[last].min() == Y[last].max(): last -= 1
    mid = np.arange(r0, last - 40); Lm, Rm, Lsm, Rsm = edges_full(Y[mid].astype(float), st)
    mL = np.median(Lm[Lsm == 0]) if (Lsm == 0).sum() >= 20 else np.nan; mR = np.median(Rm[Rsm == 0]) if (Rsm == 0).sum() >= 20 else np.nan
    if np.isnan(mL) and np.isnan(mR): return None
    rows = np.arange(last - 40, last + 1); L, R, Ls, Rs = edges_full(Y[rows].astype(float), st); g = st['g']
    lv = np.median(Y[rows][:, 100:620].astype(float), 1) - st['B']
    dep = (Ls == 1) | ((Ls == 0) & (np.abs(L - mL) > g)) | ((Rs == 0) & (np.abs(R - mR) > g)) | ((Rs == 1) & st['rspec'])
    ok = dep | ((Ls == 2) & (Rs == 2)) | (lv <= 2 * (st['top'] - st['B'])); i = len(rows)
    while i > 0 and ok[i - 1]: i -= 1
    while i < len(rows) and not dep[i]: i += 1
    return int(rows[i] + 4) if i < len(rows) else None
def judge(Y, tops, st, win_empty=False):
    res = {'torn': [False, False], 'lines': [[], []], 'nosw': [False, False], 'swheld': [False, False]}; acc_b, acc_d, acc_b3 = [], [], []; prof = []; acc_r = []
    for fi, (a, b) in enumerate(FR):
        t0 = int(tops[fi]) - 4 if tops[fi] >= 0 else a
        # change v10: the judged region ends above this field's measured head-switch line (the line in which the head switches),
        # not a fixed 8 lines from the field end (that number was the agent's, not the owner's)
        sw = switch_line(Y, SWR[fi], max(a, t0), st)
        if sw is not None: st['sw'][fi] = sw
        elif st['sw'][fi] is not None: st['sw_held'][fi] += 1; res['swheld'][fi] = True
        if st['sw'][fi] is None: res['nosw'][fi] = True; continue
        rows = np.arange(max(a, t0), st['sw'][fi] - 4); Yl = Y[rows].astype(float)
        L, R, Ls, Rs = edges(Yl, st)
        both = (Ls == 0) & (Rs == 0)
        # change v5: each edge's reference from the lines where THAT edge is measured (a black scene can leave the left
        # unmeasurable while the right is measured on every line); window statistics keep their old both-edge gate
        mL = np.median(L[Ls == 0]) if (Ls == 0).sum() >= 20 else np.nan; mR = np.median(R[Rs == 0]) if (Rs == 0).sum() >= 20 else np.nan
        if np.isnan(mL) and np.isnan(mR): continue
        g = st['g']; lvL, lvR0 = edges.lvL.copy(), edges.lvR.copy()
        # change v6: each line's expected edge follows its own step height (C2: brighter edges land later), a straight-line
        # fit over this field's measured lines that sit within the guard of the flat median; flat median if under-determined
        def fit(E, S, lv, m0):
            # returns a predictor lv -> expected edge (level fit, or the flat median when under-determined)
            if np.isnan(m0): return lambda v: np.full(len(v), np.nan)
            sel = (S == 0) & np.isfinite(lv) & (np.abs(E - m0) <= g)
            if sel.sum() >= 20 and np.percentile(lv[sel], 90) - np.percentile(lv[sel], 10) >= 20:
                b, a = np.polyfit(lv[sel], E[sel], 1)
                return lambda v: np.where(np.isfinite(a + b * v), a + b * v, m0)
            return lambda v: np.full(len(v), m0)
        fL, fR = fit(L, Ls, lvL, mL), fit(R, Rs, lvR0, mR)
        # change v12: a late rise counts as a push right on its own (without rspec) when the line LEAVES the blanking band late -
        # blanking extends up to the rise. Dark content beside the edge sits above the band, so that line leaves it at the normal
        # place and only its halfway point is late; it does not pass.
        kL0 = edges.kL.copy(); kref = np.median(kL0[(Ls == 0) & np.isfinite(kL0)]) if ((Ls == 0) & np.isfinite(kL0)).sum() >= 20 else np.nan
        lateK = np.isfinite(kL0) & (kL0 - kref > g)
        dl, dr = L - fL(lvL), R - fR(lvR0)
        pushR = (Rs == 1) & (Ls == 0) & (dl > g) & (st['rspec'] | lateK)
        pushL = (Ls == 1) & ((Rs == 2) | ((Rs == 0) & (dr < -g)))
        shiftsq = (Ls == 0) & (Rs == 0) & (np.abs(dl) > g) & (np.abs(dr) > g)
        moved = pushR | pushL | shiftsq
        # change v11: lines between the aperture start and registration's measured top are also TESTED when they carry the
        # torn-line signature - a single rise (once the 3-sample average leaves the blanking band it does not return to it before
        # the final fall; caption data returns between bits) to picture height (own step, or level with picture at sample 0,
        # above the detector's measurable floor 2 x bump; a dark line has none). Reference and statistics stay below the top.
        xr = np.arange(a, rows[0]) if rows[0] > a else np.zeros(0, int); xm = np.zeros(len(xr), bool)
        if len(xr):
            Lx, Rx, Lsx, Rsx = edges(Y[xr].astype(float), st); lvLx, lvRx = edges.lvL.copy(), edges.lvR.copy(); floor = 2 * st['bump']
            lateKx = np.isfinite(edges.kL) & (edges.kL - kref > g)
            for i, r in enumerate(xr):
                m3 = np.convolve(Y[r].astype(float), np.ones(3) / 3, 'valid'); up = np.nonzero(m3 > st['top'])[0]
                single = len(up) > 0 and bool((m3[up[0]:up[-1] + 1] > st['top']).all())
                tall = (Lsx[i] == 0 and lvLx[i] > floor) or (Lsx[i] == 1 and np.median(Y[r, 40:680]) - st['B'] > floor)
                xm[i] = single and tall
            dlx, drx = Lx - fL(lvLx), Rx - fR(lvRx)
            movx = ((Rsx == 1) & (Lsx == 0) & (dlx > g) & (st['rspec'] | lateKx)) | ((Lsx == 1) & ((Rsx == 2) | ((Rsx == 0) & (drx < -g)))) | \
                   ((Lsx == 0) & (Rsx == 0) & (np.abs(dlx) > g) & (np.abs(drx) > g))
            xm &= movx
        # band over tested lines in raster order: extra lines above the top, then the judged lines
        allr = np.r_[xr, rows]; allm = np.r_[xm, moved]
        nb = np.r_[False, (allm[:-1] & (np.diff(allr) == 1))] | np.r_[(allm[1:] & (np.diff(allr) == 1)), False]
        bandall = allm & nb; band = bandall[len(xr):]
        if bandall.any():
            res['torn'][fi] = True; res['lines'][fi] = (allr[bandall] + 4).tolist()
            if band.any(): lo, hi = np.nonzero(band)[0][[0, -1]]; cut = np.zeros(len(rows), bool); cut[lo:hi + 1] = True
            else: cut = np.zeros(len(rows), bool)
            if bandall[:len(xr)].any(): res.setdefault('above_top', [[], []])[fi] = (xr[bandall[:len(xr)]] + 4).tolist()
        else: cut = np.zeros(len(rows), bool)
        if both.sum() < 20: continue   # statistics: same fields as before the per-edge reference
        ok = both & ~cut & (np.abs(dl) <= g) & (np.abs(dr) <= g)
        acc_b.append(Yl[ok, 0:3].ravel()); acc_b3.append(Yl[ok, 0:3].mean(1))
        lvR = lvR0; nl = (Ls == 0) & ~cut & (np.abs(dl) <= g) & np.isfinite(lvR) & (lvR > 2 * (st['top'] - st['B']))
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
