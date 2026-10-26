#!/usr/bin/env python3
"""On-share test of checked_read.py's re-read of a compacted chunk's layout: writes a 2-chunk test file through the share,
waits for it to upload, then
  1. a plain checked read proves every byte;
  2. a read whose first layout of chunk 1 names slices that no longer exist (as a layout taken just before JuiceFS compacted
     that chunk does) reads the chunk's layout again, proves every byte and writes the file unchanged;
  3. a read whose chunk 1 names missing slices every time (a lost slice) stops with exit 3 and names why.
The test file is removed at the end. Uploads ~100 MB to the volume's object store and lists two directories."""
import hashlib, json, os, subprocess, sys, tempfile, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); CR = os.path.join(HERE, 'checked_read.py')
NAME = '/Volumes/zpool/zz-checked-read-relayout-test-%d.bin' % os.getpid()
FUSE = os.path.expanduser('~/.juicemount/fuse-internal') + NAME[len('/Volumes/zpool'):]
def staged():
    t = urllib.request.urlopen('http://127.0.0.1:9568/metrics', timeout=10).read().decode()
    return float([l for l in t.splitlines() if l.startswith('juicefs_staging_block_bytes')][0].rsplit(' ', 1)[1])
def run(env, tag):
    d = tempfile.mkdtemp(); out, rep = os.path.join(d, 'out'), os.path.join(d, 'rep.json')
    p = subprocess.run([sys.executable, CR, NAME, '--out', out, '--report', rep], env=dict(os.environ, **env), capture_output=True, text=True, timeout=1800)
    r = json.load(open(rep)); same = os.path.exists(out) and hashlib.sha256(open(out, 'rb').read()).hexdigest() == want
    print('%s: exit %d, relayouts %d, mismatches %s, output identical %s' % (tag, p.returncode, len(r['relayouts']), [m.get('reason') for m in r['mismatches']], same))
    return p.returncode, r, same, p.stderr
data = os.urandom(100 << 20); want = hashlib.sha256(data).hexdigest()
if os.path.exists(NAME): sys.exit('%s exists' % NAME)
fd = os.open(NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
try:
    for i in range(0, len(data), 1 << 20): os.write(fd, data[i:i + (1 << 20)])
    os.fsync(fd); os.close(fd); fd = None
    t = time.time()
    while (os.path.getsize(FUSE) != len(data) or staged() > 0) and time.time() - t < 900: time.sleep(5)
    if staged() > 0: sys.exit('uploads did not finish in 15 min')
    time.sleep(10)
    rc, r, same, _ = run({}, 'plain')
    assert rc == 0 and same and not r['relayouts'] and not r['mismatches'], 'plain read failed'
    rc, r, same, err = run({'CHECKED_READ_TEST_GONE': '1'}, 'compacted chunk 1')
    assert rc == 0 and same and len(r['relayouts']) == 1 and r['relayouts'][0]['chunk'] == 1 and not r['mismatches'], 'the compacted chunk was not re-read'
    assert 'was rewritten (compacted)' in err
    rc, r, same, _ = run({'CHECKED_READ_TEST_GONE': '1,always'}, 'lost slice in chunk 1')
    assert rc == 3 and r['mismatches'] and 'still names it' in r['mismatches'][0]['reason'] and r['bytes_written'] == 64 << 20, 'a lost slice did not fail'
    print('checked_read relayout: all tests passed')
finally:
    if fd is not None: os.close(fd)
    if os.path.exists(NAME): os.remove(NAME)
    ad = os.path.join(os.path.dirname(NAME), '._' + os.path.basename(NAME))
    if os.path.exists(ad): os.remove(ad)
