import json, glob, numpy as np
E = json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json'))
clean1 = {(u, e['field']) for e in E if e['score'] != 'torn' for u in range(e['first'], e['last'] + 1)}
torn1 = {(u, e['field']) for e in E if e['score'] == 'torn' for u in range(e['first'], e['last'] + 1)}
T = json.load(open('premise/torn_sets.json'))
def load(names):
    F, L = [], []
    for n in names:
        z = np.load('premise/guard/%s.npz' % n)
        if len(z['F']): F.append(z['F'])
        if len(z['L']): L.append(z['L'])
    return (np.concatenate(F) if F else np.zeros((0, 8))), (np.concatenate(L) if L else np.zeros((0, 9)))
srcs = {'tape1': sorted(p.split('/')[-1][:-4] for p in glob.glob('premise/guard/w*.npz')), 'cap4': ['cap4'], 'cap3': ['cap3'], 'cap2': ['cap2'], 'cap1': ['cap1'], 'pan': ['pan']}
print('== 1. guard vs the statistic it guards, per judged field (unflagged measured lines)')
print('%-6s %6s | g p50  | adj-diff p99 p50 | dist-from-median p99 left p50 / right p50 | ratio (dist p99 / g) p50 p90' % ('src', 'fields'))
for s, ns in srcs.items():
    F, _ = load(ns)
    if s == 'cap1': F = F[F[:, 0] >= 6667]
    if not len(F): continue
    r = np.maximum(F[:, 3], F[:, 4]) / F[:, 2]
    print('%-6s %6d | %5.2f | %5.2f            | %5.2f / %5.2f                              | %5.2f %5.2f' % (s, len(F), np.median(F[:, 2]), np.median(F[:, 5]), np.median(F[:, 3]), np.median(F[:, 4]), np.median(r), np.percentile(r, 90)))
print('\n== 2. scored CLEAN fields: lines beyond g on the statistic g is applied to')
def clean_rows(s):
    if s == 'tape1': _, L = load(srcs['tape1']); m = np.array([(int(u), int(f)) in clean1 for u, f in L[:, :2]]) if len(L) else np.zeros(0, bool)
    elif s == 'cap4': _, L = load(['cap4']); m = (L[:, 0] == 700) & (L[:, 1] == 2)
    else: _, L = load(['cap3']); m = (L[:, 0] == 13893) & (L[:, 1] == 1)
    return L[m]
for s in ('tape1', 'cap4', 'cap3'):
    C = clean_rows(s); g = C[:, 8]; al, ar = np.abs(C[:, 3]), np.abs(C[:, 4])
    print('%-6s lines %6d fields %4d | |dl|>g %5.1f%%  |dr|>g %5.1f%%  both>g %5.2f%% | lines flagged %d' % (s, len(C), len({(a, b) for a, b in C[:, :2]}), 100 * np.mean(al > g), 100 * np.mean(ar > g), 100 * np.mean((al > g) & (ar > g)), int(C[:, 7].sum())))
print('\n== 3. where the clean spread lives (scored clean fields, per field then pooled): sd of distance from median')
for s in ('tape1', 'cap4', 'cap3'):
    C = clean_rows(s); out = {k: [] for k in ('raw', 'after level', 'after level+line', 'adjacent/sqrt2')}
    for side, dcol, lcol in (('left', 3, 5), ('right', 4, 6)):
        acc = {k: [] for k in out}
        for key in {(a, b) for a, b in C[:, :2]}:
            m = (C[:, 0] == key[0]) & (C[:, 1] == key[1]) & np.isfinite(C[:, lcol])
            if m.sum() < 30: continue
            d, lv, ln = C[m, dcol], C[m, lcol], C[m, 2]
            A1 = np.c_[np.ones(len(d)), lv]; r1 = d - A1 @ np.linalg.lstsq(A1, d, rcond=None)[0]
            A2 = np.c_[np.ones(len(d)), lv, ln]; r2 = d - A2 @ np.linalg.lstsq(A2, d, rcond=None)[0]
            o = np.argsort(ln); adj = np.diff(ln[o]) == 1
            acc['raw'].append(d.std()); acc['after level'].append(r1.std()); acc['after level+line'].append(r2.std()); acc['adjacent/sqrt2'].append(np.diff(d[o])[adj].std() / np.sqrt(2))
        print('%-6s %-5s ' % (s, side) + '  '.join('%s %.2f' % (k, np.median(v)) for k, v in acc.items() if v))
print('\n== 4. scored TORN fields: how far the flagged lines sit beyond g (min over finite edges of |dev|/g)')
for s, names, torn in (('tape1', srcs['tape1'], torn1), ('cap4', ['cap4'], {tuple(x) for x in T['cap4']}), ('cap3', ['cap3'], {tuple(x) for x in T['cap3']})):
    F, _ = load(names); m = np.array([(int(u), int(f)) in torn for u, f in F[:, :2]]) & (F[:, 6] == 1)
    x = F[m, 7]; x = x[np.isfinite(x)]
    print('%-6s flagged scored-torn fields %5d | weakest flagged line / g  p10 %.1f p50 %.1f | fields whose weakest line is < 2g: %.1f%%' % (s, len(x), np.percentile(x, 10), np.median(x), 100 * np.mean(x < 2)))
