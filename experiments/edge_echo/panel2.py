# Stills: captured | first version (echo read from the left picture edge) | new model (echo strength from the test line,
# the tape's own edge shape left in, echo lagged near blanking).  Luma only.
import numpy as np, sys
import model as M, deghost as G
from aware import aware, clean
from stretch_check import remove_img, model_from_testline
from PIL import Image
q, _, _ = model_from_testline(); u = np.load('units.npy', mmap_mode='r'); tr = M.tr
for k in map(int, sys.argv[1:]):
    line = u[k][277, 1::2].astype(float) - M.BL; top = np.median(line[560:680]); c1 = M.cr(line, 0.5 * top, 400, 540, False)
    d = 1 - np.interp(c1 + np.arange(5, 10), np.arange(720), line).min() / top
    y = u[k][G.ROWS][:, 1::2].astype(float) - G.BL
    L, nl = G.left_resp(y); q1, s0 = G.echo_from_step(L); old = aware(y, q1, 220)
    new = remove_img(y, q, d, top, cleaner=lambda X: clean(X, 220))
    print(f'unit {k}: depth from the test line {d:.2f}, bar top {top:.0f} codes; output range new {new.min():.0f}..{new.max():.0f}, old {old.min():.0f}..{old.max():.0f}')
    im = lambda v: np.clip(v[:220] + G.BL, 0, 255).astype(np.uint8); bar = np.full((6, 720), 255, np.uint8)
    both = np.vstack([im(y), bar, im(old), bar, im(new)])
    Image.fromarray(both).resize((1440, both.shape[0] * 3), Image.LANCZOS).save(f'model{k}.png')
