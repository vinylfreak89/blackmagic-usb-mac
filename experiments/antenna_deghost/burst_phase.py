# per ghost: phase from the synthetic burst's copy (burst at its real offset off the window, 180 deg, VHS colour
# bandwidth), strength from brightness. Fit c_k = b g_k to each field's leaked band; check b_k = |c_k| / |g_luma,k|.
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, gclean as G_
F=np.load(S+'/an/rtall.npy',mmap_mode='r'); gh=np.load(S+'/an/ghosts_sharp.npy')
gl=[(T.real,l.real,a) for T,l,a,b in gh if T.real>=40]
env=np.concatenate([np.zeros(290),U.burst_env()])*U.B0                      # synthetic burst, off the window
X=[]
for T,lam,g in gl:
    k=U.ghost_kernel([(T,lam,1.0+0j)],200,2.0,False); X.append(np.convolve(np.concatenate([env,np.zeros(360)]),k)[400:460])
X=np.stack(X+[np.ones(60)],1)                                                 # 60 chroma samples = 120 luma at the left
Cs=[]; per=[]
for i in range(len(F)):
    C=G_.chroma(F[i][2:238]); m=C.mean(0)[:60]
    c=np.linalg.lstsq(X,m,rcond=None)[0][:-1]
    if np.abs(c).max()<0.3: continue                                          # colour killed: no burst
    per.append(c)
per=np.array(per); c=np.median(per.real,0)+1j*np.median(per.imag,0)
print('colour fields used: %d'%len(per))
for (T,lam,g),ck,col in zip(gl,c,per.T):
    sp=np.degrees(np.std(np.angle(col*np.conj(ck))))
    print('ghost %6.2f: burst copy %.3f at %+4.0f deg (field-to-field phase spread %.0f deg) -> ghost phase %+4.0f | brightness strength %.3f | implied burst level %.2f x standard'%(T,abs(ck),np.degrees(np.angle(ck)),sp,np.degrees(np.angle(ck/U.B0*abs(U.B0))),abs(g),abs(ck)/abs(g)))
np.save(S+'/an/burst_phase.npy',np.array([(T,lam,abs(g)*np.exp(1j*np.angle(ck*np.sign(U.B0.real))),abs(ck)/abs(g)) for (T,lam,g),ck in zip(gl,c)],dtype=complex))
