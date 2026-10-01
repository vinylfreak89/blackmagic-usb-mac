# Usage: HDETECT_LIB=/path/libhdetect.dylib python3 c_port_compare.py NAME CAPTURE.tpc TOPS_SIDECAR.csv
# Feed the same units and tops to the v11 Python detector (reference) and the C port; compare per unit.
import sys, os, ctypes, json, numpy as np
P_DIR=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,P_DIR)
import phys, phys_run, playback as P
L=ctypes.CDLL(os.environ['HDETECT_LIB'])  # cc -O2 -std=c11 -fPIC -dynamiclib src/frameserver/hdetect.c -o LIB -lm
class R(ctypes.Structure):
    _fields_=[('judged',ctypes.c_int),('torn',ctypes.c_int*2),('nosw',ctypes.c_int*2),('swheld',ctypes.c_int*2),('switch_line',ctypes.c_int*2),('nlines',ctypes.c_int*2),('lines',(ctypes.c_int16*525)*2)]
L.hd_size.restype=ctypes.c_size_t; L.hd_judge.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.POINTER(R)]
L.hd_init.argtypes=[ctypes.c_void_p]
st=ctypes.create_string_buffer(L.hd_size()); L.hd_init(st)
name,path,tops_csv=sys.argv[1:4]
tops=phys_run.sidecar_tops(tops_csv)
W=phys.Win(); n=same=0; diffs=[]
for c,raw in P.raw_units(path,0,os.path.getsize(path)):
    Y=np.ascontiguousarray(raw[:,1::2]); t=tops(c); r=R()
    L.hd_judge(st,Y.ctypes.data,int(t[0]),int(t[1]),ctypes.byref(r))
    if not W.ok(): W.add(phys.warm_frame(Y)); assert not r.judged; continue
    s=W.stats(); res,fr=phys.judge(Y,t,s); W.add(fr); n+=1
    py=[sorted(res['lines'][k]) for k in (0,1)]; cc=[sorted(r.lines[k][:r.nlines[k]]) for k in (0,1)]
    pt=[bool(x) for x in res['torn']]; ct=[bool(x) for x in r.torn]
    if py==cc and pt==ct: same+=1
    else: diffs.append((c,pt,ct,py,cc))
print(name,'units judged',n,'identical',same,'different',len(diffs))
for d in diffs[:8]: print('  unit',d[0],'torn py',d[1],'c',d[2],'| py',d[3],'| c',d[4])
