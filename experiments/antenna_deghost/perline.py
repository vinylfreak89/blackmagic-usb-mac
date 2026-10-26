# per-line leak: colour burst level+phase per line; brightness line-start pattern scale per line. Echo check per line:
# correlation between the (left-band) leftover of each line and the same line further right at the ghost delays
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); gh=np.load(S+'/an/ghosts_sharp.npy')
gy=[(T.real,l.real,a) for T,l,a,b in gh]; gc=[(T.real,l.real,b) for T,l,a,b in gh if T.real>=40]
ky=U.ghost_kernel(gy,400); kc=U.ghost_kernel(gc,200,2.0,False); Sx=np.load(S+'/an/line_start_pattern.npy')
env=np.concatenate([np.zeros(290),U.burst_env()]); leak1=np.convolve(np.concatenate([env,np.zeros(360)])*U.B0,np.concatenate([[0],kc[1:]]))[400:760]
def colour(C,mode):
    kk=leak1[:55]-leak1[:55].mean()
    if mode=='field':
        m=C.mean(0)[:55]; a=np.real(np.vdot(kk,m-m.mean()))/np.real(np.vdot(kk,kk)); a=np.full(C.shape[0],max(a,0)+0j)
    else:
        M=C[:,:55]-C[:,:55].mean(1,keepdims=True); a=(M@np.conj(kk))/np.real(np.vdot(kk,kk))
        a=np.convolve(a,np.ones(3)/3,'same')                           # lightly smoothed down the field
    pre=a[:,None]*(U.B0*env)[None]; return U.inverse_by_kernel(C,kc,pre.astype(complex))
def luma(Y,mode):
    Yb=Y-U.BL; s=np.ones(Y.shape[0])
    if mode=='line':
        t=slice(5,130); k=Sx[t]-Sx[t].mean(); M=Yb[:,t]-Yb[:,t].mean(1,keepdims=True); s=np.convolve((M@k)/(k@k),np.ones(3)/3,'same')
    P=s[:,None]*Sx[None]; return U.inverse_by_kernel(Yb-P,ky,np.zeros((Y.shape[0],400))).real+P+U.BL
def echo(X,band,lags,cplx):
    """per line: leftover of the band (minus the line's own smooth level) correlated with the line at +lag"""
    B=X[:,band]-X[:,band].mean(1,keepdims=True); tot=0
    for d in lags:
        Z=X[:,band.start+d:band.stop+d]; Z=Z-Z.mean(1,keepdims=True)
        tot+=np.abs(np.sum(Z*np.conj(B)))/np.sqrt(np.sum(np.abs(B)**2)*np.sum(np.abs(Z)**2))
    return tot/len(lags)
res={}
for i in range(0,len(F),4):
    f=F[i][2:238]; Y=f[:,1::2].astype(float); C=U.tone_cancel(G_.chroma(f))
    if U.field_leak_scale(C,leak1)<0.3: continue
    for nm,X,band,lags,cp in (('colour input',C,slice(2,55),[d//2 for d in (58,74,90,103,113)],1),('colour, per-field burst',colour(C,'field'),slice(2,55),[d//2 for d in (58,74,90,103,113)],1),('colour, per-line burst',colour(C,'line'),slice(2,55),[d//2 for d in (58,74,90,103,113)],1),
                              ('brightness input',Y,slice(5,110),[58,74,90,103,113],0),('brightness, one pattern',luma(Y,'clip'),slice(5,110),[58,74,90,103,113],0),('brightness, per-line pattern',luma(Y,'line'),slice(5,110),[58,74,90,103,113],0)):
        res.setdefault(nm,[]).append(echo(X,band,lags,cp))
for k,v in res.items(): print('%-30s line-start band vs the same line at the ghost delays: %.3f'%(k,np.mean(v)))
