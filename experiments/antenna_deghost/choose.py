# per field: candidate shifts per line from the signal; a best path down the field picks one per line,
# charging each choice its own (confidence) cost plus the roughness it makes against the line above.
import numpy as np, sys, warnings
warnings.filterwarnings('ignore')
S=sys.argv[1]
V=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
R=np.load(S+'/an/refs.npy'); E=np.load(S+'/an/est2.npy'); med=float(np.nanmedian(E[0]))
L=np.arange(24,257); NF=V.shape[0]*2
CL,CR,S0,S1=12.7,722.9,5.5,713.5
PIN=((CL-S0)+(CR-S1))/2
LAMBDA=3.0                       # cost of an unconfident candidate, in roughness units (mean |diff| per sample)
def shifted(y,s):
    x=np.arange(720)-s; i0=np.floor(x).astype(int); f=x-i0; ok=(i0>=0)&(i0<719)
    o=np.full(720,np.nan,np.float32); o[ok]=y[i0[ok]]*(1-f[ok])+y[i0[ok]+1]*f[ok]; return o
def rough(a,b):
    c=slice(60,660); d=np.abs(a[c]-b[c]); return float(np.nanmean(d)) if np.isfinite(d).sum()>200 else 20.0
out=np.full((NF,len(L)),np.nan)
for g in range(NF):
    Y=V[g//2][g%2::2][L-20,1::2].astype(np.float32)
    xl,cl,xr,cr=R[g,:,0],R[g,:,1],R[g,:,2],R[g,:,3]
    own=[]
    for i in range(len(L)):
        c=[]
        if not np.isnan(xl[i]) and xl[i]>S0: c.append((CL-xl[i], 1-cl[i]))
        if not np.isnan(xr[i]) and xr[i]<S1: c.append((CR-xr[i], 1-cr[i]))
        lo_ok = (np.isnan(xl[i]) or xl[i]<=S0) and (np.isnan(xr[i]) or xr[i]>=S1)
        if lo_ok and Y[i,6:30].min()>14 and Y[i,690:713].min()>14: c.append((PIN, 0.3))
        own.append(c)
    vals=np.array([v for c in own for v,_ in c]) if any(own) else np.array([PIN])
    cand=[]
    for i in range(len(L)):
        near=[v for j in range(max(0,i-8),min(len(L),i+9)) for v,_ in own[j]]
        c=list(own[i])
        if near: c.append((float(np.median(near)), 0.6))
        c.append((PIN, 0.9))                                   # the window's typical placement, as a last resort
        # merge near-duplicates
        m=[]
        for v,k in sorted(c):
            if m and abs(v-m[-1][0])<0.75: m[-1]=(m[-1][0],min(m[-1][1],k))
            else: m.append((v,k))
        cand.append(m)
    rows=[[shifted(Y[i],v-med) for v,_ in cand[i]] for i in range(len(L))]
    cost=[np.array([LAMBDA*k for _,k in cand[0]])]; back=[None]
    for i in range(1,len(L)):
        prev=cost[-1]; cur=np.zeros(len(cand[i])); bp=np.zeros(len(cand[i]),int)
        for a in range(len(cand[i])):
            t=[prev[b]+rough(rows[i][a],rows[i-1][b]) for b in range(len(cand[i-1]))]
            bp[a]=int(np.argmin(t)); cur[a]=t[bp[a]]+LAMBDA*cand[i][a][1]
        cost.append(cur); back.append(bp)
    k=int(np.argmin(cost[-1]))
    for i in range(len(L)-1,-1,-1):
        out[g,i]=cand[i][k][0]
        if i>0: k=back[i][k]
np.save(S+'/an/shift_chosen.npy',out)
