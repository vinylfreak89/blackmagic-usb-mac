#!/usr/bin/env python3
"""Per-row, per-unit properties from the unit's own regenerated rows — the same code for every capture, no profile,
no lock, no constant fitted to a tape (owner, 2026-09-07: "measure very simple constraints about luma, chroma,
positioning within the horizontal blanking region").
Per field of every exact unit, using the field's own blanking rows (lines 11..19 / 274..282) as the reference:
  blank_y, blank_ystd, blank_cstd     the regenerated blank: luma level, its noise, its chroma noise
  per line (pass-through region 20..264 / 283..527):
    recorded   chroma noise > 2x the blank's (the decoder's noise passes only through recorded rows)
    y          luma mean; above_black = y > blank_y + 6*blank_ystd
    left/right first/last sample above blank_y + 6*blank_ystd
    in_place   the active content sits where an active line sits inside the H blanking structure:
               left within the field's own body-left range, right within its body-right range (the body = the 200
               rows below the first 20 recorded rows; ranges = min..max over rows with edges, widened by 1 sample:
               the measured 717/718/719 jitter of a full-width line); skewed rows and the other head's rows are not
  derived: top = first row recorded & in_place & above_black; bottom = last such row; switch = first recorded row
  below the top that is not in_place (its content is displaced) — reported, never locked.
Usage: row_properties.py <capture> <out.csv> [--units a,b,c] (rows only for the named units; derived values for all)"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out'); ap.add_argument('--units',default=''); A=ap.parse_args()
dump={int(x) for x in A.units.split(',') if x}
F={1:dict(blank=(7,15),span=(16,260)),2:dict(blank=(270,278),span=(279,523))}   # unit rows; line = row + 4
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['unit','counter','field','top','bottom','switch','n_pic','blank_y','blank_cstd','llo','lhi','rlo','rhi'])
rw=csv.writer(open(A.out+'.rows.csv','w',newline='')); rw.writerow(['unit','field','line','y','ystd','cstd_ratio','recorded','above_black','left','right','in_place'])
st=dict(first=None,n=0); buf=bytearray()
def emit(u):
    c=int.from_bytes(u[4:6],'little'); st['first']=c if st['first'] is None else st['first']; unit=(c-st['first'])&0xffff
    R=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE); Y=R[:,1::2].astype(np.float32); C=np.stack([R[:,0::4],R[:,2::4]],axis=1).astype(np.float32)
    for f,S in F.items():
        a,b=S['blank']; by=Y[a:b+1]; bc=C[a:b+1]; by_m=float(by.mean()); by_s=float(max(by.std(),0.5)); bc_s=float(max(bc.std(),0.3)); thr=by_m+6*by_s
        cr=C.std(axis=(1,2))/bc_s; rec=cr>2.0
        above=Y>thr; anyr=above.any(axis=1); left=np.where(anyr,above.argmax(axis=1),-1); right=np.where(anyr,Y.shape[1]-1-above[:,::-1].argmax(axis=1),-1)
        ymean=Y.mean(axis=1); s0,s1=S['span']
        recrows=[r for r in range(s0,s1+1) if rec[r]]
        llo=lhi=rlo=rhi=-1; inplace=np.zeros(LINES,bool)
        if len(recrows)>40:
            b0=recrows[0]+20; b1=min(b0+200,recrows[-1]-10)
            ok=(left[b0:b1]>=0)&(right[b0:b1]>=0)
            if ok.sum()>=20:
                bl=left[b0:b1][ok]; br=right[b0:b1][ok]; llo,lhi,rlo,rhi=int(bl.min())-1,int(bl.max())+1,int(br.min())-1,int(br.max())+1
                inplace=(left>=llo)&(left<=lhi)&(right>=rlo)&(right<=rhi)
        # HEAD SWITCH by its own signatures against the row above (owner, 2026-09-07: RF peak, horizontal timing
        # garbage, AGC mismatch) — measured identically on every capture, no profile:
        #   rf     a localized transient: the row's max |diff to the row above| >= 6x its mean |diff| and >= 40 luma,
        #          with the rest of the row aligned (median segment lag 0)
        #   timing the row's content is time-shifted against the row above: median |segment lag| >= 2 samples or the
        #          median segment residual >= 3x the picture rows' own residual
        #   agc    a level step: |row mean - row above| >= 6x the blank noise with the row nearly flat (std < 3)
        # the switch line = the first row below the picture top carrying rf; the other head = rows after it carrying
        # timing or agc; picture = recorded rows above the switch that are above black
        SEG=[(30+k*55,30+(k+1)*55) for k in range(12)]
        def timing(r):
            """against the row above, over TEXTURED segments only (a flat segment matches at any lag): median |lag| of
            the best match, the residual at that lag, the residual at lag 0, the row's mean and max |diff|"""
            row=Y[r]; prev=Y[r-1]; lags=[]; res=[]; res0=[]
            for a,b in SEG:
                if float(prev[a:b].std())<4*by_s: continue
                cands=[(float(np.abs(row[a:b]-prev[a+s:b+s]).mean()),s) for s in range(-24,25)]
                best=min(cands,key=lambda x:x[0]); res.append(best[0]); lags.append(abs(best[1])); res0.append(cands[24][0])
            d=np.abs(row-prev)
            if len(lags)<3: return None
            return float(np.median(lags)),float(np.median(res)),float(np.median(res0)),float(d[30:690].mean()),float(d.max())
        sw=-1
        if len(recrows)>40:
            b0=recrows[0]+20; b1=min(b0+200,recrows[-1]-10)
            for r in range(b0,s1+1):
                t=timing(r)
                if t is None: continue
                lag,resid,resid0,dmean,dmax=t
                rf = dmax>=max(40.0,6*dmean) and lag==0                      # a localized transient on an aligned row
                tim = lag>=2 and resid0>=2*max(resid,1.0)                     # the row is shifted: a lag fits it twice as well as none
                agc = abs(float(ymean[r]-ymean[r-1]))>=6*by_s and float(Y[r,40:680].std())<3   # a flat level step
                if rf or tim or agc: sw=r; break
        pic=[r for r in range(s0,(sw if sw>0 else s1+1)) if rec[r] and ymean[r]>thr]
        top=pic[0] if pic else -1; bottom=(sw-1) if sw>0 else (pic[-1] if pic else -1)
        L=lambda r:(r+4 if r>=0 else -1)
        w.writerow([unit,c,f,L(top),L(bottom),L(sw),len(pic),round(by_m,2),round(bc_s,2),llo,lhi,rlo,rhi])
        if unit in dump:
            for r in range(s0,s1+1): rw.writerow([unit,f,r+4,round(float(ymean[r]),1),round(float(Y[r,40:680].std()),1),round(float(cr[r]),2),int(rec[r]),int(ymean[r]>thr),int(left[r]),int(right[r]),int(inplace[r])])
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
except RuntimeError as e: print('walk ended:',str(e)[:60])
print('units',st['n'],'->',A.out)
