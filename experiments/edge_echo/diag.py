# The owner sees rolling diagonal bands in the removed picture.  How much does the removal raise what is already in the capture
# in each frequency band, where the picture is flat?  Spectrum along the line of (frame - five-line-cleaned frame), mid-picture
# rows, captured and removed, and the gain the removal applies at each frequency for that frame's taps.
import sys, numpy as np
import model as M, harness as H, direct as D
np.set_printoptions(linewidth=250, precision=2, suppress=True)
lum = np.load('p2_luma.npy', mmap_mode='r'); A = np.load('w2_p2_am.npy'); t = np.load('d_p2.npz'); Q, direct = t['Q'], t['direct']
fr = np.fft.rfftfreq(512, 1 / 13.5); edges = [0.1, 0.25, 0.35, 0.45, 0.55, 0.7, 1.0, 1.5, 2.5, 4.0]; out = []
def spec(x):                              # line-to-line difference (picture mostly cancels, what changes from line to line stays), columns 100..611
    d = (x[1:] - x[:-1])[:, 100:612] * np.hanning(512); return np.sqrt((np.abs(np.fft.rfft(d, axis=1)) ** 2).mean(0))
for f in range(60, 900, 28):
    y = lum[f].astype(float) - M.BL; x = D.removed(y, Q[f], A[f, 1]); sc = spec(y[20:200]); sr = spec(x[20:200]); g = 1 / np.abs(1 + np.fft.rfft(np.r_[0, Q[f][1:]], 512))
    out.append([A[f, 0]] + [np.sqrt((sr[(fr >= a) & (fr < b)] ** 2).mean() / (sc[(fr >= a) & (fr < b)] ** 2).mean()) for a, b in zip(edges[:-1], edges[1:])] + [g[(fr >= a) & (fr < b)].max() for a, b in zip(edges[:-1], edges[1:])])
out = np.array(out); n = len(edges) - 1; print('bands, MHz:', ['%.2f-%.2f' % (a, b) for a, b in zip(edges[:-1], edges[1:])])
for lo, hi in ((0.45, 0.65), (0.65, 0.8), (0.8, 1.0)):
    s = (out[:, 0] >= lo) & (out[:, 0] < hi)
    if s.sum(): print('reading %.2f-%.2f (%2d frames): line-to-line content, removed / captured: %s' % (lo, hi, s.sum(), np.median(out[s, 1:1 + n], 0))); print('%34s largest gain of the exact undoing in the band: %s' % ('', np.median(out[s, 1 + n:], 0)))
