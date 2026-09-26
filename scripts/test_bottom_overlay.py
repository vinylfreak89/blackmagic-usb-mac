"""Logged bottom provenance fits without covering the vote, schedule or strip."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import geometry_render as g
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
dr=ImageDraw.Draw(Image.new('RGB',(g.W,g.H)))
row={'ge_bottom_flat':'1','ge_bottom_flat_margin':'3',
     'bottom_rule_f1':'flat_reference','bottom_rule_f2':'fallback'}
for field in (1,2):
    for name,value in zip(('p5','p50','p95'),('98.05','100','255')):row[f'bottom_F_{name}_f{field}']=value
assert g.bottom_label(row)=='b1 flat F98.05/100/255; b2 fall F98.05/100/255 M3'
assert dr.textlength(g.bottom_label(row),font=font)<452
for field in (1,2):
    for name in ('p5','p50','p95'):row[f'bottom_F_{name}_f{field}']='254.95'
assert dr.textlength(g.bottom_label(row),font=font)<452
assert g.FH+148+14 < g.H-14-13
assert g.bottom_label({})==''
assert g.bottom_label({'ge_bottom_flat':'0'})=='bottom flat off'
assert g.bottom_label({'ge_bottom_flat':'1'})=='b1 -- F--/--/--; b2 -- F--/--/--'
print('BOTTOM-OVERLAY PASS: logged frame-owned rules/quantiles, intact text, separate strip area')
