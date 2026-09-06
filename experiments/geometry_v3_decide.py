#!/usr/bin/env python3
"""Decision layer v3 over geometry_v3_measure.py (contract v2 §8), per field per unit — the commercial-tape stage:
the picture's top is the first recorded row (the deck's raster; VBI-type rows are not yet skipped, fixture-A work)
and its bottom is a per-source constant, the head-switch line minus one, LOCKED from consecutive agreeing units and
confirmed by every later unit's reading: a unit whose reading agrees confirms, one without a reading (dark, no
edges) holds, one that disagrees is counted, and K consecutive disagreeing readings re-lock (a new source).
Before the first lock the top is the measured recorded start (standard 23/286 when there is none) and the bottom
is Unknown (-1, no bar), never a substituted number. Body shift vs the previous unit is reported, not yet applied
(the recorded start answers 'did it move' directly on this tape).
Output columns match field_pair_review.py: ordinal, counter, applied_d1/2, f{1,2}_picture_top_line,
f{1,2}_bottom_line, f{1,2}_reason, plus f{1,2}_switch_line (measured), f{1,2}_lock (locked switch line).
Usage: geometry_v3_decide.py <measure.csv> <out.csv> [--k 3]"""
import sys, csv, argparse, collections
ap=argparse.ArgumentParser(); ap.add_argument('meas'); ap.add_argument('out'); ap.add_argument('--k',type=int,default=3); A=ap.parse_args()
ORIGIN={'1':23,'2':286}
rows=list(csv.DictReader(open(A.meas))); units=collections.OrderedDict()
for r in rows: units.setdefault(r['unit'],{})[r['field']]=r
PEDESTAL=11.0   # recorded black on both tapes sits at ~11 (measured: the band rows' left run and recorded black under the picture); a per-source constant, DEFAULT until measured at lock
W=10            # lock window: the last W eligible readings; lock when >= 60% of them lie within one line of their mode (DEFAULT; ~1/3 s)
st={f:dict(lock=-1,hist=[],rec=None) for f in ('1','2')}; stats=collections.Counter()
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['ordinal','counter','applied_d1','applied_d2','f1_picture_top_line','f1_bottom_line','f1_reason','f2_picture_top_line','f2_bottom_line','f2_reason','f1_band_first','f1_lock','f2_band_first','f2_lock','f1_shift','f2_shift','f1_body_med','f2_body_med'])
def eligible(r):
    """the owner's lock condition: significant, non-dirty luma — the body's median luma above recorded black by more
    than three times the body's own row noise. A sub-black or pedestal-level raster (fade, dark card) never locks."""
    return r['body_med']!='' and float(r['body_med'])>=PEDESTAL+3*float(r['body_ystd'])
def mode(v): return collections.Counter(v).most_common(1)[0][0]
for unit,fr in units.items():
    out={}
    for f in ('1','2'):
        r=fr[f]; S=st[f]; top=int(r['top']); sw=int(r['band_first']); rl=int(r['rec_last']); rf=int(r['rec_first']); reason=''
        if top<=0: top=ORIGIN[f]; reason='NoRecordedRegion'
        # the reading is the owner's definition: the first row below the body whose left OR right edge falls outside
        # the body's own edge variance (side-agnostic). It reads the partial line when the other head's content
        # differs at the switch side, else the first band row. A reading at the clip line is not a head switch
        # (the band always has rows below the switch) and never locks.
        if sw>0 and sw>=rl: sw=-1; reason=reason or 'NoBand'
        # the lock's invariant is the recorded region (the deck's raster); when it changes the source changed
        if S['lock']>0 and rf>0 and S['rec']!=(rf,rl): S['lock']=-1; S['hist'].clear(); reason=reason or 'RecordedRegionChanged'
        if S['lock']<0:
            if sw>0 and eligible(r): S['hist'].append(sw)
            elif not eligible(r): S['hist'].clear()
            h=S['hist'][-W:]
            if len(h)>=W:
                md=mode(h); near=[x for x in h if abs(x-md)<=1]
                if len(near)>=0.6*W: S['lock']=md; S['rec']=(rf,rl); reason=reason or 'Locked'   # the band's first row; the switch line is the row above it
            if S['lock']<0: reason=reason or ('Acquiring' if (sw>0 and eligible(r)) else ('Hold' if sw<0 else 'NotEligible'))
        else:
            if sw<0: reason=reason or 'Hold'
            elif abs(sw-S['lock'])<=1: reason=reason or 'Confirmed'
            else: reason=reason or 'Disagree(%d)'%sw       # logged; the lock holds until its invariant fails
        # bottom = the last line inside the edge variance = the partial line (harness reference convention: the
        # switch lands inside it; the rows below carry the other head)
        bottom=(S['lock']-1) if S['lock']>0 else -1   # the partial line = the last line inside the edge variance (reference convention)
        d=top-ORIGIN[f]
        stats[(f,reason.split('(')[0])]+=1; out[f]=(d,top,bottom,reason,sw,S['lock'],r['shift'],r['body_med'])
    w.writerow([unit,fr['1']['counter'],out['1'][0],out['2'][0],out['1'][1],out['1'][2],out['1'][3],out['2'][1],out['2'][2],out['2'][3],out['1'][4],out['1'][5],out['2'][4],out['2'][5],out['1'][6],out['2'][6],out['1'][7],out['2'][7]])
for f in ('1','2'): print('field',f,{k[1]:v for k,v in sorted(stats.items()) if k[0]==f})
