# side by side, per field: TBC-off as captured | retimed from each line's own blanking (UYVY, 1448x240 per field)
import numpy as np, sys
S=sys.argv[1]
V=np.fromfile(S+'/rp/b.uyvy',np.uint8).reshape(-1,480,1440)
SH=np.load(S+'/an/'+(sys.argv[2] if len(sys.argv)>2 else 'shift_final2.npy')); E=np.load(S+'/an/est2.npy'); med=float(np.nanmedian(E[0]))
L=np.arange(24,257); BLK=np.tile(np.array([128,16],np.uint8),720)
def shift_uyvy(row, s):
    y=row[1::2].astype(np.float32); u=row[0::4].astype(np.float32); v=row[2::4].astype(np.float32)
    def sh(a, s, fill):
        x=np.arange(len(a))-s; i0=np.floor(x).astype(int); f=x-i0; ok=(i0>=0)&(i0<len(a)-1)
        o=np.full(len(a),fill,np.float32); o[ok]=a[i0[ok]]*(1-f[ok])+a[i0[ok]+1]*f[ok]; return o
    y2=sh(y,s,16); u2=sh(u,s/2,128); v2=sh(v,s/2,128)
    out=np.empty(1440,np.uint8); out[1::2]=np.clip(y2,0,255); out[0::4]=np.clip(u2,0,255); out[2::4]=np.clip(v2,0,255); return out
gap=np.tile(np.array([128,16],np.uint8),8)    # 8 samples = 16 bytes: rows stay 1448 samples
o=sys.stdout.buffer
for g in range(V.shape[0]*2):
    f=V[g//2][g%2::2]                       # 240 rows = slots 20..259
    raw=np.concatenate([f[2:240], np.tile(BLK,(2,1))])          # lines 22..259 + 2 black
    fix=raw.copy()
    for i,l in enumerate(L):
        s=SH[g,i] if g<SH.shape[0] else np.nan
        if not np.isnan(s): fix[l-22]=shift_uyvy(raw[l-22], s-med)
    o.write(np.concatenate([raw, np.tile(gap,(240,1)), fix],1).tobytes())
