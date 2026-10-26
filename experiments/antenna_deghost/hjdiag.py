import numpy as np, sys, csv, collections
S=sys.argv[1]
T=np.load(S+'/an/truth2.npy'); NB=T.shape[0]; good=(T[...,1]>0.6)&(T[...,3]>0.6); d=(T[...,0]+T[...,2])/2
r=list(csv.DictReader(open(S+'/rp/a_log.csv'))); st=np.array([x['reading'].split('/')[0] for x in r])
locked=np.array([all(x=='still' for x in st[max(0,g+33):g+40]) for g in range(NB)])
med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0]))
def load(jc):
    C=np.full((NB,258),np.nan); R=np.full((NB,258),'',object)
    for x in csv.DictReader(open(S+'/an/hj_%s.csv'%jc)): C[int(x['field']),int(x['line'])]=float(x['correction']); R[int(x['field']),int(x['line'])]=x['source']
    return C[:,24:257],R[:,24:257]
m=good&locked[:,None]
# truth's own line-to-line jumps (adjacent lines both good)
dd=np.abs(np.diff(d,axis=1)); both=m[:,1:]&m[:,:-1]
print('truth: adjacent good-line pairs %d, |step| p50 %.2f p99 %.2f, >4: %.3f%%'%(both.sum(),np.median(dd[both]),np.percentile(dd[both],99),100*(dd[both]>4).mean()))
for jc in ('0','0.5','1','2'):
    C,R=load(jc); e=np.abs(C+med-d)
    cnt=collections.Counter(R[m]); bad=collections.Counter(R[m&(e>6)])
    print('jc',jc,' sources:',{k:'%d (%.0f%% err>6)'%(v,100*bad[k]/v) for k,v in cnt.most_common()})
C0,R0=load('0'); C1,R1=load('1'); e0=np.abs(C0+med-d); e1=np.abs(C1+med-d)
worse=m&(e1>6)&(e0<3); print('lines good at 0, bad at 1:',worse.sum(),'; bad at 0, good at 1:',(m&(e0>6)&(e1<3)).sum())
print('of worse, source at 1:',collections.Counter(R1[worse]).most_common(), ' source at 0:',collections.Counter(R0[worse]).most_common(4))
# run lengths of worse within fields
runs=[]
for g in range(NB):
    w=worse[g]; i=0
    while i<len(w):
        if w[i]:
            j=i
            while j<len(w) and w[j]: j+=1
            runs.append((j-i,g,i+24)); i=j
        else: i+=1
runs.sort(reverse=True); print('longest runs (len, field, first line):',runs[:12]); np.save(S+'/an/worse_runs.npy',np.array(runs))
