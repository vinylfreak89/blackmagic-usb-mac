"""Pack the named, provenance-checked static-mask caches for the C reader.

Generated luma stays in scratch. Input caches are made by static_mask_probe.py
through its complete CAP1 walker; this packer does not bless arbitrary captures.
"""
import sys
from pathlib import Path
import numpy as np

cache, destination = map(Path, sys.argv[1:])
with destination.open('xb') as out:
    for name, counters in [('commercial', [6687, 6690, 6700]),
                           ('sp', [13653, 13972]), ('off', [739, 333])]:
        with np.load(cache / (name + '.npz')) as data:
            for counter in counters:
                for c in (counter - 1, counter):
                    a = data[str(c)]
                    assert a.shape == (525, 720) and a.dtype == np.uint8
                    out.write(a.tobytes())
