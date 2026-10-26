import numpy as np, sys, importlib.util
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from PIL import Image
S=sys.argv[2]; f=int(sys.argv[3]); r0,r1=[int(v) for v in sys.argv[4].split(',')]; sys.argv=[sys.argv[0],sys.argv[1],S,'0']
spec=importlib.util.spec_from_file_location('er',S+'/an/er/echo_render.py'); er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
gh=np.load(S+'/an/ghosts_sharp.npy'); gc=[(T.real,l.real,b) for T,l,a,b in gh if T.real>=40]; kc=U.ghost_kernel(gc,200,2.0,False)
env=np.concatenate([np.zeros(290),U.burst_env()]); leak1=np.convolve(np.concatenate([env,np.zeros(360)])*U.B0,np.concatenate([[0],kc[1:]]))[400:760]
rt=er.H.field(np.ascontiguousarray(er.V[f//2][f%2::2]),f); C=U.tone_cancel(G_.chroma(rt[2:238]))
old=U.colour_inverse_exact(C,gc,U.burst_level_exact(C,gc)*U.B0,0.0)
kk=leak1[:55]-leak1[:55].mean(); M=C[:,:55]-C[:,:55].mean(1,keepdims=True); a=np.convolve((M@np.conj(kk))/np.real(np.vdot(kk,kk)),np.ones(3)/3,'same')
new=U.inverse_by_kernel(C,kc,(a[:,None]*(U.B0*env)[None]).astype(complex))
x=2*np.arange(360); fig,ax=plt.subplots(3,1,figsize=(14,8),sharex=True)
for a_,X,t in ((ax[0],C,'input'),(ax[1],old,'remover used in the render'),(ax[2],new,'one-sided remover, burst per line')):
    m=X[r0:r1].mean(0); a_.plot(x,m.real,'b',lw=1,label='U'); a_.plot(x,m.imag,'r',lw=1,label='V'); a_.set_title('%s: field %d rows %d-%d averaged'%(t,f,r0,r1)); a_.grid(alpha=.3); a_.set_xticks(range(0,720,40))
ax[0].legend(); plt.tight_layout(); plt.savefig(S+'/an/sky_profile.png',dpi=70)
def rgbc(Z):
    u=np.repeat(Z.real,2,1); v=np.repeat(Z.imag,2,1); Y=np.full(u.shape,128.0)
    return np.clip(np.stack([Y+1.4*v,Y-0.34*u-0.71*v,Y+1.77*u],-1),0,255).astype(np.uint8)
im=np.concatenate([rgbc(Z)[r0:r1+40] for Z in (C,old,new)],0); Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*2),Image.NEAREST).save(S+'/an/sky_colour.png'); print('ok')
