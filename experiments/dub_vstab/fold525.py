# the 525-line fold the landmark is tracked in: per field whose rows are all new (placed.csv from render_placed.py --log),
# each visible row's share of samples at the floor (<= 12; rowstats2.npz from look2.py), the field's median removed and
# scaled by its spread, laid at the row's write time mod 525.  Unseen rows NaN.  -> fold525.npy (525, fields)
import numpy as np, csv, sys
S = sys.argv[1]; R0, R1 = 18, 254
def build(low, rows):
    M = np.full((525, len(rows)), np.nan, np.float32)
    for j, r in enumerate(rows):
        a = low[int(r['field']), R0:R1].astype(float); a = (a - np.median(a)) / a.std()
        M[np.floor(np.mod(float(r['tape_line_of_row_18']) - R0 + np.arange(R0, R1), 525)).astype(int), j] = a
    return M
if __name__ == '__main__':
    rows = [r for r in csv.DictReader(open(S + '/placed.csv')) if r['kind'] == 'all']
    M = build(np.load(S + '/rowstats2.npz')['low'], rows); old = np.load(S + '/fold525.npy') if '--check' in sys.argv else None
    if old is not None: print('same as the saved fold:', np.array_equal(M, old, equal_nan=True))
    else: np.save(S + '/fold525.npy', M)
