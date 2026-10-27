# residual of the per-stretch tape fit in capture codes: where along the line it sits, against the noise of the mean
import numpy as np, sys, pickle; sys.path.insert(0,'.')
import plain_stretch as PS
S=sys.argv[1]; res,spans,stretches=pickle.load(open(S+'/plain_stretch_tape.pkl','rb'))
T,G,Q,m,ms=res['sync']; n=len(T)
segs=[(15,40),(40,80),(80,130),(130,180),(180,230),(230,300)]
print('stretch  group(level,se)  RMS resid codes in samples '+' '.join('%d-%d'%s for s in segs))
for (a,b,nl),q,gr in zip(spans,Q,stretches):
    g=q[0:2*n:2]+1j*q[1:2*n:2]; p0=q[2*n]; ng=len(gr); sig=np.abs(q[2*n+1:2*n+1+ng]); lev=q[2*n+1+ng:]
    out=PS.model(T,g,'sync',gr,p0,sig,lev)
    for o,(L,prof,se) in zip(out,gr):
        r=prof-o
        print('%5.1fs  L%4.0f se %.3f  '%(a/59.94,L,se)+' '.join('%6.2f'%np.sqrt(np.mean(r[x:y]**2)) for x,y in segs)+'   max %.2f at %d'%(np.abs(r[15:]).max(),15+np.abs(r[15:]).argmax()))
