# per field, post-retime (hretime log corrections): mean complex chroma (U-128 + i(V-128)) by distance t from the picture start
import numpy as np, csv, sys
S=sys.argv[1]; START=4.4
V=np.memmap(S+'/rp/b.uyvy',np.uint8,'r').reshape(-1,480,1440)
C={}
for r in csv.DictReader(open(S+'/an/hj_final.csv')): C[(int(r['field']),int(r['line']))]=float(r['correction'])
TT=np.arange(-40,240,2)
fields=range(0,1674,int(sys.argv[2])); out=[]
for g in fields:
    f=V[g//2][g%2::2]; acc=np.zeros(len(TT),complex); cnt=np.zeros(len(TT))
    for l in range(30,250):
        c=C.get((g,l)); 
        if c is None: continue
        row=f[l-20].astype(np.float32); u=row[0::4]-128; v=row[2::4]-128          # chroma at luma x = 0,2,4,...
        x=(START-c+TT)/2.0; ok=(x>=2)&(x<=356)
        z=np.interp(x[ok],np.arange(360),u)+1j*np.interp(x[ok],np.arange(360),v)
        acc[ok]+=z; cnt[ok]+=1
    out.append(acc/np.maximum(cnt,1))
Z=np.array(out); np.save(S+'/an/burst_ghost.npy',Z)
mag=np.abs(Z).mean(0); print('t (samples from picture start): mean |chroma vector| over fields')
print('  '+' '.join('%d:%.1f'%(t,m) for t,m in zip(TT,mag) if t%10==0))
pk=int(np.argmax(np.abs(Z)[:, (TT>0)&(TT<150)].mean(0)))+np.nonzero((TT>0)&(TT<150))[0][0]
ph=np.degrees(np.angle(Z[:,pk])); a=np.abs(Z[:,pk])
print('peak at t=%d: |vector| per field p10 %.1f p50 %.1f p90 %.1f; phase per field p10 %.0f p50 %.0f p90 %.0f deg; circular spread %.2f'%(TT[pk],*np.percentile(a,[10,50,90]),*np.percentile(ph,[10,50,90]),1-abs(np.mean(np.exp(1j*np.radians(ph))))))
far=(TT>160); print('content level for comparison (t>160): mean |vector| %.1f'%np.abs(Z[:,far]).mean())
