#!/usr/bin/env python3
"""switch_geometry.py output -> the field_pair_review.py reference columns (contract v3): per field, picture top = top;
picture bottom = the expected bottom top + 239 clipped at the last recorded row (the picture's own geometry, not the
switch); head-switch marker = S, the first row belonging to the other head (the band runs from S to the clip).
Usage: sg_to_render_csv.py <sg.csv> <out.csv> <counters.csv>   (counters: a CSV with unit|ordinal and counter columns for the same capture; the renderer joins by the 16-bit device counter)"""
import sys, csv
rows=list(csv.DictReader(open(sys.argv[1]))); by={}
cnt={}
for c in csv.DictReader(open(sys.argv[3])):
    k=int(c.get('unit',c.get('ordinal'))); cnt.setdefault(k,int(c['counter']))
for r in rows: by.setdefault(int(r['unit']),{})[r['field']]=r
w=csv.writer(open(sys.argv[2],'w',newline='')); w.writerow(['ordinal','counter','f1_picture_top_line','f1_bottom_line','f1_hs_bottom_line','f1_S','f2_picture_top_line','f2_bottom_line','f2_hs_bottom_line','f2_S'])
for u in sorted(by):
    if u not in cnt: continue
    out=[u,cnt[u]]
    for f in ('1','2'):
        r=by[u].get(f); top=int(r['top']) if r else -1; last=int(r['last_rec']) if r else -1; S=int(r['S_first_shifted']) if r else -1
        bottom=min(top+239,last) if (top>0 and last>0) else -1
        out+=[top,bottom,S if S>0 else -1,S]
    w.writerow(out)
print('rows',len(by),'->',sys.argv[2])
