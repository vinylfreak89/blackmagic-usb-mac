import sys, csv, collections
import numpy as np
sys.path.insert(0,'/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments')
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BLANK={1:list(range(7,16)),2:list(range(270,279))}; BASE={1:19,2:282}
eng={}
for r in csv.DictReader(open('/private/tmp/run-timing.DdLgYt/plain/geometry.csv')):
    eng[(int(r['counter']),int(r['field']))]=(int(r['T']),int(r['S']),int(r['clip']))
def runs_at(row,blank):
    m=row<=blank+1.0; out=[];cur=0;s0=0
    for i,v in enumerate(m):
        if v:
            if cur==0: s0=i
            cur+=1
        elif cur: out.append((s0,cur));cur=0
    if cur: out.append((s0,cur))
    return out
def at_ref(row,blank,ref):
    (slo,shi),(nlo,nhi)=ref
    return any(slo<=s<=shi and nlo<=n<=nhi for s,n in runs_at(row,blank))
st={"buf":bytearray()}
S_={'ct':0,'co':0,'n':0}; dn=collections.Counter(); up=collections.Counter()
def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2]
    for fld in (1,2):
        T,Sv,clip=eng.get((c,fld),(-1,-1,-1))
        if T<0 or Sv<0 or clip<0: continue
        blank=float(np.median(Y[BLANK[fld]]))
        starts,lens=[],[]
        for off in range(177,228):
            rr=runs_at(Y[BASE[fld]+off].astype(np.float64),blank)
            if rr: starts.append(rr[-1][0]); lens.append(rr[-1][1])
        if len(starts)<20: continue
        ref=((int(np.percentile(starts,5)),int(np.percentile(starts,95))),
             (int(np.percentile(lens,5)),int(np.percentile(lens,95))))
        if ref[1][0]<=1: continue
        S_['n']+=1
        for off in range(77,177):
            S_['ct']+=1
            if not at_ref(Y[BASE[fld]+off].astype(np.float64),blank,ref): S_['co']+=1
        first=None
        for off in range(0,(clip-4)-BASE[fld]+1):
            if not at_ref(Y[BASE[fld]+off].astype(np.float64),blank,ref):
                first=BASE[fld]+off+4; break
        dn[(first-T) if first is not None else None]+=1
        R=None
        for r0 in range(clip-4,BASE[fld]-1,-1):
            if at_ref(Y[r0].astype(np.float64),blank,ref): break
            R=r0+4
        up[(R-T) if R is not None else None]+=1
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
walk_tagged('captures/composite_program_30s.tpc',on_video=on_video,progress=False)
print("askable field-readings with engine T, S and clip: %d" % S_['n'])
print("\nCONTROL -- 'off reference' on ORDINARY picture rows, field-relative lines 100-200:")
print("  %d of %d rows fire = %.1f%% false-positive rate per row" % (S_['co'],S_['ct'],100*S_['co']/S_['ct']))
def show(lbl,c):
    tot=sum(c.values()); print("\n%s  (offset from the engine's T; 0 = agree)" % lbl)
    for k in sorted(c,key=lambda x:(x is None,x))[:12]:
        print("   %-8s %5d  %5.1f%%" % ("none" if k is None else "%+d"%k, c[k], 100*c[k]/tot))
show("DOWNWARD scan: first off-reference row from the picture top",dn)
show("UPWARD run: topmost row with every row below it off-reference",up)
