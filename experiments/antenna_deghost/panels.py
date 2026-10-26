# panels.py S out.png field... : per field, luma panels: raw | committed | s0 | s0.15 | key-corrected | TBC-on reference
import numpy as np, sys, csv
from PIL import Image, ImageDraw
S, out = sys.argv[1:3]; G=[int(x) for x in sys.argv[3:]]
T=np.load(S+'/an/truth2.npy'); d=(T[...,0]+T[...,2])/2; med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440); A=np.load(S+'/rp/A.npy',mmap_mode='r')
def load(n):
    C={}
    for x in csv.DictReader(open(S+'/an/hj_%s.csv'%n)):
        g=int(x['field'])
        if g in G: C.setdefault(g,{})[int(x['line'])]=float(x['correction'])
    return C
runs=[('committed',load('0')),('s0',load('s0')),('s0.15',load('s0.15'))]
def sh(y,c):
    x=np.arange(720)-c; i0=np.floor(x).astype(int); f=x-i0; ok=(i0>=0)&(i0<719); o=np.full(720,16.0); o[ok]=y[i0[ok]]*(1-f[ok])+y[i0[ok]+1]*f[ok]; return o
L=np.arange(24,257); tiles=[]
for g in G:
    Y=V[g//2][g%2::2][:,1::2].astype(np.float32); raw=Y[L-20]
    pan=[('raw',raw)]+[(n,np.array([sh(Y[l-20],C[g][l]) for l in L])) for n,C in runs]
    pan.append(('key',np.array([sh(Y[l-20],d[g,l-24]-med) for l in L])))
    # TBC-on field that matched best, lines 24..256, shifted by -med? reference shown as is
    best=None
    for ga in range(g+33,g+40):
        if ga<A.shape[0]:
            q=np.corrcoef(A[ga][L-22][:,200:520:4].ravel().astype(float),raw[:,200:520:4].ravel())[0,1]
            if best is None or q>best[0]: best=(q,ga)
    pan.append(('TBC-on %d'%best[1],A[best[1]][L-22].astype(np.float32)))
    row=np.concatenate([np.concatenate([np.repeat(p,2,0),np.full((466,6),255)],1) for _,p in pan],1)
    im=Image.fromarray(np.clip(row,0,255).astype(np.uint8)).convert('RGB'); dr=ImageDraw.Draw(im)
    for k,(n,_) in enumerate(pan): dr.rectangle([k*726+4,4,k*726+150,22],fill=(0,0,0)); dr.text((k*726+8,7),'field %d %s'%(g,n),fill=(255,255,0))
    tiles.append(np.array(im))
Image.fromarray(np.concatenate(tiles,0)).save(out); print(out)
