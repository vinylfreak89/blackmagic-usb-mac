#!/usr/bin/env python3
"""Absolute placement audit from the tape's own black line 22 (field 1) / 285 (field 2), on the raw raster.

Row 18 (field 1) and row 281 (field 2) are black in every unit (regenerated, like the Shuttle's inserts). A source
whose line 22 / 285 is black shows that line as a dark row (row mean <= 10, above the 1.4 blanking) at row 18 + d /
281 + d, below the caption when one is present, immediately above the picture. So d = (last dark row before the
first two picture rows) - 18 (field 1) or - 281 (field 2), searched in rows 18..29 / 281..292, bounded 0..3.
This sees the common-mode error the comb audit cannot (both fields one line high together: a black line at the
top of the frame) and the tied-body units the parity truth cannot (no caption). It is INVALID where the source
carries video on line 22 (the second recording of fixture A reads 0 there against a caption truth of +2/+3), so the
per-segment validity is reported by agreement with the sidecar's caption placements: a recording is 'gap-valid'
only if gap and caption agree on >= 95% of the units carrying both. Output per unit: gap d per field, applied d,
verdict (agree / OFF+n / no-gap / picture-at-18). Usage: gap_gauge_audit.py <capture> <sidecar.csv> <out.csv> [start_ordinal]
"""
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
def gap_d(Y, base):
    m=[Y[r].mean() for r in range(base,base+12)]
    pic=next((k for k in range(1,11) if m[k]>12 and m[k+1]>12), None)
    if pic is None: return 'no-picture'
    dark=[k for k in range(0,pic) if m[k]<=10]
    if not dark: return 'picture-at-base'
    d=dark[-1]
    return d if d<=3 else 'deep-%d'%d
w=csv.writer(open(OUT,'w',newline='')); w.writerow(['ordinal','counter','t','f1_gap_d','applied_d1','f1_verdict','f1_caption_d','f2_gap_d','applied_d2','f2_verdict'])
stats=collections.Counter(); cap_agree=collections.Counter(); buf=bytearray(); audited=[0]
def emit(u):
    c=int.from_bytes(u[4:6],'little'); i,r=side_get(c)
    if r is None: return
    audited[0]+=1
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,81:1361:2].astype(np.float32)
    rec=[r['ordinal'],r['counter_extended'],round(int(r['ordinal'])*1001/30000,2)]
    for f,(base,key,capkey,ins) in enumerate(((18,'applied_d1','f1_gauge_line',21),(281,'applied_d2','f2_gauge_line',284))):
        g=gap_d(Y,base); a=int(r[key])
        cap=r.get(capkey,'-1'); capd=None
        if r.get('f%d_gauge'%(f+1))=='CEA608Parity' and cap not in ('','-1'): capd=int(cap)-ins
        if isinstance(g,int):
            v='agree' if g==a else 'OFF%+d'%(a-g)
            if capd is not None: cap_agree[(f+1,'gap==caption' if g==capd else 'gap!=caption')]+=1
        else: v=g
        stats[(f+1,v)]+=1
        rec+=[g,a,v]+([capd if f==0 else ''] if f==0 else [])
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
walk_error=None
try: walk_tagged(CAP, on_video=on_video, progress=False)
except RuntimeError as e: walk_error=str(e)[:120]; print("walk ended:", walk_error)
for f in (1,2): print('field %d:'%f, dict((k[1],v) for k,v in sorted(stats.items()) if k[0]==f))
print('gap vs caption (validity):', dict(cap_agree))
print('audited %d of %d exact sidecar rows'%(audited[0],len(rows_s)))
if audited[0]!=len(rows_s): print('FAIL: audited units != exact sidecar rows (walk error: %s)'%walk_error); sys.exit(2)
