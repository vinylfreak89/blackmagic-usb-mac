# per-field echo cancellation prototype, on retimed fields (hretime.field on the TBC-off pass)
import numpy as np, sys
R=sys.argv[1]; sys.path.insert(0,R); import hretime as H
S=sys.argv[2]; V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440)
START=4.4; BL=1.5; SYNC=BL-40*2.19; TAUS=np.arange(85,126)
def retimed(g): return H.field(np.ascontiguousarray(V[g//2][g%2::2]),g)
def hp(a,w=61): return a-np.apply_along_axis(lambda r:np.convolve(r,np.ones(w)/w,'same'),1,a)
def fit_luma(Y):
    """IV regression: detail(x) on detail(x - tau), tau 85..125, instruments = the rows above and below (their noise is independent)"""
    D=hp(Y); Z=(np.roll(D,1,0)+np.roll(D,-1,0))/2; xs=np.arange(265,705); rows=np.arange(2,len(Y)-2)
    yv=D[np.ix_(rows,xs)].ravel(); X=np.stack([D[np.ix_(rows,xs-t)].ravel() for t in TAUS],1); Zi=np.stack([Z[np.ix_(rows,xs-t)].ravel() for t in TAUS],1)
    return np.linalg.solve(Zi.T@X+1e-3*np.eye(len(TAUS))*np.trace(Zi.T@X)/len(TAUS),Zi.T@yv)
def guess_hidden(t):
    """the unseen part before the picture (retimed: picture starts at START): blanking, with the -40 IRE sync"""
    s=np.full(t.shape,BL); s[(t>=START-126)&(t<START-63)]=SYNC; return s
def cancel_luma(Y,h):
    n=Y.shape[1]; hid=guess_hidden(np.arange(-TAUS[-1],0)).astype(np.float32)
    out=np.concatenate([np.tile(hid,(len(Y),1)),Y.astype(np.float32)],1); off=TAUS[-1]
    for x in range(n):
        src=out[:,off+x-TAUS]                          # already-cleaned samples tau earlier (or the guessed blanking)
        out[:,off+x]=out[:,off+x]-src@h
    return out[:,off:]
if __name__=='__main__':
    g=int(sys.argv[3]); f=retimed(g); Y=f[2:238,1::2].astype(np.float32)
    h=fit_luma(Y); np.save(S+'/an/h_luma_%d.npy'%g,h)
    print('field %d: echo kernel, largest taps:'%g,' '.join('%d:%+.3f'%(t,v) for t,v in sorted(zip(TAUS,h),key=lambda p:-abs(p[1]))[:8]),'| sum %.3f'%h.sum())
    # out-of-sample check: the left bands (samples 5-140) predicted from the guessed blanking alone vs observed
    pred=np.zeros(140); t=np.arange(140)
    for k,tau in enumerate(TAUS): pred+=h[k]*(guess_hidden((t-tau).astype(float))-BL)
    obs=np.median(hp(Y)[:,:140],0)
    sl=slice(8,135); pr=pred-np.convolve(pred,np.ones(61)/61,'same')
    print('left bands: observed vs predicted from blanking+sync only: r = %.3f; observed swing %.1f, predicted %.1f codes'%(np.corrcoef(obs[sl],pr[sl])[0,1],obs[sl].std(),pr[sl].std()))
    np.savez(S+'/an/bands_%d.npz'%g,obs=obs,pred=pr)
