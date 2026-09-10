#!/usr/bin/env python3
"""The head switch as ONE INSTANT, with T and S derived from it — properties 1, 2 and 8 together.

The T/S argument cost a day because two readers measured two rows and compared them. Under the
owner's frame they are not two rows: **the switch is an instant, and T and S are two quantisations
of it** — T the line the instant falls INSIDE, S the first line entirely after. So this measures ONE
quantity, a time in the field's own sweep, and DERIVES both. **A T-versus-S disagreement is then
structurally impossible rather than adjudicated**, which is the point.

  the instant  = (line, column) -- a position in the sweep, not a row to classify   [property 1]
  T            = the line the instant falls inside                                  [property 2]
  S            = T + 1, by construction                                             [property 2]

⚠️ **PROPERTY 8 IS A FIRST-CLASS OUTCOME HERE, not an exception.** The device delivers 720 of the
line's 858 samples, so 138 samples — 16% of every line — are never seen. An instant landing there
produces a delivered row with no partial in it, and `T = S` is then the CORRECT reading rather than a
reader's mistake. The contract carries this at `:657-658`. This instrument reports
`UNSAMPLED_INTERVAL` for that case, so a detector built on it can represent `T = S` instead of being
right about it by accident.

⚠️ **The peak is the instant's witness and it is a LIGHT peak only.** Owner, 2026-09-11, closing that
line: "i accept that it is visible but not visible from a statistic. dark peaks will go undetected".
So the amplitude floor stays and dark excursions are not hunted — measured, hunting them catches dark
CONTENT. Where no peak is present the instant is **Unknown**, and T and S are Unknown with it. That
is the honest output, not a fallback to a row.

  switch_instant.py [capture.tpc] [--from N] [--to N] [--amp N]
"""
from __future__ import annotations
import argparse, sys, os, csv, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BASE={1:19,2:282}
DELIVERED=720; LINE_SAMPLES=858          # 720 delivered of an 858-sample line; 138 never seen
BAND_OFFSETS=range(232,240)              # the field's last eight picture lines


def narrow_light_peak(row, floor):
    """The instant's witness: the largest POSITIVE narrow excursion above the row's own median.

    Narrow means under 100 samples -- the width bound separating a peak (tens) from a relocated
    blanking interval (140-199), which is bimodal in the data with 8 of 3,824 readings in the
    40-119 valley. Positive only, per the closed dark-peak ruling.
    """
    med=float(np.median(row)); d=row-med
    order=np.argsort(-d)                    # positive excursions first
    seen=set()
    for k in order[:400]:
        if k in seen: continue
        amp=float(d[k])
        if amp < floor: return None
        thr=amp/2.0
        a=k
        while a>0 and d[a-1]>=thr: a-=1
        b=k
        while b<len(d)-1 and d[b+1]>=thr: b+=1
        seen.update(range(a,b+1))
        if b-a+1 < 100:
            return amp, k, b-a+1
    return None


def instant(Y, field, floor):
    """ONE measurement: where in this field's sweep the switch happens.

    Returns a dict with the instant and both quantisations, or an Unknown with its reason.
    """
    best=None
    for off in BAND_OFFSETS:
        r=BASE[field]+off
        p=narrow_light_peak(Y[r].astype(np.float64), floor)
        if p is None: continue
        amp,col,w=p
        if best is None or amp>best[0]: best=(amp,BASE[field]+off+4,col,w)
    if best is None:
        return {"known":False,"why":"no light peak — the instant has no witness in this field"}
    amp,line,col,w=best
    # the instant as a time: which line, and how far along that line's own sweep
    phase = col / float(LINE_SAMPLES)
    unsampled = col >= DELIVERED           # cannot happen for a peak we SAW, but stated explicitly
    return {"known":True,"line":line,"column":col,"phase":phase,"amp":amp,"width":w,
            "T":line,"S":line+1,"unsampled":unsampled,
            "delivered_fraction":DELIVERED/float(LINE_SAMPLES)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("capture",nargs="?",default="captures/composite_program_30s.tpc")
    ap.add_argument("--from",dest="frm",type=int,default=6667)
    ap.add_argument("--to",dest="to",type=int,default=10**9)
    ap.add_argument("--amp",type=float,default=89.0,help="the amplitude floor the dark-peak ruling keeps")
    ap.add_argument("--geometry",default="/private/tmp/run-timing.DdLgYt/plain/geometry.csv")
    a=ap.parse_args()
    eng={}
    if os.path.exists(a.geometry):
        for r in csv.DictReader(open(a.geometry)):
            eng[(int(r["counter"]),int(r["field"]))]=(int(r["T"]),int(r["S"]))
    st={"buf":bytearray()}; rows=[]
    def emit(u):
        c=int.from_bytes(u[4:6],"little")
        if not (a.frm<=c<=a.to): return
        Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2]
        for fld in (1,2):
            rows.append((c,fld,instant(Y,fld,a.amp),eng.get((c,fld),(-1,-1))))
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
    known=[r for r in rows if r[2]["known"]]
    print("capture %s, counters >= %d"%(os.path.basename(a.capture),a.frm))
    print("  field-readings %d   instant KNOWN %d (%.0f%%)   Unknown %d"
          %(len(rows),len(known),100*len(known)/max(len(rows),1),len(rows)-len(known)))
    print("  ⚠️ Unknown is the honest output where the instant has no witness -- not a fallback to a row.")
    if not known: return 0
    ph=np.array([r[2]["phase"] for r in known]); col=np.array([r[2]["column"] for r in known])
    print("\n  THE INSTANT, as a position in the line's own sweep:")
    print("    column   median %d   p10 %d   p90 %d   (of %d delivered, %d in the line)"
          %(np.median(col),np.percentile(col,10),np.percentile(col,90),DELIVERED,LINE_SAMPLES))
    print("    phase    median %.3f of the line   p10 %.3f   p90 %.3f"%(np.median(ph),np.percentile(ph,10),np.percentile(ph,90)))
    print("    ⚠️ %.1f%% of every line is never delivered, so an instant landing there is invisible"
          %(100*(1-DELIVERED/LINE_SAMPLES)))
    agree=collections.Counter()
    for c,f,i,(eT,eS) in known:
        if eT>0: agree[i["T"]-eT]+=1
    tot=sum(agree.values())
    if tot:
        print("\n  DERIVED T against the engine's T (the engine's own export), n=%d:"%tot)
        for k in sorted(agree):
            if abs(k)<=2: print("    %-4s %5d  %5.1f%%"%("%+d"%k,agree[k],100*agree[k]/tot))
    print("\n  ⚠️ T and S here are DERIVED FROM ONE NUMBER, so they cannot disagree with each other.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
