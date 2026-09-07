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
OUT=open(A.out,'w',newline=''); w=csv.writer(OUT); w.writerow(['unit','counter','field','top','sig_top','d','T','S','switch_lines','below','blank_under','c_vis','H','how','peak_x','partial_evidence','caption_line','insert_data','line22','l22_level','comb_shift','comb_ratio','comb_static','lock_state','confirmed_by','case','applied','H_comparator','H_counts','C_comparator','C_counts','clip','events','band_tests','disc_x','blank_y','sig_b'])
PED={1:None,2:None}   # the carried pedestal per field
# LOCKS BY RUNNING COUNT (owner, 2026-09-07: "No magic numbers. It should be derived and stabilized. ie, check the number
# of times that level has appeared. If it's appeared more often than any other level, then it becomes the comparator
# and replaces the previous comparator"). The source's constants (contract, definitions) are comparators by running
# count in fixed arrays: H the picture lines, CSW the switch-line count, CLIP the clip line, L22 the tape's line-22
# level. The account (contract rule 9) decides each unit from the signature top and the switch line against the
# geometry's expectation and the comparators: rigid / row above the picture / travel / hidden top / loud report.
CTR={}
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
LASTCTR=[None]
PREV={1:None,2:None}     # the previous unit's field rasters, for the comb's static mask
LOCKST={1:'acquiring',2:'acquiring'}; DAPPLIED={1:0,2:0}
# the source's constants as comparators (contract, definitions): H = picture lines (switch line - signature top), CSW =
# the switch-line count (visible switch lines where the band ends above the clip), CLIP = the last row not at the
# blanking level, L22 = the level of the tape's line 22; D = the geometry's offset per field; CONF = what confirmed the lock
H={1:RunMode(),2:RunMode()}; CSW={1:RunMode(),2:RunMode()}; CLIP={1:RunMode(),2:RunMode()}; L22={1:RunMode(),2:RunMode()}
D={1:0,2:0}; CONF={1:'',2:''}
def lock_reset_all():
    for f in (1,2):
        H[f]=RunMode(); CSW[f]=RunMode(); CLIP[f]=RunMode(); L22[f]=RunMode(); LOCKST[f]='no-lock'; DAPPLIED[f]=0; D[f]=0; CONF[f]=''; PREV[f]=None
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
    return best>=35 and float(x[300:696].std())<=4*max(float(np.diff(x[300:696]).std())/np.sqrt(2),0.5)
def xds_bar(row):
    """the smeared XDS-like bar (contract section 3; the frozen envelope measured 2026-09-04): 48-bin luma profile, row
    mean < 95, bins 20..47 all <= 40, a run of >= 6 consecutive bins > 60 within bins 0..19"""
    if float(row.mean())>=95: return False
    prof=row[:720].reshape(48,15).mean(axis=1)
    if (prof[20:]>40).any(): return False
    run=0
    for v in prof[:20]:
        run=run+1 if v>60 else 0
        if run>=6: return True
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
        vbi_ok=(float(Y[0,40:680].std())>=20 and float(Y[1,40:680].std())>=20 and ym[2]<thr and float(Y[2,40:680].std())<4*sig_b)   # 20: a presence margin (waveform rows 40-54 measured, absent 0.5)
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
        line22_row=None
        xds_row=next((r for r in recrows[:6] if xds_bar(Y[r])),None)
        if cap_row is not None: line22_row=cap_row+1                      # the tape's line 22 is one line below its line 21 (owner)
        elif xds_row is not None: line22_row=xds_row+1                    # the tape's line 285 is one line below its line 284 (the XDS bar), field 2 of the EP recording
        elif rec[3] and flatrow(3):
            seen=[v for v in L22[f].v if v is not None]                  # the levels of the tape's line 22 its line 21 has placed (a comparator by running count, fed by caption/XDS + 1 only)
            if seen and min(seen)-2*sig_b<=ym[3]<=max(seen)+2*sig_b: line22_row=3
        # no gate on line-21 evidence: a dark first row that the signatures call line 22 is decided by the account (rule 9)
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
            if flatrow(r) and r+3<Y.shape[0] and all(rec[q] for q in (r+1,r+2,r+3)) and ym[r]<0.5*float(ym[r+1:r+4].mean()) and all(ym[q]>ped+6*sig_b for q in (r+1,r+2,r+3)): return 'gap'   # the tape's grey line 22 (owner ruling 2026-09-05) over PICTURE rows; a dark row over dark rows is a dark scene (commercial tape, 2026-09-07)
            return ''
        vbi={r:vbi_kind(r) for r in recrows[:6]}
        top=next((r for r in recrows if not vbi.get(r,'')),None) if recrows else None   # the first picture row (owner)
        M[f]=dict(Y=Y,C=C,by_m=by_m,sig_b=sig_b,c_b=c_b,base=base,slot=slot,ym=ym,thr=thr,rec=rec,recrows=recrows,vbi_ok=vbi_ok,ped=ped,sig_n=sig_n,
                  insert_data=insert_data,cap_row=cap_row,line22_row=line22_row,vbi=vbi,top=top)
    # unit-level lock-like loss (owner: both fields at once): a counter discontinuity, regenerated rows absent in either field,
    # or no picture in both fields (a snow-like candidate; the signal-state layer's verdict is the input in the live path)
    # (offline stand-in for the signal-state input: both fields without picture; the regenerated rows absent is a hold, rule 6)
    loss = gap or (M[1]['top'] is None and M[2]['top'] is None)
    if loss: lock_reset_all()
    for f in (1,2):
        m=M[f]; Y=m['Y']; base=m['base']; slot=m['slot']; ym=m['ym']; thr=m['thr']; rec=m['rec']; recrows=m['recrows']; top=m['top']
        by_m=m['by_m']; sig_b=m['sig_b']; ped=m['ped']; sig_n=m['sig_n']
        if loss or top is None or len(recrows)<60 or not m['vbi_ok']:
            why=('reset' if loss else ('rows-absent' if not m['vbi_ok'] else 'hidden'))
            st=('no-lock' if loss else (LOCKST[f] if LOCKST[f]!='acquiring' else 'acquiring'))
            if not loss and LOCKST[f]=='locked': st='hold'
            w.writerow([u,CTR[u],f,-1,(top+base) if top is not None else -1,-1,-1,-1,-1,-1,-1,-1,-1,'','','',-1,'','',-1,'','','',st,CONF[f],why,DAPPLIED[f],-1,'',-1,'',-1,why,'','',round(by_m,2),round(sig_b,2)])
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
        # the top switch line: S-1 where S-1 carries the partial line's evidence (the peak / a departing later segment), else S
        T=None; n_below=0
        if sw is not None:
            pf=feats.get(sw-1); partial = pf is not None and (px>=0 or (abs(pf['wlag'])>=2 and pf['wr']<=0.90))
            T=sw-1 if partial else sw
            # the switch lines: contiguous rows from T down that carry a switch signature; below them, rows at the pedestal/blank to the clip
            n_below=sum(1 for r in range(T,last_rec+1) if r in feats and flat(feats[r],r))   # its pedestal rows (the TBC's cleared switch lines), reported
        Hu=(T-top) if T is not None else None                                 # the picture lines by signature: the switch line minus the signature top
        # under the band: switch lines the TBC cleared sit at the pedestal (contract: 9-11) and are switch lines; rows at
        # the blanking level are not; the clip is the last row that is not at the blanking level (a comparator)
        def blanklvl(r): return ym[r]<=thr
        clip_u=next((r for r in range(last_rec,top,-1) if not blanklvl(r)),last_rec)
        CLIP[f].add(clip_u-min(D[f],0)); clip_c=CLIP[f].top()[0]             # a field sitting high shows its clip |d| rows up (contract, clip line)
        if T is not None:
            pad_start=next((r for r in range(T,Y.shape[0]) if padding[r]),Y.shape[0])   # the Shuttle's padding bounds the pass-through region
            blank_under=sum(1 for r in range(T,pad_start) if blanklvl(r))    # blank rows between the band and the padding
            n_sw=clip_c-T+1                                                  # the band's extent: the top switch line to the clip
            c_vis=sum(1 for r in range(T,min(clip_c,last_rec)+1) if not blanklvl(r))   # the visible switch lines (timed or pedestal-black)
        else: blank_under=0; n_sw=0; c_vis=0
        # feed the comparators with this unit's signature readings (running count, fixed arrays; owner ruling four)
        Hc0=H[f].top()[0]
        lost=max(0,(3+D[f])+239-clip_c) if T is not None else 0               # lines past the clip (closure)
        if T is not None: CSW[f].add(c_vis+lost)                             # c: the visible switch lines plus the lines lost past the clip (a positive offset must not read c as c - d)
        m.update(d=None,T=T,Hu=Hu,n_sw=n_sw,n_below=n_below,blank_under=blank_under,c_vis=c_vis,sw=sw,how=how,px=px,ev=ev,feats=feats,tests=tests,M_spk=M_spk,last_rec=last_rec,clip_c=clip_c,clip_u=clip_u)
        # THE ACCOUNT (contract rule 9): the signature top and the switch line against the geometry's expectation (the
        # previous decision) and the comparators
        d_cap=(m['cap_row']-1) if m['cap_row'] is not None else None       # the tape's line 21 at row r: d = r - 1 (row 1 = line 21)
        case=''; hid=None; rowabove=None
        if T is None:
            case='noS'                                                        # no switch line measured: the account cannot run; the geometry holds
        elif Hc0 is None:
            # the seed (contract: d from the bands above, or 0 with the top at 23 — the owner's basis assumption — or the caption's d)
            d0=d_cap if d_cap is not None else max(top-3,0)
            D[f]=d0; H[f].add(T-(3+d0)); case='seed'+('-cap' if d_cap is not None else '')
            if d_cap is None and top==3 and blank_under>0: hid=-blank_under; m['hid_range']=True; case+=f';hidden-1..{hid:+d}?'   # blank rows under the band at the seed: candidates -1..-(rows), put to the comb (owner, 15:40)
        else:
            exp_top=3+D[f]; exp_T=exp_top+Hc0; dt=top-exp_top; dT=T-exp_T
            # rule 9, the cases in order; the first that fits decides
            if dt==0 and dT==0: case='steady'
            elif dt==dT: D[f]+=dt; case=f'rigid{dt:+d}'                       # the switch line followed the picture: the field moved
            elif top==3 and dT<dt:
                hid=D[f]+dT; case=f'hidden{hid:+d}?'                          # the top pinned at 23: the switch line's move is the field's (d = V - H), applied only when the comb confirms it
            elif dT==0: case=f'rowabove{dt:+d}'; rowabove=dt                 # the row above the picture: the field did not move (unless the settled comb says so)
            elif dt!=0 and abs(dT-dt)==1: D[f]+=dt; case=f'rigid{dt:+d}+travel{dT-dt:+d}'   # the field moved by the top (the reliable edge) with one row of the reading's travel
            elif dt==0 and abs(dT)==1: case=f'travel{dT:+d}'                  # the switch-line reading's travel (the partial line, the peak)
            elif dt==0: case=f'switch{dT:+d}!'                                # more than the travel: reported loudly, held
            else: case=f'geom{dt:+d}/{dT:+d}!'                                # different amounts: reported loudly, held
            if hid is None: H[f].add((Hc0-(top-(3+D[f]))) if top>3 else Hc0)   # H fed by the top's evidence only: the switch line's identity minus the signature top; its reading's travel never feeds H (owner: the peak gone keeps the switch line)
            Hc1=H[f].top()[0]
            if Hc1!=Hc0: D[f]=T-Hc1-3; case+=f';H{Hc0}->{Hc1}'               # a comparator replaced re-places the crop (owner ruling four)
            if d_cap is not None and d_cap!=D[f]:
                if LOCKST[f]!='locked' or abs(d_cap-D[f])==1:                 # before a lock the caption re-seeds (the model); under one, a caption one row off re-identifies the rows: line 22 is the row below it, the picture starts after (owner, 16:20)
                    D[f]=d_cap; H[f]=RunMode(); H[f].add(T-(3+d_cap)); CSW[f]=RunMode(); case+=';reseed-cap!'
                else: case+=f';cap{d_cap:+d}!'                                 # logged and reported, geometry wins (the model)
        Cc=CSW[f].top()[0]
        if Cc is not None and c_vis>Cc+1: case+=f';c_vis{c_vis-Cc:+d}!'      # visible switch lines beyond c + 1 (the travel): reported loudly
        elif Cc is not None and c_vis!=Cc: case+=f';c{c_vis-Cc:+d}'
        m['d']=D[f]; m['case']=case; m['hid']=hid; m['rowabove']=rowabove; m['d_cap']=d_cap
    # the comb at a placement (d1,d2): the relative vertical shift of the two crops that minimises the weave's comb
    # energy on static, detailed picture, at the capture's field precedence (the transport order; --repair is the
    # per-capture pairing input)
    def comb_at(d1,d2):
        Y1=M[1]['Y']; Y2=M[2]['Y']
        if PREV[1] is None or PREV[2] is None: return None,None,0.0
        n=min(200,Y1.shape[0]-3-d1-8,Y2.shape[0]-3-d2-8)
        if n<40 or 3+d1<0 or 3+d2<0: return None,None,0.0
        A1=Y1[3+d1:3+d1+n,24:696]; A2=Y2[3+d2:3+d2+n,24:696]
        st1=np.abs(A1-PREV[1][3+d1:3+d1+n,24:696])<=4*M[1]['sig_n']; st2=np.abs(A2-PREV[2][3+d2:3+d2+n,24:696])<=4*M[2]['sig_n']
        det=np.abs(A1[:-1]-A1[1:])>4*M[1]['sig_n']; det=np.concatenate((det,det[-1:]),axis=0)
        static=st1&st2&det; sf=float(static.mean())
        if static.sum()<0.03*static.size: return None,None,sf                   # 3%: the harness's own aperture
        k=np.ones(8)/8.0
        L1=np.apply_along_axis(lambda r: np.convolve(r,k,mode='same'),1,A1); L2=np.apply_along_axis(lambda r: np.convolve(r,k,mode='same'),1,A2)
        E={}
        for sh in range(-3,4):
            lo=max(0,-sh); hi=n-1-max(0,sh)
            if hi-lo<20: continue
            a=L1[lo:hi]; b=L2[lo+sh:hi+sh]; c=L1[lo+1:hi+1]
            dd=np.abs(a-2*b+c); msk=static[lo:hi]&static[lo+sh:hi+sh]&static[lo+1:hi+1]
            if msk.any(): E[sh]=float(dd[msk].mean())
        if len(E)<3: return None,None,sf
        best=min(E,key=E.get); ss=sorted(E.values()); return best,(ss[0]/ss[1] if ss[1]>0 else 1.0),sf
    def decisive(s,r): return s is not None and r is not None and r<=0.8
    comb_s=None; comb_r=None; static_frac=0.0
    both = all(M[f].get('d') is not None for f in (1,2))
    if both:
        # the settled comb's two exceptions, per field: the hidden top (confirmed at the candidate placement) and the
        # row above the picture (the owner's "unless ... a comb disagreement on the settled comb")
        for f in (1,2):
            m=M[f]; o=3-f
            if m['hid'] is not None:
                # confirmed only when the comb CHANGES: decisive nonzero at the held crop and decisive zero at the candidate
                # (a move shared by both fields reads zero at both placements and stays held — contract, the comb);
                # at the seed the candidates run from -1 down to -(blank rows under the band)
                s0,r0,_=comb_at(M[1]['d'],M[2]['d'])
                cands=list(range(D[f]-1,m['hid']-1,-1)) if m.get('hid_range') else [m['hid']]
                hit=None
                if decisive(s0,r0) and s0!=0:
                    for hd in cands:
                        cand={f:hd,o:M[o]['d']}; s,r,_=comb_at(cand[1],cand[2])
                        if decisive(s,r) and s==0: hit=hd; break
                if hit is not None: D[f]=hit; m['d']=D[f]; H[f].add(m['T']-(3+D[f])); m['case']+=f';comb-confirmed{hit:+d}!'
                else: m['case']+=(';held-travel' if abs(m['hid']-D[f])==1 else ';held!')
            if m['rowabove'] is not None and LOCKST[f]=='locked':
                s0,r0,_=comb_at(M[1]['d'],M[2]['d'])
                if decisive(s0,r0) and s0!=0:
                    cand={f:m['d']+m['rowabove'],o:M[o]['d']}; s1,r1,_=comb_at(cand[1],cand[2])
                    if decisive(s1,r1) and s1==0: D[f]=cand[f]; m['d']=D[f]; m['case']+=';comb-moved'
        comb_s,comb_r,static_frac=comb_at(M[1]['d'],M[2]['d'])
        PREV[1]=M[1]['Y'].copy(); PREV[2]=M[2]['Y'].copy()
    for f in (1,2):
        m=M[f]
        if m.get('d') is None: continue
        base=m['base']; top=m['top']; d=m['d']; T=m['T']; sw=m['sw']
        Hc,Hn,Hn2=H[f].top(); Cc,Cn,Cn2=CSW[f].top(); l22,ln,ln2=L22[f].top()
        # the lock: a comparator plus one confirmation — a caption placing the field at the account's d, or the comb
        # reading zero at the placed crops (a comb-only lock is a lock at the account's reading; recorded as such)
        cap_ok = (m['d_cap'] is not None and m['d_cap']==d) or (m['d_cap'] is None and m['insert_data'] and abs(d)<=1)   # a raw caption at the account's d, or the insert's bytes with no raw caption at |d| <= 1 (the tape's line 21 inside the Shuttle's window)
        comb_ok = decisive(comb_s,comb_r) and comb_s==0
        comb_bad = decisive(comb_s,comb_r) and comb_s!=0
        if LOCKST[f]!='locked' and Hc is not None and (cap_ok or comb_ok): LOCKST[f]='locked'; CONF[f]=('caption' if cap_ok else 'comb')
        st=LOCKST[f]
        applied = d if st=='locked' else 0
        DAPPLIED[f]=applied
        events=[m['case']]
        if comb_bad: events.append(f'comb{comb_s:+d}!')                       # a veto: applied (rule 1), reported (section 8)
        if m['n_below']>0: events.append(f'below{m["n_below"]}')
        if m['blank_under']>0: events.append(f'blank{m["blank_under"]}')
        disc='|'.join(f"{r+base}:{m['feats'][r]['blank_x']}/{(6+m['feats'][r]['lead_run']) if m['feats'][r]['lead_run']>0 else -1}/{m['feats'][r]['x'] if m['feats'][r]['spike']>m['M_spk'] else -1}" for r in ((sw-1,sw,sw+1) if sw is not None else ()) if r in m['feats'])
        band_tests='|'.join(f"{r+base}:{m['tests'](r)}" for r in range(sw,m['last_rec']+1)) if sw is not None else ''
        dec_top=3+d                                                            # the decided top: the crop origin 23 + d
        w.writerow([u,CTR[u],f,dec_top+base,top+base,d,(T+base) if T is not None else -1,(sw+base) if sw is not None else -1,m['n_sw'],m['n_below'],m['blank_under'],m['c_vis'],
                    m['Hu'] if m['Hu'] is not None else -1,m['how'],m['px'],m['ev'],(m['cap_row']+base) if m['cap_row'] is not None else -1,int(m['insert_data']),(m['line22_row']+base) if m['line22_row'] is not None else -1,
                    (l22 if l22 is not None else -1),(comb_s if comb_s is not None else ''),(round(comb_r,2) if comb_r is not None else ''),round(static_frac,3),
                    st,CONF[f],m['case'],applied,(Hc if Hc is not None else -1),f'{Hn}/{Hn2}',(Cc if Cc is not None else -1),f'{Cn}/{Cn2}',m['clip_c']+base,';'.join(events),band_tests,disc,round(m['by_m'],2),round(m['sig_b'],2)])
        if u in VERB:
            sys.stdout.flush(); print(f"unit {u} field {f}: top L{dec_top+base} sig L{top+base} d {d} T {('L%d'%(T+base)) if T is not None else 'none'} S {('L%d'%(sw+base)) if sw is not None else 'none'} extent {m['n_sw']} c_vis {m['c_vis']} blank {m['blank_under']} Hu {m['Hu']} | H {Hc} {Hn}/{Hn2} C {Cc} {Cn}/{Cn2} clip {m['clip_c']+base} l22 {l22} | cap {m['cap_row']} ins {int(m['insert_data'])} l22row {m['line22_row']} vbi {dict((k+base,v) for k,v in m['vbi'].items() if v)} | comb {comb_s} {comb_r} static {static_frac:.3f} | {st} {CONF[f]} {m['case']} applied {applied} {events}")
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
