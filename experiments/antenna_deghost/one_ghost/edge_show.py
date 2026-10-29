# still: the owner's review fields, colour ghost removed (seq2) | plus the outline copies edge_avg reads after an edge
# (13-102 samples), removed by edge_deghost with the strengths of the field's own stretch.
# usage: edge_show.py S OUT.png [fields]
import numpy as np, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/../an'); sys.path.insert(0, HERE + '/../an/er')
import seq2
S_ = sys.argv[1]; _a = sys.argv[:]; sys.argv = [_a[0], S_, 'T']; import edge_deghost as D; sys.argv = _a
from PIL import Image, ImageDraw
S, OUT = sys.argv[1], sys.argv[2]
FIELDS = [int(v) for v in (sys.argv[3] if len(sys.argv) > 3 else '5,328,600,1000,1300').split(',')]
NR = 236; BL = 1.5; sh = np.load(S + '/tape_sh.npy'); NF = len(sh)
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(NF, NR, 360))
z = np.load(S + '/tape_chain.npz'); Ts = list(z['Ts']); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])))
if 'Tc' in z.files: ch['cp'] = dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c']))
D.Z = np.load(S + '/edge_avg.npz')
def fillmask(f):
    m = np.zeros((NR, 720), bool)
    for r, c in enumerate(sh[f]):
        if c > 0: m[r, :int(np.ceil(c)) + 1] = True
        elif c < 0: m[r, 720 - int(np.ceil(-c)) - 1:] = True
    return m
def rgb(y, c):
    Yc = y + BL; cb = np.repeat(c.real, 2, 1); cr = np.repeat(c.imag, 2, 1); k = 1.164 * (Yc - 16)
    return np.clip(np.rint(np.stack([k + 1.596 * cr, k - 0.392 * cb - 0.813 * cr, k + 2.017 * cb], -1)), 0, 255).astype(np.uint8)
rows, labels = [], []; gap = np.zeros((NR, 6, 3), np.uint8)
for f in FIELDS:
    y = np.asarray(Yy[f], float); c = np.asarray(Cc[f], complex)
    y2, c2 = seq2.process(y, c, sh[f], ch, Ts, float(z['D']), float(z['sig']), float(z['lam']), B=seq2.field_burst(c, ch, float(z['D'])))
    panels = [rgb(y2, c2)]; lab = ['field %d: colour ghost removed' % f]
    ech = D.tape_echoes(f); panels.append(rgb(D.remove(y2, fillmask(f), ech), c2))
    lab.append('outline copies removed: ' + ', '.join('%d: %.3f' % (T, abs(v)) for T, v in ech))
    row = panels[0]
    for p in panels[1:]: row = np.concatenate([row, gap, p], 1)
    rows.append(row); rows.append(np.zeros((4, row.shape[1], 3), np.uint8)); labels.append(lab)
W = rows[0].shape[1]
img = Image.fromarray(np.concatenate(rows[:-1], 0)).resize((2 * W, 2 * (len(FIELDS) * (NR + 4) - 4)), Image.NEAREST)
d = ImageDraw.Draw(img)
for i, lab in enumerate(labels):
    y0 = 2 * i * (NR + 4) + 4
    for j, t in enumerate(lab):
        x0 = 2 * j * 726 + 4; d.rectangle([x0, y0, x0 + 6.2 * len(t), y0 + 12], fill=(0, 0, 0)); d.text((x0 + 2, y0 + 1), t, fill=(255, 255, 0))
img.save(OUT); print('wrote', OUT); print('\n'.join(' | '.join(l) for l in labels))
