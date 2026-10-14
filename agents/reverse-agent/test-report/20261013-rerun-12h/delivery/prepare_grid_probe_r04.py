from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
P=Path(__file__).resolve().parent
old=P/'probe_grid_columnwidth_r03.mjs';new=P/'probe_grid_columnwidth_r04.mjs'
assert not new.exists()
s=old.read_text(encoding='utf8')
assert s.count("op.style!=='body'")==1
s=s.replace("op.style!=='body'","!['body','table-cell'].includes(op.style)")
assert s.count('const target=s.getRange(op.range);target.merge();')==1
s=s.replace('const target=s.getRange(op.range);target.merge();',"const target=s.getRange(op.range);target.merge();if(op.style==='table-cell')target.format.borders={preset:'outside',style:'thin',color:'#808080'};")
new.write_text(s,encoding='utf8')
out=P/'grid-columnwidth-probe-r03-failure.json';assert not out.exists()
out.write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'status':'CODE_SCOPE_REJECTED_TABLE_CELL_FIXTURE','providerInvoked':False,'xlsxCreated':False,'inputsModified':False,'oldCodeSha256':hashlib.sha256(old.read_bytes()).hexdigest(),'code':str(old),'freshCode':str(new)},indent=2)+'\n',encoding='utf8')
print(str(new))
