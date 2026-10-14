"""Fresh errata copy of QA prose, never edits specification/artifact bytes."""
from pathlib import Path
import hashlib,json
R=Path(__file__).parent
p=R/'ASSISTED-TABLES-DELIVERY-R03.md';original=p.read_bytes();text=original.decode('utf8')
a='実XLSXのstyles/sharedStringsも一致し、sheet XMLは4行の高さ以外一致した。'
b='実XLSXのstyles/sharedStrings/table bytesも一致した。sheet XML差分は4行の高さとArtifact Toolが生成するtable relationship IDであり、同一targetとtarget bytesを解決照合した上で他の全XML一致を検査した。'
assert text.count(a)==1
corrected=R/'ASSISTED-TABLES-DELIVERY-R03B.md'
with corrected.open('x',encoding='utf8') as stream:stream.write(text.replace(a,b)+'\n旧QA説明R03の「sheet XMLは4行の高さ以外一致」という記述を訂正した。機械QA JSONは当初から同一targetを持つrelationship ID差分を記録しており、その検査結果・原稿・生成物は変更していない。\n')
record={'scope':'QA prose errata only','priorReport':str(p),'priorSha256':hashlib.sha256(original).hexdigest(),'priorPreserved':p.read_bytes()==original,'correctedReport':str(corrected),'correctedSha256':hashlib.sha256(corrected.read_bytes()).hexdigest(),'artifactBytesEdited':False}
with (R/'assisted-tables-r03-report-errata.json').open('x',encoding='utf8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2)
print(json.dumps(record,ensure_ascii=False))
