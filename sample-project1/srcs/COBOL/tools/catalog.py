"""Fixed SQL parameter metadata; never infer the SQL type from user values."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
fixed={
 'ST-LOAD':[19], 'ST-UQ':[15,19,19], 'ST-CODE':[24,10],
 'ST-CLASS':[19], 'ST-CAP':[19,19,19], 'ST-YEAR':[4],
 'MC-LOAD':[19], 'MC-REF':[19], 'MC-UQ':[4,9,19,19],
 'MC-NAME':[4,2,36,19,19], 'MK-CATEGORY':[24], 'MK-LOAD':[24,10],
 'LOG-INSERT':[35,11,19,19,1024,128,33,36,120,1],
 'MAINT-LOG':[21,35,11,19,19,1024,128,33,36,120]
}
rows=[];contracts=[]
for p in sorted((ROOT/'sql').glob('*.sql')):
 sql=p.read_text(encoding='utf-8').strip().rstrip(';')
 declared=re.findall(r'@\w+\s+(\w+)(?:\((\d+|max)\))?\s*=\s*\?',sql,re.I)
 if declared:
  sizes=[]
  for typ,n in declared:
   sizes.append(int(n) if n.isdigit() and typ.lower() not in ['datetimeoffset','datetime2'] else
    {'bigint':19,'smallint':5,'int':10,'bit':1,'date':10,'datetimeoffset':33,'datetime2':27}.get(typ.lower(),1024))
 else:sizes=fixed.get(p.stem,[])
 if len(sizes)!=sql.count('?'):raise ValueError(f'{p.stem}: declared parameter count mismatch')
 rows.append('{'+json.dumps(p.stem)+','+json.dumps(sql,ensure_ascii=False)+','+str(len(sizes))+',{'+','.join(map(str,sizes or [0]))+'}}')
 contracts.append({'command':p.stem,'parameters':len(sizes),'columnSizes':sizes,'path':'sql/'+p.name})
(ROOT/'bridge/sql_catalog.h').write_text('/* fixed SQL and declared ODBC parameter widths */\nstatic const struct {const char *id;const char *sql;int count;unsigned long sizes[40];} catalog[]={\n'+',\n'.join(rows)+'\n};\n',encoding='utf-8')
(ROOT/'tools/sql-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n',encoding='utf-8')
print(f'Catalog: {len(rows)} commands; every parameter has a declared ColumnSize.')
