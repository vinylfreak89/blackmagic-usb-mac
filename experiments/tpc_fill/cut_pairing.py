# Where a hard cut lands in each field slot, from a sidecar's per-field motion error: same unit in both slots = fields paired as the
# source frames; slot 2 one unit before slot 1 = paired one field apart.
import csv, sys, numpy as np
csv.field_size_limit(1<<30)
hdr=None; e1=[]; e2=[]; ok=[]
with open(sys.argv[1],newline='') as f:
    for line in f:
        if line.startswith('#'): continue
        if hdr is None: hdr=next(csv.reader([line])); i1=hdr.index('motion_error_f1'); i2=hdr.index('motion_error_f2'); idr=hdr.index('drop_reason'); continue
        r=line.rstrip('\n').split(',')
        good=len(r)>i2 and r[idr]=='None' and r[i1]!='' and r[i2]!=''
        e1.append(float(r[i1]) if good else np.nan); e2.append(float(r[i2]) if good else np.nan); ok.append(good)
e1=np.array(e1); e2=np.array(e2); n=len(e1)
med=lambda x,i: np.nanmedian(x[max(0,i-30):i])
same=[]; s2first=[]; s1first=[]; other=0
i=40
while i<n-3:
    w=slice(i-3,i+3)
    if not np.isfinite(e1[i-35:i+4]).all() or not np.isfinite(e2[i-35:i+4]).all(): i+=1; continue
    b1=med(e1,i-1); b2=med(e2,i-1)
    sp1=e1[i]>6*b1+8; sp2=e2[i]>6*b2+8
    quiet=lambda x,b,j: x[j]<3*b+3
    if sp2 and sp1 and quiet(e1,b1,i-1) and quiet(e2,b2,i-1) and quiet(e1,b1,i+1) and quiet(e2,b2,i+1): same.append(i); i+=8; continue
    if sp2 and not sp1 and e1[i+1]>6*b1+8 and quiet(e2,b2,i+1) and quiet(e1,b1,i-1) and quiet(e2,b2,i-1): s2first.append(i); i+=8; continue
    if sp1 and not sp2 and e2[i+1]>6*b2+8 and quiet(e1,b1,i+1) and quiet(e1,b1,i-1) and quiet(e2,b2,i-1): s1first.append(i); i+=8; continue
    i+=1
m=lambda i: '%d:%02d'%(i/29.97//60,i/29.97%60)
print(sys.argv[1].split('/')[-1],'rows',n)
print('  isolated cuts landing in both slots in the same unit: %d | slot 2 one unit before slot 1: %d | slot 1 one unit before slot 2: %d'%(len(same),len(s2first),len(s1first)))
for lo in range(0,n,int(29.97*600)):
    hi=lo+int(29.97*600); print('  %s-%s: same %d, slot 2 first %d, slot 1 first %d'%(m(lo),m(min(hi,n)),sum(lo<=x<hi for x in same),sum(lo<=x<hi for x in s2first),sum(lo<=x<hi for x in s1first)))
