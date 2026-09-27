"""Progressive repair annotations and encoded-luma audit of BOTH margin lanes.

Picture deinterlacing must not deinterlace single-row metadata. Restore the two
original narrow tick lanes after deinterlacing; all picture pixels are unchanged.
The audit reads the visible ticks, not a duplicate machine-readable tick strip.
"""
import subprocess

import numpy as np

from published_pixels import repair_ticks

TICK_X = (173, 823)
TICK_COLORS = {'I': (255, 40, 40), 'R': (255, 165, 0)}


def preserve_tick_lanes(source, target, deinterlacer, prefix):
    """FFmpeg graph fragment, labels without brackets; native 480-row review."""
    p = prefix
    return (f'[{source}]split=3[{p}l][{p}r][{p}d];'
            f'[{p}l]crop=8:480:172:0[{p}lc];'
            f'[{p}r]crop=8:480:822:0[{p}rc];'
            f'[{p}d]{deinterlacer}[{p}di];'
            f'[{p}di][{p}lc]overlay=x=172:y=0:format=yuv422:shortest=1[{p}o];'
            f'[{p}o][{p}rc]overlay=x=822:y=0:format=yuv422:shortest=1[{target}]')


def readback_ticks(path, rows, strips):
    """Check every visible R/I tick location/type and every absent tick, both sides.

    Native limited-range Y avoids 4:2:0 chroma mixing adjacent red/orange rows.
    Nominal BT.601 Y codes for background/I/R are 26/105/158. Nearest-code
    decoding permits at most 20 codes of lossy error, well below half the gaps.
    Missing, extra, wrong-type, swapped-field and shifted ticks all fail.
    """
    frames = {int(r['counter_extended']): r for r in rows
              if r.get('published') == '1' and r.get('frame_top_unit')}
    graph = ('[0:v]split[l][r];[l]crop=4:480:174:0,extractplanes=y[lc];'
             '[r]crop=4:480:824:0,extractplanes=y[rc];[lc][rc]hstack[out]')
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(path),
        '-filter_complex', graph, '-map', '[out]', '-pix_fmt', 'gray',
        '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    counts = {'I': 0, 'R': 0}
    try:
        for index, (_, counter, _, _) in enumerate(strips):
            block = proc.stdout.read(480 * 8)
            if len(block) != 480 * 8:
                raise ValueError(f'truncated tick readback at frame {index}')
            pixels = np.frombuffer(block, np.uint8).reshape(480, 8)
            expected = np.zeros(480, np.uint8)
            for j, action in repair_ticks(frames[counter]) if counter in frames else []:
                expected[j] = 1 if action == 'I' else 2
                counts[action] += 1
            for lane, offset in enumerate((0, 4)):
                values = np.median(pixels[:, offset:offset+3], axis=1)
                distances = np.abs(values[:, None] - np.array([26, 105, 158]))
                actual = distances.argmin(axis=1)
                bad = np.flatnonzero((actual != expected) | (distances.min(axis=1) > 20))
                if len(bad):
                    raise ValueError(f'tick mismatch frame {index} counter {counter} lane {lane}: '
                                     f'rows={bad.tolist()} expected={expected[bad].tolist()} '
                                     f'observed={actual[bad].tolist()} Y={values[bad].tolist()}')
        if proc.stdout.read(1):
            raise ValueError('extra encoded frames beyond tick audit timeline')
        if proc.wait() != 0:
            raise ValueError('ffmpeg tick decode failed')
    finally:
        proc.stdout.close()
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
    return dict(frames=len(strips), lanes=2, interpolated=counts['I'], retimed=counts['R'], differences=0)
