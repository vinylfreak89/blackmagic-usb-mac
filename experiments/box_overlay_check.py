"""Sound version: no old-vs-new diff (lossy re-encode confounds it). Compare the NEW
frame against the rows box_census itself says are bands, on counter 6700."""
import subprocess, sys, numpy as np
sys.path.insert(0, "experiments")
from PIL import Image
from packet_capture_reader import walk_tagged
from box_census import h_profile, row_threshold, bands, verdict, FIELDS

PX, DW, LANE, FIELD_ROWS = 180, 640, 22, 243
F1, F2 = 20, 283
BOX1, BOX2 = 8+2*22, 8+3*22
UNIT, HDR, ROWB, ROWS = 756_048, 48, 1440, 525
WANT = 6700

# --- the raw unit, and the bands the detector finds in it ---
# the renderer's own streaming extractor, so the probe cannot disagree with it about units
MARK = b"\x00\x00\xff\xff"
state = {"buf": bytearray(), "u": None}
class Found(Exception): pass
def on_v(p):
    b = state["buf"]; b.extend(p)
    while True:
        i = b.find(MARK)
        if i < 0: return
        if i > 0: del b[:i]
        j = b.find(MARK, 4)
        if j < 0: return
        if j == UNIT and int.from_bytes(b[4:6], "little") == WANT:
            state["u"] = bytes(b[:UNIT]); raise Found
        del b[:j]
try:
    walk_tagged("captures/composite_program_30s.tpc", on_video=on_v, progress=False)
except Found:
    pass
u = state["u"]
assert u, "unit not found"
R = np.frombuffer(u, np.uint8)[HDR:].reshape(ROWS, ROWB)
hp = h_profile(R[:, 1::2])
exp = {}
for f, first in ((0, F1), (1, F2)):
    lo, hi = FIELDS[f+1]
    b = bands(hp, lo, hi, row_threshold(hp, lo, hi, 4.5, 0.28), 6)
    assert verdict(b, 6, 40) == "box", f"field {f+1} not boxed"
    z = first - 4          # applied d is (0,0) on this capture
    exp[f] = {sr - z for sr in list(range(lo, b["content_top"])) + list(range(b["content_bot"]+1, hi+1))}
    print(f"field {f+1}: bands = storage {lo}..{b['content_top']-1} and {b['content_bot']+1}..{hi}"
          f"  -> {len(exp[f])} picture lines")

# --- the rendered frame ---
out="/tmp/vb2.png"
subprocess.run(["ffmpeg","-v","error","-y","-i","/private/tmp/hw-session/v10/cap1_review.box.mp4",
                "-vf","select=eq(n\\,444)","-fps_mode","passthrough","-frames:v","1",out], check=True)
img = np.asarray(Image.open(out).convert("RGB")).astype(int)
pic = img[:486, PX:PX+DW]

both = exp[0] & exp[1]
only1 = exp[0] - exp[1]
only2 = exp[1] - exp[0]
print(f"\nexpected: {len(both)} picture lines where BOTH fields band (-> purple), "
      f"{len(only1)} f1-only, {len(only2)} f2-only")

def cast(rows):
    if not rows: return None
    px = np.array([pic[r].mean(axis=0) for r in rows])
    return px.mean(axis=0)

ok = True
# purple rows: both output rows 2k and 2k+1
pr = [r for k in sorted(both) for r in (2*k, 2*k+1) if 0 <= r < 486]
c = cast(pr)
print(f"\nrows the detector says are BOTH-field bands  -> mean RGB {np.round(c,1).tolist()}")
if not (c[0] > c[1] + 15 and c[2] > c[1] + 15):
    print("   FAIL: not purple (needs R and B both above G)"); ok = False
else: print("   purple: R and B both well above G, as PURPLE=(200,110,235) blended")

# a control: mid-picture rows the detector says are CONTENT, not band
content_k = [k for k in range(60, 180) if k not in exp[0] and k not in exp[1]]
cc = cast([2*k for k in content_k])
print(f"rows the detector says are CONTENT (control)  -> mean RGB {np.round(cc,1).tolist()}")
if abs(cc[0]-cc[2]) > 25:
    print("   FAIL: content rows carry a colour cast -- overlay is leaking"); ok = False
else: print("   no cast: the overlay is confined to the bands")

# --- tick lanes, dominant colour of lit pixels ---
print()
for f, off, want in ((0, BOX1, "red"), (1, BOX2, "blue")):
    L = img[:486, PX-off-LANE+2 : PX-off]
    lit = L.sum(axis=2) > 200
    n = int(lit.sum())
    m = L[lit].mean(axis=0) if n else np.zeros(3)
    got = "red" if m[0] > m[2] else "blue"
    print(f"box lane f{f+1} (x {PX-off-LANE+2}..{PX-off}): {n:4d} lit px, mean RGB "
          f"{np.round(m,1).tolist()} -> {got}")
    if n == 0 or got != want:
        print(f"   FAIL: expected {want}-dominant ticks"); ok = False
print("\nPASS" if ok else "\nFAIL")
sys.exit(0 if ok else 1)
