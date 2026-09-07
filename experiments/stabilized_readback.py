#!/usr/bin/env python3
"""Machine read-back of a field-pair review render (experiments/field_pair_review.py), EVERY frame, from the PIXELS of
the finished video file — never from the CSV that produced it. Answers the owner's question for the stabilized clip:
"neither red line should ever move once", and the two questions that follow from it.

Per frame, per field panel (field 1 = x 0..719, field 2 = x 720..1439; 243 rows = NTSC lines 20..262 / 283..525):
  1. RED BARS: the rows whose pixels are the renderer's red (R high, G and B suppressed) across the panel width. Exactly
     two are expected (top, bottom). Every frame where either row differs from the previous frame is reported by unit.
     If a manifest (<render>.frames.csv, written by the renderer) exists, the found rows are also checked against the
     rows the renderer SAID it drew (rt = top - first_line - shift): a mismatch is a renderer/decoder defect.
  2. PICTURE SHIFT between consecutive frames: brute-force integer vertical shift in -3..+3 of the rows between the bars
     (minimum MAD), with the decisiveness ratio best/second-best; sign = the picture's displacement in the output,
     positive = it moved down. In a stabilized clip a decisive nonzero shift means
     the picture moved in the OUTPUT. Content motion (a tilt, a cut) is not separated here; the list names the units so
     they can be looked at.
  3. PICTURE ABOVE THE TOP BAR / BELOW THE BOTTOM BAR: a row outside the bars is "picture-like" when it correlates with
     the nearest picture row (normalized correlation >= CORR) AND carries horizontal texture comparable to the body
     (gradient energy >= GRAD x the body's median). Those two constants are this instrument's only thresholds; they are
     printed in the header, and the per-row numbers are in the CSV so a reader can re-decide.
Output: <render>.readback.csv (one row per frame per field) and a summary with counts and the failing unit numbers.
Exit status 1 if any red bar moved between consecutive frames in either field, else 0.
Usage: stabilized_readback.py <render.mov> [--manifest <frames.csv>] [--corr 0.7] [--grad 0.5] [--max-list 40]"""
import sys, os, csv, argparse, subprocess, numpy as np
ap=argparse.ArgumentParser(); ap.add_argument('render'); ap.add_argument('--manifest'); ap.add_argument('--corr',type=float,default=0.7)
ap.add_argument('--grad',type=float,default=0.5); ap.add_argument('--max-list',type=int,default=40); ap.add_argument('--out')
ap.add_argument('--vscale',type=int,default=0,help='rows per raster line in the render (0 = infer from the height: 243 x vscale)')
A=ap.parse_args()
W=720; FIRST={1:20,2:283}
pr=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames','-of','csv=p=0',A.render],capture_output=True,text=True,check=True)
width,height,nb=[x for x in pr.stdout.strip().split(',')]; width=int(width); H=int(height); nb=int(nb) if nb.isdigit() else -1
INFO=width-2*W; assert INFO in (200,230), f'unexpected width {width}: not a field_pair_review render'
VS=A.vscale or (H//243 if H%243==0 else 1); assert H==243*VS, f'height {H} is not 243 x {VS}'
H0=H; H=243   # all row arithmetic below is in raster rows; the frame is reduced by taking one pixel row per raster row
man=None; mpath=A.manifest or (A.render+'.frames.csv')
if os.path.exists(mpath):
    man=list(csv.DictReader(open(mpath)))
    if nb>=0 and len(man)!=nb: print(f'WARNING manifest rows {len(man)} != video frames {nb}; joining by frame index anyway')
ff=subprocess.Popen(['ffmpeg','-v','error','-i',A.render,'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE); FS=width*H0*3
def red_rows(p):
    r=p[:,:,0].astype(np.int16); gb=np.maximum(p[:,:,1],p[:,:,2]).astype(np.int16)
    frac=((r-gb)>=100).mean(axis=1)            # the renderer draws R=255, G=B=Y//3: redness >= 170 on every column before compression
    return list(np.nonzero(frac>=0.95)[0])
def luma(p): return p.astype(np.float32).mean(axis=2)
def corr(a,b):
    a=a-a.mean(); b=b-b.mean(); d=np.sqrt((a*a).sum()*(b*b).sum())
    return float((a*b).sum()/d) if d>0 else 0.0
def grad(row): return float(np.abs(np.diff(row)).mean())
out=open(A.out or (A.render+'.readback.csv'),'w'); wr=csv.writer(out)
wr.writerow(['frame','ordinal','counter','field','n_red','red_top','red_bot','man_top','man_bot','top_moved','bot_moved','shift','ratio','above_pict_rows','below_pict_rows','above_detail','below_detail'])
prev={1:None,2:None}; prevY={1:None,2:None}; k=0
S={f:dict(top_moved=[],bot_moved=[],nred=[],shift=[],above=[],below=[],man_mismatch=[],shifts={},ratios=[]) for f in (1,2)}
while True:
    b=ff.stdout.read(FS)
    if len(b)<FS: break
    fr=np.frombuffer(b,np.uint8).reshape(H0,width,3)[VS//2::VS]   # the middle pixel row of each doubled raster row
    m=man[k] if (man and k<len(man)) else None
    ordinal=m['ordinal'] if m else str(k); counter=m['counter'] if m else ''
    for f in (1,2):
        p=fr[:,(f-1)*W:f*W]; rr=red_rows(p); n=len(rr)
        rt=rr[0] if n else -1; rb=rr[-1] if n>=2 else -1
        if n!=2: S[f]['nred'].append((ordinal,n))
        mt=mb=-1
        if m:
            top=int(m[f'f{f}_top']); bot=int(m[f'f{f}_bot']); sh=int(m[f'f{f}_shift'])
            mt=(top-FIRST[f]-sh) if top>0 else -1; mb=(bot-FIRST[f]-sh) if bot>0 else -1
            if (mt if 0<=mt<H else -1)!=rt or (mb if 0<=mb<H else -1)!=rb: S[f]['man_mismatch'].append((ordinal,rt,rb,mt,mb))
        tm=bm=0
        if prev[f] is not None:
            if rt!=prev[f][0]: tm=1; S[f]['top_moved'].append((ordinal,prev[f][0],rt))
            if rb!=prev[f][1]: bm=1; S[f]['bot_moved'].append((ordinal,prev[f][1],rb))
        Y=luma(p); shift=''; ratio=''
        if rt>=0 and rb>rt+12 and prevY[f] is not None:
            a=rt+1+3; bb=rb-3; ref=prevY[f][a:bb]
            mads={s:float(np.abs(Y[a+s:bb+s]-ref).mean()) for s in range(-3,4) if a+s>=0 and bb+s<=H}
            best=min(mads,key=mads.get); srt=sorted(mads.values()); ratio=srt[0]/srt[1] if srt[1]>0 else 1.0; shift=best
            S[f]['shifts'][best]=S[f]['shifts'].get(best,0)+1; S[f]['ratios'].append(ratio)
            if best!=0 and ratio<=0.8: S[f]['shift'].append((ordinal,best,round(ratio,2)))
        ab=[]; be=[]; adet=[]; bdet=[]
        if rt>=0 and rb>rt+2:
            body=Y[rt+1:rb]; gmed=float(np.median([grad(r) for r in body]))
            first=Y[rt+1]; last=Y[rb-1]
            for r in range(0,rt):
                c=corr(Y[r],first); g=grad(Y[r]); adet.append(f'{r}:L{Y[r].mean():.1f}/c{c:.2f}/g{g:.1f}')
                if c>=A.corr and g>=A.grad*gmed: ab.append(r)
            for r in range(rb+1,H):
                c=corr(Y[r],last); g=grad(Y[r]); bdet.append(f'{r}:L{Y[r].mean():.1f}/c{c:.2f}/g{g:.1f}')
                if c>=A.corr and g>=A.grad*gmed: be.append(r)
            if ab: S[f]['above'].append((ordinal,ab))
            if be: S[f]['below'].append((ordinal,be))
        wr.writerow([k,ordinal,counter,f,n,rt,rb,mt,mb,tm,bm,shift,f'{ratio:.3f}' if ratio!='' else '',' '.join(map(str,ab)),' '.join(map(str,be)),' '.join(adet),' '.join(bdet[:6])])
        prev[f]=(rt,rb); prevY[f]=Y
    k+=1
out.close(); ff.wait()
print(f'READBACK {A.render}: {k} frames (manifest rows {len(man) if man else "none"}), panel {W}x{H}, thresholds corr>={A.corr} grad>={A.grad}x body median')
fail=0
for f in (1,2):
    s=S[f]; L=A.max_list
    print(f'FIELD {f}: red rows != 2 in {len(s["nred"])} frames {s["nred"][:L]}')
    print(f'  top bar moved in {len(s["top_moved"])} frames: {s["top_moved"][:L]}')
    print(f'  bottom bar moved in {len(s["bot_moved"])} frames: {s["bot_moved"][:L]}')
    print(f'  renderer manifest mismatch (unit, found top, found bot, said top, said bot): {len(s["man_mismatch"])} {s["man_mismatch"][:L]}')
    print(f'  picture shift between consecutive frames, decisive (ratio<=0.8) and nonzero: {len(s["shift"])} frames {s["shift"][:L]}')
    print(f'  shift histogram (all frames): {dict(sorted(s["shifts"].items()))}; ratio quantiles p50/p90 {np.percentile(s["ratios"],[50,90]).round(3).tolist() if s["ratios"] else "n/a"}')
    print(f'  picture-like rows ABOVE the top bar: {len(s["above"])} frames {s["above"][:L]}')
    print(f'  picture-like rows BELOW the bottom bar: {len(s["below"])} frames {s["below"][:L]}')
    fail|=bool(s['top_moved'] or s['bot_moved'])
sys.exit(1 if fail else 0)
