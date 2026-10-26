# per field, from the burst's copy: delay tau and complex echo g = copy / standard burst; then exact recursive cancellation of colour
import numpy as np, sys
R=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0,R); sys.path.insert(0,S+'/an'); import echo_proto as E
START=E.START; B0=-51.4+0j                             # standard burst (20 IRE on -U), decoded
BURST=(START-54.8, START-21.0)                         # burst span relative to the retimed picture start, luma samples
def chroma(f): return (f[:,0::4].astype(np.float64)-128)+1j*(f[:,2::4].astype(np.float64)-128)   # at luma x = 0,2,4..
def env(xl):                                           # burst envelope, smoothed by VHS colour bandwidth (~0.5 MHz)
    e=((xl>=BURST[0])&(xl<BURST[1])).astype(float); k=np.exp(-0.5*(np.arange(-30,31)/9.0)**2); k/=k.sum()
    return np.convolve(e,k,'same')
def fit_field(C):
    x=np.arange(360)*2.0; blob=np.median(C.real,0)+1j*np.median(C.imag,0)
    grid=np.arange(-300,720,1.0); best=None
    for tau in np.arange(60,140.5,0.5):
        m=np.interp(x-tau,grid,env(grid))*B0; sel=x<150
        g=np.vdot(m[sel],blob[sel])/np.vdot(m[sel],m[sel]); r=blob[sel]-g*m[sel]; q=1-np.sum(np.abs(r)**2)/np.sum(np.abs(blob[sel]-blob[sel].mean())**2)
        if best is None or q>best[0]: best=(q,tau,g)
    return best
def cancel(C,tau,g):
    """c_clean(x) = c(x) - g * c_clean(x - tau); before the picture: the standard burst in blanking"""
    x=np.arange(360)*2.0; grid=np.arange(-300,720,1.0); out=C.copy(); hidden=lambda t: np.interp(t,grid,env(grid))*B0
    for j in range(360):
        t=x[j]-tau
        if t<START: src=hidden(np.array([t]))[0]*np.ones(len(C))
        else:
            k=t/2.0; i0=int(np.floor(k)); fr=k-i0; src=out[:,i0]*(1-fr)+out[:,min(i0+1,359)]*fr
        out[:,j]=C[:,j]-g*src
    return out
if __name__=='__main__':
    for g_ in [int(v) for v in sys.argv[3].split(',')]:
        f=E.retimed(g_); C=chroma(f[2:238]); q,tau,g=fit_field(C)
        print('field %d: delay %.1f samples (%.2f us), echo %.3f at %+.0f deg relative to the burst; fit explains %.0f%% of the copy'%(g_,tau,tau/13.5,abs(g),np.degrees(np.angle(g)),100*q))
