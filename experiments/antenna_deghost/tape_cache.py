# antenna tape, TBC-off pass: retime every field once and keep the retimed lines (rows 2..237) with each line's shift,
# so the ghost passes can run over the whole tape in chunks.  luma float32 (code - 1.5), colour complex64 (Cb-128, Cr-128)
import numpy as np, sys, os, io, time, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/er')
import hretime as H
SRC, OUT = sys.argv[1], sys.argv[2]; BL = 1.5; ROWS = slice(2, 238); NR = 236
V = np.memmap(SRC, np.uint8, 'r').reshape(-1, 480, 1440); NF = 2 * V.shape[0]
def one(k):
    raw = np.ascontiguousarray(V[k // 2][k % 2::2]); log = io.StringIO(); rt = H.field(raw, k, log=log); sh = np.zeros(240)
    for line in log.getvalue().split():
        _, ln, c, _ = line.split(','); sh[int(ln) - H.FIRST] = float(c)
    Yy = np.memmap(OUT + '_y.f32', np.float32, 'r+', shape=(NF, NR, 720)); Cc = np.memmap(OUT + '_c.c64', np.complex64, 'r+', shape=(NF, NR, 360))
    Yy[k] = rt[ROWS, 1::2].astype(np.float32) - BL; Cc[k] = (rt[ROWS, 0::4].astype(np.float32) - 128) + 1j * (rt[ROWS, 2::4].astype(np.float32) - 128)
    Yy.flush(); Cc.flush(); del Yy, Cc
    return k, sh[ROWS]
if __name__ == '__main__':
    t0 = time.time()
    np.memmap(OUT + '_y.f32', np.float32, 'w+', shape=(NF, NR, 720)).flush(); np.memmap(OUT + '_c.c64', np.complex64, 'w+', shape=(NF, NR, 360)).flush()
    sh = np.zeros((NF, NR)); done = 0
    with mp.Pool(4) as p:
        for k, s in p.imap_unordered(one, range(NF), chunksize=8): sh[k] = s; done += 1
    assert done == NF, (done, NF)
    np.save(OUT + '_sh.npy', sh); print('%d fields x %d lines cached in %.0f s' % (NF, NR, time.time() - t0))
