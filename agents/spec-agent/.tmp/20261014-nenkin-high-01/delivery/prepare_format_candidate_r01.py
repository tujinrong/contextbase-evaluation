"""Prepare generic V2-62 geometry code only. Never reads a business input or creates XLSX."""
import ast, hashlib, json, math, os, re
from pathlib import Path
from datetime import datetime, timezone

REPO=Path(r'D:\開発\contextbase-evaluation')
OLD=REPO/'agents/reverse-agent/test-report/20261013-rerun-12h/delivery'
DEST=REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery'
REPORT=REPO/'agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01'

def safe(p):
    p=Path(os.path.abspath(p))
    for q in (p,*p.parents):
        if q.is_symlink() or (q.exists() and getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Linked path')
    return p
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
    p=safe(p)
    with p.open('xb') as f:f.write(b)

def main():
    DEST.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    source_paths=[OLD/'delivery_model_r18_r02.py',OLD/'build_xlsx_r18.mjs']
    before={str(p):digest(safe(p).read_bytes()) for p in source_paths}
    model=safe(source_paths[0]).read_text(encoding='utf-8')
    builder=safe(source_paths[1]).read_text(encoding='utf-8')
    changes=[]
    def replace(text,old,new,label):
        if text.count(old)!=1:raise ValueError('Expected exact single code anchor: '+label)
        changes.append({'label':label,'old':old,'new':new})
        return text.replace(old,new,1)
    model=replace(model,"SCHEMA = 'reverse-agent-delivery-model/1'", "SCHEMA = 'reverse-agent-delivery-model/1'\n# User-selected V2 format profile. No change to Markdown/source content.\nGRID_COLUMNS = 62\nGRID_COLUMN_WIDTH = 3\nGRID_TEXT_UNITS_PER_COLUMN = 2.75\nGRID_BODY_START_COLUMN = 2\nGRID_IMAGE_MAX_WIDTH = 1100\nFORMAT_PROFILE = {'id':'v2-62-user-selected','coverPrintArea':'O6:AU36','gridColumns':GRID_COLUMNS,'gridColumnWidth':GRID_COLUMN_WIDTH,'gridBodyStartColumn':GRID_BODY_START_COLUMN,'itemListColumns':10,'listHeaderRow':1,'literalStrings':True}", 'explicit-format-profile')
    model=replace(model,"    if role=='table':", "    if role=='normal':\n        if columns != GRID_COLUMNS: raise ValueError('V2-62 normal sheet geometry mismatch')\n        sheet['gridColumnWidth']=GRID_COLUMN_WIDTH\n    if role=='table':",'normal-grid-profile-gate')
    model=replace(model,"    width=sum(sheet['columnWidths'][left-1:right])*13/18 if 'columnWidths' in sheet else (right-left+1)*(2 if sheet['columns']==120 else 13)","    width=(right-left+1)*GRID_TEXT_UNITS_PER_COLUMN if sheet['role']=='normal' else sum(sheet['columnWidths'][left-1:right])*13/18 if 'columnWidths' in sheet else (right-left+1)*13",'62-column-readable-height-budget')
    model=replace(model,"for index in range(columns): spans.append((index*120//columns+1,(index+1)*120//columns))","for index in range(columns): spans.append((index*sheet['columns']//columns+1,(index+1)*sheet['columns']//columns))",'grid-spans-use-declared-canvas')
    model=replace(model,"grid=sheet['columns']==120","grid=sheet['role']=='normal'",'grid-table-role-not-magic-width')
    model=replace(model,"1 if block['kind']=='heading' or sheet['columns']!=120 else 21","1 if block['kind']=='heading' or sheet['role']!='normal' else GRID_BODY_START_COLUMN",'B-to-BJ-narrative-placement')
    model=replace(model,"if not 1100<=image_max_width<=1850:raise ValueError('Image projection must fit the documented GRID canvas')","if not 1<=image_max_width<=GRID_IMAGE_MAX_WIDTH:raise ValueError('Image projection exceeds bounded V2-62 canvas')",'bounded-images-no-outside-frame')
    model=replace(model,"matrix=blocks[0]['matrix']; sheet=new_sheet(decl['sheet'],'list',len(matrix[0]))","matrix=blocks[0]['matrix']\n                if section['heading']=='項目一覧' and len(matrix[0])!=10: raise ValueError('Item LIST requires the declared ten-column form')\n                sheet=new_sheet(decl['sheet'],'list',len(matrix[0]))",'item-list-ten-column-gate')
    model=replace(model,"sheet=new_sheet(decl['sheet'],'normal',120)\n                add_text(sheet,1,1,120,section['heading'],'title')","sheet=new_sheet(decl['sheet'],'normal',GRID_COLUMNS)\n                add_text(sheet,1,1,GRID_COLUMNS,section['heading'],'title')",'normal-62-title-and-frame')
    model=replace(model,"'title':title,'sourceMetadata':meta,'rawMarkdown':entry['rawMarkdown'], 'sheets':sheets,","'title':title,'sourceMetadata':meta,'rawMarkdown':entry['rawMarkdown'], 'formatProfile':FORMAT_PROFILE, 'sheets':sheets,",'document-format-profile-binding')
    model=replace(model,"'projection':{'imageMaxWidth':args.image_max_width,'previewMaxHeight':args.preview_max_height},","'formatProfile':FORMAT_PROFILE,\n           'projection':{'imageMaxWidth':args.image_max_width,'previewMaxHeight':args.preview_max_height},",'model-format-profile-binding')
    ast.parse(model)
    builder=replace(builder,"const modelRaw=await fs.readFile(modelPath);const model=JSON.parse(modelRaw.toString('utf8'));", "const modelRaw=await fs.readFile(modelPath);const model=JSON.parse(modelRaw.toString('utf8'));\nif(model.formatProfile?.id!=='v2-62-user-selected'||model.formatProfile.gridColumns!==62||model.formatProfile.coverPrintArea!=='O6:AU36'||model.formatProfile.itemListColumns!==10)throw new Error('Explicit user-selected V2-62 format profile required');",'builder-explicit-profile-gate')
    builder=replace(builder,"region.format.columnWidth=specification.columns===120?2:specification.role==='cover'?3:18;","if(specification.role==='normal'&&(specification.columns!==62||specification.gridColumnWidth!==3))throw new Error('V2-62 normal sheet mismatch');\n      region.format.columnWidth=specification.role==='normal'?specification.gridColumnWidth:specification.role==='cover'?3:18;",'builder-normal-width3')
    model_path=DEST/'delivery_model_v2_62_r01.py';builder_path=DEST/'build_xlsx_v2_62_r01.mjs'
    write(model_path,model.encode('utf-8'));write(builder_path,builder.encode('utf-8'))
    profile=DEST/'format-profile-v2-62-r01.json'
    write(profile,(json.dumps({'schema':'spec-agent-format-profile/1','role':'AG-SPEC','id':'v2-62-user-selected','userOverrideOfProjectGrid120':True,'cover':{'columns':47,'printArea':'O6:AU36','outside':'unbordered'},'normal':{'columns':62,'lastColumn':'BJ','columnWidth':3,'narrativeStartColumn':'B','outsideFrame':'medium','headerBottom':'double'},'itemList':{'columns':10,'lastColumn':'J','headerRow':1,'dataMerges':False,'recordSplitting':False},'formulaAuthoring':False,'literalStringStorage':True,'businessContentAuthored':False,'artifactToolPublicApiOnly':True,'printMetadataStatus':'PUBLIC_API_NOT_YET_VERIFIED','metadataInWorkbookStatus':'PUBLIC_API_NOT_YET_VERIFIED','authoringMarkerStarted':False,'actualXlsxCreated':False},ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    # Functions-only extraction: production main, imports, bound-file reads and providers cannot run.
    selected={'col','a1','text_width','cell_height','new_sheet','add_text','add_matrix','add_blocks','document_model'}
    tree=ast.parse(model);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected]
    env={'math':math,'re':re,'GRID_COLUMNS':62,'GRID_COLUMN_WIDTH':3,'GRID_TEXT_UNITS_PER_COLUMN':2.75,'GRID_BODY_START_COLUMN':2,'GRID_IMAGE_MAX_WIDTH':1100,'FORMAT_PROFILE':{'id':'v2-62-user-selected'},'TABLE_COLUMNS':['No','論理名','物理名','PK','NOT NULL','タイプ','長さ','初期値','説明']}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(model_path),'exec'),env)
    tests=[]
    def check(name,fn,expect_error=False):
        try:fn()
        except ValueError:
            if not expect_error:raise
        else:
            if expect_error:raise AssertionError('Expected format rejection: '+name)
        tests.append({'name':name,'pass':True})
    def eq(a,b):assert a==b,(a,b)
    check('BJ-is-62',lambda:eq(env['col'](62),'BJ'))
    check('normal62-width3',lambda:eq(env['new_sheet']('synthetic','normal',62)['gridColumnWidth'],3))
    check('normal120-is-rejected',lambda:env['new_sheet']('synthetic','normal',120),True)
    samples=['001','000000000000000001','1.0','=1+1','+001','-001','@name',"'quote",'令和06年04月01日','9223372036854775807','a|b','line1\nline2']
    def literals():
        s=env['new_sheet']('synthetic','list',10)
        for i,value in enumerate(samples,1):env['add_text'](s,i,1,1,value)
        eq([o['value'] for o in s['operations']],samples)
    check('all-literals-exact-no-coercion',literals)
    def grid():
        s=env['new_sheet']('synthetic','normal',62);matrix=[['a','b','c'],['001','=1+1','令和06年04月01日']]
        env['add_matrix'](s,1,matrix,grid=True)
        eq([o['range'] for o in s['operations'][:3]],['A1:T1','U1:AO1','AP1:BJ1'])
        eq([o['value'] for o in s['operations']],[v for row in matrix for v in row]);eq(s['tables'][0]['range'],'A1:BJ2')
    check('grid-proportional-spans-exact62',grid)
    def prose():
        s=env['new_sheet']('synthetic','normal',62);env['add_blocks'](s,[{'kind':'paragraph','text':'SYNTHETIC-001','sourceLines':[1,1]}],3)
        eq(s['operations'][0]['range'],'B3:BJ3');eq(s['operations'][0]['value'],'SYNTHETIC-001')
    check('narrative-B-to-BJ',prose)
    check('cell32768-rejected',lambda:env['add_text'](env['new_sheet']('s','list',10),1,1,1,'x'*32768),True)
    check('unrepresentable-control-rejected',lambda:env['add_text'](env['new_sheet']('s','list',10),1,1,1,'x\x01'),True)
    def long_token():
        s=env['new_sheet']('s','list',1);env['add_matrix'](s,1,[['header'],['x'*500]])
    check('oversize-whole-list-token-rejected',long_token,True)
    def record_rows():
        s=env['new_sheet']('s','list',10);matrix=[[str(i) for i in range(10)],['0001']*10,['0002']*10]
        eq(env['add_matrix'](s,1,matrix),4);eq(len(s['operations']),30);eq(s['tables'][0]['recordCount'],2)
        eq([o['range'] for o in s['operations'][:10]],[f'{env["col"](i)}1:{env["col"](i)}1' for i in range(1,11)])
    check('list10-header1-records-not-split-or-merged',record_rows)
    after={str(p):digest(safe(p).read_bytes()) for p in source_paths};assert before==after
    result={'schema':'spec-agent-format-candidate-preparation/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'CODE_ONLY_SYNTHETIC_GEOMETRY','status':'PREPARED_NOT_XLSX_AUTHORING','sourcePinsBefore':before,'sourcePinsAfter':after,'oldFilesUnchanged':True,'mechanicalCodeChanges':changes,'candidatePins':{str(p):digest(safe(p).read_bytes()) for p in (model_path,builder_path,profile)},'syntheticTests':tests,'syntheticPassCount':len(tests),'productionInputRead':False,'providerExecuted':False,'authoringMarkerStarted':False,'artifactToolExecuted':False,'actualXlsxCreated':False,'outputModified':False,'remaining':['Native artifact authoring marker must be coordinated exactly once after document plan count is fixed.','Artifact public print margins/areas/repeating-header and Excel-contained metadata API remain unverified.','Actual XLSX full literal/blank/border/geometry and original-size image review remain required.']}
    target=REPORT/'candidate-preparation.json';write(target,(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'path':str(target),'sha256':digest(safe(target).read_bytes()),'syntheticPassCount':len(tests),'actualXlsxCreated':False},ensure_ascii=False))

if __name__=='__main__':main()
