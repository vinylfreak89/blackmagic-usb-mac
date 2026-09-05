#!/usr/bin/env python3
"""Relative inter-field registration of the PUBLISHED crops, measured on the raw raster.

For every exact unit, take field 1's crop (rows 19+d1 .. +240) and field 2's crop (282+d2 .. +240) from the
sidecar, weave them, and measure comb energy on STATIC pixels only after an 8-px horizontal low-pass, for field-2
re-weave shifts -3..+3.  The static mask is ONE mask for all candidate shifts: pixels whose field-1 crop and
field-2 crop (at the applied crops) both changed by < 6 against the PREVIOUS unit's own published crops, so a crop
that followed a raster move still compares the same picture lines (Codex review 2026-09-05, finding 1).
A registered pair has its minimum at shift 0; a unit whose minimum is elsewhere is presented with the fields
misregistered by that many lines.  'registered' and 'MISREGISTERED' both require a unique minimum with an energy
drop of >= 25% against the second-best shift on >= 3% static pixels; otherwise the unit is 'flat' (finding 2).
This is a weave-continuity metric (|f2 - mean(f1 above, f1 below)|), a proxy for what a weaving deinterlacer
combs on, not a yadif output measurement (finding 3).  Units are compared only when the sidecar ordinals are
consecutive (a short/unframed unit between them breaks the pair) and the tool exits 2 unless every exact sidecar
row was audited (finding 4).
Output CSV per unit: ordinal, counter, best_shift, e0, ebest, static_fraction, verdict.  Summary on stdout.
Usage: relative_comb_audit.py <capture> <sidecar.csv> <out.csv> [start_ordinal]
"""
import sys, csv, collections, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"; F1=19; F2=282; H=240
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
def lp(a):  # 8-px horizontal box low-pass
    c=np.cumsum(np.pad(a,((0,0),(8,0))),axis=1); return (c[:,8:]-c[:,:-8])/8.0
w=csv.writer(open(OUT,'w',newline='')); w.writerow(['ordinal','counter','t','best_shift','e0','ebest','static_fraction','verdict'])
st={'prev':None,'previ':None,'prevord':None,'preva1':None,'preva2':None}; buf=bytearray(); stats=collections.Counter(); hist=collections.Counter()
def emit(u):
    c=int.from_bytes(u[4:6],'little'); i,r=side_get(c)
    if r is None: st['prev']=None; return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,81:1361:2].astype(np.float32)
    d1,d2=int(r['applied_d1']),int(r['applied_d2']); a1=F1+d1; a2=F2+d2
    shifts=[s for s in range(-3,4) if 0<=a2+s and a2+s+H<=LINES]
    ok = 0<=a1 and a1+H<=LINES and 0 in shifts
    consecutive = st['prev'] is not None and st['previ']==i-1 and int(r['ordinal'])==st['prevord']+1
    stats['audited']+=1
    if consecutive and ok:
        P,pa1,pa2=st['prev'],st['preva1'],st['preva2']
        f1=lp(Y[a1:a1+H]); p1=lp(P[pa1:pa1+H]); f2c=lp(Y[a2:a2+H]); p2=lp(P[pa2:pa2+H])
        static=(np.abs(f1-p1)<6)&(np.abs(f2c-p2)<6)           # one mask, previous unit at ITS published crops
        m=static[:-1]&static[1:]; sf=float(m.mean())
        res=[]
        for s in shifts:
            f2=lp(Y[a2+s:a2+s+H])
            # comb: field-2 line between two field-1 lines; energy = |f2 - (f1_above+f1_below)/2| on static pixels
            comb=np.abs(f2[:-1]-(f1[:-1]+f1[1:])/2)[m]
            res.append((s,float(comb.mean()) if comb.size else np.nan))
        e0=[x for x in res if x[0]==0][0]; valid=[x for x in res if not np.isnan(x[1])]
        best=min(valid,key=lambda x:x[1]) if valid else None
        second=min((x[1] for x in valid if x[0]!=best[0]),default=np.nan) if best else np.nan
        if best is None or sf<0.03 or np.isnan(second) or second<=0 or (second-best[1])/second<0.25: v='flat'
        elif best[0]==0: v='registered'
        else: v='MISREGISTERED'
        stats[v]+=1
        if v=='MISREGISTERED': hist[best[0]]+=1
        if v!='registered' or int(r['ordinal'])%50==0:
            w.writerow([r['ordinal'],r['counter_extended'],round(int(r['ordinal'])*1001/30000,2),best[0] if best else '',round(e0[1],2),round(best[1],2) if best else '',round(sf,3),v])
    elif st['prev'] is not None and not consecutive: stats['skipped:not-consecutive']+=1
    st['prev']=Y; st['previ']=i; st['prevord']=int(r['ordinal']); st['preva1']=a1; st['preva2']=a2
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
audited=stats.pop('audited',0)
print('units:',dict(stats),'| misregistered by shift:',sorted(hist.items()),'| audited %d of %d exact sidecar rows'%(audited,len(rows_s)))
if audited!=len(rows_s):
    print('FAIL: audited units != exact sidecar rows (walk error: %s)'%walk_error); sys.exit(2)
