# hretime log -> sbs.py shift file: (fields, 233) values = correction + med for lines 24..256
import numpy as np, sys, csv
S, src, dst = sys.argv[1:4]
med=float(np.nanmedian(np.load(S+'/an/est2.npy')[0])); SH=np.full((1674,233),np.nan)
for r in csv.DictReader(open(src)):
    l=int(r['line'])
    if 24<=l<=256: SH[int(r['field']),l-24]=float(r['correction'])+med
assert np.isfinite(SH).all(), np.isnan(SH).sum()
np.save(S+'/an/'+dst,SH); print('ok', SH.shape)
