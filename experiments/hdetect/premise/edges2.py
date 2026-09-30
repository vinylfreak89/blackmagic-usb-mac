# Edge = where the line leaves the blanking run that starts at the window edge.
# Blanking band per field: its level = median of samples 0-2 over the field's lines, its top = the 99th percentile of those
# samples (the range blanking actually occupies in this field, measured, no multiplier).
# Left: walk from sample 0 while the sample is inside the band; the rise is the steepest step within the next 12 samples,
# located at the 50% point between the band level and the level 4-10 samples after it. No run at sample 0 -> 'no blanking'.
# Right: sample 719 reads blanking on every line (device), so walk left from 718 while inside the band; same for the fall.
import numpy as np
def band(Yfield):
    s = Yfield[:, 0:3].astype(float).ravel(); return float(np.median(s)), float(np.percentile(s, 99))
def left(y, B, top):
    # the rise to picture is the LAST departure from the blanking band before the line stays above it: an excursion that
    # falls back into the band (tape 1's post-blanking bump) is not the edge. Scan the first 150 samples for the last
    # in-band sample that is followed by the picture; the rise is the steepest step in the 12 samples after it.
    y = y.astype(float)
    if y[0] > top and y[1] > top and y[2] > top: return ('none', np.nan, y[0] - B)
    inb = np.nonzero(y[:150] <= top)[0]
    if not len(inb) or inb[-1] >= 149: return ('flat', np.nan, 0.0)
    k = int(inb[-1]) + 1
    d = np.diff(y[max(0, k - 1):k + 12]); i = max(0, k - 1) + int(np.argmax(d))
    post = np.median(y[i + 4:i + 11]); t = B + 0.5 * (post - B)
    for j in range(max(1, k - 1), min(719, i + 8)):
        if y[j - 1] < t <= y[j]: return ('edge', j - 1 + (t - y[j - 1]) / (y[j] - y[j - 1]), post - B)
    return ('edge', float(i), post - B)
def right(y, B, top):
    # sample 719 is blanking on every line (device); bright normal falls are still falling at 718 (C2), so the fall is the
    # steepest drop in the last 14 samples before the run of in-band samples that ends at 719; 'none' when the line is still
    # above half of its own step at 718 (the fall has not happened inside the window)
    y = y.astype(float); k = 719
    while k > 570 and y[k] <= top: k -= 1
    if k <= 570: return ('flat', np.nan, 0.0)
    lo = max(0, k - 13); d = np.diff(y[lo:k + 2]); i = lo + int(np.argmin(d))
    pre = np.median(y[max(0, i - 10):max(1, i - 3)]); t = B + 0.5 * (pre - B)
    if y[718] >= t and i >= 717: return ('none', np.nan, pre - B)
    for j in range(min(718, k + 1), max(0, i - 8), -1):
        if y[j] >= t > y[j + 1]: return ('edge', j + (y[j] - t) / (y[j] - y[j + 1]), pre - B)
    return ('edge', float(i), pre - B)
