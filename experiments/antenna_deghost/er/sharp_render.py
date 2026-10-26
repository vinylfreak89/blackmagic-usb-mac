# hretime | sharp ghosts removed (exact frequency-domain inverse, fractional delays; colour with the burst off the edge)
import numpy as np, sys, multiprocessing as mp
R, S = sys.argv[1], sys.argv[2]; nframes = int(sys.argv[3]) if len(sys.argv) > 3 else None
sys.path.insert(0, R); import hretime as H, unwind as U, gclean as G_
V = np.memmap(S + '/rp/b.uyvy', np.uint8, 'r').reshape(-1, 480, 1440)
gh = np.load(R + '/ghosts_sharp.npy'); gy = [(T.real, l.real, a) for T, l, a, b in gh]; gc = [(T.real, l.real, b) for T, l, a, b in gh if T.real >= 40]
def one(k):
    rt = H.field(np.ascontiguousarray(V[k // 2][k % 2::2]), k); r = slice(2, 238)
    Y = rt[r, 1::2].astype(float); C = U.tone_cancel(G_.chroma(rt[r])); a = U.burst_level_exact(C, gc)
    Cc = U.colour_inverse_exact(C, gc, a * U.B0, 0.0); Yc = U.luma_inverse(Y, gy, 0.0)
    cl = rt.copy(); o = cl[r]; o[:, 1::2] = np.clip(np.rint(Yc), 0, 255)
    o[:, 0::4] = np.clip(np.rint(Cc.real + 128), 0, 255); o[:, 2::4] = np.clip(np.rint(Cc.imag + 128), 0, 255); cl[r] = o
    BLK = np.tile(np.array([128, 16], np.uint8), 720); gap = np.tile(np.array([128, 16], np.uint8), 8)
    rows = [np.concatenate([x[2:240], np.tile(BLK, (2, 1))]) for x in (rt, cl)]
    return np.concatenate([rows[0], np.tile(gap, (240, 1)), rows[1]], 1).tobytes()
if __name__ == '__main__':
    nf = 2 * (V.shape[0] if nframes is None else nframes); o = sys.stdout.buffer
    with mp.Pool(4) as pool:
        for i, b in enumerate(pool.imap(one, range(nf), chunksize=8)): o.write(b)
    print('sharp_render: %d fields' % nf, file=sys.stderr)
