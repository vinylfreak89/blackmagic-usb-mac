# Seam checks on a filled stretch: audio steps at each junction against the surrounding audio, and picture change across each filled run.
import sys, json, pickle, numpy as np
sys.path.insert(0, '.')
from region import *
from PIL import Image
def check_stretch(g, sheet=True):
    meta = json.load(open('ev/events.json'))[g]; mods = pickle.load(open('ev/m%02d.pkl' % g, 'rb'))
    N = Region(open('ev/n%02d.bin' % g, 'rb').read(), meta['file_from']); L, Rr = N.pcm(); res = []
    shift = 0
    for m in sorted(mods, key=lambda m: m['file_from']):
        rep = m['rep']
        for sm in rep.get('seams', []):
            j1 = sm['cut1'] + shift; j2 = sm['cut2'] + shift + sm['M']; shift += sm['M']
            out = dict(cluster=rep['name'], kind='audio', samples_inserted=sm['inserted'], missing=sm['M'], level_db=sm.get('levels_db'))
            for nm, j in (('start', j1), ('end', j2)):
                worst = 0
                for x in (L, Rr):
                    x = x.astype(np.float64); st = np.abs(np.diff(x[j - 1500:j + 1500])); me = abs(x[j] - x[j - 1])
                    c2 = np.abs(x[j - 1500 + 2:j + 1500] - 2 * x[j - 1500 + 1:j + 1499] + x[j - 1500:j + 1498]); mc = max(abs(x[j + 1] - 2 * x[j] + x[j - 1]), abs(x[j] - 2 * x[j - 1] + x[j - 2]))
                    worst = max(worst, float((st < me).mean()), float((c2 < mc).mean()))
                out['junction_' + nm + '_percentile'] = round(100 * worst, 1)
            res.append(out)
        if rep.get('video_units_filled'):
            W = N.whole_units()
            def rows(c):
                o = W[c % 65536]; return np.frombuffer(bytes(N.v[o + 48:o + UNIT]), np.uint8).reshape(525, 1440)
            def f(c, s): return rows(c)[24:256, 1::2].astype(np.float32) if s == 1 else rows(c)[287:519, 1::2].astype(np.float32)
            for lo, hi in rep['video_units_filled']:
                seq = [(c, s) for c in range(lo - 4, hi + 5) for s in (1, 2)]
                d = [float(np.abs(f(*seq[i]) - f(*seq[i - 2])).mean()) for i in range(2, len(seq))]      # same-slot change, field by field in time order
                lab = [seq[i] for i in range(2, len(seq))]
                inside = [x for x, (c, s) in zip(d, lab) if lo <= c <= hi + 1]; outside = [x for x, (c, s) in zip(d, lab) if not (lo <= c <= hi + 1)]
                res.append(dict(cluster=rep['name'], kind='picture', units=[lo, hi], change_at_and_inside_fill=[round(x, 2) for x in inside], change_in_untouched_neighbours=[round(x, 2) for x in outside],
                                worst_ratio=round(max(inside) / (np.median(outside) + 1e-6), 2)))
                if sheet:
                    tiles = []
                    for c in range(lo - 2, hi + 3):
                        r = rows(c); fr = np.empty((464, 720), np.uint8); fr[0::2] = r[24:256, 1::2]; fr[1::2] = r[287:519, 1::2]
                        im = Image.fromarray(fr).resize((360, 270)); tiles.append((c, im))
                    W_ = min(len(tiles), 7); H_ = (len(tiles) + W_ - 1) // W_; sh = Image.new('L', (360 * W_, 290 * H_), 0)
                    from PIL import ImageDraw; dr = ImageDraw.Draw(sh)
                    for i, (c, im) in enumerate(tiles):
                        x, y = (i % W_) * 360, (i // W_) * 290; sh.paste(im, (x, y + 20)); dr.text((x + 4, y + 4), '%d %s' % (c % 65536, 'FILLED' if lo <= c <= hi else 'target'), fill=255)
                    sh.save('ev/sheet_%s_%d.png' % (rep['name'], lo))
    return res
if __name__ == '__main__':
    allr = []
    for g in [int(x) for x in sys.argv[1:]]:
        try: r = check_stretch(g)
        except Exception as e: r = [dict(cluster='g%02d' % g, error=repr(e))]
        for x in r: print(json.dumps(x)[:600])
        allr += r
    json.dump(allr, open('ev/seam_check.json', 'w'), indent=1)
