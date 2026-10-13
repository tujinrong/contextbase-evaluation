"""Read newly frozen completed Markdown, preserving actual bounded ranges."""
from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
REPORT=Path(__file__).resolve().parent
stem,name,start,end=sys.argv[1:];start=int(start);end=int(end)
assert datetime.now(timezone.utc)<datetime.fromisoformat('2026-10-13T03:20:58+00:00')
p=REPORT/'frozen'/stem/(stem+'.md')
if not p.exists():p=REPORT/'frozen-text'/stem/(stem+'.md')
before=hashlib.sha256(p.read_bytes()).hexdigest()
lines=p.read_text(encoding='utf-8-sig').splitlines();assert 1<=start<=end<=len(lines)
print(str(p))
for i in range(start,end+1):print(f'{i}: {lines[i-1]}')
assert hashlib.sha256(p.read_bytes()).hexdigest()==before
with (REPORT/name).open('x',encoding='utf-8',newline='\n') as f:
    json.dump({'schema':'reverse-independent-current-md-read-boundaries/1','round':6,'readAt':datetime.now(timezone.utc).isoformat(),'stem':stem,'path':str(p),'sha256':before,'startLine':start,'endLine':end,'sourceBeforeAfterMatch':True,'imagesActuallyViewedByThisTextRead':0,'approval':None},f,ensure_ascii=False,indent=2);f.write('\n')
