# known answer for the outline-repeat fit (or_fit) and the joint removal, before the tape.
# Part A: the independent generator (og_gen: random outlines, cause-first off-air chain), echoes of known delay and
#   strength, the fit's delays found by scanning from guesses 1.5 samples off; truth = the same seed with no echoes.
#   Noise is 0 here: the generator's lines are independent draws (no shared outlines between neighbouring lines), so
#   the neighbour-line instrument cannot be exercised on it; part A uses plain least squares.
# Part B: real programme from a commercial (prerecorded, no multipath) capture, pushed through og_gen's off-air chain
#   with known echoes, then known band-limited noise; the no-echo pass with the same noise is the truth.  Most of that
#   capture is one held picture whose own repeats read 0.03-0.09 at many delays, so it cannot serve as a content floor;
#   the echo is scored as (reading with echo) - (reading of the same fields without it), which cancels the content.  Removal is scored against the no-echo truth (per-line gain and offset fitted, since echoes
#   also move the line's AGC), and the fit is rerun on the corrected fields: copies must fall to the content floor.
# usage: or_ka.py S [A|B|AB]
import numpy as np, sys, multiprocessing as mp
import og_gen as G, or_fit as F
S = sys.argv[1]; PARTS = sys.argv[2] if len(sys.argv) > 2 else 'AB'
NB = [dict(T=30, mag=0.04, phase=60), dict(T=60, mag=0.07, phase=-110), dict(T=77, mag=0.05, phase=25), dict(T=88, mag=0.06, phase=155)]
NULLS = [140, 160, 180, 200, 220, 240, 260, 280]
def okmask(fill, clip): return ~fill & ~clip
IV = True
def sums(Y, OK, Ts, t0=None): return np.stack([F.field_sums(Y[k], OK[k], Ts, t0) for k in range(len(Y))])
def scan(Y, OK, Ts0, half=4.0, step=0.25, passes=2):
    """coordinate ascent on pooled explained energy; one fixed target start so candidates are compared on one set"""
    Ts = list(Ts0); t0 = F.S0 + int(np.ceil(max(Ts0) + half)) + 15
    for _ in range(passes):
        for k in range(len(Ts)):
            grid = np.arange(Ts[k] - half, Ts[k] + half + 1e-9, step); prof = []
            for T in grid:
                tt = Ts[:k] + [T] + Ts[k + 1:]; prof.append(F.solve(sums(Y, OK, tt, t0).sum(0), len(tt))[1])
            Ts[k] = float(grid[int(np.argmax(prof))])
    return Ts
def nullfloor(Y, OK):
    return {T: abs(F.fit(sums(Y, OK, [T]), 1, nboot=0, iv=IV)[0][0]) for T in NULLS}
def resid(A, Tr, ok, sl):
    e = []
    for a, t, m0 in zip(A.reshape(-1, 720), Tr.reshape(-1, 720), ok.reshape(-1, 720)):
        m = m0.copy(); m[:20] = False; X = np.vstack([t[m], np.ones(m.sum())]).T; k = np.linalg.lstsq(X, a[m], rcond=None)[0]
        d = a - (k[0] * t + k[1]); mm = m.copy(); mm[:sl.start] = False; mm[sl.stop:] = False; e.append(d[mm])
    e = np.concatenate(e); return float(np.sqrt(np.mean(e ** 2)))
def report(name, truth, Ts, g, sd, after, floor, res, dsync):
    fmt = lambda v: '%.3f∠%+4.0f' % (abs(v), np.degrees(np.angle(v)) if abs(v) > 1e-9 else 0)
    print('== %s' % name)
    for k, T in enumerate(Ts):
        tv = min(truth, key=lambda e: abs(e[0] - T)) if truth else None
        tv = tv if tv and abs(tv[0] - T) < 3 else None
        print('   echo %7.2f  true %s  found %s  error %.4f  sd %.4f  after removal %.4f'
              % (T, ('%s @%.2f' % (fmt(tv[1]), tv[0])) if tv else '   none          ', fmt(g[k]), abs(g[k] - (tv[1] if tv else 0)), sd[k], abs(after[k])))
    print('   null delays 140-280 (one at a time): max %.4f  median %.4f' % (max(floor.values()), np.median(list(floor.values()))))
    for nm, r0, r1 in res: print('   residual vs echo-free truth, %-12s delivered %.2f codes RMS -> corrected %.2f' % (nm, r0, r1))
    sys.stdout.flush()
def evaluate(name, Y, OK, Ytrue, fill, truth, Ts0, dsync=0.0):
    Ts = scan(Y, OK, Ts0); g, sd, _ = F.fit(sums(Y, OK, Ts), len(Ts), iv=IV)
    out = np.stack([F.remove(Y[k], fill[k], Ts, g, dsync) for k in range(len(Y))])
    after = F.fit(sums(out, OK, Ts), len(Ts), nboot=0, iv=IV)[0]
    res = [(nm, resid(Y, Ytrue, OK, sl), resid(out, Ytrue, OK, sl)) for nm, sl in (('left t<130', slice(20, 130)), ('rest t>=130', slice(130, 715)))]
    return name, truth, Ts, g, sd, after, nullfloor(Y, OK), res, dsync
# ---- part A
def caseA(item):
    name, kw, Ts0 = item; c = G.Case(**kw); r = G.generate(c)
    kw0 = dict(kw); kw0['target'] = (0.0, 0.0, kw['target'][2]); kw0['neighbours'] = (); r0 = G.generate(G.Case(**kw0))
    truth = [(T, g) for T, g in c.echoes(True)]
    return evaluate(name, r['Y'], okmask(r['fill'], r['clip']), r0['Y'], r['fill'], truth, Ts0)
def casesA():
    s = 97000; base = dict(fields=120, rows=60, noise=0); out = []
    def add(name, Ts0, **kw):
        nonlocal s; s += 1; d = dict(base); d.update(kw); d['seed'] = s; out.append((name, d, Ts0))
    off5 = [31.5, 58.5, 78.5, 86.5, 101.5]
    add('tape-like 0.08∠-50 @103, four neighbours', off5, target=(0.08, -50, 103.0), neighbours=NB)
    add('0.20∠+90 @104.5, four neighbours', off5, target=(0.2, 90, 104.5), neighbours=NB)
    add('0.04∠-150 @102.6 alone', [101.0], target=(0.04, -150, 102.6))
    add('no echoes at all (fit five)', off5, target=(0.0, 0, 103.0))
    add('ADVERSARIAL height-proportional source edge at 104.5, no echo', [103.0], target=(0.0, 0, 104.5), source='adversarial')
    add('retime +4.5 (fill), 0.08∠-50 @103 + neighbours', off5, target=(0.08, -50, 103.0), neighbours=NB, retime=4.5)
    add('detector pll + Nyquist 0.6 (model mismatch), 0.08∠-50 @103', off5, target=(0.08, -50, 103.0), neighbours=NB, detector='pll', nyq=0.6)
    add('only 60/77/103 fitted while 30/88 present', [58.5, 78.5, 101.5], target=(0.08, -50, 103.0), neighbours=NB)
    return out
# ---- part B
CY = None
def real_lines(fy):
    """236 rows of real programme (codes) -> 237 contiguous 858-sample lines at 108 MHz in IRE, sync and blanking
    as og_gen draws them, the programme in the window (stream 142 ..); line 0 is history"""
    t = np.arange(G.LINE, dtype=float)
    base = -40 * (G.rc_edge(t, G.FP, 0.35 * 13.5 / 4) - G.rc_edge(t, G.SYNC_END, 0.35 * 13.5 / 4))
    L = np.tile(base, (len(fy) + 1, 1)); L[1:, G.WIN0:] = (fy[:, :G.LINE - G.WIN0] - 1.5) / 2.19
    L[0, G.WIN0:] = L[1, G.WIN0:]
    v = L.ravel(); X = np.fft.rfft(v); X8 = np.zeros(len(v) * G.OS // 2 + 1, complex); X8[:len(X)] = X
    return (np.fft.irfft(X8, len(v) * G.OS) * G.OS).reshape(len(fy) + 1, G.L8)
def real_field(item):
    k, echoes = item; c = G.Case(0); pic = real_lines(CY[k].astype(float))
    out = []
    for e in (echoes, []):
        V = G.chain(pic, c, e, None)[1:] * 2.19
        win = np.concatenate([V, np.concatenate([V[1:, :4], np.zeros((1, 4))], 0)], 1)[:, G.WIN0:G.WIN0 + G.NWIN]
        out.append(win)
    return out
def noise_like(shape, sd, seed):
    if not sd: return np.zeros(shape)
    z = np.random.default_rng(seed).normal(0, 1, shape)
    z = np.real(np.fft.ifft(np.fft.fft(z, axis=-1) * G.skirt(np.fft.fftfreq(shape[-1]) * 13.5, -4.2, 4.2, 1.0), axis=-1))
    return z * sd / z.std()
def partB(pool):
    global IV
    truthE = [(103.0, 0.08 * np.exp(-1j * np.radians(50))), (76.5, 0.05 * np.exp(-1j * np.radians(150))), (60.0, 0.04 * np.exp(-1j * np.radians(60)))]
    Ts = [103.0, 76.5, 60.0]; NF = 120
    res = pool.map(real_field, [(k, truthE) for k in range(NF)], chunksize=4)
    Yc = np.stack([r[0] for r in res]); Y0c = np.stack([r[1] for r in res])
    fmt = lambda v: '%.3f∠%+4.0f' % (abs(v), np.degrees(np.angle(v)))
    for nz in (0, 3, 6):
        z = noise_like(Yc.shape, nz, 11); Y = Yc + z; Y0 = Y0c + z
        OK = (Y > -0.5) & (Y < 253.5); fill = np.zeros_like(OK)
        for iv in (False, True):
            IV = iv
            g = F.fit(sums(Y, OK, Ts), 3, nboot=0, iv=iv)[0]; g0 = F.fit(sums(Y0, OK, Ts), 3, nboot=0, iv=iv)[0]
            out = np.stack([F.remove(Y[k], fill[k], Ts, g - g0, 0.0) for k in range(NF)])
            after = F.fit(sums(out, OK, Ts), 3, nboot=0, iv=iv)[0] - g0
            r = [(nm, resid(Y, Y0, OK, sl), resid(out, Y0, OK, sl)) for nm, sl in (('left t<130', slice(20, 130)), ('rest t>=130', slice(130, 715)))]
            print('== REAL programme + noise %d codes, %s:' % (nz, 'neighbour-line instrument' if iv else 'plain least squares'))
            for k, (T, gt) in enumerate(truthE):
                print('   echo %6.1f  true %s  with-echo %s  content alone %s  difference %s  error %.4f  after removal %.4f'
                      % (T, fmt(gt), fmt(g[k]), fmt(g0[k]), fmt(g[k] - g0[k]), abs(g[k] - g0[k] - gt), abs(after[k])))
            for nm, r0, r1 in r: print('   residual vs echo-free truth, %-12s delivered %.2f codes RMS -> corrected %.2f' % (nm, r0, r1))
            sys.stdout.flush()
    IV = True
if __name__ == '__main__':
    CY = np.load(S + '/clean/commercial_y.npy', mmap_mode='r')
    IV = False                                   # part A workers fork with plain least squares; part B sets its own
    with mp.get_context('fork').Pool(4) as p:
        if 'A' in PARTS:
            for r in p.imap(caseA, casesA()): report(*r)
        if 'B' in PARTS: partB(p)
