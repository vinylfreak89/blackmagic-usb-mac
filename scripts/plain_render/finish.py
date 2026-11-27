#!/usr/bin/env python3
"""finish.py D PART OUT -- the one-pass render's last step. PART's video frame count, from the file's own index (ffprobe's
nb_frames reads the index, not the media: on a cloud volume nothing but the index is fetched), must be twice the relay's
slots (59.94p from 29.97 slots; one fewer when the last field has no partner; less the last slots the audio does not reach,
which -shortest leaves out), and it must hold an audio track. Then PART
takes OUT's name. An existing OUT (--replace) is deleted first; on the JuiceFS share the result is checked in JuiceMount's own
directory, by inode and size, because JuiceMount keeps a deleted path's size mark (2026-10-21). Prints RESULT."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'juicefs'))
from share_refresh import wait_sizes
D, PART, OUT = sys.argv[1:4]
SHARE = '/Volumes/zpool'; FUSE = os.path.expanduser('~/.juicemount/fuse-internal')
def truth(p):
    p = os.path.realpath(p)
    return FUSE + p[len(SHARE):] if p.startswith(SHARE + '/') and os.path.isdir(FUSE) else p
def refuse(m): print('RESULT REFUSED: ' + m); sys.exit(1)

# The share's size is JuiceMount's record; JuiceFS's is where the bytes are. They disagreed once for a whole render written to a
# just-deleted path (2026-11-18: 37 GB listed, 0 held), and every read of it was an I/O error. A share that lists LESS than
# JuiceFS holds is only behind (share_refresh.py), and is brought up to date first.
held = os.stat(truth(PART)).st_size; listed = os.path.getsize(PART)
if held != listed and PART != truth(PART): wait_sizes({PART: held}, timeout=60); listed = os.path.getsize(PART)
if held != listed: refuse('the share lists %d bytes for %s but JuiceFS holds %d: the render did not reach the volume' % (listed, PART, held))
slots = json.load(open(os.path.join(D, 'schedule.json')))['slots']
au = json.load(open(os.path.join(D, 'audio.json')))
r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,nb_frames,duration', '-of', 'json', PART], capture_output=True, text=True)
if r.returncode != 0: refuse('ffprobe could not read %s: %s' % (PART, r.stderr[-300:]))
st = json.loads(r.stdout).get('streams', [])
v = [s for s in st if s.get('codec_type') == 'video']; a = [s for s in st if s.get('codec_type') == 'audio']
if len(v) != 1 or len(a) != 1: refuse('expected one video and one audio track, found %d and %d' % (len(v), len(a)))
vf = int(v[0].get('nb_frames', -1))
# -shortest ends the video with the audio. The audio relay's last sample can fall short of the last slot's end (2026-11-20,
# 19-08-04: 1,310 samples, 27 ms, short of 84,533 slots; ffmpeg left that slot out), so the slots the audio does not reach in
# full may be missing at the end, and only those.
SLOT = 48000 * 1001 / 30000                       # 1601.6 samples per slot
short_slots = max(0, -(-(slots * SLOT - au['samples']) // SLOT)) if au['samples'] < slots * SLOT else 0
lowest = 2 * (slots - int(short_slots)) - 1
if not lowest <= vf <= 2 * slots:
    refuse('the render has %d frames, expected %d (down to %d where the audio ends %d slots early)' % (vf, 2 * slots, lowest, short_slots))
if vf < 2 * slots - 1:
    print('the last %d slots are not in the render: the audio ends %.1f ms before the last slot does' % (
          slots - (vf + 1) // 2, (slots * SLOT - au['samples']) / 48))
print('video %d frames (%.2f s, %d slots); audio %d samples streamed (%.2f s), %s s in the file; audio breaks %d; '
      'silence inserted (counter, samples): %s; re-anchors earlier than the audio (counter, samples, left contiguous): %s; '
      'untrusted anchors (counter, implied samples, left contiguous): %s' % (
      vf, vf * 1001 / 60000, slots, au['samples'], au['samples'] / 48000, a[0].get('duration'), au['discontinuities'],
      au['silence_inserted'], au['reanchors_earlier'], au['untrusted_breaks']))
size = os.path.getsize(PART); ino = os.stat(truth(PART)).st_ino
if os.path.exists(OUT): os.remove(OUT)
os.rename(PART, OUT)
t = os.stat(truth(OUT))
if t.st_size != size or t.st_ino != ino or os.path.exists(truth(PART)): refuse('the renamed render is not the one checked (size %d of %d, inode %d of %d)' % (t.st_size, size, t.st_ino, ino))
print(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,duration,nb_frames', '-of', 'compact', OUT], capture_output=True, text=True).stdout.strip())
print('RESULT OK', OUT)
