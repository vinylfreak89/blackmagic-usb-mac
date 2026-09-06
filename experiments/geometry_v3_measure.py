#!/usr/bin/env python3
"""Geometry measurement v3 (contract v2, docs/geometry_first_engine.md §8), per unit per field, raw raster only.
Built on two facts measured on the commercial tape's stable region (units 551..1132, 2026-09-07, edge_rows_census.py):
  RECORDED  a row that came through the analog decoder carries the decoder's chroma noise; the Shuttle's regenerated
            rows (blanking, line 22/285, 263+/526+) carry a flat chroma. Ratio of a row's chroma std to the unit's own
            blanking rows' chroma std: blank rows max 1.48, recorded rows min 2.02 over 44,232 row readings, black
            pictures included (luma is clipped to blanking in a black picture; chroma noise is not). RASTER-derived
            rule: recorded = ratio >= 1.75 (the gap's midpoint); re-verify on every new source.
  BOTTOM    the last row whose left and right active edges sit inside the body's own edge variance, scanning UP from
            the clip line (§8 point 4); the head-switch band's edges fall outside it; a dark row inside the picture
            cannot end the picture. Edges: first/last sample above the blanking luma + 6 x its std (§8's "timing is
            never perfect" variance is the body rows' own min..max of left and right).
Per field per unit, NTSC lines:  rec_first, rec_last (the recorded region = the deck's raster, a per-source constant),
  top (= rec_first here; VBI-type rows above the picture are NOT yet skipped — fixture A work, not the commercial
  tape), bottom (edge variance, -1 when the body has too few edged rows: black picture), band_last (last recorded row
  with any edge below the bottom), body edge range, shift vs previous unit (-6..+6, MAD best/second), flat.
Usage: geometry_v3_measure.py <capture> <out.csv> [--ratio 1.75]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out'); ap.add_argument('--ratio',type=float,default=1.75); A=ap.parse_args()
# unit rows (line = row + 4): pass-through region rows 19..260 / 282..522 by the reference raster; the search spans the
# whole non-padding region so a displaced recorded region is still found
F={1:dict(blank=(7,15),search=(16,261),body_off=20,body_len=200),2:dict(blank=(270,278),search=(279,523),body_off=20,body_len=200)}
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['unit','counter','field','rec_first','rec_last','top','bottom','band_last','switch_line','band_first','seam_line','seam_ratio','n_body_edged','left_lo','left_hi','right_lo','right_hi','shift','mad','mad2','flat','body_med','body_ystd','blank_y','blank_cstd'])
st=dict(first=None,n=0,prev={1:None,2:None}); buf=bytearray()
def emit(u):
    c=int.from_bytes(u[4:6],'little'); st['first']=c if st['first'] is None else st['first']; unit=(c-st['first'])&0xffff
    R=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE); Y=R[:,1::2].astype(np.float32); C=np.stack([R[:,0::4],R[:,2::4]],axis=1).astype(np.float32)  # C: (rows, 2, 360)
    for f,S in F.items():
        a,b=S['blank']; by=Y[a:b+1]; bc=C[a:b+1]; by_m,by_s=float(by.mean()),float(max(by.std(),0.5)); bc_s=float(max(bc.std(),0.3)); thr=by_m+6*by_s
        cstd=C.std(axis=(1,2)); rec=(cstd/bc_s)>=A.ratio
        s0,s1=S['search']; rr=[r for r in range(s0,s1+1) if rec[r]]
        rec_first=rr[0] if rr else -1; rec_last=rr[-1] if rr else -1
        above=Y>thr; anyr=above.any(axis=1); left=np.where(anyr,above.argmax(axis=1),-1); right=np.where(anyr,Y.shape[1]-1-above[:,::-1].argmax(axis=1),-1)
        top=rec_first
        bottom=band_last=switch_line=band_first=seam_line=-1; seam_ratio=''; llo=lhi=rlo=rhi=-1; nbe=0
        if rec_first>=0 and rec_last-rec_first>60:
            b0=rec_first+S['body_off']; b1=min(b0+S['body_len'],rec_last-10)
            ok=(left[b0:b1]>=0)&(right[b0:b1]>=0); nbe=int(ok.sum())
            RUN=100; dY=np.abs(np.diff(Y,axis=0)); lrun=dY[:,10:10+RUN].mean(axis=1); rrun=dY[:,710-RUN:710].mean(axis=1)
            lref=max(float(lrun[b0-1:b1-1].max()),0.25); rref=max(float(rrun[b0-1:b1-1].max()),0.25)
            for r in range(b1,rec_last+1):
                if lrun[r-1]>lref or rrun[r-1]>rref: band_first=r; break
            if nbe>=20:
                bl=left[b0:b1][ok]; br=right[b0:b1][ok]; llo,lhi,rlo,rhi=int(bl.min()),int(bl.max()),int(br.min()),int(br.max())
                for r in range(rec_last,b1-1,-1):
                    if left[r]>=0 and band_last<0: band_last=r
                    if left[r]>=0 and llo<=left[r]<=lhi and rlo<=right[r]<=rhi: bottom=r; break
                # SWITCH LINE (measured 2026-09-07 on the commercial tape, zoomed rows 255-263 / 518-526): the head
                # switch lands mid-line (field 1 ~35% into line 260, field 2 at the far right of 522); from that row
                # down the row carries the other head: its edge falls outside the body's range (a bright run to
                # sample 719 past the picture's 718, or a black run putting the left edge at 0 / ~137). The first row
                # below the body with an edge outside the range is the switch line; rows with no edge (dark picture
                # content) are skipped, never taken as an edge. A per-source constant: the decision layer locks it.
                for r in range(b1,rec_last+1):
                    if left[r]<0: continue
                    if not (llo<=left[r]<=lhi and rlo<=right[r]<=rhi): switch_line=r; break
                # SEAM (owner, 2026-09-07: the band can be on either side): from the switch line down, one horizontal
                # region of the row carries the other head and departs from the row above while the rest continues.
                # Per row, the mean |row - row above| in six 120-sample segments (segment 0 starts at sample 10, past
                # the H-blanking dip), each against the LARGEST such difference any body row shows in that segment —
                # the field's own row-to-row variance. The first row below the body where any segment exceeds it is
                # the seam: the partial line when the other head's level differs there, else the first band row; a
                # dark row inside the picture never departs. Side-agnostic by construction.
                SEG=[(10,120)]+[(k*120,(k+1)*120) for k in range(1,6)]
                dY=np.abs(np.diff(Y,axis=0))                                   # dY[r-1] = |Y[r]-Y[r-1]|
                segd=np.stack([dY[:,a:b].mean(axis=1) for a,b in SEG],axis=1)  # (rows-1, 6)
                ref=segd[b0-1:b1-1].max(axis=0)                                # body rows' own maxima per segment
                ratios=segd/np.maximum(ref,0.25)[None,:]
                for r in range(b1,rec_last+1):
                    q=float(ratios[r-1].max())
                    if q>1.0: seam_line=r; seam_ratio=round(q,2); break
        body=Y[rec_first+S['body_off']:rec_first+S['body_off']+S['body_len'],40:680] if rec_first>=0 else None
        shift=mad=mad2=''; flat=''; body_med=body_ystd=''
        if body is not None and body.shape[0]==S['body_len']:
            flat=round(float(np.abs(np.diff(body,axis=0)).mean()),2); body_med=round(float(np.median(body)),1); body_ystd=round(float(np.median(body.std(axis=1))),2)
            P=st['prev'][f]
            if P is not None:
                b0=rec_first+S['body_off']
                res=sorted(((s,float(np.abs(P[6:-6]-Y[b0+6+s:b0+S['body_len']-6+s,40:680]).mean())) for s in range(-6,7)),key=lambda x:x[1])
                shift,mad,mad2=res[0][0],round(res[0][1],2),round(res[1][1],2)
            st['prev'][f]=body
        L=lambda r:(r+4 if r>=0 else -1)
        w.writerow([unit,c,f,L(rec_first),L(rec_last),L(top),L(bottom),L(band_last),L(switch_line),L(band_first),L(seam_line),seam_ratio,nbe,llo,lhi,rlo,rhi,shift,mad,mad2,flat,body_med,body_ystd,round(by_m,2),round(bc_s,2)])
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
try: walk_tagged(A.cap,on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:80])
print('units',st['n'],'->',A.out)
