#!/usr/bin/env python3
"""Per unit per field: the luma mean/std of the first pass-through rows (lines 23-26 / 286-289) and the blanking level,
to decide whether a dark first row is a VBI row (its level content-independent across units) or picture (its level
following the scene). Usage: first_row_level_census.py <capture.tpc> <out.csv> [--from-counter N]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out'); ap.add_argument('--from-counter',type=int,default=0); A=ap.parse_args()
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['unit','counter','field','blank','r23','s23','r24','s24','r25','s25','r26','s26'])
buf=bytearray(); N=[0]
def emit(u):
    c=int.from_bytes(u[4:6],'little'); i=N[0]; N[0]+=1
    if c<A.from_counter: return
    R=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)
    for f,base in ((1,16),(2,279)):
        Y=R[:,1::2].astype(np.float32)
        blank=float(Y[base-9:base,40:680].mean())
        row=[i,c,f,round(blank,2)]
        for k in (3,4,5,6):
            seg=Y[base+k,40:680]; row+= [round(float(seg.mean()),2), round(float(seg.std()),2)]
        w.writerow(row)
def on_video(p):
    buf.extend(p)
    while True:
        i=buf.find(MARK)
        if i<0: return
        if i>0: del buf[:i]
        j=buf.find(MARK,4)
        if j<0: return
        if j==UNIT: emit(bytes(buf[:UNIT]))
        del buf[:j]
try: walk_tagged(A.cap,on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:60])
print('units',N[0],'->',A.out)
