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
F1=dict(insert=17, blank22=18, origin=19, last=261)   # RASTER rows (line = row+4); 'last' = last pass-through row + 1
F2=dict(insert=280, blank22=281, origin=282, last=523)
CAP,OUT=sys.argv[1],sys.argv[2]; START=int(sys.argv[3]) if len(sys.argv)>3 else 0

def row_stats(Y): return Y.mean(axis=1), Y.std(axis=1)
def torn(rowfull):
    """An H-torn row: its active video starts before the raster's left blanking (RASTER: the first 12 of the 720
    samples are blanking, measured 2-20 on clean rows; a row whose first 6 samples carry picture-level luma lost its
    horizontal sync).  DEFAULT threshold 60 (picture level), raised from 20 after false positives on clean rows."""
    return rowfull[0:6].mean()>60
CORR=0.5      # DEFAULT: adjacent-row correlation that makes two rows one picture. MEASURED 2026-09-06 (35:00 and 05:00,
              # bright units): VBI rows vs their neighbours (insert, black 22, XDS bar, data line, caption) corr p90 <= 0.35;
              # picture row vs the next p10 >= 0.43 at the very top edge, 0.62-0.85 one row in.
FLAT=3.0      # DEFAULT: a row with std below this is flat; two flat rows at the same level (within FLAT_D) continue a picture
FLAT_D=4.0
def continuity(Y, m, s):
    """c[r] = 1 if rows r and r+1 belong to one two-dimensional picture: correlated across the line, or both flat at the
    same non-blank level. A VBI row is a one-dimensional waveform and never correlates with the picture under it."""
    A=Y-m[:,None]; ss=(A*A).sum(1); num=(A[:-1]*A[1:]).sum(1); den=np.sqrt(ss[:-1]*ss[1:]); den[den<1e-6]=1e-6
    corr=num/den
    flat=(s[:-1]<FLAT)&(s[1:]<FLAT)&(np.abs(m[:-1]-m[1:])<FLAT_D)&(m[:-1]>BLANK+8)
    c=np.zeros(len(m),bool); c[:-1]=(corr>=CORR)|flat
    return c, np.concatenate([corr,[0.0]])
def hs_partial(rowfull):
    """The head-switch line: picture on one side of a wandering split column, recorded black on the other. Returns
    (split_column, side) with side 'L' when the black run touches the left edge, 'R' the right, else None.
    DEFAULT black level 20 (recorded black measures ~11 on both fixtures, Shuttle blanking 1.4)."""
    blk=rowfull<=20; n=len(rowfull)
    L=0
    while L<n and blk[L]: L+=1
    R=0
    while R<n and blk[n-1-R]: R+=1
    if 0.1*n<L<0.95*n and L>=R: return L,'L'
    if 0.1*n<R<0.95*n: return n-R,'R'
    return None,None
def measure_field(Y, F, prev_field, Yfull=None):
    m, s = row_stats(Y)
    c, corr = continuity(Y, m, s)
    kind = {}; ntorn=0
    for r in range(F['insert']+1, F['last']):
        if Yfull is not None and r < F['origin']+40 and torn(Yfull[r]): kind[r]='torn'; ntorn+=1
        elif r < F['origin']+8 and cc608(Yfull[r] if Yfull is not None else Y[r])[0]: kind[r]='cc608'
        elif m[r] <= DARK: kind[r]='dark'
        elif c[r] and c[r+1]: kind[r]='picture'
        else: kind[r]='other'
    # top edge: first row from which the picture is continuous for PICTURE_ROWS rows
    top=None
    for r in range(F['insert']+1, F['last']-PICTURE_ROWS):
        if all(kind.get(r+k)=='picture' for k in range(PICTURE_ROWS)): top=r; break
    cap=[r for r in range(F['insert']+1, F['origin']+8) if kind.get(r)=='cc608']
    gap=None
    if top is not None:
        darks=[r for r in range(F['insert']+1, top) if kind.get(r)=='dark']
        gap=darks[-1] if darks else None
    # bottom edge: last row continuous with the row above it (measured per unit, no corridor); then the partial
    # head-switch line directly under it, if any, with its split column
    bottom=None; hs=(None,None)
    if top is not None:
        for r in range(F['last']-1, top+PICTURE_ROWS, -1):
            if c[r-1]: bottom=r; break
        if bottom is not None and bottom+1<F['last'] and Yfull is not None: hs=hs_partial(Yfull[bottom+1])
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
    # a torn top strip hides the edge: if any torn row lies within the first 12 rows above/at the found top, the edge is not trusted
    if top is not None and any(kind.get(r)=='torn' for r in range(F['insert']+1, top+12)): top=None
    return dict(top=top, cap=cap, gap=gap, bottom=bottom, hs_split=hs[0], hs_side=hs[1], body=body, ntorn=ntorn,
                height=(bottom-top+1) if (top is not None and bottom is not None) else None)

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
cols=['ordinal','counter_extended','transport','kind','applied_d1','applied_d2','f1_reason','f1_notes','f1_top','f1_bottom','f1_height','f1_hs_split','f1_cap','f1_gap','f1_body_up','f1_body_lo','f2_reason','f2_notes','f2_top','f2_bottom','f2_height','f2_hs_split','f2_cap','f2_gap','f2_body_up','f2_body_lo','published']
w.writerow(cols)
st=dict(n=0,prev=None); S=[FieldState(),FieldState()]; buf=bytearray(); stats=collections.Counter()
def emit(u):
    c16=int.from_bytes(u[4:6],'little'); o=START+st['n']; st['n']+=1
    Yall=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)   # full 720-sample luma rows (for the 608 decoder and the blanking test)
    Y=Yall[:,40:680]                                                                          # 640-sample active area for statistics
    prev=st['prev']; rec=[o,c16,'Complete',0]
    out=[]
    for f,F in ((0,F1),(1,F2)):
        pf=None if prev is None else prev
        mm=measure_field(Y,F,pf,Yall)
        d,reason,notes=decide(S[f],F,mm)
        stats[(f+1,reason)]+=1
        b=mm['body']; out.append((d,reason,';'.join(notes),mm['top'],mm['bottom'],mm['height'],(str(mm['hs_split'])+mm['hs_side']) if mm['hs_split'] is not None else '',mm['cap'][-1] if mm['cap'] else '',mm['gap'] if mm['gap'] is not None else '', b[0][0] if b else '', b[1][0] if b else ''))
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
