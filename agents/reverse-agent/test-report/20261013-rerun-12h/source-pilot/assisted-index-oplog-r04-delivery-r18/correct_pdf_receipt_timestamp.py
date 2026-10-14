from pathlib import Path
from datetime import datetime,timezone
import json
HERE=Path(__file__).absolute().parent
d=json.loads((HERE/'pdf-actual-view-log.json').read_text(encoding='utf8'))
d.pop('completedUtc')
d['sealedObservedUtc']=datetime.now(timezone.utc).isoformat()
d['timestampCorrection']='Prior completedUtc was an unsupported handwritten value; actual 49 page observations are unchanged. This fresh log supersedes timestamp metadata only.'
p=HERE/'pdf-actual-view-log-r02.json';assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
s=(HERE/'seal_pdf_qa.py').read_text(encoding='utf8').replace('pdf-actual-view-log.json','pdf-actual-view-log-r02.json').replace("p=HERE/'pdf-review.json'","p=HERE/'pdf-review-r02.json'")
p=HERE/'seal_pdf_qa_r02.py';assert not p.exists();p.write_text(s,encoding='utf8')
