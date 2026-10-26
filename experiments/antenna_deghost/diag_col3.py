exec(open('diag_gen.py').read())
import seq2
f=lambda v:' '.join('%.0f:%.3f∠%+.0f'%(T,abs(g),np.degrees(np.angle(g))) for T,g in zip(Ts,v))
Ly,Lc,Sh=build(gy_t); my,mc,_,_=R.masked_mean(Ly,Lc,Sh)
G1=np.ones(Y.NFFT,complex); G2=np.ones(X.NFFT,complex)
ac,gy,L=seq2.measure(my,mc,Ts,D,SIG,LAM,G1,G2,BL)
print('colour (B known)  ',f(ac/BL)); print('true              ',f([g[3] for g in gc_t]))
nf=Sh<=0; my,mc,_,_=R.masked_mean(Ly[nf],Lc[nf],Sh[nf]); ac,gy,L=seq2.measure(my,mc,Ts,D,SIG,LAM,G1,G2,BL)
print('no-fill lines only',f(ac/BL))
