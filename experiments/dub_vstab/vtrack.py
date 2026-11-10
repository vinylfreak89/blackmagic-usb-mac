# the vertical landmark's path: a smooth path through the 525-line fold (fold525.npy: row darkness per pass at its tape
# phase), found as the cheapest path (cost = the fold's value, lowest on the landmark; unseen rows cost nothing; a step
# of more than MAXSTEP rows per pass is not allowed, steps cost a little).  Known answer: the same noise with a line of
# known path drawn in (--ka).
import numpy as np, sys
MAXSTEP = 4; STEPCOST = 0.15
def track(M):
    R, N = M.shape; C = np.where(np.isfinite(M), np.clip(M, -3, 3), 0.0)
    # sharpen: the landmark is one or two rows of low values
    cost = np.full((N, R), np.inf); back = np.zeros((N, R), np.int8); cost[0] = C[:, 0]
    steps = np.arange(-MAXSTEP, MAXSTEP + 1)
    for j in range(1, N):
        cand = np.stack([np.roll(cost[j - 1], s) + STEPCOST * abs(s) for s in steps])      # arriving from row r - s
        k = cand.argmin(0); cost[j] = cand[k, np.arange(R)] + C[:, j]; back[j] = k
    path = np.zeros(N, int); path[-1] = int(cost[-1].argmin())
    for j in range(N - 1, 0, -1): path[j - 1] = (path[j] - steps[back[j, path[j]]]) % R
    return path
if __name__ == '__main__':
    S = sys.argv[1]; M = np.load(S + '/fold525.npy')
    if '--ka' in sys.argv:
        rng = np.random.default_rng(3); R, N = M.shape
        Z = M.copy()
        for j in range(N): Z[:, j] = np.roll(Z[:, j], rng.integers(0, R))                   # the real landmark scattered
        vis = np.isfinite(M)                                                              # keep the real pattern of unseen rows
        Z = np.where(vis, np.where(np.isfinite(Z), Z, rng.normal(0, 1, M.shape)), np.nan)
        true = (100 - 0.33 * np.arange(N) + 12 * np.sin(2 * np.pi * np.arange(N) / 47)) % R
        depth = np.nanpercentile(M, 1)                                                    # as deep as the real fold's darkest 1%
        for j in range(N):
            r = int(round(true[j])) % R
            if vis[r, j]: Z[r, j] = depth
        p = track(Z); e = (p - true + R / 2) % R - R / 2
        print('known answer: line of depth %.2f on the scattered fold, seen in %.0f%% of passes: path error median %.2f rows, 95th pct %.2f, worst %.1f' % (depth, 100 * np.mean([vis[int(round(t)) % R, j] for j, t in enumerate(true)]), np.median(np.abs(e)), np.percentile(np.abs(e), 95), np.abs(e).max()))
    else:
        p = track(M); np.save(S + '/vpath.npy', p); print('path (every 50th pass):', p[::50].tolist())
