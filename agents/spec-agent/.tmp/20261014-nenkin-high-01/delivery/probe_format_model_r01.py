"""AST-only, synthetic format probes. No imports from production and no business reads."""
import ast, hashlib, json, math, os, re
from pathlib import Path
from datetime import datetime, timezone
BASE=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
REPORT=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
OLD=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\delivery_model_r18_r02.py')
P=BASE/'delivery_model_v2_62_r01.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in (P,OLD,BASE/'build_xlsx_v2_62_r01.mjs',BASE/'format-profile-v2-62-r01.json')}
original=ast.parse(OLD.read_text(encoding='utf-8'));fresh=ast.parse(P.read_text(encoding='utf-8'))
old_functions={n.name:n for n in original.body if isinstance(n,ast.FunctionDef)}
functions={n.name:n for n in fresh.body if isinstance(n,ast.FunctionDef)}
selected={'col','a1','text_width','cell_height','new_sheet','add_text','add_matrix','add_blocks','document_model'}
columns=['No','論理名','物理名','PK','NOT NULL','タイプ','長さ','初期値','説明']
env={'math':math,'re':re,'GRID_COLUMNS':62,'GRID_COLUMN_WIDTH':3,'GRID_TEXT_UNITS_PER_COLUMN':2.75,'GRID_BODY_START_COLUMN':2,'GRID_IMAGE_MAX_WIDTH':1100,'FORMAT_PROFILE':{'id':'v2-62-user-selected'},'TABLE_COLUMNS':columns}
exec(compile(ast.Module(body=[functions[n] for n in selected],type_ignores=[]),str(P),'exec'),env)
entry={'documentId':'TOY-001','canonicalDocumentPath':'toy.md','markdown':'synthetic-only','markdownSha256':'0'*64,'renderDirectory':'synthetic-only','renderPinsSha256':'1'*64,'renderManifestSha256':'2'*64,'rawMarkdown':'synthetic-only','images':[]}
tests=[]
def check(name,fn,reject=False):
    try:fn()
    except ValueError:
        if not reject:raise
    else:
        if reject:raise AssertionError('Expected rejection '+name)
    tests.append({'name':name,'pass':True})
def eq(a,b):assert a==b,(a,b)
def setup(item_columns=10,preamble=None,sections_extra=None):
    meta={'schema':'spec-md/1.0','documentId':'TOY-001','path':'toy.md','sheets':[{'heading':'概要','kind':'GRID','sheet':'01_概要'},{'heading':'項目一覧','kind':'LIST','sheet':'02_項目一覧'},{'heading':'補足','kind':'GRID','sheet':'03_補足'}]}
    sections=[{'heading':'概要','blocks':[{'kind':'paragraph','text':'SYNTHETIC-001','sourceLines':[3,3]}]},
              {'heading':'項目一覧','blocks':[{'kind':'table','matrix':[[str(i) for i in range(item_columns)],['001','=1+1','令和06年04月01日','1.0',"'quote",'@name','+01','-01','9223372036854775807','line1\nline2'][:item_columns]],'sourceLines':[5,7]}]},
              {'heading':'補足','blocks':[]}]
    if sections_extra:sections_extra(meta,sections)
    p=[] if preamble is None else preamble
    env['parse_markdown']=lambda markdown,images:(meta,'Synthetic fixture',p,sections)
    return env['document_model'](entry)
def forms():
    d=setup();eq([s['role'] for s in d['sheets']],['cover','normal','list','normal']);eq([s['columns'] for s in d['sheets']],[47,62,10,62])
    eq(d['sheets'][0]['printArea'],'O6:AU36');eq(d['sheets'][1]['operations'][0]['range'],'A1:BJ1');eq(d['sheets'][2]['tables'][0]['headerRow'],1)
check('three-forms-47-cover-62-grid-10-item-list',forms)
check('item-list9-refused',lambda:setup(9),True)
def list_exact():
    d=setup();s=d['sheets'][2];eq([o['value'] for o in s['operations']][10:],['001','=1+1','令和06年04月01日','1.0',"'quote",'@name','+01','-01','9223372036854775807','line1\nline2']);eq(s['lastRow'],2)
check('list-values-newline-leading-zero-era-formula-literal-exact',list_exact)
def preamble():
    p=[{'kind':'paragraph','text':'TOY-ID 1.0','sourceLines':[2,2]},{'kind':'table','matrix':[['key','value'],['ID','001'],['version','1.0'],['era','令和06年04月01日'],['extra','=1+1']],'sourceLines':[3,8]}]
    d=setup(preamble=p);grid=d['sheets'][1];values=[o['value'] for o in grid['operations']]
    assert all(v in values for v in ['TOY-ID 1.0','001','1.0','令和06年04月01日','=1+1'])
    eq([o['range'] for o in d['sheets'][0]['operations']],['O6:AU9','O12:W14','X12:AU14','O15:W17','X15:AU17','O18:W20','X18:AU20'])
check('cover-first3-attributes-and-full-preamble-retained',preamble)
check('list-with-paragraph-rejected',lambda:setup(sections_extra=lambda m,s:s[1]['blocks'].append({'kind':'paragraph','text':'toy','sourceLines':[8,8]})),True)
check('list-with-second-table-rejected',lambda:setup(sections_extra=lambda m,s:s[1]['blocks'].append(s[1]['blocks'][0])),True)
check('undeclared-section-order-rejected',lambda:setup(sections_extra=lambda m,s:s.reverse()),True)
check('duplicate-sheet-casefold-rejected',lambda:setup(sections_extra=lambda m,s:m['sheets'][2].update(sheet='01_概要')),True)
check('unsafe-sheet-name-rejected',lambda:setup(sections_extra=lambda m,s:m['sheets'][2].update(sheet='unsafe/name')),True)
def table():
    meta={'schema':'spec-md/1.1','documentId':'TOY-001','path':'toy.md','layout':'TABLE','columns':columns,'sheets':[{'sheet':'toy_table'}],'sections':[{'heading':'テーブルヘッダー','kind':'HEADER'},{'heading':'項目詳細','kind':'LIST'}]}
    sections=[{'heading':'テーブルヘッダー','blocks':[{'kind':'table','matrix':[['key','value'],['literal','001']],'sourceLines':[2,4]}]}, {'heading':'項目詳細','blocks':[{'kind':'table','matrix':[columns,['01','toy','physical','','','nvarchar','0008','','=1+1']],'sourceLines':[6,8]}]}]
    env['parse_markdown']=lambda md,images:(meta,'Synthetic TABLE',[],sections)
    d=env['document_model'](entry);eq(len(d['sheets']),1);eq(d['sheets'][0]['role'],'table');eq(d['sheets'][0]['columns'],9)
    eq(d['sheets'][0]['tables'][0]['header'],columns)
    assert '' in [o['value'] for o in d['sheets'][0]['operations']]
check('TABLE9-single-sheet-blank-rules-retained',table)
check('image-width-exceeds1100-rejected',lambda:env['document_model'](entry,1101),True)
for name in ['safe_path','canonical','load_bound','inline_text','parse_markdown']:
    check('guard-and-parser-AST-unchanged-'+name,lambda name=name:eq(ast.dump(old_functions[name],include_attributes=False),ast.dump(functions[name],include_attributes=False)))
assert all(sha(Path(p))==h for p,h in before.items())
result={'schema':'spec-agent-format-model-probes/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'AST_FUNCTIONS_ONLY_SYNTHETIC','syntheticPassCount':len(tests),'tests':tests,'beforeAfterPins':before,'allPinnedBytesUnchanged':True,'actualMarkdownParserExecuted':False,'parseStubIsSyntheticOnly':True,'productionInputRead':False,'providerExecuted':False,'artifactToolExecuted':False,'markerExecuted':False,'workbookCreated':False,'outputModified':False}
target=REPORT/'model-guard-probes-r01.json'
with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target),'pass':len(tests)},ensure_ascii=False))
