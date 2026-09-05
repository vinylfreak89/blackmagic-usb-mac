#!/usr/bin/env python3
"""Contact sheet for seam/splice candidates: inside a slice, re-run the band test (upper vs lower picture band of a field
shifting by different amounts against the previous unit, or one band continuous while another is new) and render the
previous and current RAW rasters side by side for the first N firing units, so each candidate is classified on the
picture. Usage: seam_triage.py <slice.tpc> <out.png> [N]"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from PIL import Image, ImageDraw
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CAP,OUT=sys.argv[1],sys.argv[2]; N=int(sys.argv[3]) if len(sys.argv)>3 else 4
units=[]; buf=bytearray()
def emit(u): units.append(np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].copy())
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
except RuntimeError: pass
def vshift(P,Y,lo,hi):
    return min(((s,float(np.abs(P[lo:hi].astype(np.float32)-Y[lo+s:hi+s].astype(np.float32)).mean())) for s in range(-6,7)),key=lambda x:x[1])
def mad(P,Y,lo,hi): return float(np.abs(P[lo:hi].astype(np.float32)-Y[lo:hi].astype(np.float32)).mean())
hits=[]
for i in range(1,len(units)):
    P,Y=units[i-1],units[i]
    f1u=vshift(P,Y,30,120); f1l=vshift(P,Y,150,250); f2u=vshift(P,Y,293,383); f2l=vshift(P,Y,413,513)
    seam=lambda a,b: abs(a[0]-b[0])>=2 and a[1]<12 and b[1]<12
    m=[mad(P,Y,a,b) for a,b in ((22,100),(100,180),(180,255),(285,363),(363,443),(443,518))]
    spl=(min(m[:3])<8 and max(m[:3])>30) or (min(m[3:])<8 and max(m[3:])>30)
    if seam(f1u,f1l) or seam(f2u,f2l) or spl:
        hits.append((i,f"seam f1 {f1u[0]}/{f1l[0]} f2 {f2u[0]}/{f2l[0]} mads {f1u[1]:.0f}/{f1l[1]:.0f}/{f2u[1]:.0f}/{f2l[1]:.0f}" + (" SPLICE bands "+"/".join(f"{x:.0f}" for x in m) if spl else "")))
print('units',len(units),'hits',len(hits))
sel=hits[:N] if len(hits)<=N else [hits[k*len(hits)//N] for k in range(N)]
TW,TH=360,262; img=Image.new('L',(2*TW+8,len(sel)*(TH+18)+4),0); d=ImageDraw.Draw(img); y=2
for i,lab in sel:
    d.text((4,y+2),f"unit {i-1} -> {i}: {lab}",fill=255); y+=18
    for k,Y in enumerate((units[i-1],units[i])):
        t=Y[::2,::2][:TH,:TW]; img.paste(Image.fromarray(t),(k*(TW+8),y))
    y+=TH
img.save(OUT); print('saved',OUT,[h[0] for h in sel])
