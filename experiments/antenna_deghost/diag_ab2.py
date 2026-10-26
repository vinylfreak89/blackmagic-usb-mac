# (1) measure from lines with no left fill only (one fixed set of lines: copy of the pool = pool of the copies)
# (2) before a pass, a line's left fill is replaced by what was there: the ghosted reference plus the picture edge
exec(open('diag_gen.py').read())
import seq
cache='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad/ab_cache.npz'
g74=gy_t[2][3]; rest=[g for g in gy_t if abs(g[0]-74.25)>0.1]
if os.path.exists(cache):
    z=np.load(cache); LA,LB,LcA,Sh=z['LA'],z['LB'],z['LcA'],z['Sh']
else:
    LA,LcA,Sh=build(gy_t); LB,_,_=build(rest); np.savez(cache,LA=LA,LB=LB,LcA=LcA,Sh=Sh)
f=lambda v:' '.join('%.0f:%.3f∠%+.0f'%(T,abs(g),np.degrees(np.angle(g))) for T,g in zip(Ts,v))
def meas(Lyy,sel=None):
    if sel is None: sel=np.ones(len(Lyy),bool)
    my,mc,_,_=R.masked_mean(Lyy[sel],LcA[sel],Sh[sel]); ac,gy,uc,uy,ex=R.fit_lin(mc,my,Ts,D,SIG,LAM)
    return [g if T>=80 else ex['dy'][i]/ex['L'] for i,(T,g) in enumerate(zip(Ts,gy))]
nofill=Sh<=0
print('lines without left fill: %d of %d'%(nofill.sum(),len(Sh)))
print('A all lines:     ',f(meas(LA)));  print('A no-fill lines: ',f(meas(LA,nofill)))
print('B all lines:     ',f(meas(LB)));  print('B no-fill lines: ',f(meas(LB,nofill)))
P=Y.PRE
def refill(Ly,Sh,ghosts):
    # ghosted reference over prefix AND window (what the reference contributes everywhere), plus the picture edge at START
    ref=M.fwd(np.concatenate([R.hidden_y(D),np.zeros(Ly.shape[1])])[None],M.resp_y(ghosts),True)[0]
    hy=np.repeat(ref[None,:P],len(Ly),0); out=Ly.copy(); n=np.arange(Ly.shape[1]); e=R.edge_y(Ly.shape[1],1.0)
    for r,s in enumerate(Sh):
        if s>0:
            k=int(np.ceil(s))+1; lev=(Ly[r,k:k+4]-ref[P+k:P+k+4]).mean()/max(e[k:k+4].mean(),1e-3)
            out[r,:k]=ref[P:P+k]+lev*e[:k]
    return np.concatenate([hy,out],1)
for name,full in [('fill as signal',np.concatenate([np.repeat(seq.start_lines(LA,LcA,gy_t,[],D,BL)[0][:1,:P],len(LA),0),LA],1)),('fill replaced',refill(LA,Sh,gy_t))]:
    F1,_=seq.pass_full_y(full,74.25,SIG,LAM,g74); LP=F1[:,P:]
    for nm,sel in [('all',None),('no-fill',nofill)]:
        s_=np.ones(len(LP),bool) if sel is None else sel
        my1,_,_,_=R.masked_mean(LP[s_],LcA[s_],Sh[s_]); myB,_,_,_=R.masked_mean(LB[s_],LcA[s_],Sh[s_]); d=(my1-myB)[:150]
        print('pass(A) %-14s pooled over %-7s: diff vs B rms %.3f max %.3f | measured %s'%(name,nm,np.sqrt(np.mean(d**2)),np.abs(d).max(),f(meas(LP,sel))))
