# colour measurement bias: (a) no ghosts, (b) true ghosts; burst level known (2.4); no noise; chain G = 1
exec(open('diag_gen.py').read())
import seq2
f=lambda v:' '.join('%.0f:%.3f∠%+.0f'%(T,abs(g),np.degrees(np.angle(g))) for T,g in zip(Ts,v))
Gy=np.ones(Y.NFFT,complex); Gc=np.ones(X.NFFT,complex)
for name,gcl in [('no colour ghosts',[]),('true colour ghosts',gc_t)]:
    Ly,Lc,Sh=build(gy_t,gc_list=gcl); my,mc,_,_=R.masked_mean(Ly,Lc,Sh)
    for nc in (70,):
        ac,gy,L=seq2.measure(my,mc,Ts,D,SIG,LAM,Gy,Gc,BL,nc=nc)
        print('%-20s nc=%d  colour %s'%(name,nc,f(ac/BL)))
    np.save('/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad/mc_%s.npy'%('0' if not gcl else 't'),mc)
print('true                         colour',f([g[3] for g in gc_t]))
