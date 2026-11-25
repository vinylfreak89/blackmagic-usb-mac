# The same removal without the lag near blanking (which delays the predicted echo wherever the picture is not bright); samples at the floor left as captured.
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import model as M, refit4 as F
from aware import clean
from stretch_check import remove_img
m = F.build(2, 75, 80, 1, verbose=False)
for lumf, vbif, outf in (('run_luma.npy', 'vbi_luma.npy', 'clip_removed.npy'), ('lo_luma.npy', 'lo_vbi.npy', 'lo6_removed.npy')):
    R = F.per_frame(vbif, m); lum = np.load(lumf, mmap_mode='r'); out = np.lib.format.open_memmap(outf, mode='w+', dtype=np.uint8, shape=lum.shape)
    for k in range(lum.shape[0]):
        y = lum[k].astype(float) - M.BL; x = remove_img(y, R[k, 1] * m['Q'][0] + R[k, 2] * m['Q'][1], 1.0, R[k, 3], a_dark=1.0, g_dark=1.0, cleaner=lambda v: clean(v, 220)); fl = y <= 0.5; x[fl] = y[fl]
        out[k] = np.clip(np.rint(x + M.BL), 0, 255); F.guard()
    out.flush(); np.save(outf.replace('removed', 'read'), R); print(outf, 'done')
