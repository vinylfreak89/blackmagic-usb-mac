# per field of the TBC-off pass: hretime | ghosts removed with copies measured from known signals:
# colour = colour-transition copies (colour fields, tone cancelled) x2, bounded two-sided inverse, burst level per field
# from its leak; brightness = bright-transition copies x2, left-to-right sweep from clean sources. UYVY 1448x240 out.
import numpy as np, sys, multiprocessing as mp
R, S = sys.argv[1], sys.argv[2]; nframes = int(sys.argv[3]) if len(sys.argv) > 3 else None
sys.path.insert(0, R); import hretime as H, unwind as U, gclean as G_
V = np.memmap(S + '/rp/b.uyvy', np.uint8, 'r').reshape(-1, 480, 1440)
dcs, G = np.load(R + '/colour_set2_raw.npy'); dcs = dcs.real.astype(int); G = G * 2.0
dy, gy = np.load(R + '/luma_set.npy'); dy = dy.real.astype(int); ghy = list(zip(dy, gy * 2.0))
n = 360; big = np.concatenate([U.B0 * U.burst_env(), np.zeros(n)]); K = sum(g * np.roll(big, dc)[U.PRE:] for dc, g in zip(dcs, G))
def one(k):
    rt = H.field(np.ascontiguousarray(V[k // 2][k % 2::2]), k); r = slice(2, 238)
    Y = rt[r, 1::2].astype(float); C = U.tone_cancel(G_.chroma(rt[r])); a = U.field_leak_scale(C, K)
    Cc = U.bounded_inverse_colour(C, dcs, G, a * U.B0, 0.15) if a > 0 else C
    Yc = U.remove_luma_clean(Y, ghy, U.BL, sync_depth=0.0)
    cl = rt.copy(); o = cl[r]; o[:, 1::2] = np.clip(np.rint(Yc), 0, 255)
    o[:, 0::4] = np.clip(np.rint(Cc.real + 128), 0, 255); o[:, 2::4] = np.clip(np.rint(Cc.imag + 128), 0, 255); cl[r] = o
    BLK = np.tile(np.array([128, 16], np.uint8), 720); gap = np.tile(np.array([128, 16], np.uint8), 8)
    rows = [np.concatenate([x[2:240], np.tile(BLK, (2, 1))]) for x in (rt, cl)]
    return np.concatenate([rows[0], np.tile(gap, (240, 1)), rows[1]], 1).tobytes()
if __name__ == '__main__':
    nf = 2 * (V.shape[0] if nframes is None else nframes); o = sys.stdout.buffer
    with mp.Pool(4) as pool:
        for i, b in enumerate(pool.imap(one, range(nf), chunksize=4)):
            o.write(b)
            if i % 200 == 0: print('measured_render: field %d of %d' % (i, nf), file=sys.stderr, flush=True)
    print('measured_render: %d fields' % nf, file=sys.stderr)
