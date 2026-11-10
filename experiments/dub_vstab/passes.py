"""Where each delivered row sits on the tape's line axis, from the frame synchroniser's own behaviour alone.

The synchroniser, with no vertical lock, writes the tape into its field memory in passes.  Pass k starts at tape line
s_k and writes row r with tape line s_k + r.  Free-running, s_{k+1} = s_k + LP (290 tape lines: 262.5 kept, 27.5 not),
so inside a free run a row's tape line follows from COUNTING passes and nothing else.  What has to be watched is when
the free run breaks (the synchroniser took something for sync and restarted its write).  For that the read side is the
clock: the output reads row r of field f at time fp*f + r, fp = the output field period in tape lines (262.5 if tape
and output lines were equally long; fitted, fit_fp()).  A row can only be read after it was written, so
  - a field whose rows are all new shows a pass that started in (R_prev, R],  R = fp*f;
  - a field that repeats the last one means the next pass had not started by R;
  - a field new on one side of row c and repeated on the other, followed by a field with the two sides exchanged, is
    one pass shown over two fields: the read caught the write at c, so the pass started at R (new above c first if the
    write is the slower, new below c first if the faster);
  - a partly new field with no such partner is a pass cut short at c: the write restarted there.
Each observation is an interval for the pass's start.  The tracker carries the interval forward by LP per pass, widened
by Q for the slow drift of fp, and intersects.  An empty intersection is a break.  After a break the next pass is put
  - at the cut (s + rows written), when the last pass was cut short and that start is possible, else
  - the same delay before its read as the last pass was before its own (written in step with the read),
moved into its own interval if outside.  These two are assumptions, not measurements: passes placed by them are flagged.

Units (measured later, timebase.py / hband4.py): times here count LP = 290 from one pass to the next, so the fitted fp
(262.12-262.20 on the capture) says a pass is really about 290.4 output lines long, not that the tape's lines are
longer than the output's.  Row offsets inside a pass are written lines either way.

Input: per output field, which visible rows are new (differ from the previous field's same row; classify()).
Output: per field, per row, the tape line (float, multiples of 0.5) or NaN where the row is a repeat.
"""
import numpy as np
LP = 290.0; TOL = 1.5; CROSS = 2.5; Q = 0.25

def field_kind(new):
    """new: bool per visible row.  -> ('all'|'none'|'top'|'bottom'|'odd', boundary row index, mismatches)"""
    n = len(new); k = int(new.sum())
    if k == n: return 'all', n, 0
    if k == 0: return 'none', 0, 0
    c = np.concatenate([[0], np.cumsum(new)])                       # c[i] = new rows among the first i
    top = (np.arange(n + 1) - c) + (k - c)                           # mismatches of 'new above i, stale below'
    bot = c + ((n - np.arange(n + 1)) - (k - c))                     # mismatches of 'stale above i, new below'
    it, ib = int(top.argmin()), int(bot.argmin())
    if top[it] <= bot[ib]: return ('top', it, int(top[it])) if top[it] <= 0.1 * n else ('odd', it, int(top[it]))
    return ('bottom', ib, int(bot[ib])) if bot[ib] <= 0.1 * n else ('odd', ib, int(bot[ib]))

def kinds_of(news):
    n = len(news[0]); fk = [('all', n, 0)] + [field_kind(news[f]) for f in range(1, len(news))]
    other = dict(top='bottom', bottom='top'); F = len(news)
    def partner(a, b): return 0 <= a and b < F and fk[a][0] in other and fk[b][0] == other[fk[a][0]] and abs(fk[a][1] - fk[b][1]) <= 6
    second = [False] * F
    for f in range(1, F): second[f] = partner(f - 1, f) and not second[f - 1]
    first = [fk[f][0] in other and not second[f] and partner(f, f + 1) for f in range(F)]
    return fk, first, second

def track(news, row0, fp, lp=LP, q=Q):
    """fp: the output field period in tape lines, or the read start time of every field (read_times()).
    -> (tape, info).  tape[f]: tape line per visible row, NaN where repeated.  info: kind per field, pass per field,
    per pass its tape start, read-time interval width, how it was placed ('first'|'free'|'cut'|'step'), run index."""
    F = len(news); n = len(news[0]); rows = row0 + np.arange(n); fk, first, second = kinds_of(news)
    RT = np.asarray(fp, float) if np.ndim(fp) else float(fp) * np.arange(F)      # read start of each field, tape lines
    P = []                                   # passes: dict(lo, hi, tape, how, run, field, cut)
    field_pass = np.full(F, -1); closed = False
    for f in range(F):
        R = RT[f]; Rp = RT[f - 1] if f else R - 262.5; kind, c, _ = fk[f]
        if second[f]: field_pass[f] = len(P) - 1; continue
        if kind == 'none':
            if P:
                P[-1]['lo'] = max(P[-1]['lo'], R - TOL - lp - q)       # the next pass had not started by this read
                if P[-1]['lo'] > P[-1]['hi']: closed = True
            field_pass[f] = len(P) - 1; continue
        a, b = (R - CROSS, R + CROSS) if first[f] else (Rp - TOL, R + TOL)
        cut = row0 + c if (kind == 'top' and not first[f]) else None   # rows written before the write restarted
        if not P:
            P.append(dict(lo=a, hi=b, tape=0.0, how='first', run=0, field=f, cut=cut))
        else:
            L = P[-1]; lo, hi = max(a, L['lo'] + lp - q), min(b, L['hi'] + lp + q)
            if lo <= hi and not closed and L['cut'] is None:
                P.append(dict(lo=lo, hi=hi, tape=L['tape'] + lp, how='free', run=L['run'], field=f, cut=cut))
            else:
                mid = 0.5 * (L['lo'] + L['hi']); step = how = None
                if L['cut'] is not None and a <= mid + L['cut'] <= b: step, how = float(L['cut']), 'cut'
                if step is None:
                    s = min(max(mid + R - RT[L['field']], a), b); step, how = round(2 * (s - mid)) / 2, 'step'
                lo, hi = max(a, L['lo'] + step - 2), min(b, L['hi'] + step + 2)
                if lo > hi: lo, hi = a, b
                P.append(dict(lo=lo, hi=hi, tape=L['tape'] + step, how=how, run=L['run'] + 1, field=f, cut=cut))
            closed = False
        field_pass[f] = len(P) - 1
    tape = []
    for f in range(F):
        t = np.full(n, np.nan); k = field_pass[f]; kind, c, _ = fk[f]
        if kind == 'none' or k < 0: tape.append(t); continue
        m = np.asarray(news[f], bool) if f else np.ones(n, bool)
        if kind == 'top': m = np.arange(n) < c
        elif kind == 'bottom': m = np.arange(n) >= c
        t[m] = P[k]['tape'] + rows[m]; tape.append(t)
    info = dict(kind=[k[0] for k in fk], field_pass=field_pass, how=[p['how'] for p in P], run=np.array([p['run'] for p in P]),
                start=np.array([p['tape'] for p in P]), width=np.array([p['hi'] - p['lo'] for p in P]), pass_field=np.array([p['field'] for p in P]))
    return tape, info

def fit_fp(news, row0, grid=np.arange(261.5, 263.0001, 0.01)):
    """the output field period in tape lines: the value under which the free run breaks least (ties: the middle one).
    Fitted with the tracker's own slack: the real repeat timing jitters by a row or so (measured: with no slack every
    period breaks a clean stretch 20+ times), and a fit without slack then prefers a wrong period."""
    br = np.array([sum(h in ('cut', 'step') for h in track(news, row0, fp)[1]['how']) for fp in grid])
    best = np.nonzero(br == br.min())[0]; return float(grid[best[len(best) // 2]]), int(br.min())

def read_times(news, row0, win=400, hop=200):
    """read start time of every field with the field period fitted per stretch of `win` fields (it drifts slowly with the
    tape's speed) and interpolated between stretch centres.  -> (times, fitted periods per stretch)"""
    F = len(news)
    if F <= win: fp = fit_fp(news, row0)[0]; return fp * np.arange(F), [fp]
    cs, fps = [], []
    for a in range(0, F - win + 1, hop):
        b = F if a + hop + win > F else a + win; cs.append(0.5 * (a + b)); fps.append(fit_fp(news[a:b], row0)[0])
    per = np.interp(np.arange(F), cs, fps); return np.concatenate([[0], np.cumsum(per[:-1])]), fps

def classify(cur, prev, texture=8.0, same=8.0):
    """cur, prev: (rows, 720) luma of a field and the one before.  -> bool per row: new.  A row repeated by the synchroniser
    comes back within the output chain's noise (measured 1.2 codes mean difference, 3.4 at the 99th percentile; new rows
    19 at the 1st); a row flat in both fields cannot tell and takes the verdict of the nearest row that can."""
    c = cur.astype(np.float32); p = prev.astype(np.float32)
    tex = (c.std(1) >= texture) | (p.std(1) >= texture); d = np.abs(c - p).mean(1)
    new = d >= same; idx = np.nonzero(tex)[0]
    if len(idx) == 0: return np.ones(len(c), bool)
    near = idx[np.abs(np.arange(len(c))[:, None] - idx[None]).argmin(1)]
    return new[near]
