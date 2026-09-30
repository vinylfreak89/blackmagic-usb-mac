# Random sample of flagged runs outside the owner's scored events, rendered for eyeball judgement.
import sys, json, os, struct, numpy as np, random; sys.path.insert(0, '.')
from load import load_mm; import sw2
from PIL import Image, ImageDraw
TP = {'tvc2': '/Volumes/vinylfreak89/captures/tornado_video_classics_2.mov.raw.tpc', 'trip': '/Volumes/vinylfreak89/captures/trip_tape.mov.raw.tpc'}
t = sys.argv[1]; K = int(sys.argv[2]); rng = random.Random(20260930)
c, p, M, E = load_mm(t); fl = np.load('flags_%s_fmB1+toph.npy' % t); top = np.load('%s.toph.npy' % t)
span = set()
if t == 'tvc2':
    for e in json.load(open('/private/tmp/wave-engine/claude1/abrender/tear_runs_fm.json')):
        for u in range(e['first'], e['last'] + 1): span.add((u - 2763, e['field'] - 1))
runs = []
for f in (0, 1):
    idx = [u for u in np.nonzero(fl[:, f])[0] if (u, f) not in span]
    if not idx: continue
    s = q = idx[0]
    for u in idx[1:]:
        if u - q > 1: runs.append((f, s, q)); s = u
        q = u
    runs.append((f, s, q))
pick = rng.sample(runs, K)
# flagged lines per chosen frame: rerun the rule over a lead-in so the window state is realistic
H_ = struct.Struct('<IBBHIIII'); UNIT = 756048
def read_unit(i):
    fd = os.open(TP[t], os.O_RDONLY); want = int(c[i]); start = max(0, int(p[i]) - (80 << 20)); b = os.pread(fd, int(p[i]) + (8 << 20) - start, start); os.close(fd)
    j = b.find(b'CAP1'); v = bytearray()
    # resync on a record chain
    while j >= 0:
        q = j; ok = 0
        while ok < 8 and q + 24 <= len(b):
            m, ty, ep, pi, seq, st, req, al = H_.unpack_from(b, q)
            if m != 0x31504143 or ty > 4: break
            q += 24 + (al if ty in (0, 3) else 0); ok += 1
        if ok == 8: break
        j = b.find(b'CAP1', j + 1)
    q = j
    while q + 24 <= len(b):
        m, ty, ep, pi, seq, st, req, al = H_.unpack_from(b, q)
        if m != 0x31504143 or q + 24 + (al if ty in (0, 3) else 0) > len(b): break
        if ty == 0 and ep == 0x83: v += b[q + 24:q + 24 + al]
        q += 24 + (al if ty in (0, 3) else 0)
    k = v.find(b'\x00\x00\xff\xff')
    while k >= 0:
        if struct.unpack_from('<H', v, k + 4)[0] == want and v[k + 6:k + 8] == b'\x01\xe8' and v[k + UNIT:k + UNIT + 4] == b'\x00\x00\xff\xff':
            return np.frombuffer(bytes(v[k + 48:k + UNIT]), np.uint8).reshape(525, 1440)
        k = v.find(b'\x00\x00\xff\xff', k + 1)
    raise SystemExit('unit not found %d' % i)
tiles = []
for n, (f, s, e) in enumerate(pick):
    a = max(0, s - 60); sw2.LINES.clear(); sw2.run(M[a:e + 1], E[a:e + 1], 'fmB1', keep_lines=True, top=top[a:e + 1])
    cand = [(len([h for ff, h in sw2.LINES.get(u - a, []) if ff == f + 1]), u) for u in range(s, e + 1)]
    nl, u = max(cand); ls = sorted(h for ff, h in sw2.LINES.get(u - a, []) if ff == f + 1)
    raw = read_unit(u); Y = raw[:, 1::2]; r0 = 19 if f == 0 else 282; rows = np.r_[r0:r0 + 243]
    full = Image.fromarray(Y[rows]).resize((360, 243)).convert('RGB'); d = ImageDraw.Draw(full)
    for h in ls: y = (h - 4 - r0); d.line((0, y, 8, y), fill=(255, 0, 255)); d.line((351, y, 359, y), fill=(255, 0, 255))
    lo = max(r0, min(ls) - 4 - 12); hi = min(r0 + 243, max(ls) - 4 + 13)
    def strip(x0, x1):
        im = Image.fromarray(Y[lo:hi, x0:x1]).resize(((x1 - x0) * 3, (hi - lo) * 6), Image.NEAREST).convert('RGB'); dd = ImageDraw.Draw(im)
        for h in ls: y = (h - 4 - lo) * 6 + 3; dd.line((0, y, 4, y), fill=(255, 0, 255)); dd.line((im.width - 5, y, im.width - 1, y), fill=(255, 0, 255))
        return im
    L = strip(0, 60); R = strip(660, 720)
    tile = Image.new('RGB', (360 + 10 + 180 + 10 + 180, max(243, L.height) + 18), (25, 25, 25)); tile.paste(full, (0, 18)); tile.paste(L, (370, 18)); tile.paste(R, (560, 18))
    ImageDraw.Draw(tile).text((2, 2), '#%d %s ext %d f%d run %d fr lines %s' % (n + 1, t, (u + 2763) if t == 'tvc2' else u, f + 1, e - s + 1, ','.join(map(str, ls))[:60]), fill=(255, 255, 0))
    tiles.append(tile)
    print(n + 1, f + 1, u, e - s + 1, ls, flush=True)
per = 6
for k in range(0, len(tiles), per):
    grp = tiles[k:k + per]; Wd = max(x.width for x in grp); Hh = sum(x.height + 8 for x in grp)
    sh = Image.new('RGB', (Wd, Hh), (10, 10, 10)); y = 0
    for x in grp: sh.paste(x, (0, y)); y += x.height + 8
    sh.save('fp_%s_%02d.jpg' % (t, k // per + 1), quality=90)
