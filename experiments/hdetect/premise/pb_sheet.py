import sys, json, random, numpy as np
sys.path.insert(0, 'premise'); sys.path.insert(0, '/private/tmp/wave-engine/claude1/abrender')
from playback import raw_units, a_offset, AF
from PIL import Image, ImageDraw
U = json.load(open('premise/pb_unscored.json')); rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
pick = sorted(rng.sample(U, int(sys.argv[1])), key=lambda x: x[1])
tiles = []
for w, u, f, lines in pick:
    raw = None
    for c, r in raw_units(AF, max(0, a_offset(u) - (6 << 20)), a_offset(u) + (6 << 20)):
        if c == u % 65536: raw = r; break
    if raw is None: continue
    Y = raw[:, 1::2]; r0 = 19 if f == 1 else 282; F = Y[r0:r0 + 243]
    full = Image.fromarray(F).resize((360, 243)).convert('RGB'); d = ImageDraw.Draw(full)
    for rr in lines: y = rr - r0; d.line((0, y, 6, y), fill=(255, 0, 255)); d.line((353, y, 359, y), fill=(255, 0, 255))
    lo = max(0, min(lines) - r0 - 6); hi = min(243, max(lines) - r0 + 7)
    def strip(x0, x1):
        im = Image.fromarray(F[lo:hi, x0:x1]).resize(((x1 - x0) * 3, (hi - lo) * 5), Image.NEAREST).convert('RGB'); dd = ImageDraw.Draw(im)
        for rr in lines: y = (rr - r0 - lo) * 5 + 2; dd.line((0, y, 4, y), fill=(255, 0, 255))
        return im
    L, R = strip(0, 60), strip(660, 720)
    t = Image.new('RGB', (360 + 10 + 180 + 10 + 180, max(243, L.height) + 16), (25, 25, 25)); t.paste(full, (0, 16)); t.paste(L, (370, 16)); t.paste(R, (560, 16))
    ImageDraw.Draw(t).text((2, 2), 'w%d A %d f%d  NTSC %s' % (w, u, f, ','.join(str(x + 4) for x in lines[:14])), fill=(255, 255, 0)); tiles.append(t)
for k in range(0, len(tiles), 6):
    g = tiles[k:k + 6]; S = Image.new('RGB', (max(x.width for x in g), sum(x.height + 6 for x in g)), (0, 0, 0)); y = 0
    for x in g: S.paste(x, (0, y)); y += x.height + 6
    S.save('premise/pb_unscored_%d.jpg' % (k // 6 + 1), quality=88)
print(len(tiles), 'tiles')
