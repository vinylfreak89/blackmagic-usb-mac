"""Vote text must come from its frame row, fit intact, and clear the strip label."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import geometry_render as g
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
dr=ImageDraw.Draw(Image.new('RGB',(g.W,g.H)))
row=dict(ge_anchor_vote='1',vote_anchor='0',vote_engine_anchor='5',vote_confident='0',
         vote_count='30',vote_winner_count='27',frame_d2='0',f2_first='291')
assert g.vote_label(row)=='anchor +0; engine +5; confident 0; win 27/30 used 30'
assert dr.textlength(g.vote_label(row),font=font)<452
row.update(vote_count='0',vote_winner_count='0')
assert g.vote_label(row)=='anchor +0; engine +5; confident 0; win 0/30; empty'
assert dr.textlength(g.vote_label(row),font=font)<452
assert g.FH+134+14 < g.H-14-13
assert g.vote_label({})==''
assert g.vote_label({'ge_anchor_vote':'0'})=='anchor vote off'
assert 'missing' in g.vote_label({'ge_anchor_vote':'1'})
print('VOTE-OVERLAY PASS: frame-owned logged evidence, intact text, separate strip area')
