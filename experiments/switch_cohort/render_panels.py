#!/usr/bin/env python3
"""Render the frozen cohort's panels for blind adjudication.

One panel per unit. Each shows the three sampled rows of each field, at both edges of the delivered
window, as luma against sample index, with that field's OWN written-blanking level drawn as a
reference line and the rows immediately above and below drawn faintly for corroboration.

NOTHING IN A PANEL INDICATES A VERDICT. No run is highlighted, no boundary is marked, no
measurement is printed. The adjudicator answers the two questions in CRITERIA.md from the samples.

  render_panels.py            -> experiments/switch_cohort/panels/
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from PIL import Image, ImageDraw
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
HERE=os.path.dirname(os.path.abspath(__file__))
K=json.load(open(os.path.join(HERE,"COHORT_KEYS.json")))
NEED=sorted({k["counter"] for k in K["keys"]})
ROWS={}                                   # counter -> {(field,row)}
for k in K["keys"]: ROWS.setdefault(k["counter"],set()).add((k["field"],k["storage_row"]))
W=48                                       # samples shown at each edge
CW,CH,GAP = 300,110,12                     # cell size
BLANK_REF_ROWS=(8,16)                      # the device's written blanking above field 1's picture

YMAX=24.0   # the judgement lives at the low end; anything above this is plainly picture and is
            # clipped to the top of the cell. Fixed for every cell so they are comparable.

def cell(d,x,y,seg,neigh,z,title):
    d.rectangle([x,y,x+CW,y+CH],outline=(70,70,84))
    d.text((x+4,y+2),title,fill=(170,170,185))
    def px(i,v): return x+4+int(i*(CW-8)/(len(seg)-1)), y+CH-8-int(min(v,YMAX)/YMAX*(CH-24))
    for lev in (5,10,15,20):
        yy=px(0,lev)[1]; d.line([x+2,yy,x+CW-2,yy],fill=(44,44,54))
        d.text((x+CW-16,yy-5),str(lev),fill=(70,70,84))
    zy=px(0,z)[1]
    d.line([x+2,zy,x+CW-2,zy],fill=(90,150,230))
    for nb in neigh:
        d.line([px(i,v) for i,v in enumerate(nb)],fill=(96,96,112))
    d.line([px(i,v) for i,v in enumerate(seg)],fill=(235,235,245))
    # ⚠️ FIXED 2026-09-10, found by an adjudicator: this used range(0,len(seg)+1,8) with
    # px(min(i,len(seg)-1)), which drew a tick labelled 48 on sample 47 - the axis then read 0-48
    # across 48 samples and anyone interpolating near the right end was off by up to a sample.
    # The frozen panel set carries that error in its boundary VALUES and is NOT re-rendered, because
    # the cohort is keyed to those exact images; anything new uses this.
    for i in range(0,len(seg),8):
        xx=px(i,0)[0]
        d.line([xx,y+CH-8,xx,y+CH-3],fill=(80,80,95))
        d.text((xx-6,y+CH-3),str(i),fill=(70,70,84))
    xx=px(len(seg)-1,0)[0]                       # and label the LAST sample where it actually is
    d.line([xx,y+CH-8,xx,y+CH-3],fill=(80,80,95))
    d.text((xx-8,y+CH-3),str(len(seg)-1),fill=(70,70,84))

def render(ctr,Y,out):
    want=sorted(ROWS[ctr])
    nrow=len(want)
    Wpx=2*CW+3*GAP+130; Hpx=nrow*(CH+GAP)+56
    img=Image.new('RGB',(Wpx,Hpx),(16,16,18)); d=ImageDraw.Draw(img)
    d.text((10,8),f"capture composite_program_30s.tpc   counter {ctr}",fill=(255,220,120))
    d.text((10,22),"luma against sample index, vertical axis 0-24 codes and clipped there; blue = this field's "
                   "own written blanking; grey = the rows above and below",fill=(150,150,165))
    y=42
    for fld,row in want:
        z=float(np.median(Y[BLANK_REF_ROWS[0]+(0 if fld==1 else 263):BLANK_REF_ROWS[1]+(0 if fld==1 else 263)]))
        d.text((10,y+CH//2-14),f"field {fld}",fill=(215,215,225))
        d.text((10,y+CH//2-2),f"row {row}",fill=(150,150,165))
        d.text((10,y+CH//2+10),f"blank {z:.2f}",fill=(90,150,230))
        for j,(a,b,lbl) in enumerate(((0,W,"left edge, samples 0-47"),(720-W,720,"right edge, samples 672-719"))):
            seg=Y[row][a:b].astype(np.float64)
            neigh=[Y[row-1][a:b].astype(np.float64), Y[row+1][a:b].astype(np.float64)]
            cell(d,130+j*(CW+GAP),y,seg,neigh,z,lbl)
        y+=CH+GAP
    img.save(os.path.join(out,f"cohort_{ctr}.png"))

def main():
    out=os.path.join(HERE,"panels"); os.makedirs(out,exist_ok=True)
    buf=bytearray(); done=set()
    def emit(u):
        c=int.from_bytes(u[4:6],'little')
        if c in ROWS and c not in done:
            Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2]
            render(c,Y,out); done.add(c)
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
    try: walk_tagged('captures/composite_program_30s.tpc',on_video=on_video,progress=False)
    except RuntimeError: pass
    print(f"rendered {len(done)} of {len(NEED)} panels to {out}")
    missing=[c for c in NEED if c not in done]
    if missing: print("MISSING:",missing)

if __name__=="__main__": main()
