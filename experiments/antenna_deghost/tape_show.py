# five fields of the antenna tape: retimed (left) | ghost sequence applied (right).  Each field at full height.
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import seq2
from PIL import Image
S, OUT = sys.argv[1], sys.argv[2]; FIELDS = [int(f) for f in (sys.argv[3] if len(sys.argv) > 3 else '328,600,1000,1300,5').split(',')]
NR = 236; BL = 1.5; sh = np.load(S + '/tape_sh.npy'); NF = len(sh)
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(NF, NR, 360))
z = np.load(S + '/tape_chain.npz'); Ts = list(z['Ts']); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])))
if 'Tc' in z.files: ch['cp'] = dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c']))
def rgb(y, c):
    Yc = y + BL; cb = np.repeat(c.real, 2, 1); cr = np.repeat(c.imag, 2, 1); k = 1.164 * (Yc - 16)
    out = np.stack([k + 1.596 * cr, k - 0.392 * cb - 0.813 * cr, k + 2.017 * cb], -1)
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)
rows = []
for f in FIELDS:
    y = np.asarray(Yy[f], float); c = np.asarray(Cc[f], complex)
    Bf = seq2.field_burst(c, ch, float(z['D'])) if os.environ.get('PERFIELD', '1') == '1' else None
    y2, c2 = seq2.process(y, c, sh[f], ch, Ts, float(z['D']), float(z['sig']), float(z['lam']), B=Bf)
    print('field %d: own burst level %s' % (f, 'pooled' if Bf is None else '%.2f∠%+.0f' % (abs(Bf), np.degrees(np.angle(Bf)))))
    gap = np.zeros((NR, 6, 3), np.uint8)
    rows.append(np.concatenate([rgb(y, c), gap, rgb(y2, c2)], 1)); rows.append(np.zeros((4, 1446, 3), np.uint8))
Image.fromarray(np.concatenate(rows[:-1], 0)).save(OUT)
print('wrote', OUT)
