#!/usr/bin/env python3
"""Field-pair review video: both fields of every unit side by side, one video frame per unit (29.97 fps), 1440x243,
SAR 8:9, with the harness reference's picture top and bottom for each field drawn as red bars.
Rows: NTSC lines 20..262 (field 1) and 283..525 (field 2), i.e. 243 raster lines per field, the three lines above the
standard picture start (20, 21, 22) at rows 0..2 and the picture at row 3 when the field is at its standard place.
  --mode raw         nothing shifted: the raster as captured; bars at the reference's top/bottom lines
  --mode stabilized  each field shifted by its reference displacement (top - 23 / top - 286) so the picture top sits
                     on row 3 every unit; rows 0..2 then show the TAPE's lines 20/21/22 wherever the displacement
                     brought them into the pass-through region (a displaced tape line 21 overwrites the device's
                     insert in the view); reading past the raster end shows the hard padding (legal black).
Every frame carries its transport ordinal, device counter, and the reference values used, so any frame can be checked
against the reference CSV. Join is by device counter (16-bit) sequentially from --start-ordinal; a unit whose counter
does not match the next reference row aborts (fail closed).
Usage: field_pair_review.py <capture> <reference.csv> <out.mov> --mode raw|stabilized [--start-ordinal N] [--max-units N] [--vscale 2]"""
import sys, os, csv, argparse, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from PIL import Image, ImageDraw
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F={1:dict(origin_line=23, first_line=20, top='f1_picture_top_line', bot='f1_bottom_line', hs='f1_hs_partial_line', clip='f1_last_recorded_line'),
   2:dict(origin_line=286, first_line=283, top='f2_picture_top_line', bot='f2_bottom_line', hs='f2_hs_partial_line', clip='f2_last_recorded_line')}
H=243; W=720; INFO=230   # info column appended to the RIGHT of the two fields; no text ever covers a raster row
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('ref'); ap.add_argument('out')
ap.add_argument('--mode',choices=['raw','stabilized'],required=True); ap.add_argument('--start-ordinal',type=int,default=0); ap.add_argument('--max-units',type=int,default=0)
ap.add_argument('--profile',type=int,default=3,help='ProRes profile: 3 = HQ (slices), 0 = proxy (whole tape, ~4 GB)')
ap.add_argument('--codec',choices=['prores','x264'],default='prores',help='x264: libx264 crf 14, yuv420p (row pairs align with doubled raster rows when --vscale 2), .mp4')
ap.add_argument('--vscale',type=int,default=1,help='duplicate every raster row this many times (owner: 2 -> 1440x486 reads more easily); bars scale with it')
A=ap.parse_args(); VS=A.vscale
ref=list(csv.DictReader(open(A.ref)))
# sequential join: start at the reference row whose ordinal is nearest --start-ordinal, then advance one row per exact unit
ff=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{2*W+INFO}x{H*VS}','-r','30000/1001','-i','-',
    '-vf','setsar=8/9']+(['-c:v','prores_ks','-profile:v',str(A.profile),'-pix_fmt','yuv422p10le'] if A.codec=='prores' else ['-c:v','libx264','-crf','14','-preset','slow','-pix_fmt','yuv420p','-movflags','+faststart'])+[A.out],stdin=subprocess.PIPE)   # ProRes HQ: keeps the odd 243-line height exactly, plays natively on macOS
n=[0]; hold={1:0,2:0}; buf=bytearray(); skipped=[]; prevY={1:None,2:None}
BODY={1:(43,243),2:(306,506)}   # raster rows compared unit to unit per field (lines 47..246 / 310..509), samples 40..680
def body_motion(Y,f):
    """the field's own unit-to-unit motion on the RAW raster: integer shift -3..+3 of this unit's body against the previous
    unit's, minimum mean abs difference, with the ratio best/second-best (<=0.8 decisive). Positive = moved down."""
    a,b=BODY[f]; P=prevY[f]; prevY[f]=Y
    if P is None: return None
    ref=P[a:b,40:680]; res=sorted(((sft,float(np.abs(Y[a+sft:b+sft,40:680].astype(np.float32)-ref).mean())) for sft in range(-3,4)),key=lambda x:x[1])
    return res[0][0], (res[0][1]/res[1][1] if res[1][1]>0 else 1.0)
manifest=open(A.out+'.frames.csv','w'); manifest.write('frame,ordinal,counter,f1_top,f1_bot,f1_shift,f2_top,f2_bot,f2_shift\n')   # read-back joins frames to units by this file, never by OCR
bycounter={}
for _i,_r in enumerate(ref): bycounter.setdefault(int(_r['counter'])&0xffff,[]).append(_i)
pos=0
def val(r,k):
    try: return int(r[k])
    except: return None
def field_view(Y, f, top, bot, mode, hs=None):
    Fd=F[f]; d = (top-Fd['origin_line']) if (top is not None and top>0 and mode=='stabilized') else 0
    r0=(Fd['first_line']-4)+d                       # raster row of the view's first line
    view=np.zeros((H,W),np.uint8)
    src=Y[max(0,r0):min(LINES,r0+H)]
    view[max(0,-r0):max(0,-r0)+len(src)]=src        # rows beyond the raster stay black (hard padding is black anyway)
    rgb=np.stack([view,view,view],axis=2)
    if top is not None and top>0:
        rt=(top-Fd['first_line'])-d; rb=(bot-Fd['first_line'])-d if (bot is not None and bot>0) else None
        if 0<=rt<H: rgb[rt,:,0]=255; rgb[rt,:,1]//=3; rgb[rt,:,2]//=3
        if rb is not None and 0<=rb<H: rgb[rb,:,0]=255; rgb[rb,:,1]//=3; rgb[rb,:,2]//=3
        # head-switch marker (owner, 2026-09-07: two bands, one for the head switch, one for the actual bottom): YELLOW
        rh=(hs-Fd['first_line'])-d if (hs is not None and hs>0) else None
        if rh is not None and 0<=rh<H and rh!=rb: rgb[rh,:,0]=255; rgb[rh,:,1]=255; rgb[rh,:,2]//=3
    return rgb, d
def emit(u):
    global pos
    c16=int.from_bytes(u[4:6],'little')
    # join by device counter: the reference carries exact units only; a capture unit whose counter the reference does
    # not carry (device-short, fragment) is skipped with a log line, never silently dropped or misaligned
    global bycounter
    cands=bycounter.get(c16,[])
    if n[0]==0 and cands:
        # first unit of a slice: the reference row with this counter nearest --start-ordinal (the 16-bit counter wraps)
        near=[min(cands,key=lambda i:abs(int(ref[i]['ordinal'])-A.start_ordinal))]; print('joined at reference ordinal',ref[near[0]]['ordinal'])
    else:
        near=[i for i in cands if i>=pos and i-pos<=64]
    if not near:
        skipped.append(c16); return
    pos=near[0]; r=ref[pos]
    pos+=1; n[0]+=1
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)
    frame=np.zeros((H,2*W+INFO,3),np.uint8); txt=[]; man=[]
    for f in (1,2):
        top=val(r,F[f]['top']); bot=val(r,F[f]['bot']); hs=val(r,F[f]['hs']) if F[f]['hs'] in r else None
        if top is None or top<=0: top=None
        rgb,d=field_view(Y,f,top,bot,A.mode,hs); frame[:,(f-1)*W:f*W]=rgb; man+= [top if top else -1, bot if (bot and bot>0) else -1, d]
        mo=body_motion(Y,f); motxt=('moved %+d vs prev (r %.2f)'%mo if (mo and mo[1]<=0.8) else ('still vs prev (r %.2f)'%mo[1] if mo else 'first unit'))
        txt.append(f"ref top {top if top else '?'} | ref bottom {bot if (bot and bot>0) else '?'} | head switch {hs if (hs and hs>0) else '?'} | displaced {d:+d} (crop {-d:+d}) | {motxt}")
    im=Image.fromarray(np.repeat(frame,VS,axis=0)); dr=ImageDraw.Draw(im); x0=2*W+6; HH=H*VS
    dr.rectangle([2*W,0,2*W+INFO-1,HH-1],fill=(28,28,28))
    dr.text((x0,6),f"unit {r['ordinal']}",fill=(0,255,255)); dr.text((x0,20),f"ctr {c16}  {A.mode}",fill=(200,200,200))
    for k,f in enumerate((1,2)):
        y0=44+k*100; dr.text((x0,y0),f"FIELD {f}",fill=(255,255,255))
        for q,line in enumerate(txt[k].split(' | ')): dr.text((x0,y0+14+q*14),line,fill=(255,200,200))
    dr.text((x0,HH-40),"rows: lines 20-262",fill=(120,120,120)); dr.text((x0,HH-26),"      / 283-525",fill=(120,120,120)); dr.text((x0,HH-12),"red = top/bottom  yellow = head switch",fill=(255,80,80))
    ff.stdin.write(np.asarray(im).tobytes())
    manifest.write(','.join(str(x) for x in [n[0]-1, r['ordinal'], c16]+man)+'\n')
    if A.max_units and n[0]>=A.max_units: raise StopIteration
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
try: walk_tagged(A.cap, on_video=on_video, progress=False)
except StopIteration: pass
except RuntimeError as e: print('walk ended:',str(e)[:100])
ff.stdin.close(); ff.wait(); manifest.close(); print('frames',n[0],'->',A.out,'ffmpeg rc',ff.returncode,'| capture units not in the reference (skipped):',len(skipped),skipped[:10])
