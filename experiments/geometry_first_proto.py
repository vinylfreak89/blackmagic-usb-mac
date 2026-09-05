#!/usr/bin/env python3
"""Geometry-first registration engine — Python prototype of docs/geometry_first_engine.md.

Reads exact units from a capture (or slice), decides (d1, d2) per unit from the picture geometry alone, using the
tape's line 21 / black line 22 only as confirmations, and writes a sidecar with the same key columns the audits
read (ordinal, counter_extended, transport, kind, applied_d1, applied_d2, f1_reason, f2_reason, ...).
Constants are tagged in comments: RASTER (measured reference), STANDARD, DEFAULT (tape-fitted, to be replaced).
Usage: geometry_first_proto.py <capture> <out_sidecar.csv> [start_ordinal]
"""
import sys, csv, collections, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
from packet_capture_reader import walk_tagged
from cc608_decode import decode as cc608
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
BLANK=1.4                 # RASTER: Shuttle blanking level
DARK=BLANK+8.0            # DEFAULT: the tape's black line 22 measures 4-7; darkest picture row seen 10
PICTURE_ROWS=3            # DEFAULT: a top edge needs three consecutive picture rows
F1=dict(insert=17, blank22=18, origin=19, last=260, hs=(257,261))   # RASTER rows (line = row+4)
F2=dict(insert=280, blank22=281, origin=282, last=522, hs=(519,523))
CAP,OUT=sys.argv[1],sys.argv[2]; START=int(sys.argv[3]) if len(sys.argv)>3 else 0

def row_stats(Y): return Y.mean(axis=1), Y.std(axis=1)
def is_vbi_type(Yrow):
    """A row the tape's VBI could have put here: a parity-valid 608 line, or a run-in-only line."""
    ok,b1,b2,info = cc608(Yrow)
    if ok: return 'cc608'
    if isinstance(info,str) and info.startswith('start bits'): return 'runin'   # run-in found, no valid start bits: the tape's line 20 / a run-in-only line
    return None
def measure_field(Y, F, prev_field):
    m, s = row_stats(Y)
    rows = range(F['origin']-2, F['last'])          # from the tape-visible region (the row above the black 22) downward
    kind = {}
    for r in range(F['insert']+1, F['last']):
        if m[r] <= DARK: kind[r]='dark'
        else:
            v = is_vbi_type(Y[r]) if r < F['origin']+8 else None
            kind[r] = v or 'picture'
    # top edge: first r >= origin-? with PICTURE_ROWS consecutive picture rows
    top=None
    for r in range(F['insert']+1, F['last']-PICTURE_ROWS):
        if all(kind.get(r+k)=='picture' for k in range(PICTURE_ROWS)): top=r; break
    cap=[r for r in range(F['insert']+1, F['origin']+8) if kind.get(r)=='cc608']
    gap=None
    if top is not None:
        darks=[r for r in range(F['insert']+1, top) if kind.get(r)=='dark']
        gap=darks[-1] if darks else None
    # bottom edge: last picture row before the head-switch band / padding
    bottom=None
    for r in range(F['last']-1, (top or F['origin'])+10, -1):
        if kind.get(r)=='picture': bottom=r; break
    hs_lo,hs_hi=F['hs']; bottom_uncertain = bottom is not None and hs_lo<=bottom<hs_hi
    # body continuity witness against the previous unit's same field: upper and lower halves
    body=None
    if prev_field is not None:
        def vs(lo,hi):
            best=None
            for sft in range(-6,7):
                d=float(np.abs(prev_field[lo:hi]-Y[lo+sft:hi+sft]).mean())
                if best is None or d<best[1]: best=(sft,d)
            return best
        o=F['origin']; body=(vs(o+10,o+110), vs(o+130,o+230))
    return dict(top=top, cap=cap, gap=gap, bottom=bottom, bottom_uncertain=bottom_uncertain, body=body, height=(bottom-top+1) if (top is not None and bottom is not None) else None)

class FieldState:
    def __init__(s): s.d=0; s.lock=False; s.line22_video=None; s.prev=None
def decide(fs, F, mm, signal_ok=True):
    """Geometry decides; VBI confirms; hold only when the edge is hidden; splice/lock loss re-acquires."""
    reason='?'; notes=[]
    top=mm['top']
    # lock loss: a splice (one half continuous, the other a new picture) or the classifier's signal loss
    if mm['body'] is not None:
        (u_s,u_m),(l_s,l_m)=mm['body']
        if (u_m<8 and l_m>30) or (l_m<8 and u_m>30): fs.lock=False; notes.append('Splice')
    if not signal_ok: fs.lock=False; notes.append('SignalLoss')
    if top is None:
        return fs.d, ('EdgeHidden' if fs.lock else 'LockLost'), notes
    d_top = top - F['origin']
    # line-22 rule (STANDARD): a dark row directly above the top is the tape's black 22 -> top is already line 23 (no change);
    # a caption two rows above the top means the picture starts at line 23 (no change); a caption ONE row above the top
    # means the row under the caption is line 22 carrying video -> the recording has video on 22: crop one lower.
    d=d_top
    if mm['cap']:
        c=mm['cap'][-1]; d_cap=c-F['insert']
        if top==c+1:
            fs.line22_video=True; d=d_top+1; notes.append('Line22Video')
        elif top==c+2:
            fs.line22_video=False
        if d!=d_cap: notes.append('VbiDisagrees(cap %+d)'%d_cap)
    elif mm['gap'] is not None:
        d_gap=mm['gap']-F['blank22']
        if mm['gap']==top-1 and d_gap!=d_top: notes.append('VbiDisagrees(gap %+d)'%d_gap)
    elif fs.line22_video: d=d_top+1; notes.append('Line22VideoAssumed')
    if not fs.lock:
        fs.lock=True; reason='Acquired'; notes.append('jump %+d'%(d-fs.d))
    elif d!=fs.d: reason='GeometryMoved'
    else: reason='Geometry'
    fs.d=d
    return d, reason, notes

w=csv.writer(open(OUT,'w',newline=''))
cols=['ordinal','counter_extended','transport','kind','applied_d1','applied_d2','f1_reason','f1_notes','f1_top','f1_bottom','f1_height','f1_cap','f1_gap','f1_body_up','f1_body_lo','f2_reason','f2_notes','f2_top','f2_bottom','f2_height','f2_cap','f2_gap','f2_body_up','f2_body_lo','published']
w.writerow(cols)
st=dict(n=0,prev=None); S=[FieldState(),FieldState()]; buf=bytearray(); stats=collections.Counter()
def emit(u):
    c16=int.from_bytes(u[4:6],'little'); o=START+st['n']; st['n']+=1
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,81:1361:2].astype(np.float32)
    prev=st['prev']; rec=[o,c16,'Complete',0]
    out=[]
    for f,F in ((0,F1),(1,F2)):
        pf=None if prev is None else prev
        mm=measure_field(Y,F,pf)
        d,reason,notes=decide(S[f],F,mm)
        stats[(f+1,reason)]+=1
        b=mm['body']; out.append((d,reason,';'.join(notes),mm['top'],mm['bottom'],mm['height'],mm['cap'][-1] if mm['cap'] else '',mm['gap'] if mm['gap'] is not None else '', b[0][0] if b else '', b[1][0] if b else ''))
    rec+= [out[0][0],out[1][0]] + list(out[0][1:]) + list(out[1][1:]) + [1]
    w.writerow(rec); st['prev']=Y
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
except RuntimeError as e: print('walk ended:',str(e)[:100])
for f in (1,2): print('field %d reasons:'%f, dict((k[1],v) for k,v in sorted(stats.items()) if k[0]==f))
print('units',st['n'])
