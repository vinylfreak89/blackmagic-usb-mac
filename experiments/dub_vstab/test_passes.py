# Known answer for passes.track: a synchroniser simulated from its mechanism (a write pointer filling a field memory in
# passes, a read pointer emptying it), independent of the tracker's interval logic.  Time is in tape lines: the write
# puts tape line s_k + r in row r at time s_k + r; the read takes row r of field f at fp(f) + r * (field period / 262.5).
# Truth = the tape line each row read held.  Errors are relative to the first pass (the tape axis has no absolute zero).
import numpy as np, sys
import passes as P
ROW0, NROW = 18, 236
def simulate(F, s0, fp, events=()):
    """fp: number or function f -> read start time of field f.  events {pass index: ('cut', rows) | ('step', lines)}:
    'cut' ends that pass after `rows` rows, the next starting at once; 'step' starts the NEXT pass `lines` later."""
    R = np.array([fp(f) for f in range(F + 1)]) if callable(fp) else fp * np.arange(F + 1)
    ev = dict(events); starts = [s0]; nrows = []
    while starts[-1] < R[-1] + 600:
        k = len(starts) - 1; e = ev.get(k)
        if e and e[0] == 'cut': nrows.append(e[1]); starts.append(starts[-1] + e[1])
        elif e and e[0] == 'step': nrows.append(262); starts.append(starts[-1] + e[1])
        else: nrows.append(262); starts.append(starts[-1] + P.LP)
    starts = np.array(starts[:-1]); nrows = np.array(nrows); rows = ROW0 + np.arange(NROW); ks = np.arange(len(starts))[:, None]
    news, truth, prev = [], [], None
    for f in range(F):
        T = R[f] + rows * (R[f + 1] - R[f]) / 262.5; wt = starts[:, None] + rows[None]
        k = np.where((wt <= T[None]) & (rows[None] < nrows[:, None]), ks, -1).max(0)
        news.append(np.ones(NROW, bool) if prev is None else k != prev); truth.append(np.where(k >= 0, wt[np.clip(k, 0, None), np.arange(NROW)], np.nan)); prev = k
    return news, truth
def run(name, F, s0, fp, events=(), bound=None, fit=True):
    news, truth = simulate(F, s0, fp, events)
    RT, fps = P.read_times(news, ROW0); fpe = float(np.mean(fps))
    tape, info = P.track(news, ROW0, RT); how = info['how']; e0 = None; err = []; byhow = {}
    for f in range(F):
        m = np.isfinite(tape[f]) & np.isfinite(truth[f])
        if (np.isfinite(tape[f]) != (news[f] & np.isfinite(truth[f]))).any() and info['kind'][f] != 'odd': print('   field %d: placed rows differ from the new rows (%s)' % (f, info['kind'][f]))
        if not m.any(): continue
        e = tape[f][m] - truth[f][m]
        if e0 is None: e0 = e[0]
        err.append(e - e0); byhow.setdefault(how[info['field_pass'][f]], []).append(e - e0)
    e = np.concatenate(err); kinds = {k: info['kind'].count(k) for k in sorted(set(info['kind']))}
    print('== %s: fields %s; passes placed %s; field period fitted %.2f (mean)\n      error (rows): worst %.2f, share within 1 row %.4f, at the end %+.2f'
          % (name, kinds, {h: how.count(h) for h in sorted(set(how))}, fpe, np.abs(e).max(), (np.abs(e) <= 1).mean(), err[-1][-1]))
    if bound is not None: assert np.abs(e).max() <= bound + 1e-6, 'error over %.1f rows' % bound
if __name__ == '__main__':
    run('free run, tape and output lines equal', 900, -97.3, 262.5, bound=0)
    run('free run, tape lines 0.14% longer', 900, -200.2, 262.13, bound=0)
    run('free run, tape lines 0.15% shorter', 900, -31.9, 262.9, bound=0)
    run('free run, field period drifting 262.0 -> 262.4', 1800, -80.0, lambda f: 262.0 * f + 0.4 * f * f / 3600, bound=0)
    run('write restarted once after 140 rows', 900, -150.0, 262.13, {20: ('cut', 140)}, bound=0)
    # not asserted: these three cannot be told from a free run by repeats alone until an expected repeat fails to come, so
    # the passes just before a 'step' break can sit up to the size of that break off (reported, flagged in the render)
    run('written in step with the read for 30 passes', 900, -120.0, 262.13, {k: ('step', 262.13) for k in range(40, 70)})
    run('restarts on six passes in a row (rows 140-175)', 900, -60.0, 262.13, {k: ('cut', 140 + 7 * (k - 300)) for k in range(300, 306)})
    run('next pass 12 lines early, once (sync seen in the idle gap)', 900, -60.0, 262.13, {200: ('step', 278.0)})
    print('asserted cases passed')
