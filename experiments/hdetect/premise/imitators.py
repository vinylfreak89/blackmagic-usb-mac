import sys, numpy as np
sys.path.insert(0, 'premise'); import playback as P
CASES = [('overmodulation (credits)', 100629, 1, [199, 146, 125]), ('dark post', 34792, 2, [305, 306, 307]),
         ('horizon', 132200, 1, [197, 198, 199]), ('blinds at picture edge', 148999, 2, [423, 424, 427]),
         ('dark lines near field bottom', 16160, 1, [253, 254]), ('dark lines near field bottom', 31024, 1, [249, 250])]
def unit(u):
    for c, r in P.raw_units(P.AF, P.a_offset(u) - (6 << 20), P.a_offset(u) + (6 << 20)):
        if c == u % 65536: return r.astype(float)
for name, u, f, lines in CASES:
    raw = unit(u)
    print('\n%s  A %d field %d' % (name, u, f))
    for ln in lines:
        row = raw[ln - 4]; y = row[1::2]; cb = np.repeat(row[0::4] - 128, 2); cr = np.repeat(row[2::4] - 128, 2)
        true_b = y[0:3]
        # imitator: samples beyond the first 30 whose luma sits within 6 codes of the line's own blanking level
        bl = np.median(true_b); cand = np.nonzero((np.abs(y - bl) <= 6) & (np.arange(720) >= 30) & (np.arange(720) <= 700))[0]
        if not len(cand):
            print('   NTSC %d: no blanking-level samples inside the picture (min luma inside %.0f at %d)' % (ln, y[30:700].min(), 30 + int(np.argmin(y[30:700])))); continue
        runs = np.split(cand, np.nonzero(np.diff(cand) > 1)[0] + 1); r = max(runs, key=len)
        seg = y[r]; c = np.hypot(cb[r], cr[r])
        print('   NTSC %d: true blanking (0-2) level %.1f | imitator run samples %d-%d (%d long): level %.1f sd %.2f, chroma mean %.1f max %.1f hue %.0f deg | neighbours of the run: %.0f .. %.0f' % (
            ln, true_b.mean(), r[0], r[-1], len(r), seg.mean(), seg.std(), c.mean(), c.max(), (np.degrees(np.arctan2(cr[r].mean(), cb[r].mean())) + 360) % 360,
            y[max(0, r[0] - 3)], y[min(719, r[-1] + 3)]))
# for reference: true blanking noise on clean lines of this tape (samples 0-2 and the flat blanking before the rise)
