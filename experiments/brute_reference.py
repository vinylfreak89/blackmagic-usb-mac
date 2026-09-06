#!/usr/bin/env python3
"""Brute-force reference, pass 1 (per unit, per field, no thresholds, no row classification):
  cap_line   the unique line of the field (NTSC 12..266 / 275..528, every line tried) whose CEA-608 decode has valid
             odd parity, excluding the device's own regenerated 21/284; '' if none, 'multi' if more than one
  shift      the vertical shift in -6..+6 at which the whole picture body (rows origin+10..origin+230, all 640 active
             columns, raw luma) best matches the previous unit's same field; with mad, and second-best mad
  flat       row-to-row std of the field's body (a mute/flat raster has ~none)
Pass 2 (chain_reference.py) turns cap_line into absolute displacement anchors and chains shifts between them.
Slow by design; run over the whole tape in the background.
Usage: brute_reference.py <capture> <out.csv>"""
import sys, os, csv, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from cc608_decode import decode
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
FIELDS={1:dict(origin=19, lines=range(12,267), insert=21), 2:dict(origin=282, lines=range(275,529), insert=284)}
CAP,OUT=sys.argv[1],sys.argv[2]
w=csv.writer(open(OUT,'w',newline='')); w.writerow(['n','counter','field','cap_line','shift','mad','mad2','flat'])
st=dict(n=0, ext=None, prev={1:None,2:None}); buf=bytearray()
def emit(u):
    c16=int.from_bytes(u[4:6],'little')
    if st['ext'] is None: st['ext']=c16
    else: st['ext']+=(c16-(st['ext']&0xffff))&0xffff
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2]
    for f,F in FIELDS.items():
        hits=[ln for ln in F['lines'] if ln!=F['insert'] and decode(Y[ln-4])[0]]
        cap='' if not hits else (str(hits[0]) if len(hits)==1 else 'multi')
        body=Y[F['origin']+10:F['origin']+230,40:680].astype(np.int16)
        flat=float(np.abs(np.diff(body.astype(np.float32),axis=0)).mean())
        shift=mad=mad2=''
        P=st['prev'][f]
        if P is not None:
            res=sorted(((s,float(np.abs(P[6:-6]-body[6+s:6+s+len(P)-12]).mean())) for s in range(-6,7)),key=lambda x:x[1])
            shift,mad,mad2=res[0][0],round(res[0][1],2),round(res[1][1],2)
        st['prev'][f]=body
        w.writerow([st['n'],st['ext'],f,cap,shift,mad,mad2,round(flat,2)])
    st['n']+=1
    if st['n']%2000==0: print('units',st['n'],flush=True)
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
try: walk_tagged(CAP,on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:100])
print('units',st['n'],'->',OUT)
