import numpy as np, sys, csv
S=sys.argv[1]; LAG=int(np.load(S+'/an/ab_lag.npy')[0])
def vlines(p): return [r for r in csv.reader(open(p)) if r[0]=='V']
def a0(p): return next(int(r[2]) for r in csv.reader(open(p)) if r[0]=='A')
VA=vlines(S+'/rp/a.timing.csv'); VB=vlines(S+'/rp/b.timing.csv'); A0a=a0(S+'/rp/a.timing.csv'); A0b=a0(S+'/rp/b.timing.csv')
pa=np.array([int(r[8]) for r in VA]); pb=np.array([int(r[8]) for r in VB])
A=np.fromfile(S+'/rp/a_stab.uyvy',np.uint8).reshape(-1,480,1440); B=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
NA,NB=A.shape[0]*2,B.shape[0]*2
L=np.arange(40,250,2)
def rowsA(g): return A[g//2][g%2::2][L-22,1::2].astype(np.float32)
def rowsB(g): return B[g//2][g%2::2][L-20,1::2].astype(np.float32)
def ncc_rows(x,y,W=40):
    """per row: best normalised correlation of y against x over shifts -W..W (edges), and the shift"""
    x=np.diff(x[:,60:700],axis=1); y=np.diff(y[:,60:700],axis=1)
    x-=x.mean(1,keepdims=True); y-=y.mean(1,keepdims=True)
    F=np.fft.rfft(x,n=1280,axis=1); G=np.fft.rfft(y,n=1280,axis=1)
    cc=np.fft.irfft(F*np.conj(G),n=1280,axis=1); cc=np.concatenate([cc[:,-W:],cc[:,:W+1]],1)
    nr=np.sqrt((x*x).sum(1)*(y*y).sum(1))+1e-6; k=cc.argmax(1)
    return cc[np.arange(len(k)),k]/nr, k-W
out=[]
for gb in range(NB):
    fb=gb//2; sb=(pb[fb]-A0b)/5 + (gb%2)*800.8           # this field's sound sample in B
    pts_a=A0a+5*(sb+LAG); fa=int(np.argmin(np.abs(pa-pts_a)))
    y=rowsB(gb); best=None
    for ga in range(2*fa-3, 2*fa+5):
        if not 0<=ga<NA: continue
        x=rowsA(ga); v=(x.std(1)>2)&(y.std(1)>2)
        if v.sum()<40: continue
        c,_=ncc_rows(x[v],y[v]); s=float(np.median(c))
        if best is None or s>best[0]: best=(s,ga)
    out.append((gb, best[1] if best else -1, best[0] if best else 0, 2*fa))
O=np.array(out); np.save(S+'/an/ab_map.npy',O)
d=O[:,1]-O[:,3]
print('match quality (median row correlation): p10 %.2f p50 %.2f p90 %.2f'%tuple(np.percentile(O[:,2],[10,50,90])))
print('chosen A field minus the sound-clock prediction:', dict(zip(*np.unique(d,return_counts=True))))
print('A field - B field along the clip:', ' '.join('%d:%+d'%(g,O[g,1]-g) for g in range(0,NB,120)))
