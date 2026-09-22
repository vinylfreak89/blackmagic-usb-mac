"""Overlay geometry/evidence test, no programme images or OCR guesses."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import geometry_render as g
from PIL import Image, ImageDraw, ImageFont

font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
class Draw:
    def __init__(self): self.dr=ImageDraw.Draw(Image.new('RGB',(1000,656)));self.texts=[]
    def textlength(self,*args,**kw):return self.dr.textlength(*args,**kw)
    def text(self,xy,text,**kw):self.texts.append((xy,text));self.dr.text(xy,text,**kw)
row=dict(comb_d='0',comb_margin='1.01',comb_ran='1',comb_decided='0',triggers='63',confidence='LOW',reset_before='1')
d=Draw();g.draw_comb_status(d,row,-1,font,6,526,462)
assert d.texts[0]==((6,526),'DIFFERS RESET'),d.texts
assert len(d.texts)==2 and d.texts[1][0][0]>=106
assert all(xy[0]+d.textlength(t,font=font)<=462 for xy,t in d.texts)
e=[282.]*11;e[5]=e[6]=4.3
row.update(comb_rejected='1',comb_discarded='0',comb_reject_ratio='66.1',comb_substituted_d='0',
           comb_floor_lo='0',comb_floor_hi='1',comb_rise_left='66.1',comb_rise_right='66.7',comb_basin='1')
lines=g.comb_panel_lines(row,e,0)
assert lines[1]=='box/min 1x' and lines[2]=='REJECT 66.1x -> d+0'
assert lines[3]=='floor +0..+1 BASIN' and lines[4]=='rise L66.1x R66.7x'
assert all(d.textlength(s,font=font)<=218 for s in lines),lines
row.update(comb_discarded='1',comb_substituted_d='',comb_floor_lo='1',comb_floor_hi='5',
           comb_rise_right='',comb_basin='0')
lines=g.comb_panel_lines(row,e,-1)
assert lines[2]=='DISCARD 66.1x; HOLD' and lines[3]=='floor +1..+5 OPEN' and lines[4].endswith('R--x')
assert all(d.textlength(s,font=font)<=218 for s in lines),lines
assert 'floor --' in g.comb_panel_lines({},e,7)
print('COMB-PANEL PASS: fixed DIFFERS/RESET slot; published vs rejected ratio; logged floor/rises; discard; legacy evidence')
