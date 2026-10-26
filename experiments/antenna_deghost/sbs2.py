# side by side per field from hretime's own output on stdin: TBC-off as captured | hretime output (UYVY 1448x240 per field)
import numpy as np, sys
S=sys.argv[1]; V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440); FR=480*1440
BLK=np.tile(np.array([128,16],np.uint8),720); gap=np.tile(np.array([128,16],np.uint8),8)
inp=sys.stdin.buffer; o=sys.stdout.buffer; n=0
while True:
    b=inp.read(FR)
    if not b: break
    assert len(b)==FR, 'short frame'
    fx=np.frombuffer(b,np.uint8).reshape(480,1440)
    for p in (0,1):
        raw=np.concatenate([V[n][p::2][2:240],np.tile(BLK,(2,1))]); fix=np.concatenate([fx[p::2][2:240],np.tile(BLK,(2,1))])
        o.write(np.concatenate([raw,np.tile(gap,(240,1)),fix],1).tobytes())
    n+=1
assert n==V.shape[0], (n, V.shape[0])
print('sbs2: %d frames'%n, file=sys.stderr)
