# The echo by direct division, from the ghost-cancelling reference the broadcast carries on line 19 / 282: a frequency sweep on a
# 30 IRE pedestal, sent in both polarities over an eight-field sequence (rows 5 and 13 of the VBI arrays).
#   echo of a frame, relative to the capture's weakest-echo state = transform(frame's sweep) / transform(weak-state sweep)
# No model and no fitted numbers.  Known answer (a made-up echo on the reference sweep and bar): exact.  On the real lines it takes
# out about half of the test bar's echo, and a quarter of the sweep arrives in a form that does not flip with its polarity:
# the chain after the echo is not linear (README, "The line-19 sweep").
# Run from the scratch directory:   python3 gcr.py   -> reference sweep, per-passage sweeps (p2_sweep.npy, first_sweep.npy), the bar test
import sys
import numpy as np, barread as B
np.set_printoptions(linewidth=260, precision=3, suppress=True)
NF = 1024; fr = np.fft.rfftfreq(NF, 1 / 13.5); R19, R282 = 5, 13; SEG = slice(40, 560); WIN = np.clip((np.arange(720) - 20) / 25.0, 0, 1) * np.clip((600 - np.arange(720)) / 40.0, 0, 1);   # flat over the sweep and its echoes; eased only where there is nothing LO, HI = 0.12, 2.9
LO, HI = 0.12, 2.9
def sweeps(vbif, floor=3.0):          # per frame, from its OWN two fields (line 19 and line 282 carry opposite polarities).
    # The standard puts the sweep on a 30 IRE pedestal swinging to -10 and +70 IRE; the capture cuts off everything below blanking, so
    # the bottoms of the downward swings are missing in whichever field swings down there.  A sample at the floor is left out and the
    # other field's (which swings up there) is used alone: sweep = polarity x (line - its own pedestal).  The cut is the capture's
    # last stage and has no memory, so every sample above the floor is good.
    v = np.load(vbif, mmap_mode='r'); n = v.shape[0]; num = np.zeros((n, 720)); den = np.zeros((n, 720))
    for r in (R19, R282):
        x = v[:, r].astype(float); ped = np.median(x[:, 500:640], 1, keepdims=True); c = x - ped; pol = np.sign(c[:, 70:112].sum(1))[:, None]; ok = x > floor; num += np.where(ok, pol * c, 0); den += ok
    sweeps.clipped = float((den[:, 60:460] < 2).mean()); return num / np.maximum(den, 1)
def shift(y, dlt): return np.fft.irfft(np.fft.rfft(y, NF) * np.exp(-2j * np.pi * np.fft.rfftfreq(NF) * dlt), NF)[:len(y)]
def offset(y, tmpl):                    # sideways offset of y against a template (samples), from the phase slope where both are strong
    a = np.fft.rfft(y * WIN, NF) * np.conj(np.fft.rfft(tmpl * WIN, NF)); m = (fr > 0.8) & (fr < 2.4); w = np.abs(a[m]); ph = np.unwrap(np.angle(a[m])); f = fr[m]
    A = np.c_[f, np.ones(len(f))] * w[:, None]; sl = np.linalg.lstsq(A, ph * w, rcond=None)[0][0]; return -sl * 13.5 / (2 * np.pi)
def align(d, half=10):
    out = d.copy(); off = np.zeros(len(d))
    for it in range(2):
        tm = out.mean(0) if it == 0 else None
        for k in range(len(d)):
            t = tm if it == 0 else out[max(0, k - half):k + half + 1].mean(0); o = offset(out[k], t); out[k] = shift(out[k], -o); off[k] += o
    return out, off
def spectrum(y): return np.fft.rfft(y * WIN, NF)
def echo(dk, Dref, lag0=-40, lag1=140):  # the division; kept up to where the reference fades (2.9 MHz), and to lags an echo can have (eased ends)
    Hq = spectrum(dk) / Dref; band = 0.5 + 0.5 * np.cos(np.pi * np.clip((fr - HI) / 0.5, 0, 1)); Hq = 1 + (Hq - 1) * band
    h = np.fft.irfft(Hq, NF); n = np.arange(NF); lag = np.where(n > NF // 2, n - NF, n); g = np.clip((lag - lag0 + 10) / 10.0, 0, 1) * np.clip((lag1 + 20 - lag) / 20.0, 0, 1); d0 = h[0]; h = h * g; h[0] = d0; return np.fft.rfft(h, NF)
if __name__ == '__main__':
    lo, off_lo = align(sweeps('lo_vbi.npy')); L, g = B.lines('lo_vbi.npy'); gm = B.running_median(np.nanmean(g, 1)); weak = gm < 0.15; print('weak passage: %d frames, %d under 0.15; sideways jitter of the sweep line %.2f samples rms' % (len(lo), weak.sum(), off_lo.std()))
    ref = lo[weak].mean(0) if weak.sum() >= 30 else lo.mean(0); np.save('gcr_ref.npy', ref); Dref = spectrum(ref)
    print('reference sweep spectrum every 0.25 MHz:', np.round([np.abs(Dref)[np.argmin(np.abs(fr - f))] for f in np.arange(0.25, 4.01, 0.25)], 0))
    for name in ('p2_vbi.npy', 'vbi_luma.npy'):
        d, off = align(sweeps(name)); np.save(name.replace('_vbi', '_sweep').replace('vbi_luma', 'first_sweep'), d); nz = np.sqrt(np.mean(np.diff(d, axis=0)[:, SEG] ** 2) / 2)
        print('%s: sideways jitter %.2f samples rms; noise of one frame\'s sweep %.2f codes rms (from frame differences)' % (name, off.std(), nz))
        for k in (100, 300, 420, 540, 560, 700):
            Hq = echo(d[k], Dref); A = np.abs(Hq); m = (fr > 0.2) & (fr < 2.5); i = np.argmin(A[m]); print('   frame %d: least left %.3f at %.2f MHz; |H| at 0.25,0.5,0.75,1,1.5,2,2.5: %s' % (k, A[m][i], fr[m][i], np.round([A[np.argmin(np.abs(fr - f))] for f in (0.25, 0.5, 0.75, 1, 1.5, 2, 2.5)], 2)))
    # ---- tests on things the sweep never saw: the frame's own test bar (line 18 / 281), and the picture's right border
    import bartest as GB
    ref_s = np.load('gcr_ref.npy'); Dref = spectrum(ref_s)
    for vbif, sw, parf in (('p2_vbi.npy', 'p2_sweep.npy', 'reflect_par_p2.npy'), ('vbi_luma.npy', 'first_sweep.npy', 'reflect_par_first.npy')):
        d = np.load(sw); Lb, gb = B.lines(vbif); S = np.hypot(*np.load(parf)[:, :2].T); rows = []
        for k in range(2, len(d) - 2, 6):
            Hq = echo(d[k], Dref); ys = GB.bar_lines(Lb, gb, k, N=2)
            for j in range(2):
                if ys[j] is None or np.isnan(ys[j]).mean() > 0.2: continue
                y = np.nan_to_num(ys[j], nan=1.0); x = GB.remove_line(y, Hq); rows.append([S[k]] + [np.sqrt(np.mean((v_ - GB.ref[j])[(B.TB >= a) & (B.TB <= b)] ** 2)) for v_ in (y, x) for _, a, b in GB.PARTS])
        o = np.array(rows); print('%s: the test bar against its weak-echo reference, captured -> after removal with the sweep\'s echo (direct division)' % vbif)
        for a, b in ((0, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0), (1.0, 9)):
            s_ = (o[:, 0] >= a) & (o[:, 0] < b)
            if s_.sum() >= 4: print('  strength %.1f-%.1f (%3d): ' % (a, b, s_.sum()) + ' | '.join('%s %.3f -> %.3f' % (GB.PARTS[i][0], np.median(o[s_, 1 + i]), np.median(o[s_, 5 + i])) for i in range(4)))
