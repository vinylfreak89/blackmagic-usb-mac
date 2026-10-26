import numpy as np, csv, sys
S=sys.argv[1]; sys.path.insert(0,S+'/an'); from cpedge import start_cp
sys.path.insert(0,'/Users/vinylfreak89/Documents/blackmagic-usb-mac/.claude/worktrees/compassionate-curran-38acb0/recovery'); import hretime as H
T=np.load(S+'/an/truth2.npy'); NB=len(T); d=(T[...,0]+T[...,2])/2; good=(T[...,1]>0.7)&(T[...,3]>0.7)
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r])
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)]); med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
B=np.load(S+'/rp/B.npy',mmap_mode='r'); rows=[]
DG=len(sys.argv)>2
if DG:
    import deghost as Dg; ec=np.load(sys.argv[2])
for g in np.nonzero(locked)[0][::2]:
    Y=B[g].astype(np.float32)
    if DG: Y[2:238]=Dg.deghost_luma(Y[2:238],ec['Er'],ec['Ef'])
    for i in np.nonzero(good[g])[0]:
        y=Y[i+4]; s=H.START-(d[g,i]-med)
        if not (8<s<120): continue
        k,conf=start_cp(y); rf=H.refs(y)[0]; pm=y[int(s)+3:int(s)+23].mean()
        rows.append((s,k,conf,rf,pm))
R=np.array(rows); s,k,conf,rf,pm=R.T
off=np.median(k-s); print('lines with the true start 8-120 samples in: %d; change point minus true start: median %+.2f'%(len(R),off))
pc=lambda a: tuple(np.percentile(a,[50,90])) if len(a) else (np.nan,np.nan)
for name,m in (('all',pm>=0),('picture mean <10',pm<10),('10-25',(pm>=10)&(pm<25)),('25+',pm>=25)):
    e_cp=np.abs(k[m]-off-s[m]); hit=~np.isnan(rf[m]); e_rf=np.abs(rf[m][hit]-s[m][hit])
    a=pc(e_rf); b=pc(e_cp); c=pc(e_cp[~hit])
    print('  %-17s n %5d | level detector finds %3.0f%%, |err| p50 %.2f p90 %.2f | change point |err| p50 %.2f p90 %.2f, within 2: %3.0f%% | where the level detector finds nothing: p50 %.2f p90 %.2f'
          %(name,m.sum(),100*hit.mean(),a[0],a[1],b[0],b[1],100*np.mean(e_cp<=2),c[0],c[1]))
np.save(S+'/an/cp_eval%s.npy'%('_dg' if DG else ''),R)
