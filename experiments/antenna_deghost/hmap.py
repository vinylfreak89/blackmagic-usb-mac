import numpy as np, csv, sys
from PIL import Image, ImageDraw
S=sys.argv[1]; D=np.load(S+'/an/hD.npy'); C=np.load(S+'/an/hC.npy')
rows=list(csv.DictReader(open(S+'/rp/log.csv'))); NF=D.shape[0]; SL=np.arange(22,258)
print('match strength percentiles', np.nanpercentile(C,[10,50,90]).round(2))
ev=(np.abs(D)>=3)&(C>0.25)
raw=np.zeros((263,NF),np.uint8); tape=np.zeros((263,NF),np.uint8)
for g in range(NF):
    m=float(rows[g]['marker_slot']); par=int(rows[g]['parity']); top=int(round(m))-16
    for i,s in enumerate(SL):
        v=min(255,int(abs(D[g,i])*20)) if ev[g,i] else 0
        raw[s,g]=v
        o=s-top
        if o<0: o+=262 if par==1 else 263
        if o>=263: o-=263
        tape[o,g]=v
def save(a,name,title):
    im=Image.fromarray(a).resize((NF,263*2),Image.NEAREST).convert('RGB'); d=ImageDraw.Draw(im); d.text((4,4),title,fill=(255,255,0))
    for L in range(0,263,20): d.text((NF-30,2*L),str(L),fill=(0,255,0))
    im.save(S+'/an/'+name)
save(raw,'hmap_raw.png','sideways jump vs row above; y = synchroniser line, x = field (1698 = 28 s)')
save(tape,'hmap_tape.png','same, y = tape line (stabilised)')
