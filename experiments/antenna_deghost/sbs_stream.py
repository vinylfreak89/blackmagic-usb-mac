# frames on stdin (vstab output) -> per field: input | hretime.field(input) as UYVY 1448x240 on stdout; --log FILE
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); import hretime as H
log = open(sys.argv[2], 'w'); log.write('field,line,correction,source\n')
FR = 480 * 1440; BLK = np.tile(np.array([128, 16], np.uint8), 720); gap = np.tile(np.array([128, 16], np.uint8), 8)
inp = sys.stdin.buffer; o = sys.stdout.buffer; n = 0
while True:
    b = inp.read(FR)
    if not b: break
    if len(b) != FR: sys.exit('sbs_stream: short frame after %d' % n)
    fr = np.frombuffer(b, np.uint8).reshape(480, 1440)
    for p in (0, 1):
        f = fr[p::2]; fx = H.field(f, 2 * n + p, log)
        raw = np.concatenate([f[2:240], np.tile(BLK, (2, 1))]); fix = np.concatenate([fx[2:240], np.tile(BLK, (2, 1))])
        o.write(np.concatenate([raw, np.tile(gap, (240, 1)), fix], 1).tobytes())
    n += 1
log.close(); print('sbs_stream: %d frames' % n, file=sys.stderr)
