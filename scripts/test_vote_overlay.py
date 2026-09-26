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
assert g.vote_label(row)=='anchor +0 eng +5 conf 0 win 27/30 pair off'
assert dr.textlength(g.vote_label(row),font=font)<452
row.update(vote_count='0',vote_winner_count='0')
assert g.vote_label(row)=='anchor +0 eng +5 conf 0 win 0/30 empty pair off'
assert dr.textlength(g.vote_label(row),font=font)<452
assert g.FH+134+14 < g.H-14-13
assert g.vote_label({})==''
assert g.vote_label({'ge_anchor_vote':'0'})=='anchor vote off'
assert 'missing' in g.vote_label({'ge_anchor_vote':'1'})
row.update(ge_vote_pair='1',vote_rB='0.59999999999999998',vote_pair_pass='1')
assert 'rB 0.600 pair 1' in g.vote_label(row)
assert dr.textlength(g.vote_label(row),font=font)<452
row.update(vote_rB='-0.999999',vote_pair_pass='0',vote_anchor='-10',vote_engine_anchor='+5')
assert dr.textlength(g.vote_label(row),font=font)<452
assert g.placement_source({'anchor_source':'anchor_vote'},'engine')=='vote anchor'
assert g.placement_source({'anchor_source':'census'},'engine')=='engine'
assert g.placement_source({'anchor_source':'anchor_vote'},'manual')=='manual'
header=f"ctr {999999:>6}   applied ({-10:+d},{5:+d}) from {g.placement_source({'anchor_source':'anchor_vote'},'engine')}"
assert dr.textlength(header,font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',12))<456
assert g.blankspot_label({}) == ''
assert g.blankspot_label({'ge_vote_blankspot':'0'}) == 'A1 off'
assert g.blankspot_label({'ge_vote_blankspot':'1'}) == 'A1 --'
assert g.blankspot_label({'ge_vote_blankspot':'1','vote_blankspot_pass':'1'}) == 'A1 pass'
failed=dict(ge_vote_blankspot='1',vote_blankspot_pass='0',vote_blankspot_line='291',f2_first='286')
assert g.blankspot_label(failed) == 'A1 FAIL @291'
label=g.blankspot_label(failed)+' | wave bar 0.45; clamp +/-5'
assert dr.textlength(label,font=font)<452
assert g.FH+120+13 < g.FH+134
print('VOTE-OVERLAY PASS: frame-owned logged evidence, intact text, separate strip area')
