#!/usr/bin/env python3
"""switch_geometry.py output -> the field_pair_review.py reference columns (contract v3): per field, picture top = top;
picture bottom = the expected bottom top + 239 clipped at the last recorded row (the picture's own geometry, not the
switch); head-switch marker = S, the first row belonging to the other head (the band runs from S to the clip).
Usage: sg_to_render_csv.py <sg.csv> <out.csv> <counters.csv> [--body-correct <bodyshift.csv>]
--body-correct: contract v3 §10.5 — when exactly one field's body moved decisively (ratio <= 0.8) against the previous
unit and the measured top did not move by that amount, the field shifted under a clamped top: carry the difference as
an offset on that field's applied top (bounded to ±3, reset when the top itself moves by the body's amount); the comb
is the confirmation this rule still needs   (counters: a CSV with unit|ordinal and counter columns for the same capture; the renderer joins by the 16-bit device counter)"""
import sys, csv
import argparse
ap=argparse.ArgumentParser(); ap.add_argument('sg'); ap.add_argument('out'); ap.add_argument('counters'); ap.add_argument('--body-correct'); ap.add_argument('--repair-slots',action='store_true',help='the engine ran with --repair (fields paired one later): render slot 1 of unit u from engine field 2 of unit u-1, slot 2 from engine field 1 of unit u'); A=ap.parse_args(); sys.argv=[sys.argv[0],A.sg,A.out,A.counters]
rows=list(csv.DictReader(open(sys.argv[1]))); by={}
BS={int(r['unit']):r for r in csv.DictReader(open(A.body_correct))} if A.body_correct else {}
off={'1':0,'2':0}; prev_top={'1':None,'2':None}; corrected=0
cnt={}
for c in csv.DictReader(open(sys.argv[3])):
    k=int(c.get('unit',c.get('ordinal'))); cnt.setdefault(k,int(c['counter']))
for r in rows: by.setdefault(int(r['unit']),{})[r['field']]=r
w=csv.writer(open(sys.argv[2],'w',newline='')); w.writerow(['ordinal','counter','f1_picture_top_line','f1_bottom_line','f1_hs_bottom_line','f1_S','f2_picture_top_line','f2_bottom_line','f2_hs_bottom_line','f2_S'])
for u in sorted(by):
    if u not in cnt: continue
    out=[u,cnt[u]]
    for f in ('1','2'):
        r=(by.get(u-1,{}).get('2') if f=='1' else by[u].get('1')) if A.repair_slots else by[u].get(f); top=int(r['top']) if r else -1; last=int(r['last_rec']) if r else -1; S=int(r['S_first_shifted']) if r else -1
        if BS and u in BS and top>0:
            b=BS[u]; o='2' if f=='1' else '1'
            def dec(k): return b[f'f{k}_shift']!='' and float(b[f'f{k}_ratio'])<=0.8 and int(b[f'f{k}_shift'])!=0
            s_this=int(b[f'f{f}_shift']) if dec(f) else 0; s_other=int(b[f'f{o}_shift']) if dec(o) else 0
            dtop=(top-prev_top[f]) if prev_top[f] is not None else 0
            if s_this and not s_other and dtop!=s_this: off[f]=max(-3,min(3,off[f]+s_this-dtop)); corrected+=1
            elif dtop!=0 and dtop==s_this: off[f]=0
        prev_top[f]=top
        atop=top+off[f] if top>0 else top
        bottom=min(atop+239,last) if (atop>0 and last>0) else -1
        out+=[atop,bottom,S if S>0 else -1,S]
    w.writerow(out)
print('rows',len(by),'->',sys.argv[2],'| body corrections applied',corrected)
