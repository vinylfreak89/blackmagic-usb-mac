#!/usr/bin/env python3
"""swap's ._ cleanup removes the ._ entry of every name that no longer exists, keeps the ._ of names still there, and
names each entry it could not remove (2026-11-24: two ._ entries of 13-11-20's patched names stayed on the share after a
swap that ignored every delete error). usage: test_orphan_stubs.py"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_patch as CP
d = tempfile.mkdtemp()
P = lambda n: os.path.join(d, n)
open(P('cap.tpc'), 'w').close(); open(P('._cap.tpc'), 'w').close()           # still exists: its ._ stays
open(P('._cap patched.tpc'), 'w').close()                                     # renamed away: its ._ goes
os.mkdir(P('._cap patched.mov'))                                              # cannot be unlinked: reported
left = CP.orphan_stubs([P('cap.tpc'), P('cap patched.tpc'), P('cap patched.mov'), P('never.csv')])
assert os.path.exists(P('._cap.tpc')), 'the ._ of an existing name is kept'
assert not os.path.exists(P('._cap patched.tpc')), 'the ._ of a renamed-away name is removed'
assert len(left) == 1 and left[0].startswith(P('._cap patched.mov') + ':'), left
os.rmdir(P('._cap patched.mov')); os.remove(P('cap.tpc')); os.remove(P('._cap.tpc')); os.rmdir(d)
print('orphan_stubs: ok')
