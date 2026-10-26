# strengths fixed from brightness; one burst level b and one phase per ghost, fitted so the synthetic burst's copies
# reproduce the clip-averaged leak (fields normalised by their own level). Coordinate descent on phases and b.
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
gh=np.load(S+'/an/ghosts_sharp.npy'); gl=[(T.real,l.real,abs(a)) for T,l,a,b in gh if T.real>=40]
env=np.concatenate([np.zeros(290),U.burst_env()])*U.B0; X=[]
for T,lam,g in gl:
    k=U.ghost_kernel([(T,lam,1.0+0j)],200,2.0,False); X.append(np.convolve(np.concatenate([env,np.zeros(360)]),k)[400:460])
X=np.stack(X,1); ref=np.load(S+'/an/band_avg.npy')[:60]; mags=np.array([g for _,_,g in gl])
phi=np.full(len(gl),np.radians(140.0)); b=1.0
def model(phi,b): return X@(b*mags*np.exp(1j*phi))
for it in range(200):
    for k in range(len(gl)):
        rest=ref-model(phi,b)+X[:,k]*b*mags[k]*np.exp(1j*phi[k]); cst=0
        Xk=X[:,k]*b*mags[k]; p=np.vdot(Xk,rest-np.mean(rest-Xk*np.exp(1j*phi[k]))); phi[k]=np.angle(p)
    M=X@(mags*np.exp(1j*phi)); r_=ref-ref.mean(); M_=M-M.mean(); b=max(0.05,np.real(np.vdot(M_,r_))/np.real(np.vdot(M_,M_)))
res=ref-model(phi,b); res=res-res.mean()
print('burst level %.2f x standard; leak explained %.3f'%(b,1-np.linalg.norm(res)**2/np.linalg.norm(ref-ref.mean())**2))
for (T,lam,g),p in zip(gl,phi): print('  ghost %6.2f: strength %.3f (brightness), phase %+4.0f (burst)'%(T,g,np.degrees(p)))
np.save(S+'/an/colour_ghosts_bp.npy',np.array([(T,lam,g*np.exp(1j*p)) for (T,lam,g),p in zip(gl,phi)],dtype=complex)); np.save(S+'/an/colour_ghosts_bp_b.npy',np.array([b]))
