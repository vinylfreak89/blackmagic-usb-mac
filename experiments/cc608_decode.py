#!/usr/bin/env python3
# CEA-608 line decoder as a registration instrument: per unit, which raster line carries a caption waveform that DECODES
# with valid odd parity. A smeared or vertically duplicated line fails parity; the real line 21 passes. Usage:
#   cc608_decode.py <capture.tpc> <units> <comma-separated unit rows>   (unit row r = NTSC line r+4)
# Decode CEA-608 bytes from a luma line: locate the 503.5 kHz clock run-in by correlation, sample the 3 start bits and
# 16 data bits at the run-in's phase (bit cell = 1.986 us = 26.8 px at 13.5 MHz), check odd parity per byte.
import sys, numpy as np, collections
sys.path.insert(0,'/Users/vinylfreak89/Documents/blackmagic-usb-mac/experiments'); from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; LINES=525; MARK=b"\x00\x00\xff\xff"
CELL=1.986e-6*13.5e6   # 26.81 px
def decode(row):
    """row: 720-px luma. Returns (ok, byte1, byte2, info) or (False, None, None, reason)."""
    x=row.astype(np.float64)
    # run-in search window: 10.5us after sync leading edge; our first active px is ~9.4us after it
    lo,hi=10,230
    seg=x[lo:hi]-x[lo:hi].mean(); n=np.arange(lo,hi)
    w=2*np.pi/CELL; c=(seg*np.cos(w*n)).sum(); s=(seg*np.sin(w*n)).sum(); amp=np.hypot(c,s)*2/len(seg)
    if amp<15: return (False,None,None,'no run-in')
    phase=np.arctan2(s,c)                 # peaks where cos(w n - phase)=1 -> n = (phase+2pi k)/w
    peaks=[(phase+2*np.pi*k)/w for k in range(-2,40)]; peaks=[p for p in peaks if lo<=p<hi+16*CELL+8*CELL]
    # find the run-in extent: consecutive peaks with high value
    high=x[lo:hi].max(); low=x[lo:hi].min(); thr=(high+low)/2
    def val(p):
        i=int(round(p)); return x[max(0,i-2):i+3].mean() if i<len(x) else low
    bits=[1 if val(p)>thr else 0 for p in peaks]
    # run-in = first long run of 1s at peaks; start bits: after run-in, cells '0','0','1'
    try:
        first1=bits.index(1)
    except ValueError: return (False,None,None,'no high peaks')
    k=first1
    while k<len(bits) and bits[k]==1: k+=1
    runlen=k-first1
    if runlen<5 or runlen>9: return (False,None,None,f'run-in {runlen} cycles')
    # cells after run-in: expect 0,0,1 then 16 data bits
    if k+19>len(bits): return (False,None,None,'line too short')
    if not (bits[k]==0 and bits[k+1]==0 and bits[k+2]==1): return (False,None,None,f'start bits {bits[k:k+3]}')
    d=bits[k+3:k+19]
    b1=sum(d[i]<<i for i in range(8)); b2=sum(d[8+i]<<i for i in range(8))
    odd=lambda b: bin(b).count('1')%2==1
    return (odd(b1) and odd(b2), b1, b2, f'runin {runlen} amp {amp:.0f}')
if __name__=='__main__':
    CAP=sys.argv[1]; N=int(sys.argv[2]); ROWS=[int(r) for r in sys.argv[3].split(',')]
    class Done(Exception): pass
    buf=bytearray(); st={'n':0}; res={r:collections.Counter() for r in ROWS}; per_unit=collections.Counter(); bytes_seen={r:collections.Counter() for r in ROWS}
    def emit(u):
        st['n']+=1
        Y=np.frombuffer(u,np.uint8)[HDR:].reshape(LINES,LINE)[:,1::2].astype(np.float32)   # full 720 px luma
        valid=[]
        for r in ROWS:
            ok,b1,b2,info=decode(Y[r])
            res[r]['valid' if ok else ('parity-fail' if b1 is not None else info.split(' ')[0]+'…')]+=1
            if ok: valid.append(r+4); bytes_seen[r][(b1,b2)]+=1
        per_unit[tuple(valid)]+=1
        if st['n']>=N: raise Done()
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
    try: walk_tagged(CAP, on_video=on_video, progress=False)
    except Done: pass
    print(f"== {CAP}: {st['n']} units")
    for r in ROWS: print(f"  line {r+4}: {dict(res[r].most_common(5))}; top bytes {[(hex(a),hex(b),n) for (a,b),n in bytes_seen[r].most_common(3)]}")
    print(f"  lines with VALID parity per unit: {per_unit.most_common(8)}")
