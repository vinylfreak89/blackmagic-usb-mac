# the burst alone: colour averaged over all lines of many fields (picture averages out; the burst and anything made
# from it stays), before and after removal
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
F=np.load(S+'/an/rtall.npy',mmap_mode='r')
gh=np.load(S+'/an/ghosts_sharp.npy'); gc=[(T.real,l.real,b) for T,l,a,b in gh if T.real>=40]; kc=U.ghost_kernel(gc,200,2.0,False)
env=np.concatenate([np.zeros(290),U.burst_env()]); leak1=np.convolve(np.concatenate([env,np.zeros(360)])*U.B0,np.concatenate([[0],kc[1:]]))[400:760]
Min=np.zeros(360,complex); Mout=np.zeros(360,complex); Mout0=np.zeros(360,complex); nf=0
for i in range(0,len(F),3):
    C=G_.chroma(F[i][2:238]); m=C.mean(0)[:85]; kk=leak1[:85]-leak1[:85].mean(); mm=m-m.mean(); a=max(0.0,float(np.real(np.vdot(kk,mm))/np.real(np.vdot(kk,kk))))
    if a<0.3: continue
    Cc=U.inverse_by_kernel(C,kc,np.repeat((a*U.B0*env)[None],C.shape[0],0).astype(complex))
    C0=U.inverse_by_kernel(C,kc,np.zeros((C.shape[0],400),complex))
    Min+=C.mean(0)/a; Mout+=Cc.mean(0)/a; Mout0+=C0.mean(0)/a; nf+=1
Min/=nf; Mout/=nf; Mout0/=nf; x=2*np.arange(360)
fig,ax=plt.subplots(3,1,figsize=(14,8),sharex=True)
for a_,M,t in ((ax[0],Min,'input'),(ax[1],Mout,'after removal, burst off the edge'),(ax[2],Mout0,'after removal, no burst off the edge')):
    a_.plot(x,M.real,'b',lw=1,label='U'); a_.plot(x,M.imag,'r',lw=1,label='V'); a_.axhline(0,color='gray',lw=.5); a_.set_title(t+' (line average over %d colour fields)'%nf); a_.grid(alpha=.3); a_.set_xticks(range(0,720,40))
ax[0].legend(); ax[2].set_xlabel('luma sample'); plt.tight_layout(); plt.savefig(S+'/an/burst_echo.png',dpi=70)
for nm,M in (('input',Min),('after',Mout),('after, no burst',Mout0)):
    hp=M-np.convolve(M,np.ones(41)/41,'same'); print('%-16s detail (|U+jV| minus its 41-sample average) at 0-110: %.1f | 110-250: %.1f | 250-400: %.1f | 400-700: %.1f'%(nm,*[np.abs(hp[a//2:b//2]).mean() for a,b in ((0,110),(110,250),(250,400),(400,700))]))
