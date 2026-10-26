# deghosted frames on stdin; original frames from a file -> per field: hretime(original) | hretime(deghosted), UYVY 1448x240
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); import hretime as H
V = np.memmap(sys.argv[2], np.uint8, 'r').reshape(-1, 480, 1440)
logA = open(sys.argv[3], 'w'); logB = open(sys.argv[4], 'w')
for l in (logA, logB): l.write('field,line,correction,source\n')
FR = 480 * 1440; BLK = np.tile(np.array([128, 16], np.uint8), 720); gap = np.tile(np.array([128, 16], np.uint8), 8)
inp = sys.stdin.buffer; o = sys.stdout.buffer; n = 0
while True:
    b = inp.read(FR)
    if not b: break
    fd = np.frombuffer(b, np.uint8).reshape(480, 1440)
    for p in (0, 1):
        a = H.field(V[n][p::2], 2 * n + p, logA); d = H.field(fd[p::2], 2 * n + p, logB)
        rows = [np.concatenate([x[2:240], np.tile(BLK, (2, 1))]) for x in (a, d)]
        o.write(np.concatenate([rows[0], np.tile(gap, (240, 1)), rows[1]], 1).tobytes())
    n += 1
assert n == V.shape[0], (n, V.shape[0]); print('sbs_dg: %d frames' % n, file=sys.stderr)
