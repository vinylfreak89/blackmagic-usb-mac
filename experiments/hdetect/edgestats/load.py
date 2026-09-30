import numpy as np, glob
D = '/private/tmp/claude-501/-Users-vinylfreak89-Documents-blackmagic-usb-mac/8ad5adc7-a74c-4853-97ac-571007154e12/scratchpad/edgestats/'
def load(name, every=1):
    C, P, M = [], [], []
    for x in sorted(glob.glob(D + '%s_*.npz' % name)):
        z = np.load(x); C.append(z['counter']); P.append(z['pos']); M.append(z['m'][::every] if every > 1 else z['m'])
    return np.concatenate(C), np.concatenate(P), np.concatenate(M)
def load2(name):
    """stats and end samples, checked to be the same units in the same order."""
    c, p, M = load(name); c2, p2, E = load('E' + name)
    assert len(c) == len(c2) and (c == c2).all() and (p == p2).all(), name
    return c, p, M, E

def consolidate(name):
    """write <name>.M4.npy (stats columns 0-5... only pl, pr, rise, fall kept at their column positions via a 6-col array)
    and <name>.E.npy once, so several runs can memory-map them."""
    c, p, M, E = load2(name)
    np.save(D + name + '.c.npy', c); np.save(D + name + '.p.npy', p)
    np.save(D + name + '.M6.npy', np.ascontiguousarray(M[..., :6])); np.save(D + name + '.E.npy', E)
def load_mm(name):
    return (np.load(D + name + '.c.npy'), np.load(D + name + '.p.npy'), np.load(D + name + '.M6.npy', mmap_mode='r'),
            np.load(D + name + '.E.npy', mmap_mode='r'))
