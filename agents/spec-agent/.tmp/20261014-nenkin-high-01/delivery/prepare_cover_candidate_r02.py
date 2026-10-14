"""Fresh V2 cover geometry projection. No business input or Workbook authoring."""
import ast,hashlib,json,math,re
from pathlib import Path
from datetime import datetime,timezone
R=Path(r'D:\開発\contextbase-evaluation')
D=R/'agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery'
O=R/'agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
origins=[D/'delivery_model_v2_62_r01.py',D/'build_xlsx_v2_62_r01.mjs',D/'format-profile-v2-62-r01.json']
before={str(p):sha(p) for p in origins}
assert list(before.values())==['d85cdc40ec8bcad7eadd174b15254212164aa0c129178347fe6a4838d87dfaf4','d70a0eb222b68869e93e8bd33f2b4e415e6553698f75d0931f96c3fa24a8e5c8','aeeffe5ce926b648ba678302340f22afc52c91775177f4b284da40a5b24e9d13']
model=origins[0].read_text(encoding='utf-8');builder=origins[1].read_text(encoding='utf-8');changes=[]
def replace(text,old,new,label):
    assert text.count(old)==1,label
    changes.append({'label':label,'old':old,'new':new});return text.replace(old,new,1)
helper='''
APPROVAL_FRAMES = ['O23:Y23','Z23:AJ23','AK23:AU23','O24:Y28','Z24:AJ28','AK24:AU28']
COVER_EXTRA_FRAMES = APPROVAL_FRAMES + ['O36:AU36']
def cover_extra_operations(entry, preamble):
    # Explicit caller mapping references an existing Markdown preamble table cell.
    # Never guess approval/company values from source code, names or neighboring cells.
    bindings=entry.get('coverBindings',[])
    if not isinstance(bindings,list):raise ValueError('Explicit cover mapping must be a list')
    tables=[b for b in preamble if b['kind']=='table'];selected={}
    for item in bindings:
        if set(item)!={'range','sourceTable','sourceRow','sourceColumn'}:raise ValueError('Unknown cover source mapping fields')
        target=item['range']
        if target not in COVER_EXTRA_FRAMES or target in selected:raise ValueError('Unknown/duplicate cover frame target')
        indexes=[item[k] for k in ('sourceTable','sourceRow','sourceColumn')]
        if any(type(n) is not int or n<0 for n in indexes):raise ValueError('Cover source indexes must be explicit nonnegative integers')
        a,b,c=indexes
        if a>=len(tables) or b>=len(tables[a]['matrix']) or c>=len(tables[a]['matrix'][b]):raise ValueError('Cover source cell outside original preamble')
        value=tables[a]['matrix'][b][c]
        if not isinstance(value,str) or len(value.encode('utf-16-le'))//2>32767 or any(ord(ch)<32 and ch not in '\\t\\r\\n' for ch in value):raise ValueError('Cover literal cannot be represented')
        selected[target]=(value,tables[a]['sourceLines'],dict(item))
    operations=[]
    for target in COVER_EXTRA_FRAMES:
        value,lines,binding=selected.get(target,('',None,None))
        operation={'range':target,'value':value,'style':'cover-company-band' if target=='O36:AU36' else 'cover-cell','sourceLines':lines,'formatOnlyBlank':binding is None}
        if binding:operation['sourceCellBinding']=binding
        operations.append(operation)
    return operations
'''
model=replace(model,"def new_sheet(name, role, columns):",helper+"\ndef new_sheet(name, role, columns):",'explicit-literal-cover-mapping-and-seven-empty-frames')
model=replace(model,"        sheets.append(cover);used.add('表紙'.casefold())","        cover['operations'].extend(cover_extra_operations(entry,preamble))\n        sheets.append(cover);used.add('表紙'.casefold())",'cover-add-seven-format-only-merges')
model=replace(model,"sheet=new_sheet(decl['sheet'],'list',len(matrix[0]))\n                add_matrix", "sheet=new_sheet(decl['sheet'],'list',len(matrix[0]))\n                sheet['itemList']=section['heading']=='項目一覧'\n                add_matrix",'item-list-explicit-flag-for-print-plan')
model=replace(model,"'id':'v2-62-user-selected'","'id':'v2-62-preserved-reference'",'profile-id-interpreted-v2-basis')
builder=replace(builder,"'v2-62-user-selected'","'v2-62-preserved-reference'",'builder-profile-id-interpreted-v2-basis')
builder=replace(builder,"        else if(operation.style==='cover-title')outside(range,'double','#595959');", "        else if(operation.style==='cover-title')outside(range,'double','#595959');\n        else if(operation.style==='cover-company-band')range.format.borders={top:{style:'thin',color:light}};",'company-band-top-thin-only')
ast.parse(model)
mp=D/'delivery_model_v2_62_r02.py';bp=D/'build_xlsx_v2_62_r02.mjs';fp=D/'format-profile-v2-62-r02.json'
for p,text in [(mp,model),(bp,builder)]:
    with p.open('x',encoding='utf-8') as f:f.write(text)
profile=json.loads(origins[2].read_text(encoding='utf-8'));profile['id']='v2-62-preserved-reference';profile.pop('userOverrideOfProjectGrid120')
profile.update(selectionBasis='INTERPRETATION_OF_REQUEST_TO_PRESERVE_EXISTING_V2_FORMAT',userExplicitlySpecified62=False,projectGrid120OverriddenForThisRun=True,referencePins={str(R/'agents/reverse-agent/AGENTS.md'):sha(R/'agents/reverse-agent/AGENTS.md'),str(R/'agents/reverse-agent/src/docsite/v2/reference_format.json'):sha(R/'agents/reverse-agent/src/docsite/v2/reference_format.json')})
profile['cover'].update(expectedMergedRegions=14,extraEmptyFrames=['O23:Y23','Z23:AJ23','AK23:AU23','O24:Y28','Z24:AJ28','AK24:AU28','O36:AU36'],companyBandBorder='top thin only',approvalValues='blank unless explicit bound original MD cell mapping')
profile['tableException']={'columns':9,'singleSheet':True,'literalBlanksPreserved':True}
profile['generalList']={'columns':'original declared matrix column count','itemListOnly10':True,'headerRow':1,'forcedGridConversion':False}
with fp.open('x',encoding='utf-8') as f:json.dump(profile,f,ensure_ascii=False,indent=2);f.write('\n')
tree=ast.parse(model);names={'cover_extra_operations'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
env={'APPROVAL_FRAMES':profile['cover']['extraEmptyFrames'][:6],'COVER_EXTRA_FRAMES':profile['cover']['extraEmptyFrames']}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(mp),'exec'),env)
fn=env['cover_extra_operations'];tests=[]
def check(name,func,reject=False):
    try:func()
    except ValueError:
        if not reject:raise
    else:
        if reject:raise AssertionError('Expected rejection '+name)
    tests.append({'name':name,'pass':True})
def eq(a,b):assert a==b,(a,b)
check('exact-seven-reference-ranges',lambda:eq([x['range'] for x in fn({},[])],profile['cover']['extraEmptyFrames']))
check('all-seven-values-default-blank',lambda:eq([x['value'] for x in fn({},[])],['']*7))
check('company-only-top-thin-style',lambda:eq(fn({},[])[-1]['style'],'cover-company-band'))
check('approval-six-thin-cover-cell-style',lambda:eq([x['style'] for x in fn({},[])][:-1],['cover-cell']*6))
table=[{'kind':'table','matrix':[['key','value'],['explicit','001']],'sourceLines':[3,5]}]
binding={'range':'O36:AU36','sourceTable':0,'sourceRow':1,'sourceColumn':1}
check('explicit-md-cell-value-copy-only',lambda:eq(fn({'coverBindings':[binding]},table)[-1]['value'],'001'))
check('explicit-md-cell-source-lines-bound',lambda:eq(fn({'coverBindings':[binding]},table)[-1]['sourceLines'],[3,5]))
check('duplicate-frame-rejected',lambda:fn({'coverBindings':[binding,binding]},table),True)
check('outside-AU-target-rejected',lambda:fn({'coverBindings':[{**binding,'range':'AV36:AW36'}]},table),True)
check('unknown-mapping-field-rejected',lambda:fn({'coverBindings':[{**binding,'value':'invented'}]},table),True)
check('out-of-source-cell-rejected',lambda:fn({'coverBindings':[{**binding,'sourceRow':2}]},table),True)
check('bool-source-index-rejected',lambda:fn({'coverBindings':[{**binding,'sourceColumn':True}]},table),True)
check('negative-source-index-rejected',lambda:fn({'coverBindings':[{**binding,'sourceTable':-1}]},table),True)
check('nonlist-mapping-rejected',lambda:fn({'coverBindings':{}},table),True)
huge=[{'kind':'table','matrix':[['x'*32768]],'sourceLines':[1,1]}]
check('too-long-cover-source-cell-rejected',lambda:fn({'coverBindings':[{**binding,'sourceRow':0,'sourceColumn':0}]},huge),True)
for p,h in before.items():assert sha(Path(p))==h
record={'schema':'spec-agent-cover-format-candidate/2','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'PREPARED_NOT_AUTHORING','oldPinsBeforeAfter':before,'candidatePins':{str(p):sha(p) for p in (mp,bp,fp)},'changes':changes,'syntheticTests':tests,'pass':len(tests),'businessInputRead':False,'providerExecuted':False,'artifactExecuted':False,'markerExecuted':False,'actualXlsxCreated':False,'selectionBasis':'62-column V2 profile derives from requested preservation of existing V2 format; no literal user 62 instruction is claimed.','remaining':['Actual cover 14 merges/borders/AV-outside neutrality and all three formats must be read back/rendered after Artifact authoring.','Any cover binding must be caller-pinned and refer only to a literal cell present in unchanged MD preamble.']}
p=O/'cover-candidate-r02-preparation.json'
with p.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p),'tests':len(tests)},ensure_ascii=False))

