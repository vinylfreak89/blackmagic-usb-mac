# Per-line horizontal-blanking reference points, from each line alone.
# A line's captured window shows at most the two ends of its blanking: a run at blanking level from x=0 that ends
# where picture rises (its start of picture), and/or a run at blanking level that begins where picture falls and
# reaches x=719 (its end of picture). Blanking sits far below the darkest picture (black with setup), so it is found
# by level, not by contrast with neighbouring picture.
import numpy as np
BLANK_MAX = 9.0        # a blanking sample reads below this (measured: blanking ~1-2, picture black with setup ~16+)
PIC_MIN = 14.0         # the picture next to an edge must reach this within a few samples
def crossing(r, i0, i1, level):
    """sub-sample position where r crosses level between samples i0 and i1 (i1 = i0 +-1)"""
    a, b = r[i0], r[i1]
    return i0 + (i1 - i0) * (level - a) / (b - a) if b != a else float(i0)
def line_refs(y):
    """y: one line's 720 luma samples. Returns (start, start_conf, end, end_conf); NaN where no reference is in view."""
    r = np.convolve(y.astype(np.float32), np.ones(3) / 3, 'same'); r[0], r[-1] = y[0], y[-1]
    out = [np.nan, 0.0, np.nan, 0.0]
    # left: blanking from x=0 up to the rise
    if r[1] < BLANK_MAX:
        k = 1
        while k < 200 and r[k] < BLANK_MAX: k += 1
        if k < 200:
            pic = r[k + 2:k + 10].mean()
            if pic > PIC_MIN:
                lvl = r[max(0, k - 4):k].mean()
                mid = lvl + 0.5 * (pic - lvl)
                j = k
                while j < k + 8 and r[j] < mid: j += 1
                out[0] = crossing(r, j - 1, j, mid)
                flat = r[1:k].std() if k > 2 else 3.0
                out[1] = float(np.clip((pic - lvl) / 40, 0, 1) * np.clip(1 - flat / 6, 0, 1))
    # right: blanking from the fall to x=719
    if r[-2] < BLANK_MAX:
        k = 718
        while k > 520 and r[k] < BLANK_MAX: k -= 1
        if k > 520:
            pic = r[k - 9:k - 1].mean()
            if pic > PIC_MIN:
                lvl = r[k + 1:k + 5].mean()
                mid = lvl + 0.5 * (pic - lvl)
                j = k
                while j > k - 8 and r[j] < mid: j -= 1
                out[2] = crossing(r, j, j + 1, mid)
                flat = r[k + 1:719].std() if k < 717 else 3.0
                out[3] = float(np.clip((pic - lvl) / 40, 0, 1) * np.clip(1 - flat / 6, 0, 1))
    return out
