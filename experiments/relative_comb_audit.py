#!/usr/bin/env python3
"""Relative inter-field registration of the PUBLISHED crops, measured on the raw raster.

For every exact unit, take field 1's crop (rows 19+d1 .. +240) and field 2's crop (282+d2 .. +240) from the
sidecar, weave them, and measure comb energy on STATIC pixels only (same-parity temporal mask: |Y - Y_prev| < 6 in
both fields, previous unit) after an 8-px horizontal low-pass, for field-2 re-weave shifts -3..+3.  A registered
pair has its minimum at shift 0; a unit whose minimum is elsewhere is presented with the fields misregistered by
that many lines (this is what yadif/bwdif would comb on).  Units with fewer than 3% static pixels or a comb-energy
drop below 25% between best and shift 0 are 'flat' (no evidence either way).
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
st={'prev':None,'previ':None}; buf=bytearray(); stats=collections.Counter(); hist=collections.Counter()
def emit(u):
    c=int.from_bytes(u[4:6],'little'); i,r=side_get(c)
    if r is None: st['prev']=None; return
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,81:1361:2].astype(np.float32)
    d1,d2=int(r['applied_d1']),int(r['applied_d2']); a1=F1+d1; a2=F2+d2
    shifts=[s for s in range(-3,4) if 0<=a2+s and a2+s+H<=LINES]
    ok = 0<=a1 and a1+H<=LINES and 0 in shifts
    if st['prev'] is not None and st['previ']==i-1 and ok:
        P=st['prev']; f1=lp(Y[a1:a1+H]); p1=lp(P[a1:a1+H])
        static1=np.abs(f1-p1)<6
        res=[]
        for s in shifts:
            f2=lp(Y[a2+s:a2+s+H]); p2=lp(P[a2+s:a2+s+H]); m=static1[:-1]&(np.abs(f2-p2)<6)[:-1]&static1[1:]
            # comb: field-2 line between two field-1 lines; energy = |f2 - (f1_above+f1_below)/2| on static pixels
            comb=np.abs(f2[:-1]-(f1[:-1]+f1[1:])/2)[m]
            res.append((s,float(comb.mean()) if comb.size else np.nan, m.mean()))
        e0=[x for x in res if x[0]==0][0]; best=min((x for x in res if not np.isnan(x[1])),key=lambda x:x[1],default=None)
        sf=e0[2]
        if best is None or sf<0.03: v='flat'
        elif best[0]==0: v='registered'
        elif e0[1]>0 and (e0[1]-best[1])/e0[1]<0.25: v='flat'
        else: v='MISREGISTERED'
        stats[v]+=1
        if v=='MISREGISTERED': hist[best[0]]+=1
        if v!='registered' or int(r['ordinal'])%50==0:
            w.writerow([r['ordinal'],r['counter_extended'],round(int(r['ordinal'])*1001/30000,2),best[0] if best else '',round(e0[1],2),round(best[1],2) if best else '',round(sf,3),v])
    st['prev']=Y; st['previ']=i
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
try: walk_tagged(CAP, on_video=on_video, progress=False)
except RuntimeError as e: print("walk ended:", str(e)[:80])
print('units:',dict(stats),'| misregistered by shift:',sorted(hist.items()))
