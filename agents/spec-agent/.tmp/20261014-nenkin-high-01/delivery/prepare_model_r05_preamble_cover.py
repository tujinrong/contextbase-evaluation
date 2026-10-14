"""Generic sheet placement only: preserve source literals, never compose business prose."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

D=Path(__file__).parent
O=Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01")
source=D/"delivery_model_v2_62_r04.py"; raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=="45d58010da0bd0de9317f40a4cc82881086e115ddf80f67c7dbb07bb47b47791"
text=raw.decode("utf-8").replace("\r\n","\n")
start=text.index("        cover=new_sheet('表紙','cover',47)")
end=text.index("        sheets.append(cover);used.add('表紙'.casefold())",start)
block=text[start:end]
helper="\ndef cover_sheet(entry, title, preamble):\n"+"\n".join(line[4:] for line in block.rstrip().splitlines())+"\n    return cover\n\n"
helper+="def preamble_sheet_name(declarations):\n    # The formatter-added name never changes any declared source sheet name.\n    used={'表紙'.casefold()} | {d['sheet'].casefold() for d in declarations}\n    base='文書属性'; candidate=base; index=2\n    while candidate.casefold() in used:\n        candidate=f'{base}_{index}'; index+=1\n    return candidate\n\n"
assert text.count("\ndef document_model(")==1
text=text.replace("\ndef document_model(",helper+"\ndef document_model(",1)
assert text.count(block)==1
text=text.replace(block,"        cover=cover_sheet(entry,title,preamble)\n",1)
guard="        if preamble and (not declarations or declarations[0]['kind']!='GRID'):\n            raise ValueError('Preamble preservation requires the first declared GRID chapter')\n"
assert text.count(guard)==1
text=text.replace(guard,"        if preamble and not declarations: raise ValueError('Preamble has no declared source chapter')\n",1)
insert="        sheets.append(cover);used.add('表紙'.casefold())\n"
assert text.count(insert)==1
text=text.replace(insert,insert+"        if preamble and declarations[0]['kind']=='LIST':\n            attributes=new_sheet(preamble_sheet_name(declarations),'normal',GRID_COLUMNS)\n            attributes['formatterAddedPreambleSheet']=True\n            add_blocks(attributes,preamble,1,image_max_width)\n            sheets.append(attributes);used.add(attributes['name'].casefold())\n",1)
assert text.count("        sheets=[sheet]\n")==1
text=text.replace("        sheets=[sheet]\n","        if sheet['name'].casefold()=='表紙'.casefold(): raise ValueError('Declared TABLE sheet conflicts with formatter cover')\n        sheets=[cover_sheet(entry,title,preamble),sheet]\n",1)
ast.parse(text)
out=D/"delivery_model_v2_62_r05.py"
if out.exists():
    assert out.read_bytes()==text.encode("utf-8")  # preserve initial unqualified code candidate
else:
    with out.open("xb") as h:h.write(text.encode("utf-8"))
assert source.read_bytes()==raw
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
old=load(source,"model_r04_pure_placement")
new=load(out,"model_r05_pure_placement")
checks=[]
def check(name,wanted,seen):
    ok=wanted==seen;checks.append({'name':name,'pass':ok});assert ok,name
def fixture(meta,preamble,chapters):
    md='<!-- spec-meta: '+json.dumps(meta,ensure_ascii=False)+' -->\n# Toy specification\n'+preamble+'\n'+chapters
    return {'documentId':meta['documentId'],'canonicalDocumentPath':meta['path'],'markdown':'synthetic-only.md','markdownSha256':hashlib.sha256(md.encode()).hexdigest(),'renderDirectory':'synthetic-only','renderPinsSha256':'0'*64,'renderManifestSha256':'0'*64,'rawMarkdown':md,'images':[]}
def meta(decl):return {'schema':'spec-md/1.0','documentId':'TOY','version':'1.0','path':'toy.md','sheets':decl}
def normal_meta():return meta([{'heading':'Body','kind':'GRID','sheet':'Normal'}])
normal=fixture(normal_meta(),'ID TOY\n\n|Name|Value|\n|---|---|\n|Version|1.0|','## Body\nLiteral unchanged 001 令和01年 =x\n')
check('normal-first route deep identical',old.document_model(normal),new.document_model(normal))
reference=json.loads((Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\src\docsite\v2\reference_format.json')).read_text(encoding='utf-8'))
def find_merge_sets(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('mergedRanges','mergedCells','merges','mergeRanges') and isinstance(v,list) and len(v)==14:yield set(v)
            yield from find_merge_sets(v)
    elif isinstance(value,list):
        for v in value:yield from find_merge_sets(v)
reference_merges=next(find_merge_sets(reference))
listdecl=[{'heading':'First list','kind':'LIST','sheet':'文書属性'},{'heading':'Body','kind':'GRID','sheet':'文書属性_2'}]
for count in (0,1,4):
    preamble='ID TOY\n\nPreamble text 001 =value 令和01年\n\n'+('|Key|Value|\n|---|---|\n'+''.join(f'|K{i}|V{i}|\n' for i in range(count)) if count else '')
    entry=fixture(meta(listdecl),preamble,'## First list\n|A|B|C|\n|---|---|---|\n|001|令和01年|=literal|\n\n## Body\nEnd unchanged\n')
    result=new.document_model(entry)
    check(f'LIST-first {count} sheet order',['表紙','文書属性_3','文書属性','文書属性_2'],[s['name'] for s in result['sheets']])
    check(f'LIST-first {count} exact cover merges',reference_merges,{op['range'] for op in result['sheets'][0]['operations']})
    check(f'LIST-first {count} list row1/header columns',('A1:A1',3), (result['sheets'][2]['operations'][0]['range'],result['sheets'][2]['columns']))
    _,_,parsed_pre,_=new.parse_markdown(entry['rawMarkdown'],[])
    expected=[b['text'] for b in parsed_pre if b['kind'] not in ('table','image')]+[v for b in parsed_pre if b['kind']=='table' for r in b['matrix'] for v in r]
    check(f'LIST-first {count} full preamble literal and order',expected,[op['value'] for op in result['sheets'][1]['operations']])
    check(f'LIST-first {count} retained numeric/formula/era literals',['001','令和01年','=literal'],[op['value'] for op in result['sheets'][2]['operations']][-3:])
    check(f'LIST-first {count} no invented cover values',True,all(op['value']=='' for op in result['sheets'][0]['operations'] if op.get('formatOnlyBlank')))
tablemeta={'schema':'spec-md/1.1','documentId':'TOY','version':'1.0','path':'toy.md','layout':'TABLE','columns':new.TABLE_COLUMNS,'sheets':[{'sheet':'TableLiteral'}],'sections':[{'heading':'テーブルヘッダー','kind':'HEADER'},{'heading':'項目詳細','kind':'LIST'}]}
tablechap='## テーブルヘッダー\n|Key|Value|\n|---|---|\n|Physical|toy_table|\n\n## 項目詳細\n|'+'|'.join(new.TABLE_COLUMNS)+'|\n|'+'|'.join(['---']*9)+'|\n|1|Name|field_id||NOT NULL|string|001||令和01年|\n'
for prefix in ('','ID TOY\n\n|Key|Value|\n|---|---|\n|Version|1.0|\n'):
    entry=fixture(tablemeta,prefix,tablechap);previous=old.document_model(entry);result=new.document_model(entry)
    check('TABLE single nine-column content deep unchanged '+str(bool(prefix)),previous['sheets'],result['sheets'][1:])
    check('TABLE14-frame formatter cover '+str(bool(prefix)),reference_merges,{op['range'] for op in result['sheets'][0]['operations']})
    check('TABLE raw metadata/coverage unchanged '+str(bool(prefix)),(previous['sourceMetadata'],previous['visibleCoverage'],previous['rawMarkdown']),(result['sourceMetadata'],result['visibleCoverage'],result['rawMarkdown']))
    check('TABLE company top-only style '+str(bool(prefix)),'cover-company-band',next(o['style'] for o in result['sheets'][0]['operations'] if o['range']=='O36:AU36'))
    check('TABLE nine-cell blank/value row literal '+str(bool(prefix)),['1','Name','field_id','','NOT NULL','string','001','','令和01年'],[o['value'] for o in result['sheets'][1]['operations']][-9:])
before={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
after={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
check('function AST delta only generic sheet placement',['cover_sheet','document_model','preamble_sheet_name'],changed)
receipt={'scope':'MECHANICAL_SHEET_PLACEMENT_AND_SYNTHETIC_PARSER_ONLY','status':'PASS','count':len(checks),'checks':checks,
 'source':{'path':str(source),'sha256':hashlib.sha256(raw).hexdigest()},'candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},
 'rule':'Cover O6:AU36 always14frames; LIST-first preamble on collision-safe normal62 sheet before declared chapters; TABLE has one declared9-column content sheet plus formatter cover.',
 'businessTextAuthored':False,'productionBusinessReads':0,'providerExecuted':0,'artifactAuthoring':0,'originalMetadataAndSourceOrderPreserved':True,
 'limitations':['Synthetic complete-shape parsing only; actual native readability and coverage must be confirmed after authoring.','Additional formatter cover does not constitute an additional declared business chapter.']}
record=O/'model-r05-preamble-cover-probes.json'
with record.open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'model':str(out),'sha256':receipt['candidate']['sha256'],'receipt':str(record),'receiptSha256':hashlib.sha256(record.read_bytes()).hexdigest(),'checks':len(checks)}))
