"""Sidecar-only overlay source ownership, abstention and discard provenance."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
import geometry_render as g
rows={10:dict(f1_first='26',f1_last='262',f2_first='',f2_last='525',
              wave_top_f1='24',wave_status_f1='ACCEPTED',wave_step_f1='.5',wave_max_step_f1='.7',
              wave_top_f2='292',wave_status_f2='DISCARDED',wave_step_f2='.8',wave_max_step_f2='.9'),
      11:dict(f1_first='28',f1_last='260',f2_first='286',f2_last='524',
              wave_top_f1='26',wave_status_f1='ACCEPTED',wave_step_f1='.6',wave_max_step_f1='.7')}
frame,edges,waves=g.frame_evidence(rows,10,11)
assert edges==[[26,262],[None,525]],edges
assert waves[0]['top']=='26' and waves[1]['top']=='292',waves
assert g.waveform_label(2,waves[1])=='f2 DISCARDED top 292 step 0.800 max 0.900'
rows[10].update(wave_top_f2='',wave_status_f2='ABSTAIN',wave_step_f2='0',wave_max_step_f2='.3')
assert 'ABSTAIN top --' in g.waveform_label(2,g.frame_evidence(rows,10,11)[2][1])
assert g.trigger_words(32)=='basis changed'
print('WAVEFORM-OVERLAY PASS: frame census vs unit waveform, discard/abstain, engine trigger')
