#!/usr/bin/env python3
"""The deliverable review frame: 720x486 as placed, in colour, plus the raster. One frame per unit.

Contract "Final outputs" (owner, 2026-09-07 21:4x): "for final outputs, the 720x486 overlay plus the
raster that shows the picture shift... plus all the decision information". This builds that, and it
replaces a luma-only strip I built by mistake -- his correction, 2026-09-11: "idk what render it
thinks its doing but its not the 720x486 plus the other shit we agreed to. its some luma only
bullshit". "Remove all this MAD and sigma bullshit" meant strip the STATISTIC, not the colour.

**The box overlay, owner 2026-09-10 11:13:09, previously recorded NOWHERE** (`bounding box`,
`purple` and `alpha` each appear zero times in the contract and CLAUDE.md): "it should draw the
bounding box when it finds it on top of the picture. keeping its field colors, meaning if they
colide the box should be purple. and it should be like transparentish, so you can still see
underneath it." So: field 1's box red, field 2's blue, purple where they coincide, alpha-blended.

The box detector is `box_census.py`'s own, imported rather than reimplemented, so this render and
that census cannot drift apart.

⚠️ Colour is a standard BT.601 limited-range decode. This material's black sits near code 1.4 rather
than 16 (CLAUDE.md section 6), so the decode is the STANDARD one applied to a non-standard black, not
a correction of it -- that is what "as placed" means and nothing here remaps levels.

⚠️ No ratio, no MAD, no sigma anywhere in the output.

  review_frame.py [capture.tpc] --counter N [--counter N ...] [--out DIR]
"""
from __future__ import annotations
import argparse, sys, os, csv
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
from box_census import h_profile, row_threshold, bands, verdict, FIELDS

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
# 486 mode, CLAUDE.md section 11 as corrected 2026-09-09: lines 20-262 in EACH field, 243 per field.
F1_486=(20,262); F2_486=(283,525)


def uyvy_to_rgb(raw):
    """raw: (rows, 1440) uint8 UYVY -> (rows, 720, 3) uint8, BT.601 limited range."""
    r=raw.astype(np.float64)
    Y=r[:,1::2]
    U=np.repeat(r[:,0::4],2,axis=1); V=np.repeat(r[:,2::4],2,axis=1)
    y=1.164*(Y-16.0); u=U-128.0; v=V-128.0
    rgb=np.stack([y+1.596*v, y-0.813*v-0.391*u, y+2.018*u],axis=-1)
    return np.clip(rgb,0,255).astype(np.uint8)


def blend(img, box, colour, a=0.35):
    """Alpha-blend a filled rectangle -- 'transparentish, so you can still see underneath it'."""
    x0,y0,x1,y1=box
    if y1<y0 or x1<x0: return
    reg=np.asarray(img.crop((x0,y0,x1+1,y1+1)),dtype=np.float64)
    reg=reg*(1-a)+np.array(colour,dtype=np.float64)*a
    img.paste(Image.fromarray(np.clip(reg,0,255).astype(np.uint8)),(x0,y0))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("capture",nargs="?",default="captures/composite_program_30s.tpc")
    ap.add_argument("--counter",type=int,action="append",required=True)
    ap.add_argument("--geometry",default="/private/tmp/run-timing.DdLgYt/plain/geometry.csv")
    ap.add_argument("--out",default="/private/tmp")
    a=ap.parse_args()
    eng={}
    if os.path.exists(a.geometry):
        for r in csv.DictReader(open(a.geometry)):
            eng[(int(r['counter']),int(r['field']))]=r
    want=set(a.counter); st={"buf":bytearray()}; got={}
    def emit(u):
        c=int.from_bytes(u[4:6],"little")
        if c in want: got[c]=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW).copy()
    def on_video(p):
        b=st["buf"]; b.extend(p)
        while True:
            i=b.find(MARK)
            if i<0: return
            if i>0: del b[:i]
            j=b.find(MARK,4)
            if j<0: return
            if j==UNIT: emit(bytes(b[:UNIT]))
            del b[:j]
    walk_tagged(a.capture,on_video=on_video,progress=False)

    for c in sorted(got):
        raw=got[c]; Y=raw[:,1::2]
        rgb=uyvy_to_rgb(raw)
        h=h_profile(Y)
        box={}
        for f,(lo,hi) in FIELDS.items():
            thr=row_threshold(h,lo,hi,4.5,0.28)
            b=bands(h,lo,hi,thr,6)
            box[f]=(b,verdict(b,6,40))
        # ---- 486 output as placed: weave field 1 lines 20-262 with field 2 lines 283-525
        f1=rgb[F1_486[0]-4:F1_486[1]-4+1]; f2=rgb[F2_486[0]-4:F2_486[1]-4+1]
        n=min(len(f1),len(f2)); out486=np.empty((n*2,720,3),dtype=np.uint8)
        out486[0::2]=f1[:n]; out486[1::2]=f2[:n]
        W=720; PAD=16; RH=2
        img=Image.new("RGB",(W*2+PAD*3,max(n*2,LINES*RH)+150),(16,16,20))
        d=ImageDraw.Draw(img)
        d.text((10,8),"REVIEW FRAME  counter %d  --  capture %s"%(c,os.path.basename(a.capture)),(240,240,246))
        d.text((10,22),"LEFT: 720x486 output AS PLACED (lines 20-262 / 283-525, woven), colour, BT.601 limited.",(180,180,190))
        d.text((10,34),"RIGHT: the full 525-line raster, vertically 2x. Box: field 1 RED, field 2 BLUE, PURPLE where",(180,180,190))
        d.text((10,46),"they coincide, alpha 0.35 so you see through it. No ratio, no MAD, no sigma anywhere.",(180,180,190))
        y0=64
        # ---- the box goes ON THE PICTURE (owner: "on top of the picture"), and PURPLE is where the
        # two fields' boxes cover the same PICTURE line. In raster coordinates they never can:
        # field 2 sits 263 rows below field 1, so a collision test there is vacuous. Woven, output
        # rows 2p and 2p+1 are field 1 line 20+p and field 2 line 283+p -- the corresponding pair.
        ov=out486.astype(np.float64)
        RED=np.array([255,70,70]); BLUE=np.array([70,120,255]); PURPLE=np.array([180,70,255]); AL=0.35
        def covers(f,line):
            b,vd=box[f]
            return vd=="box" and b["content_top"]+4 <= line <= b["content_bot"]+4
        n_pur=0
        for pp in range(n):
            in1=covers(1,F1_486[0]+pp); in2=covers(2,F2_486[0]+pp)
            if not (in1 or in2): continue
            if in1 and in2:
                ov[2*pp]=ov[2*pp]*(1-AL)+PURPLE*AL; ov[2*pp+1]=ov[2*pp+1]*(1-AL)+PURPLE*AL; n_pur+=1
            elif in1: ov[2*pp]=ov[2*pp]*(1-AL)+RED*AL
            else:     ov[2*pp+1]=ov[2*pp+1]*(1-AL)+BLUE*AL
        out486=np.clip(ov,0,255).astype(np.uint8)
        img.paste(Image.fromarray(out486),(PAD,y0))
        d.rectangle([PAD-1,y0-1,PAD+W,y0+n*2],outline=(90,90,100))
        # ---- full raster, 2x vertical
        rx=PAD*2+W
        img.paste(Image.fromarray(np.repeat(rgb,RH,axis=0)),(rx,y0))
        # box overlay on the raster, per field, in the raster's own rows
        for f,(b,vd) in box.items():
            if vd!="box" or b["content_top"]<0: continue
            col=(255,70,70) if f==1 else (70,120,255)
            r0=y0+(b["content_top"])*RH; r1=y0+(b["content_bot"])*RH+RH-1
            blend(img,(rx,r0,rx+W-1,r1),col)
            d.rectangle([rx,r0,rx+W-1,r1],outline=col)
        # (the raster keeps plain per-field outlines; collision has no meaning in its coordinates)
        # ---- the decision record, in words and line numbers only
        ty=y0+max(n*2,LINES*RH)+10
        d.text((10,ty),"DECISION RECORD    picture lines where BOTH fields' boxes coincide (purple): %d"%n_pur,(240,240,246))
        line=ty+16
        for f in (1,2):
            e=eng.get((c,f))
            b,vd=box[f]
            txt="field %d:  T=%s  S=%s  top=%s  clip=%s   box=%s"%(
                f, e['T'] if e else "?", e['S'] if e else "?", e['top'] if e else "?",
                e['clip'] if e else "?", vd)
            d.text((10,line),txt,(255,215,90) if f==1 else (110,215,255)); line+=14
            if vd=="box":
                d.text((28,line),"box content rows %d-%d (NTSC lines %d-%d)"%(
                    b["content_top"],b["content_bot"],b["content_top"]+4,b["content_bot"]+4),(200,200,208)); line+=14
        p=os.path.join(a.out,"review_%d.png"%c)
        img.save(p); print("wrote %s (%dx%d)"%((p,)+img.size))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
