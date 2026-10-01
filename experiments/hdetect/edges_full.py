# generated from phys.edges with the rise/fall search limits (150 / 570) removed - measurement only
import numpy as np
def edges_full(Yl, st):
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
            while k < len(m3) - 1 and m3[k] <= top: k += 1
            if k >= len(m3) - 1: Ls[i] = 2
            else:
                kL[i] = k   # where the line leaves the blanking band
                seg = np.diff(y[max(0, k - 1):k + 16]); j = max(0, k - 1) + int(np.argmax(seg))
                lvl = np.median(y[j + 4:j + 11]) - B; lvL[i] = lvl
                if lvl <= 2 * bump: Ls[i] = 2
                else:
                    t = B + 0.5 * lvl; hit = [x for x in range(max(1, k - 1), min(719, j + 8)) if y[x - 1] < t <= y[x]]
                    if hit: x = hit[0]; L[i] = x - 1 + (t - y[x - 1]) / (y[x] - y[x - 1])
                    else: Ls[i] = 2
        # right
        k = 718
        while k > 2 and m3[k - 2] <= top: k -= 1
        if k <= 2: Rs[i] = 2; continue
        lo = max(0, k - 15); seg = np.diff(y[lo:k + 2]); j = lo + int(np.argmin(seg))
        lvl = np.median(y[max(0, j - 10):max(1, j - 3)]) - B; lvR[i] = lvl
        if lvl <= 2 * (top - B): Rs[i] = 2; continue
        t = B + 0.5 * lvl
        if y[718] - B >= 0.5 * lvl: Rs[i] = 1; continue
        hit = [x for x in range(min(717, k + 1), max(0, j - 8), -1) if y[x] >= t > y[x + 1]]
        if hit: x = hit[0]; R[i] = x + (y[x] - t) / (y[x] - y[x + 1])
        else: Rs[i] = 2
    edges_full.lvR = lvR; edges_full.lvL = lvL; edges_full.kL = kL
    return L, R, Ls, Rs
