#!/usr/bin/env python3
# Whole-tape follow audit on the RAW raster, no render: at every unit where the engine changed a field's applied
# offset, did the field's picture BODY (rows well inside the picture, same field, previous unit) move by the same
# amount? Body shift is the integer vertical shift (-3..+3) minimising the mean absolute difference of the field's
# rows 40..200 (field 2: 303..463) against the previous unit; a scene cut (MAD floor > 25) is reported as unmeasurable.
#   both fields' bodies shift by the same nonzero amount with no applied change -> content-motion (a camera tilt), ignored
#   applied change == body shift  -> correct follow (output still)
#   applied change != body shift  -> engine-caused output motion (the crop moved on a still picture, or by the wrong amount)
# Also reports units where the body moved but the applied did not (missed moves).
# Usage: follow_audit.py <capture.cap6|slice.tpc> <frameserver sidecar.csv> <out.csv> [start_ordinal]
import sys, csv, collections, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CAP,SIDE,OUT=sys.argv[1],sys.argv[2],sys.argv[3]; START=int(sys.argv[4]) if len(sys.argv)>4 else 0
rows_s=[(int(r['counter_extended']),r) for r in csv.DictReader(open(SIDE)) if r.get('transport')=='Complete' and r.get('kind')=='0']
by16=collections.defaultdict(list)
for i,(k,_) in enumerate(rows_s): by16[k&0xffff].append(i)
_last=[None]
def side_get(c16):
    c=by16.get(c16)
    if not c: return None,None
    ref=_last[0] if _last[0] is not None else START
    i=min(c,key=lambda x:abs(x-ref))
    if _last[0] is not None and abs(i-_last[0])>8: return None,None
    _last[0]=i; return i,rows_s[i][1]
def body_shift(a,b,lo,hi):
    best=None
    for s in range(-3,4):
        d=float(np.abs(a[lo:hi]-b[lo+s:hi+s]).mean())
        if best is None or d<best[1]: best=(s,d)
    return best
w=csv.writer(open(OUT,'w',newline='')); w.writerow(['ordinal','counter','t','f1_applied_change','f1_body_shift','f1_mad','f1_verdict','f2_applied_change','f2_body_shift','f2_mad','f2_verdict','f1_reason','f2_reason'])
st={'prevY':None,'previ':None,'prevord':None}; buf=bytearray(); stats=collections.Counter()
def emit(u):
    c=int.from_bytes(u[4:6],'little'); i,r=side_get(c)
    if r is None: st['prevY']=None; return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,81:1361:2].astype(np.float32)
    stats[('audited',0)]+=1
    if st['prevY'] is not None and st['previ']==i-1 and int(r['ordinal'])==st['prevord']+1:   # a short/unframed unit between two exact rows breaks the pair
        p=rows_s[i-1][1]; rec=[r['ordinal'],r['counter_extended'],round(int(r['ordinal'])*1001/30000,2)]
        for f,(lo,hi,key) in enumerate(((40,200,'applied_d1'),(303,463,'applied_d2'))):
            da=int(r[key])-int(p[key]); s,mad=body_shift(st['prevY'],Y,lo,hi)
            if mad>25: v='unmeasurable'
            elif da==0 and s==0: v='still'
            elif da==s: v='follow'
            elif da==0: v='MISS'
            else: v='ENGINE-MOTION'
            rec+=[da,s,round(mad,1),v]
        # Content motion (a camera tilt, a subject moving up the frame) moves BOTH fields' bodies together and is not
        # a raster event; it must not be scored as a miss or as engine motion. Measured 2026-09-05 at 40:26 (handheld
        # shot) where every unit read as a MISS in both fields.
        # Gated on both witnesses being measurable (MAD <= 25): a cut or damaged pair whose two unconstrained
        # minima happen to coincide is not content motion (Codex review 2026-09-05, finding 6).
        if rec[4]==rec[8] and rec[4]!=0 and rec[3]==0 and rec[7]==0 and rec[5]<=25 and rec[9]<=25:
            rec[6]='content-motion'; rec[10]='content-motion'
        for f in (0,1): stats[(f+1,rec[6 if f==0 else 10])]+=1
        rec+=[r.get('f1_reason',''),r.get('f2_reason','')]   # pre-v9 sidecars carry no per-field reason
        if any(x in ('follow','MISS','ENGINE-MOTION') for x in (rec[6],rec[10])): w.writerow(rec)
    st['prevY']=Y; st['previ']=i; st['prevord']=int(r['ordinal'])
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
walk_error=None
try: walk_tagged(CAP, on_video=on_video, progress=False)
except RuntimeError as e: walk_error=str(e)[:120]; print("walk ended:", walk_error)
audited=stats.pop(('audited',0),0)
for f in (1,2): print(f"field {f}: {dict((k[1],v) for k,v in stats.items() if k[0]==f)}")
print('audited %d of %d exact sidecar rows'%(audited,len(rows_s)))
if audited!=len(rows_s):
    print('FAIL: audited units != exact sidecar rows (walk error: %s)'%walk_error); sys.exit(2)
