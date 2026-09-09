#!/usr/bin/env python3
"""Raw rows across the head-switch band, for a unit and its two neighbours, so a reported band change can be
looked at instead of inferred from a number.

Prose and labels are NTSC lines (unit row + 4). Each row is drawn twice: at natural scale, and stretched so
0..STRETCH codes fill 0..255 (the band sits near blanking, invisible at natural scale). The reference's T (the
band's top row) is marked in red on the left, its S (the switch line) in blue.
Usage: switch_panel.py <capture.tpc> <ref.csv> <out.png> <field 1|2> <counter> [<counter> ...]
"""
import sys, os, csv, collections, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
STRETCH=40.0; RH=11; W=720; GAP=18; LW=104

CAP,REF,OUT,FIELD = sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4])
want=[int(x) for x in sys.argv[5:]]
show=sorted({c+k for c in want for k in (-1,0,1)})
LINES_SHOWN = range(252,267) if FIELD==1 else range(514,529)

ref={}
for r in csv.DictReader(open(REF)):
    if int(r['field'])==FIELD: ref[int(r['counter'])]=r

grab={}
buf=bytearray()
def emit(u):
    c=int.from_bytes(u[4:6],'little')
    if c in show and c not in grab:
        grab[c]=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.uint8).copy()
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
except RuntimeError as e: print('walk ended:',str(e)[:60])
missing=[c for c in show if c not in grab]
if missing: print('MISSING counters (not rendered):',missing)
cols=[c for c in show if c in grab]
if not cols: sys.exit('no units found')

nr=len(list(LINES_SHOWN))
blockh=nr*RH+34
img=Image.new('RGB',(LW+len(cols)*(W+GAP), blockh*2+16),(14,14,16)); d=ImageDraw.Draw(img)
for bi,(name,stretch) in enumerate((('natural',False),(f'stretched 0..{int(STRETCH)} codes',True))):
    y0=bi*blockh+8
    d.text((6,y0),f'field {FIELD} — {name}',fill=(210,210,210))
    for ci,c in enumerate(cols):
        x0=LW+ci*(W+GAP); r=ref.get(c,{})
        d.text((x0,y0),f"ctr {c}  T={r.get('T','?')} S={r.get('S','?')} top={r.get('top','?')} band={r.get('switch_lines','?')}",fill=(230,230,120))
    for ri,ntsc in enumerate(LINES_SHOWN):
        y=y0+16+ri*RH
        d.text((6,y),f'line {ntsc}',fill=(170,170,180))
        for ci,c in enumerate(cols):
            x0=LW+ci*(W+GAP); row=grab[c][ntsc-4].astype(np.float32)
            v=np.clip(row/STRETCH*255.0,0,255) if stretch else row
            img.paste(Image.fromarray(np.repeat(v.astype(np.uint8)[None,:],RH-2,axis=0),'L').convert('RGB'),(x0,y))
            rr=ref.get(c,{})
            if rr.get('T') and int(rr['T'])==ntsc: d.rectangle([x0-7,y,x0-3,y+RH-3],fill=(230,60,60))
            if rr.get('S') and int(rr['S'])==ntsc: d.rectangle([x0-13,y,x0-9,y+RH-3],fill=(70,120,255))
img.save(OUT); print('wrote',OUT,img.size)

# the numbers behind the picture, so the panel and the census cannot drift apart
print(f"\nfield {FIELD}: per row, mean luma and the trailing run of samples within 3 codes of the row's last value")
hdr='line  ' + '  '.join(f'{c:>16}' for c in cols); print(hdr)
for ntsc in LINES_SHOWN:
    cells=[]
    for c in cols:
        row=grab[c][ntsc-4].astype(np.float32)
        lvl=float(row[715]); run=0
        for k in range(719,-1,-1):
            if abs(float(row[k])-lvl)<=3: run+=1
            else: break
        cells.append(f'{row[24:696].mean():7.2f} run{run:4d}')
    print(f'{ntsc:<5} ' + '  '.join(f'{x:>16}' for x in cells))
