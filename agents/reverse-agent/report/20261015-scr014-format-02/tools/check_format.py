"""Check reversible formatting and preserve all business clauses exactly."""
import hashlib,json,re
from pathlib import Path
W=Path(__file__).resolve().parent;REV=W.parents[1];R=REV/'report'/W.name
canonical='基本設計書/基本設計書_SCR-014_日次 _ 月次処理.md'
old=(REV/'output/md'/canonical).read_text('utf8');new=(W/'draft'/canonical).read_text('utf8');rules=json.loads((W/'hierarchy.json').read_bytes());mapping=json.loads((R/'numbering-map.json').read_bytes())
restored=new.replace('"version":"1.3"','"version":"1.2"').replace('文書版：1.3','文書版：1.2')
for c in rules['referenceCorrections']:restored=restored.replace(c['to'],c['from'])
for rule in rules['groups']:
 start=restored.index('### '+rule['section']+'\n');end=restored.find('\n### ',start+4)
 if end<0:end=len(restored)
 part=restored[start:end]
 for parent,g in enumerate(rule['groups'],1):
  label=f'**{parent}. {g["title"]}**';assert part.count(label)==1;part=part.replace(label,'')
  for child,oldnum in enumerate(g['steps'],1):
   label=f'　**{parent}.{child}.** ';assert part.count(label)==1;part=part.replace(label,f'{oldnum}. ',1)
 restored=restored[:start]+part+restored[end:]
clean=lambda text:'\n'.join(l for l in text.splitlines() if l.strip() and not l.startswith('根拠：'))
assert clean(old)==clean(restored),'Unexpected business or diagram change'
assert '根拠：' not in new
e=json.loads((R/'source-evidence.json').read_bytes());assert len(e['citations'])==sum(l.startswith('根拠：') for l in old.splitlines())==24
m=json.loads((W/'view-model.json').read_bytes())
assert not any('根拠：' in op['value'] for s in m['sheets'] for op in s['operations'])
for x in mapping['steps']:
 value=x['text']
 for c in rules['referenceCorrections']:value=value.replace(c['from'],c['to'])
 assert f'**{x["newNumber"]}.** '+value in new
result={'schema':'scr014-format-equivalence/1','status':'PASS','version':'1.3','markdownSha256':hashlib.sha256((W/'draft'/canonical).read_bytes()).hexdigest(),'citationParagraphsMoved':24,'hierarchicalSections':len(rules['groups']),'hierarchicalSteps':len(mapping['steps']),'nonFormattingContentExactlyPreserved':True,'referenceCorrections':rules['referenceCorrections'],'newSourceAnalysis':False,'qaModified':False}
(R/'format-equivalence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result,ensure_ascii=False))
