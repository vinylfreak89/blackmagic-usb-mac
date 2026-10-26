# dispositive: is the pass wrong, or the measurement?  A = all ghosts; B = all but 74 (same pictures, no noise)
# pass(A, true 74) should equal B up to the cross terms g74*g_k at 74+T_k (all beyond 115)
exec(open('diag_gen.py').read())
import seq
def meas(Lyy,Lcc,Sh):
    my,mc,_,_=R.masked_mean(Lyy,Lcc,Sh); ac,gy,uc,uy,ex=R.fit_lin(mc,my,Ts,D,SIG,LAM)
    return [g if T>=80 else ex['dy'][i]/ex['L'] for i,(T,g) in enumerate(zip(Ts,gy))], my, ex['L']
f=lambda v:' '.join('%.0f:%.3f∠%+.0f'%(T,abs(g),np.degrees(np.angle(g))) for T,g in zip(Ts,v))
g74=gy_t[2][3]; rest=[g for g in gy_t if abs(g[0]-74.25)>0.1]
LA,LcA,ShA=build(gy_t); LB,LcB,ShB=build(rest)
mA,myA,LA_=meas(LA,LcA,ShA); mB,myB,LB_=meas(LB,LcB,ShB)
P=Y.PRE; F=seq.start_lines(LA,LcA,gy_t,[],D,BL)[0]; F1,_=seq.pass_full_y(F,74.25,SIG,LAM,g74); LP=F1[:,P:]
mP,myP,LP_=meas(LP,LcA,ShA)
print('A (all):          ',f(mA),' L %.2f'%LA_)
print('B (no 74), direct:',f(mB),' L %.2f'%LB_)
print('pass(A, true 74): ',f(mP),' L %.2f'%LP_)
d=myP-myB; print('pooled line pass(A)-B  rms over 0..150 %.3f  max %.3f at %d'%(np.sqrt(np.mean(d[:150]**2)),np.abs(d[:150]).max(),np.abs(d[:150]).argmax()))
print('per-line pass(A)-B rms (unmasked, 0..150) %.3f'%np.sqrt(np.mean((LP-LB)[:,:150]**2)))
np.savez('/tmp/x.npz') if False else None
for n in range(0,150,10): print(n, ' '.join('%6.2f'%v for v in d[n:n+10]))
