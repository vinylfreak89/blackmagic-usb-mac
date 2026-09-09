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
  top      the first RECORDED row that is not a VBI row (contract section 3; VBI rows are excluded by signature at
           line 228, never by level) -- 'the first picture row is the first picture row' (owner)
  reliable rows = top .. switch-1; band = switch .. last recorded row; closure = reliable + band vs 240
Usage: switch_geometry.py <capture> <out.csv> [--repair] [--units a,b,c (verbose rows)]"""
import sys, os, csv, argparse, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from packet_capture_reader import walk_tagged
from cc608_decode import decode as cc608, RUNIN_MIN_CODES
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
MAXLAG=24                                              # the alignment search is +-MAXLAG samples (1.8 us at 13.5 MHz)
# DERIVED from the search itself, not typed. At the extreme lag the two rows overlap over span-MAXLAG samples, so
# requiring the extreme-lag comparison to still use at least half the span gives span >= 2*MAXLAG. The old value
# was a typed 60. Measured before replacing it: sweeping the floor to 40 and to 100 leaves capture 1's reference
# byte-identical, 0 cells changed of 12,880 at both, and the floor is monotone -- raising it can only reject rows
# -- so identical output at 40 and 100 PROVES no row has a span in [40,100) and every value in that range gives
# the same answer. 48 lies inside it, so this derivation is a no-op here rather than a retuning.
SPAN_FLOOR=int(os.environ.get('SG_SPAN_FLOOR', 2*MAXLAG))
# DEFAULT OFF, measured 2026-09-10. With torn selecting, an independent census puts the first relocated-blanking
# row exactly on S in 963 of 1,013 readings; with it off, 1,009 of 1,013. The 50-reading error class collapses to
# 4, and every remaining one is inside the same 6880-6963 window, so the 845 readings outside that window stay
# exact either way -- improvement inside, no regression outside. Contract rule 6 says the same thing
# independently: "Horizontal tearing is not a geometry event", and torn selects rows whose lag varies along the
# line, which is what horizontal tearing is. Set SG_TORN_SELECTS=1 to restore it for a comparison.
TORN_SELECTS=os.environ.get('SG_TORN_SELECTS','0')!='0'
# STEP_SELECTS: whether a whole-row lag alone may make a row the switch line. DEFAULT OFF, measured 2026-09-10.
# The independent census reads 963 of 1,013 with both step and torn selecting, 1,009 with torn off, and 1,012
# with both off; the single survivor is 6907 f1, inside the same window, so the 845 readings outside it are exact
# throughout. The concern before measuring was that step might be load-bearing on the line-TBC-off regime, where
# the contract records whole-line displaced rows -- but capture 1 IS that regime (CLAUDE.md: composite_program_30s
# was taken with V-stabilize/line TBC OFF), so the case at risk is the case measured, and it improves.
# The physics says the same: TBC-off rows are displaced a median of 192 samples while the lag search is bounded
# at +-MAXLAG = 24, so step CANNOT see a real head-switch displacement -- it aliases. What finds those rows is the
# physical relocated-blanking test. Step, like torn, can only fire on sub-switch-scale timing wobble, and contract
# rule 6 says horizontal tearing is not a geometry event. Set SG_STEP_SELECTS=1 to restore it for a comparison.
STEP_SELECTS=os.environ.get('SG_STEP_SELECTS','0')!='0'
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
        c=[(float(np.abs(row[a:b]-prev[a+s:b+s]).mean()),s) for s in range(-MAXLAG,MAXLAG+1)]; lags.append(min(c,key=lambda x:x[0])[1])
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
    # SPAN_FLOOR is an INSTRUMENT LIMIT, not a source property, and it is derived from the lag search rather than
    # typed -- see its definition. Sweepable by SG_SPAN_FLOOR, because "is this constant carrying a decision" is a
    # question to answer by measurement rather than to argue from the fact that a number looks arbitrary.
    if len(span)>=SPAN_FLOOR and float(row[24:696].std())>=4*sig_n and float(prev[24:696].std())>=4*sig_n:   # both rows textured above the field's noise; a flat row has no alignment to measure
        a=24+int(span[0]); b=24+int(span[-1])+1
        sads=[(float(np.abs(row[a:b]-prev[a+t:b+t]).mean()),t) for t in range(-MAXLAG,MAXLAG+1)]; best=min(sads,key=lambda x:x[0]); wlag=best[1]; wr=best[0]/max(sads[MAXLAG][0],1e-6)
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
    # The row's own horizontal blanking at each END of the delivered window. An NTSC line is 858
    # samples with 720 delivered and 147 of horizontal blanking (contract section 2), so 147 - 138 =
    # 9 samples of a correctly timed row's own blanking fall inside the window. A row whose right
    # part arrived from the other head has its blanking elsewhere and does not return to the blank
    # level at the end. Counted against the FIELD's own blanking rows, never a typed level.
    end_run = 0
    if by_m is not None:
        k = 719
        while k >= 0 and abs(float(row[k]) - by_m) <= 6 * sig_b:
            end_run += 1; k -= 1
    lead_blank = (by_m is not None) and abs(float(row[0:3].min()) - by_m) <= 6 * sig_b
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
    return dict(end_run=end_run,lead_blank=lead_blank,blank_run=blank_run,blank_x=blank_x,lagmed=(float(np.median(al)) if len(lags)>=3 else None),n=len(lags),dm=dm,dsig=ds,spike=sp,x=x,width=r-l+1,uniform=uniform,above_range=above_range,lead_run=run,wlag=wlag,wr=wr,dip_absent=dip_absent)
# the record is flushed per unit (Python 3.14 buffers 128 KiB, ~600 rows, before the first write)
OUT=open(A.out,'w',newline=''); w=csv.writer(OUT); w.writerow(['unit','counter','field','top','d','T','S','switch_lines','below','lost','height','how','peak_x','partial_evidence','caption_line','insert_data','line22','l22_level','comb_shift','comb_ratio','comb_static','lock_state','band_class','applied','band_comparator','band_counts','switch_total_comparator','switch_total_counts','events','band_tests','disc_x','blank_y','sig_b'])
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
SEEN21={1:False,2:False}   # line 21 evidence seen in this source (a caption off the insert or data on the insert): line 22 is defined one line below it
class RunMode:
    """a comparator by running count in a FIXED array (owner: "keep a fixed number. If it falls below that number it drops
    out and the entire array shifts. No dynamic memory allocation!!! (In the real C engine)"): SLOTS entries of
    (value, count) kept in count order. A hit increments its entry and bubbles it up; a new value takes a free slot with
    count 1, or, with the array full, replaces the last (least-counted) entry, which drops out. Counts never decrement;
    entries move only by their own counts rising past their neighbours. The comparator is slot 0. SLOTS is a capacity
    (memory), not a decision constant."""
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
        self.v[-1]=x; self.n[-1]=1                                           # full: the least-counted entry drops out; the new value takes its slot
    def top(self):
        if self.v[0] is None: return None,0,0
        return self.v[0],self.n[0],(self.n[1] if self.v[1] is not None else 0)
BAND={1:RunMode(),2:RunMode()}; FIRST={1:RunMode(),2:RunMode()}
CLIP={1:RunMode(),2:RunMode()}   # the deck's clip line, learned per source and held (rule 4), never typed in
def lock_reset(f):
    """a change of geometry — the loss of the source lock, or a loss that looks like one — resets every comparator of the
    field at once (owner, 2026-09-07: "A change of geometry (a loss of source lock or lock like loss resets everything
    immediately)"). Called on a unit with no measurable picture, on regenerated VBI rows that are not the Shuttle's
    (lines 20/21 absent or line 22 not blank: the decoder without sync), and on a counter discontinuity."""
    BAND[f]=RunMode(); FIRST[f]=RunMode(); CLIP[f]=RunMode(); LASTTOP.pop(f,None)
LASTCTR=[None]
def lock_update(f,obs):
    """obs = this unit's observed band count S..clip or None; returns (state, comparator, class, count, runner-up)"""
    BAND[f].add(obs); comp,n,n2=BAND[f].top()
    if comp is None: return 'acquiring',None,'',0,0
    if obs is None: cls='no-picture'
    elif obs>comp: cls='band+'
    elif obs>=comp-1: cls='travel'
    else: cls='short'
    return 'locked',comp,cls,n,n2
PREV={1:None,2:None}     # the previous unit's field rasters, for the comb's static mask
LOCKST={1:'acquiring',2:'acquiring'}; DAPPLIED={1:0,2:0}
HEIGHT={1:RunMode(),2:RunMode()}; L22={1:RunMode(),2:RunMode()}
def lock_reset_all():
    for f in (1,2):
        BAND[f]=RunMode(); HEIGHT[f]=RunMode(); L22[f]=RunMode(); LOCKST[f]='no-lock'; DAPPLIED[f]=0; PREV[f]=None; SEEN21[f]=False
CELL608=1.986e-6*13.5e6   # the CEA-608 clock cell in samples (standard)
def runin_burst(row):
    """the 608 run-in burst present anywhere over the row's left 300 samples: the clock-frequency amplitude over sliding
    64-sample windows (the run-in is 7 cycles = 188 samples; a fragment is shorter) at the decoder's own gate (35: measured
    captions 52-60, chance picture hits 15-22)"""
    x=row.astype(np.float64); w=2*np.pi/CELL608; best=0.0; W=int(round(3*CELL608))   # three cycles of the clock: a fragment of the burst
    for a in range(8,300-W,16):
        seg=x[a:a+W]-x[a:a+W].mean(); n=np.arange(a,a+W)
        amp=np.hypot((seg*np.cos(w*n)).sum(),(seg*np.sin(w*n)).sum())*2/len(seg); best=max(best,amp)
    # the burst sits in the left third and the row is flat after it (the run-in line's structure; a picture row with
    # a periodic texture on the left carries content on the right too)
    # The gate is the DECODER's, imported rather than copied. It used to be a typed 35 here with a comment claiming
    # it sat "at the decoder's own gate"; when that gate was derived from CEA-608 + BT.601 (2026-09-10) this copy
    # silently kept the old value and the two ran 27.375 against 35 for as long as nobody looked. `best` above is
    # the same peak amplitude in the same units as the decoder's `amp`, so it takes the same bar.
    return best>=RUNIN_MIN_CODES and float(x[300:696].std())<=4*max(float(np.diff(x[300:696]).std())/np.sqrt(2),0.5)
XDS_STATS={'calls':0,'fired':0,'rej_mean':0,'rej_right':0,'rej_run':0}
def xds_bar(row):
    """the smeared XDS-like bar (contract section 3; the frozen envelope measured 2026-09-04): 48-bin luma profile, row
    mean < 95, bins 20..47 all <= 40, a run of >= 6 consecutive bins > 60 within bins 0..19.

    All four numbers are FITTED to the second recording of fixture A, where this bar exists; they are not derived
    and cannot be, because the bar is a smeared source artefact rather than a standard waveform. Whether they can
    be removed is therefore a question about the capture under test, not about the constants: set SG_XDS_STATS to
    count calls, firings and which clause rejects, so "is this carrying a decision here" is measured."""
    XDS_STATS['calls']+=1
    if float(row.mean())>=95: XDS_STATS['rej_mean']+=1; return False
    prof=row[:720].reshape(48,15).mean(axis=1)
    if (prof[20:]>40).any(): XDS_STATS['rej_right']+=1; return False
    run=0
    for v in prof[:20]:
        run=run+1 if v>60 else 0
        if run>=6: XDS_STATS['fired']+=1; return True
    XDS_STATS['rej_run']+=1
    return False
def process_unit(u,RU,RN):
    """one unit: RU = this unit's raster, RN = the next unit's (needed only with --repair)"""
    if A.only and u not in VERB: return
    gap = LASTCTR[0] is not None and ((CTR[u]-LASTCTR[0])&0xffff)!=1
    LASTCTR[0]=CTR[u]
    M={}
    for f in (1,2):
        R=RU if (f==1 or not A.repair) else RN; slot=(2 if (f==1 and A.repair) else (1 if (f==2 and A.repair) else f))
        Y,C,by_m,sig_b,c_b=field_arrays(R,slot); base=20 if slot==1 else 283   # line = row + base (slot numbering)
        ym=Y.mean(axis=1); thr=by_m+6*sig_b
        ystd=Y[:,40:680].std(axis=1); cstd=C.std(axis=(1,2))
        padding=(ystd==0)&(cstd==0)
        rec=(~padding)&((cstd/c_b>2.0)|(ym>thr)|(ystd>=4*sig_b))              # measured gaps: blank <= 1.48x, recorded >= 2.02x chroma noise
        recrows=[r for r in range(3,Y.shape[0]) if rec[r]]                      # rows 0..2 = lines 20/21/22 regenerated
        # the Shuttle's regenerated rows present = stable VBI (contract section 3)
        # presence is measured against the field's OWN blanking noise, not a typed margin: a regenerated waveform
        # row must stand above the noise of the rows that carry no waveform. Measured here, waveform rows are 40-54
        # and absent rows 0.5 - two populations a wide margin apart, so the derived bar separates them as surely as
        # the typed 20 did, and it travels to a capture whose noise differs. (Verified: rebuilding capture 1's
        # reference with this form changes 0 of 1,840 field readings in every column.)
        vbi_ok=(float(Y[0,40:680].std())>=6*sig_b and float(Y[1,40:680].std())>=6*sig_b and ym[2]<thr and float(Y[2,40:680].std())<4*sig_b)
        # the pedestal: the flat run contiguous with the clip
        flat_rec=[]
        for r in reversed(recrows):
            if ym[r]>thr and float(Y[r,40:680].std())<4*sig_b: flat_rec.append(float(ym[r]))
            else: break
        if flat_rec: PED[f]=min(flat_rec)
        ped=PED[f] if PED[f] is not None else by_m
        # the field's noise from adjacent samples (VHS luma band-limited near 3 MHz)
        mid=[r for r in range(40,200) if rec[r]]
        sig_n=float(np.median([float(np.diff(Y[r,24:696]).std()) for r in mid]))/np.sqrt(2) if len(mid)>=20 else 4*sig_b
        # caption evidence: the Shuttle's insert bytes (row 1) and a parity-valid row off the insert within the first rows
        ins_ok,ib1,ib2,_=cc608(Y[1]); insert_data = bool(ins_ok and ((ib1 or 0)&0x7f or (ib2 or 0)&0x7f))
        cap_row=None
        for r in recrows[:6]:
            ok,_,_,_=cc608(Y[r])
            if ok: cap_row=r; break
        # VBI rows by signature only (contract section 3); the tape's line 22 = the row under the tape's line 21
        def flatrow(r): return float(Y[r,40:680].std())<4*sig_b
        def subblack(r): return ym[r]<ped-3*sig_b
        if cap_row is not None or insert_data: SEEN21[f]=True
        line22_row=None
        if cap_row is not None: line22_row=cap_row+1                      # the tape's line 22 is one line below its line 21 (owner)
        elif SEEN21[f] and rec[3] and (subblack(3) or flatrow(3)):        # without any line-21 evidence in the source no line 22 can be identified: a dark first row is picture
            seen=[v for v in L22[f].v if v is not None]                  # the levels of the tape's line 22 seen so far (a comparator by running count)
            if (seen and min(seen)-2*sig_b<=ym[3]<=max(seen)+2*sig_b) or (not seen and insert_data): line22_row=3
        if line22_row is not None and line22_row<Y.shape[0] and rec[line22_row]: L22[f].add(int(round(ym[line22_row])))
        def vbi_kind(r):
            if cap_row is not None and r<cap_row: return 'above21'           # rows above the tape's line 21 are its lines 20 and earlier
            ok,_,_,info=cc608(Y[r])
            if ok: return 'cc608'
            if info!='no run-in' or runin_burst(Y[r]): return 'runin'         # the run-in burst present, no data
            if r==line22_row: return 'line22'
            if xds_bar(Y[r]): return 'xds'
            a=Y[r,24:696]-Y[r,24:696].mean(); t=Y[0,24:696]-Y[0,24:696].mean(); d=float(np.sqrt((a*a).sum()*(t*t).sum()))
            if d>0 and float((a*t).sum()/d)>=0.8: return 'line20'                 # the tape's line-20 timing pattern = the Shuttle's regenerated one (0.8: a template-match aperture)
            if SEEN21[f] and flatrow(r) and r+3<Y.shape[0] and all(rec[q] for q in (r+1,r+2,r+3)) and ym[r]<0.5*float(ym[r+1:r+4].mean()): return 'gap'   # the tape's grey line 22 (owner ruling 2026-09-05), only where line 21 has been seen in the source
            return ''
        vbi={r:vbi_kind(r) for r in recrows[:6]}
        for r,k in vbi.items():
            if k=='gap' and line22_row is None: L22[f].add(int(round(ym[r])))   # the grey line 22 is the tape's line 22 too (owner ruling 2026-09-05): its level feeds the comparator
        top=next((r for r in recrows if not vbi.get(r,'')),None) if recrows else None   # the first picture row (owner)
        M[f]=dict(Y=Y,C=C,by_m=by_m,sig_b=sig_b,c_b=c_b,base=base,slot=slot,ym=ym,thr=thr,rec=rec,recrows=recrows,vbi_ok=vbi_ok,ped=ped,sig_n=sig_n,
                  insert_data=insert_data,cap_row=cap_row,line22_row=line22_row,vbi=vbi,top=top)
    # unit-level lock-like loss (owner: both fields at once): a counter discontinuity, regenerated rows absent in either field,
    # or no picture in both fields (a snow-like candidate; the signal-state layer's verdict is the input in the live path)
    loss = gap or (not M[1]['vbi_ok']) or (not M[2]['vbi_ok']) or (M[1]['top'] is None and M[2]['top'] is None)
    if loss: lock_reset_all()
    for f in (1,2):
        m=M[f]; Y=m['Y']; base=m['base']; slot=m['slot']; ym=m['ym']; thr=m['thr']; rec=m['rec']; recrows=m['recrows']; top=m['top']
        by_m=m['by_m']; sig_b=m['sig_b']; ped=m['ped']; sig_n=m['sig_n']
        # The deck's clip is a PER-SOURCE quantity, learned and held like any other (contract rule 4),
        # not a number typed in. It was written here as 262/525 - this tape's values - and every
        # switch-line count is that literal minus a measured row, so a wrong clip moved every count
        # on any other source. It is now the last recorded row, taken from the rows themselves, with
        # the same running comparator the contract uses for the line-22 level: the most frequent
        # value wins and is replaced only by one whose count passes it.
        last_recorded = recrows[-1] if recrows else None
        if last_recorded is not None: CLIP[f].add(last_recorded + base)
        clipr,_cn,_cn2 = CLIP[f].top()
        if clipr is None: clipr = (last_recorded + base) if last_recorded is not None else None
        clip_row = (clipr - base) if clipr is not None else None
        if loss or top is None or len(recrows)<60:
            why=('reset' if loss else 'hidden')
            st=('no-lock' if loss else (LOCKST[f] if LOCKST[f]!='acquiring' else 'acquiring'))
            if not loss and LOCKST[f]=='locked': st='hold'
            w.writerow([u,CTR[u],f,(top+base) if top is not None else -1,-1,-1,-1,-1,-1,-1,-1,'','','',-1,'','',-1,'','','',st,why,DAPPLIED[f],'','','','','','',round(by_m,2),round(sig_b,2)])
            continue
        d=top-3                                                               # the offset: the rows above the picture from line 23 (bands above)
        last_rec=recrows[-1]
        ped_lvl=ped+6*sig_b
        feats={r:rowfeat(Y[r],Y[r-1],sig_b,ped_lvl,by_m,sig_n) for r in range(top+1,last_rec+1)}
        feats2={r:rowfeat(Y[r],Y[r-2],sig_b,ped_lvl,by_m,sig_n) for r in range(top+2,last_rec+1)}   # against the row two above: a settled other-head row matches its predecessor but not the picture
        body=[feats[r] for r in range(top+20,min(top+200,last_rec-10)) if feats[r]['lagmed'] is not None]
        body2=[feats2[r] for r in range(top+20,min(top+200,last_rec-10)) if r in feats2 and feats2[r]['lagmed'] is not None]
        M_lag2=max(ft['lagmed'] for ft in body2) if body2 else 1.0; M_dm2=max(ft['dm'] for ft in body2) if body2 else 20.0
        # the field's own variance: the body rows' own maxima (nothing inside the picture exceeds them by definition)
        M_lag=max(ft['lagmed'] for ft in body) if body else 1.0; M_dm=max(ft['dm'] for ft in body) if body else 20.0
        # M_run is the body's MAXIMUM leading blank run and the test below adds 8. Both halves are typed, and the
        # slack is NOT inert: removing it (2026-09-10) changed three field-2 units — 6287, 6674 and 6776 — and two
        # of those are units this project records as honest abstentions, "the band not detectable in every unit even
        # of a clean source" case, which under rule 4 are a hold. It also INTRODUCED a jitter blip at 6674 (field 2
        # blips 8 -> 9), so it is a regression on tier 0's own criterion and was reverted.
        # Why it is load-bearing at all, when the populations look cleanly separated: measured over 508 units,
        # body rows' lead_run never exceeds 14 while band rows reach 199, so any bar between about 15 and 140 gives
        # the same answer on most units. But M_run is a per-unit MAX, so on a unit whose body envelope happens to be
        # narrow the bar drops and the slack decides. That is the same extreme-statistic fragility that the trailing
        # test had, in the other direction. The principled replacement is the body's DISTRIBUTION rather than its
        # max plus a constant — a design change to be measured, not guessed, and not attempted at 04:00.
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
        # TORN_SELECTS: whether a row's lag statistic alone may make it the switch line. Measured 2026-09-10 at
        # commercial 6899: line 260 is ordinary picture - blank_run 0, dip present, no relocated blanking anywhere -
        # and it is selected as the switch by torn alone, lagmed 19.5 against a body envelope of 17.0 and dm 11.99
        # against 4.56. M_lag is the body's MAXIMUM, the third extreme-value envelope in this file to be caught
        # deciding a boundary. Line 261 below it is the real other-head row and says so physically: blank_run 88,
        # dip absent. An independent census puts the first relocated-blanking row exactly on S in 963 of 1,013
        # readings, so the physical signature is present in the overwhelming majority and the lag statistic is not
        # needed to find it. Sweepable so the question is settled by the census rather than by argument.
        def shifted(ft,r,two=False): return (STEP_SELECTS and step(ft,r,two)) or (TORN_SELECTS and torn(ft) if not two else False) or flat(ft,r) or ft['lead_run']>M_run+8 or ft['dip_absent'] or blanked(ft)   # the two-above pass carries no torn test: two rows apart the picture's own detail exceeds the body envelope (commercial counters 6907, 6943 read seven picture rows as torn)   # (the upward scan from the clip keeps a dip-less row inside the picture from ever being taken as the band)
        def peak(ft,r): return ft['spike']>M_spk and ft['spike']>ft['dm']+5*ft['dsig'] and ft['width']<=12 and ft['above_range']<ft['spike']/2 and not shifted(ft,r)
        if os.environ.get('SG_EXPLAIN'):
            # SG_EXPLAIN="field:line[,line...]" names WHICH test made a row part of the band, so a band edge
            # that moves can be attributed instead of guessed at. Reports every disjunct of shifted(), not the
            # first true one, because two tests firing together and one firing marginally are different faults.
            _ef,_els = os.environ['SG_EXPLAIN'].split(':')     # "field:line[,line...]", for every --units unit
            if int(_ef)==f:
                print(f'  explain unit {u} field {f}: M_lag {M_lag:.3f} M_dm {M_dm:.3f} M_lag2 {M_lag2:.3f} M_dm2 {M_dm2:.3f} M_run {M_run} M_spk {M_spk:.2f} sig_b {sig_b:.3f} ped {ped:.2f}')
                for _L in (int(x) for x in _els.split(',')):
                    _r=_L-4-SLOT[f][0]
                    if _r not in feats: print(f'    line {_L}: no features (outside top+1..last_rec)'); continue
                    for _lbl,_fs,_two in (('1-above',feats,False),('2-above',feats2,True)):
                        if _r not in _fs: print(f'    line {_L} {_lbl}: absent'); continue
                        ft=_fs[_r]
                        print(f"    line {_L} {_lbl}: lagmed {ft['lagmed']} dm {ft['dm']:.2f} wlag {ft['wlag']} wr {ft['wr']:.3f} "
                              f"lead_run {ft['lead_run']} blank_run {ft['blank_run']} dip_absent {ft['dip_absent']} "
                              f"spike {ft['spike']:.1f} width {ft['width']} std {float(Y[_r,40:680].std()):.2f} mean {ym[_r]:.2f}")
                        print(f"       step {step(ft,_r,_two)} | torn {torn(ft) if not _two else 'n/a'} | flat {flat(ft,_r)} | "
                              f"lead_run>M_run+8 {ft['lead_run']>M_run+8} ({ft['lead_run']} > {M_run+8}) | "
                              f"dip_absent {ft['dip_absent']} | blanked {blanked(ft)} => SHIFTED {shifted(ft,_r,_two)}")
                    print(f"    line {_L}: peak(1-above) {peak(feats[_r],_r) if _r in feats else 'n/a'}")
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
        # the top switch line: S-1 where S-1 carries the partial line's evidence (the peak / a departing later segment), else S
        T=None; n_sw=0; n_below=0; lost=0
        if sw is not None:
            pf=feats.get(sw-1)
            # The partial switch row keeps its normal LEFT transition and loses its trailing
            # blanking, because its right-hand part came from the other head (measured on the raw
            # samples of the commercial capture, unit 6687: line 260 ramps from blanking as any row
            # does and then ends at luma 17-20 where 258/259 end at 1-2; both agents read the same
            # rows, 2026-09-09). The expectation is the field's OWN picture rows, not a constant:
            # body_end is the smallest trailing blanking run they show.
            # The expectation comes from the picture rows IMMEDIATELY ABOVE the candidate, and from
            # their MEDIAN, not the whole field's minimum. Falsified 2026-09-09 on counters
            # 6701/6702/6703, three units whose field-2 bottoms are byte-alike in structure (lines
            # 520-522 return to blanking, 523 keeps its leading ramp and ends at luma 19-21, 524/525
            # begin at 24-30 with no ramp): the whole-field minimum let one anomalous body row 160
            # lines away drag the expectation to 1, so the same row read partial, not-partial,
            # partial. A local median cannot be moved by a single distant row, and the separation it
            # decides is 1 against 8+, so nothing hinges on which robust statistic is used.
            above=[feats[r]['end_run'] for r in range(max(top, sw-21), sw-1) if r in feats]
            # The MINIMUM of that local window, not its median. A partial row's trailing blanking is
            # ABSENT, not merely shorter than typical, and the separation is categorical: measured on
            # the commercial capture at counters 6667/6687/6690, ordinary picture rows carry 15-22
            # samples of their own trailing blanking and a partial carries 1. The median sits inside
            # the ordinary spread, so it fired on line 259 of 6667 (end_run 16 against a median of
            # 17) where the raw samples say that row is ordinary picture and the switch is the fully
            # displaced row below it. The first version of this used the minimum over 160 whole-field
            # rows and one distant anomaly dragged it to 1; the fault was the WINDOW, and narrowing
            # the window to the rows immediately above is what makes the minimum the right bar.
            # ...and the MINIMUM is wrong too, for the same reason the whole-field minimum was: it is an
            # extreme, so it tracks the noisiest row in the window rather than the population. Measured
            # 2026-09-10 at counters 6667/6668/6669, three consecutive units whose line 259 is ordinary
            # picture in all three (raw rows looked at; means 21.87/21.91/22.36, full-width texture, no
            # partial structure): its trailing run reads 16, 12, 17 against a window minimum of 15.0 in
            # every unit, so `end_run >= body_end` flipped False for one unit and the band's top moved
            # 260 -> 259 -> 260. That is 27 of field 1's 35 off-mode units.
            # The fix is not a margin on the same comparison -- a margin from the body's own dispersion
            # was tried on the same day and moved field 1 by three blips while making field 2 worse.
            # The comparison itself is the fault: it asks "is this below the shortest ordinary row",
            # when the measured question is "which of two populations is this row in". The populations
            # are stated two comments above and are categorical: ordinary rows carry 15-22 samples of
            # trailing blanking, a partial carries 1, because a partial row's blanking is ABSENT -- the
            # other head's active video runs to the row's end. So classify by which centre the candidate
            # is nearer, the ordinary rows' or zero. The boundary is the midpoint between two MEASURED
            # centres, one of which is zero by construction, so nothing is typed in: 12 against a median
            # of 16 is plainly an ordinary row, and 1 against 16 is plainly not.
            body_end=float(np.median(above)) if len(above)>=10 else None
            # SYMMETRIC in direction (owner, 2026-09-10: "I've seen the head switch move both ways,
            # the harness needs to be honest rather than fitted garbage if it's to be trusted"). A
            # partial row is one that keeps its own blanking at ONE end and loses it at the other,
            # whichever end that is: the other head arriving from the right leaves the leading
            # blanking and takes the trailing, and arriving from the left does the reverse. The old
            # test required leading-present AND trailing-absent, so a switch the other way was
            # invisible to it. Neither end is privileged now.
            # ⚠️ `lead_blank` is a BOOL, never a tri-state, so an unreadable lead is asserted as "not blank" rather
            # than recorded as unknown — the "missing is not a value" fault. It does not bite on this capture,
            # because `by_m` is `float(by.mean())` and always a real number, but the project records units where
            # the Shuttle's regenerated rows are absent entirely (whole-tape units 176-194: no timing line, no
            # caption insert, all-black raster). There `by.mean()` still returns a number — of rows that are not
            # blanking — so `lead_blank` is computed against a meaningless reference and returns a confident False,
            # which flips `ends_partial` to equal `trail_ok` and silently changes the answer. Fixing it means making
            # `lead_blank` genuinely tri-state and routing None to the fallback below; that changes behaviour on
            # captures this harness is gated from, so it is named rather than guessed at here.
            lead_ok  = pf is not None and pf.get('lead_blank')
            trail_ok = pf is not None and body_end is not None and 2*pf['end_run'] >= body_end
            # `(lead_ok is not None)` used to sit in this condition and was DEAD: lead_ok is `pf is not None and
            # pf.get('lead_blank')`, which is a bool in every case, so the clause was always true. Removed because
            # a dead clause that reads like a guard is worse than no guard — it advertises a safety that is not
            # there. The real guard it was standing in for is the tri-state above, which does not exist yet.
            ends_partial = (pf is not None and body_end is not None and (lead_ok != trail_ok))
            # The peak and the whole-row lag stay as corroboration; neither is required, because a
            # dark row carries no lag to improve (the defect this replaces: line 260 read wlag 6 at
            # ratio 0.97, so the old test failed and the switch line fell through to the full row).
            # The ENDS are authoritative where they can be read, and the peak and the whole-row lag
            # are corroboration only. Falsified 2026-09-09 against the engine on the raw rows:
            # counter 6667 line 259 ramps up from blanking AND returns to it (last samples 1,1,2,2,
            # 2,1,2,1) — an ordinary picture row — while line 260 starts at 22 with no ramp, so
            # there is no partial and the switch line is 260. My OR let the peak/lag alternative
            # fire on that normal row and I reported 259. At counter 6690 line 260 ramps up
            # normally and ends at 22 without returning: that IS a partial, and the engine, which
            # has no ends test, took 261. Each instrument was wrong in one direction; the ends
            # decide both, so they are no longer one option among three.
            if os.environ.get('SG_EXPLAIN_PARTIAL') and int(os.environ['SG_EXPLAIN_PARTIAL'])==f:
                _ab=[feats[r]['end_run'] for r in range(max(top, sw-21), sw-1) if r in feats]
                print(f"  partial unit {u} field {f}: sw L{sw+4+SLOT[f][0]} pf {'None' if pf is None else 'yes'} "
                      f"lead_blank {None if pf is None else pf.get('lead_blank')} end_run {None if pf is None else pf['end_run']} "
                      f"body_end(min of {len(_ab)}) {body_end} | above runs {sorted(_ab)} "
                      f"median {float(np.median(_ab)) if _ab else None}")
                print(f"     lead_ok {lead_ok} trail_ok {trail_ok} ends_partial {ends_partial} "
                      f"=> T will be L{(sw-1 if ends_partial else sw)+4+SLOT[f][0]}")
            if pf is not None and body_end is not None and pf.get('lead_blank') is not None:
                partial = ends_partial
            else:
                partial = pf is not None and (px>=0 or (abs(pf['wlag'])>=2 and pf['wr']<=0.90))
            T=sw-1 if partial else sw
            # the switch lines: contiguous rows from T down that carry a switch signature; below them, rows at the pedestal/blank to the clip
            n_sw=clip_row-T+1                                                 # the switch band: the top switch line to the clip (the TBC's blacked switch lines included)
            n_below=sum(1 for r in range(T,last_rec+1) if r in feats and flat(feats[r],r))   # its black rows (pedestal), reported: blank under the picture is comb-confirmed evidence, never an actuator
            lost=0
        h=(T-3) if T is not None else None                                    # the rows from line 23 to the row before the switch line = 237 + d when the switch moves with the picture
        # comparators (running count, fixed arrays): the source's switch-line count = visible switch lines + d (the lines
        # past the clip are the offset's), and the switch-line count itself as seen; the height is NOT a constant
        total=(n_sw+d) if T is not None else None
        BAND[f].add(n_sw if T is not None else None); HEIGHT[f].add(total)
        bc,bn,bn2=BAND[f].top(); hc,hn,hn2=HEIGHT[f].top(); l22,ln,ln2=L22[f].top()
        # class against the field's switch-line count: extent + d equal to it, or one less (the partial line), is the travel;
        # more is band+ (the switch read on a picture row); less is short (rows under the band grew)
        cls='' if hc is None or T is None else ('travel' if hc-1<=total<=hc else ('band+' if total>hc else 'short'))
        # a clamped top (the top at line 23 with the band's extent beyond the count): the picture sits high, d = count - extent
        # (contract, definition of d), a reading the comb must confirm before it is applied
        d_clamp=(hc-n_sw) if (hc is not None and T is not None and d==0 and n_sw>hc) else None
        # the comb: the relative vertical shift of the two crops that minimises the weave's comb energy on static picture
        # (static = both fields' rows unchanged against the previous unit within the noise); computed once both fields are measured
        m['d']=d; m['d_clamp']=d_clamp; m['T']=T; m['h']=h; m['n_sw']=n_sw; m['n_below']=n_below; m['lost']=lost; m['sw']=sw; m['how']=how; m['px']=px; m['ev']=ev
        m['feats']=feats; m['tests']=tests; m['M_spk']=M_spk; m['last_rec']=last_rec; m['cls']=cls; m['comp']=(bc,bn,bn2,hc,hn,hn2,l22,ln,ln2)
    comb_s=None; comb_r=None; static_frac=0.0
    if all(f in M and M[f].get('T') is not None or (f in M and 'd' in M[f]) for f in (1,2)) and 'd' in M[1] and 'd' in M[2]:
        Y1=M[1]['Y']; Y2=M[2]['Y']; d1=M[1]['d']; d2=M[2]['d']
        if PREV[1] is not None and PREV[2] is not None:
            n=min(200,Y1.shape[0]-3-d1-8,Y2.shape[0]-3-d2-8)
            A1=Y1[3+d1:3+d1+n,24:696]; A2=Y2[3+d2:3+d2+n,24:696]
            st1=np.abs(A1-PREV[1][3+d1:3+d1+n,24:696])<=4*M[1]['sig_n']; st2=np.abs(A2-PREV[2][3+d2:3+d2+n,24:696])<=4*M[2]['sig_n']
            det=np.abs(A1[:-1]-A1[1:])>4*M[1]['sig_n']; det=np.concatenate((det,det[-1:]),axis=0)   # vertical detail in field 1 (a flat area combs at no shift)
            static=st1&st2&det; static_frac=float(static.mean())
            if static.sum()>=0.03*static.size:                                   # enough static, detailed picture to measure (3%: the harness's own aperture)
                # the weave's comb energy: field-1 row i, field-2 row i+sh, field-1 row i+1 interleaved; a registered weave is
                # smooth line to line, a misregistered one alternates; measured as the mean second difference along the
                # weave over static, detailed pixels, after an 8-sample horizontal low-pass (the same metric as the
                # project's static_comb_metric.py)
                k=np.ones(8)/8.0
                L1=np.apply_along_axis(lambda r: np.convolve(r,k,mode='same'),1,A1); L2=np.apply_along_axis(lambda r: np.convolve(r,k,mode='same'),1,A2)
                E={}
                for sh in range(-3,4):                                            # the range: whatever is required (owner); ±3 covers every displacement seen
                    lo=max(0,-sh); hi=n-1-max(0,sh)
                    if hi-lo<20: continue
                    a=L1[lo:hi]; b=L2[lo+sh:hi+sh]; c=L1[lo+1:hi+1]
                    dd=np.abs(a-2*b+c); msk=static[lo:hi]&static[lo+sh:hi+sh]&static[lo+1:hi+1]
                    E[sh]=float(dd[msk].mean()) if msk.any() else None
                E={k:v for k,v in E.items() if v is not None}
                if len(E)>=3:
                    best=min(E,key=E.get); ss=sorted(E.values()); comb_s=best; comb_r=(ss[0]/ss[1]) if ss[1]>0 else 1.0
        PREV[1]=Y1.copy(); PREV[2]=Y2.copy()
    for f in (1,2):
        m=M[f]
        if 'd' not in m: continue
        base=m['base']; top=m['top']; d=m['d']; T=m['T']; sw=m['sw']
        bc,bn,bn2,hc,hn,hn2,l22,ln,ln2=m['comp']
        # the lock: comparators plus one confirmation — a caption placing the field (its line 21 two rows above the picture, or
        # the insert carrying data with the top at 23..24) or the comb agreeing at these crops
        cap_ok = (m['cap_row'] is not None and m['cap_row']+2==top) or (m['insert_data'] and d<=1)
        comb_ok = (comb_s==0 and comb_r is not None and comb_r<=0.8)
        comb_bad = (comb_s is not None and comb_s!=0 and comb_r is not None and comb_r<=0.8)
        if LOCKST[f]!='locked' and bc is not None and (cap_ok or comb_ok): LOCKST[f]='locked'
        st=LOCKST[f]
        dc=m.get('d_clamp')
        if dc is not None and comb_s is not None and comb_s==dc and comb_r is not None and comb_r<=0.8: d=dc; m['d']=d   # the high-field reading, confirmed by the comb at that shift
        applied = d if st=='locked' else 0
        DAPPLIED[f]=applied
        events=[]
        if m['cls']=='band+': events.append('band+')
        if m['cls']=='short': events.append('short' if m.get('d_clamp') is None else f"clamped{m['d_clamp']:+d}")
        tot=(m['n_sw']+m['d']) if m['T'] is not None else None
        if hc is not None and tot is not None and tot!=hc: events.append(f'lines{tot-hc:+d}'+('p' if m['px']>=0 else 'a'))   # the switch-line count (visible + d) against the source's: the partial line's one row is the travel
        if comb_bad: events.append(f'comb{comb_s:+d}')
        if m['n_below']>0: events.append(f'below{m["n_below"]}')
        disc='|'.join(f"{r+base}:{m['feats'][r]['blank_x']}/{(6+m['feats'][r]['lead_run']) if m['feats'][r]['lead_run']>0 else -1}/{m['feats'][r]['x'] if m['feats'][r]['spike']>m['M_spk'] else -1}" for r in ((sw-1,sw,sw+1) if sw is not None else ()) if r in m['feats'])
        band_tests='|'.join(f"{r+base}:{m['tests'](r)}" for r in range(sw,m['last_rec']+1)) if sw is not None else ''
        w.writerow([u,CTR[u],f,top+base,d,(T+base) if T is not None else -1,(sw+base) if sw is not None else -1,m['n_sw'],m['n_below'],m['lost'],m['h'] if m['h'] is not None else -1,
                    m['how'],m['px'],m['ev'],(m['cap_row']+base) if m['cap_row'] is not None else -1,int(m['insert_data']),(m['line22_row']+base) if m['line22_row'] is not None else -1,
                    (l22 if l22 is not None else -1),(comb_s if comb_s is not None else ''),(round(comb_r,2) if comb_r is not None else ''),round(static_frac,3),
                    st,m['cls'],applied,(bc if bc is not None else -1),f'{bn}/{bn2}',(hc if hc is not None else -1),f'{hn}/{hn2}',';'.join(events),band_tests,disc,round(m['by_m'],2),round(m['sig_b'],2)])
        if u in VERB:
            sys.stdout.flush(); print(f"unit {u} field {f}: top L{top+base} d {d} T {('L%d'%(T+base)) if T is not None else 'none'} S {('L%d'%(sw+base)) if sw is not None else 'none'} switch lines {m['n_sw']} below {m['n_below']} lost {m['lost']} h {m['h']} | comp band {bc} {bn}/{bn2} height {hc} {hn}/{hn2} l22 {l22} | cap {m['cap_row']} ins {int(m['insert_data'])} l22row {m['line22_row']} vbi {dict((k+base,v) for k,v in m['vbi'].items() if v)} | comb {comb_s} {comb_r} static {static_frac:.3f} | {st} {m['cls']} applied {applied} {events}")
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
if os.environ.get('SG_XDS_STATS'):
    s=XDS_STATS
    print(f"  xds_bar: calls {s['calls']}  FIRED {s['fired']}  rejected by mean>=95 {s['rej_mean']}, "
          f"by bins 20-47 >40 {s['rej_right']}, by no run of 6 {s['rej_run']}")
