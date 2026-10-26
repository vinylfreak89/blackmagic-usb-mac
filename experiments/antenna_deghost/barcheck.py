# straightness of a vertical feature: per line, dark-weighted centroid of luma in a column window; per version slope + scatter
import numpy as np, sys, csv
S=sys.argv[1]; g=int(sys.argv[2]); c0,c1=int(sys.argv[3]),int(sys.argv[4]); l0,l1=int(sys.argv[5]),int(sys.argv[6])
T=np.load(S+'/an/truth2.npy'); d=(T[...,0]+T[...,2])/2; med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440); A=np.load(S+'/rp/A.npy',mmap_mode='r')
def load(n):
    C={}
    for x in csv.DictReader(open(S+'/an/hj_%s.csv'%n)):
        if int(x['field'])==g: C[int(x['line'])]=float(x['correction'])
    return C
def sh(y,c):
    x=np.arange(720)-c; i0=np.floor(x).astype(int); f=x-i0; ok=(i0>=0)&(i0<719); o=np.full(720,np.nan); o[ok]=y[i0[ok]]*(1-f[ok])+y[i0[ok]+1]*f[ok]; return o
L=np.arange(l0,l1); Y=V[g//2][g%2::2][:,1::2].astype(np.float32)
ga=int(sys.argv[7]) if len(sys.argv)>7 else None
vers=[('raw',{l:0.0 for l in L})]+[(n,load(n)) for n in ('0','s0','s0.15')]+[('key',{l:d[g,l-24]-med for l in L})]
def centroid(row):
    w=row[c0:c1]; w=np.nanmax(w)-w; w=np.where(w>np.nanpercentile(w,60),w,0); x=np.arange(c0,c1); return (w*x).sum()/w.sum()
rows=[(n,np.array([centroid(sh(Y[l-20],C[l])) for l in L])) for n,C in vers]
if ga is not None: rows.append(('TBC-on %d'%ga,np.array([centroid(A[ga][l-22].astype(np.float32)) for l in L])))
for n,x in rows:
    p=np.polyfit(L,x,1); r=x-np.polyval(p,L)
    print('%-12s feature drifts %+6.1f samples over lines %d-%d | scatter about a straight line: %.2f | line-to-line jitter %.2f'%(n,p[0]*(l1-l0),l0,l1,np.median(np.abs(r)),np.median(np.abs(np.diff(x)))))
