import sys, json, numpy as np
sys.path.insert(0, 'premise'); from edges import line_edges
U = np.load('tape1_scored_units.npz')
T = json.load(open('/private/tmp/wave-engine/claude1/abrender/sheet_tiles.json'))
W = {x['rep'] for x in json.load(open('/private/tmp/wave-engine/claude1/abrender/disagree.json'))} | {157531}
FR = {1: (19, 262), 2: (282, 525)}
out = []
for t in T:
    if t['rep'] == 23568: continue
    torn = t['rep'] not in W; f = 1 if len(t['rows'][0]) >= len(t['rows'][1]) else 2   # the field the owner scored
    Y = U[str(t['rep'])][:, 1::2]; a, b = FR[f]
    blank = float(np.percentile(Y[a:b, 0:3], 5))
    E = np.array([line_edges(Y[r]) for r in range(a, b - 8)])
    # field reference: lines whose rise starts from blanking and whose fall ends at blanking, with a step >= 20 codes
    okr = (np.abs(E[:, 1] - blank) <= 3) & (E[:, 2] - E[:, 1] >= 20); okf = (np.abs(E[:, 4] - blank) <= 3) & (E[:, 5] - E[:, 4] >= 20)
    mr = np.median(E[okr, 0]) if okr.sum() >= 20 else np.nan; mf = np.median(E[okf, 3]) if okf.sum() >= 20 else np.nan
    for k, r in enumerate(range(a, b - 8)):
        out.append((t['rep'], f, torn, r + 4, E[k, 0] - mr, okr[k], E[k, 3] - mf, okf[k], E[k, 6] - blank, E[k, 7] - blank, E[k, 2] - E[k, 1], E[k, 5] - E[k, 4]))
A = np.array(out, dtype=float); np.save('premise/c3c5.npy', A)
print('fields: torn', len({(r[0]) for r in out if r[2]}), 'clean', len({r[0] for r in out if not r[2]}))
