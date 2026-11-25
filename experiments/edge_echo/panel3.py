# Stills: captured | previous model (straight-line split, bar-rise taps) | two-shape echo read from that frame's own
# test lines against the measured no-echo edge.  Luma only, first field.
import numpy as np, sys
import model as M, deghost as G, refit3 as T
from aware import clean
from stretch_check import remove_img, model_from_testline
from PIL import Image
q_old, _, _ = model_from_testline(); own, V, Q, _ = T.shapes(); u = np.load('units.npy', mmap_mode='r'); tr = M.tr
for k in map(int, sys.argv[1:]):
    acc = []
    for row in (14, 277):
        line = u[k][row, 1::2].astype(float) - M.BL; top = np.median(line[560:680]); r, _ = T.rise(line, top) if top >= 120 else (None, None)
        if r is not None: acc.append((T.amounts(r, own, V), 1 - r[(tr >= 5) & (tr <= 9)].min(), top))
    if not acc: print('unit', k, ': no bar reading'); continue
    a = np.mean([x[0] for x in acc], 0); g = np.mean([x[1] for x in acc]); top = np.mean([x[2] for x in acc])
    y = u[k][G.ROWS][:, 1::2].astype(float) - G.BL; cl = lambda X: clean(X, 220)
    old = remove_img(y, q_old, g, top, cleaner=cl); new = remove_img(y, a[0] * Q[0] + a[1] * Q[1], 1.0, top, cleaner=cl)
    print(f'unit {k}: strength reading {g:.2f}, amounts {a[0]:.2f} / {a[1]:.2f}, bar top {top:.0f}; output range new {new.min():.0f}..{new.max():.0f}, previous {old.min():.0f}..{old.max():.0f}')
    im = lambda v: np.clip(v[:220] + G.BL, 0, 255).astype(np.uint8); bar = np.full((6, 720), 255, np.uint8)
    both = np.vstack([im(y), bar, im(old), bar, im(new)])
    Image.fromarray(both).resize((1440, both.shape[0] * 3), Image.LANCZOS).save(f'two{k}.png')
