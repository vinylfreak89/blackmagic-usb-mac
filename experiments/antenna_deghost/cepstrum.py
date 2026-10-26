"""Copies measured from the averaged log spectrum of many lines. Every line carries the same copies, so their spectral
ripple adds identically; picture content averages to a smooth spectrum (low quefrency only). A line's own gain (AGC)
is an additive constant in the log spectrum: it moves only quefrency 0. Rows near the recorder's head switch (and the
band below it) and rows with clipped samples are left out. The copies' response (1+H) is rebuilt minimum-phase from
the ghost quefrencies."""
import numpy as np, sys; S=sys.argv[1]; nblocks=int(sys.argv[2])
sys.path.insert(0,S+'/an'); import gclean as G
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); idx=np.load(S+'/an/rtall_idx.npy')
SW_STREAK=(25.0,0.5)
def switch_rows(Y):
    up=Y[1:-1]-Y[:-2]; dn=Y[1:-1]-Y[2:]; frac=((up>SW_STREAK[0])&(dn>SW_STREAK[0]))[:,20:700].mean(1)
    bad=np.zeros(len(Y),bool)
    for i in np.nonzero(frac>=SW_STREAK[1])[0]+1: bad[max(0,i-4):i+16]=True
    return bad
NY,NC=2048,1024; ys,cs=slice(130,712),slice(65,356)
wy=np.hanning(ys.stop-ys.start); wc=np.hanning(cs.stop-cs.start)
blocks=np.array_split(np.arange(len(F)),nblocks); res=[]
for bi,blk in enumerate(blocks):
    My=np.zeros(NY); Mc=np.zeros(NC); n=0; dropped=[0,0]
    for i in blk:
        f=F[i][2:238]; Y=f[:,1::2].astype(float); C=G.chroma(f)
        bad=switch_rows(Y); clip=((Y[:,10:700]>=250)|(Y[:,10:700]<=1)).mean(1)>0.002
        dropped[0]+=bad.sum(); dropped[1]+=(clip&~bad).sum()
        ok=~bad&~clip
        if not ok.any(): continue
        yl=(Y[ok][:,ys]-Y[ok][:,ys].mean(1,keepdims=True))*wy; cl=(C[ok][:,cs]-C[ok][:,cs].mean(1,keepdims=True))*wc
        My+=np.log(np.abs(np.fft.fft(yl,NY,axis=1))**2+1e-3).sum(0); Mc+=np.log(np.abs(np.fft.fft(cl,NC,axis=1))**2+1e-3).sum(0); n+=ok.sum()
    cy=np.fft.ifft(My/n)/2; cc=np.fft.ifft(Mc/n)/2
    res.append((cy,cc)); print('block %d: fields %d-%d, %d lines used, %d near the switch, %d clipped'%(bi,idx[blk[0]],idx[blk[-1]],n,dropped[0],dropped[1]),flush=True)
np.save(S+'/an/cepstra.npy',np.array([[a for a in r] for r in res],dtype=object),allow_pickle=True)
def minphase(c,N,q0,q1):
    k=np.zeros(N,complex); q=np.arange(N); pos=(q>=q0)&(q<=q1)
    k[pos]=c[pos]+np.conj(c[(-q[pos])%N])
    return np.fft.ifft(np.exp(np.fft.fft(k)))
cyall=np.mean([r[0] for r in res],0); ccall=np.mean([r[1] for r in res],0)
for name,c,N,q0,q1,scale in (('brightness',cyall,NY,16,260,1),('colour',ccall,NC,10,130,2)):
    h=minphase(c,N,q0,q1); h[0]-=1; mag=np.abs(h[:q1+40])
    pk=[q for q in range(q0,q1+30) if mag[q]>mag[q-1] and mag[q]>=mag[q+1] and mag[q]>0.02]
    print(name,'copies (delay in luma samples: strength∠phase):',' '.join('%d:%.3f∠%+.0f'%(q*scale,mag[q],np.degrees(np.angle(h[q]))) for q in sorted(pk,key=lambda q:-mag[q])[:12]))
    print('   total over delays: %.3f∠%+.0f   sum|h| %.3f'%(abs(h[q0:q1+30].sum()),np.degrees(np.angle(h[q0:q1+30].sum())),mag[q0:q1+30].sum()))
    np.save(S+'/an/cep_h_%s.npy'%('y' if scale==1 else 'c'),h)
# drift: the strongest colour copy, block by block
for bi,(cy,cc) in enumerate(res):
    h=minphase(cc,NC,10,130); h[0]-=1; m=np.abs(h[10:130]); q=np.argmax(m)+10
    hy=minphase(cy,NY,16,260); hy[0]-=1; my=np.abs(hy[16:260]); qy=np.argmax(my)+16
    print('block %d: colour strongest %d:%.3f∠%+.0f  brightness strongest %d:%.3f∠%+.0f'%(bi,2*q,abs(h[q]),np.degrees(np.angle(h[q])),qy,abs(hy[qy]),np.degrees(np.angle(hy[qy]))))
