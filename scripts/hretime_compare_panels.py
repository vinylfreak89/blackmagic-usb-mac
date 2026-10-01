#!/usr/bin/env python3
"""Display saved worker UYVY buffers; never synthesize a repair.

Manifest: {"actions": {"a": "csv", "b": "csv"}, "cases": [
 {"name": "safe_basename", "capture": "key", "counter": 1, "field": 1,
  "lines": [23, 47], "raw_a": "file", "raw_b": "file",
  "output_a": "file", "output_b": "file", "edges": ["left", "right"]}]}.
Buffers are headerless 525x1440 UYVY from hretime_repair_probe. Counters in its
action CSV are source-unit counters, including reversed pairing. Requires
numpy and Pillow. Output PNGs are exclusive: existing files are not replaced.
"""
import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def generate(manifest, destination):
    cases = manifest['cases']
    keys = {(c['capture'], int(c['counter']), int(c['field'])) for c in cases}
    actions = {}
    for variant, path in manifest['actions'].items():
        with open(path, newline='') as stream:
            for row in csv.DictReader(stream):
                key = (row['capture'], int(row['counter']), int(row['field']))
                if key in keys:
                    indexed = (variant, *key, int(row['line']))
                    if indexed in actions:
                        raise ValueError(f'duplicate source row: {indexed}')
                    actions[indexed] = (row['action'], int(row['shift']))
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    for case in cases:
        name = case['name']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError(f'unsafe output name: {name}')
        lo, hi = map(int, case['lines'])
        if not 4 <= lo <= hi <= 528:
            raise ValueError('NTSC lines must lie in the stored raster')
        data = {}
        for key in ('raw_a', 'raw_b', 'output_a', 'output_b'):
            buf = Path(case[key]).read_bytes()
            if len(buf) != 525 * 1440:
                raise ValueError(f'{key}: expected headerless complete raster')
            data[key] = np.frombuffer(buf, np.uint8).reshape(525, 1440)
        if not np.array_equal(data['raw_a'], data['raw_b']):
            raise ValueError(f'{name}: variants have different input pixels')
        source = (case['capture'], int(case['counter']), int(case['field']))
        for variant in ('a', 'b'):
            for line in range(lo, hi + 1):
                # Crops can include device rows outside the published aperture.
                action, shift = actions.get((variant, *source, line), ('N', 0))
                if action not in ('R', 'I') and not np.array_equal(
                        data['raw_a'][line - 4], data['output_' + variant][line - 4]):
                    raise ValueError(f'{name}/{variant}/{line}: unmarked pixel change')
                if action == 'R' and not shift:
                    raise ValueError(f'{name}/{variant}/{line}: zero retime')
        views = [('full', 0, 720, 1)]
        for side in case.get('edges', []):
            if side not in ('left', 'right'):
                raise ValueError(f'unknown edge: {side}')
            views.append((side, 0 if side == 'left' else 640,
                          80 if side == 'left' else 720, 8))
        for view, x0, x1, scale in views:
            margin, step, header, gap = 152, 14, 34, 14
            height = (hi - lo + 1) * step + header
            image = Image.new('RGB', (margin + (x1 - x0) * scale,
                                      3 * height + 2 * gap), '#202020')
            draw = ImageDraw.Draw(image)
            for block, (variant, title, pixels) in enumerate((
                    ('raw', 'RAW INPUT', data['raw_a']),
                    ('a', '(a) adopted AND', data['output_a']),
                    ('b', 'visible-(b) candidate', data['output_b']))):
                top = block * (height + gap)
                draw.text((8, top + 3), f'{name} | {title} | NTSC {lo}-{hi} | '
                          f'x={x0}..{x1-1}, horizontal {scale}x', fill='white')
                draw.text((8, top + 18), 'line / action / shift; R=retime I=interpolate '
                          'C=zero action N=untouched; native luma, no level remap', fill='#bbbbbb')
                for line in range(lo, hi + 1):
                    action, shift = ('RAW', 0) if variant == 'raw' else actions.get(
                        (variant, *source, line), ('N', 0))
                    y = top + header + (line - lo) * step
                    color = {'R': 'orange', 'I': '#ff7777', 'C': 'cyan',
                             'U': 'magenta'}.get(action, 'white')
                    draw.text((8, y + 1), f'{line:3d}  {action:3s}  {shift:+d}', fill=color)
                    row = pixels[line - 4, 1::2][x0:x1]
                    raster = np.repeat(np.repeat(row[None, :], step, axis=0), scale, axis=1)
                    image.paste(Image.fromarray(raster).convert('RGB'), (margin, y))
            path = destination / f'{name}_{view}.png'
            with path.open('xb') as stream:
                image.save(stream, format='PNG')
            outputs.append(str(path))
    return outputs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(json.loads(args.manifest.read_text()), args.destination), indent=2))
