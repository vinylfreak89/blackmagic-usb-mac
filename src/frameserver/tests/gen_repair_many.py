"""gen_repair_many.py OUT.tpc N -- a capture of N picture units where every 4th (c % 4 == 3) is 224 bytes short like
scripts/test_unit_repair_replay.py's unit 3 (748 bytes of a line deleted, 524 zeros in their place): a repair candidate."""
import sys
from pathlib import Path
out_path, N = sys.argv[1], int(sys.argv[2])
script = Path(__file__).resolve().parents[3] / 'scripts/test_unit_repair_replay.py'
pre = script.read_text().split("video = build(510)")[0]
g = {'__file__': str(script)}; sys.argv = ['x', 'x']; exec(compile(pre, str(script), 'exec'), g)
fx, header, raster, HB, L = g['fx'], g['header'], g['raster'], g['HB'], g['L']
units = []
for c in range(N):
    u = header(c % 65536) + raster(c % 50)
    if c % 4 == 3:
        p = HB + 220 * L + 950; u = u[:p] + bytes(524) + u[p + 748:]
    units.append(u)
video = b''.join(units) + header(N)[:8]
audio = bytearray()
for c in range(N + 1):
    audio += fx.resync(c) + b''.join(fx.pcm(c * 1601 + i) for i in range(1601))
with open(out_path, 'wb') as out:
    for ep, stream, packet in ((fx.AUDIO, audio, 2048), (fx.VIDEO, video, 15360)):
        for seq, off in enumerate(range(0, len(stream), packet)):
            out.write(fx.record(fx.DATA, ep, 0, seq, 0, packet, stream[off:off + packet]))
