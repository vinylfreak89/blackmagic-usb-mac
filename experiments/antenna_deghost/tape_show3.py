# five fields, three panels: retimed | colour ghost removed | colour + brightness cluster 84-129 removed.
# FLAG: the brightness measurement FAILS its known-answer test (strength errors 0.06-0.13) and the cluster contradicts
# the tape's no-picture lines; rendered on the owner's request to see what it does.
import numpy as np, sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import seq2, bright_seq as Bq
from PIL import Image, ImageDraw
S, OUT = sys.argv[1], sys.argv[2]; FIELDS = [328, 600, 1000, 1300, 5]
NR = 236; BL = 1.5; sh = np.load(S + '/tape_sh.npy'); NF = len(sh)
Yy = np.memmap(S + '/tape_y.f32', np.float32, 'r', shape=(NF, NR, 720)); Cc = np.memmap(S + '/tape_c.c64', np.complex64, 'r', shape=(NF, NR, 360))
z = np.load(S + '/tape_chain.npz'); ch = dict(Gy=z['Gy'], Gc=z['Gc'], start=(z['gy0'], z['gc0'], float(z['B'])), cp=dict(Tc=list(z['Tc']), sig_c=float(z['sig_c']), lam_c=float(z['lam_c'])))
G = np.load(S + '/sync_edge_ghosts.npy'); blur = {float(T): (float(sg), float(lm)) for T, sg, lm, _, _ in G}; Ts = [float(T) for T in G[:, 0]]
md = np.load(S + '/ripple_bins.npy')[0]
chy = Bq.run(md, Ts, blur, 14.0, nuisance=(79.0,))
def rgb(y, c):
    Yc = y + BL; cb = np.repeat(c.real, 2, 1); cr = np.repeat(c.imag, 2, 1); k = 1.164 * (Yc - 16)
    return np.clip(np.rint(np.stack([k + 1.596 * cr, k - 0.392 * cb - 0.813 * cr, k + 2.017 * cb], -1)), 0, 255).astype(np.uint8)
rows = []; gap = np.zeros((NR, 6, 3), np.uint8)
for f in FIELDS:
    y = np.asarray(Yy[f], float); c = np.asarray(Cc[f], complex)
    Bf = seq2.field_burst(c, ch, float(z['D'])); _, c2 = seq2.process(y, c, sh[f], ch, [], float(z['D']), 1.5, 2.0, B=Bf)
    y3 = Bq.process_y(y, sh[f], chy)
    rows.append(np.concatenate([rgb(y, c), gap, rgb(y, c2), gap, rgb(y3, c2)], 1)); rows.append(np.zeros((4, rows[-1].shape[1], 3), np.uint8))
img = Image.fromarray(np.concatenate(rows[:-1], 0)); d = ImageDraw.Draw(img)
for x, t in ((4, 'retimed'), (730, 'colour ghost removed'), (1456, 'colour + brightness 84-129 removed (FAILS known-answer test)')):
    d.rectangle([x - 2, 2, x + 6.2 * len(t), 14], fill=(0, 0, 0)); d.text((x, 3), t, fill=(255, 255, 0))
img.save(OUT); print('wrote', OUT)
