#!/usr/bin/env python3
"""Known-answer test: capture_patch's one-pass read_back when the assembler exits before it opens its output FIFO (a bad
plan, the volume's metadata store down). The read-back must end with the assembler's failure, named, within a minute,
not wait forever on a FIFO nobody will open (it did before 2026-10-23).  usage: test_read_back_source_exit.py"""
import os, shutil, signal, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import capture_patch as CP

def main():
    W = tempfile.mkdtemp(prefix='rbx-')
    signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(AssertionError('read_back still waiting after 120 s')))
    signal.alarm(120)
    try:
        CP.read_back(os.path.join(W, 'P.mov.raw.tpc'), 1000, None, os.path.join(W, 'P.mov'), os.path.join(W, 'new.csv'), W, '23,286',
                     assembler=([sys.executable, '-c', 'import sys; sys.exit(3)'], W, dict(os.environ)))
        raise AssertionError('read_back succeeded with no assembler output')
    except CP.Failed as e:
        assert 'assemble.py failed (exit 3)' in str(e), str(e)
        print('assembler gone before its FIFO: %s' % e)
    finally:
        signal.alarm(0); shutil.rmtree(W)
    print('read_back source exit: all tests passed')

if __name__ == '__main__': main()
