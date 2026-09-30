import sys, os, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, 'premise'); import playback as P
path, out = sys.argv[1], sys.argv[2]; specs = [(int(a), int(b), int(c)) for a, b, c in (s.split(':') for s in sys.argv[3:])]  # unit:line0:line1
want = {u % 65536: u for u, _, _ in specs}; got = {}
for c, raw in P.raw_units(path, 0, os.path.getsize(path)):
    if c in want: got[want.pop(c)] = raw.copy()
    if not want: break
fig, ax = plt.subplots(len(specs), 3, figsize=(18, 4 * len(specs)), squeeze=False)
for k, (u, l0, l1) in enumerate(specs):
    raw = got[u]; Y = raw[:, 1::2].astype(float); C = raw[:, 0::2].astype(float)
    for ln in range(l0, l1 + 1):
        y = Y[ln - 4]; ax[k, 0].plot(range(0, 90), y[0:90], lw=.8, label=str(ln)); ax[k, 1].plot(range(630, 720), y[630:720], lw=.8)
    ax[k, 2].imshow(Y[l0 - 14:l1 - 4 + 11], cmap='gray', aspect='auto', vmin=0, vmax=235, extent=(0, 720, l1 + 10, l0 - 10))
    ax[k, 0].set_title('unit %d lines %d-%d left' % (u, l0, l1)); ax[k, 1].set_title('right'); ax[k, 0].legend(fontsize=6, ncol=2)
plt.tight_layout(); plt.savefig(out, dpi=70)
