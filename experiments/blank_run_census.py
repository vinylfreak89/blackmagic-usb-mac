#!/usr/bin/env python3
"""Census of blank-level runs INSIDE recorded rows, classed by the harness reference: for every unit and field, every row
from the reference's picture top to the last recorded row, the longest run of samples (within 24..696) whose luma stays
within 6 sigma_b of the field's blank (lines 11-19 / 274-282) — the decoder's blanking level. Picture rows (top .. switch-2)
vs the switch row (switch-1, switch) vs band rows (> switch). Prints the histogram of run lengths per class.
Usage: blank_run_census.py <capture> <reference.csv> <out.csv>"""
import sys, os, csv, numpy as np, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
cap,ref,out=sys.argv[1:4]
R={int(r['counter']):r for r in csv.DictReader(open(ref))}
SLOT={1:(20-4,265-4),2:(283-4,527-4)}   # frame rows of lines 20..264 / 283..526
w=csv.writer(open(out,'w',newline='')); w.writerow(['counter','field','line','cls','run','run_std','mean','std'])
H={f:collections.defaultdict(collections.Counter) for f in (1,2)}
buf=bytearray(); N=[0]
def runs_blank(row,by,sb):
    m=(np.abs(row[24:696]-by)<=6*sb).astype(np.int8)
    # longest run of ones
    best=0; cur=0; bs=0; s=0
    for i,v in enumerate(m):
        if v: 
            if cur==0: s=i
            cur+=1
            if cur>best: best=cur; bs=s
        else: cur=0
    seg=row[24+bs:24+bs+best] if best else row[0:0]
    return best,(float(seg.std()) if best>1 else 0.0)
def emit(u):
    c=int.from_bytes(u[4:6],'little'); N[0]+=1
    if c not in R: return
    F=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE); Y=F[:,1::2].astype(np.float32)
    for f in (1,2):
        a,b=SLOT[f]; bl=Y[a-9:a-1]; by=float(bl.mean()); sb=float(max(bl.std(),0.5))
        top=int(R[c].get(f'f{f}_picture_top_line') or -1); sw=int(R[c].get(f'f{f}_switch_first_line') or -1); last=int(R[c].get(f'f{f}_last_recorded_line') or -1)
        if top<0 or sw<0 or last<0: continue
        for L in range(top,last+1):
            row=Y[L-4]
            cls='pic' if L<=sw-2 else ('sw-1' if L==sw-1 else ('sw' if L==sw else 'band'))
            run,rs=runs_blank(row,by,sb)
            w.writerow([c,f,L,cls,run,round(rs,2),round(float(row.mean()),1),round(float(row[40:680].std()),1)])
            H[f][cls][min(run//16*16,256)]+=1
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
try: walk_tagged(cap,on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:80])
print('units',N[0])
for f in (1,2):
    for cls in ('pic','sw-1','sw','band'):
        h=H[f][cls]; tot=sum(h.values())
        print(f'field {f} {cls:5s} rows {tot:6d} | run>=64: {sum(v for k,v in h.items() if k>=64):6d} | run>=32: {sum(v for k,v in h.items() if k>=32):6d} | hist(16-bins)', dict(sorted(h.items())))
