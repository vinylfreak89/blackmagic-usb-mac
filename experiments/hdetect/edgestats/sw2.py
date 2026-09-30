# Field-majority edge rule over per-line stats + end samples, run in tape order (a frame sees only frames before it; lines
# detected torn never enter the window). One change per variant against the baseline (disagree_fm.py, 2026-09-30):
#   field : baseline. blank = 5th pct of the field's samples 0-7; sy = MAD of those within +-3 of blank; an edge is measured
#           when the picture beside it is > 3*sy above blank; half-height crossing; an edge still above half height at
#           sample 0 / 719 is beyond the window (-inf / +inf); majority = field median; margin = max(2, 4*MAD).
#   win   : (A) blank, sy and the reference come from the window instead of the field: the last N frames, lines within
#           +-W of the same height in both fields, detected lines excluded. Everything else unchanged.
#   winB  : A + an edge is measured when the picture beside it clears the window's blanking noise floor: the level that
#           clean blanking samples 0-2 stay under Q of the time (replaces 3*sy).
#   winB1 : A + an edge is measured when the picture beside it is more than the window's blanking noise floor (sy, the
#           robust spread of blanking samples) above blank: 3*sy becomes 1*sy.
#   winK  : like win, but the window at each height holds the last N CLEAN observations there, however old, so a long
#           tear never pushes the clean reference out (win lost long tears once 30 frames of detections emptied it).
#   winKx : winK, but a line with no verdict never enters the window as clean (only a height that has never had a
#           verdict bootstraps from its lines).
#   fmB   : baseline field-majority reference; only blank and sy come from the window (the noise floor measured over
#           the last N frames' clean lines instead of per field).
#   fmB1  : fmB + an edge is measured when the picture beside it is more than sy above blank (3*sy -> 1*sy).
#   winBC : A + B + the departure margin is the window's edge noise floor: the level that clean lines' distance from their
#           own reference stays under Q of the time (replaces max(2, 4*MAD)).
# Both: a line is torn when BOTH edges depart the same direction; a field is torn when >= 2 adjacent lines are; the last 8
# lines of each field are left out. Crossing positions come from the stats (half height from the line's own lowest sample
# 0-7), which differs from the baseline only where that sample is above blanking and sample 0 is below half height.
import numpy as np, warnings
USED = np.r_[0:235, 243:478]
def mad(x): x = np.asarray(x, float); return 1.4826 * float(np.median(np.abs(x - np.median(x)))) if len(x) else 0.0
def hist_stats(h):
    """blank = 5th percentile, sy = MAD of samples within +-3 of blank, from a 256-bin histogram of blanking samples."""
    cs = np.cumsum(h); tot = cs[-1]
    if tot == 0: return np.nan, np.nan
    B = float(np.searchsorted(cs, 0.05 * tot))
    lo, hi = int(max(0, np.ceil(B - 3))), int(min(255, np.floor(B + 3)))
    w = h[lo:hi + 1].astype(float); v = np.arange(lo, hi + 1)
    if w.sum() <= 50: return B, 1.0
    cw = np.cumsum(w); med = v[np.searchsorted(cw, cw[-1] / 2)]
    d = np.abs(v - med); o = np.argsort(d); cd = np.cumsum(w[o]); md = d[o][np.searchsorted(cd, cd[-1] / 2)]
    return B, max(0.5, 1.4826 * float(md))
def edges(m, e, B, sy, gstep=None):
    g = 3 * sy if gstep is None else gstep
    pl, pr = m[:, 2] / 10, m[:, 3] / 10; rise, fall = m[:, 4] / 10, m[:, 5] / 10
    y0, y719 = e[:, 0].astype(float), e[:, 15].astype(float)
    L = np.full(len(m), np.nan); R = np.full(len(m), np.nan)
    okL = (pl - B) > g; hL = B + 0.5 * (pl - B); cr = (m[:, 4] > 0) & (m[:, 4] < 2000)
    L[okL & cr] = rise[okL & cr]
    # a crossing inside samples 0-7 is computed exactly from the samples (at this blank's half height)
    a = e[:, :8].astype(float); ab = a >= hL[:, None]; k = ab.argmax(1); inn = ab.any(1) & (k > 0)
    ya, yb = a[np.arange(len(a)), np.maximum(k - 1, 0)], a[np.arange(len(a)), k]
    L[okL & inn] = ((k - 1) + (hL - ya) / np.maximum(yb - ya, 1e-6))[okL & inn]
    L[okL & (y0 >= hL)] = -np.inf
    okR = (pr - B) > g; hR = B + 0.5 * (pr - B); cf = (m[:, 5] > 5210) & (m[:, 5] < 7190)
    R[okR & cf] = fall[okR & cf]
    z = e[:, 8:].astype(float); zb = z >= hR[:, None]; j = 7 - zb[:, ::-1].argmax(1); inr = zb.any(1) & (j < 7)   # last sample >= h in 712-719
    za, zc = z[np.arange(len(z)), j], z[np.arange(len(z)), np.minimum(j + 1, 7)]
    R[okR & inr] = (712 + j + (za - hR) / np.maximum(za - zc, 1e-6))[okR & inr]
    R[okR & (y719 >= hR)] = np.inf
    return L, R
def judge(L, R, refL, refR, tL, tR, kn):
    with np.errstate(invalid='ignore'):
        dL = np.where(L - refL >= tL, 1, np.where(refL - L >= tL, -1, 0)); dR = np.where(R - refR >= tR, 1, np.where(refR - R >= tR, -1, 0))
    t = (dL != 0) & (dL == dR) & kn; band = np.zeros_like(t)
    for f in (0, 1):
        s = t[f * 235:(f + 1) * 235]; band[f * 235:(f + 1) * 235] = s & (np.r_[False, s[:-1]] | np.r_[s[1:], False])
    return band
def hq(h, q):
    cs = np.cumsum(h); return float(np.searchsorted(cs, q * cs[-1])) if cs[-1] else np.nan
LINES = {}
def run(M, E, variant='field', N=30, W=2, minref=20, Q=0.999, keep_lines=False, top=None):
    """top: (units, 2) registration first picture line per field (NTSC), -1 = unknown -> that field gets no verdict.
    Lines above the top are not judged and do not enter any reference."""
    n = len(M); flags = np.zeros((n, 2), bool); known = np.zeros((n, 2), bool)
    ringL = np.full((N, 470), np.nan); ringR = np.full((N, 470), np.nan); ringH = np.zeros((N, 256), np.int64); ringH3 = np.zeros((N, 256), np.int64); ringD = np.zeros((N, 4096), np.int64); k = 0
    ptrL = np.zeros(470, int); ptrR = np.zeros(470, int); ever = np.zeros(470, bool)
    for u in range(n):
        mfull, efull = M[u], E[u]; m = mfull[USED].astype(np.float64); e = efull[USED]
        if variant in ('field', 'fmB', 'fmB1'):
            if variant != 'field':
                Bw, syw = hist_stats(ringH.sum(0))
            L = np.empty(470); R = np.empty(470); refL = np.full(470, np.nan); refR = np.full(470, np.nan); tL = np.full(470, np.nan); tR = np.full(470, np.nan); kn = np.zeros(470, bool)
            for f in (0, 1):
                s = slice(f * 235, (f + 1) * 235); ef = efull[f * 243:(f + 1) * 243, :8].astype(float)
                B = float(np.percentile(ef, 5)); samp = ef[20:220]; ms = np.abs(samp - B) <= 3
                sy = max(0.5, mad(samp[ms])) if ms.sum() > 50 else 1.0
                if variant != 'field':
                    if not np.isfinite(Bw): L[s] = R[s] = np.nan; continue
                    B, sy = Bw, syw
                L[s], R[s] = edges(m[s], e[s], B, sy, sy if variant == 'fmB1' else None)
                if top is not None and top[u, f] >= 0:                        # lines above the picture enter no reference
                    L[s][:max(0, int(top[u, f]) - (23 if f == 0 else 286))] = np.nan; R[s][:max(0, int(top[u, f]) - (23 if f == 0 else 286))] = np.nan
                fl = L[s][np.isfinite(L[s])]; fr = R[s][np.isfinite(R[s])]
                if len(fl) >= 20 and len(fr) >= 20:
                    refL[s] = np.median(fl); refR[s] = np.median(fr); tL[s] = max(2, 4 * mad(fl)); tR[s] = max(2, 4 * mad(fr)); kn[s] = True
        else:
            B, sy = hist_stats(ringH.sum(0)); gstep = None
            if variant in ('winB', 'winBC') and np.isfinite(B): gstep = hq(ringH3.sum(0), Q) - B
            if variant == 'winB1' and np.isfinite(B): gstep = sy       # the measured noise floor itself, no multiplier
            if np.isfinite(B): L, R = edges(m, e, B, sy, gstep)
            else: L = np.full(470, np.nan); R = np.full(470, np.nan)
            def ref(ring):
                a = ring.reshape(N, 2, 235); cols = []
                for d in range(-W, W + 1):
                    sh = np.full_like(a, np.nan)
                    if d >= 0: sh[:, :, :235 - d] = a[:, :, d:]
                    else: sh[:, :, -d:] = a[:, :, :235 + d]
                    cols.append(sh)
                s = np.concatenate(cols, 0).reshape(-1, 235); cnt = np.isfinite(s).sum(0)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore'); med = np.nanmedian(s, 0); md = 1.4826 * np.nanmedian(np.abs(s - med), 0)
                return np.r_[med, med], np.r_[np.maximum(2, 4 * md)] if False else np.tile(np.maximum(2, 4 * md), 2), np.r_[cnt, cnt]
            refL, tL, cL = ref(ringL); refR, tR, cR = ref(ringR); kn = (cL >= minref) & (cR >= minref)
            if variant == 'winBC':
                g = hq(ringD.sum(0), Q) / 10
                if np.isfinite(g): tL = np.full(470, g); tR = np.full(470, g)
                else: kn[:] = False
        if top is not None:
            for f in (0, 1):
                s = slice(f * 235, (f + 1) * 235); t0 = int(top[u, f])
                if t0 < 0: kn[s] = False; continue
                above = np.arange(235) < t0 - (23 if f == 0 else 286); L[s][above] = np.nan; R[s][above] = np.nan
        band = judge(L, R, refL, refR, tL, tR, kn)
        if keep_lines and band.any(): LINES[u] = [(int(f) + 1, int(h) + (23 if f == 0 else 286)) for f, h in zip((np.arange(470) >= 235)[band], np.r_[0:235, 0:235][band])]
        for f in (0, 1):
            s = slice(f * 235, (f + 1) * 235); flags[u, f] = band[s].any(); known[u, f] = kn[s].any()
        if variant != 'field':
            clean = ~band
            if variant in ('winK', 'winKx'):
                adm = clean if variant == 'winK' else clean & (kn | ~ever)      # winKx: no verdict is never clean
                ever |= kn
                for ring, ptr, X in ((ringL, ptrL, L), (ringR, ptrR, R)):
                    j = np.nonzero(adm & np.isfinite(X))[0]; ring[ptr[j], j] = X[j]; ptr[j] = (ptr[j] + 1) % N
            else:
                ringL[k] = np.where(clean & np.isfinite(L), L, np.nan); ringR[k] = np.where(clean & np.isfinite(R), R, np.nan)
            # blanking samples: samples 0-7 of clean lines whose rise comes after sample 8 (so all eight precede the edge)
            bo = clean & (m[:, 4] >= 80) & (m[:, 4] < 2000)
            ringH[k] = np.bincount(e[bo, :8].ravel(), minlength=256); ringH3[k] = np.bincount(e[bo, :3].ravel(), minlength=256)
            # edge noise floor: clean lines' distance from their reference, in 0.1-sample bins
            dd = np.r_[np.abs(L - refL), np.abs(R - refR)]; dd = dd[np.isfinite(dd) & np.r_[clean & kn, clean & kn]]
            ringD[k] = np.bincount(np.minimum(np.round(dd * 10).astype(int), 4095), minlength=4096)
            k = (k + 1) % N
    return flags, known
