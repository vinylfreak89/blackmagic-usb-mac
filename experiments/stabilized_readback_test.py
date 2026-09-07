#!/usr/bin/env python3
"""Deciding test for stabilized_readback.py: a synthetic field-pair render with KNOWN defects goes through the same
ProRes path the real renderer uses, and the read-back must report exactly those defects and nothing else.
Sign convention (the read-back's): shift = the picture's displacement in the OUTPUT, positive = moved down. A source
offset of +k (reading the picture k rows further down the source) displaces the output by -k.
Injected (frame index: defect): 5 = field 1 bottom bar one row lower; 9 = field 2 picture displaced -1 (bars still);
13 = field 1 picture displaced +2 (bars still); 17 = field 2 picture-like row directly above its top bar; 21 = field 1
picture-like rows directly below its bottom bar (two rows); 25 = field 1 three red rows. Frames 0..29, textured
picture (random noise, fixed seed, the same picture every frame so a shift is unambiguous).
Usage: stabilized_readback_test.py [scratch_dir]"""
import sys, os, subprocess, csv, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
sd=sys.argv[1] if len(sys.argv)>1 else os.environ.get('TMPDIR','/tmp'); os.makedirs(sd,exist_ok=True)
H=243; W=720; INFO=200; N=30; rng=np.random.default_rng(7)
pic=(rng.integers(16,200,size=(H+8,W))).astype(np.uint8)      # taller than the panel so shifts have source rows
pic=np.maximum(pic, np.repeat((np.sin(np.arange(W)/9.0)*40+120).astype(np.uint8)[None,:],H+8,axis=0)//2)  # horizontal texture
TOP=3; BOT=238
def panel(shift=0, bot=BOT, above=False, below=False, extra_red=False):
    p=np.zeros((H,W,3),np.uint8); g=np.zeros((H,W),np.uint8)
    body=pic[4+shift:4+shift+(bot-TOP-1)]                    # rows TOP+1 .. bot-1
    g[TOP+1:bot]=body
    if above: g[TOP-1]=g[TOP+1]                               # a copy of the first picture row above the bar
    if below: g[bot+1]=g[bot-1]; g[bot+2]=g[bot-1]
    p[:,:,0]=g; p[:,:,1]=g; p[:,:,2]=g
    for r in ([TOP,bot]+([120] if extra_red else [])): p[r,:,0]=255; p[r,:,1]=g[r]//3; p[r,:,2]=g[r]//3
    return p
out=os.path.join(sd,'readback_selftest.mov')
ff=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{2*W+INFO}x{H}','-r','30000/1001','-i','-','-vf','setsar=8/9','-c:v','prores_ks','-profile:v','3','-pix_fmt','yuv422p10le',out],stdin=subprocess.PIPE)
man=open(out+'.frames.csv','w'); man.write('frame,ordinal,counter,f1_top,f1_bot,f1_shift,f2_top,f2_bot,f2_shift\n')
for k in range(N):
    f1=panel(shift=(-2 if k==13 else 0), bot=(BOT+1 if k==5 else BOT), below=(k==21), extra_red=(k==25))
    f2=panel(shift=(1 if k==9 else 0), above=(k==17))
    fr=np.zeros((H,2*W+INFO,3),np.uint8); fr[:,:W]=f1; fr[:,W:2*W]=f2; fr[:,2*W:]=28
    ff.stdin.write(fr.tobytes())
    b1=BOT+1 if k==5 else BOT
    man.write(f'{k},{1000+k},{k},{23+TOP-3},{20+b1},0,{286},{283+BOT},0\n')   # top-first_line-shift == TOP, bot-first_line == b1
ff.stdin.close(); ff.wait(); man.close()
r=subprocess.run([sys.executable,os.path.join(os.path.dirname(__file__),'stabilized_readback.py'),out],capture_output=True,text=True)
print(r.stdout)
rows=list(csv.DictReader(open(out+'.readback.csv')))
def got(f,key,pred): return sorted(int(x['frame']) for x in rows if x['field']==str(f) and pred(x[key]))
checks={
 'f1 bottom bar moved at frames 5 and 6 only': got(1,'bot_moved',lambda v:v=='1')==[5,6],
 'f1 top bar never moved': got(1,'top_moved',lambda v:v=='1')==[],
 'f2 bars never moved': got(2,'top_moved',lambda v:v=='1')==[] and got(2,'bot_moved',lambda v:v=='1')==[],
 'f2 decisive shift -1 at 9 and +1 back at 10 only': [(int(x['frame']),int(x['shift'])) for x in rows if x['field']=='2' and x['shift'] not in ('','0') and float(x['ratio'])<=0.8]==[(9,-1),(10,1)],
 'f1 decisive shift +2 at 13 and -2 back at 14 only': [(int(x['frame']),int(x['shift'])) for x in rows if x['field']=='1' and x['shift'] not in ('','0') and float(x['ratio'])<=0.8]==[(13,2),(14,-2)],
 'f2 picture above the top bar at 17 only': got(2,'above_pict_rows',lambda v:v!='')==[17],
 'f1 picture below the bottom bar at 21 only (rows 239 240)': got(1,'below_pict_rows',lambda v:v!='')==[21] and [x['below_pict_rows'] for x in rows if x['field']=='1' and x['frame']=='21']==['239 240'],
 'f1 three red rows at 25 only': got(1,'n_red',lambda v:v!='2')==[25],
 'manifest agrees everywhere except the injected extra red row': all((x['red_top']==x['man_top'] and x['red_bot']==x['man_bot']) for x in rows if not (x['field']=='1' and x['frame']=='25')),
 'read-back exit status 1 (a bar moved)': r.returncode==1,
}
bad=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS ' if v else 'FAIL ')+k)
print('SELFTEST', 'PASS' if not bad else 'FAIL', f'{len(checks)-len(bad)}/{len(checks)}')
sys.exit(1 if bad else 0)
