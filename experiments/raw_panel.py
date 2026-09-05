#!/usr/bin/env python3
"""Raw-raster panel: the top and bottom of both fields for a few consecutive units, with the engine's crop drawn in.

Rows are the Shuttle's unit rows (NTSC line = row + 4). Each unit is shown as four strips, vertically stretched 4x:
field-1 top rows 10..70, field-1 bottom rows 240..270, field-2 top rows 273..333, field-2 bottom rows 503..525.
A red line marks the first crop row (19 + applied_d1 / 282 + applied_d2); a blue line the last crop row.
Usage: raw_panel.py <slice.tpc> <sidecar.csv> <out.png> <ordinal> [<ordinal> ...]   (each ordinal shown with its two neighbours)
"""
import sys, csv, collections, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __import__('os').path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CAP,SIDE,OUT=sys.argv[1],sys.argv[2],sys.argv[3]; want=set(int(x) for x in sys.argv[4:])
rows_s=[(int(r['counter_extended']),r) for r in csv.DictReader(open(SIDE)) if r.get('transport')=='Complete' and r.get('kind')=='0']
by16=collections.defaultdict(list)
for i,(k,_) in enumerate(rows_s): by16[k&0xffff].append(i)
need=set()
for o in want: need.update((o-1,o,o+1))
byord={int(r['ordinal']):i for i,(_,r) in enumerate(rows_s)}
import os
grab={}; _last=[int(os.environ['RAW_PANEL_START'])] if os.environ.get('RAW_PANEL_START') else [None]; buf=bytearray()   # RAW_PANEL_START: whole-tape ordinal near the slice start, to disambiguate the 16-bit counter join
def emit(u):
    c=int.from_bytes(u[4:6],'little'); cands=by16.get(c)
    if not cands: return
    ref=_last[0] if _last[0] is not None else 0
    i=min(cands,key=lambda x:abs(x-ref))
    if _last[0] is not None and abs(i-_last[0])>200: return
    _last[0]=i
    o=int(rows_s[i][1]['ordinal'])
    if o in need: grab[o]=(rows_s[i][1], np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].copy())
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
except RuntimeError as e: print("walk ended:", str(e)[:80])
STRIPS=[(10,70,0),(240,270,0),(273,333,1),(503,525,1)]; SX=4; W=720; GAP=6; LBL=110
ords=sorted(o for o in need if o in grab)
H=sum((hi-lo)*SX+GAP for lo,hi,_ in STRIPS)+24
img=Image.new('RGB',(LBL+W*len(ords),H),(40,40,40)); dr=ImageDraw.Draw(img)
for k,o in enumerate(ords):
    r,Y=grab[o]; x0=LBL+k*W; y=0
    dr.text((x0+4,4),f"u{o} ctr{r['counter_extended']} d1={r['applied_d1']} d2={r['applied_d2']} f1={r['f1_reason']} f2={r['f2_reason']}",fill=(255,255,0))
    y=24
    for lo,hi,f in STRIPS:
        strip=np.repeat(Y[lo:hi],SX,axis=0); img.paste(Image.fromarray(strip).convert('RGB'),(x0,y))
        d=int(r['applied_d1' if f==0 else 'applied_d2']); first=(19 if f==0 else 282)+d; last=first+239
        for row,col in ((first,(255,0,0)),(last,(0,128,255))):
            if lo<=row<hi: dr.line((x0,y+(row-lo)*SX,x0+W,y+(row-lo)*SX),fill=col,width=1)
        if k==0:
            for row in range(lo,hi,5): dr.text((2,y+(row-lo)*SX-4),f"{row} L{row+4}",fill=(200,200,200))
        y+=(hi-lo)*SX+GAP
img.save(OUT); print('wrote',OUT,'units',ords)
