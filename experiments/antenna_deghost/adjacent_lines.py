# Adjacent selected lines of one field at the same level share the channel (one field is 16 ms) and the same
# blanking/sync before their start, so a ghost puts the same thing at the start of both.  Their difference over the
# start (15-200) against the difference over the plain part (220-360) separates picture content at the line start
# from a ghost that changes over time.
import numpy as np, sys; sys.path.insert(0,'.')
import plain_fit as PF
S=sys.argv[1]; NR=236; sh=np.load(S+'/tape_sh.npy'); NF=len(sh); Yy=np.memmap(S+'/tape_y.f32',np.float32,'r',shape=(NF,NR,720))
st=[]; pl=[]; rows=[]
for f in range(NF):
    y=np.asarray(Yy[f],float); sel=dict(PF.select(y,sh[f]))
    for r,L in sel.items():
        if r+1 in sel and abs(sel[r+1]-L)<3:
            d=y[r+1]-y[r]; st.append(np.sqrt(np.mean((d[15:200]-d[220:360].mean())**2))); pl.append(d[220:360].std()); rows.append((f,L))
st=np.array(st); pl=np.array(pl); L=np.array([x[1] for x in rows])
print('pairs %d'%len(st))
for a,b in PF.BANDS:
    k=(L>=a)&(L<b)
    if k.sum(): print('level %3d-%3d pairs %5d  diff RMS start 15-200: median %5.2f p90 %5.2f | plain 220-360: median %5.2f p90 %5.2f  | fraction start > 2x plain %.2f'%(
        a,b,k.sum(),np.median(st[k]),np.percentile(st[k],90),np.median(pl[k]),np.percentile(pl[k],90),np.mean(st[k]>2*pl[k])))
