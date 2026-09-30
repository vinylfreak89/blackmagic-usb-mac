# Edge rule run over per-line stats in tape order. Field-majority rule of 2026-09-30 (disagree_fm.py) with ONE change per
# variant. A frame is judged only against frames before it; lines detected torn never enter the window.
#   L = left half-height crossing (rise), R = right (fall); an edge whose line still sits above half height at the window
#   edge is censored beyond that end (-inf / +inf). A line is torn when BOTH edges depart the reference in the SAME
#   direction; a field is torn when >= 2 adjacent lines are; the last 8 lines of each field are left out.
# variants:
#   field : baseline on stats. per-field reference (median of the field's lines), blank = 5th pct of the field's bl,
#           sy = median sdL of the field, edge measurable when pl-blank > 3*sy, margin max(2, 4*MAD).
#   win   : reference, blank and sy from the window (last N frames, lines within +-W of the same height, both fields,
#           detected lines excluded). Guards unchanged.
import numpy as np
USED = np.r_[0:235, 243:478]                       # storage rows 19..253 and 282..516 (last 8 of each field out)
FIELD = np.r_[np.zeros(235, int), np.ones(235, int)]
H = np.r_[0:235, 0:235]                             # height within the field
def mad(x, axis=None):
    med = np.nanmedian(x, axis=axis, keepdims=True); return 1.4826 * np.nanmedian(np.abs(x - med), axis=axis)
def edges(m, B, sy, g=3.0):
    bl, br, pl, pr = m[:, 0] / 10, m[:, 1] / 10, m[:, 2] / 10, m[:, 3] / 10
    rise, fall = m[:, 4] / 10, m[:, 5] / 10; sdL = m[:, 7] / 100
    L = np.full(len(m), np.nan); R = np.full(len(m), np.nan)
    okL = (pl - B) > g * sy; hL = B + 0.5 * (pl - B)
    L[okL] = rise[okL]; L[okL & ((bl >= hL) | (m[:, 4] == -10))] = -np.inf; L[okL & (m[:, 4] == 32767)] = np.nan
    okR = (pr - B) > g * sy; hR = B + 0.5 * (pr - B)
    R[okR] = fall[okR]; R[okR & ((br >= hR) | (m[:, 5] == 7200))] = np.inf; R[okR & (m[:, 5] == -32768)] = np.nan
    return L, R
def judge(L, R, refL, refR, tL, tR, known):
    dL = np.where(L - refL >= tL, 1, np.where(refL - L >= tL, -1, 0)); dR = np.where(R - refR >= tR, 1, np.where(refR - R >= tR, -1, 0))
    t = (dL != 0) & (dL == dR) & known
    band = np.zeros_like(t)
    for f in (0, 1):
        s = t[f * 235:(f + 1) * 235]; b = s & (np.r_[False, s[:-1]] | np.r_[s[1:], False]); band[f * 235:(f + 1) * 235] = b
    return band
def run(M, variant='field', N=30, W=2, minref=20):
    """M: (units, 486, 13) int16 stats. Returns flags (units, 2) bool, known (units, 2) bool, lines list per unit."""
    n = len(M); flags = np.zeros((n, 2), bool); known = np.zeros((n, 2), bool); lines = {}
    ringL = np.full((N, 470), np.nan); ringR = np.full((N, 470), np.nan); ringB = np.full((N, 470), np.nan); ringS = np.full((N, 470), np.nan); k = 0
    for u in range(n):
        m = M[u][USED].astype(np.float64)
        if variant == 'field':
            L = np.empty(470); R = np.empty(470); refL = np.empty(470); refR = np.empty(470); tL = np.empty(470); tR = np.empty(470); kn = np.zeros(470, bool)
            for f in (0, 1):
                s = slice(f * 235, (f + 1) * 235); mf = m[s]
                B = np.percentile(mf[:, 0] / 10, 5); sy = max(0.5, float(np.median(mf[:, 7] / 100)))
                L[s], R[s] = edges(mf, B, sy)
                fl = L[s][np.isfinite(L[s])]; fr = R[s][np.isfinite(R[s])]
                if len(fl) >= 20 and len(fr) >= 20:
                    refL[s] = np.median(fl); refR[s] = np.median(fr); tL[s] = max(2, 4 * mad(fl)); tR[s] = max(2, 4 * mad(fr)); kn[s] = True
                else: refL[s] = refR[s] = tL[s] = tR[s] = np.nan
        else:
            B = np.nanmedian(ringB) if np.isfinite(ringB).any() else np.nan; sy = max(0.5, np.nanmedian(ringS)) if np.isfinite(ringS).any() else np.nan
            L, R = edges(m, B, sy) if np.isfinite(B) else (np.full(470, np.nan), np.full(470, np.nan))
            def ref(ring):
                a = ring.reshape(N, 2, 235); cols = []
                for d in range(-W, W + 1):
                    sh = np.full_like(a, np.nan)
                    if d >= 0: sh[:, :, :235 - d] = a[:, :, d:]
                    else: sh[:, :, -d:] = a[:, :, :235 + d]
                    cols.append(sh)
                s = np.concatenate(cols, 0).reshape(-1, 235)
                cnt = np.isfinite(s).sum(0); med = np.nanmedian(s, 0) if cnt.any() else np.full(235, np.nan)
                md = 1.4826 * np.nanmedian(np.abs(s - med), 0) if cnt.any() else np.full(235, np.nan)
                return np.r_[med, med], np.r_[np.maximum(2, 4 * md)] * np.ones(1), np.r_[cnt, cnt]
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                refL, tLh, cL = ref(ringL); refR, tRh, cR = ref(ringR)
            tL = np.r_[tLh, tLh]; tR = np.r_[tRh, tRh]; kn = (cL >= minref) & (cR >= minref)
        band = judge(L, R, refL, refR, tL, tR, kn)
        for f in (0, 1):
            s = slice(f * 235, (f + 1) * 235); flags[u, f] = band[s].any(); known[u, f] = kn[s].any()
        if band.any(): lines[u] = (H[band] + np.where(FIELD[band] == 0, 23, 286)).tolist()
        if variant != 'field':
            clean = ~band
            ringL[k] = np.where(clean & np.isfinite(L), L, np.nan); ringR[k] = np.where(clean & np.isfinite(R), R, np.nan)
            # blanking level and noise: lines that start below their own half height (a real rise inside the window), so
            # samples 0-7 and the samples before the rise are blanking; this needs no prior blanking level (cold start)
            blank_ok = clean & (m[:, 4] > 0) & (m[:, 4] != 32767)
            ringB[k] = np.where(blank_ok, m[:, 0] / 10, np.nan); ringS[k] = np.where(blank_ok & (m[:, 6] >= 3), m[:, 7] / 100, np.nan)
            k = (k + 1) % N
    return flags, known, lines
