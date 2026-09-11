"""How much of the void detector's behaviour was the PADDING RULER, and how much the statistic?

The detector's mask bound is `median(Y[0:6]) + 3.0` = 19, where the source's blanking never exceeds
code 3. Two causes are now on the table for its degenerate verdicts, and they imply different
repairs: the wrong LEVEL, or the summed-duration OBSERVABLE. This changes ONE variable -- the level
handed to the same unchanged classifier -- so the rebuild cannot later be credited with a fix the
level alone would have produced.

⚠️ Every figure here is from an instrument whose observable is known wrong (a pure translation reads
`normal`). These are NOT switch counts under any level; they are a before/after on one variable.
"""
import sys
import numpy as np
sys.path.insert(0, "experiments")
from packet_capture_reader import walk_tagged
from source_reference import ORIGIN_ROW, source_reference
from blanking_extent import local_expectation, classify, SWITCH_LINES, FIELD_ORIGIN

UNIT=756_048; HDR=48; ROW=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CAL=list(range(210,236,2)); VAL=list(range(211,236,2)); TOL=3.0
st={"buf":bytearray()}
tally={"device":{}, "source":{}}
fp={"device":[0,0], "source":[0,0]}
seen=[0]

def emit(u):
    c=int.from_bytes(u[4:6],"little")
    if c<6667 or seen[0]>=400: return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,ROW)[:,1::2].astype(np.float64)
    for f in (1,2):
        b=ORIGIN_ROW[f]; origin=FIELD_ORIGIN[f]
        ref=source_reference([Y[b+o] for o in range(20,220)])
        if ref is None: continue
        seen[0]+=1
        for name,lvl in (("device",float(np.median(Y[0:6]))),("source",ref["level"])):
            exp=local_expectation([Y[b+o] for o in CAL],lvl,TOL)
            if exp is None: continue
            for o in VAL:
                v,_,_=classify(Y[b+o],exp,lvl,TOL)
                fp[name][1]+=1
                if v in ("extended","overridden"): fp[name][0]+=1
            for ln in SWITCH_LINES[f]:
                rr=b+(ln-origin)
                if rr>=LINES: continue
                v,_,_=classify(Y[rr],exp,lvl,TOL)
                tally[name][v]=tally[name].get(v,0)+1

def on_video(p):
    bb=st["buf"]; bb.extend(p)
    while True:
        i=bb.find(MARK)
        if i<0: return
        if i>0: del bb[:i]
        j=bb.find(MARK,4)
        if j<0: return
        if j==UNIT: emit(bytes(bb[:UNIT]))
        del bb[:j]

walk_tagged("captures/composite_program_30s.tpc",on_video=on_video,progress=False)
print("ONE VARIABLE CHANGED: the level handed to the same unchanged classifier.")
print("%d field-readings from counter 6667\n"%seen[0])
print("  %-28s %9s %9s"%("verdict on the switch band","device","source"))
keys=sorted(set(tally["device"])|set(tally["source"]))
for k in keys:
    d=tally["device"].get(k,0); s=tally["source"].get(k,0)
    print("  %-28s %9d %9d"%(k,d,s))
for n in ("device","source"):
    a,b2=fp[n]
    print("  %-28s %9s"%("false-identification, %s"%n,"%d of %d = %.2f%%"%(a,b2,100*a/max(b2,1))))
print("\n  bound: device = %s, source = source level + 3.0"%"median(Y[0:6]) + 3.0 = 19.0")
