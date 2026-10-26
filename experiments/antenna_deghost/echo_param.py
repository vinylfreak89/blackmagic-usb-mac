# 3-parameter echo: y = s + a*s(x-tau) + b*H{s}(x-tau); IV fit of (a,b) per delay, pooled over fields; scan tau
import numpy as np, sys
R=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0,R); sys.path.insert(0,S+'/an'); import echo_proto as E
def hilbert_rows(a):
    F=np.fft.rfft(a,axis=1); F[:,1:]*=-1j; F[:,0]=0; return np.fft.irfft(F,n=a.shape[1],axis=1)
def shift_rows(a,t):                      # a(x - t), fractional, linear; NaN where outside
    x=np.arange(a.shape[1])-t; i0=np.floor(x).astype(int); f=x-i0; ok=(i0>=0)&(i0<a.shape[1]-1)
    o=np.full(a.shape,np.nan); o[:,ok]=a[:,i0[ok]]*(1-f[ok])+a[:,i0[ok]+1]*f[ok]; return o
fields=[int(v) for v in sys.argv[3].split(',')]
data=[]
for g in fields:
    Y=E.retimed(g)[2:238,1::2].astype(np.float64); D=E.hp(Y); Hd=hilbert_rows(D); Z=(np.roll(D,1,0)+np.roll(D,-1,0))/2; Zh=hilbert_rows(Z)
    data.append((D,Hd,Z,Zh))
taus=np.arange(80,130.5,0.5); res=[]
for tau in taus:
    ZX=np.zeros((2,2)); Zy=np.zeros(2); yy=0; 
    for D,Hd,Z,Zh in data:
        X1=shift_rows(D,tau); X2=shift_rows(Hd,tau); I1=shift_rows(Z,tau); I2=shift_rows(Zh,tau)
        m=np.zeros(D.shape,bool); m[2:-2,265:705]=True; m&=~np.isnan(X1)
        X=np.stack([X1[m],X2[m]],1); I=np.stack([I1[m],I2[m]],1); y=D[m]
        ZX+=I.T@X; Zy+=I.T@y
    ab=np.linalg.solve(ZX,Zy); res.append(ab)
res=np.array(res); amp=np.hypot(res[:,0],res[:,1]); k=int(np.argmax(amp))
print('pooled over %d fields; echo strength sqrt(a^2+b^2) by delay:'%len(fields))
print('  '+' '.join('%.0f:%.3f'%(t,a) for t,a in zip(taus,amp) if t%2==0))
print('best delay %.1f samples (%.2f us): a %+.3f, b %+.3f, strength %.3f, phase %.0f deg'%(taus[k],taus[k]/13.5,res[k,0],res[k,1],amp[k],np.degrees(np.arctan2(res[k,1],res[k,0]))))
np.save(S+'/an/echo_param.npy',np.r_[taus[k],res[k]])
