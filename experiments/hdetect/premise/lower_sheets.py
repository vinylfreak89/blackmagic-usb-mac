import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
D = json.load(open('premise/lower_probe.json')); Z = np.load('premise/lower_raw.npz'); D = [d for d in D if d['lines']]
per = 6
for s in range(0, len(D), per):
    part = D[s:s + per]; fig, ax = plt.subplots(len(part), 3, figsize=(22, 3.6 * len(part)), gridspec_kw={'width_ratios': [2.2, 1, 1]}, squeeze=False)
    for k, d in enumerate(part):
        key = '%d_%d' % (d['unit'], d['field']); raw = Z[key]; r0 = int(Z[key + '_r0'][0]); Y = raw[:, 1::2].astype(float)
        fl = [x['line'] for x in d['lines']]
        ax[k, 0].imshow(Y, cmap='gray', vmin=0, vmax=235, aspect='auto', extent=(0, 720, r0 + 4 + len(Y), r0 + 4))
        for ln in fl: ax[k, 0].plot([-12, -2], [ln + .5, ln + .5], color='r', lw=2, clip_on=False)
        ax[k, 0].set_title('%d f%d lines %s | %s' % (d['unit'], d['field'], '%d-%d' % (fl[0], fl[-1]), ' '.join('%s dl%+.1f dr%+.1f gap%s' % (x['kind'][0:5], x['dl'], x['dr'], ('%.0f' % x['gap']) if x['gap'] == x['gap'] else '-') for x in d['lines'][:3])), fontsize=8)
        for i in range(len(Y)):
            ln = r0 + 4 + i; c = 'r' if ln in fl else '0.6'; lw = 1.1 if ln in fl else 0.5
            if ln in fl or min(abs(ln - f) for f in fl) <= 3:
                ax[k, 1].plot(range(0, 100), Y[i, :100], color=c, lw=lw); ax[k, 2].plot(range(620, 720), Y[i, 620:], color=c, lw=lw)
        ax[k, 1].set_title('left (red flagged, grey +-3 lines)', fontsize=8); ax[k, 2].set_title('right', fontsize=8)
    plt.tight_layout(); plt.savefig('premise/lower/sheet_%02d.png' % (s // per), dpi=55); plt.close()
print('sheets', (len(D) + per - 1) // per)
