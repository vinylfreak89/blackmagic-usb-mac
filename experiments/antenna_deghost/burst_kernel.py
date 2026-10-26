"""The copies' response read from the leaked burst. Per field, the row-median colour of the left band is
  m_f(t) = p_f(t) + b_f * sum_T h(T) env(t - T)
with env the standard burst envelope (known position, off the grid), b_f = -a_f (the burst sits at 180 deg; a_f > 0 is
that field's colour gain), h the copies (one set for the tape) and p_f the field's own picture, smooth (B-spline).
Alternating least squares over fields: h given a_f, then a_f given h. The product a_f*h is what the band fixes; h's
overall size is set later from the picture."""
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U, gclean as G
F=np.load(S+'/an/rtall.npy',mmap_mode='r')
T=np.arange(20,242,2.0); NT=len(T); tl=np.arange(0,320,2.0); n=len(tl)          # luma delays; band at chroma samples
env=U.burst_env(); ext=np.concatenate([env,np.zeros(400)])[None]
E=np.stack([U.shift(ext,d/2.0)[0,U.PRE:U.PRE+n] for d in T],1); E=np.nan_to_num(E)   # n x NT: burst copy at delay T
knots=np.arange(-120,440,80.0)
def bspline(x,k):                                                                 # cubic B-spline basis
    B=[]
    for i in range(len(k)-4):
        def b(x,i=i):
            out=np.zeros_like(x)
            for j in range(4):
                lo,hi=k[i+j],k[i+j+1]; u=(x-lo)/(hi-lo); m=(x>=lo)&(x<hi)
                c=[(u**3)/6,(-3*u**3+3*u**2+3*u+1)/6,(3*u**3-6*u**2+4)/6,((1-u)**3)/6][j]; out[m]=c[m]
            return out
        B.append(b(x))
    return np.stack(B,1)
P=bspline(tl,knots); P=P[:,P.sum(0)>1e-6]; NP=P.shape[1]
M=[]
for i in range(len(F)):
    C=G.chroma(F[i][2:238]); m=(np.median(C.real,0)+1j*np.median(C.imag,0))[:n]
    if np.abs(m[:60]).max()>8: M.append(m)                                         # fields with a visible leak (colour on)
M=np.array(M); NF=len(M); print('fields with a leak:',NF,flush=True)
# picture part projected out per field: residual-maker R = I - P(P'P)^-1 P'
R=np.eye(n)-P@np.linalg.pinv(P); ER=R@E
a=np.array([np.abs(m[10:60]).max() for m in M]); a/=a.mean()
D=np.diff(np.eye(NT),2,axis=0); lam=float(sys.argv[2]) if len(sys.argv)>2 else 3.0
for it in range(8):
    A=sum((a[f]**2)*(ER.conj().T@ER) for f in range(NF)); bb=sum(-a[f]*(ER.conj().T@(R@M[f])) for f in range(NF))
    h=np.linalg.solve(A+lam*NF*np.trace(ER.conj().T@ER).real/NT*D.T@D/100,bb)
    k=ER@h; a=np.array([max(1e-6,-np.real(np.vdot(k,R@M[f]))/np.real(np.vdot(k,k))) for f in range(NF)])
    res=sum(np.linalg.norm(R@M[f]+a[f]*k)**2 for f in range(NF))/sum(np.linalg.norm(R@M[f])**2 for f in range(NF))
    print('iter %d: unexplained %.3f of the band (after the picture part)'%(it,res),flush=True)
s=a.mean(); h=h*s; a=a/s                                                           # a ~ 1 on average
np.save(S+'/an/burst_kernel.npy',np.stack([T.astype(complex),h]))
print('field colour gain a_f: p5/50/95 %s'%np.round(np.percentile(a,[5,50,95]),2))
print('kernel (delay: b*h, the burst-referenced copy; burst taken as 1 at 180 deg):')
for d,x in zip(T,h):
    if d%4==0: print('%4d %6.2f∠%+4.0f %s'%(d,abs(x),np.degrees(np.angle(x)),'#'*int(abs(x)*3)))
