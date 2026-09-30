# Instrument: play the current detector up to a unit, then dump every line of one field (edge readings, kind tests) and
# plot the raw rows. No rule change.
import sys, os, json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, 'premise'); import playback as P, phys, phys_run as PR
src, U, fld, n_lines = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 30
if src == 'tape1':
    TOP = np.load('edgestats/tvc2.toph.npy'); tops = lambda u: tuple(TOP[u - 2763]); want = {u % 65536: u for u in range(U - 300, U + 1)}
    def frames():
        for c, raw in P.raw_units(P.AF, max(0, P.a_offset(U - 300) - (8 << 20)), P.a_offset(U) + (8 << 20)):
            if c in want: yield want.pop(c), raw
else:
    path, tc = {'cap3': ('/private/tmp/hw-session/w_300s_aligned.tpc', 'cap3/cap3.csv')}[src]; tops = PR.pub_tops(tc) if os.environ.get('TOPMODE') == 'pub' else PR.sidecar_tops(tc)
    frames = lambda: P.raw_units(path, 0, os.path.getsize(path))
W = phys.Win()
for u, raw in frames():
    Y = raw[:, 1::2]
    if not W.ok(): W.add(phys.warm_frame(Y)); continue
    st = W.stats(); t = tops(u); res, fr = phys.judge(Y, t, st)
    if u == U: break
    W.add(fr)
fi = fld - 1; a, b = phys.FR[fi]; t0 = int(t[fi]) - 4 if t[fi] >= 0 else a; rows = np.arange(max(a, t0), b - 8); Yl = Y[rows].astype(float)
L, R, Ls, Rs = phys.edges(Yl, st); both = (Ls == 0) & (Rs == 0); mL, mR = np.median(L[both]), np.median(R[both]); g = st['g']
import collections; print("lines judged", len(rows), "| both edges measured", int(both.sum()), "(judge needs 20) | left", dict(collections.Counter(Ls.tolist())), "right", dict(collections.Counter(Rs.tolist())), "  (0 meas, 1 beyond, 2 unmeas)")
print('%s %d field %d | top line %s | result %s | st %s | field ref L %.1f R %.1f' % (src, U, fld, t[fi], res['lines'][fi], {k: (round(v, 2) if isinstance(v, float) else v) for k, v in st.items()}, mL, mR))
kind = {0: 'meas', 1: 'BEYOND', 2: 'unmeas'}
for i in range(min(n_lines, len(rows))):
    y = Yl[i]; print('  line %3d  L %6.1f %-6s dl %6.1f | R %6.1f %-6s dr %6.1f | y0-2 %s  lvl40-80 %5.1f  y716-719 %s' % (rows[i] + 4, L[i], kind[Ls[i]], L[i] - mL, R[i], kind[Rs[i]], R[i] - mR, y[0:3].astype(int), np.median(y[40:80]), Y[rows[i], 716:720].astype(int)))
fig, ax = plt.subplots(1, 3, figsize=(20, 6), gridspec_kw={'width_ratios': [1, 1, 1.4]})
for i in range(min(n_lines, len(rows))):
    ax[0].plot(range(0, 100), Yl[i, 0:100], lw=.7); ax[1].plot(range(620, 720), Yl[i, 620:720], lw=.7)
ax[0].set_title('%s %d f%d left, first %d lines from top' % (src, U, fld, n_lines)); ax[1].set_title('right')
ax[2].imshow(Yl[:n_lines + 20], cmap='gray', aspect='auto', vmin=0, vmax=235, extent=(0, 720, rows[0] + 4 + n_lines + 20, rows[0] + 4)); ax[2].set_ylabel('NTSC line')
plt.tight_layout(); plt.savefig('premise/miss/%s_%d_f%d.png' % (src, U, fld), dpi=65)
