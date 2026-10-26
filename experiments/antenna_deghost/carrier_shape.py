# Shape of the growth.  Copy size vs landing brightness L (codes above blanking), start brightness held in a narrow band.
#   gain pattern + linear ghost:  size = a + b*L              (straight; the gain part is zero at blanking)
#   carrier effect + linear ghost: size = a + b / c(L),  c(L) = 0.75 - 0.625 * (L / 219)   (carrier fraction, NTSC
#                                  negative modulation: blanking 75 %, white 12.5 %; 219 codes per 100 IRE)
# Same number of free parameters; compare the misfit against the bins' own standard errors (chi-square per bin).
# Landing below 25 codes left out (dark copies clipped at the capture floor there).
import numpy as np
S='/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac--claude-worktrees-compassionate-curran-38acb0/fce3a79e-594f-4e0b-a156-893976ab2729/scratchpad'
a_s,a_r,Ls,Lsync,Lramp=np.load(S+'/carrier_test.npy').T
c=lambda L: 0.75-0.625*L/219.0
def curve(a,L,sel,lo=25,hi=170,nb=12):
    e=np.percentile(L[sel&(L>=lo)&(L<=hi)],np.linspace(0,100,nb+1)); x=[];y=[];se=[]
    for i in range(nb):
        m=sel&(L>=e[i])&(L<=e[i+1]); x.append(np.median(L[m])); y.append(a[m].mean()); se.append(a[m].std()/np.sqrt(m.sum()))
    return np.array(x),np.array(y),np.array(se)
def fit(x,y,se,f):
    A=np.stack([np.ones_like(x),f(x)],1)/se[:,None]; p=np.linalg.lstsq(A,y/se,rcond=None)[0]; r=y/se-A@p
    return p,np.sum(r**2)/(len(x)-2)
for name,a,L,startband in [('SYNC copies (20-60)',a_s,Lsync,(15,40)),('SYNC copies (20-60)',a_s,Lsync,(40,60)),('RAMP copies (75-140)',a_r,Lramp,(30,45)),('RAMP copies (75-140)',a_r,Lramp,(45,70))]:
    sel=(Ls>=startband[0])&(Ls<startband[1]); x,y,se=curve(a,L,sel)
    pl,cl=fit(x,y,se,lambda L: L); pc,cc=fit(x,y,se,lambda L: 1/c(L))
    print('\n%s, line start %d-%d (%d lines)'%(name,startband[0],startband[1],sel.sum()))
    print('  landing  size   ±se   | straight  1/carrier')
    for xi,yi,si in zip(x,y,se): print('  %6.1f  %6.2f  %4.2f  | %6.2f    %6.2f'%(xi,yi,si,pl[0]+pl[1]*xi,pc[0]+pc[1]/c(xi)))
    print('  misfit (chi2 per bin): straight %.1f   1/carrier %.1f'%(cl,cc))
    print('  straight line extrapolated to blanking (L=0): %.2f   (pure gain pattern: the landing-dependent part is zero there)'%pl[0])
