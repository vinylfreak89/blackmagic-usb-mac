# raw frames on stdin + vstab log -> rows around each logged marker (slot e-8..e+8), luma and full UYVY, to an npz
import numpy as np, sys, csv
log, out = sys.argv[1], sys.argv[2]
M = {}
for r in csv.DictReader(open(log)):
    if r['markers']: M[int(r['field'])] = [int(float(x)) for x in r['markers'].split(';')]
FR = 480 * 1440; inp = sys.stdin.buffer; n = 0; rows = []; meta = []
while True:
    b = inp.read(FR)
    if not b: break
    fr = np.frombuffer(b, np.uint8).reshape(480, 1440)
    for p in (0, 1):
        g = 2 * n + p
        for e in M.get(g, []):
            lo, hi = e - 8 - 20, e + 9 - 20
            if lo >= 0 and hi <= 240: rows.append(fr[p::2][lo:hi].copy()); meta.append((g, e))
    n += 1
np.savez(out, rows=np.array(rows), meta=np.array(meta)); print('vbi_grab: %d frames, %d marker windows' % (n, len(rows)), file=sys.stderr)
