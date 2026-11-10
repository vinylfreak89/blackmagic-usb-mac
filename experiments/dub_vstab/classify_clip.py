# new/stale verdict for every visible row of every field of the cached clip (passes.classify), saved for the tracker
import numpy as np, sys
import passes as P
S = sys.argv[1]; U = np.load(S + '/uyvy.npy', mmap_mode='r'); N = int(np.load(S + '/n.npy')[0]); R0, R1 = 18, 254
news = np.ones((2 * N, R1 - R0), bool); prev = None
for u in range(N):
    y = U[u, :, 1::2]
    for k in range(2):
        f = y[262 * k + R0:262 * k + R1]
        if prev is not None: news[2 * u + k] = P.classify(f, prev)
        prev = np.array(f)
np.save(S + '/news.npy', news)
RT, fps = P.read_times(list(news), R0); print('field period fitted per stretch (tape lines):', fps)
tape, info = P.track(list(news), R0, RT)
kinds = info['kind']; how = info['how']; print('fields %d: %s' % (len(kinds), {k: kinds.count(k) for k in sorted(set(kinds))}))
print('passes %d: placed %s' % (len(how), {h: how.count(h) for h in sorted(set(how))}))
st = info['start']; pf = info['pass_field']
for k, h in enumerate(how):
    if h in ('cut', 'step'): print('  break at field %4d (pass %4d): %s, tape step %.1f (free run would be 290), interval width %.1f' % (pf[k], k, h, st[k] - st[k - 1], info['width'][k]))
print('interval width over free passes: median %.1f, 95th pct %.1f' % (np.median(info['width']), np.percentile(info['width'], 95)))
np.save(S + '/tape.npy', np.array(tape)); np.save(S + '/tape_how.npy', np.array([how[k] if k >= 0 else 'none' for k in info['field_pass']])); np.save(S + '/tape_pass.npy', info['field_pass'])
