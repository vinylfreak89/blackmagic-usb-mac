# The places a capture's stretch is broken, from its own bytes: picture units missing or of the wrong length (video gaps), resync
# intervals off the cadence (audio gaps), and the clusters they form. The builder fills each cluster; the line-up places a clip
# cluster by cluster (clusters.py). One definition for both.
from region import UNIT

def unwrap(cs):
    out = [cs[0]]
    for c in cs[1:]: out.append(out[-1] + ((c - out[-1] + 32768) % 65536) - 32768)
    return out
def find_gaps(R):
    whole = [(off, c) for off, c, fm, ok in R.marks if ok and fm == 0xe801]
    vg = []
    for (o1, c1), (o2, c2) in zip(whole, whole[1:]):
        if o2 - o1 != UNIT or (c2 - c1) % 65536 != 1:
            vg.append(dict(c1=c1, c2=c2, s_from=o1 + UNIT, s_to=o2, n=(c2 - c1) % 65536 - 1, k=R.vpk[R.vrec_of(o1 + UNIT)][1]))
    ag = []
    for (i1, s1, c1), (i2, s2, c2) in zip(R.resyncs, R.resyncs[1:]):
        n = s2 - s1; k = (c2 - c1) % 65536
        if k != 1 or n not in (1601, 1602):
            if ag and i1 - ag[-1]['r2'] <= 3 * 1603:      # gaps a few intervals apart are rebuilt as one span, resyncs between them included
                g = ag[-1]; g.update(c2=c2, n=s2 - g['sA'], kc=(c2 - g['c1']) % 65536, r2=i2, sB=s2)
            else: ag.append(dict(c1=c1, c2=c2, n=n, kc=k, r1=i1, r2=i2, sA=s1, sB=s2, k=R.apk[R.arec_of(i1)][1]))
    return vg, ag

def cluster_gaps(vg, ag, span=24000):
    items = sorted([(g['k'], 'v', g) for g in vg] + [(g['k'], 'a', g) for g in ag], key=lambda x: x[0]); cl = []
    for k, kind, g in items:
        if cl and k - cl[-1]['last'] < span: cl[-1][kind].append(g); cl[-1]['last'] = k
        else: cl.append(dict(v=[], a=[], last=k)); cl[-1][kind].append(g)
    return cl
