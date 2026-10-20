#!/usr/bin/env python3
"""mux.py D VIDEO_ONLY OUT -- audio placed against the first frame by its own clock, with the samples the device did not supply inserted
once where the A/V residual steps (as in the 13-30-55 render); then video + audio muxed in ONE pass with the index
reserved at the front at its exact size (dry run to /dev/null first). Checks the frame count; prints RESULT.
The dry run and the frame count do not read the video-only file's media: they use a local sparse stand-in holding its real
top-level atoms with the mdat payload left as a hole, so the index size comes from the file's own sample tables and only the
final pass reads the media (on a cloud volume each full read is a download; 2026-10-21 three reads of a 65 GB render helped
exhaust the account's daily download cap). The reservation is the exact size, so the output has no padding beyond ffmpeg's own."""
import os, re, subprocess, sys
from fractions import Fraction
D=sys.argv[1]; VOUT=sys.argv[2]; OUT=sys.argv[3]
if os.path.exists(OUT): print("RESULT REFUSED: output exists"); sys.exit(2)
V=[];A=[]
for line in open(f"{D}/timing.csv"):
    f=line.rstrip("\n").split(",")
    if f[0]=="V": V.append((int(f[1]),int(f[2]),int(f[3])))
    elif f[0]=="A": A.append([int(x) for x in f[1:]])
frames=V[-1][0]-V[0][0]+1
v0=Fraction(V[0][1],V[0][2]); pcm=open(f"{D}/a.s24","rb"); out=open(f"{D}/a_sync.s24","wb"); pos=0; shift=0; ins=[]
for (ordinal,pnum,pden,n,flags,ctr,res) in A:
    target=round(res/5)
    if target-shift>=3:
        out.write(b"\0"*((target-shift)*6)); pos+=target-shift; ins.append((ctr,target-shift)); shift=target
    at=round((Fraction(pnum,pden)-v0)*48000)+shift; data=pcm.read(n*6)
    if at<0: k=min(-at,n); data=data[k*6:]; at+=k
    if at>pos: out.write(b"\0"*((at-pos)*6)); pos=at
    elif at<pos: data=data[(pos-at)*6:]
    out.write(data); pos+=len(data)//6
out.close()
print(f"video {frames} frames ({frames*1001/30000:.2f} s); audio {pos} samples ({pos/48000:.2f} s); silence inserted (counter, samples): {ins}")
import struct
def stand_in(src, dst):
    """dst: a sparse copy of src's top-level atoms with every mdat payload left as a hole (reads only atom headers and non-mdat atoms)"""
    size=os.path.getsize(src)
    with open(src,"rb") as f, open(dst,"wb") as g:
        pos=0
        while pos<size:
            f.seek(pos); h=f.read(16); n,t=struct.unpack(">I4s",h[:8]); hl=8
            if n==1: n=struct.unpack(">Q",h[8:16])[0]; hl=16
            elif n==0: n=size-pos
            assert n>=hl and pos+n<=size, ("bad atom in the video-only file", pos, n, t)
            g.seek(pos)
            if t==b"mdat": g.write(h[:hl])
            else:
                f.seek(pos); left=n
                while left: b=f.read(min(left,1<<24)); assert b, "short read"; g.write(b); left-=len(b)
            pos+=n
        g.truncate(size)
PROXY=f"{D}/index_stand_in.mov"; stand_in(VOUT,PROXY)
vf=int(subprocess.run(["ffprobe","-v","error","-count_packets","-select_streams","v","-show_entries","stream=nb_read_packets","-of","csv=p=0",PROXY],capture_output=True,text=True).stdout.strip())
if vf not in (2*frames,2*frames-1): print(f"RESULT REFUSED: video-only file has {vf} frames, expected {2*frames}"); sys.exit(1)
def base_of(v): return ["ffmpeg","-hide_banner","-nostdin","-i",v,"-f","s24le","-ar","48000","-ac","2","-i",f"{D}/a_sync.s24",
      "-map","0:v","-map","1:a","-c:v","copy","-c:a","pcm_s24le","-shortest"]
base=base_of(VOUT)
dry=subprocess.run(base_of(PROXY)+["-moov_size","1","-f","mov","-y","/dev/null"],capture_output=True,text=True).stderr; os.remove(PROXY)
m=re.search(r"needed (\d+) additional",dry) or re.search(r"(\d+) additional",dry)
if not m: print("RESULT REFUSED: dry run gave no index size:", dry[-400:]); sys.exit(1)
need=int(m.group(1))+1
r=subprocess.run(base+["-loglevel","warning","-moov_size",str(need),OUT],capture_output=True,text=True)
if r.returncode!=0: print("RESULT FAILED:", r.stderr[-400:]); sys.exit(1)
pr=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_name,duration,nb_frames","-of","compact",OUT],capture_output=True,text=True).stdout
print(pr.strip()); print("RESULT OK", OUT)
