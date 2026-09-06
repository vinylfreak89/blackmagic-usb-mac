#!/usr/bin/env python3
"""Per unit per field: the picture body's vertical shift against the previous unit's same field (brute force -3..+3
over rows 24..224 of the field, samples 60..660, minimum mean |diff|) with the decisiveness ratio best/second-best.
A pan moves both fields by the same amount (a slow one alternates fields unit to unit); a field shift moves one field
while the other holds. Contract v3 §10.5: the witness for a field that moved under a clamped top.
Usage: field_body_shift.py <capture> <out.csv> [--repair]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out'); ap.add_argument('--repair',action='store_true'); A=ap.parse_args()
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['unit','counter','f1_shift','f1_ratio','f2_shift','f2_ratio'])
prev={1:None,2:None}; st=dict(n=0,pend=None); buf=bytearray()
def vshift(a,b):
    ref=b[24:224,60:660]; res=sorted(((s,float(np.abs(a[24+s:224+s,60:660]-ref).mean())) for s in range(-3,4)),key=lambda x:x[1]); return res[0][0],round(res[0][1]/max(res[1][1],1e-6),3)
def fields(Y,Yn):
    if A.repair: return {1:Y[282:522],2:(Yn[19:259] if Yn is not None else None)}
    return {1:Y[19:259],2:Y[282:522]}
def handle(u,c,Y,Yn):
    F=fields(Y,Yn); out=[u,c]
    for f in (1,2):
        cur=F[f]
        if cur is None or prev[f] is None: out+=['','']
        else: s,r=vshift(cur,prev[f]); out+=[s,r]
        prev[f]=cur
    w.writerow(out)
def emit(u):
    c=int.from_bytes(u[4:6],'little'); Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)
    if A.repair:
        if st['pend'] is not None: handle(st['n']-1,st['pend'][0],st['pend'][1],Y)
        st['pend']=(c,Y)
    else: handle(st['n'],c,Y,None)
    st['n']+=1
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
print('units',st['n'],'->',A.out)
