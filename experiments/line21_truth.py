#!/usr/bin/env python3
# Whole-tape line-21 truth set for the v9 acceptance test: per unit, which NTSC lines in each field decode as CEA-608
# with valid parity (cc608_decode), with their bytes. Scans the FULL fields (lines 12-266 and 272-528, unit rows r =
# line-4) with a vectorised run-in amplitude gate so only plausible lines reach the bit decoder. Output CSV: unit,counter,f1_lines,f1_bytes,f2_lines,f2_bytes,insert21,insert284
import sys, csv, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from packet_capture_reader import walk_tagged
from cc608_decode import decode
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CAP=sys.argv[1]; OUT=sys.argv[2]; N=int(sys.argv[3]) if len(sys.argv)>3 else 10**9
F1=list(range(8,263)); F2=list(range(268,525))      # full fields: lines 12-266 and 272-528 (the engine scans the same)
CELL=1.986e-6*13.5e6; _n=np.arange(10,230); _cos=np.cos(2*np.pi/CELL*_n); _sin=np.sin(2*np.pi/CELL*_n)
def amp_gate(Y,rows):
    A=Y[rows,10:230]; A=A-A.mean(axis=1,keepdims=True)
    amp=np.hypot(A@_cos,A@_sin)*2/A.shape[1]
    return [r for r,a in zip(rows,amp) if a>=35]
class Done(Exception): pass
buf=bytearray(); st={'n':0}; w=csv.writer(open(OUT,'w',newline='')); w.writerow(['unit','counter','f1_lines','f1_bytes','f2_lines','f2_bytes','insert21','insert284'])
def dec(Y,rows):
    L=[];B=[]
    for r in amp_gate(Y,rows):
        ok,b1,b2,_=decode(Y[r])
        if ok: L.append(str(r+4)); B.append(f"{b1:02x}{b2:02x}")
    return ' '.join(L), ' '.join(B)
def emit(u):
    n=st['n']; st['n']+=1
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)
    ctr=int.from_bytes(u[4:6],'little')
    i21=decode(Y[17]); i284=decode(Y[280])
    f1=dec(Y,F1); f2=dec(Y,F2)
    w.writerow([n,ctr,f1[0],f1[1],f2[0],f2[1],(f"{i21[1]:02x}{i21[2]:02x}" if i21[0] else 'none'),(f"{i284[1]:02x}{i284[2]:02x}" if i284[0] else 'none')])
    if st['n']>=N: raise Done()
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
try: walk_tagged(CAP, on_video=on_video, progress=False)
except Done: pass
print(f"wrote {OUT}: {st['n']} units")
