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
Ys=[]; buf=bytearray()
def emit(u): Ys.append(np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE))
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
SLOT={1:(16,279),2:(279,525)}     # unit rows of each slot (line 20.. / 283..); blank reference rows 7..15 / 270..278
def field_arrays(R,slot):
    a,b=SLOT[slot]; Y=R[a:b,1::2].astype(np.float32); C=np.stack([R[a:b,0::4],R[a:b,2::4]],axis=1).astype(np.float32)
    bl=R[a-9:a-1]; by=bl[:,1::2].astype(np.float32); bc=np.stack([bl[:,0::4],bl[:,2::4]],axis=1).astype(np.float32)
    return Y,C,float(by.mean()),float(max(by.std(),0.5)),float(max(bc.std(),0.3))
def rowfeat(row,prev,sig_b,ped_lvl):
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
    if len(span)>=60:
        a=24+int(span[0]); b=24+int(span[-1])+1
        sads=[(float(np.abs(row[a:b]-prev[a+t:b+t]).mean()),t) for t in range(-24,25)]; best=min(sads,key=lambda x:x[0]); wlag=best[1]; wr=best[0]/max(sads[24][0],1e-6)
    uniform = med is not None and abs(med)>=2 and sum(1 for v in lags if abs(v-med)<=2)>=2*len(lags)/3   # a whole-row time shift: the other head (the subagent's rule); flagging inside the picture varies along the row
    # the row above's own horizontal structure at the spike: a vertical picture edge there makes a narrow |diff| spike
    # from one-sample jitter; the RF transient sits where the row above is locally flat
    lo,hi=max(0,x-8),min(720,x+9); above_range=float(prev[lo:hi].max()-prev[lo:hi].min())
    # leading flat run: from sample 3 (past any sync-like spike at 0..2), the samples staying within 3 sigma_b of the
    # level at sample 3..8, ended by a step of >= 6 sigma_b; its length in samples
    lvl=float(row[3:9].mean()); run=3
    while run<719 and abs(float(row[run])-lvl)<=3*sig_b: run+=1
    run=run-3 if (run<719 and float(row[run])-lvl>=6*sig_b) else 0
    return dict(lagmed=(float(np.median(al)) if len(lags)>=3 else None),n=len(lags),dm=dm,dsig=ds,spike=sp,x=x,width=r-l+1,uniform=uniform,above_range=above_range,lead_run=run,wlag=wlag,wr=wr)
w=csv.writer(open(A.out,'w',newline='')); w.writerow(['unit','field','top','S_first_shifted','how','peak_x','partial_evidence','reliable_to_S','band_from_S','last_rec','closure','S_wlag','S_r','body_lag_max','body_r_min','M_run','M_spk','blank_y','sig_b'])
n=len(Ys)-(1 if A.repair else 0)
PED={1:None,2:None}   # the carried pedestal per field
for u in range(n):
    if A.only and u not in VERB: continue
    for f in (1,2):
        R=Ys[u] if (f==1 or not A.repair) else Ys[u+1]; slot=(2 if (f==1 and A.repair) else (1 if (f==2 and A.repair) else f))
        Y,C,by_m,sig_b,c_b=field_arrays(R,slot); base=20 if slot==1 else 283   # line = row + base (slot numbering)
        rec=(C.std(axis=(1,2))/c_b)>2.0; ym=Y.mean(axis=1); thr=by_m+6*sig_b
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
        flat_rec=[float(ym[r]) for r in recrows if ym[r]>thr and float(Y[r,40:680].std())<4*sig_b]
        if flat_rec: PED[f]=min(flat_rec)
        ped=PED[f] if PED[f] is not None else by_m
        def picture_row(r): return ym[r]>max(thr,ped+3*sig_b) and float(Y[r,40:680].std())>=4*sig_b and not cc608(Y[r])[0]
        # the top begins a run of picture rows (a lone picture-like row followed by a black or VBI row is VBI: a
        # damaged caption, the tape's line 20 data)
        top=next((r for r in recrows if picture_row(r) and picture_row(r+1) and picture_row(r+2)),None)
        if top is None or len(recrows)<60: w.writerow([u,f,-1,-1,'no-picture',-1,'',0,0,-1,'','','',-1,-1,-1,-1,round(by_m,2),round(sig_b,2)]); continue
        last_rec=recrows[-1]
        ped_lvl=ped+6*sig_b
        feats={r:rowfeat(Y[r],Y[r-1],sig_b,ped_lvl) for r in range(top+1,last_rec+1)}
        body=[feats[r] for r in range(top+20,min(top+200,last_rec-10)) if feats[r]['lagmed'] is not None]
        # the field's own variance: the body rows' own maxima (nothing inside the picture exceeds them by definition)
        M_lag=max(ft['lagmed'] for ft in body) if body else 1.0; M_dm=max(ft['dm'] for ft in body) if body else 20.0
        M_run=max(ft['lead_run'] for ft in body) if body else 8       # the picture rows' own leading blank run (the H-blanking dip)
        narrow=[ft['spike'] for ft in body if ft['width']<=12 and ft['above_range']<ft['spike']/2]; M_spk=max(narrow) if narrow else 0.0   # the picture's own narrow specks
        body_r=min(ft['wr'] for ft in body) if body else 1.0; body_lag=max(abs(ft['wlag']) for ft in body) if body else 1   # the field's own envelope, reported
        M_lag=max(ft['lagmed'] for ft in body) if body else 1.0; M_dm=max(ft['dm'] for ft in body) if body else 20.0
        def flat(ft,r): return float(Y[r,40:680].std())<4*sig_b and ym[r]>thr                                 # a pedestal row (the other head's black)
        # the other head's rows come in two shapes: a uniform whole-row time shift (the blind check's envelope: picture
        # |lag| <= 1.2, r >= 0.94), or a torn row whose lag varies along the line (no single lag fits, r stays near 1)
        # but whose segment lags and row difference exceed anything the picture's own rows show; plus the pedestal row
        # and the intruded-blanking row
        def torn(ft): return ft['lagmed'] is not None and ft['lagmed']>M_lag and ft['dm']>M_dm
        def shifted(ft,r): return (abs(ft['wlag'])>=2 and ft['wr']<=0.90) or torn(ft) or flat(ft,r) or ft['lead_run']>M_run+8
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
        r=last_rec
        while r>top+20 and shifted(feats[r],r): r-=1
        if r<last_rec: sw=r+1; how='shifted'
        if sw is not None and sw-1 in feats:
            pf=feats[sw-1]; spk_rank=(pf['spike']/M_spk) if M_spk>0 else 0.0
            narrow_flat = pf['width']<=12 and pf['above_range']<pf['spike']/2 and pf['spike']>pf['dm']+5*pf['dsig']
            ev=f"spike {pf['spike']:.0f}@{pf['x']} w{pf['width']} rank {spk_rank:.2f} narrowflat {int(narrow_flat)} wlag {pf['wlag']} r {pf['wr']:.2f}"
            if narrow_flat and spk_rank>=1.0: px=pf['x']; how='shifted+peak_above'
        reliable=(sw-top) if sw is not None else (last_rec-top+1); band=(last_rec-sw+1) if sw is not None else 0
        w.writerow([u,f,top+base,(sw+base) if sw is not None else -1,how,px,ev,reliable,band,last_rec+base,reliable+band,(feats[sw]['wlag'] if sw is not None else ''),(round(feats[sw]['wr'],2) if sw is not None else ''),body_lag,round(body_r,2),M_run,round(M_spk,0),round(by_m,2),round(sig_b,2)])
        if u in VERB:
            sys.stdout.flush(); print(f'unit {u} field {f}: top L{top+base} switch {("L%d"%(sw+base)) if sw is not None else "none"} ({how}) peak_x {px} reliable {reliable} band {band} last_rec L{last_rec+base} | body max lag {M_lag} dm {M_dm:.1f} lead_run {M_run} narrow-spike {M_spk:.0f}')
            for r in range(max(top+20,last_rec-9),last_rec+1):
                ft=feats[r]; print(f'    L{r+base}: lagmed {ft["lagmed"]} n {ft["n"]} dm {ft["dm"]:5.1f} dsig {ft["dsig"]:5.1f} spike {ft["spike"]:5.0f}@{ft["x"]} w{ft["width"]} shifted {int(shifted(ft,r))} run {ft["lead_run"]} above_rng {ft["above_range"]:.0f} peak {int(peak(ft,r))}')
print('units',n,'->',A.out)
