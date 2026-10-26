# top 30 storage rows of each field of every exact unit (NTSC line = row + 4), streamed
import sys, numpy as np
sys.path.insert(0, sys.argv[1] + '/experiments'); from packet_capture_reader import walk_tagged
UNIT=756_048; HDR=48; LINE=1440; F1=263; MARK=b"\x00\x00\xff\xff"; TOP=30
out=[]; buf=bytearray(); st={'skip':0}
def on_video(p):
    buf.extend(p)
    while True:
        i=buf.find(MARK)
        if i<0: return
        if i>0: del buf[:i]
        j=buf.find(MARK,4)
        if j<0: return
        if j==UNIT:
            r=np.frombuffer(bytes(buf[HDR:UNIT]),np.uint8).reshape(525,LINE)
            out.append(np.stack([r[:TOP],r[F1:F1+TOP]]))
        else: st['skip']+=1
        del buf[:j]
try:
    walk_tagged(sys.argv[2], on_video=on_video, progress=False)
except RuntimeError as e:
    print('reader check after the video was read:', e)
A=np.stack(out); np.save(sys.argv[3],A); print(A.shape,'skipped',st['skip'])
