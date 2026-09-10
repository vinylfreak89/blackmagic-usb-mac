#!/usr/bin/env python3
"""The contract's switch line, measured as the contract defines it -- in RAW CODES.

Track 1's gate, in the owner's words (2026-09-09): "we want agreement on the harness about the
headswitch. if we get it stable then we can finally lock the harness down. and then it just becomes
getting codex to build the engine right for capture 1."

**The object, contract :652**: "Switch line (the top switch line): the horizontal line carrying the
peak, the partial line", and :656 "S is NEVER substituted for it" -- where the partial row is not
measurable but S is, S is a BOUND and the switch line is Unknown. **That object is T.** The harness
has been calling S the switch line throughout, so both engine readers were arguing a partial-line
predicate while the harness validated a different row. This measures the object the contract names.

**Raw codes, not MAD, not sigma** (owner, 2026-09-11: "remove all this MAD and sigma bullshit"): the
peak is the largest POSITIVE excursion above the row's own median. Positive only, because a
relocated blanking interval is a large NEGATIVE excursion -- the defect already recorded in this
project twice, where an abs-then-sign statistic locked onto blanking and called it a peak.

⚠️ The contract's phrase PRESUPPOSES A PEAK EXISTS, and :655 supplies the fallback for when it does
not. So this reports agreement as a function of amplitude rather than choosing a cut-off; the
qualification is the finding, not a threshold to tune.

⚠️ It does NOT adjudicate the six T disagreements, and "within one row" spans exactly the T-versus-S
ambiguity that IS the dispute, so exact agreement is the number that bears on it.

  peak_line.py
"""
import sys, csv, collections
import numpy as np
sys.path.insert(0,'/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments')
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BASE={1:19,2:282}
eng={}
for r in csv.DictReader(open('/private/tmp/run-timing.DdLgYt/plain/geometry.csv')):
    eng[(int(r['counter']),int(r['field']))]=(int(r['T']),int(r['S']))
st={"buf":bytearray()}
agree=collections.Counter(); n=0; nopeak=0; amps=[]; pairs=[]
def emit(u):
    global n,nopeak
    c=int.from_bytes(u[4:6],"little")
    if c<6667: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for fld in (1,2):
        T,S=eng.get((c,fld),(-1,-1))
        if T<0: continue
        n+=1
        # contract :652 -- the line carrying the peak. RAW CODES above the row's own median,
        # positive only (a relocated blanking interval is a NEGATIVE excursion, not a peak).
        best=(0.0,-1)
        for off in range(232,240):
            row=Y[BASE[fld]+off]
            amp=float(row.max()-np.median(row))
            if amp>best[0]: best=(amp,BASE[fld]+off+4)
        amp,line=best
        amps.append(amp)
        agree[line-T]+=1
        pairs.append((amp,line-T))
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
walk_tagged('/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc',on_video=on_video,progress=False)
print("Contract :652's object: the line carrying the peak. RAW CODES above each row's own median,")
print("positive only. Compared against the engine's T on every reading where the engine has one.\n")
print("readings with an engine T: %d"%n)
tot=sum(agree.values())
print("\npeak-carrying line minus engine T:")
for k in sorted(agree)[:9]:
    print("   %-5s %5d  %5.1f%%"%("%+d"%k,agree[k],100*agree[k]/tot))
a=np.array(amps)
print("\npeak amplitude in raw codes: median %.0f  p10 %.0f  p90 %.0f"%(np.median(a),np.percentile(a,10),np.percentile(a,90)))
print("\nAGREEMENT AS A FUNCTION OF PEAK AMPLITUDE -- deciles, no threshold chosen:")
pairs.sort()
k=len(pairs)//10
print("  %-22s %6s %8s %8s"%("amplitude band (codes)","n","exact","within 1"))
for i in range(10):
    seg=pairs[i*k:(i+1)*k] if i<9 else pairs[9*k:]
    if not seg: continue
    ex=sum(1 for _,d in seg if d==0); w1=sum(1 for _,d in seg if abs(d)<=1)
    print("  %-22s %6d %7.0f%% %7.0f%%"%("%.0f - %.0f"%(seg[0][0],seg[-1][0]),len(seg),100*ex/len(seg),100*w1/len(seg)))
