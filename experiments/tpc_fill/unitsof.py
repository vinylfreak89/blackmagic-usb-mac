import numpy as np
from tpc import *
def video_stream(b):
    v=bytearray()
    for pos,t,ep,pi,seq,st,req,al in walk(b,0):
        if t==0 and ep==0x83: v+=b[pos+24:pos+24+al]
    return v
def units_of(b,raw=False):
    """{counter: 525x1440 array} for every whole e801 unit in a region (raw=True: the 756048 unit bytes instead)"""
    v=video_stream(b); out={}; j=v.find(MARK)
    while j>=0:
        if v[j+UNIT:j+UNIT+4]==MARK and v[j+6:j+8]==b'\x01\xe8':
            c=int.from_bytes(v[j+4:j+6],'little'); out[c]=bytes(v[j:j+UNIT]) if raw else np.frombuffer(bytes(v[j+48:j+UNIT]),np.uint8).reshape(525,1440); j=v.find(MARK,j+UNIT)
        else: j=v.find(MARK,j+4)
    return out
