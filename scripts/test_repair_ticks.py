"""Encoded visible ticks: parity, sparse rows, R/I adjacency, absence and corruption."""
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
from repair_tick_overlay import preserve_tick_lanes, readback_ticks, TICK_COLORS, TICK_X

with tempfile.TemporaryDirectory(prefix='repair-ticks-') as directory:
    directory = Path(directory)
    images = np.full((8, 706, 1000, 3), 12, np.uint8)
    rows, strips = [], []
    for frame in range(8):
        # Empty frame, isolated top/bottom, both fields, adjacent red/orange.
        ticks = [] if frame == 0 else [(j, 'R' if (j+frame)%3 == 0 else 'I')
                                      for j in (0, 1, 2, 4, 10, 101, 102, 478, 479)]
        row = dict(counter_extended=str(frame+100), published='1', frame_top_unit=str(frame+100),
                   frame_d1='0', frame_d2='0')
        for field in (1, 2):
            selected = [(j, a) for j, a in ticks if j%2 == field-1]
            row[f'hretime_lines_f{field}'] = ' '.join(
                f'{(23 if field==1 else 286)+j//2}:{a}' for j, a in selected)
            row[f'hretime_retimed_f{field}'] = str(sum(a == 'R' for _, a in selected))
            row[f'hretime_interpolated_f{field}'] = str(sum(a == 'I' for _, a in selected))
        rows.append(row);strips.append((frame, frame+100, 0, 0))
        for j, a in ticks:
            for x in TICK_X:
                images[frame, j, x:x+5] = TICK_COLORS[a]
    for parity in ('bff', 'tff'):
        for fixed in (False, True):
            output = directory / f'{parity}-{fixed}.mp4'
            deint = f'setfield={parity},bwdif=mode=send_frame:parity={parity}'
            graph = '[0:v]format=yuv422p[t];' + (
                preserve_tick_lanes('t', 'out', deint, 'p') if fixed else f'[t]{deint}[out]')
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                '-s', '1000x706', '-r', '30000/1001', '-i', '-', '-filter_complex', graph,
                '-map', '[out]', '-c:v', 'libx264', '-crf', '14', '-preset', 'medium',
                '-pix_fmt', 'yuv420p', str(output)], input=images.tobytes(), check=True)
            try:
                result = readback_ticks(output, rows, strips)
            except ValueError as exc:
                if fixed: raise
                print(f'OLD_FILTER_REPRODUCED {parity}: {exc}')
            else:
                assert fixed, 'test failed to expose old tick loss'
                assert result['differences'] == 0 and result['frames'] == 8
                print(f'FIXED_FILTER {parity}: {result}')
            if fixed:
                for defect in ('missing', 'extra', 'wrong-type'):
                    wrong = [dict(r) for r in rows]
                    if defect == 'missing':
                        wrong[0].update(hretime_lines_f1='23:I', hretime_interpolated_f1='1')
                    elif defect == 'extra':
                        wrong[1].update(hretime_lines_f1='', hretime_interpolated_f1='0', hretime_retimed_f1='0')
                    else:
                        wrong[1]['hretime_lines_f1'] = wrong[1]['hretime_lines_f1'].replace('23:I', '23:R')
                        wrong[1]['hretime_interpolated_f1'] = str(int(wrong[1]['hretime_interpolated_f1'])-1)
                        wrong[1]['hretime_retimed_f1'] = str(int(wrong[1]['hretime_retimed_f1'])+1)
                    try: readback_ticks(output, wrong, strips)
                    except ValueError: pass
                    else: raise AssertionError(f'{defect} visible tick accepted')
print('REPAIR-TICKS PASS')
