#!/usr/bin/env python3
"""mux.py D VIDEO_ONLY OUT -- the audio exactly as the device delivered it, against the video timeline relay.py built on the audio
clock (D/schedule.json: a0 and the slot count); then video + audio muxed in ONE pass with the index reserved at the front at its
exact size. Checks the frame count; prints RESULT.
Audio placement: the first block goes where its audio-clock time falls against a0 (trimmed or led by silence), and every later
block follows the previous one with no gap: the device's samples are continuous unless the transport lost some. Silence is
inserted only across a transport hole (the replay's "hole N" count above zero): there a discontinuity ends the audio run, and
the next anchored block's time says how many samples are missing; the unanchored blocks before it are held and written after
the silence. With no holes, discontinuities are counted and the audio stays contiguous. (Until 2026-10-21 silence was
inserted wherever the A/V residual stepped, which assumed every unit counter is one NTSC frame; in the Shuttle's other-format
modes the counter runs ~50-70 per second, and ~41 s of silence chopped one tape's continuous audio.)
The dry run and the frame count do not read the video-only file's media: they use a local sparse stand-in holding its real
top-level atoms with the mdat payload left as a hole, so the index size comes from the file's own sample tables and only the
final pass reads the media (on a cloud volume each full read is a download; 2026-10-21 three reads of a 65 GB render helped
exhaust the account's daily download cap). The reservation is the exact size, so the output has no padding beyond ffmpeg's own."""
import os, re, subprocess, sys, json
D=sys.argv[1]; VOUT=sys.argv[2]; OUT=sys.argv[3]
if os.path.exists(OUT): print("RESULT REFUSED: output exists"); sys.exit(2)
sched=json.load(open(f"{D}/schedule.json")); frames=sched["slots"]; a0=sched["a0_ticks"]
m=re.search(r"\bhole (\d+)", open(f"{D}/replay.log").read())
if not m: print("RESULT REFUSED: replay.log has no hole count"); sys.exit(1)
holes=int(m.group(1)); DISC, UNANCHORED = 1, 4
A=[]
for line in open(f"{D}/timing.csv"):
    f=line.rstrip("\n").split(",")
    if f[0]=="A": A.append([int(x) for x in f[1:]])
pcm=open(f"{D}/a.s24","rb"); out=open(f"{D}/a_sync.s24","wb"); pos=0; ins=[]; discs=0; overlaps=[]; held=[]; waiting=False
def put(data):
    global pos
    out.write(data); pos+=len(data)//6
for k,(ordinal,pnum,pden,n,flags,ctr,res) in enumerate(A):
    assert pden==240000, ("unexpected audio timebase", pden)
    data=pcm.read(n*6); assert len(data)==n*6, ("audio dump shorter than its log", ordinal)
    if k==0:
        at=round((pnum-a0)/5)                       # 5 ticks per sample
        if at<0: data=data[min(-at,n)*6:]
        elif at>0: put(b"\0"*(at*6))
        put(data); continue
    if flags & DISC:
        discs+=1
        if holes: waiting=True
    if waiting:
        if flags & UNANCHORED: held.append(data); continue
        at=round((pnum-a0)/5); before=pos+sum(len(h)//6 for h in held)
        if at>before: put(b"\0"*((at-before)*6)); ins.append((ctr,at-before))
        elif at<before: overlaps.append((ctr,before-at))
        for h in held: put(h)
        held=[]; waiting=False
    put(data)
for h in held: put(h)
out.close()
print(f"video {frames} frames ({frames*1001/30000:.2f} s); audio {pos} samples ({pos/48000:.2f} s); replay holes {holes}; audio discontinuities {discs}; "
      f"silence inserted at holes (counter, samples): {ins}; re-anchors earlier than the audio (counter, samples, left contiguous): {overlaps}")
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
# OUT is emptied in place and written by ffmpeg into that same file: never deleted and recreated (see plain_render.sh).
r=subprocess.run(["bash","-c",': > "$1" && truncate -s 0 "$1" && [ "$(stat -f %z "$1")" = 0 ]',"_",OUT])
if r.returncode!=0: print("RESULT REFUSED: could not empty the output in place"); sys.exit(1)
mx=subprocess.Popen(base+["-loglevel","warning","-y","-moov_size",str(need),OUT],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
so,se=mx.communicate()
class R: pass
r=R(); r.returncode=mx.returncode; r.stderr=se
if r.returncode!=0: print("RESULT FAILED:", r.stderr[-400:]); sys.exit(1)
pr=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_name,duration,nb_frames","-of","compact",OUT],capture_output=True,text=True).stdout
print(pr.strip()); print("RESULT OK", OUT)
