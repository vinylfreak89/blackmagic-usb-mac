#!/usr/bin/env python3
# Independent whole-tape audit of a v9 sidecar against the raw 525-line raster, no render involved.
# Per unit and per field it measures, from the raw unit alone:
#   * the VBI-type lines above the picture by SIGNATURE (caption-like: run-in energy or a bright dashed pulse row with a
#     dark right end; timing-like; bar-like) regardless of whether they decode;
#   * the picture's first line: the first of three consecutive rows below the VBI-type lines whose mean exceeds the
#     field's own blanking by 4 (dark pictures count; the tape's flat grey line 22 does not start a picture on its own
#     unless three rows follow);
#   * a raster-damage score: fraction of rows in the top band (first 50 picture rows) that are dropout streaks
#     (a row deviating from both vertical neighbours by > 40 over > 25% of its width).
# and compares the engine's crop start (23 + applied_d1 / 286 + applied_d2) with the measured picture top.
# Output CSV per unit; summary: mismatches (crop != measured top) by field, jumps (applied changed while the measured
# top did not, or vice versa), by 5-minute bin; runs of mismatches; damaged units.
# Usage: engine_audit.py <capture.cap6> <sidecar.csv> <out.csv>  (sidecar = frameserver schema-7 log or renderer log)
import sys, csv, collections, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CELL=1.986e-6*13.5e6; _n=np.arange(10,230); _cos=np.cos(2*np.pi/CELL*_n); _sin=np.sin(2*np.pi/CELL*_n)
CAP,SIDE,OUT=sys.argv[1],sys.argv[2],sys.argv[3]
START_ORD=int(sys.argv[4]) if len(sys.argv)>4 else 0     # approximate sidecar ordinal of the capture's first unit (slices)
rows_s=[]
for r in csv.DictReader(open(SIDE)):
    key=r.get('counter_extended') or r.get('extended_counter')
    if key and (r.get('transport')=='Complete' or r.get('unit_state')=='Exact'):
        rows_s.append((int(key),r))
by16=collections.defaultdict(list)
for i,(k,_) in enumerate(rows_s): by16[k&0xffff].append(i)
print("sidecar exact rows", len(rows_s))
_last=[None]
def side_get(c16):
    cands=by16.get(c16)
    if not cands: return None
    ref=_last[0] if _last[0] is not None else START_ORD
    i=min(cands,key=lambda x:abs(x-ref))
    if _last[0] is not None and abs(i-_last[0])>8: return None   # a wrap-alias, not the next unit
    _last[0]=i; return rows_s[i][1]
def bins(row,nb=24): return np.array([row[k*640//nb:(k+1)*640//nb].mean() for k in range(nb)])
def vbi_type(row, full):
    b=bins(row); m=row.mean()
    if m>95: return None
    a=full[10:230]-full[10:230].mean(); amp=float(np.hypot(a@_cos,a@_sin)*2/220)
    if amp>=35 and b[18:].max()<45: return 'caption'
    if b[0]>80 and b[18:21].max()>100 and b[2:17].max()<40: return 'timing'
    hi=(b>60); 
    if b[18:].max()<45 and hi[:14].sum()>=3 and (b[:14].max()-b[:14].min())>60: return 'dashed'   # bright pulses, dark gaps, dark right end
    if b[20:].max()<=40 and (b[:20]>60).sum()>=6 and b.min()<25: return 'bar'
    return None
def picture_top(Y, Yfull, lo, hi, blank):
    types={}
    r=lo
    while r<hi:
        t=vbi_type(Y[r],Yfull[r])
        if t: types[r]=t; r+=1
        else: break
    # first of three consecutive picture rows at or below r
    for s in range(r,hi-2):
        if all(Y[s+k].mean()>blank+4 and not vbi_type(Y[s+k],Yfull[s+k]) for k in range(3)): return s, types
    return None, types
def damage(Yb):
    # rows deviating from both neighbours by >40 over >25% of the width
    up=np.abs(Yb[1:-1]-Yb[:-2]); dn=np.abs(Yb[1:-1]-Yb[2:]); streak=((up>40)&(dn>40)).mean(axis=1)>0.25
    return float(streak.mean())
w=csv.writer(open(OUT,'w',newline='')); w.writerow(['unit','counter','f1_top','f1_vbi','f1_crop','f1_ok','f1_damage','f2_top','f2_vbi','f2_crop','f2_ok','f2_damage','applied_d1','applied_d2','f1_reason','f2_reason'])
st={'n':0,'ext':None,'prev':None}; buf=bytearray()
def emit(u):
    n=st['n']; st['n']+=1
    c=int.from_bytes(u[4:6],'little')
    r=side_get(c)
    if r is None: return
    st['ext']=int(r.get('counter_extended') or r.get('extended_counter'))
    Yfull=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32); Y=Yfull[:,40:680]
    rec=[n,st['ext']]
    for f,(lo,hi,origin,bl,bh,key) in enumerate(((16,60,19,7,16,'applied_d1'),(279,323,282,270,279,'applied_d2'))):
        blank=float(Y[bl:bh+1].mean())
        top,types=picture_top(Y,Yfull,lo,hi,blank)
        crop=origin+int(r[key])
        ok='' if top is None else int(top==crop)
        dmg=damage(Y[(top if top else origin):(top if top else origin)+50]) if top is not None else ''
        rec+=[('' if top is None else top+4), ' '.join(f"{k+4}{v[0]}" for k,v in sorted(types.items())), crop+4, ok, ('' if dmg=='' else round(dmg,3))]
    rec+=[r['applied_d1'],r['applied_d2'],r.get('f1_reason',''),r.get('f2_reason','')]
    w.writerow(rec)
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
except RuntimeError as e: print("walk ended:", e)
print("units audited", st['n'])
