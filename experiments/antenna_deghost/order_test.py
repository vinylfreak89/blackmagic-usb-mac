# synthetic colour line with known copies; remove them one pass per copy in different orders (each pass works on the
# current image, sources taken before modification), versus whole passes x = y - h*x_prev. Where does the residue sit?
import numpy as np
rng=np.random.default_rng(5); n=360
x=np.zeros(n,complex)
for _ in range(9):
    a,b=sorted(rng.integers(0,n,2)); x[a:b]+=rng.normal(0,30)+1j*rng.normal(0,30)
x=np.convolve(x,np.ones(5)/5,'same')
copies=[(30,0.15*np.exp(2j)),(50,0.5*np.exp(2.5j)),(58,0.3*np.exp(2.8j)),(68,0.12*np.exp(2.2j))]   # chroma-rate delays
def sh(v,d): out=np.zeros_like(v); out[d:]=v[:-d]; return out
y=x+sum(g*sh(x,d) for d,g in copies)
def residue_profile(e):
    """correlation of the residue with the true picture at each delay: where the leftover copies sit"""
    return {d:abs(np.vdot(sh(x,d)[150:],e[150:])/np.vdot(sh(x,d)[150:],sh(x,d)[150:])) for d in range(20,150,1)}
def report(name,est):
    e=est-x; p=residue_profile(e); top=sorted(p,key=lambda d:-p[d])[:5]
    print('%-34s error rms %5.2f (copies rms %.1f) | leftover copies at delay:strength %s'%(name,np.sqrt(np.mean(np.abs(e[40:])**2)),np.sqrt(np.mean(np.abs(y-x)[40:]**2)),' '.join('%d:%.2f'%(2*d,p[d]) for d in top)))
for name,order in (('strongest first',sorted(copies,key=lambda c:-abs(c[1]))),('latest first',sorted(copies,key=lambda c:-c[0])),('earliest first',sorted(copies,key=lambda c:c[0]))):
    cur=y.copy()
    for d,g in order: cur=cur-g*sh(cur,d)
    report('one pass per copy, '+name,cur)
for K in (1,2,3,5,8):
    est=y.copy()
    for _ in range(K): est=y-sum(g*sh(est,d) for d,g in copies)
    report('%d whole passes (source = previous estimate)'%K,est)
