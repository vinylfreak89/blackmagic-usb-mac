# per field of the TBC-off pass: hretime (committed) | hretime + ghost copies unwound (8 per field, strongest first,
# colour and brightness; colour sources in the leaked-burst region are off the grid). UYVY 1448x240 per field on stdout.
import numpy as np, sys, multiprocessing as mp
R, S = sys.argv[1], sys.argv[2]; nframes = int(sys.argv[3]) if len(sys.argv) > 3 else None
sys.path.insert(0, R); import hretime as H, unwind as U, gclean as G
V = np.memmap(S + '/rp/b.uyvy', np.uint8, 'r').reshape(-1, 480, 1440)
STEPS = 8
def one(n):
    rt = H.field(np.ascontiguousarray(V[n // 2][n % 2::2]), n); r = slice(2, 238)
    Y = rt[r, 1::2].astype(float); C = G.chroma(rt[r])
    Yc = U.unwind(Y, np.arange(16, 200, 2.0), STEPS, True, t0=60)[-1]
    Cc = U.unwind(C, np.arange(30, 100, 1.0), STEPS, False, t0=30, first=55)[-1]
    cl = rt.copy(); o = cl[r]; o[:, 1::2] = np.clip(np.rint(Yc), 0, 255)
    o[:, 0::4] = np.clip(np.rint(Cc.real + 128), 0, 255); o[:, 2::4] = np.clip(np.rint(Cc.imag + 128), 0, 255); cl[r] = o
    BLK = np.tile(np.array([128, 16], np.uint8), 720); gap = np.tile(np.array([128, 16], np.uint8), 8)
    rows = [np.concatenate([x[2:240], np.tile(BLK, (2, 1))]) for x in (rt, cl)]
    return np.concatenate([rows[0], np.tile(gap, (240, 1)), rows[1]], 1).tobytes()
if __name__ == '__main__':
    n = 2 * (V.shape[0] if nframes is None else nframes); o = sys.stdout.buffer
    with mp.Pool(4) as pool:
        for i, b in enumerate(pool.imap(one, range(n), chunksize=4)):
            o.write(b)
            if i % 100 == 0: print('unwind_render: field %d of %d' % (i, n), file=sys.stderr, flush=True)
    print('unwind_render: %d fields' % n, file=sys.stderr)
