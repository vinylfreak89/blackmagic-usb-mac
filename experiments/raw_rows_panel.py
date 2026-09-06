#!/usr/bin/env python3
"""Raw-row panels for named units of a capture, for reading by eye (computer vision), never from a rendered video.
Each unit: four strips, vertically magnified, NTSC line numbers and the row's luma mean/std at the left of every row:
field-1 top lines 16..32, field-1 bottom lines 252..268, field-2 top lines 279..295, field-2 bottom lines 515..528.
No crop, no engine output drawn: the raster as captured. Units are named by counter-based ordinal (counter - first
counter of the capture, the number burned into the review render), or by --counter.
Also writes <out>.census.csv: for EVERY exact unit of the capture, the mean and std of each of those rows, so
questionable units can be chosen by number and then looked at.
Usage: raw_rows_panel.py <capture> <out.png> --units 551,600,650 [--mag 6]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from PIL import Image, ImageDraw
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out'); ap.add_argument('--units',required=True); ap.add_argument('--mag',type=int,default=6)
A=ap.parse_args(); want=[int(x) for x in A.units.split(',')]
STRIPS=[('F1 top',16,32),('F1 bottom',252,268),('F2 top',279,295),('F2 bottom',515,528)]
census=open(A.out+'.census.csv','w'); cw=csv.writer(census)
cw.writerow(['unit','counter']+[f'L{l}_mean' for _,a,b in STRIPS for l in range(a,b+1)]+[f'L{l}_std' for _,a,b in STRIPS for l in range(a,b+1)])
st=dict(first=None,n=0); keep={}; buf=bytearray()
def emit(u):
    c=int.from_bytes(u[4:6],'little')
    if st['first'] is None: st['first']=c
    unit=(c-st['first'])&0xffff; st['n']+=1
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)
    means=[]; stds=[]
    for _,a,b in STRIPS:
        for l in range(a,b+1): r=Y[l-4]; means.append(round(float(r.mean()),1)); stds.append(round(float(r[40:680].std()),1))
    cw.writerow([unit,c]+means+stds)
    if unit in want: keep[unit]=Y
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
except RuntimeError as e: print('walk ended:',str(e)[:80])
census.close()
W=720; LBL=150; M=A.mag; rows_per_unit=sum(b-a+1 for _,a,b in STRIPS); gap=6
H=len(want)*(rows_per_unit*M+len(STRIPS)*gap+20)
im=Image.new('RGB',(LBL+W,H),(20,20,20)); dr=ImageDraw.Draw(im); y=0
for unit in want:
    Y=keep.get(unit)
    dr.text((4,y+2),f'unit {unit}',fill=(0,255,255)); y+=18
    if Y is None: dr.text((4,y),'NOT IN CAPTURE',fill=(255,0,0)); y+=20; continue
    for name,a,b in STRIPS:
        for l in range(a,b+1):
            r=Y[l-4]; strip=np.repeat(r[None,:],M,axis=0)
            g=np.clip(strip*2.0,0,255).astype(np.uint8)      # luma x2 so the dark edge rows are readable; numbers at left are the raw values
            im.paste(Image.fromarray(np.stack([g,g,g],axis=2)),(LBL,y))
            dr.text((4,y),f'{name[:2]} L{l} {r.mean():5.1f} s{r[40:680].std():4.1f}',fill=(255,255,0) if l in (23,286) else (200,200,200))
            y+=M
        y+=gap
im.save(A.out); print('units',st['n'],'first counter',st['first'],'panel',A.out,'census',A.out+'.census.csv')
