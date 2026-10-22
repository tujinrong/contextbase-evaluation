"""Independent narrow cover tests: actual metadata paragraph fixture + old tables.
AST-extract four mechanical functions only, no model/parser/core import/run.
"""
from pathlib import Path
import ast,copy,hashlib,json,re
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK=ROOT/'.tmp/20261014-nenkin-high-01';AUDIT=ROOT/'report/20261014-nenkin-high-01/independent-audit'
OLD=WORK/'delivery/delivery_model_v2_62_r06.py';NEW=WORK/'delivery/delivery_model_v2_62_r07.py'
MD=WORK/'drafts/author-wave-01/specifications/basic/menu.md'
PINS={str(OLD):'f8bacc711c751659ef0a6497c46e76a496833d20e311cd234111baa7042a1c31',
    str(NEW):'6c131e462b0982667c96af5b89e250009628a8f9be61317fefb51471204d48cd',
    str(MD):'ad5aa8b173a92bd3c3633075be14a82ed19f9a83ffec7cf08d7db7a1e2120955'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert all(sha(path)==value for path,value in PINS.items())
old,new=ast.parse(OLD.read_bytes()),ast.parse(NEW.read_bytes())
ofd={node.name:node for node in old.body if isinstance(node,ast.FunctionDef)}
nfd={node.name:node for node in new.body if isinstance(node,ast.FunctionDef)}
results=[]
def check(name,fn,reject=False):
    try:fn()
    except (ValueError,AssertionError,KeyError,TypeError) as exc:results.append({'name':name,'passed':reject,'exceptionType':type(exc).__name__})
    else:results.append({'name':name,'passed':not reject})
def assertion(condition):assert condition
check('all other old functions exact AST including preamble NORMAL LIST TABLE and explicitapproval mapper',lambda:assertion(
    all(ast.dump(node,include_attributes=False)==ast.dump(nfd[name],include_attributes=False) for name,node in ofd.items() if name!='cover_sheet')))
assignments=lambda tree:{node.targets[0].id:ast.dump(node,include_attributes=False) for node in tree.body
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
check('all existing module constants and assignments exact AST',lambda:assertion(assignments(old)==assignments(new)))
def namespace(tree,functions):
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in functions]
    assert {node.name for node in nodes}==functions
    ns={'re':re,'GRID_COLUMNS':62,'GRID_COLUMN_WIDTH':3,
        'COVER_EXTRA_FRAMES':['O23:Y23','Z23:AJ23','AK23:AU23','O24:Y28','Z24:AJ28','AK24:AU28','O36:AU36']}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'cover-ast-isolated','exec'),ns)
    return ns
oldns=namespace(old,{'new_sheet','cover_extra_operations','cover_sheet'})
newns=namespace(new,{'new_sheet','cover_extra_operations','cover_sheet','cover_attribute_records'})
table={'kind':'table','matrix':[['属性','値'],['文書番号','000123'],['版','1:0:beta'],['対象','']], 'sourceLines':[4,8]}
def old_table():
    source=[copy.deepcopy(table)];before=copy.deepcopy(source)
    assert newns['cover_sheet']({},'title',source)==oldns['cover_sheet']({},'title',source)
    assert source==before
check('old two-column table cover output exactly unchanged and input untouched',old_table)
check('empty preamble cover output exactly unchanged',lambda:assertion(newns['cover_sheet']({},'title',[])==oldns['cover_sheet']({},'title',[])))
check('non-two-column table remains ignored for attributes',lambda:assertion(newns['cover_attribute_records']([{'kind':'table','matrix':[['a','b','c'],['1','2','3']]}])==[]))
# Expected pre-parsed paragraph from observed actual MD lines4--8. Only the
# Markdown hardbreak syntax trailing two spaces is omitted in this fixture.
# The real MarkdownIt parser is NOT run or imported; that integration is pending.
lines=MD.read_bytes().decode('utf-8').splitlines()
observed=lines[3:8]
text='\n'.join(line[:-2] if line.endswith('  ') else line for line in observed)
paragraph={'kind':'paragraph','text':text,'sourceLines':[4,8]}
records=newns['cover_attribute_records']([paragraph])
check('actual observed preamble first3 pairs exact explicit labels/values',lambda:assertion([r['values'] for r in records[:3]]==[
    ['文書ID','SCR-017'],['文書種別','基本設計書'],['版','1.0']]))
def paragraph_cover():
    source=[copy.deepcopy(paragraph)];before=copy.deepcopy(source)
    cover=newns['cover_sheet']({},'title',source)
    assert [op['value'] for op in cover['operations'][1:7]]==['文書ID','SCR-017','文書種別','基本設計書','版','1.0']
    assert len(cover['operations'])==14 and cover['lastRow']==36 and cover['columns']==47
    assert [op['range'] for op in cover['operations'][1:7]]==['O12:W14','X12:AU14','O15:W17','X15:AU17','O18:W20','X18:AU20']
    assert all(op['value']=='' and op['formatOnlyBlank'] is True for op in cover['operations'][7:])
    assert source==before
check('actual paragraph fixes 3cover pairs withoutgeometry approval or company inference',paragraph_cover)
check('paragraph provenance ordinal and inverse literal line retained',lambda:assertion(all(
    record['sourceAttribute']['sourceParagraphLineOrdinal']==ordinal and
    record['sourceAttribute']['sourceBlockLines']==[4,8] and
    record['sourceAttribute']['label']+record['sourceAttribute']['separator']+record['sourceAttribute']['value']==record['sourceAttribute']['literalText'] and
    record['sourceAttribute']['inverseRestoresLiteralLine'] is True
    for ordinal,record in enumerate(records,1))))
def literals():
    value={'kind':'paragraph','text':'番号:00001234\nURL：http://a:b\n 空白ラベル ：  値:末尾  ','sourceLines':[4,6]}
    records=newns['cover_attribute_records']([value])
    assert [r['values'] for r in records]==[['番号','00001234'],['URL','http://a:b'],[' 空白ラベル ','  値:末尾  ']]
    assert [r['sourceAttribute']['separator'] for r in records]==[':','：','：']
check('leadingzeros fullwidth ASCII separator additionalcolons and spaces literal',literals)
for text_value in ['文書ID：SCR-017','文書ID：SCR-017\nnot a pair','\n文書ID：SCR-017',' ：value\n版：1.0']:
    check('incomplete/ambiguous paragraph not partially inferred '+repr(text_value),lambda text_value=text_value:assertion(newns['cover_attribute_records']([{'kind':'paragraph','text':text_value}])==[]))
check('explicit empty values stay empty',lambda:assertion([r['values'] for r in newns['cover_attribute_records']([{'kind':'paragraph','text':'A:\nB：'}])]==[['A',''],['B','']]))
def order():
    first={'kind':'paragraph','text':'A:1\nB:2','sourceLines':[4,5]}
    second={'kind':'table','matrix':[['label','value'],['C','3'],['D','4']],'sourceLines':[7,10]}
    assert [r['values'] for r in newns['cover_attribute_records']([first,second])]==[['A','1'],['B','2'],['C','3'],['D','4']]
    assert [r['values'] for r in newns['cover_attribute_records']([second,first])]==[['C','3'],['D','4'],['A','1'],['B','2']]
    assert [op['value'] for op in newns['cover_sheet']({},'title',[first,second])['operations'][1:7]]==['A','1','B','2','C','3']
check('paragraph and oldtable attributes retain source block order and first3slots',order)
def bindings():
    preamble=[copy.deepcopy(paragraph),copy.deepcopy(table)]
    entry={'coverBindings':[{'range':'O23:Y23','sourceTable':0,'sourceRow':1,'sourceColumn':1},
        {'range':'O36:AU36','sourceTable':0,'sourceRow':2,'sourceColumn':1}]}
    ops=newns['cover_extra_operations'](entry,preamble)
    assert ops==oldns['cover_extra_operations'](entry,preamble)
    assert ops[0]['value']=='000123' and ops[-1]['value']=='1:0:beta'
    assert ops[0]['sourceCellBinding']['sourceTable']==0 and ops[-1]['sourceCellBinding']['sourceTable']==0
check('explicitapproval and company bindings still use only originaltable index0',bindings)
check('paragraph cannot masquerade as explicitapproval source table',lambda:newns['cover_extra_operations'](
    {'coverBindings':[{'range':'O23:Y23','sourceTable':0,'sourceRow':0,'sourceColumn':0}]},[paragraph]),True)
check('duplicate explicitapproval frame binding still refused',lambda:newns['cover_extra_operations'](
    {'coverBindings':[{'range':'O23:Y23','sourceTable':0,'sourceRow':1,'sourceColumn':1}]*2},[table]),True)
assert all(sha(path)==value for path,value in PINS.items())
report={'schema':'spec-agent-cover-paragraph-r07-independent-narrow-review/1',
    'status':'PASS_CODE_AND_AST_ISOLATED_COVER_SCOPE_ONLY' if all(r['passed'] for r in results) else 'HOLD_NARROW_COVER_FAILURE',
    'reviewer':'/root/delivery_root_review/supplement_collector_review','pinnedFilesBeforeAfter':PINS,
    'unchangedInputsBeforeAfter':True,'testCount':len(results),'passedCount':sum(r['passed'] for r in results),'tests':results,
    'actualObservedPreambleFixture':{'sourceLines':[4,8],'sourceSha256':PINS[str(MD)],
        'construction':'Expected pre-parsed paragraph from actual observed source lines; Markdown trailing two-space hardbreak presentation markers omitted. Actual MarkdownIt parser not executed.'},
    'separatorBoundary':'Original paragraph and audit sourceAttribute retain exact separator. Projected cover puts label and value in separate cells and does not display the separator character in the label cell; this formatting scope must be accepted explicitly.',
    'limitations':{'modelOrMarkdownParserImportedOrRun':False,'frozenCoreOrSourceRuntimeImported':False,
        'originalInputSpecEvalOrOldOutputRead':False,'actualXlsxOrPdfOrNativeCreatedOrReviewed':False,
        'providerOrBrowserOrMarkersRun':False,'businessProseRewritten':False,'semanticApproval':False,
        'actualParagraphTokenizationIntegrationVerified':False,'actual14MergedRegionXlsxVerified':False,
        'profileAndBuilderRebindingPerformed':False,'publicationApproved':False},
    'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))}}
out=AUDIT/'model-r07-cover-paragraph-independent-review-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':report['status'],'tests':len(results),'passed':report['passedCount'],'failures':[r for r in results if not r['passed']],
    'report':str(out),'sha256':sha(out)}))
if not all(r['passed'] for r in results):raise SystemExit(1)
