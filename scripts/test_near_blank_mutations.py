"""Deciding controls must reject removing nearness or using measured history."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]/'src/field_registration'
source=(root/'geometry_engine.c').read_text()
mutations={
    'omit-nearness':('f->top_distance[k]<=ge_top_near_blank','1'),
    'measured-history':('a->interpreted_first[f]','a->first[f]'),
    'overwrite-observation':('f->top_ignored[k]=1;', 'f->top_ignored[k]=1; f->first[k]=f->interpreted_first[k];'),
}
with tempfile.TemporaryDirectory(prefix='near-blank-mutations-',dir='/private/tmp') as td:
    td=Path(td);(td/'tests').mkdir()
    shutil.copyfile(root/'geometry_engine.h',td/'geometry_engine.h')
    shutil.copyfile(root/'tests/geometry_near_blank.c',td/'tests/geometry_near_blank.c')
    for name,(old,new) in mutations.items():
        assert old in source,name
        (td/'geometry_engine.c').write_text(source.replace(old,new))
        subprocess.run(['cc','-O2','-std=c11','-Wall','-Wextra','-Werror',str(td/'tests/geometry_near_blank.c'),'-lm','-o',str(td/'test')],check=True)
        p=subprocess.run([str(td/'test')],capture_output=True,text=True)
        assert p.returncode!=0 and 'Assertion failed' in p.stderr,(name,p.returncode,p.stdout,p.stderr)
        print(name, 'REJECTED',p.returncode,p.stderr.strip())
print('NEAR-BLANK-MUTATIONS PASS: all three incorrect mechanisms rejected')
