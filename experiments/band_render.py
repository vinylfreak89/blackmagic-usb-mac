#!/usr/bin/env python3
"""The head-switch band in RAW LUMA, with T's and S's excursions. No MAD, no sigma, no ratios.

Owner, 2026-09-11: "get the measurement of the head switch band right. and be able to produce a
render that shows me the whole band, plus the excursions of S (S is the peak if I remember right)
and remove all this MAD and sigma bullshit". He asked twice and was handed a ratio plot both times.

⚠️ ONE NAME, TWO QUANTITIES -- and his parenthetical is where it bites, so this render labels both.
The contract (line 652) defines **Switch line (the top switch line): the horizontal line carrying
the peak, the partial line** -- that object is **T** -- and says "S is NEVER substituted for it".
The harness has been calling **S** the switch line throughout. So "S is the peak if I remember
right" is reaching for the contract's T. Both are drawn here, separately, against the raw rows.

Two panels:
  TOP     the band itself. One horizontal strip per unit, time running DOWN, so T's and S's
          excursions read as a moving edge rather than as a statistic. Raw luma on a stated linear
          window (the band sits at 17-22 against blanking at 1.4, so a 0-255 map would be black).
  BOTTOM  T and S per unit over a longer run, as the line numbers themselves. Not a ratio, not a
          score: the measured line.

  band_render.py [capture.tpc] [--field 1|2] [--from N] [--units N] [--out PNG]
"""
from __future__ import annotations
import argparse, sys, os, csv
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
LO_LINE={1:252,2:515}; HI_LINE={1:266,2:527}      # frame-continuous; the band plus context
RH=3; GUT=104; MAPS=((255.0,"picture: luma 0-255"),(48.0,"band: luma 0-48"))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("capture",nargs="?",default="captures/composite_program_30s.tpc")
    ap.add_argument("--field",type=int,default=1)
    ap.add_argument("--from",dest="frm",type=int,default=6900)
    ap.add_argument("--units",type=int,default=48)
    ap.add_argument("--trend",type=int,default=240,help="units in the lower T/S panel")
    ap.add_argument("--geometry",default="/private/tmp/run-timing.DdLgYt/plain/geometry.csv")
    ap.add_argument("--out",default="/private/tmp/band_render.png")
    a=ap.parse_args()
    eng={}
    for r in csv.DictReader(open(a.geometry)):
        eng[(int(r['counter']),int(r['field']))]=(int(r['T']),int(r['S']))
    st={"buf":bytearray()}; band={}; trend=[]
    lo,hi=LO_LINE[a.field],HI_LINE[a.field]

    def emit(u):
        c=int.from_bytes(u[4:6],"little")
        if c<a.frm or c>=a.frm+a.trend: return
        Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2]
        T,S=eng.get((c,a.field),(-1,-1))
        trend.append((c,T,S))
        if c<a.frm+a.units:
            band[c]=(Y[lo-4:hi-4+1].copy(),T,S)
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
    if not band: print("no units in range"); return 1

    nrow=hi-lo+1
    strip_h=nrow*RH
    top_h=len(band)*(strip_h+2)+52
    tr_h=190
    PW=720
    img=Image.new("RGB",(GUT+PW*2+24+150,top_h+tr_h+30),(18,18,22))
    d=ImageDraw.Draw(img)
    d.text((8,6),"HEAD-SWITCH BAND, RAW LUMA  --  capture %s, field %d, NTSC lines %d-%d.  LEFT %s   RIGHT %s"
           %(os.path.basename(a.capture),a.field,lo,hi,MAPS[0][1],MAPS[1][1]),(240,240,245))
    d.text((8,20),"time runs DOWN: one strip per unit, so T and S excursions read as a moving edge.",(170,170,178))
    d.text((8,34),"YELLOW = T, the contract's switch line (the peak / partial row).   CYAN = S.",(200,200,210))
    y=52
    for c in sorted(band):
        rows,T,S=band[c]
        for mi,(hi_v,_lbl) in enumerate(MAPS):
            g=np.clip(rows.astype(np.float64)/hi_v,0,1)
            img.paste(Image.fromarray(np.repeat((g*255).astype(np.uint8),RH,axis=0),"L").convert("RGB"),
                      (GUT+mi*(PW+24),y))
        d.text((6,y+strip_h//2-6),"%d"%c,(150,150,158))
        for val,col,lab in ((T,(255,215,90),"T"),(S,(110,215,255),"S")):
            if lo<=val<=hi:
                yy=y+(val-lo)*RH
                d.rectangle([GUT-14,yy,GUT-4,yy+RH-1],fill=col)
                d.rectangle([GUT+PW+4,yy,GUT+PW+18,yy+RH-1],fill=col)
                d.rectangle([GUT+PW*2+26,yy,GUT+PW*2+34,yy+RH-1],fill=col)
        d.text((GUT+PW*2+40,y+strip_h//2-6),"T=%s S=%s"%(T if T>0 else "-",S if S>0 else "-"),(190,190,198))
        y+=strip_h+2
    # trend panel: the measured line numbers themselves
    ty=top_h+14
    d.text((8,ty-12),"T and S per unit over %d units -- the measured LINE NUMBERS, not a score. Gaps = Unknown."%len(trend),(240,240,245))
    vals=[v for _,T,S in trend for v in (T,S) if v>0]
    if vals:
        vlo,vhi=min(vals)-1,max(vals)+1
        span=max(vhi-vlo,1); W=GUT+PW*2+24+140-40
        for k,(c,T,S) in enumerate(trend):
            x=40+int(W*k/max(len(trend)-1,1))
            for val,col in ((T,(255,215,90)),(S,(110,215,255))):
                if val>0:
                    yy=ty+int((tr_h-40)*(1-(val-vlo)/span))
                    d.rectangle([x,yy,x+1,yy+1],fill=col)
        for ln in range(vlo,vhi+1):
            yy=ty+int((tr_h-40)*(1-(ln-vlo)/span))
            d.text((6,yy-5),"%d"%ln,(150,150,158))
            d.line([(38,yy),(40+W,yy)],fill=(44,44,52))
        d.text((40,ty+tr_h-24),"counter %d"%trend[0][0],(150,150,158))
        d.text((40+W-90,ty+tr_h-24),"counter %d"%trend[-1][0],(150,150,158))
    img.save(a.out)
    print("wrote %s (%dx%d), %d band strips, %d units in the trend panel"%((a.out,)+img.size+(len(band),len(trend))))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
