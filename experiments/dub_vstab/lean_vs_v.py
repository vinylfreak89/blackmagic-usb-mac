# one timebase error, two readings?  If the device's line clock is not locked to the tape's lines (tape line = device
# line * (1 + e)), the tape's sync slides -858 e samples per row (the lean of the dark strokes) and the tape's vertical
# landmark slides -290 e rows per pass against pass-counted placement.  So lean = (858 / 290) * landmark rate = 2.96 x.
import numpy as np, sys
from scipy.ndimage import uniform_filter1d
S = sys.argv[1]; z = np.load(S + '/hband3.npz'); sp = z['sp']; leans = z['leans']; p = np.load(S + '/vpath.npy').astype(float)
N = len(p); HW = int(sys.argv[2]) if len(sys.argv) > 2 else 5
spec = uniform_filter1d(sp.max(1), 2 * HW + 1, axis=0, mode='nearest')            # tallest window per lean, averaged over 2HW+1 fields
lean = leans[spec.argmax(1)]; height = spec.max(1) - np.median(spec, 1)
d = np.diff(np.unwrap(p * 2 * np.pi / 525) * 525 / (2 * np.pi)); v = uniform_filter1d(np.concatenate([d[:1], d]), 2 * HW + 1, mode='nearest')
ok = np.ones(N, bool); ok[700:940] = False; ok[:HW] = False; ok[-HW:] = False        # outside the stretch placed by assumption
r = np.corrcoef(lean[ok], v[ok])[0, 1]; A = np.vstack([v[ok], np.ones(ok.sum())]).T; k, b = np.linalg.lstsq(A, lean[ok], rcond=None)[0]
print('averaging over %d fields: lean vs landmark rate: correlation %.3f; lean = %.2f x rate %+.2f  (one-timebase prediction: 2.96 x rate + 0)' % (2 * HW + 1, r, k, b))
print('landmark rate: mean %.2f rows/pass, 5th..95th pct %.2f..%.2f;  lean: mean %.2f, 5th..95th pct %.1f..%.1f samples/row' % (v[ok].mean(), *np.percentile(v[ok], [5, 95]), lean[ok].mean(), *np.percentile(lean[ok], [5, 95])))
print('same direction (both signs agree, |rate| > 0.3): %.3f of %d passes' % ((np.sign(lean) == np.sign(v))[ok & (np.abs(v) > 0.3)].mean(), (ok & (np.abs(v) > 0.3)).sum()))
print('pass: rate -> predicted lean | measured lean')
for j in range(20, 420, 16): print('  %4d: %+5.2f -> %+5.1f | %+5.1f' % (j, v[j], 2.96 * v[j], lean[j]))
np.savez(S + '/lean_v.npz', lean=lean, v=v, ok=ok, height=height)
