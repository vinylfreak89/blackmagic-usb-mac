# the measured-ghost colour result alone: brightness held at a flat mid level so only colour shows. UYVY 720x240 out.
import numpy as np, sys, multiprocessing as mp
R, S = sys.argv[1], sys.argv[2]; nframes = int(sys.argv[3]) if len(sys.argv) > 3 else None
sys.path.insert(0, R); import hretime as H, unwind as U, gclean as G_
V = np.memmap(S + '/rp/b.uyvy', np.uint8, 'r').reshape(-1, 480, 1440)
dcs, G = np.load(R + '/colour_set2_raw.npy'); dcs = dcs.real.astype(int); G = G * 2.0
n = 360; big = np.concatenate([U.B0 * U.burst_env(), np.zeros(n)]); K = sum(g * np.roll(big, dc)[U.PRE:] for dc, g in zip(dcs, G))
def one(k):
    rt = H.field(np.ascontiguousarray(V[k // 2][k % 2::2]), k); r = slice(2, 238)
    C = U.tone_cancel(G_.chroma(rt[r])); a = U.field_leak_scale(C, K)
    Cc = U.bounded_inverse_colour(C, dcs, G, a * U.B0, 0.15) if a > 0 else C
    out = np.zeros((240, 1440), np.uint8); out[:, 0::2] = 128; out[:, 1::2] = 128
    o = out[r]; o[:, 0::4] = np.clip(np.rint(Cc.real + 128), 0, 255); o[:, 2::4] = np.clip(np.rint(Cc.imag + 128), 0, 255); out[r] = o
    return out.tobytes()
if __name__ == '__main__':
    nf = 2 * (V.shape[0] if nframes is None else nframes); o = sys.stdout.buffer
    with mp.Pool(4) as pool:
        for i, b in enumerate(pool.imap(one, range(nf), chunksize=8)): o.write(b)
    print('chroma_only_render: %d fields' % nf, file=sys.stderr)
