#!/usr/bin/env python3
"""Field-1 caption position per unit (fixture A caption labels; an instrument for scoring placement, never a
placement source). Usage: cc_f1_census.py CAPTURE.tpc OUT.csv. Restored 2026-10-02 from the 2026-09-26 session.
Decode the Shuttle insert (line 21) and tape lines 22-27 with
experiments/cc608_decode.decode (run-in + start bits + odd parity). Writes counter, and either the displacement of
the first tape line that decodes (line-21), 'near0' when only the insert decodes non-null bytes, or nothing."""
import sys, numpy as np
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import geometry_render as g
from packet_capture_reader import walk_tagged
from cc608_decode import decode
out=open(sys.argv[2],'w'); out.write('counter,f1\n'); n=[0]
def emit(u):
    if not u.get('complete'): return
    n[0]+=1
    Y=np.frombuffer(u['bytes'],np.uint8)[48:].reshape(525,1440)[:,1::2]
    m=''
    for L in range(22,28):
        ok,b1,b2,_=decode(Y[L-4])
        if ok: m=str(L-21); break
    if not m:
        ok,b1,b2,_=decode(Y[17])
        if ok and not (b1 in (128,0) and b2 in (128,0)): m='near0'
    out.write(f'{u["ext"]},{m}\n')
    if n[0]%10000==0: print('units',n[0],flush=True)
fr=g.Framer(emit); walk_tagged(sys.argv[1],on_video=lambda p: fr.feed(p),progress=False); out.close(); print('done',n[0])
