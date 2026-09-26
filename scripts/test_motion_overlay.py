"""Logged frame-owned motion is visible without measuring pixels in Python."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments'))
import geometry_render as g

assert g.motion_labels({}) == ('', '')
assert g.motion_labels(dict(ge_comb_still='0')) == ('motion control off', '')
r = dict(ge_comb_still='1', ge_comb_rigid='1', picture_motion='moving',
         motion_shift_f1='-5', motion_shift_f2='-5', still_trigger='0', comb_suppressed='1',
         rigid_dx_f1='0', rigid_dy_f1='-5', rigid_clarity_f1='1.3001577662116106',
         rigid_dx_f2='0', rigid_dy_f2='-5', rigid_clarity_f2='inf')
a, b = g.motion_labels(r)
assert a == 'motion moving v(-5,-5) trigger 0 WITHHELD 1'
assert b == '2D f1(+0,-5) c1.3 f2(+0,-5) cinf'
r.update(picture_motion='still', motion_shift_f1='0', motion_shift_f2='0',
         still_trigger='1', comb_suppressed='0', rigid_dx_f1='', rigid_dx_f2='')
assert g.motion_labels(r) == ('motion still v(0,0) trigger 1 WITHHELD 0', '2D f1 -- f2 --')
r.update(picture_motion='unknown', motion_shift_f1='', motion_shift_f2='', still_trigger='0')
assert 'unknown v(--,--)' in g.motion_labels(r)[0]
# Both full lines fit the actual left-panel width, before the machine strip.
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 11)
dr = ImageDraw.Draw(Image.new('RGB', (1000, 712)))
for label in (a, b, *g.motion_labels(r)):
    assert dr.textlength(label, font=font) <= 1000 - 300 - 228 - 16, label
assert 176 + 14 < g.BAND - 27
print('MOTION-OVERLAY PASS: logged fields, unknown, still, withheld, 2D, unclipped layout')
