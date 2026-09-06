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
Usage: field_pair_review.py <capture> <reference.csv> <out.mp4> --mode raw|stabilized [--start-ordinal N] [--max-units N]"""
import sys, os, csv, argparse, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from PIL import Image, ImageDraw
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
F={1:dict(origin_line=23, first_line=20, top='f1_picture_top_line', bot='f1_bottom_line', clip='f1_last_recorded_line'),
   2:dict(origin_line=286, first_line=283, top='f2_picture_top_line', bot='f2_bottom_line', clip='f2_last_recorded_line')}
H=243; W=720
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('ref'); ap.add_argument('out')
ap.add_argument('--mode',choices=['raw','stabilized'],required=True); ap.add_argument('--start-ordinal',type=int,default=0); ap.add_argument('--max-units',type=int,default=0)
A=ap.parse_args()
ref=list(csv.DictReader(open(A.ref)))
# sequential join: start at the reference row whose ordinal is nearest --start-ordinal, then advance one row per exact unit
pos=min(range(len(ref)), key=lambda i: abs(int(ref[i]['ordinal'])-A.start_ordinal))
ff=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{2*W}x{H}','-r','30000/1001','-i','-',
    '-vf','setsar=8/9','-c:v','prores_ks','-profile:v','3','-pix_fmt','yuv422p10le',A.out],stdin=subprocess.PIPE)   # ProRes HQ: keeps the odd 243-line height exactly, plays natively on macOS
n=[0]; hold={1:0,2:0}; buf=bytearray()
def val(r,k):
    try: return int(r[k])
    except: return None
def field_view(Y, f, top, bot, mode):
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
    return rgb, d
def emit(u):
    global pos
    c16=int.from_bytes(u[4:6],'little')
    if pos>=len(ref): raise SystemExit('reference exhausted')
    if n[0]==0:
        # first unit: locate the reference row with this counter nearest --start-ordinal (within 2000 rows), then go sequential
        cands=[i for i in range(max(0,pos-2000),min(len(ref),pos+2000)) if int(ref[i]['counter'])&0xffff==c16]
        if not cands: raise SystemExit(f'first unit counter {c16} not found within 2000 rows of ordinal {A.start_ordinal}')
        pos=min(cands,key=lambda i:abs(i-pos)); print('joined at reference ordinal',ref[pos]['ordinal'])
    r=ref[pos]
    if int(r['counter'])&0xffff!=c16: raise SystemExit(f'counter mismatch at reference ordinal {r["ordinal"]}: unit {c16} vs reference {r["counter"]} (join broken, aborting)')
    pos+=1; n[0]+=1
    Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2]
    frame=np.zeros((H,2*W,3),np.uint8); txt=[]
    for f in (1,2):
        top=val(r,F[f]['top']); bot=val(r,F[f]['bot'])
        if top is None or top<=0: top=None
        rgb,d=field_view(Y,f,top,bot,A.mode); frame[:,(f-1)*W:f*W]=rgb
        txt.append(f"F{f} top {top if top else '?'} bot {bot if (bot and bot>0) else '?'} d{d:+d}")
    im=Image.fromarray(frame); dr=ImageDraw.Draw(im)
    # bottom-left: mode and the reference values; bottom-right of EACH field: the unit number (transport ordinal) so a
    # frame can be named exactly when disputing it
    dr.text((4,H-12),f"{A.mode} | {txt[0]}",fill=(255,255,0)); dr.text((W+4,H-12),txt[1],fill=(255,255,0))
    for f in (1,2): dr.text((f*W-118,H-12),f"F{f} unit {r['ordinal']}",fill=(0,255,255))
    ff.stdin.write(np.asarray(im).tobytes())
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
ff.stdin.close(); ff.wait(); print('frames',n[0],'->',A.out,'ffmpeg rc',ff.returncode)
