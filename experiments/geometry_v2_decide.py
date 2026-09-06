#!/usr/bin/env python3
"""Contract v2 decision layer over geometry_v2_measure.py output. Per field, per unit:
  LOCK    claimed only with confirmation: the measured top is a clean edge (the row above it carries no content) OR the
          comb agrees with the two tops' relative placement (decisive comb, d2-d1 == comb shift). Without it the field
          stays at standard placement (d=0) and is labelled Unconfirmed.
  TRACK   after the lock: the body shift s against the previous unit (decisive: mad < 0.8 x second-best) moves the crop
          by s when the bottom moved by s as well (the account: lines lost/gained at the bottom match); a decisive shift
          with the bottom still is content motion (both fields) or a garbage row change, and the crop holds; a
          non-decisive shift holds with the reason.
  SEGMENT events (splice/signal loss) are inputs (--relock ordinals); on one the lock is dropped and re-acquired.
Output columns match the harness reference (ordinal, counter, f{1,2}_picture_top_line, f{1,2}_bottom_line) plus
applied_d1/applied_d2 and per-field reason, so field_pair_review.py and crops_from_sidecar.py read it directly.
Usage: geometry_v2_decide.py <measure.csv> <out.csv> [--relock N,N,...]"""
import sys, csv, argparse, collections
ap=argparse.ArgumentParser(); ap.add_argument('meas'); ap.add_argument('out'); ap.add_argument('--relock',default='')
A=ap.parse_args(); relock={int(x) for x in A.relock.split(',') if x}
ORIGIN={'1':23,'2':286}
rows=list(csv.DictReader(open(A.meas))); units=collections.OrderedDict()
for r in rows: units.setdefault(r['n'],{})[r['field']]=r
def dec(r): return r['mad']!='' and float(r['mad'])<0.8*float(r['mad2']) and abs(int(r['shift']))<6   # a minimum on the search edge is not a measurement
def combdec(r2): return r2['comb']!='' and float(r2['comb'])<0.8*float(r2['comb2'])
state={'1':dict(lock=False,d=0,bottom=None),'2':dict(lock=False,d=0,bottom=None)}; stats=collections.Counter()
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['ordinal','counter','applied_d1','applied_d2','f1_picture_top_line','f1_bottom_line','f1_reason','f2_picture_top_line','f2_bottom_line','f2_reason'])
first_counter=None
for n,fr in units.items():
    r1,r2=fr['1'],fr['2']; c=int(r1['counter']); first_counter=c if first_counter is None else first_counter; ordinal=c-first_counter
    if ordinal in relock:
        for f in state: state[f]=dict(lock=False,d=0,bottom=None)
    out={}
    for f,r in (('1',r1),('2',r2)):
        S=state[f]; top=int(r['top']); bot=int(r['bottom']); reason=''
        measurable = top>0 and bot>0
        if not S['lock']:
            # ABSOLUTE confirmation (contract §8): a clean textured edge stable over 5 consecutive still units (DEFAULT
            # 5) with the row above it carrying no content, OR a parity-valid caption exactly two lines above the
            # textured top (STANDARD: caption on 21, picture from 23), OR, for this field only, the other field already
            # locked and a decisive comb placing this one relative to it. Comb alone never confirms absolute placement.
            hist=S.setdefault('hist',[])
            if measurable and float(r['top_texture'])>8.0 and (r['shift']=='' or (dec(r) and int(r['shift'])==0)): hist.append(top)
            else: hist.clear()
            reason='Unconfirmed'
            if measurable:
                d_top=top-ORIGIN[f]; cap=r['cap_line']
                # STANDARD: the caption is line 21 and the picture begins on 23; the textured top may read 22's
                # attenuated video one line early, so the caption confirms a top within one line of caption+2 and the
                # standard fixes d
                caption_ok = cap not in ('','multi') and (top-2)<=int(cap)<=(top-1)
                if caption_ok: d_top=int(cap)+2-ORIGIN[f]
                stable = len(hist)>=5 and len(set(hist[-5:]))==1
                other=state['2' if f=='1' else '1']
                comb_ok = other['lock'] and combdec(r2)
                if abs(d_top)<=6 and caption_ok: S.update(lock=True,d=d_top,bottom=bot,top=top); reason='LockedCaption'
                elif abs(d_top)<=6 and stable: S.update(lock=True,d=d_top,bottom=bot,top=top); reason='LockedStable'
                elif comb_ok:
                    d_rel=int(r2['comb_shift'])   # field 2 sits comb_shift lines relative to field 1's placement
                    d_new = other['d']+d_rel if f=='2' else other['d']-d_rel
                    if abs(d_new)<=6: S.update(lock=True,d=d_new,bottom=bot,top=top); reason='LockedComb'
        else:
            cap=r['cap_line']; capd=(int(cap)-(ORIGIN[f]-2)) if cap not in ('','multi') else None
            if measurable and dec(r):
                s=int(r['shift']); dt=(top-S['top']) if S.get('top') else None; db=(bot-S['bottom']) if S['bottom'] is not None else None
                dc=(capd-S['capd']) if (capd is not None and S.get('capd') is not None) else None
                if s==0: reason='Still'
                # a slip is confirmed when BOTH edges moved with the body, or the caption did; one edge alone is the
                # switch line's partial-line jitter or a garbage row (owner: 'if just the head switch jumps, ignorable')
                elif (dt==s and db==s) or dc==s: S['d']+=s; reason='Slip%+d'%s
                elif dt==s or db==s: reason='UnconfirmedSlip(%+d)'%s          # body and one edge moved: logged, not applied
                else: reason='ContentMotion(%+d)'%s                            # the body moved, no edge did: the picture's content moved
                S['bottom']=bot; S['top']=top
            elif measurable: reason='Undecided'
            else: reason='Unmeasurable'
            # the caption is confirmation: when it is visible and disagrees with the tracked placement three units in a
            # row, the chain has drifted and the lock's invariant failed; re-lock from the standard (logged)
            if capd is not None:
                S['capd']=capd
                if capd!=S['d']: S['capmiss']=S.get('capmiss',0)+1; reason+=';CaptionDisagrees(%+d)'%(capd-S['d'])
                else: S['capmiss']=0
                if S.get('capmiss',0)>=3: S['d']=capd; S['capmiss']=0; reason+=';RelockCaption'
            elif cap=='': S['capd']=None
        stats[(f,reason.split('(')[0])]+=1; out[f]=(S['d'],ORIGIN[f]+S['d'],bot if bot>0 else -1,reason)
    w.writerow([ordinal,c,out['1'][0],out['2'][0],out['1'][1],out['1'][2],out['1'][3],out['2'][1],out['2'][2],out['2'][3]])
for f in ('1','2'): print('field',f,{k[1]:v for k,v in sorted(stats.items()) if k[0]==f})
