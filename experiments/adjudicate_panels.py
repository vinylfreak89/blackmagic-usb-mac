#!/usr/bin/env python3
"""Adjudicate engine-vs-reference disagreements on the RAW raster. For each (field, authority, delta) class in the
scorer's disagreements.csv, sample N ordinals, cut a few units around each from the whole-tape capture (byte-offset
seek via tpc_slice.py, exact join by the device counter from the reference CSV), and render the field's top rows with
the engine's published crop (blue), the reference top (red) and the reference's caption/waveform lines (yellow).
Usage: adjudicate_panels.py <capture> <reference.csv> <disagreements.csv> <outdir> --classes "1:geometry:-1,1:geometry:+1" [--n 3]"""
import sys, os, csv, argparse, subprocess, collections, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from PIL import Image, ImageDraw
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('ref'); ap.add_argument('dis'); ap.add_argument('out')
ap.add_argument('--classes',required=True); ap.add_argument('--n',type=int,default=3); ap.add_argument('--scratch',default='/private/tmp/hw-session/adj_slices')
A=ap.parse_args(); os.makedirs(A.out,exist_ok=True); os.makedirs(A.scratch,exist_ok=True)
ref={int(r['ordinal']):r for r in csv.DictReader(open(A.ref))}
dis=list(csv.DictReader(open(A.dis)))
TOT=os.path.getsize(A.cap); BPU=TOT/86296
F={1:dict(insert=17,origin=19),2:dict(insert=280,origin=282)}
def grab(ordinal, counter):
    """cut ~6 units around the ordinal and return the raster whose 16-bit counter matches"""
    path=os.path.join(A.scratch,f'o{ordinal}.tpc')
    if not os.path.exists(path):
        start=int(max(0,(ordinal-6)*BPU))   # bytes/unit is an average (audio+tags vary); cut wide and join by counter
        subprocess.run(['python3',os.path.join(os.path.dirname(__file__),'tpc_slice.py'),A.cap,path,'--start-bytes',str(start),'--video-bytes',str(20*UNIT)],check=True,capture_output=True)
    found={}; buf=bytearray()
    def emit(u):
        c16=int.from_bytes(u[4:6],'little'); found[c16]=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].copy()
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
    try: walk_tagged(path,on_video=on_video,progress=False)
    except RuntimeError: pass
    return found.get(counter&0xffff), sorted(found)
VS=8; W=720; LAB=52; TITLE=16
for cls in A.classes.split(','):
    f,auth,delta=cls.split(':'); f=int(f); delta=int(delta)
    rows=[r for r in dis if int(r['field'])==f and r['authority']==auth and int(r['delta'])==delta]
    if not rows: print('no rows for',cls); continue
    picks=[rows[k*len(rows)//A.n] for k in range(min(A.n,len(rows)))]
    Fd=F[f]; R0,R1=Fd['insert']-2,Fd['origin']+12
    img=Image.new('RGB',(LAB+W,len(picks)*((R1-R0)*VS+TITLE+6)+4),(0,0,0)); d=ImageDraw.Draw(img); y=2
    for r in picks:
        o=int(r['ordinal']); rr=ref[o]; Y,have=grab(o,int(rr['counter']))
        if Y is None: d.text((4,y+2),f"ordinal {o}: unit with counter {rr['counter']} not in the cut (have {have[:3]}..)",fill=(255,80,80)); y+=TITLE+6; continue
        pub=int(r['published_start'])-4; rt=int(r['reference_top'])-4
        cc=rr.get(f'f{f}_cc_waveform_lines','') ; par=rr.get(f'f{f}_cc_parity_lines','')
        stat=lambda rw: f"{Y[rw,40:680].mean():.0f}/{Y[rw,40:680].std():.0f}"
        d.text((4,y+2),f"ordinal {o} ({o*1001/30000:.1f}s) field {f} {auth} delta {delta}: engine crop line {pub+4} (blue, luma {stat(pub)}), reference top {rt+4} (red, luma {stat(rt)}), ref status {rr.get(f'f{f}_top_status','')}, waveform {cc} parity {par}",fill=(255,255,255)); y+=TITLE
        img.paste(Image.fromarray(np.repeat(Y[R0:R1],VS,axis=0)),(LAB,y))
        for k,row in enumerate(range(R0,R1)):
            d.text((2,y+k*VS-1),f"{row+4}",fill=(140,140,140)); d.line([(LAB-3,y+k*VS),(LAB+W,y+k*VS)],fill=(50,50,50))
        for line_txt in (cc,par):
            for tok in str(line_txt).replace(';',' ').replace('|',' ').split():
                if tok.lstrip('-').isdigit():
                    rw=int(tok)-4
                    if R0<=rw<R1: d.line([(LAB,y+(rw-R0)*VS+VS//2),(LAB+W,y+(rw-R0)*VS+VS//2)],fill=(255,200,0))
        if R0<=rt<R1: d.line([(LAB,y+(rt-R0)*VS),(LAB+W,y+(rt-R0)*VS)],fill=(255,0,0)); d.text((LAB+W-90,y+(rt-R0)*VS-1),'REF TOP',fill=(255,0,0))
        if R0<=pub<R1: d.line([(LAB,y+(pub-R0)*VS+2),(LAB+W,y+(pub-R0)*VS+2)],fill=(0,160,255)); d.text((LAB+W-180,y+(pub-R0)*VS+1),'ENGINE CROP',fill=(0,160,255))
        y+=(R1-R0)*VS+6
    fn=os.path.join(A.out,f"f{f}_{auth}_{delta:+d}.png".replace('+','p').replace('-','m')); img.save(fn); print('saved',fn,'class size',len(rows),'samples',[int(r['ordinal']) for r in picks])
