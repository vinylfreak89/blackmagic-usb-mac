#!/usr/bin/env python3
# One-off, whole capture, second pass: the accepted luma removal as the plain render's picture filter (PLAIN_RENDER_FILTER):
# 720x480 UYVY frames on stdin, the same number on stdout, luma changed, colour untouched.
#   python3 full_filter.py TABLE.npz FIRST1,FIRST2 [PROCESSES]      (the table: full_table.py; the render's first picture lines)
# Per frame:
#   its row of the table is found by the CRC of line 120 (field 1), searched forward from the last row found; a frame that is in
#     no row (a unit the Shuttle sent short, shown partly or put back by the repair) takes the row after the last one found;
#   the removal is gate.remove_hole on the whole frame (both fields, 240 lines each), the gate is gate.py's with the floor
#     measured on lines 34-253 / 297-516 (the lines the accepted setting measured it on) and weighted along time exactly as
#     gate.py remove does (Gaussian, GATESMOOTH frames: the filter reads 21 frames ahead for it);
#   the table's weight (trade, test bar present) scales the correction.  A frame whose weight is 0 leaves as it came, byte for byte.
# The frames are worked on by several processes, in order, with a bounded number in flight.
# Exit status (non-zero fails the render, and the render it would replace stays): 3 too few frames found in the table,
# 4 a long run of frames not found, 5 input ended inside a frame, 6 memory.
import sys, os, zlib, time, resource, collections, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.update(KAPPA='9', STEADY='1', MEDIAN='0', THIN='0', HOLE='0.25', GMAX='3', GATESMOOTH='5', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
import model as M, gate as G
G.HALF = 240; W_, H_ = 720, 480; FB = W_ * H_ * 2; AHEAD = int(4 * G.GATESMOOTH) + 1; INFLIGHT = 8; SIGLINE = 120; REACH = 400; LOSTRUN = 3000
def floor_rows(f1, f2):                 # stacked fields (field 1 rows 0-239, field 2 rows 240-479): the rows of lines 34-253 and 297-516
    a = np.arange(34, 254) - f1; b = np.arange(297, 517) - f2; return np.r_[a[(a >= 0) & (a < 240)], 240 + b[(b >= 0) & (b < 240)]]
def stack(fr): y = fr[:, 1::2]; return np.vstack([y[0::2], y[1::2]]).astype(float) - M.BL
def init(rows): global ROWS; ROWS = rows
def work(args):                         # the correction, its local size, and the frame's own gate floor
    raw, q = args; Y = stack(np.frombuffer(raw, np.uint8).reshape(H_, 2 * W_)); C = G.remove_hole(Y, G.spec(q)) - Y; A = G.size(C); return C, A, float(np.percentile(A[ROWS][:, 30:690], G.PCT))
class Matcher:
    def __init__(self, sig):
        o = np.argsort(sig, kind='stable'); s = sig[o]; cut = np.nonzero(np.diff(s))[0] + 1; self.idx = dict(zip(s[np.r_[0, cut]].tolist(), np.split(o, cut))); self.n = len(sig); self.last = -1; self.miss = 0; self.found = 0; self.frames = 0
    def row(self, crc):
        self.frames += 1; c = self.idx.get(crc)
        if c is not None:
            i = np.searchsorted(c, self.last + 1)
            if i < len(c) and c[i] - self.last <= REACH: self.last = int(c[i]); self.miss = 0; self.found += 1; return self.last
        self.miss += 1; return min(max(self.last, 0) + self.miss, self.n - 1)
def smooth_floor(ths, k):               # gate.tsmooth at frame k of the floors known (nan: a frame nothing was worked out for)
    num = den = 0.0
    for o in range(-AHEAD, AHEAD + 1):
        v = ths.get(k + o)
        if v is not None and v == v: w = np.exp(-0.5 * (o / G.GATESMOOTH) ** 2); num += w * v; den += w
    return num / den if den else float('nan')
def main():
    from multiprocessing import get_context
    t = np.load(sys.argv[1]); Q, Wt = t['Q'], t['w']; f1, f2 = (int(x) for x in sys.argv[2].split(',')); procs = int(sys.argv[3]) if len(sys.argv) > 3 else 4; rows = floor_rows(f1, f2); sigrow = 2 * (SIGLINE - f1)
    need = np.convolve((Wt > 0).astype(float), np.ones(2 * AHEAD + 3), mode='same') > 0      # a row whose floor some frame's gate will use
    os.nice(10); mt = Matcher(t['sig']); pool = get_context('spawn').Pool(procs, init, (rows,)); src, dst = sys.stdin.buffer, sys.stdout.buffer
    ent = collections.OrderedDict(); ths = {}; nread = nout = worked = changed = 0; eof = False; t0 = time.time(); log = lambda s: print(s, file=sys.stderr, flush=True)
    log('table: %d rows; first lines %d,%d; %d processes; reading %d frames ahead' % (len(Wt), f1, f2, procs, AHEAD))
    while True:
        while not eof and nread - nout <= AHEAD + INFLIGHT:
            raw = src.read(FB)
            if len(raw) == 0: eof = True; break
            if len(raw) != FB: log('input ended inside frame %d' % nread); sys.exit(5)
            j = mt.row(zlib.crc32(raw[sigrow * 2 * W_:(sigrow + 1) * 2 * W_]))
            if mt.miss >= LOSTRUN: log('%d frames in a row not found in the table (at frame %d)' % (mt.miss, nread)); sys.exit(4)
            ent[nread] = (raw, j, pool.apply_async(work, ((raw, Q[j]),)) if need[j] else None); nread += 1
        if nout == nread: break
        if not eof and nread - nout <= AHEAD: continue
        for k in range(nout, min(nread, nout + AHEAD + 1)):                                    # the floors frame nout's gate needs
            if k not in ths: r = ent[k][2]; ths[k] = r.get()[2] if r is not None else float('nan')
        raw, j, r = ent.pop(nout); w = float(Wt[j])
        if w > 0 and r is not None:
            C, A, _ = r.get(); th = smooth_floor(ths, nout); m = np.clip(1 - G.KAPPA * th ** 2 / np.maximum(A ** 2, 1e-9), 0, 1); fr = np.frombuffer(raw, np.uint8).reshape(H_, 2 * W_).copy(); X = np.clip(np.rint(stack(fr) + w * m * C + M.BL), 0, 255).astype(np.uint8)
            fr[0::2, 1::2] = X[:240]; fr[1::2, 1::2] = X[240:]; out = fr.tobytes(); changed += out != raw; worked += 1
        else: out = raw
        dst.write(out); ths.pop(nout - AHEAD - 1, None); nout += 1
        if nout % 2000 == 0: log('%6d frames out, %d found in the table, %d worked on; %.0f s, %.1f frames/s' % (nout, mt.found, worked, time.time() - t0, nout / (time.time() - t0)))
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 3 << 30: log('memory over 3 GB, stopping'); sys.exit(6)
    dst.flush(); pool.close(); pool.join()
    log('frames %d in, %d out; found in the table %d (table rows %d); worked on %d, changed %d; %.0f s' % (nread, nout, mt.found, mt.n, worked, changed, time.time() - t0))
    if mt.found < 0.98 * nread or mt.found < 0.98 * mt.n: log('too few frames found in the table: this is not the capture the table was made from, or not these first lines'); sys.exit(3)
if __name__ == '__main__':
    main()
