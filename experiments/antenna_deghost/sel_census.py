# which synthetic lines does the plain-start selection keep, with and without ghosts: object lines (real content in
# 0-200) versus plain ones, and how far each kept line's start (0-200) sits from its measured level L
import numpy as np, sys, io; sys.path.insert(0,'.'); sys.path.insert(0,'er')
import rf_sim as F, hretime as H, tuner_fit as TF, plain_fit as PF
S=sys.argv[1]; NFLD=int(sys.argv[2]); NST=int(sys.argv[3]); NOGHOST='noghost' in sys.argv[4:]; SM='smooth' in sys.argv[4:]; rng=np.random.default_rng(11)
TT=[73.0,95.0,108.0,137.0,165.0,203.0]; G0=np.array([0.10*np.exp(1j*np.radians(114)),0.20*np.exp(1j*np.radians(-20)),0.15*np.exp(1j*np.radians(30)),
      0.10*np.exp(1j*np.radians(-157)),0.10*np.exp(1j*np.radians(-94)),0.13*np.exp(1j*np.radians(-34))])
scale=rng.uniform(0.3,1.6,(NST,len(TT))); scale[rng.random((NST,len(TT)))<0.2]=0.0
drift=np.exp(1j*np.radians(rng.uniform(-15,15,(NST,len(TT))))); GT=G0[None]*scale*drift*(0 if NOGHOST else 1)
V=np.memmap(S+'/rp/c.uyvy',np.uint8,'r').reshape(-1,480,1440); k1=np.ones(15)/15
ks=rng.choice(2*V.shape[0],NFLD,replace=False); per=NFLD//NST; tot=[0,0]; kept=[0,0]; dev=[[],[]]; rows=[]
for s in range(NST):
    for k in ks[s*per:(s+1)*per]:
        rt=H.field(np.ascontiguousarray(V[k//2][k%2::2]),k,log=io.StringIO()); y=rt[:,1::2].astype(float); d=np.clip((y[:,4:]-1.5)/2.19,0,110)
        d=np.concatenate([d,np.repeat(d[:,-1:],4,1)],1); tex=d-np.apply_along_axis(lambda r: np.convolve(r,k1,'same'),1,d)
        p=np.zeros_like(d)
        for b0 in range(0,len(d),24): p[b0:b0+24]=rng.uniform(10,70)+0.5*tex[b0:b0+24]
        obj=rng.random(len(d))<0.3; p[obj,:200]=d[obj,:200]; p=np.clip(p,0,110)
        o=F.run(p,list(zip(TT,GT[s])),'sync',TF.DSYNC); w=o[:,F.ACT0-4:F.ACT0-4+712]*2.19+0.9; w=np.concatenate([w,np.repeat(w[:,-1:],8,1)],1)
        w=np.maximum(w+5.0*rng.normal(size=w.shape),TF.FLOOR)
        for i in (0,1): tot[i]+=int(np.sum(obj==bool(i)))
        for r,L in PF.select(w,np.zeros(len(w))):
            i=int(obj[r]); kept[i]+=1; dev[i].append(p[r,:200].mean()-p[r,220:360].mean()); rows.append((L,w[r,:TF.WIN].copy(),i,s))
print('%s: plain lines kept %d of %d, object lines kept %d of %d (%.0f%% of the selection)'%('no ghosts' if NOGHOST else 'ghosts',kept[0],tot[0],kept[1],tot[1],100*kept[1]/max(1,sum(kept))))
for i,nm in ((0,'plain'),(1,'object')):
    if dev[i]: a=np.array(dev[i]); print('  %-6s lines: picture mean over 0-200 minus 220-360 (IRE): mean %+.1f  median %+.1f  sd %.1f'%(nm,a.mean(),np.median(a),a.std()))

# rejection: within each level band, a line whose start (window 0-WIN) departs from the band's per-sample median
# profile by more than K robust sigma (MAD of that departure over the band's lines)
for K in (3.0,4.0,6.0):
    out=[[0,0],[0,0]]; bias=[]; sgs=[]
    for st,(a,b) in [(st,bb) for st in range(NST) for bb in PF.BANDS]:
        R=[x for x in rows if a<=x[0]<b and x[3]==st]
        if len(R)<40: continue
        Y=np.array([x[1] for x in R]); Ls=np.array([x[0] for x in R]); ob=np.array([x[2] for x in R])
        med=np.median(Y,0); D=Y-med; dv=D[:,:200].mean(1)-D[:,220:300].mean(1); c=np.median(dv); sg=1.4826*np.median(np.abs(dv-c)); keep=np.abs(dv-c)<=K*sg; sgs.append(sg)
        if SM:   # also structure with no net offset: RMS of the 15-sample-smoothed departure over 0-200, offset removed
            sm=np.apply_along_axis(lambda r: np.convolve(r,np.ones(15)/15,'valid'),1,D[:,:200]-D[:,220:300].mean(1)[:,None]); rv=np.sqrt(np.mean(sm**2,1))
            c2=np.median(rv); s2=1.4826*np.median(np.abs(rv-c2)); keep&=rv<=c2+K*s2
        for i in (0,1): out[i][0]+=int(np.sum(ob==i)); out[i][1]+=int(np.sum((ob==i)&~keep))
        bias.append(np.abs(Y[keep].mean(0)-Y[keep&(ob==0)].mean(0)).max() if (keep&(ob==1)).any() else 0.0)
    print('mean departure 0-200 minus 220-300, sigma median %.2f max %.2f codes, K=%.0f:'%(np.median(sgs),max(sgs),K)+' plain lines rejected %d of %d, object lines rejected %d of %d; kept-pool start profile vs plain-only, max |diff| %.2f codes'%(out[0][1],out[0][0],out[1][1],out[1][0],max(bias)))
