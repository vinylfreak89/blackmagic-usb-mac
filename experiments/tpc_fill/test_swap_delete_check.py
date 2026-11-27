#!/usr/bin/env python3
"""capture_patch.swap after its deletes, with stand-ins for the share (SHARE) and JuiceFS (FUSE) as two folders:
  - JuiceFS still holding an original name after the delete through the share stops the swap by name, before any rename
    (a comment once swallowed this check's call, leaving a bare `fail` that raised nothing);
  - a result.json written before 2026-11-26 names a split capture's later part by its JuiceFS path: swap deletes it through
    the share, and nothing under FUSE is removed.
usage: test_swap_delete_check.py"""
import hashlib, json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_patch as CP

d = os.path.realpath(tempfile.mkdtemp(prefix='swap_check_')); share, fuse, W = (os.path.join(d, n) for n in ('share', 'fuse', 'work'))
for x in (share, fuse, W): os.makedirs(x)
CP.SHARE, CP.FUSE = share, fuse
K = CP.KINDS; O = {k: os.path.join(share, 'T' + v) for k, v in K.items()}; P = {k: os.path.join(share, 'T patched' + v) for k, v in K.items()}
J = lambda p: fuse + p[len(share):]
for p in list(O.values()) + list(P.values()): open(p, 'wb').write(os.urandom(4096))
os.link(P['tpc'], J(P['tpc']))                                  # JuiceFS shows the patched capture as the share does
for p in O.values(): shutil.copy(p, J(p))                       # and still holds the originals after their delete
part2 = os.path.join(share, 'T.mov.raw.part2.tpc'); open(part2, 'wb').write(b'p2'); open(J(part2), 'wb').write(b'p2')
open(os.path.join(W, 'sidecar.csv'), 'w').write('x\n')
st = os.stat(P['tpc']); hd, tl = CP.digests(P['tpc'], st.st_size)
json.dump(dict(state='verified', original=O, patched=P, replaced=[J(part2)], bytes=st.st_size, patched_mtime=int(st.st_mtime), patched_ino=st.st_ino,
               head=hd, tail=tl, sidecar=os.path.join(W, 'sidecar.csv'), sidecar_sha256=hashlib.sha256(b'x\n').hexdigest(), input_stats={}),
          open(os.path.join(W, 'result.json'), 'w'))
try: CP.swap(W); raise AssertionError('swap went on with an original name still on JuiceFS')
except CP.Failed as e: assert 'an original name still exists after the delete' in str(e), str(e)
assert not any(os.path.exists(p) for p in O.values()) and not os.path.exists(part2), 'the originals and part 2 are deleted through the share'
assert all(os.path.exists(J(p)) for p in O.values()) and os.path.exists(J(part2)), 'nothing is deleted through JuiceFS'
assert os.path.exists(P['tpc']) and os.path.exists(P['mov']), 'nothing renamed after the failed check'
assert json.load(open(os.path.join(W, 'result.json')))['state'] == 'verified'
shutil.rmtree(d); print('swap delete check: all tests passed')
