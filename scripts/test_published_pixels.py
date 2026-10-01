"""Actual output provenance, reversed pairing, strict spool accounting and ticks."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from published_pixels import PublishedPixels, repair_ticks

with tempfile.TemporaryDirectory(prefix='published-pixels-') as directory:
    p = Path(directory)/'pixels.uyvy'
    units = [np.full((480,1440),v,np.uint8).tobytes() for v in (10,11,12,13)]
    data = b''.join(units)
    p.write_bytes(data)
    rows = [dict(counter_extended=str(c),published='1') for c in range(10,14)]
    compressed = p.with_suffix('.zst')
    subprocess.run(['zstd','-q','-1',str(p),'-o',str(compressed)],check=True)
    ffv1 = p.with_suffix('.mkv')
    subprocess.run(['ffmpeg','-v','error','-f','rawvideo','-pix_fmt','uyvy422',
        '-s','720x480','-i',str(p),'-c:v','ffv1','-level','3','-pix_fmt','yuv422p',str(ffv1)],check=True)
    for path in (p,compressed,ffv1):
        reader = PublishedPixels(path,rows)
        try:
            a = reader.frame(11,10)
            assert np.all(a[::2] == 11) and np.all(a[1::2] == 10)
            b = reader.frame(12,11)
            assert np.all(b[::2] == 12) and np.all(b[1::2] == 11)
            try: reader.unit(10)
            except ValueError: pass
            else: raise AssertionError('accepted an evicted unit')
            result = reader.finish() # unpaired tail13 still accounted
            assert result == dict(units=4,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        finally: reader.close()
    for bad in (data[:-1],data+b'x'):
        p.write_bytes(bad)
        reader = PublishedPixels(p,rows)
        try:
            try: reader.finish()
            except ValueError: pass
            else: raise AssertionError('accepted an inexact pixel stream')
        finally: reader.close()

row = dict(frame_d1='1',frame_d2='0',hretime_lines_f1='24:C 25:I 26:U 27:R',
           hretime_lines_f2='286:I 287:R',hretime_retimed_f1='1',hretime_retimed_f2='1',
           hretime_interpolated_f1='1',hretime_interpolated_f2='1')
assert repair_ticks(row) == [(2,'I'),(6,'R'),(1,'I'),(3,'R')]
for key,value in [('hretime_lines_f1','24:I 24:I'),('hretime_lines_f2','285:I'),
                  ('hretime_retimed_f1','2'),('hretime_lines_f1','24:X'),('hretime_lines_f1','24:')]:
    try: repair_ticks(dict(row,**{key:value}))
    except ValueError: pass
    else: raise AssertionError((key,value))
print('PUBLISHED-PIXELS PASS: raw/zstd/FFV1 exact bytes, paired ownership, bounded cache, boundaries, ticks')
