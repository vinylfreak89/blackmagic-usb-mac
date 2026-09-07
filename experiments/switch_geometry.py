#!/usr/bin/env python3
"""Per-unit, per-field geometry under contract v3 (docs/geometry_first_engine.md §10) with every threshold derived
from the unit's own distributions or from physics, none fitted to a tape (owner, 2026-09-07 04:20: "variances should
be non content specific").
Per field of every exact unit:
  blank    the field's regenerated blanking rows: luma noise sigma_b, chroma noise c_b
  recorded a row whose chroma noise exceeds 2x c_b (the measured blank/recorded gap: max 1.48x vs min 2.02x)
  textured a segment (55 samples) whose row-above std exceeds 4 sigma_b
  per row r against the row above: lagmed (median |best lag| over textured segments, -24..24), dm (mean |diff|),
           spike (max |diff|), width (samples at half height around the spike)
  body     the picture rows from top+20 to top+200: their own max lagmed M_lag and max dm M_dm are the field's own
           variance of alignment; nothing inside the picture exceeds them by definition
  shifted  lagmed > M_lag and dm > M_dm                      (the other head: time-shifted beyond the picture's own spread)
  peak     spike > mean + 5 sigma of the row's own |diff| (statistics: < 1 false spike per 700-sample row) and
           width <= 12 samples (physics: the head-switch transient is a few hundred ns, i.e. a few samples at 13.5 MHz;
           picture edges measured >= 20 wide) on a row that is not shifted, directly above a shifted row
  switch   the first row from the body downward that is shifted, or that carries a peak with the next row shifted
  top      the first recorded row that is above black (luma > blank + 6 sigma_b) [VBI-type rows not yet skipped]
  reliable rows = top .. switch-1; band = switch .. last recorded row; closure = reliable + band vs 240
Usage: switch_geometry.py <capture> <out.csv> [--repair] [--units a,b,c (verbose rows)]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from cc608_decode import decode as cc608
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
ap=argparse.ArgumentParser(); ap.add_argument('cap'); ap.add_argument('out'); ap.add_argument('--repair',action='store_true',help='fields paired one later (V-stabilize-off capture): field 1 = this unit slot 2, field 2 = next unit slot 1')
ap.add_argument('--units',default=''); ap.add_argument('--only',action='store_true',help='process only the --units (test mode)'); A=ap.parse_args(); VERB={int(x) for x in A.units.split(',') if x}
SLOT={1:(16,279),2:(279,525)}     # unit rows of each slot (line 20.. / 283..); blank reference rows 7..15 / 270..278
def field_arrays(R,slot):
    a,b=SLOT[slot]; Y=R[a:b,1::2].astype(np.float32); C=np.stack([R[a:b,0::4],R[a:b,2::4]],axis=1).astype(np.float32)
    bl=R[a-9:a-1]; by=bl[:,1::2].astype(np.float32); bc=np.stack([bl[:,0::4],bl[:,2::4]],axis=1).astype(np.float32)
    return Y,C,float(by.mean()),float(max(by.std(),0.5)),float(max(bc.std(),0.3))
def rowfeat(row,prev,sig_b,ped_lvl,by_m=None,sig_n=0.0):
    lags=[]
    for a in range(30,690-55+1,55):
        b=a+55
        if float(prev[a:b].std())<4*sig_b: continue
        c=[(float(np.abs(row[a:b]-prev[a+s:b+s]).mean()),s) for s in range(-24,25)]; lags.append(min(c,key=lambda x:x[0])[1])
    d=np.abs(row-prev); dm=float(d[30:690].mean()); ds=float(d[30:690].std()); x=int(d[10:710].argmax())+10; sp=float(d[x])
    half=sp/2; l=x; r=x
    while l>0 and d[l-1]>=half: l-=1
    while r<719 and d[r+1]>=half: r+=1
    al=[abs(v) for v in lags]; med=float(np.median(lags)) if len(lags)>=3 else None
    # whole-row alignment (blind-check method, 2026-09-07): over the row's textured span, SAD at every lag -24..24; r =
    # SAD(best)/SAD(0). Picture rows: |lag| <= 1.2 and r >= 0.94 (measured on 71 full-content rows); the other head's
    # rows: r 0.39-0.89 at |lag| >= 2. A ratio, so independent of the picture's contrast.
    # the span = where BOTH rows carry texture (a partial line has content over part of the row only)
    # the span = where BOTH rows carry content above the field's own pedestal (a partial line has content over part
    # of the row only; the pedestal's own noise must not extend the span)
    cont=(row>ped_lvl)&(prev>ped_lvl); span=np.nonzero(cont[24:696])[0]
    wlag=0; wr=1.0
    if len(span)>=60 and float(row[24:696].std())>=4*sig_n and float(prev[24:696].std())>=4*sig_n:   # both rows textured above the field's noise; a flat row has no alignment to measure
        a=24+int(span[0]); b=24+int(span[-1])+1
        sads=[(float(np.abs(row[a:b]-prev[a+t:b+t]).mean()),t) for t in range(-24,25)]; best=min(sads,key=lambda x:x[0]); wlag=best[1]; wr=best[0]/max(sads[24][0],1e-6)
    uniform = med is not None and abs(med)>=2 and sum(1 for v in lags if abs(v-med)<=2)>=2*len(lags)/3   # a whole-row time shift: the other head (the subagent's rule); flagging inside the picture varies along the row
    # the row above's own horizontal structure at the spike: a vertical picture edge there makes a narrow |diff| spike
    # from one-sample jitter; the RF transient sits where the row above is locally flat
    lo,hi=max(0,x-8),min(720,x+9); above_range=float(prev[lo:hi].max()-prev[lo:hi].min())
    # leading flat run: from sample 3 (past any sync-like spike at 0..2), the samples staying within 3 sigma_b of the
    # level at sample 3..8, ended by a step of >= 6 sigma_b; its length in samples
    # the run's level: the median of samples 6..40 (past any sync-like spike at the row start); the run extends while
    # samples stay within 6x the blank noise of it (a pedestal row's noise is ~2x the blank's); it ends at a step up
    lvl=float(np.median(row[6:40])); run=6
    while run<719 and abs(float(row[run])-lvl)<=6*sig_b: run+=1
    run=run-6 if (run<719 and float(row[run])-lvl>=6*sig_b and lvl<=ped_lvl) else 0   # the run is blanking/black, not a flat picture level (commercial counter 6657: a flat grey row at 17.5 ended by its own noise read run 19)
    # the horizontal-blanking dip: a timed line begins with samples at the blank level (1..3); the other head's line,
    # with V-stabilize off, starts with content at sample 0 (its blanking is elsewhere in the line)
    dip_absent = float(row[0:7].min())>ped_lvl
    # blanking inside the row: the longest run of samples (24..696) at the decoder's blank level (within 6 sigma_b of
    # the field's own blank rows). The other head's line arrives with its horizontal blanking interval somewhere inside
    # the row (owner: the head switch always lands timing in the horizontal blanking region); a timed picture row has
    # its blanking outside the 720 samples. Its length is bounded by NTSC: longer than a sync pulse alone (4.7 us = 64
    # samples) and shorter than any blanking interval could be (200 samples = 14.8 us; H blanking is 10.9 us). Census
    # (commercial, 920 units): band rows 834/954 and 1259/1323 carry one, the row before the switch 0/531 and 0/535;
    # picture rows carry one in 0.4% and never within 4 rows of the switch (the scan from the clip is contiguous).
    blank_run=0; blank_x=-1
    if by_m is not None:
        m=np.abs(row[24:696]-by_m)<=6*sig_b
        if m.any():
            e=np.flatnonzero(np.diff(np.concatenate(([0],m.astype(np.int8),[0]))))
            k=int((e[1::2]-e[0::2]).argmax()); blank_run=int(e[1::2][k]-e[0::2][k]); blank_x=24+int(e[0::2][k])   # where along the row the other head's blanking begins
    return dict(blank_run=blank_run,blank_x=blank_x,lagmed=(float(np.median(al)) if len(lags)>=3 else None),n=len(lags),dm=dm,dsig=ds,spike=sp,x=x,width=r-l+1,uniform=uniform,above_range=above_range,lead_run=run,wlag=wlag,wr=wr,dip_absent=dip_absent)
# the record is flushed per unit (Python 3.14 buffers 128 KiB, ~600 rows, before the first write)
OUT=open(A.out,'w',newline=''); w=csv.writer(OUT); w.writerow(['unit','counter','field','top','S_first_shifted','how','peak_x','partial_evidence','reliable_to_S','band_from_S','last_rec','closure','S_wlag','S_r','body_lag_max','body_r_min','M_run','M_spk','blank_y','sig_b','S_tests','band_tests','lock_state','switch_lock','band_comparator','band_rows_obs','band_class','band_counts','first_comparator','first_counts','disc_x'])
PED={1:None,2:None}   # the carried pedestal per field
# LOCKS BY RUNNING COUNT (owner, 2026-09-07: "No magic numbers. It should be derived and stabilized. ie, check the number
# of times that level has appeared. If it's appeared more often than any other level, then it becomes the comparator
# and replaces the previous comparator"). A comparator is the value seen most often so far; a value whose count passes
# the comparator's replaces it. No window, no threshold. Two comparators per field:
#  band: the head-switch band's row count S..clip. "The number of switch lines below the top line either stays constant
#        or decreases. The top switch line should be the only variable one as that's the actual area of travel." Per
#        unit: count == comparator or comparator-1 is the travel; larger is 'band+' (the switch read on a picture row);
#        smaller with the top still is 'dropped' (the picture under a clamped top); smaller with the top moved is
#        'fell-out'. The switch line under the lock sits 240 - comparator rows below the top in every unit.
#  first: the state of the first recorded row (row 3 of the slot: line 23 / 286): 'black22' when it is sub-black and flat
#        (the tape's black line 22 with the field displaced) or 'picture'. A lone sub-black first row is the black line
#        22 only when the comparator says the source shows one there; where the comparator says picture (the commercial
#        tape, whose dark first lines are crushed picture black) it is picture.
# Lock state: 'locked' once a comparator exists; 'acquiring' before the first observation. The record carries each
# comparator's count and the runner-up's count, so the stability of every claim is visible per unit.
CTR={}; LASTTOP={}
class RunMode:
    """a comparator by running count in a FIXED array (owner: "keep a fixed number. If it falls below that number it drops
    out and the entire array shifts. No dynamic memory allocation!!! (In the real C engine)"): SLOTS entries of
    (value, count) kept in count order. A hit increments its entry and bubbles it up; a new value takes a free slot with
    count 1, or, with the array full, decrements the last slot's count — when that reaches zero the entry drops out, the
    array shifts, and the new value takes the freed slot. The comparator is slot 0. SLOTS is a capacity (memory), not a
    decision constant."""
    SLOTS=8
    def __init__(self): self.v=[None]*self.SLOTS; self.n=[0]*self.SLOTS
    def add(self,x):
        if x is None: return
        for i in range(self.SLOTS):
            if self.v[i]==x:
                self.n[i]+=1
                while i>0 and self.n[i]>self.n[i-1]:                       # bubble up: the array shifts
                    self.v[i],self.v[i-1]=self.v[i-1],self.v[i]; self.n[i],self.n[i-1]=self.n[i-1],self.n[i]; i-=1
                return
        for i in range(self.SLOTS):
            if self.v[i] is None: self.v[i]=x; self.n[i]=1; return          # a free slot
        self.n[-1]-=1                                                        # full: the last entry's count falls
        if self.n[-1]<=0: self.v[-1]=x; self.n[-1]=1                        # it dropped out; the new value takes the slot
    def top(self):
        if self.v[0] is None: return None,0,0
        return self.v[0],self.n[0],(self.n[1] if self.v[1] is not None else 0)
BAND={1:RunMode(),2:RunMode()}; FIRST={1:RunMode(),2:RunMode()}
def lock_update(f,obs):
    """obs = this unit's observed band count S..clip or None; returns (state, comparator, class, count, runner-up)"""
    BAND[f].add(obs); comp,n,n2=BAND[f].top()
    if comp is None: return 'acquiring',None,'',0,0
    if obs is None: cls='no-picture'
    elif obs>comp: cls='band+'
    elif obs>=comp-1: cls='travel'
    else: cls='short'
    return 'locked',comp,cls,n,n2
def process_unit(u,RU,RN):
    """one unit: RU = this unit's raster, RN = the next unit's (needed only with --repair)"""
    if A.only and u not in VERB: return
    for f in (1,2):
        R=RU if (f==1 or not A.repair) else RN; slot=(2 if (f==1 and A.repair) else (1 if (f==2 and A.repair) else f))
        Y,C,by_m,sig_b,c_b=field_arrays(R,slot); base=20 if slot==1 else 283   # line = row + base (slot numbering)
        ym=Y.mean(axis=1); thr=by_m+6*sig_b
        # a recorded row carries tape noise the regenerated rows do not: chroma noise above 2x the blank's, OR luma above
        # the blank (a flat grey field's rows, luma 17-20 with chroma noise only 1.7x the blank's — commercial unit 800 —
        # are recorded); the Shuttle's hard padding (Y16 C128, zero variance in both) is neither
        ystd=Y[:,40:680].std(axis=1); cstd=C.std(axis=(1,2))
        padding=(ystd==0)&(cstd==0)
        rec=(~padding)&((cstd/c_b>2.0)|(ym>thr)|(ystd>=4*sig_b))
        recrows=[r for r in range(3,Y.shape[0]) if rec[r]]                      # rows 0..2 = lines 20/21/22 regenerated
        # top = the first recorded row that carries picture: above the blank, not flat (the tape's black line 22 sits
        # at luma 4-7 with std < 4 sigma_b: a VBI row, never a top), and not a CEA-608 waveform (the tape's line 21 or
        # 20 pushed into the pass-through region by a displacement)
        # the tape's own black (its line 22, and recorded black under the picture) sits at the pedestal or below it;
        # the pedestal is the field's own: the lowest flat recorded row above the blank (the band's other-head black,
        # std < 4 sigma_b), else the blank itself. A picture row is above the pedestal by more than the blank noise.
        # recorded black (the pedestal): the field's own flat recorded row when it has one (the other head's black in
        # the band); otherwise the last pedestal seen on this source (a per-source constant measured when available,
        # never assumed); otherwise the blank
        # the pedestal is the other head's black: the run of flat recorded rows contiguous with the clip (the band's
        # bottom), never any flat row of the field — a flat dark picture (EP unit 3: lines 253-260 at luma 26, std 1-2,
        # above the band's pedestal 13) is picture, and a flat grey field (commercial unit 800, luma 17-20, std 1.3) has
        # no pedestal of its own
        flat_rec=[]
        for r in reversed(recrows):
            if ym[r]>thr and float(Y[r,40:680].std())<4*sig_b: flat_rec.append(float(ym[r]))
            else: break
        if flat_rec: PED[f]=min(flat_rec)
        ped=PED[f] if PED[f] is not None else by_m
        # a picture row is recorded and not a VBI row. VBI rows are recognised by signature, never by level: a CEA-608
        # waveform (the tape's line 21/20), a textured row uncorrelated with the row below (caption fragments, the smeared
        # XDS bar, run-in lines), or an isolated flat row before a textured row (the tape's black line 22 on the SP
        # recording, luma 4-7 before the picture; the EP recording's dim row at 18 before the picture at 107). A flat row
        # before a flat row is picture (a flat grey field; a dark band). No black level or pedestal enters the top rule
        # (2026-09-07: with the pedestal unknown on the commercial tape, its dark first line at luma 4-5 read as 'bright'
        # and the top wandered between 23 and 25 on a stable picture).
        # the field's own noise: the median over its middle rows of the std of adjacent-SAMPLE differences /sqrt(2). VHS
        # luma is band-limited near 3 MHz, so at 13.5 MHz adjacent samples of real content differ little and the
        # difference is dominated by noise; adjacent-ROW differences (tried first) carry the picture's vertical detail
        # and read 12-15 on the SP recording against a tape noise of 2-3
        mid=[r for r in range(40,200) if rec[r]]
        sig_n=float(np.median([float(np.diff(Y[r,24:696]).std()) for r in mid]))/np.sqrt(2) if len(mid)>=20 else 4*sig_b
        def corr_rows(r,q):
            # the maximum over horizontal lags -24..24 of the correlation between rows r and q: a torn or time-shifted
            # picture row (every field top of the V-stabilize-off pass; the EP recording's tears) correlates at its lag;
            # a VBI row correlates with the picture at no lag (zero-lag only, 2026-09-07 run C: the raw pass's tops read
            # 287-289 in 68 units and unmeasurable in 57 where the rows show 286)
            if q<0 or q>=Y.shape[0]: return 0.0
            a=Y[r,48:672]-Y[r,48:672].mean(); na=float(np.sqrt((a*a).sum())); best=0.0
            if na==0: return 0.0
            for t in range(-24,25):
                b=Y[q,48+t:672+t]; b=b-b.mean(); d=na*float(np.sqrt((b*b).sum()))
                if d>0: best=max(best,float((a*b).sum()/d))
            return best
        def corr_below(r): return corr_rows(r,r+1)
        # a VBI row correlates with NEITHER neighbour; a picture row at a horizontal edge correlates with one side (EP
        # counter 2303: line 26 at 41.5/26.1 correlates 0.00 with 27 and with 25 above, so the row-below test alone
        # excluded it and the field had no run of three picture rows)
        def corr_either(r): return max(corr_rows(r,r-1) if r-1>=3 and rec[r-1] else 0.0, corr_below(r))
        # the premise of the correlation and texture rules: adjacent picture lines correlate IN THIS FIELD. On a flat or
        # dark scene the picture rows are noise-only (commercial counter 6645: body rows correlate at 0.1-0.3, row std
        # 1-3 against a noise of 0.7), so 'textured' and 'uncorrelated' describe noise; the rules stand down and the top
        # is the first recorded row that is not a waveform and not sub-black (run D read 25/287 in 107/109 stable
        # units of the commercial tape with the rules active there)
        body_corr=float(np.median([corr_rows(r,r+1) for r in range(40,200,8) if rec[r] and rec[r+1]])) if sum(1 for r in range(40,200,8) if rec[r] and rec[r+1])>=10 else 0.0
        redundant=body_corr>=0.5
        def textured(r): return redundant and float(Y[r,24:696].std())>=4*sig_n
        def vbi_type(r): return redundant and textured(r) and corr_either(r)<0.5          # 0.5: a fitted default (measured VBI 0.01-0.36, picture 0.87-0.99)
        # the level rule, in its physical form: on a tape with setup the tape's black line 22 sits BELOW the tape's own
        # black (the pedestal, the other head's black in the band: SP recording 3-7 against 11.4), which no picture row
        # does; so a SUB-BLACK row before a row that is not sub-black is VBI, and a run of sub-black rows is picture (a
        # dark band, owner ruling 2026-09-06). On a tape without setup (black at blanking: the commercial tape) the
        # pedestal is the blank and nothing is sub-black, so a dark first line is picture — the constancy of that tape
        # says the same (line 23 carries grey picture at counter 6842). The earlier 'bright = above pedestal + 3 sigma_b'
        # rule read the commercial's near-black first lines as bright and its top wandered 23/24/25 on a stable picture.
        def subblack(r): return ym[r]<ped-3*sig_b
        r0=recrows[0] if recrows else None
        first_state=(('black22' if (subblack(r0) and float(Y[r0,24:696].std())<4*sig_n+2*sig_b) else 'picture') if (r0 is not None and not cc608(Y[r0])[0]) else None)
        FIRST[f].add(first_state); first_comp=FIRST[f].top()[0]
        def picture_row(r):
            if not rec[r] or cc608(Y[r])[0] or vbi_type(r): return False
            if subblack(r):
                if first_comp=='picture': return True                     # this source shows picture at its first row: a dark first line is crushed black
                return (r+1<Y.shape[0] and rec[r+1] and subblack(r+1)) or (rec[r-1] and subblack(r-1))   # a sub-black row inside or ending a sub-black band is picture; a LONE one before the picture is the tape's black line 22 (the band's last row read as VBI before this: commercial counter 6672, top 25)
            if not redundant: return True
            return textured(r) or not (r+1<Y.shape[0] and rec[r+1] and textured(r+1))   # a flat row before a textured row is VBI (the EP recording's dim isolated row), before a flat row picture
        bright=lambda r: not subblack(r)   # diagnostics only
        # the top begins a run of three picture rows (a lone waveform row before a black row is VBI: a damaged caption,
        # the tape's line 20 data)
        # the top lies within the first four recorded rows: the tape's VBI can occupy at most lines 20-22 of the pass-
        # through region (§2), three rows; a picture whose first picture-like row is deeper than that has a black top and
        # its top is unmeasurable, not a brightness edge
        top=next((r for r in recrows[:4] if picture_row(r) and picture_row(r+1) and picture_row(r+2)),None)
        if u in VERB:
            for r in recrows[:6]: print(f'  top-diag u{u} f{f} L{r+base}: mean {ym[r]:5.1f} std {float(Y[r,24:696].std()):5.1f} rec {int(rec[r])} cc608 {int(bool(cc608(Y[r])[0]))} textured {int(textured(r))} corr {corr_below(r):.2f}/{corr_either(r):.2f} bright {int(bright(r))} picture {int(picture_row(r))} | sig_n {sig_n:.2f} ped {ped:.1f} body_corr {body_corr:.2f}')
        if top is None or len(recrows)<60:
            st,held,cls,n,n2=lock_update(f,None); fc,fn,fn2=FIRST[f].top()
            w.writerow([u,CTR[u],f,-1,-1,'no-picture',-1,'',0,0,-1,'','','',-1,-1,-1,-1,round(by_m,2),round(sig_b,2),'','',st,-1,(held if held is not None else -1),-1,cls,f'{n}/{n2}',fc or '',f'{fn}/{fn2}','']); continue
        last_rec=recrows[-1]
        ped_lvl=ped+6*sig_b
        feats={r:rowfeat(Y[r],Y[r-1],sig_b,ped_lvl,by_m,sig_n) for r in range(top+1,last_rec+1)}
        feats2={r:rowfeat(Y[r],Y[r-2],sig_b,ped_lvl,by_m,sig_n) for r in range(top+2,last_rec+1)}   # against the row two above: a settled other-head row matches its predecessor but not the picture
        body=[feats[r] for r in range(top+20,min(top+200,last_rec-10)) if feats[r]['lagmed'] is not None]
        body2=[feats2[r] for r in range(top+20,min(top+200,last_rec-10)) if r in feats2 and feats2[r]['lagmed'] is not None]
        M_lag2=max(ft['lagmed'] for ft in body2) if body2 else 1.0; M_dm2=max(ft['dm'] for ft in body2) if body2 else 20.0
        # the field's own variance: the body rows' own maxima (nothing inside the picture exceeds them by definition)
        M_lag=max(ft['lagmed'] for ft in body) if body else 1.0; M_dm=max(ft['dm'] for ft in body) if body else 20.0
        M_run=max(ft['lead_run'] for ft in body) if body else 8       # the picture rows' own leading blank run (the H-blanking dip)
        narrow=[ft['spike'] for ft in body if ft['width']<=12 and ft['above_range']<ft['spike']/2]; M_spk=max(narrow) if narrow else 0.0   # the picture's own narrow specks
        body_r=min(ft['wr'] for ft in body) if body else 1.0; body_lag=max(abs(ft['wlag']) for ft in body) if body else 1   # the field's own envelope, reported
        M_lag=max(ft['lagmed'] for ft in body) if body else 1.0; M_dm=max(ft['dm'] for ft in body) if body else 20.0
        def flat(ft,r): return float(Y[r,40:680].std())<4*sig_b and ym[r]>thr and ym[r]<=ped+6*sig_b           # a pedestal row (the other head's black): flat AT the pedestal, not any flat row
        # the other head's rows come in two shapes: a uniform whole-row time shift (the blind check's envelope: picture
        # |lag| <= 1.2, r >= 0.94), or a torn row whose lag varies along the line (no single lag fits, r stays near 1)
        # but whose segment lags and row difference exceed anything the picture's own rows show; plus the pedestal row
        # and the intruded-blanking row
        def torn(ft,two=False):
            ml,md=(M_lag2,M_dm2) if two else (M_lag,M_dm)     # each pass against its own body envelope (commercial counter 6907: the two-above pass read seven picture rows as torn against the one-above maxima)
            return ft['lagmed'] is not None and ft['lagmed']>ml and ft['dm']>md
        M_dip=sum(1 for ft in body if ft['dip_absent'])   # picture rows never lack the dip; reported
        def blanked(ft): return 64<=ft['blank_run']<=200   # the other head's horizontal blanking inside the row
        def step(ft,r,two):
            # a time-base step: the row's lag against the row above is also its lag against the row two above (both
            # above rows are in time); a slanted picture feature doubles its lag two rows up (EP counter 1967: lines
            # 253-258 lag 3-5 against the row above, 6-10 against two above, read as band before this)
            if not (abs(ft['wlag'])>=2 and ft['wr']<=0.90): return False
            other=(feats.get(r) if two else feats2.get(r))
            return other is None or abs(other['wlag']-ft['wlag'])<=1
        def shifted(ft,r,two=False): return step(ft,r,two) or (torn(ft) if not two else False) or flat(ft,r) or ft['lead_run']>M_run+8 or ft['dip_absent'] or blanked(ft)   # the two-above pass carries no torn test: two rows apart the picture's own detail exceeds the body envelope (commercial counters 6907, 6943 read seven picture rows as torn)   # (the upward scan from the clip keeps a dip-less row inside the picture from ever being taken as the band)
        def peak(ft,r): return ft['spike']>M_spk and ft['spike']>ft['dm']+5*ft['dsig'] and ft['width']<=12 and ft['above_range']<ft['spike']/2 and not shifted(ft,r)
        # S = the first row from the body downward that is time-shifted / intruded beyond the field's own spread (the
        # first row that belongs entirely to the other head). The switch lands either inside S-1 (a partial line) or at
        # S's boundary; that one-row ambiguity is the band's uncertainty (contract v3 §10.4) and is reported with the
        # evidence for S-1, never resolved here by a threshold: partial evidence = a narrow spike on a flat background
        # (its height relative to the picture's own narrow specks) and/or the row's alignment departing in its later
        # segments.
        sw=None; how='none'; px=-1; ev=''
        # the band is contiguous at the bottom of the field: scan UP from the last recorded row while rows are shifted
        # or pedestal; S = the top of that run (picture rows with motion can also show a whole-row lag, but they are not
        # contiguous with the clip)
        def band_row(r): return shifted(feats[r],r) or (r in feats2 and shifted(feats2[r],r,True))
        def tests(r):
            ft=feats[r]; f2=feats2.get(r)
            a=''.join(k for k,v in (('W',step(ft,r,False)),('T',torn(ft)),('F',flat(ft,r)),('R',ft['lead_run']>M_run+8),('D',ft['dip_absent']),('B',blanked(ft))) if v)
            b=''.join(k for k,v in (('W',step(f2,r,True)),('T',False),('F',flat(f2,r)),('R',f2['lead_run']>M_run+8),('D',f2['dip_absent']),('B',blanked(f2))) if v) if f2 else ''
            return a+('/2'+b if b else '')
        r=last_rec
        while r>top+20 and band_row(r): r-=1
        if r<last_rec: sw=r+1; how='shifted'
        if sw is not None and sw-1 in feats:
            pf=feats[sw-1]; spk_rank=(pf['spike']/M_spk) if M_spk>0 else 0.0
            narrow_flat = pf['width']<=12 and pf['above_range']<pf['spike']/2 and pf['spike']>pf['dm']+5*pf['dsig']
            ev=f"spike {pf['spike']:.0f}@{pf['x']} w{pf['width']} rank {spk_rank:.2f} narrowflat {int(narrow_flat)} wlag {pf['wlag']} r {pf['wr']:.2f}"
            if narrow_flat and spk_rank>=1.0: px=pf['x']; how='shifted+peak_above'
        reliable=(sw-top) if sw is not None else (last_rec-top+1); band=(last_rec-sw+1) if sw is not None else 0
        clipr=(262 if slot==1 else 525); obs=(clipr-(sw+base)+1) if sw is not None else None   # the observed band count S..clip
        st,held,cls,n,n2=lock_update(f,obs); fc,fn,fn2=FIRST[f].top()
        if cls=='short' and obs is not None: cls='dropped' if (LASTTOP.get(f)==top) else 'fell-out'   # rows lost: with the top still, the picture dropped under a clamped top; with the top moved, the field fell out of the raster
        LASTTOP[f]=top
        swl=(top+base+240-held) if held is not None else -1                   # the switch line under the lock: 240 - max rows below the top, so it moves with the picture
        if cls in ('band+','dropped','fell-out') and px>=0: cls+='(peak)'
        # the horizontal position of the timing discontinuity at S-1 / S / S+1: 'row:blank_x/lead_run_end/transient_x'
        def discx(r):
            if r not in feats: return ''
            ft=feats[r]; return f"{r+base}:{ft['blank_x']}/{(6+ft['lead_run']) if ft['lead_run']>0 else -1}/{ft['x'] if ft['spike']>M_spk else -1}"
        disc='|'.join(discx(r) for r in ((sw-1,sw,sw+1) if sw is not None else ()))
        lockcols=[st,swl,(held if held is not None else -1),(obs if obs is not None else -1),cls,f'{n}/{n2}',fc or '',f'{fn}/{fn2}',disc]
        w.writerow([u,CTR[u],f,top+base,(sw+base) if sw is not None else -1,how,px,ev,reliable,band,last_rec+base,reliable+band,(feats[sw]['wlag'] if sw is not None else ''),(round(feats[sw]['wr'],2) if sw is not None else ''),body_lag,round(body_r,2),M_run,round(M_spk,0),round(by_m,2),round(sig_b,2),(tests(sw) if sw is not None else ''),('|'.join(f'{r+base}:{tests(r)}' for r in range(sw,last_rec+1)) if sw is not None else '')]+lockcols)
        if u in VERB:
            sys.stdout.flush(); print(f'unit {u} field {f}: top L{top+base} switch {("L%d"%(sw+base)) if sw is not None else "none"} ({how}) peak_x {px} reliable {reliable} band {band} last_rec L{last_rec+base} | body max lag {M_lag} dm {M_dm:.1f} lead_run {M_run} narrow-spike {M_spk:.0f}')
            for r in range(max(top+20,last_rec-9),last_rec+1):
                ft=feats[r]; f2=feats2.get(r)
                why=''.join(k for k,v in (('W',step(ft,r,False)),('T',torn(ft)),('F',flat(ft,r)),('R',ft['lead_run']>M_run+8),('D',ft['dip_absent']),('B',blanked(ft))) if v)
                why2=''.join(k for k,v in (('W',step(f2,r,True)),('T',False),('F',flat(f2,r)),('R',f2['lead_run']>M_run+8),('D',f2['dip_absent']),('B',blanked(f2))) if v) if f2 else '-'
                print(f'    L{r+base}: mean {ym[r]:5.1f} std {float(Y[r,40:680].std()):4.1f} lagmed {ft["lagmed"]} n {ft["n"]} dm {ft["dm"]:5.1f} dsig {ft["dsig"]:5.1f} wlag {ft["wlag"]} r {ft["wr"]:.2f} spike {ft["spike"]:5.0f}@{ft["x"]} w{ft["width"]} run {ft["lead_run"]} band {int(band_row(r))} [{why}|{why2}] peak {int(peak(ft,r))}')
# the walk: units are processed as they arrive, holding at most two rasters (the capture is never loaded whole — a
# 608-unit capture is 460 MB per process and four of them drove the host into swap, 2026-09-07)
buf=bytearray(); pend=[]; N=[0]
def emit(u):
    c=int.from_bytes(u[4:6],'little'); R=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE); i=N[0]; N[0]+=1; CTR[i]=c
    if not A.repair: process_unit(i,R,None); OUT.flush(); return
    pend.append((i,R))
    if len(pend)==2: process_unit(pend[0][0],pend[0][1],pend[1][1]); del pend[0]; OUT.flush()
def on_video(p):
    buf.extend(p)
    while True:
        i=buf.find(MARK)
        if i<0: return
        if i>0: del buf[:i]
        j=buf.find(MARK,4)
        if j<0: return
        if j==UNIT: emit(bytes(buf[:UNIT]))
        del buf[:j]
try: walk_tagged(A.cap,on_video=on_video,progress=False)
except RuntimeError as e: print('walk ended:',str(e)[:60])
n=N[0]-(1 if A.repair else 0)
print('units',n,'->',A.out)
