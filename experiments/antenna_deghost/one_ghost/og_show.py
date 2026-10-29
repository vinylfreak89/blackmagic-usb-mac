# still: the owner's review fields, two panels each: colour ghost removed (seq2) | plus the one strong brightness echo
# removed (og_remove) at the whole-tape delay, using the strength measured on the field's OWN stretch (og_tape_measure),
# whether or not that stretch passed the render rule.  Labels give the strength, the stretch's null-delay maximum and
# whether it passed.  usage: og_show.py S PER OUT.png [fields]
import numpy as np, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/../an'); sys.path.insert(0, HERE + '/../an/er')
import seq2, og_remove as RM
from PIL import Image, ImageDraw
S, PER, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
FIELDS = [int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else '5,328,600,1000,1300').split(',')]
NR = 236; BL = 1.5; sh = np.load(S + '/tape_sh.npy'); NF = len(sh)
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(NF, NR, 360))
z = np.load(S + '/tape_chain.npz'); Ts = list(z['Ts']); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])))
if 'Tc' in z.files: ch['cp'] = dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c']))
st = np.load(S + '/og_strengths_%d.npz' % PER); T = float(st['T'])
use = (np.abs(st['g']) > 3 * st['null_max']) & (np.abs(st['g']) > 4 * st['sd'])
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
    k = int(np.searchsorted(st['f1'], f, side='right')); g = complex(st['g'][k])
    y = np.asarray(Yy[f], float); c = np.asarray(Cc[f], complex)
    y2, c2 = seq2.process(y, c, sh[f], ch, Ts, float(z['D']), float(z['sig']), float(z['lam']), B=seq2.field_burst(c, ch, float(z['D'])))
    y3 = RM.remove(y2, fillmask(f), T, g)
    rows.append(np.concatenate([rgb(y2, c2), gap, rgb(y3, c2)], 1)); rows.append(np.zeros((4, rows[-1].shape[1], 3), np.uint8))
    labels.append('field %d: echo at %.1f, strength %.2f at %+.0f deg (stretch %d-%d, empty-delay control %.2f, %s)'
                  % (f, T, abs(g), np.degrees(np.angle(g)), st['f0'][k], st['f1'][k] - 1, st['null_max'][k], 'passed' if use[k] else 'FAILED the rule'))
img = Image.fromarray(np.concatenate(rows[:-1], 0)).resize((2 * 726, 2 * (len(FIELDS) * (NR + 4) - 4)), Image.NEAREST)
d = ImageDraw.Draw(img)
for i, t in enumerate(labels):
    y0 = 2 * i * (NR + 4) + 4
    d.rectangle([4, y0, 4 + 6.2 * 20, y0 + 12], fill=(0, 0, 0)); d.text((6, y0 + 1), 'colour ghost removed', fill=(255, 255, 0))
    d.rectangle([732 + 4, y0, 732 + 4 + 6.2 * len(t), y0 + 12], fill=(0, 0, 0)); d.text((732 + 6, y0 + 1), t, fill=(255, 255, 0))
img.save(OUT); print('wrote', OUT); print('\n'.join(labels))
