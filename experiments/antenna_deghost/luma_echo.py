# brightness echo: blurred copy (in-phase a, quadrature b) at delay tau; the unseen stretch before the picture is the
# standard blanking with the -40 IRE sync; left-to-right recursion with a kernel that only reaches cleaned samples
import numpy as np
START=4.4; BL=1.5; SYNC=BL-40*2.19
def kernel(a,b,sig,L=40):
    k=np.arange(-L,L+1).astype(float); w=np.exp(-0.5*(k/sig)**2); w/=w.sum()
    hk=np.zeros_like(k); nz=k!=0; hk[nz]=(1-np.cos(np.pi*k[nz]))/(np.pi*k[nz])      # discrete Hilbert kernel
    return a*w+b*np.convolve(w,hk,'same'), k
def hidden(t):
    s=np.full(t.shape,BL); s[(t>=START-147)&(t<START-84)]=SYNC; return s
def cancel(Y,a,b,sig,tau):
    K,k=kernel(a,b,sig); n=Y.shape[1]; P=int(tau)+60
    ext=np.concatenate([np.tile(hidden(np.arange(-P,0).astype(float)),(len(Y),1)),Y.astype(np.float64)],1)
    out=ext.copy()
    for x in range(int(np.ceil(START)),n):
        pos=P+x-tau-k; i0=np.floor(pos).astype(int); fr=pos-i0
        src=out[:,i0]*(1-fr)+out[:,i0+1]*fr
        out[:,P+x]=ext[:,P+x]-src@K
    return out[:,P:]
