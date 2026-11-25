# Repeating bands after removal: the bar's flat top (nothing there in the weak-echo line) after each model's removal, strong-echo fields.
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import model as M, refit4 as F
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
np.set_printoptions(linewidth=250, precision=2, suppress=True)
cols = np.arange(720); t = np.arange(-10, 200); v = np.load('vbi_luma.npy', mmap_mode='r'); w = np.load('lo_vbi.npy', mmap_mode='r')
models = {'first clip (taps 2..27)': F.build(2, 27, 27, 0, verbose=False), 'remade clip (taps 2..75, zero moved)': F.build(2, 75, 80, 1, verbose=False), 'taps 2..75, zero not moved': F.build(2, 75, 80, 0, verbose=False)}
weak = []
for k in range(w.shape[0]):
    for j in (4, 12):
        y = w[k, j].astype(float) - M.BL; top = np.median(y[560:680]); r, c = F.rise(y, top, models['first clip (taps 2..27)']['tr']) if top >= 120 else (None, None)
        if r is not None and F.reading(r, models['first clip (taps 2..27)']['tr']) < 0.12: weak.append(np.interp(c + t, cols, y) / top)
weak = np.median(weak, 0); fig, ax = plt.subplots(3, 1, figsize=(22, 13), sharex=True)
for bi, (lo, hi) in enumerate(((0.45, 0.6), (0.6, 0.75), (0.75, 0.9))):
    res = {'captured': []}; res.update({n: [] for n in models})
    for k in range(v.shape[0]):
        ya = v[k, 4].astype(float) - M.BL; yb = v[k, 12].astype(float) - M.BL; ta = np.median(ya[560:680]); tb = np.median(yb[560:680])
        if min(ta, tb) < 120: continue
        m0 = models['first clip (taps 2..27)']; rb, cb = F.rise(yb, tb, m0['tr'])
        if rb is None or not (lo <= F.reading(rb, m0['tr']) < hi): continue
        res['captured'].append(np.interp(cb + t, cols, yb) / tb)
        for n, m in models.items():
            ra, _ = F.rise(ya, ta, m['tr'])
            if ra is None: continue
            a = F.amounts(ra, m); res[n].append(np.interp(cb + t, cols, M.remove(yb, a[0] * m['Q'][0] + a[1] * m['Q'][1], 1.0, tb, 0.4, 0.8)) / tb)
    print('reading %.2f-%.2f (%d fields): removed minus weak line on the bar top, every 4th sample from +12 to +120' % (lo, hi, len(res['captured'])))
    for n in res:
        d = np.median(res[n], 0) - weak; seg = d[(t >= 30) & (t < 190)]; sp = np.abs(np.fft.rfft((seg - seg.mean()) * np.hanning(len(seg)))); f = np.fft.rfftfreq(len(seg)); pk = np.argmax(sp[2:]) + 2
        print('  %-38s %s | bar top +30..+190: rms about its mean %.3f, strongest ripple period %.1f samples' % (n, d[(t >= 12) & (t <= 120)][::4], seg.std(), 1 / f[pk]))
        ax[bi].plot(t, d, label=n, lw=1.2 if n != 'captured' else 0.8, color={'captured': '0.6'}.get(n))
    ax[bi].set_ylim(-0.12, 0.12); ax[bi].grid(True); ax[bi].legend(loc='lower right'); ax[bi].set_title('reading %.2f-%.2f: difference from the weak-echo line, from the bar rise (0) along the bar top' % (lo, hi))
plt.tight_layout(); plt.savefig('repeats.png', dpi=60)
