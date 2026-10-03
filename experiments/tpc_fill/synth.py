# Build one of the target's units from the donor capture's fields. Target pairs fields one field apart:
# target unit c = (donor unit a-1's second-slot field, donor unit a's first-slot field), a = c + OFF.
# Row mapping measured on intact units: target row r (0..262) = donor(a-1) row r+262; target row r (263..524) = donor(a) row r-263.
import numpy as np
PAD = [0, 1, 2, 3, 4, 5, 6, 261, 262, 263, 264, 265, 266, 267, 268, 269, 523, 524]
def synth_rows(a_prev, a_cur, row7):
    """a_prev, a_cur: 525x1440 arrays of donor units a-1 and a; row7: the target's row 7 from the nearest intact unit (the donor has no source for it)."""
    u = np.empty((525, 1440), np.uint8)
    u[0:263] = a_prev[262:525]; u[263:525] = a_cur[0:262]
    u[7] = row7
    u[PAD, 0::2] = 128; u[PAD, 1::2] = 16
    return u
def unit_bytes(counter, rows):
    return b'\x00\x00\xff\xff' + int(counter % 65536).to_bytes(2, 'little') + b'\x01\xe8' + bytes(40) + rows.tobytes()
