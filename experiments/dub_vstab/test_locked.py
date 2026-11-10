# Known answer for render_locked.remap, made independently of it: a tape whose every line carries a dark stroke in its
# first 63 samples, a brightness that names the line (40 + line mod 97) and one bright line per 525 (the landmark), is
# sampled the way the synchroniser does it: on a write clock whose line is (1 + rho(t)) tape lines long (rho switching
# between two values about once a second on a steady offset, as the capture shows), in passes at the capture's own pass
# times, 720 of every 858 written samples kept.
#   A. with the true timebase the render must put every stroke in columns 0..62 of every line and every line's own
#      brightness on its own line (asserted).
#   B. with the timebase ESTIMATED (landmark drawn into the capture's own scattered fold at the same path, tracked by
#      vtrack, fitted by timebase): per field, how far the landmark's line sits from its place, the lean left in the
#      stroke (samples per line; asserted small) and the stroke's sideways jump from field to field (reported).
#   C. the same with passes really 290.38 written lines long while write times count 290: without kappa a lean of
#      858 x 0.38 / 290 = 1.12 is left in every field (asserted), with it none (asserted).
# usage: test_locked.py CACHE_DIR
import numpy as np, csv, sys
import vtrack, timebase as TB, render_locked as RL
S = sys.argv[1]; M = np.load(S + '/fold525.npy'); R, N = M.shape; LP = 290.0; rng = np.random.default_rng(5)
rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
starts = np.array([float(r['tape_line_of_row_18']) - 18 for r in rows]); real = np.load(S + '/vpath.npy'); vis = np.isfinite(M)
tt = np.arange(starts[0] - 600, starts[-1] + 900, 0.25)
rho_t = 0.00125 + 0.0016 * np.tanh(4 * np.sin(2 * np.pi * tt / (53 * LP)))
Phi_t = np.concatenate([[0], np.cumsum(0.5 * (rho_t[1:] + rho_t[:-1]) * 0.25)]); PHI0 = 211.3                 # tape position at t: t + Phi + PHI0
def tape_value(phi):
    u = np.mod(phi, 525); m = np.floor(u); h = 858 * (u - m)
    return np.where(h < 63, 6.0, np.where(m == 0, 220.0, 40.0 + np.mod(m, 97)))
DELTA = 0.0                                                                # a pass is really 290 + DELTA written lines; write times still count 290
def true_time(s, t): return t + DELTA * (s - starts[0]) / LP               # the write time that really passed (t counted at 290 per pass)
def tape_pos(s, t): tr = true_time(s, t); return tr + np.interp(tr, tt, Phi_t) + PHI0
def field_rows(s):
    t = s + np.arange(18, 254, dtype=float); tau = t[:, None] + np.arange(720)[None] / 858.0
    return t, tape_value(tape_pos(s, tau))
def estimate():
    """the timebase as the capture would give it: the landmark (tape line 0) drawn into the capture's scattered fold where each pass meets it"""
    Z = M.copy(); pool = np.array([M[real[j], j] for j in range(N) if vis[real[j], j]])
    for j in range(N): Z[:, j] = np.roll(Z[:, j], rng.integers(0, R))
    Z = np.where(vis, np.where(np.isfinite(Z), Z, rng.normal(0, 1, M.shape)), np.nan)
    for j in range(N):
        t = starts[j] + np.arange(18, 254); u = np.mod(tape_pos(starts[j], t) + 262.5, 525) - 262.5; r = np.abs(u).argmin()
        if abs(u[r]) <= 0.5: Z[int(np.floor(np.mod(t[r], 525))), j] = rng.choice(pool)
    T, D, seen = TB.samples(starts, vtrack.track(Z)); return TB.Timebase(T[seen], D[seen])
def measure(tb, kappa, label):
    lean_after, vert, pos = [], [], []
    for j in range(100, 700):
        t, y = field_rows(starts[j]); Y, _, _ = RL.remap(y, np.full((len(t), 360), 128.), np.full((len(t), 360), 128.), t, tb, kappa=kappa, tref=np.full(len(t), starts[j] + 136.0))
        c = stroke(Y); L = np.nonzero(np.isfinite(c))[0]
        lm = np.nonzero((Y > 200).sum(1) > 300)[0]
        if len(lm): vert.append(((lm[0] + 1) // 2 - 4 + 131) % 262.5 - 131)
        if len(L) < 200: continue                                           # the stroke fell in the 138 samples the capture does not carry
        m = (int(np.floor(t[0] - tb.D(t[0]) + RL.TOP)) + np.arange(238)) % 525; cc = c[np.where(m <= 262, 2 * m, 2 * m - 525)]   # the pass's tape lines in the order it ran, each on its first frame line
        k = np.nonzero(np.isfinite(cc))[0]; cu = np.unwrap(cc[k] * 2 * np.pi / 858) * 858 / (2 * np.pi); lean_after.append(np.polyfit(k, cu, 1)[0]); pos.append(cu[len(cu) // 2] % 858)
    la, v = np.array(lean_after), np.abs(vert); dp = np.abs((np.diff(pos) + 429) % 858 - 429)
    print('%s: lean left in the stroke: mean %+.2f, |.| median %.2f, 95th pct %.2f samples per line (%d fields with the stroke in view)' % (label, la.mean(), np.median(np.abs(la)), np.percentile(np.abs(la), 95), len(la)))
    print('   landmark line off its place (%d fields where it shows): median %.1f, 95th pct %.1f, worst %.1f lines;  stroke sideways jump field to field: median %.0f, 95th pct %.0f samples (not pinned)' % (len(v), np.median(v), np.percentile(v, 95), v.max(), np.median(dp), np.percentile(dp, 95)))
    return la
class True_tb:                                                             # the landmark (tape line 0) comes by when t + Phi + PHI0 = 0 mod 525
    def D(self, t): return -(np.interp(t, tt, Phi_t) + PHI0)
    def rho(self, t): return np.interp(t, tt, rho_t)
def stroke(Y):
    """per drawn frame line: centre column of the dark stroke (circular), or NaN"""
    c = np.full(RL.H, np.nan)
    for L in range(RL.H):
        k = np.nonzero(Y[L] < 20)[0]
        if len(k) >= 30: a = np.angle(np.exp(2j * np.pi * k / 858).mean()); c[L] = np.mod(a * 858 / (2 * np.pi), 858)
    return c
# A: exact timebase
bad = 0; worst = 0.0; fields = list(range(100, 500, 7))
for j in fields:
    t, y = field_rows(starts[j]); Y, _, _ = RL.remap(y, np.full((len(t), 360), 128.), np.full((len(t), 360), 128.), t, True_tb())
    for L in np.nonzero(np.isfinite(Y).any(1))[0]:
        m = (L // 2) if L % 2 == 0 or L == RL.H - 1 else None              # even frame lines: tape line L/2 of the first field (checked on those)
        row = Y[L]; d = np.isfinite(row); cols = np.nonzero(d)[0]
        dark = cols[row[cols] < 20]; lit = cols[(row[cols] >= 39.5) & (cols >= 64) & (cols <= 856)]
        if len(dark) and (dark.max() > 63): bad += 1                         # a stroke sample outside columns 0..63
        if L % 2 == 0 and len(lit):
            tl = (L // 2 - 4) % 525; want = 220.0 if tl == 0 else 40.0 + tl % 97; alt = ((L - 1 + 525) // 2 - 4) % 525   # or the other field's line on this frame line
            e = np.abs(row[lit] - want); e2 = np.abs(row[lit] - (220.0 if alt == 0 else 40.0 + alt % 97)); worst = max(worst, float(np.minimum(e, e2).max()))
assert bad == 0 and worst < 0.51, (bad, worst)
print('A. true timebase, %d fields: every stroke inside columns 0..63, every line carries its own line\'s brightness (worst difference %.2f codes): passed' % (len(fields), worst))
# B: estimated timebase, passes of exactly 290 written lines
lb = np.abs(858 * rho_t); print('lean of the stroke before any correction: |.| median %.2f, 95th pct %.2f samples per line' % (np.median(lb), np.percentile(lb, 95)))
la = measure(estimate(), 0.0, 'B. estimated timebase'); assert np.median(np.abs(la)) < 0.3 and abs(la.mean()) < 0.15, la.mean()
# C: passes really 290.38 written lines long, write times counted at 290 (the landmark then drifts 0.38 rows a pass that the tape did not make)
DELTA = 0.38; tbC = estimate()
la0 = measure(tbC, 0.0, 'C. passes of 290.38 lines, kappa 0       '); assert abs(la0.mean() - 858 * DELTA / LP) < 0.2, la0.mean()
la1 = measure(tbC, DELTA / LP, 'C. passes of 290.38 lines, kappa 0.38/290'); assert np.median(np.abs(la1)) < 0.3 and abs(la1.mean()) < 0.15, la1.mean()
print('passed')
