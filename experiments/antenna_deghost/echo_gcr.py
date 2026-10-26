# fit the echo (delay, in-phase a, quadrature b) to the copy of the line's own blanking+sync (the left bands), pooled over fields
import numpy as np, sys
R=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0,R); sys.path.insert(0,S+'/an'); import echo_proto as E
START,BL,SYNC=E.START,E.BL,E.SYNC
fields=[int(v) for v in sys.argv[3].split(',')]
rows=[]
for g in fields:
    Y=E.retimed(g)[2:238,1::2].astype(np.float64); rows.append(E.hp(Y)[:,:150])
obs=np.median(np.concatenate(rows,0),0); P=80.0
fine=np.arange(-400,400,0.25)
def s_std(t): s=np.full(t.shape,P); s[(t>=START-147)&(t<START)]=BL; s[(t>=START-126)&(t<START-63)]=SYNC; return s
k=np.arange(-8,9); gk=0.9*np.exp(-0.9*k)/(1+np.exp(-0.9*k))**2; gk/=gk.sum()       # the edges' own steepness
sF=np.interp(fine,fine,np.convolve(s_std(fine),np.interp(np.arange(-32,33)/4,k,gk)/np.interp(np.arange(-32,33)/4,k,gk).sum(),'same'))
F=np.fft.rfft(sF-sF.mean()); F[1:]*=-1j; F[0]=0; hF=np.fft.irfft(F,n=len(sF))
t=np.arange(150).astype(float); sl=slice(8,140)
def hp1(v): return v-np.convolve(v,np.ones(61)/61,'same')
best=None
for tau in np.arange(60,140.25,0.25):
    X=np.stack([hp1(np.interp(t-tau,fine,sF)),hp1(np.interp(t-tau,fine,hF))],1)[sl]; y=obs[sl]
    ab,res,_,_=np.linalg.lstsq(X,y,rcond=None); r=y-X@ab; fitq=1-r.var()/y.var()
    if best is None or fitq>best[0]: best=(fitq,tau,ab)
fitq,tau,ab=best
print('pooled over %d fields: best delay %.2f samples (%.2f us); in-phase a %+.3f, quadrature b %+.3f; strength %.3f, phase %.0f deg; explains %.0f%% of the band pattern'%(len(fields),tau,tau/13.5,ab[0],ab[1],np.hypot(*ab),np.degrees(np.arctan2(ab[1],ab[0])),100*fitq))
np.save(S+'/an/echo_gcr.npy',np.r_[tau,ab]); np.save(S+'/an/echo_gcr_obs.npy',obs)
