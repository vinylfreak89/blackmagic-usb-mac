#!/usr/bin/env python3
"""Per-unit census of the rows around each field's edges, luma AND chroma, for every exact unit of a capture.
Rows: field 1 NTSC lines 16..40 and 250..264; field 2 lines 279..303 and 513..527. Per row: luma mean, luma std
(samples 40..680), Cb mean, Cr mean, chroma std, left/right active-edge sample (first/last luma sample above the
field's own blanking level + 6 x its std). Blanking reference per field per unit: lines 11..19 / 274..282.
Output CSV: one row per (unit, field, line). Usage: edge_rows_census.py <capture> <out.csv>"""
import sys, os, csv, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F={1:dict(blank=(11,19),rows=list(range(16,41))+list(range(250,265))),2:dict(blank=(274,282),rows=list(range(279,304))+list(range(513,528)))}
w=csv.writer(open(sys.argv[2],'w')); w.writerow(['unit','counter','field','line','y_mean','y_std','cb','cr','c_std','left','right','blank_y','blank_ystd','blank_c','blank_cstd'])
st=dict(first=None,n=0); buf=bytearray()
def emit(u):
    c=int.from_bytes(u[4:6],'little'); st['first']=c if st['first'] is None else st['first']; unit=(c-st['first'])&0xffff; st['n']+=1
    R=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE); Y=R[:,1::2].astype(np.float32); Cb=R[:,0::4].astype(np.float32); Cr=R[:,2::4].astype(np.float32)
    for f,S in F.items():
        a,b=S['blank']; by=Y[a-4:b-4+1]; bc=np.concatenate([Cb[a-4:b-4+1],Cr[a-4:b-4+1]])
        by_m,by_s=float(by.mean()),float(by.std()); bc_m,bc_s=float(bc.mean()),float(bc.std()); thr=by_m+6*max(by_s,0.5)
        for l in S['rows']:
            r=Y[l-4]; ab=r>thr; left=int(ab.argmax()) if ab.any() else -1; right=int(len(r)-1-ab[::-1].argmax()) if ab.any() else -1
            cs=float(np.concatenate([Cb[l-4],Cr[l-4]]).std())
            w.writerow([unit,c,f,l,round(float(r.mean()),2),round(float(r[40:680].std()),2),round(float(Cb[l-4].mean()),2),round(float(Cr[l-4].mean()),2),round(cs,2),left,right,round(by_m,2),round(by_s,2),round(bc_m,2),round(bc_s,2)])
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
try: walk_tagged(sys.argv[1],on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:80])
print('units',st['n'],'->',sys.argv[2])
