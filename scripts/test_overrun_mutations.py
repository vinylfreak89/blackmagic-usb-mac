"""Deciding controls reject either missing predicate term and measured history."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]/'src/field_registration'
source=(root/'geometry_engine.c').read_text()
mutations={
    'omit-overrun':('&& now>old',''),
    'omit-no-gain':('f->first[k]>=previous->interpreted_first[k] && now>old','now>old'),
    'measured-history':('previous->interpreted_first[k]','previous->first[k]'),
    'ignore-comb':('f->overrun_terms[k]==GE_OV_ALL','(f->overrun_terms[k]|GE_OV_SAME_COMB)==GE_OV_ALL'),
    'ignore-top-move':('f->overrun_terms[k]==GE_OV_ALL','(f->overrun_terms[k]|GE_OV_TOP_MOVED)==GE_OV_ALL'),
    'ignore-bottom':('f->overrun_terms[k]==GE_OV_ALL','(f->overrun_terms[k]|GE_OV_BOTTOM_STILL)==GE_OV_ALL'),
}
with tempfile.TemporaryDirectory(prefix='overrun-mutations-',dir='/private/tmp') as td:
    td=Path(td);(td/'tests').mkdir()
    shutil.copyfile(root/'geometry_engine.h',td/'geometry_engine.h')
    shutil.copyfile(root/'tests/geometry_overrun.c',td/'tests/geometry_overrun.c')
    for name,(old,new) in mutations.items():
        assert old in source,name
        (td/'geometry_engine.c').write_text(source.replace(old,new))
        subprocess.run(['cc','-O2','-std=c11','-Wall','-Wextra','-Werror',str(td/'tests/geometry_overrun.c'),'-lm','-o',str(td/'test')],check=True)
        p=subprocess.run([str(td/'test')],capture_output=True,text=True)
        assert p.returncode!=0 and 'assert' in p.stderr.lower(),(name,p.returncode,p.stdout,p.stderr)
        print(name,'REJECTED',p.returncode,p.stderr.strip())
print('OVERRUN-MUTATIONS PASS: geometry, history, and all three new terms are required')
