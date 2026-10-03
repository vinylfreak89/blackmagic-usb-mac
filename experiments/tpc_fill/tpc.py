# Shared helpers for reading a tagged capture (CAP1 records).
import struct, sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))      # experiments/tpc_slice.py
from tpc_slice import find_boundary
H=struct.Struct('<IBBHIIII'); MAGIC=0x31504143; UNIT=756048; SYNC=b'DeckLinkAudioResyncT'; MARK=b'\x00\x00\xff\xff'
def read_region(path,start,nbytes):
    """bytes of [first record boundary >= start, ... about nbytes], ending on a record boundary; returns (file offset, bytes)"""
    f=open(path,'rb'); p0=find_boundary(f,int(start)) if start else 0; f.seek(p0); b=f.read(int(nbytes)+(1<<20)); f.close()
    p=0; end=0
    while p+24<=len(b) and p<nbytes:
        m,t,ep,pi,seq,st,req,al=H.unpack_from(b,p)
        if m!=MAGIC: raise SystemExit('bad record at %d'%(p0+p))
        n=24+(al if t in (0,3) else 0)
        if p+n>len(b): break
        p+=n; end=p
    return p0,memoryview(b)[:end]      # a view, not a copy: these stretches are hundreds of megabytes
def walk(b,base=0):
    p=0; out=[]
    while p+24<=len(b):
        m,t,ep,pi,seq,st,req,al=H.unpack_from(b,p)
        if m!=MAGIC: raise SystemExit('bad record at %d'%(base+p))
        out.append((base+p,t,ep,pi,seq,st,req,al)); p+=24+(al if t in (0,3) else 0)
    return out
