"""Published units are not woven frames; enforce all actual frame identities."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from geometry_review_status import audit_rows, write_status, blankspot_still_settings, rigid_settings

def row(c, top='', unused='0'):
    return dict(counter_extended=str(c), published='1', frame_top_unit=str(top),
                f2_unused=unused, pairing='reversed', applied_d1='1', applied_d2='0',
                frame_d1='1' if top else '', frame_d2='0' if top else '')

rows=[row(10,11),row(11,12),row(12,unused='1')]
strips=[(0,10,1,0),(1,11,1,0)]
r=audit_rows(rows,strips)
assert blankspot_still_settings(rows)==[('','','')]
settings=[dict(ge_vote_blankspot='1',ge_comb_still='0',ge_comb_motion_min='1')]*2
assert blankspot_still_settings(settings)==[('1','0','1')]
assert rigid_settings(rows)==[('','')]
assert rigid_settings([dict(ge_comb_rigid='1',ge_comb_rigid_clarity='1.3')])==[('1','1.3')]
assert r['published_units']==3 and r['paired_frames']==r['encoded_frames']==2
assert r['boundary_units']==[dict(counter=12,location='tail',reason='no next-unit pair partner',encoded_as_fill=False)]
for bad in ([strips[1]], [(0,11,1,0)], [strips[0],strips[0]], [(0,10,2,0),strips[1]]):
    try:
        audit_rows(rows,bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f'accepted bad sequence {bad}')
bad=deepcopy(rows);bad[-1]['f2_unused']='0'
try:
    audit_rows(bad,strips)
except ValueError:
    pass
else:
    raise AssertionError('accepted unexplained missing published unit')
with tempfile.TemporaryDirectory(prefix='review-status-',dir='/private/tmp') as tmp:
    p=Path(tmp)
    write_status(p,dict(state='IN_PROGRESS',engine_commit='new'))
    assert json.loads((p/'renders.status').read_text())['state']=='IN_PROGRESS'
    write_status(p,dict(state='READY',engine_commit='new'))
    assert json.loads((p/'renders.status').read_text())['state']=='READY'
    assert len(list(p.iterdir()))==1
print('REVIEW-STATUS PASS: tail boundary, missing/reordered/duplicate frames, placements, atomic status')
