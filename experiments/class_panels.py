#!/usr/bin/env python3
"""Raw-raster panels per decision class, so a reading is confirmed on the picture, never on a metric.

For a slice and a prototype/engine sidecar, group exact units by class (per-field reason, applied change, or a caller
filter), pick N units spread across each class, and render the RAW top rows and RAW bottom rows of both fields,
magnified 8x vertically with NTSC line numbers, the measured top/bottom/caption/head-switch split drawn on the image.
Output: <outdir>/<class>.png for every class plus <outdir>/index.md listing class, unit count, sampled ordinals.
Usage: class_panels.py <slice.tpc> <sidecar.csv> <outdir> [--per-class N] [--field 1|2|both] [--changes-only]
"""
import sys, os, csv, argparse, collections, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from PIL import Image, ImageDraw
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('side'); ap.add_argument('out')
ap.add_argument('--per-class',type=int,default=4); ap.add_argument('--field',default='both'); ap.add_argument('--changes-only',action='store_true')
A=ap.parse_args(); os.makedirs(A.out,exist_ok=True)
rows=[r for r in csv.DictReader(open(A.side)) if r.get('kind','0')=='0']
fields=[1,2] if A.field=='both' else [int(A.field)]
# classes: per field, reason; plus 'change d1 a->b' when applied changed against the previous row
classes=collections.defaultdict(list)
for i,r in enumerate(rows):
    for f in fields:
        reason=r.get(f'f{f}_reason','')
        if not A.changes_only: classes[f'f{f}_{reason}'].append(i)
        if i>0:
            a,b=rows[i-1][f'applied_d{f}'],r[f'applied_d{f}']
            if a!=b: classes[f'f{f}_change_{a}_to_{b}_{reason}'].append(i)
pick={}
for k,idx in classes.items():
    n=min(A.per_class,len(idx)); pick[k]=[idx[q*len(idx)//n] for q in range(n)]
want=set(i for v in pick.values() for i in v) | set(i-1 for v in pick.values() for i in v if i>0)
units={}; buf=bytearray(); n=[0]
def emit(u):
    if n[0] in want: units[n[0]]=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].copy()
    n[0]+=1
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
try: walk_tagged(A.cap, on_video=on_video, progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:80])
if n[0]!=len(rows): print(f'WARNING: {n[0]} exact units walked vs {len(rows)} sidecar rows; panels are joined by order and may be misaligned'); 
VS=8; W=720; LAB=52; TITLE=16
F={1:dict(insert=17,origin=19,last=261),2:dict(insert=280,origin=282,last=523)}
def val(r,k):
    v=r.get(k,''); 
    try: return int(v)
    except: return None
def band(img,d,y,Y,a,b,marks):
    big=np.repeat(Y[a:b],VS,axis=0); img.paste(Image.fromarray(big),(LAB,y))
    for k,row in enumerate(range(a,b)):
        col=255 if row in marks else 120; d.text((2,y+k*VS-1),f"{row+4}",fill=col); d.line([(LAB-3,y+k*VS),(LAB+W,y+k*VS)],fill=50)
        if row in marks:
            tag,colr=marks[row]; d.line([(LAB,y+k*VS),(LAB+W,y+k*VS)],fill=colr); d.text((LAB+W-120,y+k*VS-1),tag,fill=colr)
    return y+(b-a)*VS+6
index=['# class panels','',f'slice `{A.cap}` sidecar `{A.side}`','','| class | units | sampled ordinals |','|---|---:|---|']
for k in sorted(classes):
    idx=pick[k]; f=int(k[1]); Fd=F[f]
    tiles=[(i,rows[i]) for i in idx if i in units]
    if not tiles: continue
    Hband=lambda a,b:(b-a)*VS+6
    H=Hband(Fd['insert']-2,Fd['origin']+10)+Hband(Fd['last']-8,Fd['last']+3)
    img=Image.new('RGB',(LAB+W,len(tiles)*(H+TITLE)+4),(0,0,0)); d=ImageDraw.Draw(img); y=2
    for i,r in tiles:
        Y=units[i]; top=val(r,f'f{f}_top'); bot=val(r,f'f{f}_bottom'); cap=val(r,f'f{f}_cap'); hs=r.get(f'f{f}_hs_split','')
        prev=rows[i-1][f'applied_d{f}'] if i>0 else '-'
        d.text((4,y+2),f"ord {r['ordinal']} field {f}: applied {prev}->{r[f'applied_d{f}']} {r.get(f'f{f}_reason','')} [{r.get(f'f{f}_notes','')}] top {top+4 if top is not None else '-'} bottom {bot+4 if bot is not None else '-'} cap {cap+4 if cap is not None else '-'} hs {hs}",fill=(255,255,255)); y+=TITLE
        marks={}
        if top is not None: marks[top]=('TOP',(0,255,0))
        if cap is not None: marks[cap]=('CAP',(255,200,0))
        crop=Fd['origin']+int(r[f'applied_d{f}']); marks[crop]=('CROP' if crop!=top else 'TOP=CROP',(0,160,255) if crop!=top else (0,255,0))
        y=band(img,d,y,Y,Fd['insert']-2,Fd['origin']+10,marks)
        marks={}
        if bot is not None: marks[bot]=('BOTTOM',(0,255,0))
        if bot is not None and hs: marks[bot+1]=('HS '+hs,(255,0,255))
        y=band(img,d,y,Y,Fd['last']-8,Fd['last']+3,marks)
    fn=os.path.join(A.out,k+'.png'); img.save(fn)
    index.append(f"| `{k}` | {len(classes[k])} | {', '.join(rows[i]['ordinal'] for i in idx)} |")
open(os.path.join(A.out,'index.md'),'w').write('\n'.join(index)+'\n'); print('classes',len(classes),'->',A.out)
