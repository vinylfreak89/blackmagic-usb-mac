# colour ghost set: per chroma delay, the colour-transition copy (strength and phase, colour fields, tone cancelled),
# luma delays 40..130, divided by the colour transition's own width; one overall factor fitted to the clip's burst leak
import numpy as np, sys; S=sys.argv[1]; sys.path.insert(0,S+'/an'); import unwind as U
D,r=np.load(S+'/an/chroma_strength2.npy'); D=D.real.astype(int)
W=1+2*np.abs(r[:8]).sum(); print('colour transition width: %.1f chroma samples'%W)
dcs=np.arange(20,66); base=np.array([r[dc-1] for dc in dcs])/W                    # r index: chroma delay dc -> D=dc
ref=np.load(S+'/an/band_avg.npy'); n=len(ref); big=np.concatenate([U.B0*U.burst_env(),np.zeros(n)])
K=sum(b*np.roll(big,dc)[U.PRE:] for dc,b in zip(dcs,base))
w=slice(0,75); X=np.stack([K[w],np.ones(75)],1); sol=np.linalg.lstsq(X,ref[w],rcond=None)[0]
s=sol[0]; print('overall factor %.3f∠%+.0f (a real factor means the phases agree); leak explained %.3f'%(abs(s),np.degrees(np.angle(s)),1-np.linalg.norm(ref[w]-X@sol)**2/np.linalg.norm(ref[w])**2))
for name,G in (('as measured (factor 1)',base),('scaled to the leak',abs(s)*base)):
    tot=G.sum(); c=np.zeros(1024,complex); c[0]=1; c[dcs]=G; P=np.abs(np.fft.fft(c)); rts=np.roots(c[:dcs.max()+1])
    print('%-24s sum|g| %.3f, coherent total %.3f∠%+.0f, min|P| %.3f, zeros outside %d'%(name,np.abs(G).sum(),abs(tot),np.degrees(np.angle(tot)),P.min(),(abs(rts)>=1).sum()))
np.save(S+'/an/colour_set2.npy',np.stack([dcs.astype(complex),abs(s)*base]))
