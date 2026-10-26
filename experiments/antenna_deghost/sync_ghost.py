# fit the channel response from the line's own blanking/sync: median TBC-off line aligned on its true picture start,
# against the standard NTSC line around it (front porch, -40 IRE sync, back porch, picture), ridge-regularised
import numpy as np, csv, sys
S=sys.argv[1]; parity=int(sys.argv[2])
T=np.load(S+'/an/truth2.npy'); d=(T[...,0]+T[...,2])/2; good=(T[...,1]>0.7)&(T[...,3]>0.7)
med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0])); B=np.load(S+'/rp/B.npy',mmap_mode='r'); START=4.4
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r]); NB=len(T)
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)])
TT=np.arange(-40,251)                                   # time from the true picture start, samples
rows=[]
for g in np.nonzero(locked)[0]:
    if g%2!=parity: continue
    Y=B[g].astype(np.float32)
    for i in np.nonzero(good[g])[0]:
        s0=START-(d[g,i]-med); x=s0+TT; v=np.full(len(TT),np.nan); ok=(x>=3)&(x<=716)
        v[ok]=np.interp(x[ok],np.arange(720),Y[i+4]); rows.append(v)
Rm=np.array(rows); y=np.nanmedian(Rm,0); n=(~np.isnan(Rm)).sum(0)
P=np.median(y[TT>=150]); BL=1.5; SYNC=BL-40*2.19
def std_line(t):                                      # standard waveform (codes) at time t from picture start
    s=np.full(t.shape,P); s[(t>=-146)&(t<0)]=BL; s[(t>=-126)&(t<-63)]=SYNC; return s
# bandlimit like the edges we measured (logistic slope 0.9)
k=np.arange(-8,9); g_=0.9*np.exp(-0.9*k)/(1+np.exp(-0.9*k))**2; g_/=g_.sum()
TAU=np.arange(-20,281)
fine=np.arange(-40-300,251+30)
sf=np.convolve(std_line(fine.astype(float)),g_,'same')
X=np.array([[np.interp(t-tau,fine,sf) for tau in TAU] for t in TT])
m=n>200; lam=float(sys.argv[3]) if len(sys.argv)>3 else 30.0
A=X[m]; b=y[m]; h=np.linalg.solve(A.T@A+lam*np.eye(len(TAU)),A.T@b)
np.savez(S+'/an/sync_ghost_p%d.npz'%parity,h=h,tau=TAU,y=y,TT=TT,fit=X@h,n=n,P=P)
print('parity %d: %d lines; picture level %.1f; fit rms %.2f codes over t=-40..250 (data std %.2f)'%(parity,len(rows),P,np.sqrt(np.nanmean((X[m]@h-b)**2)),np.nanstd(b-np.convolve(b,np.ones(41)/41,'same'))))
big=np.argsort(-np.abs(h*(TAU!=0)))[:12]
print('  largest response taps (delay: gain):',' '.join('%+d:%+.3f'%(TAU[j],h[j]) for j in sorted(big)), '| main tap h(0..2): %s'%np.round(h[20:23],3).tolist())
