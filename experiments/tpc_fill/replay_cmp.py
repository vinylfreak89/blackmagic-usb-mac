# Replay a stretch through the frameserver (the installed build's settings) and summarise what it published.
import sys, subprocess, os, csv
csv.field_size_limit(1 << 30)
def replay(binfile):
    out = binfile[:-4] + '.csv'
    if os.path.exists(out): os.remove(out)
    env = dict(os.environ, FS_REGISTRATION_OFF='1', FS_SHOW_PARTIAL='1')
    r = subprocess.run(['./fsr', binfile, out, '--pace-us', '1000'], env=env, capture_output=True, text=True)
    open(binfile[:-4] + '.out', 'w').write(r.stdout + r.stderr)
    rows = []; hdr = None
    for line in open(out):
        if line.startswith('#'): continue
        if hdr is None: hdr = line.rstrip('\n').split(','); continue
        rows.append(line.rstrip('\n').split(','))
    return hdr, rows, r.stdout + r.stderr
def summary(hdr, rows):
    ix = {h: i for i, h in enumerate(hdr)}
    cs = [int(r[ix['counter_extended']]) for r in rows if r[ix['counter_extended']]]
    res = [int(r[ix['audio_residual_ticks']]) for r in rows if r[ix['audio_residual_ticks']]]
    return dict(rows=len(rows), not_published=sum(1 for r in rows if r[ix['published']] != '1'), kinds={k: sum(1 for r in rows if r[ix['drop_reason']] == k) for k in set(r[ix['drop_reason']] for r in rows)},
                counter_steps=[(a, b) for a, b in zip(cs, cs[1:]) if b - a != 1], audio_steps=[(r[ix['counter_extended']], r[ix['audio_step_samples']]) for r in rows if r[ix['audio_step_samples']] not in ('', '0')],
                residual=[min(res), max(res)] if res else None, no_audio_link=sum(1 for r in rows if r[ix['published']] == '1' and r[ix['audio_residual_ticks']] == ''))
if __name__ == '__main__':
    for b in sys.argv[1:]:
        hdr, rows, txt = replay(b); print(b, summary(hdr, rows))
        for l in txt.splitlines():
            if any(k in l for k in ('holes', 'drop', 'audio', 'published')): print('   ', l[:220])
