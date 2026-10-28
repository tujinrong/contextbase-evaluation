"""Current native input/output bindings; raw storage is never a DDS buffer."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json
B=Path(__file__).resolve().parents[1]
fields=json.loads((B/'metadata/field-map.json').read_text('utf8'))
out=[];read=[]
widths=dict(ESTUNO=15,ENAME=20,EKANA=74,EGENDER=1,EPOSTAL=10,EPREF=2,
 EADDR1=112,EADDR2=112,EPHONE=20,EEMAIL=100,EADMDATE=10,ESTATUS=2,
 EENDDATE=10,ECLASS=19,EEMGNAME=20,EREL=2,EEMGPHONE=20)
for i,f in enumerate(fields,1):
 name=f['dds'];width=widths.get(name,0)
 if name:
  out += [f'{name}=Window(raw.values({i}):0:{width}:windowUsed({i}):windowAdvance);',f'prior({i})={name};']
  read += [f'ReadEdited({i}:{name});']
(B/'copy/STUEDITOUT.rpgleinc').write_text('\n'.join(out)+'\n','utf8')
(B/'copy/STUEDITIO.rpgleinc').write_text('\n'.join(read)+'\n','utf8')

limits=['select;']+[f"when field={f['index']};limit={f['rawMax']};" for f in fields]+['other;limit=320;endsl;']
(B/'copy/STUEDITLIMIT.rpgleinc').write_text('\n'.join(limits)+'\n','utf8')
