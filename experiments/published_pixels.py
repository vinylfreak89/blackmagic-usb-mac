"""Read frameserver_replay's actual 720x480 UYVY output, in sidecar unit order.

The dump is optionally lossless FFV1/Matroska or zstd-compressed during replay
(requires ffmpeg/ffprobe or the zstd CLI). This is a lossless spool,
not another registration or repair implementation. Only two transport units are
cached: reversed pairing takes f1 of the next unit and f2 of the current unit.
"""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np


class PublishedPixels:
    SIZE = 480 * 1440

    def __init__(self, path, rows):
        self.units = [int(r['counter_extended']) for r in rows
                      if r.get('published') == '1']
        if len(set(self.units)) != len(self.units):
            raise ValueError('duplicate published source unit')
        self.position = {c:i for i,c in enumerate(self.units)}
        self.process = None
        if Path(path).suffix == '.zst':
            self.process = subprocess.Popen(['zstd', '-q', '-d', '-c', str(path)], stdout=subprocess.PIPE)
            self.stream = self.process.stdout
        elif Path(path).suffix == '.mkv':
            meta = json.loads(subprocess.check_output(['ffprobe','-v','error',
                '-show_entries','stream=codec_type,codec_name,width,height,pix_fmt',
                '-of','json',str(path)]))['streams']
            if (len(meta) != 1 or meta[0].get('codec_name') != 'ffv1' or
                    meta[0].get('width') != 720 or meta[0].get('height') != 480 or
                    meta[0].get('pix_fmt') != 'yuv422p'):
                raise ValueError('published Matroska spool must be lossless 720x480 yuv422p FFV1')
            self.process = subprocess.Popen(['ffmpeg','-v','error','-i',str(path),
                '-f','rawvideo','-pix_fmt','uyvy422','pipe:1'],stdout=subprocess.PIPE)
            self.stream = self.process.stdout
        else:
            self.stream = open(path, 'rb')
        self.cache = OrderedDict()
        self.count = 0
        self.digest = hashlib.sha256()

    def _read(self):
        if self.count >= len(self.units):
            raise ValueError('read beyond published sidecar units')
        data = bytearray()
        while len(data) < self.SIZE:
            block = self.stream.read(self.SIZE-len(data))
            if not block:
                raise ValueError(f'truncated published pixels at unit {self.units[self.count]}: {len(data)}/{self.SIZE}')
            data.extend(block)
        self.digest.update(data)
        c = self.units[self.count]
        self.count += 1
        self.cache[c] = np.frombuffer(bytes(data), np.uint8).reshape(480,1440)
        while len(self.cache) > 2:
            self.cache.popitem(last=False)

    def unit(self, counter):
        if counter not in self.position:
            raise ValueError(f'unit {counter} absent from published sidecar')
        while counter not in self.cache:
            if self.count >= len(self.units) or self.position[counter] < self.count:
                raise ValueError(f'published pixel request out of order: {counter}')
            self._read()
        return self.cache[counter]

    def frame(self, top, bottom):
        # Read bottom first; reversed pairing then advances exactly one unit.
        b = self.unit(bottom)
        t = self.unit(top)
        out = np.empty((480,1440),np.uint8)
        out[::2] = t[::2]
        out[1::2] = b[1::2]
        return out

    def finish(self):
        while self.count < len(self.units):
            self._read()  # includes unpaired boundary units, not invented frames
        if self.stream.read(1):
            raise ValueError('extra pixels beyond published sidecar units')
        self.stream.close()
        if self.process and self.process.wait() != 0:
            raise ValueError('published pixel decompression failed')
        return dict(units=self.count, bytes=self.count*self.SIZE, sha256=self.digest.hexdigest())

    def close(self):
        self.stream.close()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()


def repair_ticks(row):
    """Frame-owned NTSC actions -> published woven row; C/U never get ticks."""
    out = []
    for field in (1,2):
        origin = (23 if field == 1 else 286) + int(row[f'frame_d{field}'])
        seen = set()
        for token in row.get(f'hretime_lines_f{field}', '').split():
            line, action = token.split(':')
            line = int(line)
            if line in seen or action not in ('R','I','U','C','S'):
                raise ValueError(f'invalid repair action {token}')
            seen.add(line)
            if action not in ('R','I','S'):
                continue
            j = 2*(line-origin)+field-1
            if not 0 <= j < 480:
                raise ValueError(f'repair outside published aperture: {token}')
            out.append((j, action))
        for action, column in (('R','retimed'),('I','interpolated')):
            expected = int(row.get(f'hretime_{column}_f{field}') or 0)
            actual = sum(a == action and j%2 == field-1 for j,a in out)
            if actual != expected:
                raise ValueError(f'repair tick count mismatch: field {field} {column} {actual}/{expected}')
    return out
