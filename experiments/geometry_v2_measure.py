#!/usr/bin/env python3
"""Contract v2 measurement layer (docs/geometry_first_engine.md §8), per unit per field, from the raw raster only.

Per line: the LEFT and RIGHT active edges = first and last sample whose luma rises above the field's own blanking
level by more than its noise (blanking rows 11-19 / 274-282 are the Shuttle's regenerated blank, measured per unit).
The picture body's edges sit within a variance (horizontal timing is never perfect); that variance is measured from
the body rows of the same unit. A line is PICTURE-LIKE when both its edges lie inside the body's range; the
head-switch band is the lines below the body whose edge falls outside it (left or right); rows with no active edge
at all (blank / recorded black under the pedestal) are not picture.
  top     first line at or above the body whose edges are picture-like, scanning up from the body until a line is
          not (the first non-picture-like line above stops the scan)
  bottom  last picture-like line scanning down from the body (the first line outside the range stops the scan)
  shift   brute-force vertical shift of the body against the previous unit's same field (-6..+6, all 640 columns,
          220 rows), with best and second-best MAD; no threshold here, the decision layer owns decisiveness
  flat    mean absolute row-to-row difference of the body (a mute/flat raster has none)
Nothing here classifies a row by what it carries. Usage: geometry_v2_measure.py <capture> <out.csv>"""
import sys, os, csv, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from cc608_decode import decode as cc608
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
FIELDS={1:dict(origin=19,last=261,blank=(7,16),body=(40,200)),2:dict(origin=282,last=523,blank=(270,279),body=(303,463))}
CAP,OUT=sys.argv[1],sys.argv[2]
w=csv.writer(open(OUT,'w',newline='')); w.writerow(['n','counter','field','top','top_texture','bottom','bottom_band','left_lo','left_hi','right_lo','right_hi','dip_mu','dip_sd','shift','mad','mad2','flat','edge_thr','comb_shift','comb','comb2','cap_line'])
st=dict(n=0,ext=None,prev={1:None,2:None}); buf=bytearray()
def line_edges(Y, thr):
    """per line: first and last sample above thr (None when the line never rises above the blanking)"""
    above=Y>thr; any_=above.any(axis=1)
    left=np.where(any_, above.argmax(axis=1), -1); right=np.where(any_, Y.shape[1]-1-above[:,::-1].argmax(axis=1), -1)
    return left,right
def emit(u):
    c16=int.from_bytes(u[4:6],'little')
    st['ext']=c16 if st['ext'] is None else st['ext']+((c16-(st['ext']&0xffff))&0xffff)
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)
    for f,F in FIELDS.items():
        a,b=F['blank']; blank=Y[a:b]; thr=float(blank.mean()+6*max(blank.std(),0.5))   # the field's own blanking level + its noise
        left,right=line_edges(Y,thr)
        b0,b1=F['body']; bl=left[b0:b1]; br=right[b0:b1]; ok=(bl>=0)&(br>=0)
        if ok.sum()<20:   # no measurable body (mute/flat/black): no edges to compare against
            top=bottom=bottom_band=-1; llo=lhi=rlo=rhi=-1; dmu=dsd=-1
        else:
            llo,lhi=int(bl[ok].min()),int(bl[ok].max()); rlo,rhi=int(br[ok].min()),int(br[ok].max())
            # HORIZONTAL TIMING SIGNATURE (measured 2026-09-06): every properly timed picture line begins with the
            # source's own horizontal-blanking dip, samples 0..6 at luma 1-3 (05:00) / 2-8 (35:00), before the content
            # rises; a recorded-black row or a head-switch line has no dip, it sits at the pedestal (~11) from sample 0.
            # The dip's level, against the body's own variance, is the per-row test; the threshold edges are not.
            dip=Y[:,0:7].mean(axis=1); bd=dip[b0:b1]; dmu,dsd=float(bd.mean()),float(max(bd.std(),0.5))
            dlo,dhi=float(bd.min()),float(bd.max())          # the body's own dip range (measured per unit, not a spread model)
            timed=lambda r: left[r]>=0 and (dlo-1.0)<=dip[r]<=(dhi+1.0)
            inside=lambda r: left[r]>=0 and llo<=left[r]<=lhi and rlo<=right[r]<=rhi   # edges only; the dip gates the bottom, never the top
            outward=lambda r: left[r]>=0 and (left[r]<llo or right[r]>rhi)
            # two bottoms, both reported: strict = last row that is timed AND whose edges are inside the body's
            # variance; band = last row that is timed (the switch line's inward edge does not end it). A row with no
            # content or no dip ends both.
            bottom=b1-1; bottom_band=b1-1; strict_done=False
            for r in range(b1,F['last']):
                if not timed(r): break
                bottom_band=r
                if not strict_done and inside(r) and timed(r): bottom=r
                else: strict_done=True
            # lock-time top: the first row above the body whose edges are inside the body's range AND whose content
            # continues into the row below (a picture row); its texture is reported as the lock confidence
            top=b0
            for r in range(b0-1,F['origin']-3,-1):
                if inside(r) and np.corrcoef(Y[r,40:680],Y[r+1,40:680])[0,1]>=0.5: top=r
                elif outward(r) or left[r]<0: break
                else: break
        body=Y[b0:b1,40:680]
        flat=float(np.abs(np.diff(body,axis=0)).mean())
        # confirmation only: the unique line above the body (excluding the device's regenerated 21/284) that decodes
        # as a caption with valid parity; '' none, 'multi' more than one
        ins=17 if f==1 else 280
        hits=[r for r in range(F['origin']-7, b0) if r!=ins and cc608(Y[r])[0]]
        cap='' if not hits else (str(hits[0]+4) if len(hits)==1 else 'multi')
        comb=comb2=combs=''
        if f==2:
            # weave field 1 rows (19+10 .. ) with field 2 rows (282+10+s ..): comb energy = mean |2*f2 - f1(k) - f1(k+1)|
            A=Y[19+10:19+160,40:680]; res=[]
            for sft in range(-3,4):
                B=Y[282+10+sft:282+160+sft,40:680]; res.append((sft,float(np.abs(2*B[:-1]-A[:-1]-A[1:]).mean())))
            res.sort(key=lambda x:x[1]); combs,comb,comb2=res[0][0],round(res[0][1],2),round(res[1][1],2)
        shift=mad=mad2=''
        P=st['prev'][f]
        if P is not None:
            res=sorted(((s,float(np.abs(P[6:-6]-Y[b0+6+s:b1-6+s,40:680]).mean())) for s in range(-6,7)),key=lambda x:x[1])
            shift,mad,mad2=res[0][0],round(res[0][1],2),round(res[1][1],2)
        st['prev'][f]=body
        tex=round(float(Y[top,40:680].std()),1) if top>=0 else -1
        w.writerow([st['n'],st['ext'],f,(top+4 if top>=0 else -1),tex,(bottom+4 if bottom>=0 else -1),(bottom_band+4 if bottom_band>=0 else -1),llo,lhi,rlo,rhi,(round(dmu,1) if ok.sum()>=20 else -1),(round(dsd,2) if ok.sum()>=20 else -1),shift,mad,mad2,round(flat,2),round(thr,1),combs,comb,comb2,cap])
    st['n']+=1
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
try: walk_tagged(CAP,on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:80])
print('units',st['n'],'->',OUT)
