# Echo strength across the capture from the survey's test lines; where it is weakest.
# usage: python3 survey_read.py OUTPREFIX CAPTURE_SECONDS
import sys, numpy as np
import model as M
np.set_printoptions(linewidth=260, precision=2, suppress=True)
tl = np.load(sys.argv[1] + '_tl.npy'); wh = np.load(sys.argv[1] + '_where.npy'); secs = float(sys.argv[2]); N = len(tl); done = wh[:, 2] == 1
g = np.full((N, 2), np.nan); Rs = {}
for j in (0, 1):
    R, F, T, idx = M.edges(tl[:, j]); g[idx, j] = M.gauge(R); Rs[j] = (R, idx)
gg = np.nanmean(g, 1); has = ~np.isnan(gg); tsec = (np.arange(N) + 0.5) / N * secs
print('samples', N, 'read', done.sum(), 'with a bar reading', has.sum(), '(line 18:', (~np.isnan(g[:, 0])).sum(), ', line 281:', (~np.isnan(g[:, 1])).sum(), ')')
both = ~np.isnan(g).any(1); print('line 18 vs line 281 where both read: correlation %.3f, median difference %.3f' % (np.corrcoef(g[both, 0], g[both, 1])[0, 1], np.median(g[both, 0] - g[both, 1])))
print('strength: min %.2f, 5%% %.2f, median %.2f, 95%% %.2f, max %.2f' % tuple(np.nanquantile(gg, [0, .05, .5, .95, 1])))
print('share of samples below 0.1: %.3f, below 0.2: %.3f, below 0.3: %.3f' % tuple((gg[has] < x).mean() for x in (0.1, 0.2, 0.3)))
print('per 4-minute stretch, median / min:'); 
for a in range(0, N, N // 16):
    s = gg[a:a + N // 16]; 
    if (~np.isnan(s)).any(): print('  %5.1f min: %.2f / %.2f  (%d readings)' % (tsec[a] / 60, np.nanmedian(s), np.nanmin(s), (~np.isnan(s)).sum()))
o = np.argsort(np.where(has, gg, 9))[:15]; print('weakest 15 (minute:second, strength, byte offset):')
for k in o: print('  %2d:%04.1f  %.2f  %d' % (tsec[k] // 60, tsec[k] % 60, gg[k], wh[k, 0]))
# longest runs of consecutive samples below 0.2
low = has & (gg < 0.2); runs = []; a = None
for k in range(N + 1):
    if k < N and low[k]:
        if a is None: a = k
    elif a is not None: runs.append((k - a, a)); a = None
runs.sort(reverse=True); print('longest runs of consecutive samples below 0.2 (samples, start minute:second, byte offset):')
for n, a in runs[:6]: print('  %d  %2d:%04.1f  %d' % (n, tsec[a] // 60, tsec[a] % 60, wh[a, 0]))
R, idx = Rs[1]; gi = g[idx, 1]
for name, m in (('weakest tenth', gi <= np.quantile(gi, 0.1)), ('middle', (gi > np.quantile(gi, 0.45)) & (gi < np.quantile(gi, 0.55))), ('strongest tenth', gi >= np.quantile(gi, 0.9))):
    print('bar rise, %s (strength %.2f), t=-4..27:' % (name, np.median(gi[m])), np.median(R[m], 0))
np.save(sys.argv[1] + '_g.npy', g)
