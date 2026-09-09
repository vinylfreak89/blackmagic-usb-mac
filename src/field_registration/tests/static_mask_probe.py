#!/usr/bin/env python3
"""Diagnostic only. Named raw units and synthetic pan; no engine changes.

Capture fixtures are read with the existing strict CAP1 walker. Scratch stores
only the named luminance rasters/panels. All numeric fixture choices below are
experiment parameters, not production thresholds or registration rules.
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'experiments' / 'geometry_oracle'))
from oracle import walk_exact_units

CASES = {
    'commercial': ('/Users/vinylfreak89/Documents/blackmagic-usb-mac/captures/composite_program_30s.tpc', [6687,6690,6700]),
    'sp': ('/private/tmp/hw-session/w_300s_aligned.tpc', [13653,13972]),
    'off': ('/private/tmp/hw-session/sp_vstab_off_aligned.tpc', [739,333]),
}

def load_case(name, out):
    path, wanted = CASES[name]
    cache = out / (name + '.npz')
    if cache.exists():
        with np.load(cache) as z:
            return {int(k):z[k] for k in z.files}
    keep = set(wanted) | {v-1 for v in wanted}
    got = {}
    def consume(u, index):
        del index
        ctr = int.from_bytes(u[4:6], 'little')
        if ctr in keep:
            if ctr in got: raise RuntimeError(f'duplicate counter {ctr}')
            got[ctr] = np.frombuffer(u, np.uint8)[48:].reshape(525,1440)[:,1::2].copy()
    walk_exact_units(Path(path), consume)
    if set(got) != keep: raise RuntimeError(f'missing counters: {keep-set(got)}')
    np.savez(cache, **{str(k):v for k,v in got.items()})
    return got

def panels(name, got, out):
    units = CASES[name][1]
    # One row per golden: previous and current fields, at nominal crops.
    im = Image.new('L', (1440, len(units)*260), 0)
    draw = ImageDraw.Draw(im)
    for j,ctr in enumerate(units):
        for i,c in enumerate([ctr-1,ctr]):
            a=got[c];woven=np.empty((480,720),np.uint8)
            woven[::2]=a[19:259];woven[1::2]=a[282:522]
            tile=Image.fromarray(woven).resize((720,240))
            im.paste(tile,(720*i,j*260+20));draw.text((720*i,j*260),f'{name} counter {c} nominal 23/286',fill=255)
    im.save(out/(name+'_pairs.png'))

def energies(f1,f2,mask=None):
    # Common support for all five candidates. Raw pixel positive-product metric.
    y=np.arange(3,237);a=f1[y,24:696].astype(float);c=f1[y+1,24:696].astype(float)
    e=[]
    for q in range(-2,3):
        b=f2[y+q,24:696].astype(float)
        v=np.maximum((a-b)*(c-b),0)
        e.append(float(np.mean(v if mask is None else v[mask])))
    return e

def fields(r):
    return np.stack((r[19:259],r[282:522])).astype(float)

def summarize(e):
    s=np.argsort(e)
    margin=e[s[1]]/e[s[0]] if e[s[0]] else ('infinite' if e[s[1]] else 'tie')
    return {'energies':e,'best':int(s[0])-2,'margin':margin}

def calibrated(name,got):
    # Visually inspected stationary picture patches in the pair panels. The
    # commercial patch contains printed detail; SP/off patches are the static
    # background, NOT generated blanking. Coordinates are fixture annotations.
    ctr=CASES[name][1][0]
    roi={'commercial':(60,140,240,640),'sp':(40,80,80,200),'off':(15,45,400,496)}[name]
    y0,y1,x0,x1=roi
    a,b=fields(got[ctr]),fields(got[ctr-1])
    delta=np.abs(a.reshape(2,240,90,8).sum(-1)-b.reshape(2,240,90,8).sum(-1))
    sample=delta[:,y0:y1,x0//8:x1//8]
    thresholds=sample.max(axis=(1,2))
    report={'calibration_counter':ctr,'roi_field_y_x':roi,'samples_per_field':int(sample[0].size),
            'sum_quantiles_by_field':[np.quantile(s,[0,.5,.95,.99,1]).tolist() for s in sample],
            'tolerance_sum_by_field':thresholds.tolist(),'tests':[]}
    for ctr in CASES[name][1]:
        a,b=fields(got[ctr]),fields(got[ctr-1])
        mask=temporal_mask(a,b,thresholds)
        masked=energies(*a,mask) if mask.any() else None
        report['tests'].append({'counter':ctr,'maskless':summarize(energies(*a)),
            'masked':summarize(masked) if masked is not None else None,
            'support':int(mask.sum()),'possible':int(mask.size)})
    return report,thresholds

def golden_panels(name,got,out):
    units=CASES[name][1];im=Image.new('L',(1500,len(units)*140),0);draw=ImageDraw.Draw(im)
    for j,ctr in enumerate(units):
        for i,q in enumerate(range(-2,3)):
            r=got[ctr];woven=np.empty((480,720),np.uint8)
            woven[::2]=r[19:259];woven[1::2]=r[282+q:522+q]
            im.paste(Image.fromarray(woven[140:260,200:500]),(i*300,j*140+20))
            draw.text((i*300,j*140),f'{name} ctr {ctr} d {q:+}',fill=255)
    im.save(out/(name+'_weaves.png'))

def temporal_mask(current,previous,thresholds):
    delta=np.abs(current.reshape(2,240,90,8).sum(-1)-previous.reshape(2,240,90,8).sum(-1))
    still=delta<=thresholds[:,None,None]
    y=np.arange(3,237)
    mask=still[0,y] & still[0,y+1]
    # Match the production test's adjacent-field static stencil on ONE common
    # support across five shifts. Repeat block decisions for raw pixel energy.
    for k in range(-3,4):mask &= still[1,y+k]
    return np.repeat(mask,8,axis=1)[:,24:696]

def pan(noise_samples=None):
    # Continuous piecewise-linear aperiodic vertical signal; 4 full-frame lines
    # of motion per field interval, no change to picture/blanking geometry.
    rng=np.random.default_rng(1729)
    knots=rng.uniform(30,220,(600,90))
    def scene(y):
        k=np.floor(y/2).astype(int);t=(y/2-k)[:,None]
        return np.repeat((1-t)*knots[k]+t*knots[k+1],8,axis=1)
    y=np.arange(240)*2+40
    a=scene(y);b=scene(y+1-4) # later field is four full-frame rows lower
    previous_a=scene(y+8);previous_b=scene(y+1+4)
    noise=(rng.uniform(-0.5,0.5,(4,240,720)) if noise_samples is None else
           np.repeat(rng.choice(noise_samples,(4,240,90)),8,axis=2))
    a,b,previous_a,previous_b=[v+n for v,n in zip((a,b,previous_a,previous_b),noise)]
    e=energies(a,b);order=np.argsort(e)
    return {'energy':e,'best':int(order[0])-2,'margin':e[order[1]]/e[order[0]],
            'geometry_shift':0,'pan_full_frame_lines_per_field':4,
            'temporal_abs_mean':float(np.mean(np.abs(a-previous_a))),
            'same_pan_arrays':(a,b,previous_a,previous_b)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--case',choices=CASES)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if a.case:
        got=load_case(a.case,a.out);panels(a.case,got,a.out)
        print(a.case,'loaded',sorted(got),flush=True)
    else:
        reports={};thresholds={}
        for name in CASES:
            got=load_case(name,a.out)
            reports[name],thresholds[name]=calibrated(name,got)
            golden_panels(name,got,a.out)
        # Calibration is frozen above BEFORE constructing the pan control.
        r=pan();aa,bb,pa,pb=r.pop('same_pan_arrays')
        for name,t in thresholds.items():
            m=temporal_mask(np.stack((aa,bb)),np.stack((pa,pb)),t)
            r[name+'_masked']={'support':int(m.sum()),'possible':int(m.size),
                              'reading':summarize(energies(aa,bb,m)) if m.any() else None}
        reports['pan']=r
        reports['pan_empirical_difference_noise']={}
        for name in CASES:
            got=load_case(name,a.out);c=reports[name]['calibration_counter']
            y0,y1,x0,x1=reports[name]['roi_field_y_x']
            diff=fields(got[c])-fields(got[c-1])
            samples=diff.reshape(2,240,90,8).mean(-1)[:,y0:y1,x0//8:x1//8].ravel()
            p=pan(samples);p.pop('same_pan_arrays')
            reports['pan_empirical_difference_noise'][name]=p
        expected={'commercial':{6687:0,6690:0,6700:0},'sp':{13653:-1,13972:0},'off':{739:0,333:1}}
        for name in CASES:
            for t in reports[name]['tests']:
                assert t['maskless']['best']==t['masked']['best']==expected[name][t['counter']]
        assert r['geometry_shift']==0 and r['best']==2 and r['margin']>2
        assert not r['commercial_masked']['support']
        assert r['sp_masked']['reading']['best']==2 # residual false match: NOT a pass for the mask
        assert all(p['best']==2 and p['margin']>2 for p in reports['pan_empirical_difference_noise'].values())
        print(json.dumps(reports,indent=2))
        print('seven_raw_goldens_preserved: PASS; high_margin_pan_false_minimum_reproduced: PASS; sparse_mask_failure_reproduced: PASS',file=sys.stderr)

if __name__=='__main__':main()
