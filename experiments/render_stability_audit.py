#!/usr/bin/env python3
# Audit a rendered 59.94p bob review copy for the two things a viewer sees at once and the sidecar cannot prove:
#   1. a VBI-type line inside the output frame (CEA-608 run-in / timing-line pulses / a smeared data bar) on the top or
#      bottom rows of any frame;
#   2. the picture moving vertically from one unit to the next (same-field frames compared), which is either an
#      engine follow of a still picture or a miss of a moving one — either way an output jump.
# Frames are read as gray via ffmpeg; frame 2i/2i+1 = unit i field 1/2 (the render's own convention).
# Usage: render_stability_audit.py render.mp4 [--start-unit N] [--units M] [--csv out.csv]
import sys, argparse, subprocess, csv, collections, numpy as np
W,H=720,480; CELL=1.986e-6*13.5e6
_n=np.arange(10,230); _cos=np.cos(2*np.pi/CELL*_n); _sin=np.sin(2*np.pi/CELL*_n)
def run_in_amp(row):
    a=row[10:230]-row[10:230].mean(); return float(np.hypot(a@_cos,a@_sin)*2/220)
def bins(row,nb=24): return np.array([row[k*W//nb:(k+1)*W//nb].mean() for k in range(nb)])
def vbi_kind(row):
    b=bins(row)
    if run_in_amp(row)>=35 and row.mean()<95: return '608'
    if b[0]>80 and b[18:21].max()>100 and b[2:17].max()<40: return 'timing'
    if row.mean()<95 and b[20:].max()<=40 and (b[:20]>60).sum()>=6 and b.min()<25: return 'bar'
    return None
def vshift(a,b,rng=3):
    # vertical shift of picture b relative to a from column-averaged luma profiles of the picture body
    pa=a[24:456].mean(axis=1); pb=b[24:456].mean(axis=1); pa=pa-pa.mean(); pb=pb-pb.mean()
    if pa.std()<2 or pb.std()<2: return None, 0.0
    best=None
    for s in range(-rng,rng+1):
        x=pa[max(0,s):len(pa)+min(0,s)]; y=pb[max(0,-s):len(pb)+min(0,-s)]
        c=float(np.corrcoef(x,y)[0,1])
        if best is None or c>best[1]: best=(s,c)
    return best
ap=argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--start-unit',type=int,default=0); ap.add_argument('--units',type=int,default=10**9); ap.add_argument('--csv')
a=ap.parse_args()
t0=a.start_unit*1001/30000
cmd=["ffmpeg","-v","error","-ss",f"{t0:.6f}","-i",a.video,"-f","rawvideo","-pix_fmt","gray","pipe:1"]
proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,bufsize=W*H*4)
prev=[None,None]; unit=a.start_unit; data_units=collections.Counter(); jump_units=collections.Counter(); jumps=[]; datas=[]; cuts=0
wr=csv.writer(open(a.csv,'w',newline='')) if a.csv else None
if wr: wr.writerow(['unit','f1_data_top','f1_data_bottom','f2_data_top','f2_data_bottom','f1_shift','f1_corr','f2_shift','f2_corr'])
while unit < a.start_unit+a.units:
    buf=proc.stdout.read(W*H*2)
    if len(buf)<W*H*2: break
    F=np.frombuffer(buf,np.uint8).reshape(2,H,W).astype(np.float32)
    rec=[unit]
    for f in (0,1):
        top=[vbi_kind(F[f][r]) for r in range(0,4)]; bot=[vbi_kind(F[f][r]) for r in range(476,480)]
        kt=next((k for k in top if k),''); kb=next((k for k in bot if k),'')
        if kt or kb: data_units[(f+1,kt or kb)]+=1; datas.append((unit,f+1,kt or kb))
        s,c=(None,0.0) if prev[f] is None else vshift(prev[f],F[f])
        if s is None: s=''
        elif c<0.6: cuts+=1; s=''            # scene change / no comparable content
        elif s!=0: jump_units[f+1]+=1; jumps.append((unit,f+1,s))
        rec+= [kt,kb] if f==0 else [kt,kb]
        rec+= [s,round(c,3)]
        prev[f]=F[f]
    if wr: wr.writerow(rec)
    unit+=1
proc.stdout.close(); proc.wait()
n=unit-a.start_unit
print(f"units audited {n}; units with a VBI-type line in the output frame: {sum(data_units.values())} {dict(data_units)}; units whose picture moved vs the previous unit (same field, corr>=0.6): field1 {jump_units[1]} field2 {jump_units[2]}; unmeasurable (cuts/flat) {cuts}")
def runs(events):
    out=[]; 
    for u,*rest in events:
        if out and u<=out[-1][1]+1: out[-1][1]=u
        else: out.append([u,u])
    return out
def mmss(u): t=u*1001/30000; return f"{int(t//60)}:{t%60:05.2f}"
dr=runs(datas); jr=runs(jumps)
print(f"data-line runs: {len(dr)}; first 15: {[(mmss(a),b-a+1) for a,b in dr[:15]]}")
print(f"jump runs: {len(jr)}; first 15: {[(mmss(a),b-a+1) for a,b in jr[:15]]}")
